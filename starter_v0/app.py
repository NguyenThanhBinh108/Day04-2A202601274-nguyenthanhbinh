from __future__ import annotations

import json
import re
from html import escape
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from chat import (
    ARTIFACTS_DIR,
    ROOT,
    now_iso,
    run_model_tool_loop,
    safe_slug,
    trim_history,
    write_transcript,
)
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version


load_lab_env(ROOT)

PROVIDERS = ["openrouter", "openai", "anthropic", "gemini"]
DEFAULT_SYSTEM_PROMPT = ARTIFACTS_DIR / "system_prompt.md"
DEFAULT_TOOLS = ARTIFACTS_DIR / "tools.yaml"
TRANSCRIPTS_DIR = ROOT / "transcripts"
RUNS_DIR = ROOT / "runs"
DEFAULT_HISTORY_WINDOW = 5
DEFAULT_MAX_TOOL_ROUNDS = 4


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def json_preview(value: Any, *, max_chars: int = 5000) -> str:
    text = json.dumps(value, ensure_ascii=False, indent=2, default=str)
    if len(text) > max_chars:
        return f"{text[:max_chars]}\n...<truncated>"
    return text


def compact_result(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {"type": type(value).__name__, "value": str(value)}

    keys = ["error", "message", "status", "item_count", "total_results", "chars_returned", "pdf_path", "txt_path"]
    summary = {key: value.get(key) for key in keys if key in value}
    for collection_key in ("items", "results"):
        items = value.get(collection_key)
        if isinstance(items, list):
            summary[collection_key] = f"{len(items)} item(s)"
            if items:
                first = items[0]
                if isinstance(first, dict):
                    summary["first_item"] = {
                        key: first.get(key)
                        for key in ("title", "source", "url", "summary", "section")
                        if key in first
                    }
    return summary or value


def make_transcript_id(version: str, provider: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    return "_".join([safe_slug(version), safe_slug(provider), timestamp])


def initialize_state() -> None:
    defaults = {
        "history": [],
        "turns": [],
        "transcript": None,
        "transcript_path": None,
        "last_provider": None,
        "last_version": None,
        "last_artifact_version": None,
        "scenario_label": "",
        "pending_prompt": None,
        "saved_sessions": {},
        "active_session_id": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def reset_conversation() -> None:
    st.session_state.history = []
    st.session_state.turns = []
    st.session_state.transcript = None
    st.session_state.transcript_path = None
    st.session_state.last_artifact_version = None
    st.session_state.pending_prompt = None
    st.session_state.active_session_id = None


def session_title(snapshot: dict[str, Any]) -> str:
    turns = snapshot.get("turns") or []
    first_user = ""
    for turn in turns:
        if turn.get("user"):
            first_user = str(turn["user"])
            break
    if not first_user:
        first_user = "Đoạn chat mới"
    if len(first_user) > 64:
        first_user = first_user[:61] + "..."
    return first_user


def current_session_snapshot() -> dict[str, Any]:
    transcript = st.session_state.transcript or {}
    session_id = (
        st.session_state.active_session_id
        or transcript.get("transcript_id")
        or f"draft_{datetime.now().strftime('%Y%m%dT%H%M%S%f')}"
    )
    return {
        "session_id": session_id,
        "history": list(st.session_state.history),
        "turns": list(st.session_state.turns),
        "transcript": st.session_state.transcript,
        "transcript_path": str(st.session_state.transcript_path) if st.session_state.transcript_path else None,
        "last_provider": st.session_state.last_provider,
        "last_version": st.session_state.last_version,
        "last_artifact_version": st.session_state.last_artifact_version,
        "scenario_label": st.session_state.scenario_label,
    }


def save_current_session() -> None:
    has_content = bool(st.session_state.history or st.session_state.turns or st.session_state.transcript)
    if not has_content:
        return
    snapshot = current_session_snapshot()
    session_id = snapshot["session_id"]
    st.session_state.saved_sessions[session_id] = snapshot
    st.session_state.active_session_id = session_id


def load_saved_session(session_id: str) -> None:
    snapshot = st.session_state.saved_sessions.get(session_id)
    if not snapshot:
        return
    st.session_state.history = list(snapshot.get("history") or [])
    st.session_state.turns = list(snapshot.get("turns") or [])
    st.session_state.transcript = snapshot.get("transcript")
    transcript_path = snapshot.get("transcript_path")
    st.session_state.transcript_path = Path(transcript_path) if transcript_path else None
    st.session_state.last_provider = snapshot.get("last_provider")
    st.session_state.last_version = snapshot.get("last_version")
    st.session_state.last_artifact_version = snapshot.get("last_artifact_version")
    st.session_state.scenario_label = snapshot.get("scenario_label") or ""
    st.session_state.pending_prompt = None
    st.session_state.active_session_id = session_id


def start_new_transcript() -> None:
    save_current_session()
    reset_conversation()


@st.cache_resource(show_spinner=False)
def cached_provider(provider_name: str) -> Any:
    return make_provider(provider_name)


@st.cache_data(show_spinner=False)
def cached_declarations(path_text: str) -> list[dict[str, Any]]:
    return load_tool_declarations(Path(path_text))


def ensure_transcript(
    *,
    provider_name: str,
    model: str | None,
    version: str,
    artifact_version: dict[str, str],
    history_window: int,
    max_tool_rounds: int,
) -> None:
    needs_new = (
        st.session_state.transcript is None
        or st.session_state.last_provider != provider_name
        or st.session_state.last_version != version
        or st.session_state.last_artifact_version != artifact_version["artifact_version"]
    )
    if not needs_new:
        return

    transcript_id = make_transcript_id(version, provider_name)
    transcript_path = TRANSCRIPTS_DIR / f"{transcript_id}.transcript.json"
    st.session_state.transcript = {
        "transcript_id": transcript_id,
        **artifact_version,
        "provider": provider_name,
        "model": model,
        "system_prompt": str(DEFAULT_SYSTEM_PROMPT),
        "tools": str(DEFAULT_TOOLS),
        "history_window": history_window,
        "max_tool_rounds": max_tool_rounds,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }
    st.session_state.transcript_path = transcript_path
    st.session_state.last_provider = provider_name
    st.session_state.last_version = version
    st.session_state.last_artifact_version = artifact_version["artifact_version"]


def run_turn(
    *,
    user_text: str,
    scenario_label: str,
    provider_name: str,
    model: str | None,
    version: str,
    history_window: int,
    max_tool_rounds: int,
    user_already_recorded: bool = False,
) -> None:
    system_prompt = read_text(DEFAULT_SYSTEM_PROMPT)
    artifact_version = artifact_version_dict(build_artifact_version(version, DEFAULT_SYSTEM_PROMPT, DEFAULT_TOOLS))
    declarations = cached_declarations(str(DEFAULT_TOOLS))
    openai_tools = to_openai_tools(declarations)
    provider = cached_provider(provider_name)
    selected_model = model or getattr(provider, "default_model", None)

    ensure_transcript(
        provider_name=provider_name,
        model=selected_model,
        version=version,
        artifact_version=artifact_version,
        history_window=history_window,
        max_tool_rounds=max_tool_rounds,
    )

    messages = [
        {"role": "system", "content": system_prompt},
        *trim_history(st.session_state.history, history_window),
        {"role": "user", "content": user_text},
    ]

    turn_record: dict[str, Any] = {
        "turn_index": len(st.session_state.turns) + 1,
        "started_at": now_iso(),
        "user": user_text,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
        "scenario_label": scenario_label,
    }

    try:
        result = run_model_tool_loop(
            provider=provider,
            messages=messages,
            tools=openai_tools,
            model=model or None,
            max_tool_rounds=max_tool_rounds,
        )
        turn_record.update(result)
        assistant_text = result.get("assistant_text", "")
        if not user_already_recorded:
            st.session_state.history.append({"role": "user", "content": user_text})
        st.session_state.history.append({"role": "assistant", "content": assistant_text})
    except Exception as exc:
        turn_record.update(
            {
                "status": "provider_error",
                "error": f"{type(exc).__name__}: {str(exc)}",
                "assistant_text": "Provider error. Inspect the turn details below.",
            }
        )
        if not user_already_recorded:
            st.session_state.history.append({"role": "user", "content": user_text})
        st.session_state.history.append({"role": "assistant", "content": turn_record["assistant_text"]})

    turn_record["ended_at"] = now_iso()
    turn_record["artifact_version"] = artifact_version["artifact_version"]
    turn_record["version"] = version
    st.session_state.turns.append(turn_record)

    transcript = st.session_state.transcript
    if transcript is not None:
        transcript["turns"].append(turn_record)
        write_transcript(st.session_state.transcript_path, transcript)
    save_current_session()


def status_badge(status: str) -> str:
    colors = {
        "answered": "#0f766e",
        "waiting_for_user": "#b45309",
        "max_tool_rounds": "#b45309",
        "provider_error": "#b91c1c",
        "started": "#475569",
    }
    return colors.get(status, "#475569")


def render_tool_event(event: dict[str, Any], index: int, round_index: int | None = None) -> None:
    result = event.get("result", {})
    has_error = isinstance(result, dict) and bool(result.get("error"))
    status = "error" if has_error else (result.get("status") if isinstance(result, dict) and result.get("status") else "ok")
    label_round = f"Round {round_index}" if round_index is not None else "Round ?"

    st.markdown(
        f"""
        <div class="trace-card">
          <div class="trace-top">
            <span class="trace-tool">{event.get("tool", "unknown")}</span>
            <span class="trace-meta">{label_round} · event {index} · {status}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    columns = st.columns([1, 1])
    with columns[0]:
        st.caption("Args")
        st.code(json_preview(event.get("args", {}), max_chars=3000), language="json")
    with columns[1]:
        st.caption("Result / error")
        st.code(json_preview(compact_result(result), max_chars=3000), language="json")


def render_turn(turn: dict[str, Any], *, expanded: bool = False) -> None:
    status = turn.get("status", "unknown")
    color = status_badge(status)
    with st.container(border=True):
        st.markdown(
            f"""
            <div class="turn-head">
              <div>
                <div class="turn-title">Turn {turn.get("turn_index", "?")}</div>
                <div class="muted">{turn.get("artifact_version", "")}</div>
              </div>
              <div class="status-pill" style="border-color:{color};color:{color};">{status}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption("Request")
        st.markdown(turn.get("user", ""))
        st.caption("Final response")
        if turn.get("error"):
            st.error(turn["error"])
        st.markdown(turn.get("assistant_text") or "")

        rounds = turn.get("rounds", [])
        events = turn.get("tool_events", [])
        with st.expander(f"Tool Trace · {len(events)} event(s)", expanded=expanded):
            if not rounds and not events:
                st.info("No tool calls recorded for this turn.")
            for round_record in rounds:
                round_index = round_record.get("round")
                st.markdown(f"**Round {round_index}**")
                if round_record.get("assistant_text"):
                    st.caption("Assistant before tool call")
                    st.write(round_record["assistant_text"])
                calls = round_record.get("tool_calls", [])
                results = round_record.get("tool_results", [])
                if not calls:
                    st.caption("No tool call in this round.")
                for index, result_event in enumerate(results, start=1):
                    render_tool_event(result_event, index, round_index)

        with st.expander("Raw turn JSON", expanded=False):
            st.code(json_preview(turn, max_chars=12000), language="json")


def load_json_files(folder: Path, pattern: str) -> list[tuple[Path, dict[str, Any]]]:
    if not folder.exists():
        return []
    loaded: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(folder.glob(pattern), key=lambda item: item.stat().st_mtime, reverse=True):
        try:
            loaded.append((path, json.loads(path.read_text(encoding="utf-8"))))
        except Exception:
            continue
    return loaded


def normalize_request(text: str) -> str:
    text = re.sub(r"\s+", " ", text.strip().lower())
    return text[:180]


def render_table(rows: list[dict[str, Any]], columns: list[str]) -> None:
    if not rows:
        st.info("No rows to display.")
        return

    header = "".join(f"<th>{escape(column)}</th>" for column in columns)
    body_rows = []
    for row in rows:
        cells = []
        for column in columns:
            value = row.get(column, "")
            text = "" if value is None else str(value)
            cells.append(f"<td title=\"{escape(text)}\">{escape(text)}</td>")
        body_rows.append(f"<tr>{''.join(cells)}</tr>")

    html = (
        '<div class="table-wrap">'
        '<table class="evidence-table">'
        f"<thead><tr>{header}</tr></thead>"
        f"<tbody>{''.join(body_rows)}</tbody>"
        "</table>"
        "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)


def render_chat_bubble(role: str, content: str) -> None:
    if role == "user":
        klass = "chat-row chat-row-user"
        bubble = "chat-bubble chat-bubble-user"
        label = "You"
    else:
        klass = "chat-row chat-row-assistant"
        bubble = "chat-bubble chat-bubble-assistant"
        label = "Agent"

    safe_content = escape(content or "").replace("\n", "<br>")
    html = (
        f'<div class="{klass}">'
        f'<div class="{bubble}">'
        f'<div class="chat-label">{label}</div>'
        f'<div class="chat-text">{safe_content}</div>'
        "</div>"
        "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)


def render_chat_history() -> None:
    bubbles = []
    for message in st.session_state.history:
        role = message.get("role", "assistant")
        if role == "user":
            klass = "chat-row chat-row-user"
            bubble = "chat-bubble chat-bubble-user"
            label = "You"
        else:
            klass = "chat-row chat-row-assistant"
            bubble = "chat-bubble chat-bubble-assistant"
            label = "Agent"
        safe_content = escape(message.get("content", "") or "").replace("\n", "<br>")
        bubbles.append(
            f'<div class="{klass}">'
            f'<div class="{bubble}">'
            f'<div class="chat-label">{label}</div>'
            f'<div class="chat-text">{safe_content}</div>'
            "</div>"
            "</div>"
        )

    if not bubbles:
        bubbles.append('<div class="chat-empty">Start a conversation with the research agent.</div>')

    html = f'<div class="chat-shell"><div class="chat-scroll">{"".join(bubbles)}</div></div>'
    st.markdown(html, unsafe_allow_html=True)


def evidence_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for turn in st.session_state.turns:
        rows.append(
            {
                "source": "current session",
                "version": turn.get("version", ""),
                "artifact_version": turn.get("artifact_version", ""),
                "request": turn.get("user", ""),
                "scenario": turn.get("scenario_label", ""),
                "response": turn.get("assistant_text", ""),
                "status": turn.get("status", ""),
                "tool_count": len(turn.get("tool_events", [])),
                "tool_names": ", ".join(event.get("tool", "") for event in turn.get("tool_events", [])),
                "payload": turn,
            }
        )

    for path, transcript in load_json_files(TRANSCRIPTS_DIR, "*.transcript.json"):
        for turn in transcript.get("turns", []):
            rows.append(
                {
                    "source": path.name,
                    "version": transcript.get("version", turn.get("version", "")),
                    "artifact_version": transcript.get("artifact_version", turn.get("artifact_version", "")),
                    "request": turn.get("user", ""),
                    "scenario": turn.get("scenario_label", ""),
                    "response": turn.get("assistant_text", ""),
                    "status": turn.get("status", ""),
                    "tool_count": len(turn.get("tool_events", [])),
                    "tool_names": ", ".join(event.get("tool", "") for event in turn.get("tool_events", [])),
                    "payload": turn,
                }
            )

    for path, run in load_json_files(RUNS_DIR, "*.json"):
        for result in run.get("results", []):
            request = result.get("input")
            rows.append(
                {
                    "source": path.name,
                    "version": run.get("version", ""),
                    "artifact_version": run.get("artifact_version", ""),
                    "request": json_preview(request, max_chars=700) if not isinstance(request, str) else request,
                    "scenario": result.get("id", ""),
                    "response": result.get("result", {}).get("actual_text") or "",
                    "status": "PASS" if result.get("result", {}).get("passed") else "FAIL",
                    "tool_count": len(result.get("result", {}).get("actual_tool_calls", [])),
                    "tool_names": ", ".join(call.get("name", "") for call in result.get("result", {}).get("actual_tool_calls", [])),
                    "payload": result,
                }
            )

    return rows


def render_version_compare() -> None:
    rows = evidence_rows()
    if not rows:
        st.info("No current turns, transcripts, or run JSON files found yet.")
        return

    query = st.text_input("Find scenario", placeholder="Scenario label, request text, case id, or keyword")
    if query:
        needle = query.lower()
        filtered = [
            row
            for row in rows
            if needle in row.get("request", "").lower()
            or needle in row.get("scenario", "").lower()
            or needle in row.get("source", "").lower()
        ]
    else:
        grouped = {}
        for row in rows:
            key = row.get("scenario") or normalize_request(row.get("request", ""))
            grouped.setdefault(key, []).append(row)
        repeated = [items for items in grouped.values() if len({item.get("version") for item in items}) > 1]
        filtered = repeated[0] if repeated else rows[:8]

    st.caption("Same scenario, different prompt/tool versions. Use this table during showdown to show improvement.")
    render_table(
        [
            {
                "scenario": row["scenario"],
                "version": row["version"],
                "status": row["status"],
                "tools": row["tool_names"],
                "artifact": row["artifact_version"],
                "source": row["source"],
                "request": row["request"],
            }
            for row in filtered
        ],
        ["scenario", "version", "status", "tools", "artifact", "source", "request"],
    )

    selected_labels = [
        f"{row['scenario'] or 'scenario'} · {row['version']} · {row['status']} · {row['source']}"
        for row in filtered
    ]
    if selected_labels:
        selected = st.selectbox("Inspect evidence", selected_labels)
        selected_row = filtered[selected_labels.index(selected)]
        st.caption("Response")
        st.markdown(selected_row.get("response") or "_No response text recorded._")
        with st.expander("Raw evidence JSON", expanded=False):
            st.code(json_preview(selected_row["payload"], max_chars=16000), language="json")


def apply_style() -> None:
    st.set_page_config(page_title="Research Agent Eval", page_icon=None, layout="wide")
    st.markdown(
        """
        <style>
        :root {
          --bg: #f8fafc;
          --panel: #ffffff;
          --ink: #0f172a;
          --muted: #64748b;
          --line: #e2e8f0;
          --accent: #0f766e;
        }
        .stApp {
          background:
            linear-gradient(180deg, rgba(248,250,252,.98), rgba(241,245,249,.98));
          color: var(--ink);
        }
        .stApp p,
        .stApp span,
        .stApp label,
        .stApp div {
          letter-spacing: 0;
        }
        ::selection {
          background: #dbeafe;
          color: #0f172a;
        }
        .main .block-container {
          padding-top: 1.25rem;
          padding-bottom: 6rem;
          max-width: 1280px;
        }
        h1, h2, h3 { letter-spacing: 0; }
        div[data-testid="stMetric"] {
          background: var(--panel);
          border: 1px solid var(--line);
          border-radius: 8px;
          padding: .75rem 1rem;
        }
        div[data-testid="stMetric"] * {
          color: #0f172a !important;
          -webkit-text-fill-color: #0f172a !important;
        }
        div[data-testid="stMetricLabel"] p {
          color: #334155 !important;
          -webkit-text-fill-color: #334155 !important;
        }
        div[data-testid="stMetricValue"] div {
          color: #0f172a !important;
          -webkit-text-fill-color: #0f172a !important;
        }
        .table-wrap {
          width: 100%;
          overflow-x: auto;
          overflow-y: hidden;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          background: #ffffff;
          padding-bottom: .35rem;
          scrollbar-gutter: stable;
        }
        .table-wrap::-webkit-scrollbar {
          height: 12px;
        }
        .table-wrap::-webkit-scrollbar-track {
          background: #e2e8f0;
          border-radius: 999px;
        }
        .table-wrap::-webkit-scrollbar-thumb {
          background: #94a3b8;
          border-radius: 999px;
        }
        .evidence-table {
          width: max-content;
          min-width: 1500px;
          border-collapse: collapse;
          table-layout: fixed;
          background: #ffffff;
          color: #0f172a;
          font-size: .9rem;
        }
        .evidence-table th,
        .evidence-table td {
          min-width: 150px;
        }
        .evidence-table th:nth-child(1),
        .evidence-table td:nth-child(1) {
          min-width: 190px;
        }
        .evidence-table th:nth-child(5),
        .evidence-table td:nth-child(5),
        .evidence-table th:nth-child(6),
        .evidence-table td:nth-child(6),
        .evidence-table th:nth-child(7),
        .evidence-table td:nth-child(7) {
          min-width: 260px;
        }
        .evidence-table th,
        .evidence-table td {
          border-bottom: 1px solid #e2e8f0;
          padding: .65rem .75rem;
          color: #0f172a !important;
          -webkit-text-fill-color: #0f172a !important;
          background: #ffffff !important;
          vertical-align: top;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
        .evidence-table th {
          background: #f8fafc !important;
          color: #334155 !important;
          -webkit-text-fill-color: #334155 !important;
          font-weight: 700;
          text-align: left;
        }
        .evidence-table tr:hover,
        .evidence-table tr:hover td,
        .evidence-table td:hover,
        .evidence-table th:hover {
          background: #ffffff !important;
          background-color: #ffffff !important;
          color: #0f172a !important;
          -webkit-text-fill-color: #0f172a !important;
        }
        .evidence-table thead tr:hover th {
          background: #f8fafc !important;
          background-color: #f8fafc !important;
          color: #334155 !important;
          -webkit-text-fill-color: #334155 !important;
        }
        .hero {
          display: flex;
          align-items: flex-end;
          justify-content: space-between;
          gap: 1rem;
          border-bottom: 1px solid var(--line);
          padding-bottom: 1rem;
          margin-bottom: 1rem;
        }
        .title {
          font-size: 1.65rem;
          font-weight: 720;
          color: #0f172a;
          letter-spacing: 0;
          margin: 0;
        }
        .subtitle, .muted {
          color: var(--muted);
          font-size: .9rem;
        }
        .status-pill {
          border: 1px solid;
          border-radius: 999px;
          padding: .2rem .55rem;
          font-size: .78rem;
          font-weight: 650;
          white-space: nowrap;
        }
        .turn-head, .trace-top {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 1rem;
        }
        .turn-title {
          font-weight: 720;
          font-size: 1rem;
        }
        .trace-card {
          border: 1px solid var(--line);
          border-radius: 8px;
          padding: .65rem .8rem;
          margin: .6rem 0 .4rem;
          background: #fbfdff;
        }
        .trace-tool {
          font-weight: 720;
          font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
        }
        .trace-meta {
          color: var(--muted);
          font-size: .82rem;
        }
        .chat-row {
          display: flex;
          width: 100%;
          margin: .45rem 0;
        }
        .chat-shell {
          height: 42vh;
          min-height: 260px;
          max-height: 480px;
          overflow-y: auto;
          overflow-x: hidden;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          background: #f8fafc;
          padding: .85rem;
          margin-bottom: .75rem;
          scroll-behavior: smooth;
        }
        .chat-shell::-webkit-scrollbar {
          width: 12px;
        }
        .chat-shell::-webkit-scrollbar-track {
          background: #e2e8f0;
          border-radius: 999px;
        }
        .chat-shell::-webkit-scrollbar-thumb {
          background: #94a3b8;
          border-radius: 999px;
        }
        .chat-scroll {
          display: flex;
          min-height: 100%;
          flex-direction: column;
          justify-content: flex-end;
        }
        .chat-empty {
          margin: auto;
          color: #64748b !important;
          -webkit-text-fill-color: #64748b !important;
          font-size: .95rem;
        }
        .chat-row-user {
          justify-content: flex-end;
        }
        .chat-row-assistant {
          justify-content: flex-start;
        }
        .chat-bubble {
          max-width: min(74%, 820px);
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          padding: .7rem .85rem;
          color: #0f172a !important;
          -webkit-text-fill-color: #0f172a !important;
          box-shadow: none;
          overflow-wrap: anywhere;
        }
        .chat-bubble-user {
          background: #e0f2fe;
          border-color: #bae6fd;
        }
        .chat-bubble-assistant {
          background: #ffffff;
          border-color: #e2e8f0;
        }
        .chat-label {
          color: #64748b !important;
          -webkit-text-fill-color: #64748b !important;
          font-size: .76rem;
          font-weight: 700;
          margin-bottom: .25rem;
        }
        .chat-text {
          color: #0f172a !important;
          -webkit-text-fill-color: #0f172a !important;
          font-size: .95rem;
          line-height: 1.5;
        }
        .chat-row:hover,
        .chat-bubble:hover {
          background-color: inherit !important;
        }
        div[data-testid="stExpander"] {
          border: 1px solid #e2e8f0 !important;
          border-radius: 8px !important;
          background: #ffffff !important;
        }
        div[data-testid="stExpander"] details summary {
          background: #f8fafc !important;
          background-color: #f8fafc !important;
          color: #0f172a !important;
          border-radius: 8px 8px 0 0 !important;
        }
        div[data-testid="stExpander"] details summary:hover,
        div[data-testid="stExpander"] details summary:focus,
        div[data-testid="stExpander"] details summary:active {
          background: #f8fafc !important;
          background-color: #f8fafc !important;
          color: #0f172a !important;
          box-shadow: none !important;
        }
        div[data-testid="stExpander"] details summary *,
        div[data-testid="stExpander"] details summary:hover * {
          color: #0f172a !important;
          -webkit-text-fill-color: #0f172a !important;
          opacity: 1 !important;
        }
        section[data-testid="stSidebar"] {
          border-right: 1px solid var(--line);
        }
        button[data-baseweb="tab"] {
          background: transparent !important;
        }
        button:hover,
        button:focus,
        button:active,
        [role="button"]:hover,
        [role="button"]:focus,
        [role="button"]:active,
        [role="tab"]:hover,
        [role="tab"]:focus,
        [role="tab"]:active,
        div[data-testid="stMetric"]:hover,
        div[data-testid="stTabs"] button:hover,
        div[data-testid="stTabs"] button:focus,
        div[data-testid="stTabs"] button:active,
        div[data-testid="stChatInput"] > div:hover,
        div[data-testid="stChatInput"] > div:focus-within {
          background: transparent !important;
          background-color: transparent !important;
          box-shadow: none !important;
        }
        div[data-testid="stMetric"]:hover {
          background: var(--panel) !important;
          background-color: var(--panel) !important;
        }
        div[data-testid="stChatInput"] > div:hover,
        div[data-testid="stChatInput"] > div:focus-within {
          background: #f8fafc !important;
          background-color: #f8fafc !important;
          border-color: #e2e8f0 !important;
        }
        div[data-testid="stChatInput"] textarea:hover,
        div[data-testid="stChatInput"] textarea:focus {
          background: #f1f5f9 !important;
          background-color: #f1f5f9 !important;
        }
        div[data-testid="stTabs"] * {
          text-shadow: none !important;
        }
        div[data-testid="stTabs"] [role="tab"],
        div[data-testid="stTabs"] [role="tab"] *,
        div[data-testid="stTabs"] [role="tab"] p,
        div[data-testid="stTabs"] [role="tab"] span {
          color: #0f172a !important;
          -webkit-text-fill-color: #0f172a !important;
          opacity: 1 !important;
        }
        div[data-testid="stTabs"] button,
        div[data-testid="stTabs"] button *,
        button[data-baseweb="tab"],
        button[data-baseweb="tab"] * {
          color: #0f172a !important;
          -webkit-text-fill-color: #0f172a !important;
          opacity: 1 !important;
        }
        button[data-baseweb="tab"] p {
          color: #0f172a !important;
          -webkit-text-fill-color: #0f172a !important;
          font-weight: 650;
        }
        div[data-testid="stTabs"] button[aria-selected="true"],
        div[data-testid="stTabs"] button[aria-selected="true"] *,
        div[data-testid="stTabs"] [role="tab"][aria-selected="true"],
        div[data-testid="stTabs"] [role="tab"][aria-selected="true"] *,
        button[data-baseweb="tab"][aria-selected="true"] p {
          color: #ef4444 !important;
          -webkit-text-fill-color: #ef4444 !important;
        }
        div[data-testid="stChatInput"] {
          background: transparent !important;
          border-top: 1px solid var(--line);
          position: sticky !important;
          left: auto !important;
          right: auto !important;
          transform: none !important;
          width: 100% !important;
          bottom: .75rem !important;
          z-index: 100 !important;
          padding: .65rem !important;
          border-radius: 8px !important;
          background-color: #f8fafc !important;
          box-shadow: 0 8px 24px rgba(15, 23, 42, .08) !important;
        }
        div[data-testid="stChatInput"] > div {
          background: #f8fafc !important;
          border: 1px solid #e2e8f0 !important;
          border-radius: 8px !important;
        }
        div[data-testid="stChatInput"] textarea {
          background: #f1f5f9 !important;
          color: #0f172a !important;
          border: 1px solid #cbd5e1 !important;
          border-radius: 8px !important;
          box-shadow: none !important;
        }
        div[data-testid="stChatInput"] textarea::placeholder {
          color: #64748b !important;
        }
        div[data-testid="stChatInput"] textarea:focus {
          border-color: #94a3b8 !important;
          box-shadow: 0 0 0 1px #94a3b8 !important;
        }
        @media (max-width: 900px) {
          div[data-testid="stChatInput"] {
            width: 100% !important;
            bottom: .75rem !important;
          }
        }
        div[data-testid="stChatMessage"],
        div[data-testid="stChatMessage"] *,
        div[data-testid="stChatMessage"] p,
        div[data-testid="stChatMessage"] span,
        div[data-testid="stChatMessage"] li {
          color: #0f172a !important;
          -webkit-text-fill-color: #0f172a !important;
          opacity: 1 !important;
        }
        div[data-testid="stChatMessage"] {
          background: transparent !important;
        }
        div[data-testid="stTooltipContent"],
        div[data-baseweb="tooltip"],
        div[role="tooltip"] {
          background: #ffffff !important;
          background-color: #ffffff !important;
          color: #0f172a !important;
          border: 1px solid #e2e8f0 !important;
          box-shadow: none !important;
        }
        div[data-testid="stTooltipContent"] *,
        div[data-baseweb="tooltip"] *,
        div[role="tooltip"] * {
          color: #0f172a !important;
          -webkit-text-fill-color: #0f172a !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    apply_style()
    initialize_state()

    declarations = cached_declarations(str(DEFAULT_TOOLS))

    with st.sidebar:
        st.header("Demo Control")
        provider_name = st.selectbox("Provider", PROVIDERS, index=PROVIDERS.index("openrouter"))
        version = st.text_input("Version label", value="v3").strip() or "v3"
        st.session_state.scenario_label = st.text_input(
            "Scenario label",
            value=st.session_state.scenario_label,
            placeholder="demo-news-routing",
        ).strip()
        model = None
        history_window = DEFAULT_HISTORY_WINDOW
        max_tool_rounds = DEFAULT_MAX_TOOL_ROUNDS

        if st.button("New transcript", use_container_width=True):
            start_new_transcript()
            st.rerun()

        if st.session_state.saved_sessions:
            st.divider()
            session_ids = list(st.session_state.saved_sessions)
            labels = {
                session_id: session_title(st.session_state.saved_sessions[session_id])
                for session_id in session_ids
            }
            selected_session = st.selectbox(
                "Saved chats",
                session_ids,
                format_func=lambda session_id: labels.get(session_id, session_id),
            )
            if st.button("Open selected chat", use_container_width=True):
                save_current_session()
                load_saved_session(selected_session)
                st.rerun()

    st.markdown(
        """
        <div class="hero">
          <div>
            <p class="title">Research Agent Eval</p>
            <p class="subtitle">Chat, inspect tool traces, and compare evidence across versions.</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    metric_cols = st.columns(4)
    metric_cols[0].metric("Turns", len(st.session_state.turns))
    metric_cols[1].metric("Tool Events", sum(len(turn.get("tool_events", [])) for turn in st.session_state.turns))
    metric_cols[2].metric("Tools Declared", len(declarations))
    metric_cols[3].metric("Version", version)

    tab_chat, tab_trace, tab_compare, tab_artifacts = st.tabs(["Demo Chat", "Tool Trace", "Version Compare", "Artifacts"])

    with tab_chat:
        render_chat_history()

        if st.session_state.pending_prompt:
            pending_prompt = st.session_state.pending_prompt
            with st.spinner("Running model and tools..."):
                run_turn(
                    user_text=pending_prompt,
                    scenario_label=st.session_state.scenario_label,
                    provider_name=provider_name,
                    model=model,
                    version=version,
                    history_window=history_window,
                    max_tool_rounds=max_tool_rounds,
                    user_already_recorded=True,
                )
            st.session_state.pending_prompt = None
            st.rerun()

        prompt = st.chat_input("Ask the research agent...")
        if prompt:
            st.session_state.history.append({"role": "user", "content": prompt})
            st.session_state.pending_prompt = prompt
            st.rerun()

    with tab_trace:
        if not st.session_state.turns:
            st.info("Run a request in the Chat tab to see request, response, round status, args, result, and errors.")
        else:
            latest = st.session_state.turns[-1]
            st.subheader("Latest Request")
            render_turn(latest, expanded=True)
            if len(st.session_state.turns) > 1:
                st.subheader("Previous Turns")
                for turn in reversed(st.session_state.turns[:-1]):
                    render_turn(turn, expanded=False)

    with tab_compare:
        render_version_compare()

    with tab_artifacts:
        cols = st.columns([1, 1])
        with cols[0]:
            st.subheader("Transcript")
            if st.session_state.transcript_path:
                st.code(str(st.session_state.transcript_path), language=None)
                st.download_button(
                    "Download transcript JSON",
                    data=json_preview(st.session_state.transcript or {}, max_chars=500000),
                    file_name=Path(st.session_state.transcript_path).name,
                    mime="application/json",
                    use_container_width=True,
                )
            else:
                st.info("No transcript has been created yet.")

        with cols[1]:
            st.subheader("Declared Tools")
            render_table(
                [
                    {
                        "name": item.get("name"),
                        "description": item.get("description", ""),
                        "required": ", ".join(item.get("parameters", {}).get("required", [])),
                    }
                    for item in declarations
                ],
                ["name", "description", "required"],
            )


if __name__ == "__main__":
    main()
