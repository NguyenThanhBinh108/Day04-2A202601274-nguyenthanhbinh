"""app.py — Research Agent · DAY04 Lab v2
UI: Custom HTML/CSS/JS (premium dark SaaS design) injected into Streamlit shell.
Backend: run_model_tool_loop từ chat.py — không thay đổi.
Nhóm: 2A202601602 · VinUniversity
"""
from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path

import streamlit as st

from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import build_artifact_version
from chat import run_model_tool_loop

ROOT          = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS   = ROOT / "transcripts"
TRANSCRIPTS.mkdir(exist_ok=True)
load_lab_env(ROOT)

st.set_page_config(
    page_title="Research Agent · DAY04",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════════════════════════════════════
#  FULL CUSTOM CSS — Premium dark SaaS (inject at :root level)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,300;0,14..32,400;0,14..32,500;0,14..32,600;0,14..32,700;0,14..32,800;1,14..32,400&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
  /* Core palette */
  --ink-0:   #0a0c14;
  --ink-1:   #0d1117;
  --ink-2:   #111827;
  --ink-3:   #1c2333;
  --ink-4:   #243047;

  /* Borders */
  --line-0:  rgba(255,255,255,.05);
  --line-1:  rgba(255,255,255,.09);
  --line-2:  rgba(255,255,255,.14);

  /* Text */
  --t-0:  #f0f2ff;
  --t-1:  #a8b2cc;
  --t-2:  #5c6a8a;
  --t-3:  #2e3a54;

  /* Brand */
  --brand:        #7c6ef7;
  --brand-dim:    rgba(124,110,247,.14);
  --brand-glow:   rgba(124,110,247,.28);
  --brand-dark:   rgba(124,110,247,.08);

  /* Semantic */
  --green:   #22d3a0;
  --yellow:  #f5c542;
  --red:     #f06292;
  --blue:    #60aaff;

  /* Radii */
  --r1: 6px;
  --r2: 10px;
  --r3: 14px;
  --r4: 20px;

  /* Shadows */
  --shadow-sm: 0 2px 8px rgba(0,0,0,.5);
  --shadow-md: 0 8px 32px rgba(0,0,0,.6);
  --shadow-glow: 0 0 32px var(--brand-glow);
}

/* ── Kill all Streamlit chrome ── */
*, *::before, *::after { box-sizing: border-box; }
#MainMenu, footer, header,
div[data-testid="stToolbar"],
div[data-testid="stDecoration"],
div[data-testid="stStatusWidget"],
div[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"] { display: none !important; }

html, body {
  font-family: 'Inter', system-ui, sans-serif !important;
  background: var(--ink-0) !important;
  color: var(--t-0) !important;
  height: 100%;
}

.stApp,
div[data-testid="stAppViewContainer"],
div[data-testid="stMain"],
section[data-testid="stMain"] > div {
  font-family: 'Inter', sans-serif !important;
  background: var(--ink-0) !important;
  color: var(--t-0) !important;
}

.block-container {
  padding: 0 !important;
  max-width: 100% !important;
}

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] {
  background: var(--ink-1) !important;
  border-right: 1px solid var(--line-1) !important;
  width: 280px !important;
  min-width: 280px !important;
}
section[data-testid="stSidebar"] > div:first-child {
  padding: 0 !important;
  overflow-y: auto;
  overflow-x: hidden;
  height: 100vh;
}
section[data-testid="stSidebar"]::-webkit-scrollbar { width: 2px; }
section[data-testid="stSidebar"]::-webkit-scrollbar-thumb { background: var(--line-2); }

/* Sidebar text */
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span:not([data-baseweb]) {
  color: var(--t-1) !important;
  font-size: 12px !important;
  font-family: 'Inter', sans-serif !important;
}

/* Selectbox */
section[data-testid="stSidebar"] div[data-baseweb="select"] > div:first-child {
  background: var(--ink-3) !important;
  border: 1px solid var(--line-1) !important;
  border-radius: var(--r2) !important;
  color: var(--t-0) !important;
  font-size: 13px !important;
  transition: border-color .15s;
}
section[data-testid="stSidebar"] div[data-baseweb="select"] > div:first-child:focus-within {
  border-color: var(--brand) !important;
  box-shadow: 0 0 0 2px var(--brand-dim) !important;
}

/* ── Slider: force brand color ── */
section[data-testid="stSidebar"] div[role="slider"] {
  background: var(--brand) !important;
  border: 2px solid var(--brand) !important;
  box-shadow: 0 0 0 4px var(--brand-dim) !important;
}
section[data-testid="stSidebar"] [data-baseweb="slider"] > div:first-child {
  background: var(--line-2) !important;
}
section[data-testid="stSidebar"] [data-baseweb="slider"] > div:first-child > div:first-child {
  background: var(--brand) !important;
}
section[data-testid="stSidebar"] [data-baseweb="slider"] * { --color-primary: var(--brand) !important; }
*[style*="background-color: rgb(255, 75, 75)"] { background-color: var(--brand) !important; }
*[style*="border-color: rgb(255, 75, 75)"]     { border-color:     var(--brand) !important; }

/* Sidebar buttons */
section[data-testid="stSidebar"] .stButton > button {
  width: 100%;
  background: var(--ink-3) !important;
  border: 1px solid var(--line-0) !important;
  border-radius: var(--r2) !important;
  color: var(--t-1) !important;
  font-size: 12px !important;
  font-family: 'Inter', sans-serif !important;
  padding: 7px 12px !important;
  text-align: left !important;
  transition: all .14s !important;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
section[data-testid="stSidebar"] .stButton > button:hover {
  background: var(--brand-dark) !important;
  border-color: var(--brand) !important;
  color: var(--t-0) !important;
}

/* Expander */
section[data-testid="stSidebar"] div[data-testid="stExpander"] {
  background: var(--ink-3) !important;
  border: 1px solid var(--line-1) !important;
  border-radius: var(--r2) !important;
  margin: 4px 0 !important;
}
section[data-testid="stSidebar"] div[data-testid="stExpander"] summary {
  color: var(--t-1) !important;
  font-size: 12px !important;
}

/* ── CHAT INPUT + BOTTOM BAR ── */
div[data-testid="stBottom"],
div[data-testid="stBottom"] > div,
div[data-testid="stBottom"] > div > div {
  background: var(--ink-0) !important;
  background-color: var(--ink-0) !important;
}
div[data-testid="stBottom"] {
  border-top: 1px solid var(--line-1) !important;
  padding: 14px 2rem 10px !important;
}
div[data-testid="stChatInput"] {
  background: var(--ink-2) !important;
  border: 1px solid var(--line-2) !important;
  border-radius: 14px !important;
  padding: 6px 8px !important;
  box-shadow: var(--shadow-sm) !important;
  transition: border-color .15s, box-shadow .15s !important;
}
div[data-testid="stChatInput"]:focus-within {
  border-color: var(--brand) !important;
  box-shadow: 0 0 0 3px var(--brand-dim), var(--shadow-sm) !important;
}
div[data-testid="stChatInput"] > div,
div[data-testid="stChatInput"] > div > div,
div[data-testid="stChatInput"] [data-baseweb="base-input"],
div[data-testid="stChatInput"] [data-baseweb="textarea"] {
  background: transparent !important;
  background-color: transparent !important;
}
div[data-testid="stChatInput"] textarea {
  background: transparent !important;
  color: var(--t-0) !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 14px !important;
  caret-color: var(--brand) !important;
  border: none !important;
  outline: none !important;
  box-shadow: none !important;
}
div[data-testid="stChatInput"] textarea::placeholder { color: var(--t-2) !important; }
div[data-testid="stChatInput"] button {
  background: var(--brand) !important;
  background-color: var(--brand) !important;
  border: none !important;
  border-radius: 10px !important;
  color: #fff !important;
  transition: all .14s !important;
  box-shadow: 0 2px 8px var(--brand-glow) !important;
}
div[data-testid="stChatInput"] button:hover {
  background: #6a5be0 !important;
  background-color: #6a5be0 !important;
  box-shadow: 0 4px 16px var(--brand-glow) !important;
  transform: scale(1.04);
}
div[data-testid="stChatInput"] button:disabled {
  background: var(--ink-3) !important;
  background-color: var(--ink-3) !important;
  box-shadow: none !important;
  color: var(--t-2) !important;
}

/* chat messages */
div[data-testid="stChatMessage"] {
  background: transparent !important;
  border: none !important;
  padding: 0 !important;
  margin: 0 !important;
}

/* expander main area */
div[data-testid="stExpander"] {
  background: var(--ink-2) !important;
  border: 1px solid var(--line-1) !important;
  border-radius: var(--r2) !important;
  margin: 4px 0 !important;
}
div[data-testid="stExpander"] summary { color: var(--t-2) !important; font-size: 11px !important; }

/* code */
pre, code, .stCode {
  font-family: 'JetBrains Mono', monospace !important;
  background: var(--ink-0) !important;
  border: 1px solid var(--line-1) !important;
  color: var(--t-1) !important;
  border-radius: var(--r1) !important;
  font-size: 11px !important;
}

/* spinner */
.stSpinner > div { border-top-color: var(--brand) !important; }

/* ── CUSTOM COMPONENTS ── */

/* ---- App Shell ---- */
.app-shell {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 80px);
  padding: 0 2rem;
}

/* ---- Topbar ---- */
.topbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 0 14px;
  border-bottom: 1px solid var(--line-1);
  margin-bottom: 0;
  flex-shrink: 0;
}
.topbar-left { display: flex; align-items: center; gap: 12px; }
.tb-logo {
  width: 34px; height: 34px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 60%, #c084fc 100%);
  border-radius: 9px;
  display: flex; align-items: center; justify-content: center;
  font-size: 17px;
  box-shadow: 0 0 20px rgba(99,102,241,.35);
  flex-shrink: 0;
}
.tb-title { font-size: 16px; font-weight: 700; color: var(--t-0); letter-spacing: -.35px; }
.tb-sub   { font-size: 11px; color: var(--t-2); margin-top: 1px; }
.topbar-right { display: flex; align-items: center; gap: 8px; }
.tag {
  display: flex; align-items: center; gap: 5px;
  background: var(--ink-2); border: 1px solid var(--line-1);
  border-radius: 20px; padding: 4px 10px;
  font-size: 11px; color: var(--t-1);
}
.tag-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--green); flex-shrink: 0;
}
.tag-dot.spin { background: var(--yellow); animation: pulse 1s ease-in-out infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }

/* ---- Stats strip ---- */
.stats-strip {
  display: flex; gap: 0;
  border-bottom: 1px solid var(--line-1);
  flex-shrink: 0;
}
.stat-item {
  flex: 1; display: flex; align-items: center; gap: 10px;
  padding: 11px 16px;
  border-right: 1px solid var(--line-0);
  transition: background .15s;
}
.stat-item:last-child { border-right: none; }
.stat-item:hover { background: var(--ink-2); }
.st-icon {
  width: 30px; height: 30px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; flex-shrink: 0;
}
.si-purple { background: rgba(124,110,247,.12); }
.si-green  { background: rgba(34,211,160,.08); }
.si-blue   { background: rgba(96,170,255,.08); }
.si-yellow { background: rgba(245,197,66,.07); }
.st-info { min-width: 0; }
.st-label { font-size: 9px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: var(--t-3); }
.st-val   { font-size: 18px; font-weight: 700; color: var(--t-0); letter-spacing: -.4px; line-height: 1.1; }
.st-val.sm { font-size: 13px; font-weight: 600; letter-spacing: 0; margin-top: 1px; }

/* ---- Conversation ---- */
.conv-area {
  flex: 1;
  overflow-y: auto;
  padding: 20px 0;
  scrollbar-width: thin;
  scrollbar-color: var(--line-1) transparent;
}
.conv-area::-webkit-scrollbar { width: 3px; }
.conv-area::-webkit-scrollbar-thumb { background: var(--line-1); border-radius: 2px; }

/* ---- Empty state ---- */
.empty-wrap {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; min-height: 380px; text-align: center;
  padding: 40px 24px;
}
.empty-orb {
  width: 72px; height: 72px; border-radius: 22px;
  background: linear-gradient(135deg, rgba(99,102,241,.15), rgba(139,92,246,.1));
  border: 1px solid rgba(124,110,247,.25);
  display: flex; align-items: center; justify-content: center;
  font-size: 32px; margin-bottom: 20px;
  box-shadow: 0 0 40px rgba(124,110,247,.12);
  animation: float 4s ease-in-out infinite;
}
@keyframes float { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-6px)} }
.empty-h  { font-size: 20px; font-weight: 700; color: var(--t-0); margin-bottom: 10px; letter-spacing: -.4px; }
.empty-p  { font-size: 13px; color: var(--t-1); max-width: 360px; line-height: 1.75; margin-bottom: 28px; }
.chips    { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; max-width: 480px; width: 100%; }
.chip {
  background: var(--ink-2); border: 1px solid var(--line-1);
  border-radius: 12px; padding: 12px 16px;
  font-size: 12px; color: var(--t-1); text-align: left; line-height: 1.5;
  cursor: pointer; transition: all .15s;
}
.chip:hover { border-color: var(--brand); color: var(--t-0); background: var(--brand-dark); }
.chip-em { font-size: 16px; display: block; margin-bottom: 4px; }

/* ---- Messages ---- */
.msg-row { display: flex; margin: 14px 0; align-items: flex-start; gap: 10px; }
.msg-row.user-row { flex-direction: row-reverse; }

.msg-avatar {
  width: 32px; height: 32px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 15px;
}
.av-user { background: linear-gradient(135deg, #6366f1, #8b5cf6); box-shadow: 0 0 12px rgba(99,102,241,.3); }
.av-bot  { background: var(--ink-3); border: 1px solid var(--line-1); }

.msg-body { max-width: 68%; display: flex; flex-direction: column; gap: 2px; }
.user-row .msg-body { align-items: flex-end; }

.msg-bubble {
  padding: 11px 15px; border-radius: 16px;
  font-size: 14px; line-height: 1.7; word-break: break-word;
}
.bubble-user {
  background: linear-gradient(135deg, #5a52e0, #7c6ef7);
  color: #fff;
  border-bottom-right-radius: 4px;
  box-shadow: 0 4px 16px rgba(124,110,247,.3);
}
.bubble-bot {
  background: var(--ink-2);
  border: 1px solid var(--line-1);
  color: var(--t-0);
  border-bottom-left-radius: 4px;
}
.bubble-err {
  background: rgba(240,98,146,.07);
  border: 1px solid rgba(240,98,146,.2);
  color: var(--t-0);
  border-bottom-left-radius: 4px;
}
.msg-time { font-size: 9px; color: var(--t-3); padding: 0 4px; }

/* ---- Thinking ---- */
.thinking-row { display: flex; align-items: flex-start; gap: 10px; margin: 14px 0; }
.think-bubble {
  background: var(--ink-2); border: 1px solid var(--line-1);
  border-radius: 16px; border-bottom-left-radius: 4px;
  padding: 12px 18px; display: flex; align-items: center; gap: 5px;
}
.tdot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--brand); animation: bounce 1.3s ease-in-out infinite;
}
.tdot:nth-child(2) { animation-delay: .18s; }
.tdot:nth-child(3) { animation-delay: .36s; }
@keyframes bounce { 0%,100%{transform:translateY(0);opacity:.5} 50%{transform:translateY(-6px);opacity:1} }

/* ---- Tool timeline ---- */
.tool-block { margin-top: 8px; }
.tool-line {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 8px 12px; margin-bottom: 5px;
  background: var(--ink-0);
  border: 1px solid var(--line-1);
  border-left: 3px solid var(--line-2);
  border-radius: var(--r2); font-size: 12px;
}
.tool-line.ok   { border-left-color: var(--green); }
.tool-line.err  { border-left-color: var(--red);   background: rgba(240,98,146,.04); }
.tool-line.warn { border-left-color: var(--yellow); background: rgba(245,197,66,.04); }
.tl-icon  { font-size: 13px; line-height: 1.5; flex-shrink: 0; }
.tl-name  { font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 600; color: var(--brand); }
.tl-sum   { color: var(--t-1); margin-top: 1px; }
.tl-err   { color: var(--red); margin-top: 1px; }

/* ---- Error box ---- */
.err-box {
  background: rgba(240,98,146,.06);
  border: 1px solid rgba(240,98,146,.2);
  border-left: 3px solid var(--red);
  border-radius: var(--r2);
  padding: 12px 16px; margin: 4px 0;
}
.err-head { font-size: 13px; font-weight: 600; color: var(--red); margin-bottom: 4px; }
.err-body { font-size: 11px; color: var(--t-1); font-family: 'JetBrains Mono', monospace; word-break: break-all; }
.err-tip  { font-size: 11px; color: var(--t-2); margin-top: 8px; }

/* ---- Sidebar custom ---- */
.sb-head { padding: 16px; border-bottom: 1px solid var(--line-1); display: flex; align-items: center; gap: 10px; }
.sb-logo-sm { width: 34px; height: 34px; border-radius: 9px; background: linear-gradient(135deg,#6366f1,#8b5cf6); display: flex; align-items: center; justify-content: center; font-size: 16px; flex-shrink: 0; }
.sb-nm   { font-size: 13px; font-weight: 700; color: var(--t-0) !important; line-height: 1.2; }
.sb-sub2 { font-size: 10px; color: var(--t-3) !important; }
.sb-sect { padding: 12px 16px 10px; border-bottom: 1px solid var(--line-0); }
.sb-ttl  { font-size: 9px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; color: var(--t-3) !important; margin-bottom: 10px; }
.hash-l  { font-size: 9px; color: var(--t-3); }
.hash-v  {
  font-family: 'JetBrains Mono', monospace; font-size: 10px; color: var(--brand);
  background: var(--brand-dark); border: 1px solid rgba(124,110,247,.15);
  border-radius: 5px; padding: 2px 7px; display: block; word-break: break-all;
  margin: 2px 0 6px; cursor: pointer;
  transition: border-color .14s;
}
.hash-v:hover { border-color: var(--brand); }
.sb-foot { padding: 10px 16px; font-size: 10px; color: var(--t-3); border-top: 1px solid var(--line-0); text-align: center; }

/* hint below input */
.input-hint { text-align: center; font-size: 10px; color: var(--t-3); padding-top: 4px; }

/* ── RESPONSIVE ── */
@media (max-width: 1100px) {
  .stats-strip { flex-wrap: wrap; }
  .stat-item { min-width: 50%; border-right-width: 0; }
}
@media (max-width: 700px) {
  .chips { grid-template-columns: 1fr; }
  .msg-body { max-width: 90%; }
  .app-shell { padding: 0 1rem; }
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
if "messages"     not in st.session_state: st.session_state.messages     = []
if "tool_history" not in st.session_state: st.session_state.tool_history = []
if "is_running"   not in st.session_state: st.session_state.is_running   = False

# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div class="sb-head">
      <div class="sb-logo-sm">🔍</div>
      <div>
        <div class="sb-nm">Research Agent</div>
        <div class="sb-sub2">DAY04 · Nhóm 2A202601602</div>
      </div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="sb-sect"><div class="sb-ttl">⚙ Cấu hình</div>', unsafe_allow_html=True)
    provider_name = st.selectbox("Provider", ["gemini", "openrouter", "openai", "anthropic"], index=0)
    version_label = st.selectbox("Version",  ["v0", "v1", "v2", "v3"], index=2)
    max_rounds    = st.slider("Max Tool Rounds", 1, 8, 4)
    st.caption(f"{max_rounds} rounds")
    st.markdown('</div>', unsafe_allow_html=True)

    # Artifact hashes
    st.markdown('<div class="sb-sect"><div class="sb-ttl">🔐 Artifact Hashes</div>', unsafe_allow_html=True)
    try:
        av = build_artifact_version(version_label, ARTIFACTS_DIR/"system_prompt.md", ARTIFACTS_DIR/"tools.yaml")
        st.markdown(f"""
        <div class="hash-l">Version ID</div><div class="hash-v" title="click to copy">{av.artifact_version}</div>
        <div class="hash-l">Prompt SHA</div><div class="hash-v">{av.prompt_hash[:32]}…</div>
        <div class="hash-l">Tools SHA</div><div class="hash-v">{av.tools_hash[:32]}…</div>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.caption(f"N/A: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

    # Quick queries
    st.markdown('<div class="sb-sect"><div class="sb-ttl">⚡ Câu hỏi mẫu</div>', unsafe_allow_html=True)
    QUICK = [
        ("🐦", "Tweet mới nhất của Sam Altman?"),
        ("📰", "Tin tức AI hôm nay có gì nổi bật?"),
        ("🔗", "Tóm tắt: https://openai.com/blog"),
        ("🌐", "GPT-5 đang trending trên Twitter?"),
        ("📋", "Chính sách đạo văn VinUni là gì?"),
        ("🌤", "Thời tiết Hà Nội hôm nay?"),
        ("📡", "Gửi daily digest lên Telegram"),
        ("📚", "Paper về LLM agents gần nhất?"),
    ]
    for icon, label in QUICK:
        if st.button(f"{icon}  {label}", key=f"q_{label[:16]}"):
            st.session_state["_q"] = label
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div style="padding:8px 16px;">', unsafe_allow_html=True)
    if st.button("🗑  Xóa hội thoại", key="btn_clear"):
        st.session_state.messages     = []
        st.session_state.tool_history = []
        st.session_state.is_running   = False
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    turns = sum(1 for m in st.session_state.messages if m["role"] == "user")
    tools = sum(len(e) for e in st.session_state.tool_history)
    st.markdown(
        f'<div class="sb-foot">{turns} turns · {tools} tool calls · {datetime.now().strftime("%H:%M")}</div>',
        unsafe_allow_html=True,
    )

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN WORKSPACE
# ══════════════════════════════════════════════════════════════════════════════
total_turns = sum(1 for m in st.session_state.messages if m["role"] == "user")
total_tools = sum(len(e) for e in st.session_state.tool_history)
dot_cls     = "spin" if st.session_state.is_running else ""
dot_txt     = "Đang xử lý…" if st.session_state.is_running else f"{provider_name} · {version_label}"

st.markdown(f"""
<div class="app-shell">

<!-- ── Topbar ── -->
<div class="topbar">
  <div class="topbar-left">
    <div class="tb-logo">🤖</div>
    <div>
      <div class="tb-title">Research Agent</div>
      <div class="tb-sub">DAY04 Lab v2 · Evidence-driven tool routing · Prompt engineering</div>
    </div>
  </div>
  <div class="topbar-right">
    <div class="tag">
      <span class="tag-dot {dot_cls}"></span>
      <span>{dot_txt}</span>
    </div>
  </div>
</div>

<!-- ── Stats strip ── -->
<div class="stats-strip">
  <div class="stat-item">
    <div class="st-icon si-purple">💬</div>
    <div class="st-info"><div class="st-label">Turns</div><div class="st-val">{total_turns}</div></div>
  </div>
  <div class="stat-item">
    <div class="st-icon si-green">🛠</div>
    <div class="st-info"><div class="st-label">Tool Calls</div><div class="st-val">{total_tools}</div></div>
  </div>
  <div class="stat-item">
    <div class="st-icon si-blue">🏷</div>
    <div class="st-info"><div class="st-label">Version</div><div class="st-val sm">{version_label}</div></div>
  </div>
  <div class="stat-item">
    <div class="st-icon si-yellow">⚡</div>
    <div class="st-info"><div class="st-label">Provider</div><div class="st-val sm">{provider_name}</div></div>
  </div>
</div>

<!-- ── Conversation area ── -->
<div class="conv-area">
""", unsafe_allow_html=True)

# ─── Helper: tool card HTML ────────────────────────────────────────────────────
def _tool_html(events: list[dict]) -> str:
    if not events:
        return ""
    rows = ""
    for ev in events:
        name = ev.get("tool", "?")
        res  = ev.get("result", {})
        if res.get("awaiting_user"):
            cls, icon, summ = "warn", "⏸", f"Chờ: {res.get('question','')[:70]}"
        elif res.get("error"):
            cls, icon, summ = "err", "✗", f"{res['error']}: {res.get('message','')[:60]}"
        elif curr := res.get("current"):
            cls, icon, summ = "ok", "✓", f"{res.get('location','')} · {curr.get('temperature_c','?')}°C · {curr.get('weather_description','')}"
        else:
            items = res.get("items") or res.get("results") or []
            cnt   = len(items) if isinstance(items, list) else "—"
            cls, icon, summ = "ok", "✓", f"{cnt} kết quả"

        extra = f'<div class="tl-err">{res.get("message","")[:80]}</div>' if res.get("error") else ""
        rows += f"""
        <div class="tool-line {cls}">
          <div class="tl-icon">{icon}</div>
          <div>
            <div class="tl-name">{name}</div>
            <div class="tl-sum">{summ}</div>
            {extra}
          </div>
        </div>"""
    return f'<div class="tool-block">{rows}</div>'


def _err_html(raw: str) -> str:
    hint = ""
    if "429" in raw or "RESOURCE_EXHAUSTED" in raw or "quota" in raw.lower():
        hint = "⏱ Rate limit Gemini (15 req/phút). Chờ ~60s rồi thử lại."
    elif "402" in raw or "insufficient credits" in raw.lower():
        hint = "💡 OpenRouter hết credits. Đổi sang Gemini trong sidebar."
    elif "401" in raw or "unauthorized" in raw.lower():
        hint = "💡 API key không hợp lệ. Kiểm tra file .env"
    tip = f'<div class="err-tip">{hint}</div>' if hint else ""
    return f"""
    <div class="err-box">
      <div class="err-head">❌ Lỗi từ provider</div>
      <div class="err-body">{raw[:320]}</div>
      {tip}
    </div>"""


# ─── Render messages ───────────────────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown("""
    <div class="empty-wrap">
      <div class="empty-orb">🔭</div>
      <div class="empty-h">Bắt đầu phiên nghiên cứu</div>
      <div class="empty-p">
        Đặt câu hỏi, cung cấp URL hoặc chọn gợi ý bên dưới.<br>
        Agent tự xác định công cụ phù hợp và hiển thị toàn bộ quá trình xử lý.
      </div>
      <div class="chips">
        <div class="chip"><span class="chip-em">🐦</span>Tweet mới nhất của Sam Altman?</div>
        <div class="chip"><span class="chip-em">📰</span>Tin tức AI nổi bật hôm nay?</div>
        <div class="chip"><span class="chip-em">🌤</span>Thời tiết Hà Nội hôm nay?</div>
        <div class="chip"><span class="chip-em">📋</span>Chính sách đạo văn VinUni?</div>
      </div>
    </div>""", unsafe_allow_html=True)
else:
    asst_idx = 0
    for msg in st.session_state.messages:
        role    = msg["role"]
        content = msg["content"]

        if role == "user":
            st.markdown(f"""
            <div class="msg-row user-row">
              <div class="msg-avatar av-user">🧑</div>
              <div class="msg-body">
                <div class="msg-bubble bubble-user">{content}</div>
              </div>
            </div>""", unsafe_allow_html=True)

        elif role == "assistant":
            is_err = content.startswith("❌ Lỗi:")
            if is_err:
                raw      = content[len("❌ Lỗi:"):].strip()
                inner    = _err_html(raw)
                bub_cls  = "bubble-err"
            else:
                inner   = content
                bub_cls = "bubble-bot"

            tool_html = _tool_html(
                st.session_state.tool_history[asst_idx]
                if asst_idx < len(st.session_state.tool_history) else []
            )

            if is_err:
                st.markdown(f"""
                <div class="msg-row">
                  <div class="msg-avatar av-bot">🤖</div>
                  <div class="msg-body">
                    {inner}
                    {tool_html}
                  </div>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="msg-row">
                  <div class="msg-avatar av-bot">🤖</div>
                  <div class="msg-body">
                    <div class="msg-bubble bubble-bot">{inner}</div>
                    {tool_html}
                  </div>
                </div>""", unsafe_allow_html=True)

            asst_idx += 1

    if st.session_state.is_running:
        st.markdown("""
        <div class="thinking-row">
          <div class="msg-avatar av-bot">🤖</div>
          <div class="think-bubble">
            <div class="tdot"></div>
            <div class="tdot"></div>
            <div class="tdot"></div>
          </div>
        </div>""", unsafe_allow_html=True)

# Close conv-area + app-shell
st.markdown("</div></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  AGENT LOGIC
# ══════════════════════════════════════════════════════════════════════════════
def _run(text: str) -> None:
    st.session_state.messages.append({"role": "user", "content": text})
    st.session_state.is_running = True
    st.rerun()


def _is_rate_limit(exc: Exception) -> bool:
    s = str(exc)
    return "429" in s or "RESOURCE_EXHAUSTED" in s or "quota" in s.lower()


def _execute() -> None:
    last = next((m["content"] for m in reversed(st.session_state.messages) if m["role"] == "user"), None)
    if not last:
        st.session_state.is_running = False
        return

    RETRY, WAIT = 2, 12
    try:
        sp   = (ARTIFACTS_DIR / "system_prompt.md").read_text(encoding="utf-8")
        decl = load_tool_declarations(ARTIFACTS_DIR / "tools.yaml")
        ctx  = [{"role": "system", "content": sp}, *st.session_state.messages]
        prov = make_provider(provider_name)
        t0   = time.time()

        loop, last_exc = None, None
        for attempt in range(RETRY + 1):
            try:
                loop     = run_model_tool_loop(provider=prov, messages=ctx,
                                               tools=to_openai_tools(decl),
                                               model=None, max_tool_rounds=max_rounds)
                last_exc = None; break
            except Exception as exc:
                last_exc = exc
                if _is_rate_limit(exc) and attempt < RETRY:
                    ph = st.empty()
                    for r in range(WAIT, 0, -1):
                        ph.info(f"⏱ Rate limit — chờ {r}s rồi thử lại ({attempt+1}/{RETRY})…")
                        time.sleep(1)
                    ph.empty()
                else:
                    raise
        if last_exc: raise last_exc

        text        = loop.get("assistant_text", "")       # type: ignore
        tool_events = loop.get("tool_events", [])
        rounds      = loop.get("rounds", [])
        status      = loop.get("status", "answered")
        elapsed     = time.time() - t0

        st.session_state.messages.append({"role": "assistant", "content": text})
        st.session_state.tool_history.append(tool_events)

        try:
            ts  = datetime.now().strftime("%Y%m%dT%H%M%S")
            av2 = build_artifact_version(version_label, ARTIFACTS_DIR/"system_prompt.md", ARTIFACTS_DIR/"tools.yaml")
            (TRANSCRIPTS / f"{ts}_ui_{version_label}.transcript.json").write_text(
                json.dumps({"version": version_label, "artifact_version": av2.artifact_version,
                            "provider": provider_name, "timestamp": ts, "query": last,
                            "assistant_text": text, "tool_events": tool_events,
                            "rounds": len(rounds), "status": status,
                            "elapsed_s": round(elapsed, 2)},
                           ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    except Exception as exc:
        st.session_state.messages.append({"role": "assistant", "content": f"❌ Lỗi: {exc}"})
        st.session_state.tool_history.append([])
    finally:
        st.session_state.is_running = False


if st.session_state.is_running:
    _execute()
    st.rerun()

q = st.session_state.pop("_q", None)
if q and not st.session_state.is_running:
    _run(q)

# ── Composer ─────────────────────────────────────────────────────────────────
prompt = st.chat_input(
    "Nhập câu hỏi… (Enter gửi · Shift+Enter xuống dòng)",
    disabled=st.session_state.is_running,
)
if prompt and not st.session_state.is_running:
    _run(prompt)

st.markdown('<div class="input-hint">Enter gửi · Shift+Enter xuống dòng · Gemini free: 15 req/min</div>',
            unsafe_allow_html=True)
