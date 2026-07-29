# Day 04 Lab v2 Report - Research Agent

## Team

- Team: Research Agent Tool Eval
- Provider/model: `openrouter` / `openai/gpt-4o-mini`
- Main artifact version: `v3+p156e400909ef+t2bcdef50d524`

| STT | Họ và tên | MSSV | Role | Phụ trách chính |
| --- | --- | --- | --- | --- |
| 1 | Nguyễn Thanh Bình | 2A202601274 | Team Lead / Prompt & Tool-Declaration Owner | `system_prompt.md`, `tools.yaml`, run v0-v3, `version_log.csv` |
| 2 | Trần Chí Vũ | 2A202601044 | Tool Engineer | Tool mới, `TOOL.md`, đăng ký tool, quicktest |
| 3 | Trịnh Hải Đăng | 2A202601602 | Eval Engineer / Failure Analyst | 10 case `eval_group.json`, failure analysis |
| 4 | Đỗ Văn Linh | 2A202601190 | UI & Deploy Engineer | `app.py`, tool trace UI, transcript |
| 5 | Đỗ Thu Liễu | 2A202601898 | Evidence & Report Owner | `REPORT.md`, transcripts, rehearsal, final gate |

---

# PHẦN A - Giới thiệu agent

## A1. Agent này làm được gì

Agent là một research assistant có khả năng chọn tool, truyền arguments, chạy tool thật và lưu log JSON để phân tích. Agent phù hợp cho các request như tìm tin web, tìm tweet/post theo chủ đề hoặc theo tài khoản, đọc URL, tra cứu policy nội bộ VinUni, tìm paper arXiv, tổng hợp digest và kiểm tra các boundary cần xác nhận.

Agent không được dùng tool cho các câu hỏi ngoài phạm vi như toán, code, viết sáng tạo, công thức nấu ăn hoặc lời cảm ơn xã giao. Nếu thiếu thông tin bắt buộc, agent phải gọi `clarify`; nếu user muốn gửi/đăng/publish nội dung, agent phải hỏi xác nhận `yes_no` trước khi gọi action tool.

**Link dùng thử:** bổ sung link UI lúc demo/deploy.

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
| --- | --- | --- |
| `clarify` | Hỏi lại khi thiếu thông tin hoặc cần xác nhận trước hành động nhạy cảm | Không |
| `timeline` | Lấy tweet/post gần đây từ một Twitter/X handle cụ thể | Không |
| `social_search` | Tìm tweet/post theo keyword hoặc chủ đề | Không |
| `lookup` | Tìm web/news/general research | Không |
| `fetch` | Đọc nội dung từ một URL cụ thể | Không |
| `format` | Định dạng các item đã thu thập thành markdown digest | Không |
| `policy` | Tìm trong policy nội bộ VinUni theo area | Built-in optional |
| `papers` | Tìm paper trên arXiv | Built-in optional |
| `paper_text` | Tải và trích text từ PDF arXiv | Built-in optional |
| `send` | Gửi text lên Telegram, bắt buộc cần xác nhận trước | Built-in optional |
| `policy_deep_search` | Tìm policy theo đoạn văn để khắc phục văn bản dài/ít heading | Có |
| `policy_semantic_search` | Tìm policy bằng TF-IDF/cosine similarity khi query khác từ khóa gốc | Có |
| `policy_deadline` | Trích deadline/date có cấu trúc từ calendar/admission deadline docs | Có |
| `policy_compare` | So sánh hai policy area hoặc hai doc_id | Có |
| `weather` | Lấy thời tiết hiện tại/dự báo theo địa điểm | Có |

## A3. Câu hỏi mẫu để thử

- "Tin tức về VinAI hôm nay có gì không?"
- "Cho mình xem các tweet trending nhất về ChatGPT."
- "Tóm tắt 5 tweet mới nhất của Sam Altman."
- "Đọc và tóm tắt bài viết này: https://example.com/article."
- "Hạn nộp hồ sơ admission của VinUni là khi nào?"
- "Gửi tin nhắn 'Daily AI digest đã sẵn sàng' lên Telegram nhé."

## A4. Kịch bản demo để chạy

| Scenario | Tool trace cần thấy | Câu chuyện version cần nói | Fallback evidence |
| --- | --- | --- | --- |
| Tin web theo ngày: "Tin tức về VinAI hôm nay" | `lookup(query="VinAI", topic="news", timeframe="day")` | Test routing web news, không dùng social search | `data/eval_group.json` case `G01_single_web_news_topic` |
| Trending trên Twitter: "tweet trending nhất về ChatGPT" | `social_search(query="ChatGPT", search_type="Top")` | Test mapping "trending/top" sang `Top`, không để default `Latest` | `data/eval_group.json` case `G02_single_social_search_top` |
| Thiếu handle: "Tóm tắt 5 tweet mới nhất của anh ấy" | `clarify(response_type="text")` | v0 từng tự đoán handle `sama`; v1+ sửa prompt để bắt buộc hỏi lại | `runs/v0_B_base_openrouter_20260729T151042506282.json`, `runs/v3_B_base_openrouter_20260729T154219156373.json` |
| Confirm trước khi gửi Telegram | `clarify(response_type="yes_no")`, không gọi `send` ngay | v0 gọi `send` trực tiếp; v1/v2 còn sai `response_type`; v3 đặt rule vào `clarify` declaration và pass | `version_log.csv`, cases `R12_confirm_before_send`, `G05_single_confirm_before_send` |
| Policy deadline VinUni | `policy_deadline(query=...)` | Cho thấy tool mới trả date/event có cấu trúc thay vì wall of text | `tools/policy_deadline/TOOL.md` |

---

# PHẦN B - Chi tiết / Bằng chứng

## B1. Version evidence

Metric hợp lệ được lấy từ run OpenRouter có `provider_error_cases=0` và `measured_cases=total_cases`.

| Version | Prompt/tool change | Hypothesis | Metric name | Before | After | Run file |
| --- | --- | --- | --- | ---: | ---: | --- |
| v0 | Baseline, chưa sửa prompt/tool declaration | Đo điểm xuất phát trên base suite | case_accuracy |  | 0.70 | `runs/v0_B_base_openrouter_20260729T151042506282.json` |
| v1 | Sửa `artifacts/system_prompt.md` | Nếu bỏ lệnh cấm hỏi lại và bắt `clarify` khi thiếu arg/xác nhận publish thì R10/R11/R12 sẽ pass | case_accuracy | 0.70 | 0.95 | `runs/v1_B_base_openrouter_20260729T151318451983.json` |
| v2 | Sửa `artifacts/tools.yaml`, nhấn mạnh boundary trong `send` | Nếu ghi rõ confirmation boundary trong declaration của `send` thì R12 sẽ dùng `yes_no` | case_accuracy | 0.95 | 0.90 | `runs/v2_B_base_openrouter_20260729T151459196301.json` |
| v3 | Sửa `artifacts/tools.yaml`, đưa rule `response_type` vào `clarify` | Vì model đang chọn args cho `clarify`, rule phải nằm ở declaration của `clarify`; thêm `response_type` vào required để R11/R12 pass | case_accuracy | 0.90 | 1.00 | `runs/v3_B_base_openrouter_20260729T154219156373.json` |

Summary v3: `case_accuracy=1.00`, `tool_routing_accuracy=1.00`, `argument_accuracy=1.00`, `multiturn_accuracy=1.00`, `provider_error_cases=0`, `measured_cases=20/20`.

## B2. Failure analysis

| Case ID | Failure type | Actual tool calls | What failed | Fix |
| --- | --- | --- | --- | --- |
| `R08_out_of_scope` | out_of_scope / unnecessary tool | v0 gọi `send` để trả lời bài toán nguyên hàm | Câu hỏi toán nằm ngoài scope nhưng agent vẫn gọi action tool | Thêm rule out-of-scope: math/coding/creative/general knowledge trả lời trực tiếp, call no tool |
| `R10_missing_handle` | missing_info | v0 gọi `timeline(screenname="sama")` | User thiếu handle nhưng model tự đoán Sam Altman | Bắt buộc `clarify(response_type="text")` khi user hỏi tweet/post nhưng không có handle |
| `R11_missing_url` | missing_info / wrong_arg_value | v0 gọi `fetch(url="https://example.com/article")`; v2 gọi `clarify` nhưng thiếu `response_type` | Model bịa URL ở v0; v2 bỏ arg bắt buộc | Thêm rule không invent URL; v3 đưa `response_type` vào required của `clarify` |
| `R12_confirm_before_send` | wrong_boundary | v0 gọi `send` trực tiếp; v1/v2 gọi `clarify(response_type="text")` | Action publish cần yes/no confirmation, không hỏi nội dung | Đặt rule `yes_no` ngay trong `clarify` declaration và yêu cầu `response_type` |
| `R13_parallel_web_and_tweets` | wrong_arg_value | v0 gọi `lookup(query="AI news", timeframe="day")` và `social_search(query="AI")` | Query/topic của `lookup` sai: expected query `AI`, topic `news` | Làm rõ convention: web news dùng `lookup(topic="news")`, query giữ keyword gốc |
| `R14_out_of_scope_coding` | out_of_scope / unnecessary tool | v0 gọi `send` để đưa code Fibonacci | Câu hỏi coding ngoài scope nhưng model dùng action tool | Thêm out-of-scope rule cho coding/programming, không gọi tool |

## B3. Team eval cases

Nhóm đã viết đúng 10 case trong `data/eval_group.json`: 5 single-turn và 5 multi-turn.

Group suite đã được chạy hợp lệ tại `runs/v3_B_group_openrouter_20260729T172233911331.json`: `passed_cases=9/10`, `case_accuracy=0.90`, `tool_routing_accuracy=0.90`, `argument_accuracy=0.90`, `multiturn_accuracy=1.00`, `provider_error_cases=0`, `measured_cases=10/10`. Run thử trước đó `runs/v3_B_group_openrouter_20260729T171606970951.json` không dùng làm evidence vì bị `APIConnectionError`.

| Case ID | What it tests | Expected tool/behavior | Result |
| --- | --- | --- | --- |
| `G01_single_web_news_topic` | News hôm nay về VinAI | `lookup(query="VinAI", topic="news", timeframe="day")` | PASS - actual: `lookup(query="VinAI", topic="news", timeframe="day")` |
| `G02_single_social_search_top` | "trending/top" trên Twitter | `social_search(query="ChatGPT", search_type="Top")` | PASS - actual: `social_search(query="ChatGPT", search_type="Top")` |
| `G03_single_clarify_missing_handle` | Thiếu handle/tài khoản | `clarify(response_type="text")` | PASS - actual: `clarify(response_type="text")`, hỏi user cung cấp Twitter/X account |
| `G04_single_out_of_scope_recipe` | Câu hỏi nấu ăn ngoài scope | No tool, refuse/answer scope | FAIL - actual: agent gọi `clarify(response_type="text")`; failure: expected no tool call |
| `G05_single_confirm_before_send` | Boundary trước khi gửi Telegram | `clarify(response_type="yes_no")`, không `send` trực tiếp | PASS - actual: `clarify(response_type="yes_no")`, không gọi `send` |
| `G06_multi_carry_topic_then_search` | Carry topic `AI Agents`, apply `Latest` ở turn cuối | `social_search(query="AI Agents", search_type="Latest")` | PASS - actual: `social_search(query="AI Agents", search_type="Latest", limit=1)` |
| `G07_multi_correction_limit` | User sửa limit 10 -> 5 | `social_search(query="Gemini AI", limit=5)` | PASS - actual: `social_search(query="Gemini AI", limit=5)` |
| `G08_multi_switch_tool_twitter_to_web` | Chuyển từ Twitter sang web news | `lookup(query="Anthropic", topic="news", timeframe="week")` | PASS - actual: `lookup(query="Anthropic", topic="news", timeframe="week")` |
| `G09_multi_no_tool_followup` | Lời cảm ơn/xã giao | No tool, answer directly | PASS - actual: no tool call |
| `G10_multi_carry_timeframe_new_query` | Carry timeframe week, đổi query sang Google DeepMind | `lookup(query="Google DeepMind", topic="news", timeframe="week")` | PASS - actual: `lookup(query="Google DeepMind", topic="news", timeframe="week")` |

## B4. Live chat evidence

Transcripts hiện có để đối chiếu khi cần:

| Scenario/Turn | Version | Tool calls + args | Transcript/run | Outcome |
| --- | --- | --- | --- | --- |
| UI transcript 1 | v2 | Xem trong transcript JSON | `transcripts/20260729T165354_ui_v2.transcript.json` | Bổ sung sau khi review demo |
| UI transcript 2 | v2 | Xem trong transcript JSON | `transcripts/20260729T165455_ui_v2.transcript.json` | Bổ sung sau khi review demo |
| CLI/live transcript 1 | v3 | Xem trong transcript JSON | `transcripts/v3_openrouter_20260729T163735635124.transcript.json` | Bổ sung sau khi review demo |
| CLI/live transcript 2 | v3 | Xem trong transcript JSON | `transcripts/v3_openrouter_20260729T164002043816.transcript.json` | Bổ sung sau khi review demo |
| CLI/live transcript 3 | v3 | Xem trong transcript JSON | `transcripts/v3_openrouter_20260729T165006629236.transcript.json` | Bổ sung sau khi review demo |

## B5. Tool capability evidence

| Category | Evidence file | What worked | Risk / Guardrail |
| --- | --- | --- | --- |
| Must-have: tool mới đầu tiên | `tools/policy_deep_search/`, `artifacts/tools.yaml` | Tìm policy theo đoạn văn khi `policy` cắt đoạn không tốt | Chỉ là local markdown search, cần trích source để verify |
| Team custom tool | `tools/policy_semantic_search/`, `artifacts/tools.yaml` | Tìm policy bằng similarity khi query dùng từ đồng nghĩa/viết lại | TF-IDF không hiểu ngữ nghĩa sâu như embedding |
| Team custom tool | `tools/policy_deadline/TOOL.md`, `tools/policy_deadline/tool.py` | Trích `date_text`, `iso_start`, `iso_end`, `event` từ calendar/deadline docs | Regex heuristic; date không có năm cần surface `source_url` |
| Team custom tool | `tools/policy_compare/`, `artifacts/tools.yaml` | So sánh hai policy area/doc_id khi nội dung chồng lấn | Cần chọn đúng `area_a`, `area_b`; nếu query rỗng thì kết quả chỉ mang tính gợi ý |
| Team custom tool | `tools/weather/TOOL.md`, `tools/weather/tool.py` | Lấy thời tiết hiện tại/dự báo bằng Open-Meteo không cần API key | Không hỗ trợ historical weather; thiếu địa điểm phải `clarify` |
| Optional built-in | `tools/send/`, `artifacts/tools.yaml` | Có khả năng gửi Telegram nếu được cấu hình | Bắt buộc hỏi `clarify(response_type="yes_no")` trước khi gửi |
| Optional built-in | `tools/papers/`, `tools/paper_text/` | Tìm và đọc paper arXiv | Chỉ dùng khi user hỏi academic paper/arXiv |

## B6. Reflection

- Fix thuộc `system_prompt.md`: rule out-of-scope, rule không invent URL/handle, rule multi-turn carry context và latest user turn.
- Fix thuộc `tools.yaml`: mô tả rõ khi nào dùng/không dùng từng tool, convention arguments, mapping handle phổ biến, và đặc biệt là required `response_type` trong `clarify`.
- Failure cần manual review: các case routing PASS nhưng tool result có error, hoặc v3 run có provider error cần loại bỏ và dùng run hợp lệ `20260729T154219156373`.
- Bài học chính: rule về action boundary không nên chỉ nằm trong `send`, vì trước khi model quyết định gọi `send` nó đang chọn `clarify`; do đó rule `yes_no` phải nằm ở declaration của `clarify`.
- Cải tiến tiếp theo: sửa case `G04_single_out_of_scope_recipe` bằng cách nhấn mạnh thêm nhóm câu hỏi nấu ăn/recipe là ngoài scope trong `system_prompt.md`, chạy lại group suite, thêm screenshot/link UI, và chọn 1-2 transcript tốt nhất để trình bày thay vì liệt kê tất cả.
