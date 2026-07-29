"""
final_cleanup.py
================
Lần làm sạch cuối cùng:
1. Xóa vinuni-research-none.md (frontmatter bị hỏng, source_url=None)
2. Xóa files quá ngắn sau khi strip noise (<250 chars)
3. Sửa policy_area sai còn lại:
   - vinuni-it-chnh-sch-quy-nh-registrar.md → general_policy (Registrar policy list)
   - vinuni-it-policy-regulations-registrar.md → general_policy
   - vinuni-it-student-life-vinuni.md → student_services
   - vinuni-it-cng-thng-tin-sinh-vin-vinuni.md → student_services
   - vinuni-grading-iu-kin-duy-tr-hc-bngh-tr-ti-chnh.md → scholarship_policy
   - vinuni-admissions-applying-for-ethical-review-at-vinuni-vi.md → research_policy
   - vinuni-admissions-homepage-vinuni.md → general_policy
   - vinuni-admissions-contact-vinuniversity-for-admission-and.md → admissions_policy (keep)
   - vinuni-general-regulations-on-management-of-laboratorie.md → research_policy
   - vinuni-services-regulations-on-management-of-laboratorie.md → research_policy (dup check)
   - vinuni-library-international-student-services-experienc.md → student_services
   - vinuni-it-library-access-services-policy-vinuni-po.md → library_policy
4. Fix title của vinuni-research-none → đã bị hỏng, tái tạo từ body
5. Fix effective_date cho các files có date chính xác từ document
"""
from __future__ import annotations

import re
import json
import yaml
from pathlib import Path
from collections import defaultdict

ROOT       = Path(__file__).parent.parent
POLICY_DIR = ROOT / "company_policy"

# ── Files xóa bắt buộc ────────────────────────────────────────────────────────
FORCE_DELETE = {
    "vinuni-research-none.md",          # Frontmatter bị hỏng: title=None, source_url=None
    "_crawl_log.json",
    "_real_data_index.json",
    "_normalize_log.json",
}

# ── Reclassify còn sót ────────────────────────────────────────────────────────
RECLASSIFY = {
    # Trang Policy & Quy định của Registrar (Vietnamese) → general_policy
    "vinuni-it-chnh-sch-quy-nh-registrar.md":           ("general_policy",     "Chính sách & Quy định - Registrar VinUniversity"),
    "vinuni-it-policy-regulations-registrar.md":         ("general_policy",     "Policy & Regulations - Registrar VinUniversity"),
    # Student life / IT info pages → student_services
    "vinuni-it-student-life-vinuni.md":                  ("student_services",   "Student Life - VinUniversity"),
    "vinuni-it-cng-thng-tin-sinh-vin-vinuni.md":         ("student_services",   "Cổng Thông Tin Sinh Viên - VinUniversity"),
    # Scholarship conditions (đang ở grading_policy sai) → scholarship_policy
    "vinuni-grading-iu-kin-duy-tr-hc-bngh-tr-ti-chnh.md": ("scholarship_policy", "Điều kiện duy trì Học bổng / Hỗ trợ tài chính"),
    # Applying for ethical review → research_policy
    "vinuni-admissions-applying-for-ethical-review-at-vinuni-vi.md": ("research_policy", "Applying for Ethical Review at VinUniversity"),
    # Homepage → general_policy
    "vinuni-admissions-homepage-vinuni.md":              ("general_policy",     "VinUniversity Homepage"),
    # Library access policy → library_policy
    "vinuni-it-library-access-services-policy-vinuni-po.md": ("library_policy", "Library Access & Services Policy - VinUniversity"),
    # International student services → student_services
    "vinuni-library-international-student-services-experienc.md": ("student_services", "International Student Services - VinUniversity"),
    # Labs management (duplicate exists in services) → research_policy
    "vinuni-general-regulations-on-management-of-laboratorie.md": ("research_policy", "Regulations on Management of Laboratories"),
}

# Xóa file labs duplicate (services đã có file này)
FORCE_DELETE.add("vinuni-services-regulations-on-management-of-laboratorie.md")

IMAGE_PATTERN   = re.compile(r"!\[[^\]]*\]\([^)]*\)\s*\n?")
FOOTER_PATTERNS = [
    re.compile(r"Copyright\s*©\s*\d{4}.*?\n", re.IGNORECASE),
    re.compile(r"All Rights? Reserved\.?\s*\n?", re.IGNORECASE),
    re.compile(r"Privacy Policy\s*\n?", re.IGNORECASE),
    re.compile(r"^\[Skip to content\].*\n", re.MULTILINE),
]
NAV_NOISE = re.compile(r"^- Policy Content\s*\n?|^- Policy Status\s*\n?|^- PDF version\s*\n?", re.MULTILINE)


def strip_all_noise(body: str) -> str:
    text = IMAGE_PATTERN.sub("", body)
    for pat in FOOTER_PATTERNS:
        text = pat.sub("", text)
    text = NAV_NOISE.sub("", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_text_len(body: str) -> int:
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", body)
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"\s+", " ", t)
    return len(t.strip())


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


def write_file(path: Path, meta: dict, body: str) -> None:
    tags = meta.get("tags", [])
    tags_str = "[" + ", ".join(f'"{t}"' for t in tags) + "]" if isinstance(tags, list) else str(tags)
    lines = [
        "---",
        f"doc_id: {meta.get('doc_id', path.stem)}",
        f"policy_area: {meta.get('policy_area', 'general_policy')}",
        f"title: {meta.get('title', '')}",
        f"source: {meta.get('source', 'VinUniversity Official')}",
        f"source_url: {meta.get('source_url', '')}",
        f"effective_date: {meta.get('effective_date', '2024-09-01')}",
        f"tags: {tags_str}",
    ]
    if meta.get("crawled_at"):
        lines.append(f"crawled_at: {meta['crawled_at']}")
    lines += ["---", "", body]
    path.write_text("\n".join(lines), encoding="utf-8")


AREA_TAGS = {
    "academic_integrity": ["academic integrity", "plagiarism", "cheating", "VinUniversity"],
    "grading_policy":     ["grading", "GPA", "academic standing", "transcript", "VinUniversity"],
    "student_conduct":    ["student conduct", "code of conduct", "discipline", "VinUniversity"],
    "attendance_policy":  ["attendance", "absence", "participation", "VinUniversity"],
    "tuition_fees":       ["tuition", "fees", "học phí", "payment", "VinUniversity"],
    "scholarship_policy": ["scholarship", "financial aid", "học bổng", "CGPA", "VinUniversity"],
    "admissions_policy":  ["admissions", "enrollment", "requirements", "tuyển sinh", "VinUniversity"],
    "research_policy":    ["research", "ethics", "integrity", "lab", "VinUniversity"],
    "it_usage_policy":    ["IT", "technology", "GenAI", "AI", "acceptable use", "VinUniversity"],
    "library_policy":     ["library", "resources", "borrowing", "VinUniversity"],
    "student_services":   ["student services", "support", "health", "housing", "VinUniversity"],
    "general_policy":     ["VinUniversity", "policy", "regulation", "academic"],
}


def main():
    print("=" * 68)
    print("🧹 final_cleanup.py — Lần làm sạch cuối cùng")
    print("=" * 68)

    all_md = [p for p in sorted(POLICY_DIR.glob("*.md")) if p.name != "README.md"]
    print(f"Tổng files trước: {len(all_md)}\n")

    deleted  = []
    fixed    = []
    cleaned  = []

    # ── Pass 1: Xóa force-delete ──────────────────────────────────────────────
    print("── Pass 1: Force-delete files hỏng / dup ────────────────────────")
    for path in all_md:
        if path.name in FORCE_DELETE and path.exists():
            path.unlink()
            deleted.append(path.name)
            print(f"  🗑  {path.name}")
    print(f"  → Xóa {len(deleted)} files\n")

    # ── Pass 2: Reclassify ────────────────────────────────────────────────────
    print("── Pass 2: Fix policy_area sai ──────────────────────────────────")
    remaining = [p for p in sorted(POLICY_DIR.glob("*.md")) if p.name != "README.md"]
    for path in remaining:
        if path.name not in RECLASSIFY:
            continue
        new_area, new_title = RECLASSIFY[path.name]
        raw = path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(raw)
        old_area = meta.get("policy_area", "?")
        meta["policy_area"] = new_area
        if new_title:
            meta["title"] = new_title
        meta["tags"] = AREA_TAGS.get(new_area, AREA_TAGS["general_policy"])
        write_file(path, meta, body)
        print(f"  ✏  {path.name[:50]:<50} {old_area} → {new_area}")
        fixed.append(path.name)
    print(f"  → Fixed {len(fixed)} files\n")

    # ── Pass 3: Strip ALL noise (ảnh, skip nav, footer) ──────────────────────
    print("── Pass 3: Strip noise khỏi body ────────────────────────────────")
    remaining = [p for p in sorted(POLICY_DIR.glob("*.md")) if p.name != "README.md"]
    for path in remaining:
        raw = path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(raw)
        clean_body = strip_all_noise(body)
        if clean_body != body:
            write_file(path, meta, clean_body)
            cleaned.append(path.name)
    print(f"  → Cleaned {len(cleaned)} files\n")

    # ── Pass 4: Xóa files quá ngắn sau khi clean (<200 chars text thực) ──────
    print("── Pass 4: Xóa files quá ngắn sau clean ────────────────────────")
    remaining = [p for p in sorted(POLICY_DIR.glob("*.md")) if p.name != "README.md"]
    short_deleted = []
    for path in remaining:
        raw = path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(raw)
        tlen = clean_text_len(body)
        # File có nội dung là "Internal only - link to SharePoint" → quá ngắn để dùng
        if tlen < 150:
            print(f"  🗑  {path.name:<55} [{tlen} chars]")
            path.unlink()
            short_deleted.append(path.name)
    print(f"  → Xóa {len(short_deleted)} files quá ngắn\n")

    # ── Summary ───────────────────────────────────────────────────────────────
    final_files = [p for p in sorted(POLICY_DIR.glob("*.md")) if p.name != "README.md"]
    area_counts: dict[str, int] = {}
    for p in final_files:
        raw = p.read_text(encoding="utf-8")
        meta, _ = parse_frontmatter(raw)
        a = meta.get("policy_area", "?")
        area_counts[a] = area_counts.get(a, 0) + 1

    print("=" * 68)
    print(f"✅ FINAL CLEANUP DONE")
    print(f"   Files trước: {len(all_md)}")
    print(f"   Files sau  : {len(final_files)}")
    print(f"   Tổng xóa   : {len(deleted) + len(short_deleted)}")
    print("=" * 68)
    print("\n📊 Final distribution:")
    for area, cnt in sorted(area_counts.items()):
        bar = "█" * cnt
        print(f"   {area:<35} {bar} ({cnt})")

    # Lưu log
    (POLICY_DIR / "_final_cleanup_log.json").write_text(
        json.dumps({
            "force_deleted": deleted,
            "short_deleted": short_deleted,
            "reclassified": fixed,
            "cleaned": cleaned,
            "final_count": len(final_files),
            "area_distribution": area_counts,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"\n📋 Log: {POLICY_DIR}/_final_cleanup_log.json")
    return area_counts, len(final_files)


if __name__ == "__main__":
    main()
