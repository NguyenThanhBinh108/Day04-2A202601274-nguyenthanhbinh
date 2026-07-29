# VinUniversity Policy Knowledge Base — Mô tả chi tiết Data

> 📅 Cập nhật: 2026-07-29 | Tác giả: Trịnh Hải Đăng (2A202601602)

---

## 📁 Cấu trúc thư mục tổng quan

```
starter_v0/
│
├── company_policy/               ← 🎯 THMỤC CHÍNH — Chứa toàn bộ data chính sách
│   ├── README.md                 ← Index tổng quan (tự sinh bởi build_final_index.py)
│   ├── _policy_index.json        ← Machine-readable index đầy đủ (JSON)
│   ├── _final_cleanup_log.json   ← Log của lần cleanup cuối
│   └── vinuni-*.md               ← ~60 files policy data thật
│
├── company_policy_backup/        ← Backup trước khi normalize (tham khảo)
│
├── scripts/                      ← Pipeline scripts
│   ├── crawl_vinuni.py           ← Crawler ban đầu (Firecrawl + Tavily)
│   ├── crawl_missing_policies.py ← Crawler 13 policies còn thiếu
│   ├── cleanup_policy.py         ← Cleanup lần 1 (xóa mock, filter URL)
│   ├── normalize_policy.py       ← Normalize (strip ảnh, fix area, dedup, rename)
│   ├── final_cleanup.py          ← Cleanup lần cuối (xóa file hỏng, fix area)
│   └── build_final_index.py      ← Tạo index + README
│
├── artifacts/
│   ├── system_prompt.md          ← Prompt VinU Policy Assistant
│   └── tools.yaml                ← Tool declarations cho agent
│
├── RUN_PIPELINE.bat              ← Chạy toàn bộ pipeline (Windows)
├── DATA_DESCRIPTION.md           ← File này
└── .env                          ← API keys (không commit)
```

---

## 📂 Chi tiết thư mục `company_policy/`

### Convention đặt tên file

```
vinuni-{area_short}-{topic-slug}.md

area_short mapping:
  academic   → academic_integrity
  grading    → grading_policy
  conduct    → student_conduct
  attendance → attendance_policy
  tuition    → tuition_fees
  scholarship→ scholarship_policy
  admissions → admissions_policy
  research   → research_policy
  it         → it_usage_policy
  library    → library_policy
  services   → student_services
  general    → general_policy
```

### Cấu trúc frontmatter mỗi file

```yaml
---
doc_id: vinuni-academic-student-academic-integrity-vinuni-policy
policy_area: academic_integrity
title: Student Academic Integrity - VinUni Policy
source: VinUniversity Official — Academic Integrity
source_url: https://policy.vinuni.edu.vn/all-policies/student-academic-integrity
effective_date: 2024-09-01
tags: ["academic integrity", "plagiarism", "cheating", "VinUniversity"]
crawled_at: 2026-07-29
---
[Nội dung policy thật từ VinUniversity...]
```

---

## 📊 Danh sách files theo Policy Area

### 1. 📚 `academic_integrity` — Liêm chính học thuật

| File | Tiêu đề | Nguồn |
|------|---------|-------|
| `vinuni-academic-student-academic-integrity-vinuni-policy.md` | Student Academic Integrity Policy | [policy.vinuni.edu.vn](https://policy.vinuni.edu.vn/all-policies/student-academic-integrity) |
| `vinuni-academic-research-integrity-policy-vinuni-policy.md` | Research Integrity Policy | [policy.vinuni.edu.vn](https://policy.vinuni.edu.vn/all-policies/research-integrity-policy) |

**Coverage:** Quy định đạo văn, gian lận, phân loại vi phạm Tier 1-4, sanctions.

---

### 2. 📊 `grading_policy` — Điểm số & Học vụ

| File | Tiêu đề | Nguồn |
|------|---------|-------|
| `vinuni-grading-exams-grades-registrar.md` | Exams & Grades - Registrar | [registrar.vinuni.edu.vn](https://registrar.vinuni.edu.vn/academics/exams-grades) |
| `vinuni-grading-assessment-guideline-for-undergraduate-p.md` | Assessment Guidelines (Undergrad) | [policy.vinuni.edu.vn](https://policy.vinuni.edu.vn/) |
| `vinuni-grading-procedure-for-undergraduate-graduation.md` | Procedure for Undergraduate Graduation | [policy.vinuni.edu.vn](https://policy.vinuni.edu.vn/) |
| `vinuni-grading-iu-kin-duy-tr-hc-bngh-tr-ti-chnh.md` | Điều kiện duy trì HB/HTTC (PDF) | [vinuni.edu.vn](https://vinuni.edu.vn/wp-content/uploads/2023/10/2023-2024-Dieu-kien-duy-tri-HB_HTTC-1.pdf) |

**Coverage:** Thang điểm A-F (4.0 scale), GPA calculation, graduation procedure.

---

### 3. ⚖️ `student_conduct` — Quy tắc ứng xử

| File | Tiêu đề | Nguồn |
|------|---------|-------|
| `vinuni-conduct-student-code-of-conduct-vinuni-policy-vi.md` | Student Code of Conduct | [policy.vinuni.edu.vn](https://policy.vinuni.edu.vn/all-policies/student-affairs-regulations-code-of-conduct) |
| `vinuni-conduct-employees-code-of-conduct-vinuni-policy.md` | Employees Code of Conduct | [policy.vinuni.edu.vn](https://policy.vinuni.edu.vn/) |
| `vinuni-conduct-sexual-misconduct-and-response-vinuni-po.md` | Sexual Misconduct Policy | [policy.vinuni.edu.vn](https://policy.vinuni.edu.vn/) |
| `vinuni-conduct-appendix-iv-procedure-for-student-code-o.md` | Appendix IV - Conduct Procedure | [policy.vinuni.edu.vn](https://policy.vinuni.edu.vn/) |
| `vinuni-conduct-student-incident-case-if-the-complainant.md` | Student Incident Case Procedure | [policy.vinuni.edu.vn](https://policy.vinuni.edu.vn/) |

---

### 4. 🕐 `attendance_policy` — Chuyên cần

| File | Tiêu đề | Nguồn |
|------|---------|-------|
| `vinuni-attendance-attendance-policy-at-medical-doctor-prog.md` | Attendance Policy (MD Program) | [policy.vinuni.edu.vn](https://policy.vinuni.edu.vn/) |

> ⚠️ **Gap**: Attendance Policy chung cho UG chưa có file riêng. Thông tin vắng học nằm trong Academic Regulations (general files).

---

### 5. 💰 `tuition_fees` — Học phí

| File | Tiêu đề | Nguồn |
|------|---------|-------|
| `vinuni-tuition-financial-regulations-and-tariff-for-stu.md` | Financial Regulations & Tariff | [policy.vinuni.edu.vn](https://policy.vinuni.edu.vn/all-policies/financial-regulations-and-tariff-for-student-2/) |
| `vinuni-tuition-tuition-fee-and-financial-aids-admission.md` | Tuition Fee & Financial Aids | [vinuni.edu.vn](https://vinuni.edu.vn/admissions/tuition-and-fees/) |
| `vinuni-tuition-hc-ph-hc-bng-v-h-tr-ti-chnh-admission.md` | Học phí, HB & HTTC (VI) | [vinuni.edu.vn](https://vinuni.edu.vn/) |
| `vinuni-tuition-quy-nh-ti-chnh-v-biu-ph-mc-lc.md` | Quy định tài chính & Biểu phí (VI) | [policy.vinuni.edu.vn](https://policy.vinuni.edu.vn/) |

---

### 6. 🎓 `scholarship_policy` — Học bổng

| File | Tiêu đề | Nguồn |
|------|---------|-------|
| `vinuni-scholarship-scholarships-admission.md` | Scholarships - Admissions | [vinuni.edu.vn](https://vinuni.edu.vn/admissions/scholarships/) |
| `vinuni-scholarship-guidelines-for-maintaining-entry-scholar.md` | Guidelines Maintaining Entry Scholarship | [policy.vinuni.edu.vn](https://policy.vinuni.edu.vn/all-policies/criteria-to-maintain-the-entry-scholarship-and-financial-aid-support/) |
| `vinuni-scholarship-guidelines-for-student-financial-support.md` | Guidelines for Student Financial Support | [policy.vinuni.edu.vn](https://policy.vinuni.edu.vn/) |
| `vinuni-scholarship-quy-nh-duy-tr-hc-bng-u-vo-v-h-tr.md` | Điều kiện duy trì HB đầu vào | [vinuni.edu.vn](https://vinuni.edu.vn/) |
| `vinuni-grading-iu-kin-duy-tr-hc-bngh-tr-ti-chnh.md` | Điều kiện duy trì HB (song ngữ PDF) | [vinuni.edu.vn](https://vinuni.edu.vn/wp-content/uploads/2023/10/) |

**Coverage:** HB Tài năng Full/Partial, WIT, Vingroup Family, CGPA duy trì.

---

### 7. 🚪 `admissions_policy` — Tuyển sinh

| File | Tiêu đề | Nguồn |
|------|---------|-------|
| `vinuni-admissions-vinuniversity-admissions.md` | VinUniversity Admissions | [vinuni.edu.vn](https://vinuni.edu.vn/admissions/) |
| `vinuni-admissions-admissions-regulations-for-undergraduate.md` | Admissions Regs - UG | [policy.vinuni.edu.vn](https://policy.vinuni.edu.vn/) |
| `vinuni-admissions-admissions-regulations-for-graduate-medi.md` | Admissions Regs - Grad Medical | [policy.vinuni.edu.vn](https://policy.vinuni.edu.vn/) |
| `vinuni-admissions-admissions-regulations-for-postgraduate.md` | Admissions Regs - Postgraduate | [policy.vinuni.edu.vn](https://policy.vinuni.edu.vn/) |
| `vinuni-admissions-english-language-requirements-for-underg.md` | English Language Requirements | [policy.vinuni.edu.vn](https://policy.vinuni.edu.vn/) |
| `vinuni-admissions-key-admission-deadlines-admission.md` | Key Admission Deadlines | [vinuni.edu.vn](https://vinuni.edu.vn/admissions/) |
| `vinuni-admissions-admission-criteria-admission.md` | Admission Criteria | [vinuni.edu.vn](https://vinuni.edu.vn/admissions/) |
| `vinuni-admissions-contact-vinuniversity-for-admission-and.md` | Contact for Admissions | [vinuni.edu.vn](https://vinuni.edu.vn/admissions/contact/) |

---

### 8. 🔬 `research_policy` — Nghiên cứu

| File | Tiêu đề | Nguồn |
|------|---------|-------|
| `vinuni-research-research-integrity-policy.md` | Research Integrity Policy | [policy.vinuni.edu.vn](https://policy.vinuni.edu.vn/all-policies/research-integrity-policy/) |
| `vinuni-research-research-integrity-policy-records-of-cha.md` | Research Integrity - Change Records | [policy.vinuni.edu.vn](https://policy.vinuni.edu.vn/) |
| `vinuni-research-research-support-library.md` | Research Support - Library | [library.vinuni.edu.vn](https://library.vinuni.edu.vn/) |
| `vinuni-general-regulations-on-management-of-laboratorie.md` | Regulations on Management of Labs | [policy.vinuni.edu.vn](https://policy.vinuni.edu.vn/all-policies/regulations-on-management-of-laboratories/) |

---

### 9. 💻 `it_usage_policy` — CNTT & AI

| File | Tiêu đề | Nguồn |
|------|---------|-------|
| `vinuni-it-guidelines-on-student-use-of-generative.md` | **Guidelines on Student Use of GenAI** | [policy.vinuni.edu.vn](https://policy.vinuni.edu.vn/all-policies/guidelines-on-student-use-of-generative-artificial-intelligence) |
| `vinuni-it-general-regulations-on-information-secur.md` | General Regulations on Info Security | [policy.vinuni.edu.vn](https://policy.vinuni.edu.vn/all-policies/general-regulations-on-information-security/) |
| `vinuni-it-quy-ch-o-to-i-hc-h-chnh-quy-theo-h-thng.md` | Quy chế Đào tạo Đại học (MOET format) | [registrar.vinuni.edu.vn](https://registrar.vinuni.edu.vn/) |
| `vinuni-it-chnh-sch-quy-nh-registrar.md` | Chính sách & Quy định - Registrar (VI) | [registrar.vinuni.edu.vn](https://registrar.vinuni.edu.vn/vi/) |
| `vinuni-it-policy-regulations-registrar.md` | Policy & Regulations - Registrar (EN) | [registrar.vinuni.edu.vn](https://registrar.vinuni.edu.vn/) |

---

### 10. 📖 `library_policy` — Thư viện

| File | Tiêu đề | Nguồn |
|------|---------|-------|
| `vinuni-library-e-bookstore-library.md` | E-Bookstore & Library Services | [library.vinuni.edu.vn](https://library.vinuni.edu.vn/) |
| `vinuni-it-library-access-services-policy-vinuni-po.md` | Library Access & Services Policy | [policy.vinuni.edu.vn](https://policy.vinuni.edu.vn/) |

---

### 11. 🏫 `student_services` — Dịch vụ sinh viên

| File | Tiêu đề | Nguồn |
|------|---------|-------|
| `vinuni-services-study-visa-guidelines-for-international.md` | Study Visa Guidelines | [policy.vinuni.edu.vn](https://policy.vinuni.edu.vn/all-policies/study-visa-guidelines-for-international-students/) |
| `vinuni-services-vinuni-dormitory-room-allocation-princip.md` | Dormitory Allocation Principles | [policy.vinuni.edu.vn](https://policy.vinuni.edu.vn/) |
| `vinuni-services-emergency-response-guidelines-mental-hea.md` | Emergency Response Guidelines | [policy.vinuni.edu.vn](https://policy.vinuni.edu.vn/) |
| `vinuni-services-guidance-for-fitness-to-study-procedures.md` | Fitness to Study Guidance | [policy.vinuni.edu.vn](https://policy.vinuni.edu.vn/) |
| `vinuni-services-safe-and-supported-pregnancy-policy.md` | Safe & Supported Pregnancy Policy | [policy.vinuni.edu.vn](https://policy.vinuni.edu.vn/) |
| `vinuni-services-outbound-student-exchange-procedure-vinu.md` | Outbound Student Exchange | [policy.vinuni.edu.vn](https://policy.vinuni.edu.vn/) |
| `vinuni-it-student-life-vinuni.md` | Student Life - VinUniversity | [vinuni.edu.vn](https://vinuni.edu.vn/student-life/) |
| `vinuni-library-international-student-services-experienc.md` | International Student Services | [vinuni.edu.vn](https://vinuni.edu.vn/) |

---

### 12. 📋 `general_policy` — Quy định chung

| File | Tiêu đề | Nguồn |
|------|---------|-------|
| `vinuni-general-academic-regulations-for-full-time-under.md` | Academic Regulations - UG | [policy.vinuni.edu.vn](https://policy.vinuni.edu.vn/) |
| `vinuni-general-academic-regulations-for-graduate-medica.md` | Academic Regulations - Grad Medical | [policy.vinuni.edu.vn](https://policy.vinuni.edu.vn/) |
| `vinuni-general-academic-regulations-for-master-programs.md` | Academic Regulations - Master | [policy.vinuni.edu.vn](https://policy.vinuni.edu.vn/) |
| `vinuni-general-all-policies-vinuni-policy.md` | All Policies Index (full list) | [policy.vinuni.edu.vn](https://policy.vinuni.edu.vn/all-policies/) |
| `vinuni-general-governance-structure-and-management-of-m.md` | Governance Structure | [policy.vinuni.edu.vn](https://policy.vinuni.edu.vn/) |
| `vinuni-general-undergraduate-student-guide.md` | Undergraduate Student Guide | [vinuni.edu.vn](https://vinuni.edu.vn/) |
| `vinuni-general-vinuniversity-diversity-equity-and-inclu.md` | DEI Policy | [policy.vinuni.edu.vn](https://policy.vinuni.edu.vn/) |
| `vinuni-general-2027-academic-calendar.md` | Academic Calendar 2026-2027 | [vinuni.edu.vn](https://vinuni.edu.vn/) |

---

## 🔍 Đánh giá Coverage tổng thể

| Policy Area | Files | Chất lượng | Ghi chú |
|-------------|-------|-----------|---------|
| Academic Integrity | 2 | ✅ Tốt | Tier 1-4, sanctions đầy đủ |
| Grading & Standing | 4 | ✅ Tốt | GPA scale, graduation proc |
| Student Conduct | 5 | ✅ Tốt | Code, sexual misconduct, procedure |
| Attendance | 1 | ⚠️ Ít | Chỉ MD; UG nằm trong academic regs |
| Tuition & Fees | 4 | ✅ Tốt | Biểu phí EN+VI |
| Scholarships | 5 | ✅ Tốt | Tất cả loại HB, CGPA điều kiện |
| Admissions | 8 | ✅ Tốt | UG/Grad/Postgrad, deadlines, IELTS |
| Research | 4 | ✅ Tốt | Integrity, labs |
| IT & AI | 5 | ✅ Tốt | GenAI guidelines chi tiết |
| Library | 2 | ⚠️ Vừa đủ | Có thể crawl thêm |
| Student Services | 8 | ✅ Tốt | Visa, dorm, emergency, exchange |
| General | 8 | ✅ Tốt | Academic regs đầy đủ các chương trình |

---

## ⚠️ Lưu ý quan trọng

### Files "Internal Only" — link đến Sharepoint nội bộ
Một số tài liệu trên `policy.vinuni.edu.vn` chỉ có metadata + link Sharepoint nội bộ VinGroup/VinUni:
- `vinuni-services-vinuni-dormitory-room-allocation-princip.md` — Full PDF ở Sharepoint
- `vinuni-services-emergency-response-guidelines-mental-hea.md` — Full PDF ở Sharepoint
- `vinuni-it-general-regulations-on-information-secur.md` — Full doc ở VinGroup Dataroom

→ Các files này vẫn giữ lại vì chứa metadata hợp lệ (mã văn bản, ngày ban hành, phạm vi áp dụng, link nguồn chính thức). Agent có thể trả lời metadata + hướng dẫn truy cập.

### Files tiếng Việt
Files có tên bị encode ASCII từ ký tự tiếng Việt (do slugify). Nội dung bên trong vẫn đầy đủ song ngữ VI/EN.

---

## 🔧 Scripts Pipeline — Thứ tự chạy

```powershell
# Chạy từ folder starter_v0:

# 1. Crawl data (đã chạy rồi)
# .\.venv\Scripts\python.exe scripts\crawl_vinuni.py

# 2. Final cleanup
.\.venv\Scripts\python.exe scripts\final_cleanup.py

# 3. Rebuild index + README
.\.venv\Scripts\python.exe scripts\build_final_index.py

# 4. Chạy agent
python chat.py --provider openrouter --version v1
```

---

## 🎯 Test Agent — Câu hỏi kiểm tra

| Câu hỏi | File phải match |
|---------|----------------|
| "Đạo văn Tier 3 xử lý thế nào?" | `vinuni-academic-student-academic-integrity-*` |
| "Dùng ChatGPT làm bài có vi phạm không?" | `vinuni-it-guidelines-on-student-use-of-generative` |
| "CGPA 3.2 để duy trì HB toàn phần?" | `vinuni-scholarship-guidelines-for-maintaining-*` |
| "Quy trình xin tốt nghiệp?" | `vinuni-grading-procedure-for-undergraduate-*` |
| "Học phí kỳ 2024-2025?" | `vinuni-tuition-financial-regulations-and-tariff-*` |
| "Vắng học bao nhiêu % bị cấm thi?" | `vinuni-general-academic-regulations-for-full-time-*` |
