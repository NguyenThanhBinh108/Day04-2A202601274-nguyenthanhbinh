from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from tools._shared import ROOT, err, fold_text, terms


POLICY_DIR = ROOT / "company_policy"

_NAV_LINE_RE = re.compile(r"^\s*[*\-+]?\s*\[[^\]]*\]\([^)]*\)\s*$")
_MD_NOISE_RE = re.compile(r"[*_#\\]+")

_MONTHS = "Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec"
_MONTH_NUM = {m: i + 1 for i, m in enumerate([
    "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
])}

# Ordered longest-pattern-first so alternation doesn't greedily match a
# sub-piece of a longer date expression (e.g. cross-month range before a
# bare single day-month token).
_DATE_RE = re.compile(
    rf"""
    (?P<slash_range>\d{{1,2}}/\d{{1,2}}/\d{{2,4}}\s*[–\-]\s*\d{{1,2}}/\d{{1,2}}/\d{{2,4}})
    |(?P<cross_month>\d{{1,2}}-(?:{_MONTHS})-\d{{1,2}}-(?:{_MONTHS}))
    |(?P<same_month>\d{{1,2}}(?:-\d{{1,2}})?-(?:{_MONTHS}))
    |(?P<slash_single>\d{{1,2}}/\d{{1,2}}/\d{{2,4}})
    """,
    re.VERBOSE,
)


def _is_deadline_doc(meta: dict[str, Any], path: Path) -> bool:
    tags = meta.get("tags") or []
    if not isinstance(tags, list):
        tags = [str(tags)]
    haystack = fold_text(" ".join([
        str(meta.get("doc_id") or path.stem),
        str(meta.get("title") or ""),
        " ".join(str(t) for t in tags),
    ]))
    return "deadline" in haystack or "calendar" in haystack or "key date" in haystack


def _parse_markdown_doc(path: Path) -> tuple[dict[str, Any], str]:
    raw = path.read_text(encoding="utf-8")
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) == 3:
            meta = yaml.safe_load(parts[1]) or {}
            return dict(meta), parts[2].strip()
    return {}, raw.strip()


def _strip_nav(body: str) -> str:
    lines = [ln for ln in body.splitlines() if not _NAV_LINE_RE.match(ln)]
    return "\n".join(lines)


def _clean_text(text: str) -> str:
    text = _MD_NOISE_RE.sub(" ", text)
    text = re.sub(r"\s+", " ", text).strip(" -–:–—")
    return text.strip()


def _iso_from_slash(token: str) -> str | None:
    """DD/MM/YYYY -> YYYY-MM-DD, assuming VN day/month order."""
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{2,4})", token)
    if not m:
        return None
    day, month, year = m.groups()
    if len(year) == 2:
        year = "20" + year
    try:
        return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
    except ValueError:
        return None


def _extract_events(text: str) -> list[dict[str, Any]]:
    matches = list(_DATE_RE.finditer(text))
    events: list[dict[str, Any]] = []
    for i, m in enumerate(matches):
        date_text = m.group().strip()
        prev_end = matches[i - 1].end() if i > 0 else max(0, m.start() - 80)
        next_start = matches[i + 1].start() if i + 1 < len(matches) else min(len(text), m.end() + 120)

        before = _clean_text(text[prev_end:m.start()])
        after = _clean_text(text[m.end():next_start])

        # "**Label:** 15/10/2025" style — prefer the label right before the date.
        label_before = ""
        raw_before = text[max(0, m.start() - 90):m.start()]
        raw_before_clean = re.sub(r"[*_]+", "", raw_before)
        colon_match = re.search(r"([A-ZÀ-Ỵ][^.:\n]{2,80}):\s*$", raw_before_clean.strip())
        if colon_match:
            label_before = _clean_text(colon_match.group(1))

        event = label_before or after or before
        # Trim runaway event text to a single sentence-ish chunk.
        event = event.split("  ")[0][:140].strip()

        if m.lastgroup == "slash_range":
            first, second = re.split(r"[–\-]", date_text)
            events.append({
                "date_text": date_text,
                "iso_start": _iso_from_slash(first.strip()),
                "iso_end": _iso_from_slash(second.strip()),
                "event": event,
            })
        elif m.lastgroup in ("slash_single",):
            events.append({
                "date_text": date_text,
                "iso_start": _iso_from_slash(date_text),
                "iso_end": None,
                "event": event,
            })
        else:
            # same_month / cross_month calendar-grid tokens have no explicit
            # year in the source text — best-effort only, flagged as such.
            events.append({
                "date_text": date_text,
                "iso_start": None,
                "iso_end": None,
                "event": event,
                "note": "year not present in source; day/month only",
            })
    return events


def search_policy_deadline(query: str = "", top_k: int = 15) -> dict[str, Any]:
    try:
        query_terms = terms(query)
        target_docs: list[dict[str, Any]] = []

        for path in sorted(POLICY_DIR.glob("*.md")):
            if path.name == "README.md":
                continue
            meta, body = _parse_markdown_doc(path)
            if not _is_deadline_doc(meta, path):
                continue
            body = _strip_nav(body)
            for event in _extract_events(body):
                if not event.get("event"):
                    continue
                target_docs.append({
                    "doc_id": meta.get("doc_id") or path.stem,
                    "title": str(meta.get("title") or path.stem),
                    "source": meta.get("source") or "Company Policy Handbook",
                    "source_url": meta.get("source_url"),
                    **event,
                })

        # De-dupe identical (date_text, event) pairs across a doc.
        seen: set[tuple[str, str, str]] = set()
        deduped: list[dict[str, Any]] = []
        for item in target_docs:
            key = (item["doc_id"], item["date_text"], item["event"])
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)

        if query_terms:
            filtered = [
                item for item in deduped
                if query_terms & terms(f"{item['event']} {item['title']}")
            ]
        else:
            filtered = deduped

        # Sort ISO-dated entries chronologically first; undated calendar-grid
        # entries keep source order and are appended after.
        dated = [e for e in filtered if e.get("iso_start")]
        undated = [e for e in filtered if not e.get("iso_start")]
        dated.sort(key=lambda e: e["iso_start"])

        results = (dated + undated)[: max(1, int(top_k or 15))]
        return {
            "tool": "search_policy_deadline",
            "query": query,
            "results": results,
            "freshness": "static_company_policy",
            "trust_boundary": "Dates/events are extracted heuristically from scraped policy markdown; verify against source_url before quoting as authoritative.",
            "scanned_docs": len(target_docs) and len({item["doc_id"] for item in target_docs}),
        }
    except Exception as exc:
        return err("search_policy_deadline", exc)
