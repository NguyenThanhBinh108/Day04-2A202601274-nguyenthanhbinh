"""
cleanup_policy.py  (v2)
=======================
Xóa toàn bộ mock data + trash data, chỉ giữ file có nội dung THẬT từ nguồn chính thức VinUniversity.

Tiêu chí GIỮ LẠI (tất cả phải đúng):
  1. source_url phải là domain chính thức (vinuni.edu.vn hoặc policy.vinuni.edu.vn)
  2. Nội dung text thực >= 500 ký tự (sau khi loại bỏ image/link markdown)
  3. Title không phải trang lỗi (404, Page not found, Error...)
  4. Không phải file mock được tạo tay
"""
from __future__ import annotations

import re
import sys
import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).parent.parent
POLICY_DIR = ROOT / "company_policy"

# ── Files mock tạo tay — xóa bắt buộc ───────────────────────────────────────
FORCE_DELETE = {
    "ai-research-policy.md",
    "data-privacy-policy.md",
    "external-publishing-policy.md",
    "source-citation-policy.md",
    "tool-usage-policy.md",
    "vinuni-academic-integrity.md",
    "vinuni-admissions-policy.md",
    "vinuni-attendance-policy.md",
    "vinuni-grading-policy.md",
    "vinuni-it-ai-policy.md",
    "vinuni-scholarship-policy.md",
    "vinuni-student-conduct.md",
    "_crawl_log.json",
}

# ── Domain chính thức được chấp nhận ─────────────────────────────────────────
OFFICIAL_DOMAINS = {
    "vinuni.edu.vn",
    "policy.vinuni.edu.vn",
    "tuyensinhvinuni.edu.vn",
}

# ── Domain bị từ chối (không phải nguồn chính thức) ──────────────────────────
REJECTED_DOMAINS = {
    "facebook.com", "instagram.com", "twitter.com", "youtube.com",
    "linkedin.com", "tiktok.com", "reddit.com",
}

BAD_TITLE_KEYWORDS = {"page not found", "404", "error", "access denied", "forbidden", "not found"}
MIN_TEXT_CHARS = 500


def parse_frontmatter(path: Path) -> tuple[dict, str]:
    raw = path.read_text(encoding="utf-8")
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) == 3:
            import yaml
            try:
                meta = yaml.safe_load(parts[1]) or {}
                return dict(meta), parts[2].strip()
            except Exception:
                pass
    return {}, raw.strip()


def clean_text(body: str) -> str:
    """Loại bỏ markdown noise, trả về text thuần."""
    t = re.sub(r"!\[.*?\]\(.*?\)", " ", body)      # images
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)  # links → keep text
    t = re.sub(r"#+\s*", "", t)                     # headings
    t = re.sub(r"[|]{1,}", " ", t)                  # table pipes
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def get_domain(url: str) -> str:
    m = re.search(r"https?://([^/]+)", url)
    return m.group(1).lstrip("www.") if m else ""


def is_official_url(url: str) -> bool:
    domain = get_domain(url)
    # Chấp nhận: vinuni.edu.vn và các subdomain của nó
    return domain.endswith("vinuni.edu.vn")


def is_rejected_url(url: str) -> bool:
    domain = get_domain(url)
    return any(domain.endswith(d) for d in REJECTED_DOMAINS)


def judge(path: Path, meta: dict, body: str) -> tuple[bool, str]:
    """Trả về (should_delete, reason)."""

    # Force delete
    if path.name in FORCE_DELETE:
        return True, "mock_or_temp_file"

    # Title lỗi
    title = str(meta.get("title", "")).lower()
    if any(k in title for k in BAD_TITLE_KEYWORDS):
        return True, f"error_page_title: {meta.get('title')}"

    # Kiểm tra source_url
    source_url = str(meta.get("source_url", "")).strip()
    if not source_url or not source_url.startswith("http"):
        return True, "missing_source_url"

    if is_rejected_url(source_url):
        return True, f"non_official_source: {get_domain(source_url)}"

    if not is_official_url(source_url):
        return True, f"unofficial_source: {get_domain(source_url)}"

    # Nội dung quá ngắn / trang 404
    text = clean_text(body)
    if len(text) < MIN_TEXT_CHARS:
        return True, f"too_short: {len(text)} chars"

    bad_content = [
        "sorry, this page either moved",
        "return to home page",
        "404 not found",
    ]
    body_lower = body.lower()
    for bc in bad_content:
        if bc in body_lower and len(text) < 300:
            return True, f"404_content: {bc}"

    return False, ""


def main():
    import yaml  # noqa: ensure available

    print("=" * 65)
    print("🧹 VinU Policy Cleanup v2 — Chỉ giữ nguồn CHÍNH THỨC VinU")
    print("=" * 65)

    all_files = sorted(POLICY_DIR.glob("*.md"))
    print(f"Tổng số files hiện có: {len(all_files)}\n")

    deleted = []
    kept    = []

    for path in all_files:
        if path.name == "README.md":
            continue

        meta, body = parse_frontmatter(path)
        should_del, reason = judge(path, meta, body)

        source_url = meta.get("source_url", "")
        text_len   = len(clean_text(body))

        if should_del:
            print(f"  🗑  {path.name:<50} [{reason}]")
            path.unlink()
            deleted.append({"file": path.name, "reason": reason})
        else:
            print(f"  ✅  {path.name:<50} {text_len:>5} chars | {source_url[:55]}")
            kept.append({
                "file":           path.name,
                "title":          meta.get("title", ""),
                "policy_area":    meta.get("policy_area", ""),
                "source":         meta.get("source", ""),
                "source_url":     source_url,
                "effective_date": str(meta.get("effective_date", "")),
                "text_chars":     text_len,
            })

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{'='*65}")
    print(f"🗑  Đã xóa  : {len(deleted)} files (mock/404/unofficial)")
    print(f"✅ Giữ lại : {len(kept)} files (data thật từ vinuni.edu.vn)")
    print(f"{'='*65}")

    area_count = Counter(f["policy_area"] for f in kept)
    print("\n📊 Phân bố theo policy area:")
    for area, count in sorted(area_count.items()):
        print(f"   {area:<38} {count:>2} files")

    # Lưu index
    index_path = POLICY_DIR / "_real_data_index.json"
    index_path.write_text(json.dumps({
        "total_real_files":    len(kept),
        "total_deleted":       len(deleted),
        "policy_areas":        dict(area_count),
        "files":               kept,
        "deleted_log":         deleted,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n📋 Index: {index_path}")

    # Cập nhật README
    readme = POLICY_DIR / "README.md"
    readme.write_text(
        f"# VinUniversity Policy Knowledge Base\n\n"
        f"**{len(kept)} files** — Tất cả data thật từ nguồn chính thức **vinuni.edu.vn** và **policy.vinuni.edu.vn**.\n"
        f"Không có mock data. Mỗi file có `source_url` trỏ đến trang VinU chính thức.\n\n"
        f"## Policy Areas\n"
        + "\n".join(f"- `{a}`: {c} files" for a, c in sorted(area_count.items())) +
        "\n\n## Nguồn dữ liệu\n"
        "- [policy.vinuni.edu.vn](https://policy.vinuni.edu.vn) — Policy portal chính thức\n"
        "- [vinuni.edu.vn](https://vinuni.edu.vn) — Website chính thức VinUniversity\n"
        "- Crawl qua Firecrawl API + Tavily Search API\n\n"
        "## Cách dùng\n"
        "Model gọi `policy(query, policy_area, top_k)` → Python search → trả về `facts + source_url + effective_date`.\n",
        encoding="utf-8"
    )
    print(f"📝 README: {readme}")

    if not kept:
        print("\n⚠️  CẢNH BÁO: Không còn file nào! Cần crawl lại dữ liệu.")
        sys.exit(1)


if __name__ == "__main__":
    main()
