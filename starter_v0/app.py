"""app.py — Research Agent UI (Streamlit)

Tái dùng run_model_tool_loop từ chat.py — không viết agent loop mới.
Hiển thị: request/response, tool trace (tên + args + result), version info, transcript.

Chạy: streamlit run app.py
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path

import streamlit as st

# Trên Windows, stdout của tiến trình Streamlit dùng codec cp1252. run_model_tool_loop
# trong chat.py in emoji 🔧 mỗi khi log một tool call, khiến cả lượt chat chết vì
# UnicodeEncodeError. Ép stdout/stderr về UTF-8 trước khi gọi loop.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import build_artifact_version
from chat import run_model_tool_loop

# ── Setup ──────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = ROOT / "transcripts"
TRANSCRIPTS_DIR.mkdir(exist_ok=True)

load_lab_env(ROOT)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Research Agent — DAY04 Lab",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Base */
    .stApp { background-color: #0f1117; }
    .block-container { padding-top: 1rem; }

    /* Chat messages */
    .stChatMessage {
        background-color: #1a1d26;
        border-radius: 12px;
        margin: 4px 0;
        border: 1px solid #252840;
    }

    /* Tool event cards */
    .tool-card {
        background: linear-gradient(135deg, #1e2130, #252840);
        border: 1px solid #3a3f5c;
        border-left: 4px solid #5b7df8;
        border-radius: 10px;
        padding: 10px 14px;
        margin: 6px 0;
    }
    .tool-card.error {
        border-left-color: #f87171;
        background: linear-gradient(135deg, #2a1a1a, #311f1f);
    }
    .tool-card.clarify {
        border-left-color: #fbbf24;
        background: linear-gradient(135deg, #1e1a10, #28220d);
    }
    .tool-name {
        color: #a78bfa;
        font-size: 13px;
        font-weight: bold;
        font-family: monospace;
        letter-spacing: 0.5px;
    }
    .tool-status-ok  { color: #34d399; font-size: 12px; }
    .tool-status-err { color: #f87171; font-size: 12px; }
    .tool-status-ask { color: #fbbf24; font-size: 12px; }

    /* Metric boxes */
    .metric-box {
        background: #1e2130;
        border: 1px solid #3a3f5c;
        border-radius: 8px;
        padding: 10px 6px;
        text-align: center;
        margin-bottom: 8px;
    }
    .metric-label { color: #9ca3af; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; }
    .metric-value { color: #a78bfa; font-size: 20px; font-weight: bold; margin-top: 2px; }

    /* Main header */
    .main-header {
        background: linear-gradient(135deg, #1a1d40, #0f1530);
        border: 1px solid #2d3352;
        padding: 16px 20px;
        border-radius: 12px;
        margin-bottom: 16px;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] { background-color: #13161f; }
    section[data-testid="stSidebar"] label { color: #9ca3af !important; font-size: 13px; }
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1 style="color:#a78bfa; margin:0; font-size:26px; font-weight:700;">
        🤖 Research Agent
    </h1>
    <p style="color:#6b7280; margin:4px 0 0 0; font-size:13px;">
        DAY04 Lab v2 — Tool Eval | Nhóm 2A202601602 — VinUniversity
    </p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration")

    provider_name = st.selectbox(
        "🌐 Provider",
        ["openrouter", "openai", "anthropic", "gemini"],
        index=0,
        help="LLM provider (cần API key tương ứng trong .env)",
    )

    version_label = st.selectbox(
        "📦 Version",
        ["v0", "v1", "v2", "v3"],
        index=2,
        help="Artifact version (system_prompt + tools.yaml)",
    )

    max_rounds = st.slider(
        "🔄 Max Tool Rounds",
        min_value=1, max_value=8, value=4,
        help="Số vòng tool tối đa mỗi turn",
    )

    st.divider()

    # Artifact hashes
    try:
        sp_path = ARTIFACTS_DIR / "system_prompt.md"
        tl_path = ARTIFACTS_DIR / "tools.yaml"
        av = build_artifact_version(version_label, sp_path, tl_path)
        st.markdown("### 📋 Artifact Hashes")
        st.caption(f"**Version:** `{av.artifact_version}`")
        st.caption(f"**Prompt:** `{av.prompt_hash[:16]}…`")
        st.caption(f"**Tools:**  `{av.tools_hash[:16]}…`")
    except Exception:
        st.caption("_(hash unavailable)_")

    st.divider()

    # Quick queries
    st.markdown("### 💡 Quick Queries")
    # Các câu này đều đã kiểm chứng truy xuất được trên company_policy.
    # Không đưa câu cần Twitter/web search vào đây: RAPIDAPI/TAVILY/FIRECRAWL
    # chưa có key nên những tool đó sẽ lỗi và làm hỏng demo.
    quick_queries = [
        "Vi phạm liêm chính học thuật Tier 3 bị xử lý thế nào?",
        "Sinh viên có được dùng ChatGPT làm bài tập không?",
        "Học bổng đầu vào cần duy trì GPA bao nhiêu?",
        "Quy định điểm danh và nghỉ học của VinUni ra sao?",
        "Hạn nộp hồ sơ tuyển sinh là khi nào?",
        "So sánh quy định học phí với quy định học bổng",
        "Điều kiện xét tốt nghiệp và cấp bằng gồm những gì?",
        "Tóm tắt 5 tweet mới nhất giúp mình",
        "Đăng bản tin này lên Telegram giúp mình",
        "Giải giúp mình nguyên hàm của x^2",
        "Thời tiết Hà Nội hôm nay?",
    ]
    selected_quick = st.selectbox(
        "Chọn câu mẫu",
        ["—"] + quick_queries,
        key="quick_select",
    )
    send_quick = st.button("▶ Gửi câu này", use_container_width=True, key="btn_quick")

    st.divider()

    if st.button("🗑️ Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.tool_events_history = []
        st.rerun()

# ── Session state ──────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []  # list of {role, content}
if "tool_events_history" not in st.session_state:
    st.session_state.tool_events_history = []  # parallel list, one entry per assistant turn

# ── Helpers ────────────────────────────────────────────────────────────────────

def _tool_summary(ev: dict) -> tuple[str, str]:
    """Return (summary_text, css_class) for a tool event."""
    result_obj = ev.get("result", {})
    tool_name   = ev.get("tool", "unknown")

    # clarify / ask_user
    if result_obj.get("awaiting_user"):
        q = result_obj.get("question", "")
        return f"⏸ Waiting for user — {q[:80]}", "tool-status-ask"

    if result_obj.get("error"):
        return f"❌ {result_obj['error']}: {result_obj.get('message','')[:60]}", "tool-status-err"

    items = result_obj.get("items") or result_obj.get("results") or []
    if isinstance(items, list) and items:
        return f"✅ {len(items)} item(s) returned", "tool-status-ok"

    # weather / other structured results
    if result_obj.get("current"):
        curr = result_obj["current"]
        return (
            f"✅ {result_obj.get('location','')} — "
            f"{curr.get('temperature_c','')}°C, {curr.get('weather_description','')}",
            "tool-status-ok",
        )

    return "✅ OK", "tool-status-ok"


def _render_tool_events(events: list[dict], expanded: bool = True) -> None:
    """Render a list of tool events as expander cards."""
    if not events:
        return
    with st.expander(f"🔧 Tool trace — {len(events)} call(s)", expanded=expanded):
        for ev in events:
            tool_name = ev.get("tool", "unknown")
            result_obj = ev.get("result", {})
            summary, s_class = _tool_summary(ev)

            is_err     = bool(result_obj.get("error"))
            is_clarify = bool(result_obj.get("awaiting_user"))
            card_class = ("tool-card error" if is_err
                          else "tool-card clarify" if is_clarify
                          else "tool-card")

            st.markdown(
                f'<div class="{card_class}">'
                f'<span class="tool-name">🛠 {tool_name}</span>'
                f'&nbsp;&nbsp;<span class="{s_class}">{summary}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

            c1, c2 = st.columns(2)
            with c1:
                st.caption("**Args:**")
                st.code(
                    json.dumps(ev.get("args", {}), ensure_ascii=False, indent=2),
                    language="json",
                )
            with c2:
                st.caption("**Result:**")
                # Compact result: hide big lists, show counts + first item
                disp = {}
                for k, v in result_obj.items():
                    if isinstance(v, list):
                        disp[f"{k}_count"] = len(v)
                        if v:
                            disp[f"{k}[0]"] = v[0]
                    else:
                        disp[k] = v
                st.code(
                    json.dumps(disp, ensure_ascii=False, indent=2, default=str),
                    language="json",
                )


def _run_agent(user_text: str) -> None:
    """Execute the agent loop for user_text and update session state."""
    # Optimistically add user message
    st.session_state.messages.append({"role": "user", "content": user_text})

    with st.chat_message("user", avatar="🧑"):
        st.markdown(user_text)

    with st.chat_message("assistant", avatar="🤖"):
        placeholder = st.empty()
        placeholder.markdown("⏳ *Đang xử lý...*")

        try:
            system_prompt_text = (ARTIFACTS_DIR / "system_prompt.md").read_text(encoding="utf-8")
            tool_declarations  = load_tool_declarations(ARTIFACTS_DIR / "tools.yaml")
            openai_tools       = to_openai_tools(tool_declarations)

            # Build message list: system + full conversation history
            messages_for_model = [
                {"role": "system", "content": system_prompt_text},
                *st.session_state.messages,  # includes the just-added user msg
            ]

            provider = make_provider(provider_name)
            t0 = time.time()

            loop_result = run_model_tool_loop(
                provider=provider,
                messages=messages_for_model,
                tools=openai_tools,
                model=None,
                max_tool_rounds=max_rounds,
            )

            elapsed      = time.time() - t0
            assistant_text = loop_result.get("assistant_text", "")
            tool_events    = loop_result.get("tool_events", [])
            rounds         = loop_result.get("rounds", [])
            status         = loop_result.get("status", "answered")

            placeholder.empty()
            st.markdown(assistant_text)

            # Tool trace (expanded for current turn)
            _render_tool_events(tool_events, expanded=True)

            # Status line
            st.caption(
                f"`{version_label}` · {len(rounds)} round(s) · "
                f"status: `{status}` · {elapsed:.1f}s"
            )

            # Persist
            st.session_state.messages.append({"role": "assistant", "content": assistant_text})
            st.session_state.tool_events_history.append(tool_events)

            # Auto-save transcript
            try:
                ts = datetime.now().strftime("%Y%m%dT%H%M%S")
                av_str = build_artifact_version(
                    version_label,
                    ARTIFACTS_DIR / "system_prompt.md",
                    ARTIFACTS_DIR / "tools.yaml",
                ).artifact_version
                t_path = TRANSCRIPTS_DIR / f"{ts}_ui_{version_label}.transcript.json"
                t_path.write_text(
                    json.dumps({
                        "version": version_label,
                        "artifact_version": av_str,
                        "provider": provider_name,
                        "timestamp": ts,
                        "query": user_text,
                        "assistant_text": assistant_text,
                        "tool_events": tool_events,
                        "rounds": len(rounds),
                        "status": status,
                        "elapsed_s": round(elapsed, 2),
                    }, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            except Exception:
                pass  # best-effort

        except Exception as exc:
            placeholder.empty()
            st.error(f"❌ **Error**: {exc}")
            st.caption("Kiểm tra API keys trong `.env` và chạy `preflight_provider.py` để debug.")
            st.session_state.messages.append({"role": "assistant", "content": f"[Error: {exc}]"})
            st.session_state.tool_events_history.append([])


# ── Stats row ──────────────────────────────────────────────────────────────────
total_turns = len([m for m in st.session_state.messages if m["role"] == "user"])
total_tools = sum(len(ev) for ev in st.session_state.tool_events_history)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f'<div class="metric-box"><div class="metric-label">Turns</div>'
                f'<div class="metric-value">{total_turns}</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="metric-box"><div class="metric-label">Tool Calls</div>'
                f'<div class="metric-value">{total_tools}</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="metric-box"><div class="metric-label">Version</div>'
                f'<div class="metric-value" style="font-size:17px;">{version_label}</div></div>',
                unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="metric-box"><div class="metric-label">Provider</div>'
                f'<div class="metric-value" style="font-size:14px;">{provider_name}</div></div>',
                unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Chat history ───────────────────────────────────────────────────────────────
# Track assistant-turn index to pair with tool_events_history
asst_idx = 0
for i, msg in enumerate(st.session_state.messages):
    role    = msg["role"]
    content = msg["content"]

    with st.chat_message(role, avatar="🧑" if role == "user" else "🤖"):
        st.markdown(content)

        if role == "assistant":
            # Show collapsed tool trace for past turns
            if asst_idx < len(st.session_state.tool_events_history):
                _render_tool_events(
                    st.session_state.tool_events_history[asst_idx],
                    expanded=False,
                )
            asst_idx += 1

# ── Input handling ─────────────────────────────────────────────────────────────
# 1) Quick query button
if send_quick and selected_quick != "—":
    _run_agent(selected_quick)
    st.rerun()

# 2) Chat input box
user_input = st.chat_input("Hỏi về quy định VinUni... (VD: 'Đạo văn bị xử lý thế nào?', 'Dùng ChatGPT làm bài có được không?')")
if user_input:
    _run_agent(user_input)
    st.rerun()

# ── Footer ─────────────────────────────────────────────────────────────────────
st.divider()
fc1, fc2, fc3 = st.columns([3, 3, 1])
with fc1:
    st.caption("🎓 **DAY04 Lab v2** — Research Agent Tool Eval")
with fc2:
    st.caption("👥 Nhóm **2A202601602** — VinUniversity 2026")
with fc3:
    st.caption(f"⏰ {datetime.now().strftime('%H:%M')}")
