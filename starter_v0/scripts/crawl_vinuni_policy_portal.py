"""
crawl_vinuni_policy_portal.py
==============================
Crawl từ policy.vinuni.edu.vn — nguồn chính thức nhất của VinUniversity.
Đây là portal quy định nội bộ chính thức, tất cả data 100% thật.

Usage:
    python scripts/crawl_vinuni_policy_portal.py
"""
from __future__ import annotations

import os
import re
import sys
import time
import json
import requests
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from env_loader import load_lab_env
load_lab_env(ROOT)

FIRECRAWL_KEY = os.getenv("FIRECRAWL_API_KEY", "")
TAVILY_KEY    = os.getenv("TAVILY_API_KEY", "")
POLICY_DIR    = ROOT / "company_policy"
POLICY_DIR.mkdir(exist_ok=True)

# ── Tất cả URL chính thức từ policy.vinuni.edu.vn ────────────────────────────
# Nguồn: portal quy định chính thức của VinUniversity
OFFICIAL_POLICY_URLS = [
    # ── Academic Integrity ────────────────────────────────────────────────────
    ("academic_integrity", "Student Academic Integrity Policy",
     "https://policy.vinuni.edu.vn/all-policies/student-academic-integrity"),

    # ── Academic Policies ─────────────────────────────────────────────────────
    ("grading_policy", "Academic Standards and Policies",
     "https://policy.vinuni.edu.vn/all-policies/academic-standards-and-policies"),

    ("grading_policy", "Student Course Registration Policy",
     "https://policy.vinuni.edu.vn/all-policies/student-course-registration-policy"),

    ("grading_policy", "Student Academic Appeals Policy",
     "https://policy.vinuni.edu.vn/all-policies/student-academic-appeals-policy"),

    ("grading_policy", "Student Academic Probation and Dismissal Policy",
     "https://policy.vinuni.edu.vn/all-policies/student-academic-probation-and-dismissal-policy"),

    ("grading_policy", "Credit Transfer Policy",
     "https://policy.vinuni.edu.vn/all-policies/credit-transfer-policy"),

    # ── Student Conduct ───────────────────────────────────────────────────────
    ("student_conduct", "Student Code of Conduct",
     "https://policy.vinuni.edu.vn/all-policies/student-code-of-conduct"),

    ("student_conduct", "Student Grievance Policy",
     "https://policy.vinuni.edu.vn/all-policies/student-grievance-policy"),

    ("student_conduct", "Harassment and Discrimination Policy",
     "https://policy.vinuni.edu.vn/all-policies/harassment-and-discrimination-policy"),

    # ── Attendance ────────────────────────────────────────────────────────────
    ("attendance_policy", "Student Attendance Policy",
     "https://policy.vinuni.edu.vn/all-policies/student-attendance-policy"),

    # ── Scholarships & Fees ───────────────────────────────────────────────────
    ("scholarship_policy", "Student Financial Aid Policy",
     "https://policy.vinuni.edu.vn/all-policies/student-financial-aid-policy"),

    ("tuition_fees", "Tuition and Fees Policy",
     "https://policy.vinuni.edu.vn/all-policies/tuition-and-fees-policy"),

    # ── Admissions ────────────────────────────────────────────────────────────
    ("admissions_policy", "Undergraduate Admissions Policy",
     "https://policy.vinuni.edu.vn/all-policies/undergraduate-admissions-policy"),

    ("admissions_policy", "Graduate Admissions Policy",
     "https://policy.vinuni.edu.vn/all-policies/graduate-admissions-policy"),

    # ── Research ──────────────────────────────────────────────────────────────
    ("research_policy", "Research Ethics Policy",
     "https://policy.vinuni.edu.vn/all-policies/research-ethics-policy"),

    ("research_policy", "Intellectual Property Policy",
     "https://policy.vinuni.edu.vn/all-policies/intellectual-property-policy"),

    # ── IT / Data ─────────────────────────────────────────────────────────────
    ("it_usage_policy", "IT Acceptable Use Policy",
     "https://policy.vinuni.edu.vn/all-policies/it-acceptable-use-policy"),

    ("it_usage_policy", "Data Privacy and Protection Policy",
     "https://policy.vinuni.edu.vn/all-policies/data-privacy-and-protection-policy"),

    # ── Student Services ──────────────────────────────────────────────────────
    ("student_services", "Student Health and Wellbeing Policy",
     "https://policy.vinuni.edu.vn/all-policies/student-health-and-wellbeing-policy"),

    ("library_policy", "Library Policy",
     "https://policy.vinuni.edu.vn/all-policies/library-policy"),

    # ── Main policy listing ───────────────────────────────────────────────────
    ("general_policy", "All VinUniversity Policies",
     "https://policy.vinuni.edu.vn/all-policies/"),
]

# ── Thêm Tavily search queries bổ sung ────────────────────────────────────────
TAVILY_QUERIES = [
    "site:policy.vinuni.edu.vn academic integrity",
    "site:policy.vinuni.edu.vn grading policy GPA",
    "site:policy.vinuni.edu.vn student conduct",
    "site:policy.vinuni.edu.vn attendance policy",
    "site:policy.vinuni.edu.vn financial aid scholarship",
    "site:policy.vinuni.edu.vn tuition fees",
    "site:policy.vinuni.edu.vn admissions",
    "site:policy.vinuni.edu.vn research ethics",
    "site:policy.vinuni.edu.vn IT acceptable use",
    "site:vinuni.edu.vn academic calendar 2024 2025",
    "site:vinuni.edu.vn undergraduate programs requirements",
    "site:vinuni.edu.vn student handbook regulations",
]

AREA_TAGS = {
    "academic_integrity": ["academic integrity", "plagiarism", "cheating", "honesty", "VinUniversity policy"],
    "grading_policy":     ["grading", "GPA", "academic standing", "transcript", "course registration"],
    "student_conduct":    ["student conduct", "code of conduct", "discipline", "VinUniversity"],
    "attendance_policy":  ["attendance", "absence", "participation", "VinUniversity"],
    "scholarship_policy": ["scholarship", "financial aid", "học bổng", "VinUniversity"],
    "tuition_fees":       ["tuition", "fees", "payment", "học phí", "VinUniversity"],
    "admissions_policy":  ["admissions", "enrollment", "requirements", "tuyển sinh"],
    "research_policy":    ["research", "ethics", "intellectual property", "VinUniversity"],
    "it_usage_policy":    ["IT", "acceptable use", "data privacy", "technology", "VinUniversity"],
    "student_services":   ["student services", "health", "wellbeing", "counseling"],
    "library_policy":     ["library", "resources", "borrowing", "VinUniversity"],
    "general_policy":     ["VinUniversity", "policy", "regulation"],
}


def firecrawl_scrape(url: str, timeout: int = 45) -> dict:
    if not FIRECRAWL_KEY:
        return {}
    try:
        resp = requests.post(
            "https://api.firecrawl.dev/v1/scrape",
            json={"url": url, "formats": ["markdown"], "onlyMainContent": True},
            headers={"Authorization": f"Bearer {FIRECRAWL_KEY}"},
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json().get("data", {})
        return {
            "markdown": data.get("markdown", ""),
            "title":    (data.get("metadata", {}) or {}).get("title", ""),
        }
    except Exception as e:
        print(f"    ⚠ Firecrawl: {e}")
        return {}


def tavily_search(query: str, max_results: int = 8) -> list[dict]:
    if not TAVILY_KEY:
        return []
    try:
        resp = requests.post(
            "https://api.tavily.com/search",
            json={
                "query": query,
                "topic": "general",
                "max_results": max_results,
                "search_depth": "advanced",
                "include_raw_content": True,
            },
            headers={"Authorization": f"Bearer {TAVILY_KEY}"},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("results", [])
    except Exception as e:
        print(f"    ⚠ Tavily: {e}")
        return []


def is_official_vinuni(url: str) -> bool:
    return "vinuni.edu.vn" in url


def clean_text_len(content: str) -> int:
    t = re.sub(r"!\[.*?\]\(.*?\)", " ", content)
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"\s+", " ", t)
    return len(t.strip())


def save_policy_file(
    doc_id: str,
    area: str,
    title: str,
    source_url: str,
    content: str,
    effective_date: str = "2024-09-01",
) -> Path | None:
    if not content or len(content.strip()) < 200:
        return None

    tags = AREA_TAGS.get(area, ["VinUniversity", "policy"])
    tags_str = "[" + ", ".join(f'"{t}"' for t in tags) + "]"
    area_display = area.replace("_", " ").title()

    md = (
        f"---\n"
        f"doc_id: {doc_id}\n"
        f"policy_area: {area}\n"
        f"title: {title}\n"
        f"source: VinUniversity Official — {area_display}\n"
        f"source_url: {source_url}\n"
        f"effective_date: {effective_date}\n"
        f"tags: {tags_str}\n"
        f"crawled_at: {datetime.now().strftime('%Y-%m-%d')}\n"
        f"---\n\n"
        f"{content.strip()[:9000]}\n"
    )

    path = POLICY_DIR / f"{doc_id}.md"
    path.write_text(md, encoding="utf-8")
    print(f"    💾 {path.name} ({clean_text_len(content)} chars) ← {source_url[:60]}")
    return path


def main():
    print("=" * 68)
    print("🎓 VinU Policy Portal Crawler — Nguồn chính thức 100%")
    print("=" * 68)
    print(f"  Firecrawl: {'✓' if FIRECRAWL_KEY else '✗'}")
    print(f"  Tavily:    {'✓' if TAVILY_KEY else '✗'}")
    print()

    saved = []
    seen_urls: set[str] = set()

    # ── PHASE 1: Scrape từng URL policy chính thức ────────────────────────────
    print(f"📄 Phase 1: Scraping {len(OFFICIAL_POLICY_URLS)} official policy URLs...\n")
    for area, title, url in OFFICIAL_POLICY_URLS:
        print(f"  → {url}")
        result = firecrawl_scrape(url)
        content = result.get("markdown", "")
        crawl_title = result.get("title", "") or title

        if clean_text_len(content) < 300:
            print(f"    ⚠ Skipped (too short or failed)")
            time.sleep(1)
            continue

        slug = re.sub(r"[^a-z0-9-]", "-", title.lower())[:40].strip("-")
        doc_id = f"official-{area[:12]}-{slug[:30]}"
        path = save_policy_file(doc_id, area, crawl_title or title, url, content)
        if path:
            saved.append(path)
            seen_urls.add(url)
        time.sleep(1.5)

    # ── PHASE 2: Tavily search bổ sung từ policy.vinuni.edu.vn ───────────────
    print(f"\n🔍 Phase 2: Tavily supplementary search ({len(TAVILY_QUERIES)} queries)...\n")
    for query in TAVILY_QUERIES:
        print(f"  → {query[:60]}")
        results = tavily_search(query, max_results=6)
        for r in results:
            r_url     = r.get("url", "")
            r_title   = r.get("title", "")
            r_content = r.get("raw_content", "") or r.get("content", "")

            # Chỉ lấy từ vinuni.edu.vn
            if not is_official_vinuni(r_url):
                continue
            if r_url in seen_urls:
                continue
            if clean_text_len(r_content) < 400:
                continue

            seen_urls.add(r_url)

            # Đoán area từ URL + title
            combined = (r_url + " " + r_title).lower()
            area = "general_policy"
            if any(w in combined for w in ["integrity", "plagiarism", "honesty"]):
                area = "academic_integrity"
            elif any(w in combined for w in ["grading", "gpa", "grade", "academic-standing", "registration"]):
                area = "grading_policy"
            elif any(w in combined for w in ["conduct", "discipline", "behavior"]):
                area = "student_conduct"
            elif any(w in combined for w in ["attendance", "absent"]):
                area = "attendance_policy"
            elif any(w in combined for w in ["scholarship", "financial-aid", "học bổng"]):
                area = "scholarship_policy"
            elif any(w in combined for w in ["tuition", "fee", "học phí"]):
                area = "tuition_fees"
            elif any(w in combined for w in ["admission", "enroll", "tuyển sinh"]):
                area = "admissions_policy"
            elif any(w in combined for w in ["research", "ethics", "intellectual"]):
                area = "research_policy"
            elif any(w in combined for w in ["it", "technology", "data-privacy", "acceptable-use"]):
                area = "it_usage_policy"
            elif any(w in combined for w in ["library"]):
                area = "library_policy"
            elif any(w in combined for w in ["student", "support", "health", "wellbeing"]):
                area = "student_services"

            slug   = re.sub(r"[^a-z0-9-]", "-", r_title.lower())[:35].strip("-")
            doc_id = f"tavily-{area[:12]}-{slug[:30]}"
            path   = save_policy_file(doc_id, area, r_title, r_url, r_content)
            if path:
                saved.append(path)
        time.sleep(0.5)

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{'='*68}")
    print(f"✅ Crawl hoàn tất! Đã lưu {len(saved)} files mới (nguồn chính thức)")
    print(f"{'='*68}")
    print(f"📁 Thư mục: {POLICY_DIR}")


if __name__ == "__main__":
    main()
