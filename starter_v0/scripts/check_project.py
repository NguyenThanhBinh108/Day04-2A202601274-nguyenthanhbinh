"""check_project.py — Kiểm tra toàn bộ project trước khi nộp bài.

Chạy: python scripts/check_project.py
Từ thư mục: starter_v0/
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # starter_v0/

PASS = "✅"
FAIL = "❌"
WARN = "⚠️ "

errors   : list[str] = []
warnings : list[str] = []


def check(label: str, cond: bool, detail: str = "", is_warning: bool = False) -> None:
    if cond:
        print(f"  {PASS} {label}")
    else:
        icon = WARN if is_warning else FAIL
        msg = f"{label}" + (f" — {detail}" if detail else "")
        print(f"  {icon} {msg}")
        (warnings if is_warning else errors).append(msg)


# ── 1. Required files ──────────────────────────────────────────────────────────
print("\n📁 1. Required files")
required_files = [
    "artifacts/system_prompt.md",
    "artifacts/tools.yaml",
    "artifacts/version_log.csv",
    "artifacts/REPORT.md",
    "data/eval_base.json",
    "data/eval_group.json",
    "app.py",
    "requirements.txt",
    "tools/weather/TOOL.md",
    "tools/weather/tool.py",
]
for rel in required_files:
    p = ROOT / rel
    check(rel, p.exists(), "file missing")

# ── 2. Dirs for output ─────────────────────────────────────────────────────────
print("\n📂 2. Output directories")
for rel in ["runs", "transcripts", "analysis"]:
    check(rel + "/", (ROOT / rel).is_dir(), "directory missing")

# ── 3. eval_group.json — 10 cases ─────────────────────────────────────────────
print("\n🧪 3. eval_group.json")
try:
    eg = json.loads((ROOT / "data/eval_group.json").read_text(encoding="utf-8"))
    cases   = eg.get("cases", [])
    single  = [c for c in cases if "query" in c]
    multi   = [c for c in cases if "turns" in c]
    check("Total cases == 10", len(cases) == 10, f"found {len(cases)}")
    check("5 single-turn (query)", len(single) == 5, f"found {len(single)}")
    check("5 multi-turn (turns)",  len(multi)  == 5, f"found {len(multi)}")
    # Check multi-turn last turn is user
    for c in multi:
        last_role = c["turns"][-1].get("role")
        check(
            f"{c['id']}: last turn is user",
            last_role == "user",
            f"got role={last_role!r}",
        )
    # Check all have required fields
    required_case_fields = {"id", "phase", "failure_type", "expect", "metadata"}
    for c in cases:
        missing = required_case_fields - set(c.keys())
        check(f"{c.get('id','?')}: has required fields", not missing, f"missing {missing}")
    # Check failure_types are valid
    allowed_ft = {"wrong_tool", "wrong_arg_value", "wrong_boundary", "unnecessary_tool", "out_of_scope", "missing_info"}
    for c in cases:
        ft = c.get("failure_type")
        check(f"{c.get('id','?')}: valid failure_type", ft in allowed_ft, f"got {ft!r}")
except Exception as exc:
    errors.append(f"eval_group.json parse error: {exc}")
    print(f"  {FAIL} eval_group.json parse error: {exc}")

# ── 4. tools.yaml — weather declared ──────────────────────────────────────────
print("\n🛠  4. tools.yaml")
try:
    import yaml
    tools_data = yaml.safe_load((ROOT / "artifacts/tools.yaml").read_text(encoding="utf-8"))
    tool_names = [t["name"] for t in tools_data.get("tools", [])]
    core_required = ["clarify", "timeline", "social_search", "lookup", "fetch", "format"]
    for name in core_required:
        check(f"core tool '{name}' declared", name in tool_names)
    check("weather tool declared", "weather" in tool_names)
    check(f"total tools >= 5", len(tool_names) >= 5, f"found {len(tool_names)}")
    print(f"     Declared tools: {tool_names}")
except Exception as exc:
    errors.append(f"tools.yaml parse error: {exc}")
    print(f"  {FAIL} tools.yaml parse error: {exc}")

# ── 5. tools/__init__.py — weather registered ─────────────────────────────────
print("\n🔗 5. tools/__init__.py")
try:
    init_text = (ROOT / "tools/__init__.py").read_text(encoding="utf-8")
    check("imports weather", "from .weather.tool import" in init_text)
    check("registers weather", '"weather"' in init_text or "'weather'" in init_text)
except Exception as exc:
    errors.append(f"tools/__init__.py read error: {exc}")

# ── 6. system_prompt.md — not the broken baseline ─────────────────────────────
print("\n📝 6. system_prompt.md (not broken baseline)")
try:
    sp = (ROOT / "artifacts/system_prompt.md").read_text(encoding="utf-8")
    bad_phrases = [
        "hates being asked questions",
        "just go ahead and do it",
        "make a sensible guess",
    ]
    for phrase in bad_phrases:
        check(f"no broken phrase: '{phrase[:40]}'", phrase not in sp, "baseline broken prompt detected")
    check("has clarify rules", "clarify" in sp.lower(), "no clarify mentioned")
    check("has out-of-scope rule", "scope" in sp.lower() or "out of scope" in sp.lower())
except Exception as exc:
    errors.append(f"system_prompt.md read error: {exc}")

# ── 7. requirements.txt — streamlit present ───────────────────────────────────
print("\n📦 7. requirements.txt")
try:
    req = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    check("streamlit >= 1.30.0", "streamlit" in req)
    check("requests present", "requests" in req)
    check("PyYAML present", "PyYAML" in req or "pyyaml" in req.lower())
except Exception as exc:
    errors.append(f"requirements.txt read error: {exc}")

# ── 8. version_log.csv — has content ──────────────────────────────────────────
print("\n📊 8. version_log.csv")
try:
    vl = (ROOT / "artifacts/version_log.csv").read_text(encoding="utf-8").strip().splitlines()
    check("has header row", len(vl) >= 1)
    check("has data rows (v0-v3 placeholder or real)", len(vl) >= 2,
          f"only {len(vl)} line(s) — fill after running eval", is_warning=True)
except Exception as exc:
    errors.append(f"version_log.csv read error: {exc}")

# ── 9. .env NOT committed ─────────────────────────────────────────────────────
print("\n🔑 9. Security")
env_file = ROOT / ".env"
gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8") if (ROOT / ".gitignore").exists() else ""
check(".env in .gitignore", ".env" in gitignore)
check(".env exists locally (not committed)", env_file.exists(), is_warning=True)

# ── 10. app.py — correct build_artifact_version call ─────────────────────────
print("\n🖥  10. app.py")
try:
    app_text = (ROOT / "app.py").read_text(encoding="utf-8")
    check("imports run_model_tool_loop from chat", "from chat import run_model_tool_loop" in app_text)
    check("uses build_artifact_version correctly", "build_artifact_version(version_label" in app_text)
    check("saves transcripts", "transcript" in app_text.lower())
except Exception as exc:
    errors.append(f"app.py read error: {exc}")

# ── Summary ───────────────────────────────────────────────────────────────────
print("\n" + "="*55)
if errors:
    print(f"❌ FAIL — {len(errors)} error(s), {len(warnings)} warning(s)")
    for e in errors:
        print(f"   • {e}")
    sys.exit(1)
elif warnings:
    print(f"⚠️  PASS with {len(warnings)} warning(s) — review before submit")
    for w in warnings:
        print(f"   • {w}")
    sys.exit(0)
else:
    print("✅ ALL CHECKS PASSED — project ready")
    sys.exit(0)
