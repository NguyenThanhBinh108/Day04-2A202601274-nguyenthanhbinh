"""
build_policy_agent.py
=====================
Cập nhật system_prompt.md và tools.yaml phù hợp với VinUniversity Policy Assistant
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

SYSTEM_PROMPT = """\
Bạn là **VinU Policy Assistant** — trợ lý tra cứu quy định nội bộ chính thức của **Đại học VinUniversity**.

## Vai trò
Trả lời mọi câu hỏi về quy định, chính sách, thủ tục của VinUniversity dựa trên tài liệu chính thức.
Luôn trích dẫn nguồn rõ ràng: tên tài liệu, mục/điều khoản, ngày hiệu lực.

## Nguyên tắc bắt buộc
1. **Luôn dùng `policy` tool trước** — tra cứu tài liệu nội bộ VinU trước khi trả lời bất kỳ câu hỏi nào về quy định.
2. **Nếu không tìm thấy trong policy** → dùng `lookup` hoặc `fetch` để tìm trên website chính thức vinuni.edu.vn.
3. **Mỗi câu trả lời PHẢI có phần Nguồn** — ghi rõ: tên tài liệu, URL (nếu có), ngày hiệu lực.
4. **Trả lời bằng tiếng Việt** trừ khi người dùng hỏi bằng tiếng Anh.
5. **Không bịa đặt** — nếu không tìm thấy thông tin, nói thẳng "Tôi không tìm thấy quy định này, vui lòng liên hệ phòng ban liên quan."

## Cách trả lời
- Đưa câu trả lời ngắn gọn, đúng trọng tâm
- Trích dẫn đúng điều khoản, mục cụ thể
- Cuối mỗi câu trả lời, hiển thị:
  ```
  📖 Nguồn: [Tên tài liệu] | [URL nếu có] | Hiệu lực: [ngày]
  ```
- Nếu có nhiều nguồn liên quan, liệt kê tất cả

## Phạm vi hỗ trợ
- Quy định học thuật (học bổng, học phí, điểm số, tốt nghiệp)
- Quy định sinh viên (kỷ luật, đạo đức, hành vi)
- Thủ tục hành chính (nhập học, đăng ký môn, nghỉ học)
- Quy định nghiên cứu và liêm chính học thuật
- Dịch vụ sinh viên (thư viện, IT, y tế)
- Lịch học, lịch thi, deadline quan trọng

## Ví dụ câu hỏi bạn có thể trả lời
- "Quy định vắng học bao nhiêu % thì bị cấm thi?"
- "Học bổng VinUniversity có những loại nào?"
- "Điểm GPA tối thiểu để không bị cảnh báo học vụ là bao nhiêu?"
- "Làm thế nào để xin miễn học một môn?"
- "Quy định về đạo văn ở VinU như thế nào?"
"""

TOOLS_YAML = """\
# VinUniversity Policy Assistant — Tool Declarations
# Tên tool phải khớp với TOOL_FUNCTIONS trong tools/__init__.py
tools:

  # ── Tool chính: Tra cứu tài liệu nội bộ VinU ──────────────────────────────
  - name: policy
    description: >
      Tra cứu tài liệu quy định nội bộ chính thức của VinUniversity.
      LUÔN gọi tool này trước khi trả lời bất kỳ câu hỏi nào về quy định,
      chính sách, thủ tục của VinUniversity.
      Trả về nội dung tài liệu kèm nguồn (doc_id, title, source, effective_date).
    parameters:
      type: object
      properties:
        query:
          type: string
          description: "Câu hỏi hoặc từ khóa cần tra cứu (VD: 'quy định vắng học', 'học bổng merit', 'đạo văn')"
        policy_area:
          type: string
          enum:
            - all
            - academic_integrity
            - grading_policy
            - student_conduct
            - attendance_policy
            - tuition_fees
            - scholarship_policy
            - admissions_policy
            - research_policy
            - it_usage_policy
            - library_policy
            - student_services
            - general_policy
          default: "all"
          description: "Nhóm quy định cần tra cứu. Dùng 'all' nếu không chắc chắn."
        top_k:
          type: integer
          default: 5
          description: "Số lượng kết quả trả về (nên để 5 để có đủ ngữ cảnh)"
      required: [query]

  # ── Tìm kiếm web: bổ sung khi policy không có ────────────────────────────
  - name: lookup
    description: >
      Tìm kiếm trên internet — dùng khi policy tool không có đủ thông tin.
      Ưu tiên tìm trên vinuni.edu.vn.
      VD: query="site:vinuni.edu.vn academic integrity policy"
    parameters:
      type: object
      properties:
        query:
          type: string
          description: "Từ khóa tìm kiếm. Thêm 'site:vinuni.edu.vn' để lọc kết quả VinU."
        topic:
          type: string
          enum: [general, news]
          default: "general"
        timeframe:
          type: string
          enum: [day, week, month, year]
          default: "year"
        max_results:
          type: integer
          default: 5
      required: [query]

  # ── Đọc trang web: lấy nội dung đầy đủ ──────────────────────────────────
  - name: fetch
    description: >
      Đọc toàn bộ nội dung một trang web cụ thể của VinUniversity.
      Dùng khi biết chính xác URL cần đọc.
      VD: url="https://vinuni.edu.vn/admissions/scholarships/"
    parameters:
      type: object
      properties:
        url:
          type: string
          description: "URL đầy đủ của trang cần đọc"
      required: [url]

  # ── Hỏi thêm người dùng: khi cần làm rõ ─────────────────────────────────
  - name: clarify
    description: >
      Hỏi người dùng để làm rõ thông tin khi câu hỏi quá mơ hồ và không thể
      đoán được họ đang hỏi về quy định nào. Chỉ dùng khi thực sự cần thiết.
    parameters:
      type: object
      properties:
        question:
          type: string
          description: "Câu hỏi để làm rõ yêu cầu"
        response_type:
          type: string
          enum: [text, yes_no, choice]
          default: "text"
        options:
          type: array
          items: {type: string}
          default: []
      required: [question]

  # ── Format: định dạng câu trả lời ────────────────────────────────────────
  - name: format
    description: >
      Định dạng kết quả policy thành văn bản có cấu trúc đẹp với nguồn trích dẫn.
      Dùng sau khi đã thu thập đủ thông tin từ policy/lookup/fetch.
    parameters:
      type: object
      properties:
        items:
          type: array
          description: "Danh sách các mục policy đã tra cứu được"
          items:
            type: object
            properties:
              title: {type: string}
              url: {type: string}
              source: {type: string}
              summary: {type: string}
              section: {type: string}
        template:
          type: string
          enum: [brief, sections, bullets, thread, daily_ai_vn]
          default: "sections"
          description: "Dùng 'sections' cho policy response, 'brief' cho câu trả lời ngắn"
        headline:
          type: string
          default: ""
      required: [items, template]
"""


def main():
    # Cập nhật system prompt
    sp_path = ROOT / "artifacts" / "system_prompt.md"
    sp_path.write_text(SYSTEM_PROMPT, encoding="utf-8")
    print(f"✅ Updated: {sp_path}")

    # Cập nhật tools.yaml
    tools_path = ROOT / "artifacts" / "tools.yaml"
    tools_path.write_text(TOOLS_YAML, encoding="utf-8")
    print(f"✅ Updated: {tools_path}")

    print("\n🎓 VinU Policy Assistant configured!")
    print("Run: python chat.py --provider openrouter --version v1")


if __name__ == "__main__":
    main()
