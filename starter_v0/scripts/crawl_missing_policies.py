"""
crawl_missing_policies.py  —  Bước 2 / 3
==========================================
Crawl 8 policies còn thiếu từ policy.vinuni.edu.vn.
Tất cả URL đều là nguồn chính thức, data 100% thật.
"""
from __future__ import annotations

import os
import re
import sys
import time
import requests
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from env_loader import load_lab_env
load_lab_env(ROOT)

FIRECRAWL_KEY = os.getenv("FIRECRAWL_API_KEY", "")
POLICY_DIR    = ROOT / "company_policy"
POLICY_DIR.mkdir(exist_ok=True)

# ── 8 policies còn thiếu — URL chính thức từ policy.vinuni.edu.vn ─────────────
MISSING_POLICIES = [
    {
        "area":    "attendance_policy",
        "title":   "Student Attendance Policy",
        "url":     "https://policy.vinuni.edu.vn/all-policies/student-attendance-policy/",
        "tags":    ["attendance", "absence", "participation", "vắng học", "VinUniversity"],
    },
    {
        "area":    "it_usage_policy",
        "title":   "Security Regulations in Use of AI",
        "url":     "https://policy.vinuni.edu.vn/all-policies/4647/",
        "tags":    ["AI security", "IT policy", "VinUniversity", "VSOC_IT07"],
    },
    {
        "area":    "student_services",
        "title":   "VinUni Dormitory Room Allocation Principles",
        "url":     "https://policy.vinuni.edu.vn/all-policies/vinuni-dormitory-room-allocation-principles-first-year-students-only/",
        "tags":    ["dormitory", "ký túc xá", "housing", "student services", "VinUniversity"],
    },
    {
        "area":    "student_services",
        "title":   "Study Visa Guidelines for International Students",
        "url":     "https://policy.vinuni.edu.vn/all-policies/study-visa-guidelines-for-international-students/",
        "tags":    ["visa", "international students", "immigration", "student services", "VinUniversity"],
    },
    {
        "area":    "grading_policy",
        "title":   "Procedure for Undergraduate Graduation",
        "url":     "https://policy.vinuni.edu.vn/all-policies/procedure-for-undergraduate-graduation/",
        "tags":    ["graduation", "commencement", "degree completion", "undergraduate", "VinUniversity"],
    },
    {
        "area":    "student_services",
        "title":   "Emergency Response Guidelines — Mental Health and Physical Health",
        "url":     "https://policy.vinuni.edu.vn/all-policies/emergency-response-guidelines-mental-health-and-physical-health-learners-incidents/",
        "tags":    ["emergency", "mental health", "physical health", "safety", "VinUniversity"],
    },
    {
        "area":    "student_services",
        "title":   "Guidance for Fitness to Study Procedures",
        "url":     "https://policy.vinuni.edu.vn/all-policies/guidance-for-fitness-to-study-procedures/",
        "tags":    ["fitness to study", "health", "academic accommodation", "VinUniversity"],
    },
    {
        "area":    "student_services",
        "title":   "Formal Escalation Management Procedure for Student Complaints",
        "url":     "https://policy.vinuni.edu.vn/all-policies/formal-escalation-management-procedure-for-students/",
        "tags":    ["complaint", "escalation", "grievance", "student services", "VinUniversity"],
    },
    {
        "area":    "student_services",
        "title":   "Safe and Supported Pregnancy Policy",
        "url":     "https://policy.vinuni.edu.vn/all-policies/safe-and-supported-pregnancy-policy/",
        "tags":    ["pregnancy", "health", "student support", "VinUniversity"],
    },
    {
        "area":    "research_policy",
        "title":   "Research Integrity Policy",
        "url":     "https://policy.vinuni.edu.vn/all-policies/research-integrity-policy/",
        "tags":    ["research integrity", "ethics", "publication", "VinUniversity", "POL-RMO-003"],
    },
    {
        "area":    "general_policy",
        "title":   "VinUniversity Diversity, Equity, and Inclusion Policy",
        "url":     "https://policy.vinuni.edu.vn/all-policies/vinuniversity-diversity-equity-and-inclusion-dei-policy/",
        "tags":    ["DEI", "diversity", "equity", "inclusion", "VinUniversity"],
    },
    {
        "area":    "it_usage_policy",
        "title":   "General Regulations on Information Security",
        "url":     "https://policy.vinuni.edu.vn/all-policies/general-regulations-on-information-security/",
        "tags":    ["information security", "IT", "VSOC_IT04", "VinUniversity"],
    },
    {
        "area":    "student_services",
        "title":   "Regulations on Management of Laboratories",
        "url":     "https://policy.vinuni.edu.vn/all-policies/regulations-on-management-of-laboratories/",
        "tags":    ["laboratory", "lab management", "safety", "research", "VinUniversity"],
    },
]

IMAGE_PATTERN   = re.compile(r"!\[[^\]]*\]\([^)]*\)\s*\n?")
FOOTER_PATTERNS = [
    re.compile(r"Copyright\s*©\s*\d{4}\s+VinUni\.?\s*\n?", re.IGNORECASE),
    re.compile(r"All Rights? Reserved\.?\s*\n?", re.IGNORECASE),
    re.compile(r"Privacy Policy\s*\n?", re.IGNORECASE),
]


def strip_noise(body: str) -> str:
    text = IMAGE_PATTERN.sub("", body)
    for pat in FOOTER_PATTERNS:
        text = pat.sub("", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_text_len(body: str) -> int:
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", body)
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"\s+", " ", t)
    return len(t.strip())


def make_slug(title: str, area: str, max_len: int = 40) -> str:
    area_prefix = {
        "attendance_policy":  "attendance",
        "it_usage_policy":    "it",
        "student_services":   "services",
        "grading_policy":     "grading",
        "research_policy":    "research",
        "general_policy":     "general",
    }.get(area, area[:8])
    s = re.sub(r"[^a-z0-9\s-]", "", title.lower())
    s = re.sub(r"[\s-]+", "-", s).strip("-")[:max_len].rstrip("-")
    return f"vinuni-{area_prefix}-{s}"


def firecrawl_scrape(url: str, timeout: int = 50) -> dict:
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
        print(f"    ⚠ Firecrawl error: {e}")
        return {}


def save(policy: dict, content: str, crawled_title: str) -> Path | None:
    if clean_text_len(content) < 300:
        return None

    clean_content = strip_noise(content)
    title         = crawled_title or policy["title"]
    doc_id        = make_slug(policy["title"], policy["area"])
    tags_str      = "[" + ", ".join(f'"{t}"' for t in policy["tags"]) + "]"
    area_display  = policy["area"].replace("_", " ").title()

    md = (
        "---\n"
        f"doc_id: {doc_id}\n"
        f"policy_area: {policy['area']}\n"
        f"title: {title}\n"
        f"source: VinUniversity Official — {area_display}\n"
        f"source_url: {policy['url']}\n"
        f"effective_date: 2024-09-01\n"
        f"tags: {tags_str}\n"
        f"crawled_at: {datetime.now().strftime('%Y-%m-%d')}\n"
        "---\n\n"
        + clean_content[:9500]
        + "\n"
    )

    path = POLICY_DIR / f"{doc_id}.md"
    path.write_text(md, encoding="utf-8")
    return path


def main():
    print("=" * 68)
    print("🌐 crawl_missing_policies.py  —  Bước 2/3")
    print(f"   Target: {len(MISSING_POLICIES)} missing policies")
    print(f"   Source: policy.vinuni.edu.vn (chính thức)")
    print("=" * 68)

    if not FIRECRAWL_KEY:
        print("❌ Thiếu FIRECRAWL_API_KEY! Dừng lại.")
        sys.exit(1)

    saved   = []
    skipped = []

    for policy in MISSING_POLICIES:
        print(f"\n  → [{policy['area'][:15]}] {policy['title'][:50]}")
        print(f"     {policy['url']}")

        # Kiểm tra đã có file chưa
        existing = list(POLICY_DIR.glob(f"vinuni-*-{make_slug(policy['title'], policy['area'])[7:]}*.md"))
        if existing:
            print(f"     ⏭  Đã có: {existing[0].name}")
            skipped.append(policy["title"])
            continue

        result   = firecrawl_scrape(policy["url"])
        content  = result.get("markdown", "")
        cr_title = result.get("title", "")

        text_len = clean_text_len(content)
        if text_len < 300:
            print(f"     ⚠  Quá ngắn ({text_len} chars) — bỏ qua")
            skipped.append(policy["title"])
            time.sleep(1)
            continue

        path = save(policy, content, cr_title)
        if path:
            print(f"     💾 Saved: {path.name} ({text_len} chars)")
            saved.append({"title": policy["title"], "file": path.name, "url": policy["url"]})
        else:
            skipped.append(policy["title"])

        time.sleep(2)  # Rate limit friendly

    print(f"\n{'='*68}")
    print(f"✅ CRAWL MISSING POLICIES HOÀN THÀNH")
    print(f"   Đã lưu  : {len(saved)} files mới")
    print(f"   Bỏ qua  : {len(skipped)}")
    print("=" * 68)
    if saved:
        print("\nFiles mới:")
        for s in saved:
            print(f"  ✅ {s['file']}")
            print(f"     ← {s['url']}")


if __name__ == "__main__":
    main()
