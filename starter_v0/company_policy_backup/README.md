# VinUniversity Policy Knowledge Base

**39 files** — Tất cả data thật từ nguồn chính thức **vinuni.edu.vn** và **policy.vinuni.edu.vn**.
Không có mock data. Mỗi file có `source_url` trỏ đến trang VinU chính thức.

## Policy Areas
- `academic_integrity`: 6 files
- `admissions_policy`: 7 files
- `attendance_policy`: 1 files
- `grading_policy`: 2 files
- `it_usage_policy`: 11 files
- `library_policy`: 2 files
- `research_policy`: 1 files
- `scholarship_policy`: 2 files
- `student_conduct`: 3 files
- `tuition_fees`: 4 files

## Nguồn dữ liệu
- [policy.vinuni.edu.vn](https://policy.vinuni.edu.vn) — Policy portal chính thức
- [vinuni.edu.vn](https://vinuni.edu.vn) — Website chính thức VinUniversity
- Crawl qua Firecrawl API + Tavily Search API

## Cách dùng
Model gọi `policy(query, policy_area, top_k)` → Python search → trả về `facts + source_url + effective_date`.
