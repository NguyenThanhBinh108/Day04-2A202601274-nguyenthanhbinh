# Phân công nhóm — Day 04 Lab v2 (Research Agent Tool Eval)

> File này là bảng điều phối nội bộ. Nội dung nộp bài chính vẫn nằm ở `artifacts/REPORT.md`.
> Mỗi người tự cập nhật cột **Trạng thái** trong bảng 5 khi làm xong một mục.

---

## 1. Thành viên & vai trò

| STT | Họ và tên        | MSSV        | Role                                                        | Deliverable chính chịu trách nhiệm                                                  |
| --- | ------------------- | ----------- | ----------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| 1   | Nguyễn Thanh Bình | 2A202601274 | **R1 — Team Lead / Prompt & Tool-Declaration Owner** | `system_prompt.md`, `tools.yaml`, chạy v0→v3, `version_log.csv`                 |
| 2   | Trần Chí Vũ      | 2A202601044 | **R2 — Tool Engineer**                               | Tool mới (bắt buộc ≥1, bonus >3):`tool.py` + `TOOL.md` + đăng ký + quicktest |
| 3   | Trịnh Hải Đăng  | 2A202601602 | **R3 — Eval Engineer / Failure Analyst**             | 10 case`eval_group.json`, đọc failure trace, `analysis/*.csv`                     |
| 4   | Đỗ Văn Linh      | 2A202601190 | **R4 — UI & Deploy Engineer**                        | `app.py` (Streamlit), tool trace UI, deploy public URL, live chat                     |
| 5   | Đỗ Thu Liễu      | 2A202601898 | **R5 — Evidence & Report Owner**                     | `REPORT.md` phần A + B, transcripts, rehearsal demo, gate nộp bài                  |

**Tên nhóm:** ______________________  **Provider/model:** `openrouter` / `openai/gpt-4o-mini` (xác nhận lại sau preflight)

> Nhóm có thể hoán đổi role. Nếu đổi, sửa cột Role ở bảng trên rồi báo cả nhóm — các bảng dưới tham chiếu theo mã R1–R5.

---

## 2. Quy tắc sở hữu file (tránh conflict khi cùng push)

Mỗi file chỉ có **một** người được sửa. Cần đổi file của người khác thì nhắn cho chủ file, không tự sửa.

| File / thư mục                        | Chủ sở hữu   | Ghi chú                                                                             |
| --------------------------------------- | --------------- | ------------------------------------------------------------------------------------ |
| `artifacts/system_prompt.md`          | R1              | Chỉ R1 sửa. Đây là biến thí nghiệm chính của v1/v2/v3.                     |
| `artifacts/tools.yaml`                | R1              | R2 gửi declaration của tool mới cho R1 chèn vào.                                |
| `artifacts/version_log.csv`           | R1              | 1 dòng / 1 version.                                                                 |
| `tools/**` (trừ `tools.yaml`)      | R2              | Gồm`tools/__init__.py`.                                                           |
| `data/eval_group.json`                | R3              | Không ai sửa`data/eval_base.json`.                                               |
| `analysis/*.csv`                      | R3              | Sinh từ`scripts/parse_runs.py`.                                                   |
| `app.py`                              | R4              | Không viết agent loop mới — phải gọi`run_model_tool_loop` trong `chat.py`. |
| `requirements.txt`                    | R4              | R2/R4 cùng cần thêm dep → gom lại cho R4 commit một lần.                      |
| `artifacts/REPORT.md`                 | R5              | Người khác gửi nội dung cho R5, không tự sửa.                                |
| `runs/*.json`, `transcripts/*.json` | sinh tự động | Không sửa tay.                                                                     |

---

## 3. Phân công theo checkpoint K4 (14:00–18:00)

| Thời gian   | Checkpoint              | R1 — Bình                                      | R2 — Vũ                                            | R3 — Đăng                              | R4 — Linh                                | R5 — Liễu                                           |
| ------------ | ----------------------- | ------------------------------------------------ | ---------------------------------------------------- | ----------------------------------------- | ----------------------------------------- | ----------------------------------------------------- |
| 14:00–14:15 | Kickoff                 | Chốt role, mở`starter_v0/`                   | Đọc`tools/README.md`                             | Đọc`eval_base.json`                   | Đọc mục UI trong README                | Mở`REPORT.md`, lập checklist                      |
| 14:15–14:40 | Setup                   | Chạy preflight provider                         | Điền`.env` tool keys (Tavily/Firecrawl/RapidAPI) | Xác nhận 20 case base load được      | Cài`streamlit`, dựng khung `app.py` | Điền mục Team ở`REPORT.md`                      |
| 14:40–15:15 | **Baseline v0**   | Chạy eval v0, ghi 4 metric                      | Chốt ý tưởng tool mới                           | Đọc 1 failed trace, liệt kê case fail | UI local chạy được 1 request          | Ghi metric v0 vào bảng B1                           |
| 15:15–15:50 | **v1 + Tool**     | Sửa 1 hypothesis → chạy v1 → ghi version log | Hoàn thiện tool mới +`TOOL.md` + quicktest      | Nháp 5 case single-turn                  | UI hiển thị được tool trace          | Bắt đầu phần A (A1, A2)                           |
| 15:50–16:05 | Nghỉ                   | —                                               | —                                                   | —                                        | —                                        | —                                                    |
| 16:05–16:30 | **Eval + v2**     | Sửa hypothesis 2 → chạy v2                    | Tool mới#2 (bonus)                                  | Xong đủ 10 case, chạy suite group      | Deploy tunnel, lấy public URL            | **Chốt phần A + rehearsal**                   |
| 16:30–17:15 | **Showdown**      | Trả lời challenge về routing                  | Demo tool mới                                       | Demo case eval bắt lỗi                  | Điều khiển UI khi demo                 | Dẫn phần giới thiệu, ghi feedback                 |
| 17:15–17:35 | **v3 + Report B** | Áp feedback → chạy v3                         | Tool bonus#3+ nếu kịp                              | Failure analysis cuối (B2, B3)           | Chạy 3 live turn, lưu transcript        | Tổng hợp B1–B6                                     |
| 17:35–17:40 | Final gate              | Xác nhận version_log đủ v0–v3               | Xác nhận tool đã đăng ký đủ 4 chỗ          | Xác nhận đúng 10 case                 | Xác nhận link demo còn sống           | **Kiểm tra không có `.env`/key rồi nộp** |
| 17:40–18:00 | Kahoot                  | —                                               | —                                                   | —                                        | —                                        | —                                                    |

---

## 4. Ai điền mục nào trong `REPORT.md`

| Mục trong REPORT.md                          | Người viết | Người review           | Deadline        |
| --------------------------------------------- | ------------- | ------------------------ | --------------- |
| Team / Members / Provider-model               | R5            | R1                       | 14:40           |
| **A1** — Agent làm được gì        | R5            | R1                       | 16:20           |
| **A1** — Link dùng thử (public URL)  | R4            | R5                       | 16:25           |
| **A2** — Bảng tool                    | R2            | R1                       | 16:20           |
| **A3** — Câu hỏi mẫu để thử      | R3            | R4 (test thật trên UI) | 16:25           |
| **A4** — Kịch bản demo đã rehearse | R5            | cả nhóm                | **16:30** |
| **B1** — Version evidence (v0–v3)     | R1            | R5                       | 17:30           |
| **B2** — Failure analysis              | R3            | R1                       | 17:30           |
| **B3** — Team eval cases (10 case)     | R3            | R5                       | 17:30           |
| **B4** — Live chat evidence            | R4            | R5                       | 17:30           |
| **B5** — Tool capability evidence      | R2            | R1                       | 17:30           |
| **B6** — Reflection                    | R5 tổng hợp | cả nhóm                | 17:35           |

---

## 5. Bảng theo dõi tiến độ (tự điền)

Trạng thái: `⬜ chưa làm` / `🟡 đang làm` / `✅ xong`

| #  | Hạng mục bắt buộc                   | Người phụ trách | Bằng chứng cần có                                                    | Trạng thái | Ghi chú |
| -- | --------------------------------------- | ------------------- | ------------------------------------------------------------------------ | ------------ | -------- |
| 1  | Setup + preflight provider PASS         | R1                  |                                                                          | Done         |          |
| 2  | Baseline v0 chạy xong                  | R1                  | `runs/*v0*.json`                                                       |              |          |
| 3  | v1 (1 hypothesis, 1 thay đổi)         | R1                  | run JSON + 1 dòng version_log                                           |              |          |
| 4  | v2                                      | R1                  | run JSON + 1 dòng version_log                                           |              |          |
| 5  | v3                                      | R1                  | run JSON + 1 dòng version_log                                           |              |          |
| 6  | `version_log.csv` đủ v0–v3         | R1                  | 4 dòng dữ liệu                                                        |              |          |
| 7  | Tool mới#1 (bắt buộc)                | R2                  | `tool.py` + `TOOL.md` + `__init__.py` + `tools.yaml` + quicktest |              |          |
| 8  | Tool mới#2 (bonus)                     | R2                  | như trên                                                               |              |          |
| 9  | Tool mới#3 (bonus)                     | R2                  | như trên                                                               |              |          |
| 10 | Tool mới#4 (bonus)                     | R2                  | như trên                                                               |              |          |
| 11 | 5 eval case single-turn                 | R3                  | `data/eval_group.json`                                                 |              |          |
| 12 | 5 eval case multi-turn                  | R3                  | `data/eval_group.json`                                                 |              |          |
| 13 | Chạy suite group                       | R3                  | `runs/*group*.json`                                                    |              |          |
| 14 | `analysis/*.csv` (optional)           | R3                  |                                                                          |              |          |
| 15 | UI chạy local (`localhost:8501`)     | R4                  | screenshot                                                               |              |          |
| 16 | UI hiện tool trace + version           | R4                  | screenshot                                                               |              |          |
| 17 | Deploy public URL                       | R4                  | link`trycloudflare.com`                                                |              |          |
| 18 | Live chat ≥3 turn                      | R4                  | `transcripts/*.transcript.json`                                        |              |          |
| 19 | REPORT phần A                          | R5                  |                                                                          |              |          |
| 20 | REPORT phần B                          | R5                  |                                                                          |              |          |
| 21 | Rehearsal 3–5 scenario                 | R5                  |                                                                          |              |          |
| 22 | Gate nộp bài (không có`.env`/key) | R5                  |                                                                          |              |          |

---

## 6. Điều kiện metric hợp lệ (R1 + R3 kiểm mỗi lần chạy)

Mỗi run chỉ được đưa vào report nếu:

- `summary.provider_error_cases == 0`
- `summary.measured_cases == total_cases`
- Mọi `tool_results` có error đều đã review thủ công (routing PASS **không** chứng minh tool chạy đúng)

## 7. Checklist đồng bộ khi đổi tên tool (R1 chủ trì, R2 + R3 xác nhận)

Đổi tên tool phải sync đủ 8 chỗ, thiếu 1 chỗ là eval báo `not declared in tools.yaml`:

1. `artifacts/system_prompt.md` — R1
2. `artifacts/tools.yaml` — R1
3. `tools/<tool_name>/TOOL.md` — R2
4. `tools/__init__.py` — R2
5. `data/eval_base.json` (**chỉ đổi field tên tool**, không sửa query/expected) — R3
6. `data/eval_research_extension.json` — R3
7. `data/eval_group.json` — R3
8. `artifacts/REPORT.md` + poster/demo text — R5

## 8. Quy tắc không được vi phạm

- Không sửa query / expected args / expected behavior trong `data/eval_base.json`.
- Mỗi version chỉ đổi **một** thứ; không chạy 3 lần giống hệt nhau để lấy tên v1/v2/v3.
- Để `TELEGRAM_BOT_TOKEN` và `TELEGRAM_CHAT_ID` **unset** trong mọi lần `run_eval`.
- Không commit `.env`, API key, `.venv/`, cache/build output.
- Không để lộ secrets trong screenshot, log, poster hoặc UI public.
