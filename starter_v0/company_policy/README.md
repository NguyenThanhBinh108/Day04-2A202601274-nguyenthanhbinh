# VinUni Regulations KB

Kho quy chế và nội quy nội bộ của VinUniversity dùng cho agent tra cứu quy định.

Model không đọc trực tiếp các file này. Nó gọi `policy(query, policy_area, top_k)`; code Python tìm trong các file markdown ở đây và trả về từng section kèm metadata nguồn (`doc_id`, `section`, `source`, `effective_date`) để agent trích dẫn làm bằng chứng.

## Tài liệu

| doc_id | policy_area | Bản | Hiệu lực | Nguồn |
|---|---|---|---|---|
| `vinuni-student-academic-integrity` | `academic_integrity` | V3.0 | 2022-09-30 | [policy.vinuni.edu.vn](https://policy.vinuni.edu.vn/all-policies/student-academic-integrity/) |
| `vinuni-student-code-of-conduct` | `student_conduct` | V5.0 | 2025-12-24 | [policy.vinuni.edu.vn](https://policy.vinuni.edu.vn/all-policies/student-affairs-regulations-code-of-conduct/) |
| `vinuni-academic-regulations-undergraduate` | `academic_regulations` | V8.1 | 2024-10-30 | [policy.vinuni.edu.vn](https://policy.vinuni.edu.vn/all-policies/academic-regulations-for-full-time-undergraduate-programs/) |
| `vinuni-graduation-degree-conferral` | `graduation` | V1.0 | 2024-11-12 | [policy.vinuni.edu.vn](https://policy.vinuni.edu.vn/all-policies/procedure-for-undergraduate-graduation-review-and-degree-conferral/) |

Tổng 191 section. Nội dung lấy từ VinUniversity Policy Library công khai.

## Ràng buộc khi thêm tài liệu mới

Tool `policy` có ba giới hạn mà tài liệu phải tuân theo:

1. **Bắt buộc có frontmatter** — thiếu là mất hết metadata trích dẫn.
2. **Chia section bằng `##`** và giữ mỗi section dưới ~900 ký tự. `facts` bị cắt cứng ở 1000 ký tự, section quá dài sẽ bị cụt và trích dẫn mất ý nghĩa.
3. **Tránh marker của bộ lọc untrusted** — dòng bắt đầu bằng `>` hoặc chứa `ignore`, `bo qua`, `assistant:`, `system:`, `tro ly:` sẽ bị loại khỏi `facts` mà không báo lỗi.

## Lưu ý ngôn ngữ

Tài liệu quy chế viết bằng **tiếng Anh**. Truy vấn tiếng Việt cho kết quả kém vì chỉ khớp được qua `tags`. Prompt đã yêu cầu agent dịch câu hỏi sang từ khóa tiếng Anh trước khi gọi `policy`.

Dùng kho này cho quy định nội bộ VinUni. Tin tức, mạng xã hội, URL công khai và paper khoa học thì dùng các tool live tương ứng.
