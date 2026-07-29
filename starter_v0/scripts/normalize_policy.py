"""
normalize_policy.py  —  Bước 1 / 3
====================================
Làm sạch & chuẩn hóa toàn bộ files trong company_policy/:
  1. Xóa image markdown lines  (![...](...))
  2. Xóa footer noise (Copyright, Privacy Policy, All Rights Reserved, logo lines)
  3. Sửa policy_area bị gán sai
  4. Xóa files là curriculum / không phải policy
  5. Deduplicate: giữ file text-dài nhất trong nhóm trùng source
  6. Đổi tên file thành convention chuẩn vinuni-{area}-{topic}.md
"""
from __future__ import annotations

import re
import sys
import yaml
import json
import shutil
from pathlib import Path
from collections import defaultdict

ROOT       = Path(__file__).parent.parent
POLICY_DIR = ROOT / "company_policy"
BACKUP_DIR = ROOT / "company_policy_backup"

# ── 1. Files xóa hoàn toàn (curriculum / không phải policy) ──────────────────
DELETE_FILENAMES = {
    # Curriculum / program info — không phải regulations
    "tavily-general_poli-bachelor-of-arts-in-psychology.md",
    "tavily-general_poli-curriculum-framework---bachelo.md",
    "tavily-general_poli-curriculum-structure---vinuni-.md",
    "tavily-general_poli-integrated-degree-program-over.md",
    "tavily-general_poli-integrated-degree-programs-pro.md",
    "tavily-it_usage_pol-curriculum-framework---medical.md",
    "tavily-it_usage_pol-curriculum-framework---vinuni-.md",
    # Homepage / general info — không phải policy
    "tavily-general_poli-home---experience-vinuni.md",
    "tavily-it_usage_pol-home-page---families-and-paren.md",
    # General academics page — gán sai area
    "vinuni-it_usage_policy-51.md",
    # Temp / log files
    "_crawl_log.json",
    "_real_data_index.json",
}

# ── 2. Reclassify: sửa policy_area sai ───────────────────────────────────────
RECLASSIFY = {
    # GenAI guidelines → it_usage_policy
    "tavily-student_serv-guidelines-on-student-use-of-g.md": "it_usage_policy",
    # Financial regulations → tuition_fees
    "tavily-student_serv-financial-regulations-and-tari.md": "tuition_fees",
    "tavily-student_serv-guidelines-for-student-financi.md": "scholarship_policy",
    # Assessment → grading_policy
    "tavily-student_serv-assessment-guideline-for-under.md": "grading_policy",
    # Academic affairs → general_policy
    "tavily-it_usage_pol-policy---regulations---academi.md": "general_policy",
    # Research integrity  
    "tavily-academic_int-research-integrity-policy---vi.md": "research_policy",
    "tavily-academic_int-research-integrity-policy-reco.md": "research_policy",
    # Absence form
    "tavily-general_poli-absence-form-md-program---vinu.md": "attendance_policy",
    # Academic calendar
    "tavily-general_poli-2027-academic-calendar.md": "general_policy",
    # Governance
    "tavily-general_poli-governance-structure-and-manag.md": "general_policy",
    "tavily-general_poli-vinuni-governance-framework-gu.md": "general_policy",
    # Regulations on labs
    "tavily-general_poli-regulations-on-management-of-l.md": "general_policy",
    # Student exchange
    "tavily-student_serv-outbound-student-exchange-proc.md": "student_services",
    # Undergraduate guide
    "tavily-student_serv-undergraduate-student-guide.md": "general_policy",
    # Student archives
    "tavily-student_serv-student-archives---vinuni-poli.md": "general_policy",
    # Student incident
    "tavily-student_serv-student-incident-case--if-the-.md": "student_conduct",
    # Student affairs listing
    "tavily-student_serv-student-affairs---vinuni-polic.md": "general_policy",
    # Appendix student conduct
    "tavily-student_cond-appendix-iv--procedure-for-stu.md": "student_conduct",
    # Sexual misconduct
    "tavily-student_cond-sexual-misconduct-and-response.md": "student_conduct",
    # Attendance medical
    "tavily-attendance_p-attendance-policy-at-medical-d.md": "attendance_policy",
    # Scholarship cohort
    "tavily-scholarship_-cohort-2025---vingroup-scholar.md": "scholarship_policy",
    "tavily-scholarship_-guidelines-for-maintaining-ent.md": "scholarship_policy",
}

# ── 3. Noise patterns cần xóa khỏi body ──────────────────────────────────────
IMAGE_PATTERN    = re.compile(r"!\[[^\]]*\]\([^)]*\)\s*\n?")
FOOTER_PATTERNS  = [
    re.compile(r"Copyright\s*©\s*\d{4}\s+VinUni\.?\s*\n?", re.IGNORECASE),
    re.compile(r"All Rights? Reserved\.?\s*\n?", re.IGNORECASE),
    re.compile(r"Privacy Policy\s*\n?", re.IGNORECASE),
    re.compile(r"^---\s*\n?$", re.MULTILINE),  # trailing hrule
]
# Lines chỉ có whitespace + markdown table separator
EMPTY_LINE = re.compile(r"^\s*$")


def strip_noise(body: str) -> str:
    """Xóa image links, footer noise khỏi body."""
    text = IMAGE_PATTERN.sub("", body)
    for pat in FOOTER_PATTERNS:
        text = pat.sub("", text)
    # Collapse nhiều blank lines thành 1
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


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


def make_slug(title: str, max_len: int = 45) -> str:
    s = re.sub(r"[^a-z0-9\s-]", "", title.lower())
    s = re.sub(r"[\s-]+", "-", s).strip("-")
    return s[:max_len].rstrip("-")


def area_short(area: str) -> str:
    MAP = {
        "academic_integrity": "academic",
        "grading_policy":     "grading",
        "student_conduct":    "conduct",
        "attendance_policy":  "attendance",
        "tuition_fees":       "tuition",
        "scholarship_policy": "scholarship",
        "admissions_policy":  "admissions",
        "research_policy":    "research",
        "it_usage_policy":    "it",
        "library_policy":     "library",
        "student_services":   "services",
        "general_policy":     "general",
    }
    return MAP.get(area, area[:8])


def write_policy_file(path: Path, meta: dict, body: str) -> None:
    tags = meta.get("tags", [])
    if isinstance(tags, list):
        tags_str = "[" + ", ".join(f'"{t}"' for t in tags) + "]"
    else:
        tags_str = str(tags)

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


def main():
    print("=" * 68)
    print("🧹 normalize_policy.py  —  Bước 1/3")
    print("=" * 68)

    # Backup trước khi xử lý
    if BACKUP_DIR.exists():
        shutil.rmtree(BACKUP_DIR)
    shutil.copytree(POLICY_DIR, BACKUP_DIR)
    print(f"✅ Backup → {BACKUP_DIR.name}/\n")

    all_md = [p for p in sorted(POLICY_DIR.glob("*.md")) if p.name != "README.md"]
    print(f"Files hiện có: {len(all_md)}\n")

    deleted  = []
    fixed    = []
    cleaned  = []

    # ── Pass 1: Xóa files không phải policy ──────────────────────────────────
    print("── Pass 1: Xóa curriculum / noise files ─────────────────────────")
    for path in all_md:
        if path.name in DELETE_FILENAMES:
            print(f"  🗑  {path.name}")
            path.unlink()
            deleted.append(path.name)
    print(f"  → Đã xóa {len(deleted)} files\n")

    # ── Pass 2: Reclassify policy_area sai ────────────────────────────────────
    print("── Pass 2: Sửa policy_area sai ──────────────────────────────────")
    remaining = [p for p in sorted(POLICY_DIR.glob("*.md")) if p.name != "README.md"]
    for path in remaining:
        if path.name not in RECLASSIFY:
            continue
        raw = path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(raw)
        new_area = RECLASSIFY[path.name]
        old_area = meta.get("policy_area", "?")
        if old_area == new_area:
            continue
        meta["policy_area"] = new_area
        # Cập nhật tags
        area_tag_map = {
            "research_policy":    ["research", "integrity", "ethics", "VinUniversity"],
            "it_usage_policy":    ["IT", "AI tools", "GenAI", "technology", "VinUniversity"],
            "tuition_fees":       ["tuition", "fees", "financial", "học phí", "VinUniversity"],
            "scholarship_policy": ["scholarship", "financial aid", "học bổng", "VinUniversity"],
            "grading_policy":     ["grading", "GPA", "assessment", "academic standing"],
            "student_conduct":    ["student conduct", "discipline", "code of conduct", "VinUniversity"],
            "attendance_policy":  ["attendance", "absence", "VinUniversity"],
        }
        if new_area in area_tag_map:
            meta["tags"] = area_tag_map[new_area]
        write_policy_file(path, meta, body)
        print(f"  ✏  {path.name[:55]:<55} {old_area} → {new_area}")
        fixed.append({"file": path.name, "from": old_area, "to": new_area})
    print(f"  → Đã fix {len(fixed)} files\n")

    # ── Pass 3: Strip image/footer noise từ body ──────────────────────────────
    print("── Pass 3: Xóa image/footer noise khỏi nội dung ────────────────")
    remaining = [p for p in sorted(POLICY_DIR.glob("*.md")) if p.name != "README.md"]
    for path in remaining:
        raw  = path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(raw)
        clean_body = strip_noise(body)
        if clean_body != body:
            write_policy_file(path, meta, clean_body)
            cleaned.append(path.name)
            print(f"  🧼 {path.name[:55]}")
    print(f"  → Đã làm sạch {len(cleaned)} files\n")

    # ── Pass 4: Deduplicate theo source_url ───────────────────────────────────
    print("── Pass 4: Deduplicate theo source_url ──────────────────────────")
    url_groups: dict[str, list[Path]] = defaultdict(list)
    remaining = [p for p in sorted(POLICY_DIR.glob("*.md")) if p.name != "README.md"]
    for path in remaining:
        raw  = path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(raw)
        url = str(meta.get("source_url", "")).strip()
        if url:
            url_groups[url].append(path)

    dedup_deleted = []
    for url, paths in url_groups.items():
        if len(paths) <= 1:
            continue
        # Giữ file có text dài nhất
        def score(p: Path) -> int:
            raw = p.read_text(encoding="utf-8")
            _, body = parse_frontmatter(raw)
            return clean_text_len(body)
        paths_sorted = sorted(paths, key=score, reverse=True)
        keep = paths_sorted[0]
        for dup in paths_sorted[1:]:
            print(f"  🗑  DUP {dup.name[:50]:<50} (keep: {keep.name[:30]})")
            dup.unlink()
            dedup_deleted.append(dup.name)
    print(f"  → Đã xóa {len(dedup_deleted)} duplicates\n")

    # ── Pass 5: Đổi tên file thành convention chuẩn ───────────────────────────
    print("── Pass 5: Chuẩn hóa tên file ───────────────────────────────────")
    remaining = [p for p in sorted(POLICY_DIR.glob("*.md")) if p.name != "README.md"]
    renamed = []
    for path in remaining:
        raw  = path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(raw)
        area  = meta.get("policy_area", "general_policy")
        title = meta.get("title", path.stem)
        # Tạo tên chuẩn
        short = area_short(area)
        slug  = make_slug(title, max_len=40)
        new_name = f"vinuni-{short}-{slug}.md"
        new_path = POLICY_DIR / new_name

        if path.name == new_name:
            continue
        if new_path.exists():
            # Nếu trùng tên, thêm suffix
            stem = new_name[:-3]
            i = 2
            while new_path.exists():
                new_path = POLICY_DIR / f"{stem}-{i}.md"
                i += 1
            new_name = new_path.name

        # Cập nhật doc_id theo tên mới
        meta["doc_id"] = new_path.stem
        write_policy_file(new_path, meta, body)
        path.unlink()
        print(f"  📝 {path.name[:40]:<40} → {new_path.name}")
        renamed.append({"old": path.name, "new": new_path.name})
    print(f"  → Đã đổi tên {len(renamed)} files\n")

    # ── Final summary ─────────────────────────────────────────────────────────
    final_files = [p for p in sorted(POLICY_DIR.glob("*.md")) if p.name != "README.md"]
    area_counts: dict[str, int] = {}
    for p in final_files:
        raw = p.read_text(encoding="utf-8")
        meta, _ = parse_frontmatter(raw)
        a = meta.get("policy_area", "?")
        area_counts[a] = area_counts.get(a, 0) + 1

    print("=" * 68)
    print(f"✅ NORMALIZE HOÀN THÀNH")
    print(f"   Trước: {len(all_md)} files")
    print(f"   Sau  : {len(final_files)} files")
    print(f"   Xóa  : {len(deleted) + len(dedup_deleted)} (noise + dup)")
    print("=" * 68)
    print("\n📊 Files theo policy area:")
    for area, cnt in sorted(area_counts.items()):
        print(f"   {area:<35} {cnt:>2} files")

    # Lưu log
    log = {
        "deleted_noise": deleted,
        "reclassified": fixed,
        "dedup_deleted": dedup_deleted,
        "renamed": renamed,
        "final_count": len(final_files),
        "areas": area_counts,
    }
    (POLICY_DIR / "_normalize_log.json").write_text(
        json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n📋 Log: {POLICY_DIR}/_normalize_log.json")
    print(f"💾 Backup: {BACKUP_DIR}")


if __name__ == "__main__":
    main()
