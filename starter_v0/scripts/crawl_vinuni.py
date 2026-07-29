"""
crawl_vinuni.py
===============
Crawl VinUniversity website và lưu thành các file .md trong company_policy/
Sử dụng Firecrawl API để crawl toàn bộ nội dung

Usage:
    python scripts/crawl_vinuni.py
"""
from __future__ import annotations

import os
import re
import sys
import time
import json
import requests
from pathlib import Path

# ── Setup paths ──────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from env_loader import load_lab_env
load_lab_env(ROOT)

FIRECRAWL_KEY = os.getenv("FIRECRAWL_API_KEY", "")
TAVILY_KEY    = os.getenv("TAVILY_API_KEY", "")
POLICY_DIR    = ROOT / "company_policy"
POLICY_DIR.mkdir(exist_ok=True)

# ── VinUniversity URLs cần crawl ──────────────────────────────────────────────
VINUNI_URLS = [
    # Trang chính
    ("about",               "https://vinuni.edu.vn/about-vinuni/"),
    # Academic policies
    ("academic-policies",   "https://vinuni.edu.vn/academic-life/academic-policies/"),
    ("academic-calendar",   "https://vinuni.edu.vn/academic-life/academic-calendar/"),
    ("academic-programs",   "https://vinuni.edu.vn/academics/"),
    # Student life
    ("student-life",        "https://vinuni.edu.vn/student-life/"),
    ("student-support",     "https://vinuni.edu.vn/student-life/student-support-services/"),
    ("student-conduct",     "https://vinuni.edu.vn/student-life/student-conduct/"),
    # Admissions
    ("admissions",          "https://vinuni.edu.vn/admissions/"),
    ("admissions-undergrad","https://vinuni.edu.vn/admissions/undergraduate/"),
    ("tuition-fees",        "https://vinuni.edu.vn/admissions/tuition-and-fees/"),
    ("scholarships",        "https://vinuni.edu.vn/admissions/scholarships/"),
    # Research
    ("research",            "https://vinuni.edu.vn/research/"),
    ("research-policy",     "https://vinuni.edu.vn/research/research-policy/"),
    # Faculty & Staff
    ("faculty",             "https://vinuni.edu.vn/faculty-and-staff/"),
    # IT & Infrastructure
    ("it-services",         "https://vinuni.edu.vn/student-life/it-services/"),
    # Library
    ("library",             "https://vinuni.edu.vn/student-life/library/"),
]

# Backup: nếu Firecrawl không crawl được, dùng Tavily search
VINUNI_SEARCH_QUERIES = [
    "VinUniversity academic integrity policy plagiarism",
    "VinUniversity grading policy GPA academic standing",
    "VinUniversity student conduct code of conduct",
    "VinUniversity attendance policy regulations",
    "VinUniversity tuition fees scholarship policy",
    "VinUniversity IT acceptable use policy AI tools",
    "VinUniversity research ethics policy",
    "VinUniversity admissions requirements criteria",
    "VinUniversity library services resources",
    "VinUniversity student support services",
    "đại học VinUniversity quy định học thuật sinh viên",
    "VinUniversity nội quy quy chế học bổng",
]


def slug(text: str) -> str:
    """Tạo slug từ text."""
    return re.sub(r"[^a-z0-9-]", "-", text.lower().strip()).strip("-")


def firecrawl_scrape(url: str) -> dict:
    """Scrape một URL bằng Firecrawl."""
    if not FIRECRAWL_KEY:
        return {}
    try:
        resp = requests.post(
            "https://api.firecrawl.dev/v1/scrape",
            json={"url": url, "formats": ["markdown"], "onlyMainContent": True},
            headers={"Authorization": f"Bearer {FIRECRAWL_KEY}"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json().get("data", {})
        return {
            "markdown": data.get("markdown", ""),
            "title": (data.get("metadata", {}) or {}).get("title", ""),
            "url": url,
        }
    except Exception as e:
        print(f"  ⚠ Firecrawl error for {url}: {e}")
        return {}


def firecrawl_crawl_site(base_url: str = "https://vinuni.edu.vn", limit: int = 50) -> list[dict]:
    """Crawl toàn bộ site bằng Firecrawl /crawl endpoint."""
    if not FIRECRAWL_KEY:
        return []
    try:
        print(f"\n🔥 Starting Firecrawl CRAWL of {base_url} (limit={limit})...")
        resp = requests.post(
            "https://api.firecrawl.dev/v1/crawl",
            json={
                "url": base_url,
                "limit": limit,
                "scrapeOptions": {"formats": ["markdown"], "onlyMainContent": True},
                "includePaths": [
                    "*/academic*", "*/student*", "*/admission*",
                    "*/research*", "*/policy*", "*/regulation*",
                    "*/scholarship*", "*/tuition*", "*/faculty*",
                    "*/about*", "*/library*",
                ],
            },
            headers={"Authorization": f"Bearer {FIRECRAWL_KEY}"},
            timeout=30,
        )
        resp.raise_for_status()
        job = resp.json()
        job_id = job.get("id")
        if not job_id:
            print(f"  ⚠ No job ID returned: {job}")
            return []
        print(f"  ✓ Crawl job started: {job_id}")

        # Poll for results
        for attempt in range(30):
            time.sleep(5)
            status_resp = requests.get(
                f"https://api.firecrawl.dev/v1/crawl/{job_id}",
                headers={"Authorization": f"Bearer {FIRECRAWL_KEY}"},
                timeout=30,
            )
            status_resp.raise_for_status()
            status_data = status_resp.json()
            status = status_data.get("status", "")
            total = status_data.get("total", 0)
            completed = status_data.get("completed", 0)
            print(f"  [{attempt+1}/30] Status: {status} | {completed}/{total} pages", end="\r")

            if status == "completed":
                print(f"\n  ✓ Crawl completed! {completed} pages")
                return status_data.get("data", [])
            elif status in ("failed", "cancelled"):
                print(f"\n  ✗ Crawl {status}")
                return []

        print("\n  ⚠ Timeout waiting for crawl")
        return []
    except Exception as e:
        print(f"  ✗ Crawl error: {e}")
        return []


def tavily_search(query: str, max_results: int = 5) -> list[dict]:
    """Search bằng Tavily."""
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
        print(f"  ⚠ Tavily error: {e}")
        return []


def categorize_content(title: str, url: str, content: str) -> str:
    """Phân loại nội dung vào policy_area."""
    combined = (title + " " + url + " " + content[:500]).lower()
    if any(w in combined for w in ["integrity", "plagiarism", "academic honesty", "cheating", "liêm chính"]):
        return "academic_integrity"
    if any(w in combined for w in ["grading", "gpa", "grade", "transcript", "điểm", "academic standing"]):
        return "grading_policy"
    if any(w in combined for w in ["conduct", "behavior", "discipline", "violation", "nội quy", "kỷ luật"]):
        return "student_conduct"
    if any(w in combined for w in ["attendance", "absent", "chuyên cần", "vắng mặt"]):
        return "attendance_policy"
    if any(w in combined for w in ["tuition", "fee", "payment", "học phí", "lệ phí"]):
        return "tuition_fees"
    if any(w in combined for w in ["scholarship", "financial aid", "học bổng", "hỗ trợ tài chính"]):
        return "scholarship_policy"
    if any(w in combined for w in ["admission", "enrollment", "apply", "tuyển sinh", "nhập học"]):
        return "admissions_policy"
    if any(w in combined for w in ["research", "ethics", "publication", "nghiên cứu", "đạo đức"]):
        return "research_policy"
    if any(w in combined for w in ["it", "technology", "ai", "software", "digital", "computer", "công nghệ"]):
        return "it_usage_policy"
    if any(w in combined for w in ["library", "thư viện", "resource", "database"]):
        return "library_policy"
    if any(w in combined for w in ["student", "support", "service", "sinh viên", "hỗ trợ"]):
        return "student_services"
    return "general_policy"


def make_doc_id(area: str, index: int = 0) -> str:
    return f"vinuni-{area}-{index:02d}" if index > 0 else f"vinuni-{area}"


AREA_TAGS = {
    "academic_integrity": ["academic integrity", "plagiarism", "cheating", "honesty", "citation"],
    "grading_policy": ["grading", "GPA", "transcript", "academic standing", "pass fail"],
    "student_conduct": ["student conduct", "discipline", "behavior", "code of conduct", "violation"],
    "attendance_policy": ["attendance", "absence", "tardiness", "participation"],
    "tuition_fees": ["tuition", "fees", "payment", "financial", "học phí"],
    "scholarship_policy": ["scholarship", "financial aid", "merit", "học bổng"],
    "admissions_policy": ["admissions", "enrollment", "requirements", "tuyển sinh"],
    "research_policy": ["research", "ethics", "publication", "intellectual property"],
    "it_usage_policy": ["IT", "technology", "AI tools", "software", "acceptable use"],
    "library_policy": ["library", "resources", "borrowing", "database"],
    "student_services": ["student services", "support", "counseling", "health"],
    "general_policy": ["VinUniversity", "policy", "regulation", "handbook"],
}


def save_policy_file(
    doc_id: str,
    area: str,
    title: str,
    source_url: str,
    content: str,
    effective_date: str = "2024-09-01",
) -> Path:
    """Lưu nội dung thành file .md trong company_policy/"""
    if not content.strip():
        return None

    # Trim content
    content_trimmed = content.strip()[:8000]

    tags = AREA_TAGS.get(area, ["VinUniversity", "policy"])
    tags_str = "[" + ", ".join(f'"{t}"' for t in tags) + "]"

    area_display = area.replace("_", " ").title()

    md_content = f"""---
doc_id: {doc_id}
policy_area: {area}
title: {title}
source: VinUniversity Official Website — {area_display}
source_url: {source_url}
effective_date: {effective_date}
tags: {tags_str}
---

{content_trimmed}
"""

    filename = f"{doc_id}.md"
    path = POLICY_DIR / filename
    path.write_text(md_content, encoding="utf-8")
    print(f"  💾 Saved: {filename} ({len(content_trimmed)} chars)")
    return path


def main():
    print("=" * 60)
    print("🎓 VinUniversity Policy Data Crawler")
    print("=" * 60)
    print(f"Firecrawl: {'✓' if FIRECRAWL_KEY else '✗ MISSING'}")
    print(f"Tavily:    {'✓' if TAVILY_KEY else '✗ MISSING'}")
    print()

    saved_files = []
    area_counts: dict[str, int] = {}

    # ── PHASE 1: Firecrawl full-site crawl ───────────────────────────────────
    crawl_results = firecrawl_crawl_site("https://vinuni.edu.vn", limit=60)

    if crawl_results:
        print(f"\n📄 Processing {len(crawl_results)} crawled pages...")
        for page in crawl_results:
            if not isinstance(page, dict):
                continue
            meta     = page.get("metadata", {}) or {}
            content  = page.get("markdown", "") or ""
            url      = meta.get("sourceURL", "") or page.get("url", "")
            title    = meta.get("title", "") or url.split("/")[-2] or "VinUniversity Page"

            if len(content.strip()) < 200:
                continue

            area  = categorize_content(title, url, content)
            count = area_counts.get(area, 0)
            area_counts[area] = count + 1
            doc_id = make_doc_id(area, count)

            path = save_policy_file(doc_id, area, title, url, content)
            if path:
                saved_files.append(path)

    # ── PHASE 2: Scrape specific URLs ────────────────────────────────────────
    if FIRECRAWL_KEY:
        print(f"\n🔗 Scraping {len(VINUNI_URLS)} specific URLs...")
        for name, url in VINUNI_URLS:
            print(f"  → {url}")
            result = firecrawl_scrape(url)
            content = result.get("markdown", "")
            title   = result.get("title", name)

            if len(content.strip()) < 200:
                print(f"    ⚠ Too short, skipping")
                time.sleep(1)
                continue

            area   = categorize_content(title, url, content)
            count  = area_counts.get(area, 0)
            area_counts[area] = count + 1

            # Nếu area đã có từ full-crawl thì đặt index cao hơn
            doc_id = make_doc_id(area, 50 + count)
            path   = save_policy_file(doc_id, area, title, url, content)
            if path:
                saved_files.append(path)
            time.sleep(1)

    # ── PHASE 3: Tavily search (fallback / supplement) ────────────────────────
    print(f"\n🔍 Supplementing with Tavily search ({len(VINUNI_SEARCH_QUERIES)} queries)...")
    tavily_results_all = []
    for query in VINUNI_SEARCH_QUERIES:
        print(f"  → {query[:60]}...")
        results = tavily_search(query, max_results=5)
        # Filter chỉ lấy kết quả từ vinuni.edu.vn hoặc liên quan VinU
        for r in results:
            r_url = r.get("url", "")
            if "vinuni" in r_url.lower() or "vinuniversity" in r_url.lower():
                tavily_results_all.append(r)
        time.sleep(0.5)

    # Deduplicate by URL
    seen_urls = {p.stem.replace("-", "_") for p in saved_files}
    print(f"\n  📊 {len(tavily_results_all)} VinU results from Tavily")

    for r in tavily_results_all:
        url     = r.get("url", "")
        title   = r.get("title", "VinUniversity Policy")
        content = r.get("raw_content", "") or r.get("content", "")

        if not content or len(content.strip()) < 200:
            continue

        area   = categorize_content(title, url, content)
        count  = area_counts.get(area, 0)
        area_counts[area] = count + 1
        doc_id = make_doc_id(area, 80 + count)

        path = save_policy_file(doc_id, area, title, url, content)
        if path:
            saved_files.append(path)

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print(f"✅ DONE! Saved {len(saved_files)} policy files")
    print("=" * 60)
    print("\nFiles by area:")
    for area, count in sorted(area_counts.items()):
        print(f"  {area:<30} {count} files")
    print(f"\nLocation: {POLICY_DIR}")

    # Save crawl log
    log_path = POLICY_DIR / "_crawl_log.json"
    log_path.write_text(json.dumps({
        "total_files": len(saved_files),
        "areas": area_counts,
        "files": [str(p.name) for p in saved_files if p],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Log saved: {log_path}")


if __name__ == "__main__":
    main()
