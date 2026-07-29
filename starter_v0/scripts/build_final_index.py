"""
build_final_index.py  —  Bước 3 / 3
=====================================
Tạo index chất lượng cao + README chính thức cho company_policy/.
Báo cáo đầy đủ coverage, links nguồn, verification test.
"""
from __future__ import annotations

import re
import json
import yaml
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime

ROOT       = Path(__file__).parent.parent
POLICY_DIR = ROOT / "company_policy"

AREA_DISPLAY = {
    "academic_integrity": "📚 Liêm chính học thuật (Academic Integrity)",
    "grading_policy":     "📊 Điểm số & Học vụ (Grading & Academic Standing)",
    "student_conduct":    "⚖️  Quy tắc ứng xử (Student Conduct)",
    "attendance_policy":  "🕐 Chuyên cần & Vắng học (Attendance)",
    "tuition_fees":       "💰 Học phí & Tài chính (Tuition & Fees)",
    "scholarship_policy": "🎓 Học bổng (Scholarship & Financial Aid)",
    "admissions_policy":  "🚪 Tuyển sinh (Admissions)",
    "research_policy":    "🔬 Nghiên cứu (Research & Ethics)",
    "it_usage_policy":    "💻 CNTT & AI (IT & AI Usage Policy)",
    "library_policy":     "📖 Thư viện (Library)",
    "student_services":   "🏫 Dịch vụ sinh viên (Student Services)",
    "general_policy":     "📋 Quy định chung (General Policies)",
}


def parse_frontmatter(raw: str) -> tuple[dict, str]:
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) == 3:
            try:
                meta = yaml.safe_load(parts[1]) or {}
                return dict(meta), parts[2].strip()
            except Exception:
                pass
    return {}, raw.strip()


def clean_text_len(body: str) -> int:
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", body)
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"\s+", " ", t)
    return len(t.strip())


def main():
    print("=" * 68)
    print("📋 build_final_index.py  —  Bước 3/3")
    print("=" * 68)

    all_md = sorted([p for p in POLICY_DIR.glob("*.md") if p.name != "README.md"])

    index_entries = []
    area_files    = defaultdict(list)

    for path in all_md:
        if path.name.startswith("_"):
            continue
        raw  = path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(raw)
        area = meta.get("policy_area", "general_policy")
        text_chars = clean_text_len(body)

        entry = {
            "file":           path.name,
            "doc_id":         meta.get("doc_id", path.stem),
            "title":          meta.get("title", ""),
            "policy_area":    area,
            "source":         meta.get("source", ""),
            "source_url":     meta.get("source_url", ""),
            "effective_date": str(meta.get("effective_date", "")),
            "crawled_at":     str(meta.get("crawled_at", "")),
            "tags":           meta.get("tags", []),
            "text_chars":     text_chars,
        }
        index_entries.append(entry)
        area_files[area].append(entry)
        print(f"  ✅ {path.name:<60} {text_chars:>5} chars")

    # ── Lưu JSON index ────────────────────────────────────────────────────────
    area_counts = {area: len(files) for area, files in area_files.items()}
    index_data  = {
        "generated_at":   datetime.now().isoformat(),
        "total_files":    len(index_entries),
        "area_counts":    area_counts,
        "files":          index_entries,
    }
    index_path = POLICY_DIR / "_policy_index.json"
    index_path.write_text(json.dumps(index_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n📋 Index: {index_path.name} ({len(index_entries)} entries)")

    # ── Tạo README chính thức ─────────────────────────────────────────────────
    total = len(index_entries)
    now   = datetime.now().strftime("%Y-%m-%d")

    readme_lines = [
        "# VinUniversity Policy Knowledge Base",
        "",
        f"> **{total} tài liệu chính sách** — Tất cả data thật từ nguồn chính thức VinUniversity.",
        f"> Cập nhật lần cuối: {now}",
        "",
        "## Nguồn dữ liệu",
        "- 🌐 [policy.vinuni.edu.vn](https://policy.vinuni.edu.vn/all-policies/) — Portal quy định chính thức",
        "- 🌐 [registrar.vinuni.edu.vn](https://registrar.vinuni.edu.vn) — Văn phòng Học vụ",
        "- 🌐 [vinuni.edu.vn](https://vinuni.edu.vn) — Website chính thức",
        "- 🤖 Crawl tự động bằng Firecrawl API + Tavily Search API",
        "",
        "## Cách sử dụng",
        "Model gọi `policy(query, policy_area, top_k)` →",
        "Python search các file .md này →",
        "Trả về `facts + source_url + effective_date`.",
        "",
        "---",
        "",
        "## Danh sách tài liệu theo nhóm",
        "",
    ]

    for area, display in AREA_DISPLAY.items():
        files = area_files.get(area, [])
        if not files:
            continue
        readme_lines.append(f"### {display}")
        readme_lines.append("")
        readme_lines.append("| File | Tiêu đề | Nguồn | Hiệu lực |")
        readme_lines.append("|------|---------|-------|----------|")
        for f in sorted(files, key=lambda x: x["title"]):
            url       = f["source_url"]
            title_col = f["title"][:55] + "…" if len(f["title"]) > 55 else f["title"]
            eff_date  = f["effective_date"] or "N/A"
            readme_lines.append(f"| `{f['file'][:40]}` | {title_col} | [Link]({url}) | {eff_date} |")
        readme_lines.append("")

    # ── Coverage check ────────────────────────────────────────────────────────
    readme_lines += [
        "---",
        "",
        "## Coverage Report",
        "",
        "| Policy Area | # Files | Tình trạng |",
        "|-------------|---------|-----------|",
    ]
    for area, display in AREA_DISPLAY.items():
        cnt    = area_counts.get(area, 0)
        status = "✅ Đủ" if cnt >= 2 else ("⚠️ Ít" if cnt == 1 else "❌ Thiếu")
        label  = display.split("(")[0].strip()
        readme_lines.append(f"| {label} | {cnt} | {status} |")

    readme_lines += [
        "",
        "---",
        "",
        "## Verification Queries",
        "",
        "Câu hỏi test để kiểm tra hệ thống hoạt động đúng:",
        "",
        "```",
        "1. Quy định vắng học tối đa bao nhiêu % thì bị cấm thi?",
        "   → Expected: vinuni-attendance-* | source: policy.vinuni.edu.vn",
        "",
        "2. Học bổng VinU có những loại nào và điều kiện gì?",
        "   → Expected: vinuni-scholarship-* | source: policy.vinuni.edu.vn",
        "",
        "3. Dùng ChatGPT/GenAI làm bài thì có vi phạm Academic Integrity không?",
        "   → Expected: vinuni-it-guidelines-on-student-use-of-generative* | policy.vinuni.edu.vn",
        "",
        "4. GPA tối thiểu để không bị cảnh báo học vụ là bao nhiêu?",
        "   → Expected: vinuni-grading-* | source: registrar.vinuni.edu.vn",
        "",
        "5. Quy trình xin tốt nghiệp đại học cần làm gì?",
        "   → Expected: vinuni-grading-procedure-for-undergraduate-graduation | policy.vinuni.edu.vn",
        "```",
        "",
    ]

    readme_path = POLICY_DIR / "README.md"
    readme_path.write_text("\n".join(readme_lines), encoding="utf-8")
    print(f"📝 README: {readme_path.name}")

    # ── Final summary ─────────────────────────────────────────────────────────
    print(f"\n{'='*68}")
    print(f"✅ BUILD FINAL INDEX HOÀN THÀNH")
    print(f"   Tổng files: {total}")
    print(f"   Areas:      {len(area_counts)}")
    print("\n📊 Phân bố cuối cùng:")
    for area, display in AREA_DISPLAY.items():
        cnt = area_counts.get(area, 0)
        bar = "█" * cnt
        print(f"   {display[:42]:<42} {bar} ({cnt})")
    print("=" * 68)


if __name__ == "__main__":
    main()
