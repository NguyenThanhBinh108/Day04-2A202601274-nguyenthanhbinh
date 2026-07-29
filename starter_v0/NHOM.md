# 🤖 DAY04 — Research Agent Tool Eval

## Nhóm: 2A202601602 — Trịnh Hải Đăng + 4 thành viên

> **Mục tiêu cốt lõi**: Build một research agent chạy thật, đo được, cải thiện được theo vòng lặp evidence-driven — không phải chatbot trả lời hay, mà là agent biết gọi đúng tool, đúng args, đúng timing.

---

## 📋 MỤC LỤC

1. [Hiểu bài lab — What &amp; Why](#1-hiểu-bài-lab)
2. [Kiến thức cần có](#2-kiến-thức-cần-có)
3. [Kiến trúc hệ thống](#3-kiến-trúc-hệ-thống)
4. [Phân công nhóm 5 người](#4-phân-công-nhóm-5-người)
5. [Quy trình Git — tránh conflict](#5-quy-trình-git)
6. [Các bước thực hiện chi tiết](#6-các-bước-thực-hiện)
7. [Cách viết Tool mới chuẩn production](#7-viết-tool-mới)
8. [Cách viết Eval Cases](#8-viết-eval-cases)
9. [Vòng lặp tối ưu v0→v3](#9-vòng-lặp-tối-ưu)
10. [Xây dựng UI Streamlit](#10-ui-streamlit)
11. [Checklist nộp bài](#11-checklist-nộp-bài)
12. [Tái tạo từ file MD này — khi có conflict](#12-tái-tạo-khi-conflict)

---

## 1. Hiểu bài lab

### Bài lab yêu cầu gì?

| Hạng mục                                      | Bắt buộc | Mô tả                                             |
| ----------------------------------------------- | :--------: | --------------------------------------------------- |
| Chạy được bằng provider thật              |     ✅     | OpenRouter / OpenAI / Anthropic / Gemini            |
| ≥ 5 tool trong`tools.yaml`                   |     ✅     | Starter đã có 6 core tools + 4 optional          |
| Chạy base eval`v0`                           |     ✅     | `run_eval.py --version v0 --suite base`           |
| 3 vòng cải tiến thật:`v1`, `v2`, `v3` |     ✅     | Mỗi version sửa 1 hypothesis, chạy lại, ghi log |
| Ghi`version_log.csv`                          |     ✅     | Header sẵn trong file, fill sau mỗi run           |
| Viết ≥ 1 tool mới (+ TOOL.md)                |     ✅     | Đăng ký trong`__init__.py` và `tools.yaml`  |
| 10 eval cases trong`eval_group.json`          |     ✅     | 5 single-turn + 5 multi-turn                        |
| Nộp run JSON + transcript JSON                 |     ✅     | Sinh tự động khi chạy eval/chat                 |
| UI chạy được (Streamlit khuyến nghị)      |     ✅     | `app.py` — tái dùng `run_model_tool_loop`    |
| Deploy link (Cloudflare Tunnel)                 |     ✅     | Để team khác test từ máy khác                 |
| Hoàn thành`REPORT.md`                       |     ✅     | Phần A trước 16:30, Phần B sau showdown         |
| Viết thêm > 3 tool mới                       |  ⭐ Bonus  | Không tính tool optional có sẵn                 |

### Sản phẩm là gì?

```
User Input → [Research Agent] → Tool Selection → Tool Execution → Answer
                ↑                      ↓
         system_prompt.md        tools.yaml
         (prompt engineering)  (tool declarations)
```

Agent **không phải** chatbot. Agent là hệ thống:

- Nhận câu hỏi người dùng
- Quyết định gọi tool nào (routing)
- Truyền đúng arguments
- Biết khi nào cần hỏi lại (`clarify`)
- Biết khi nào cần xác nhận trước khi làm (`send` → hỏi yes/no trước)

---

## 2. Kiến thức cần có

### A. Tool Calling / Function Calling

**Khái niệm cốt lõi**: Model AI (GPT-4, Claude, Gemini) có khả năng không chỉ trả lời text mà còn **quyết định gọi hàm** (function) theo structured format.

```python
# Model nhận list tools như thế này:
tools = [
    {
        "type": "function",
        "function": {
            "name": "lookup",
            "description": "Tra cứu thông tin trên internet",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "topic": {"type": "string", "enum": ["general", "news"]}
                },
                "required": ["query"]
            }
        }
    }
]

# Model trả về:
# response.tool_calls = [ToolCall(name="lookup", args={"query": "AI news", "topic": "news"})]
```

**Tại sao quan trọng**: Tên tool và description trong `tools.yaml` chính là **ngôn ngữ giao tiếp** giữa bạn và model. Description tệ → routing sai.

### B. Prompt Engineering cho Agent

Khác chatbot thông thường, agent cần prompt rõ **ranh giới hành vi**:

| Tình huống                     | Hành vi đúng                 | Hành vi sai (baseline)           |
| -------------------------------- | ------------------------------- | --------------------------------- |
| Thiếu handle Twitter            | Gọi`clarify` hỏi lại       | Tự đoán`sama`                |
| Có URL cụ thể                 | Gọi`fetch` với URL đó     | Gọi`lookup` search lại        |
| Request "gửi lên Telegram"     | Gọi`clarify(yes_no)` trước | Tự gọi`send` ngay             |
| Câu hỏi tích phân toán học | Không gọi tool, từ chối     | Gọi`lookup` search công thức |
| Vừa cần web + tweets           | Gọi 2 tool parallel            | Chỉ gọi 1 tool                  |

> **Starter intentionally broken**: `system_prompt.md` và `tools.yaml` trong starter được làm cho SAI CỐ Ý để bạn phải sửa. Đây là điểm mấu chốt của lab.

### C. Eval-Driven Optimization (Evidence Loop)

```
v0 (baseline) → Chạy eval → Đọc JSON → Tìm failures → Đặt hypothesis
     ↓
Sửa 1 thứ (prompt hoặc tool declaration) → v1
     ↓
So sánh metric trước/sau → Ghi version_log.csv
     ↓
Lặp lại → v2 → v3
```

Các metric quan trọng trong run JSON:

- `summary.case_accuracy` — % case PASS
- `summary.tool_routing_accuracy` — % gọi đúng tool
- `summary.argument_accuracy` — % args đúng
- `summary.multiturn_accuracy` — % multi-turn PASS

### D. Cấu trúc dữ liệu quan trọng

```python
# AgentRun (agent.py)
@dataclass
class AgentRun:
    text: str | None           # text response từ model
    tool_calls: list[ToolCall] # list tool được gọi
    tool_results: list[dict]   # kết quả thực thi tool

# run_model_tool_loop return (chat.py)
{
    "status": "answered" | "waiting_for_user" | "max_tool_rounds",
    "assistant_text": str,
    "rounds": [...],        # mỗi round: tool calls + results
    "tool_events": [...]    # flat list tất cả tool events
}
```

### E. Các API/Service cần hiểu

| Service            | Tool                            | API Key                | Dùng để      |
| ------------------ | ------------------------------- | ---------------------- | --------------- |
| OpenRouter         | Model provider                  | `OPENROUTER_API_KEY` | Gọi LLM        |
| Tavily             | `lookup`                      | `TAVILY_API_KEY`     | Web search      |
| Firecrawl          | `fetch`                       | `FIRECRAWL_API_KEY`  | Scrape URL      |
| RapidAPI Twitter45 | `timeline`, `social_search` | `RAPIDAPI_KEY`       | Twitter data    |
| arXiv              | `papers`, `paper_text`      | Không cần            | Research papers |
| Telegram           | `send`                        | `TELEGRAM_BOT_TOKEN` | Gửi message    |

---

## 3. Kiến trúc hệ thống

```
starter_v0/
├── artifacts/                    # ← NHÓM SỬA FILES NÀY
│   ├── system_prompt.md          # Prompt cho agent (prompt engineering)
│   ├── tools.yaml                # Tool declarations (routing rules)
│   ├── version_log.csv           # Ghi metric mỗi version
│   └── REPORT.md                 # Báo cáo demo + nộp bài
│
├── tools/                        # ← NHÓM THÊM TOOL MỚI VÀO ĐÂY
│   ├── __init__.py               # Registry: TOOL_FUNCTIONS dict
│   ├── clarify/tool.py           # Tool: hỏi lại user
│   ├── lookup/tool.py            # Tool: web search (Tavily)
│   ├── fetch/tool.py             # Tool: đọc URL (Firecrawl)
│   ├── timeline/tool.py          # Tool: Twitter timeline
│   ├── social_search/tool.py     # Tool: Twitter search
│   ├── format/tool.py            # Tool: format digest
│   ├── send/tool.py              # Tool: gửi Telegram
│   ├── papers/tool.py            # [Optional] arXiv search
│   └── paper_text/tool.py        # [Optional] arXiv PDF
│
├── data/                         # ← NHÓM VIẾT eval_group.json
│   ├── eval_base.json            # KHÔNG SỬA — 20 cases cố định
│   ├── eval_group.json           # NHÓM TỰ VIẾT — 10 cases
│   └── eval_research_extension.json  # Optional
│
├── providers/                    # Đã xong, không cần sửa
│   ├── openrouter_provider.py
│   ├── openai_provider.py
│   ├── anthropic_provider.py
│   └── gemini_provider.py
│
├── agent.py                      # ResearchAgent class — không sửa
├── chat.py                       # CLI chat + run_model_tool_loop — không sửa
├── run_eval.py                   # Eval runner — không sửa
├── versioning.py                 # Hash tracking — không sửa
├── env_loader.py                 # Load .env — không sửa
│
├── app.py                        # ← NHÓM TẠO FILE NÀY (UI)
├── requirements.txt              # Thêm streamlit>=1.30.0
└── .env                          # Keys — KHÔNG COMMIT
```

---

## 4. Phân công nhóm 5 người

> **Nguyên tắc**: Phân theo file/folder để tránh conflict tối đa. Mỗi người owns một zone rõ ràng.

### 🧑‍💼 Người 1 — Prompt Engineer

**Own files**: `artifacts/system_prompt.md`, `artifacts/tools.yaml`, `artifacts/version_log.csv`

**Nhiệm vụ**:

- Setup env, chạy preflight, verify API keys của cả nhóm
- Chạy `v0` baseline, đọc failures, đặt hypothesis cho v1/v2/v3
- Sửa `system_prompt.md` và `tools.yaml` theo từng hypothesis
- Ghi `version_log.csv` sau mỗi run
- Coordinate merge và review PR của nhóm

**Commands thường dùng**:

```powershell
# Chạy eval
python run_eval.py --provider openrouter --version v0 --suite base --eval-cases data/eval_base.json

# Chat live
python chat.py --provider openrouter --version v3
```

---

### 🛠️ Người 2 — Tool Developer #1

**Own files**: `tools/YOUR_TOOL_1/` (toàn bộ folder)

**Nhiệm vụ**:

- Implement tool mới bắt buộc (VD: `summarize`, `translate`, `weather`)
- Viết `TOOL.md` đầy đủ
- Đăng ký vào `tools/__init__.py` và khai báo `tools.yaml`
- Smoke-test trực tiếp trước khi merge
- Viết ít nhất 2 eval cases liên quan

---

### 🛠️ Người 3 — Tool Developer #2 (Bonus)

**Own files**: `tools/YOUR_TOOL_2/`, `tools/YOUR_TOOL_3/`

**Nhiệm vụ**:

- Implement thêm tool để lấy điểm bonus (cần > 3 tool mới)
- VD: `summarize_pdf`, `translate`, `stock_price`, `image_search`
- Mỗi tool cần `TOOL.md`, implementation, smoke-test
- Viết 2–3 eval cases cho tools này

---

### 📊 Người 4 — Eval Engineer

**Own files**: `data/eval_group.json`

**Nhiệm vụ**:

- Thiết kế 10 eval cases cho `eval_group.json`
- 5 single-turn + 5 multi-turn, mỗi loại failure type ít nhất 1
- Phân tích failures từ base eval, viết Phần B2 trong `REPORT.md`
- Chạy `run_eval.py --suite group` sau khi tool mới sẵn sàng

**Commands thường dùng**:

```powershell
# Chạy group eval
python run_eval.py --provider openrouter --version v3 --suite group --eval-cases data/eval_group.json

# Parse runs thành CSV
python scripts/parse_runs.py runs/ --output analysis/base_runs.csv
```

---

### 🎨 Người 5 — UI Engineer

**Own files**: `app.py`, `requirements.txt` (thêm streamlit)

**Nhiệm vụ**:

- Tạo `app.py` Streamlit tái dùng `run_model_tool_loop` từ `chat.py`
- UI phải hiển thị: request/response, tool trace (tên + args + result), version info
- Setup Cloudflare Tunnel để generate public link
- Test link với máy khác trước showdown
- Điền link vào REPORT.md Phần A

---

## 5. Quy trình Git

### Branch strategy

```
main                    ← nhánh production, chỉ merge khi stable
  └── haidang2425       ← nhánh lead (đang active)
      ├── feat/tool-summarize     ← Người 2
      ├── feat/tool-translate     ← Người 3
      ├── feat/eval-group         ← Người 4
      └── feat/ui-streamlit       ← Người 5
```

### Quy tắc Git cho nhóm

```powershell
# 1. Mỗi người tạo branch từ haidang2425
git checkout -b feat/tool-YOUR_TOOL_NAME

# 2. Commit thường xuyên (không commit .env)
git add tools/your_tool/ tools/__init__.py artifacts/tools.yaml
git commit -m "feat(tool): add YOUR_TOOL_NAME with TOOL.md and smoke test"

# 3. Trước khi merge — pull latest
git pull origin haidang2425 --rebase

# 4. Push và tạo PR
git push origin feat/tool-YOUR_TOOL_NAME

# 5. Lead review + merge
```

### Files mỗi người owns (không ai khác sửa)

| File/Folder                    | Owner                          | Ghi chú                           |
| ------------------------------ | ------------------------------ | ---------------------------------- |
| `artifacts/system_prompt.md` | Người 1                      | Chỉ Lead được sửa             |
| `artifacts/tools.yaml`       | Người 1 + declarations mới  | Người 2/3 chỉ thêm block mới  |
| `artifacts/version_log.csv`  | Người 1                      | Chỉ Lead điền                   |
| `artifacts/REPORT.md`        | Người 1 + Người 4          | Split theo section A/B             |
| `tools/YOUR_TOOL_1/`         | Người 2                      | Toàn bộ folder                   |
| `tools/YOUR_TOOL_2/`         | Người 3                      | Toàn bộ folder                   |
| `tools/__init__.py`          | Người 2 + 3 merge cẩn thận | Chỉ thêm dòng import + dict key |
| `data/eval_group.json`       | Người 4                      | Không ai khác sửa               |
| `app.py`                     | Người 5                      | Chỉ người 5 sửa                |
| `requirements.txt`           | Người 5                      | Thêm streamlit                    |

### Khi xảy ra conflict

**`tools/__init__.py` conflict** (phổ biến nhất):

```python
# Chỉ cần thêm 2 loại dòng — không đụng gì khác
from .your_tool.tool import your_function   # Dòng import đầu file
"your_tool": your_function,                 # Dòng trong TOOL_FUNCTIONS dict
```

→ Conflict thường do 2 người thêm dòng cùng vị trí. Giải quyết: giữ cả hai dòng, không xóa.

**`artifacts/tools.yaml` conflict**:
→ Mỗi tool là một block riêng trong list `tools:`. Giữ cả hai block.

**Khẩn cấp — dùng file MD này để tái tạo**:

```powershell
# Pull file MD về (bản mới nhất)
git checkout origin/main -- NHOM.md
# Đọc mục 12 bên dưới và làm theo
```

---

## 6. Các bước thực hiện

### ⏱️ Timeline (4 tiếng: 14:00–18:00)

```
14:00–14:15  KICKOFF       Đọc README, phân công, tạo branches
14:15–14:40  SETUP         Điền API keys .env, chạy preflight
14:40–15:15  BASELINE v0   Chạy eval, đọc failures, dựng UI local
15:15–15:50  v1 + TOOL     Sửa hypothesis, viết tool mới, chạy v1
15:50–16:05  NGHỈ
16:05–16:30  v2 + EVAL     10 team eval cases, evidence v2, rehearse
16:30–17:15  SHOWDOWN      Demo, live test, challenge
17:15–17:35  v3 + REPORT   Apply feedback, v3, hoàn thiện report
17:35–17:40  FINAL GATE    Kiểm tra, chuẩn bị nộp
```

### Bước 0: Setup môi trường (ĐÃ XONG)

```powershell
cd starter_v0
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Mở `.env`, điền keys:

```env
OPENROUTER_API_KEY=sk-or-...
TAVILY_API_KEY=tvly-...
FIRECRAWL_API_KEY=fc-...
RAPIDAPI_KEY=...
RAPIDAPI_TWITTER_HOST=twitter-api45.p.rapidapi.com
# Để trống trong eval:
# TELEGRAM_BOT_TOKEN=...
# TELEGRAM_CHAT_ID=...
```

Chạy preflight:

```powershell
python scripts/preflight_provider.py --provider openrouter
```

### Bước 1: Chạy Baseline v0

```powershell
python run_eval.py --provider openrouter --version v0 --suite base --eval-cases data/eval_base.json
```

Mở file `runs/v0_base_*.json`. Ghi lại 4 metric:

```
case_accuracy:          ____ / 20
tool_routing_accuracy:  ____
argument_accuracy:      ____
multiturn_accuracy:     ____
```

### Bước 2: Phân tích failure và đặt hypothesis

Đọc từng case FAIL trong `results[*].result.failures`:

| Case ID | Expected            | Actual             | Root Cause                    | Fix         |
| ------- | ------------------- | ------------------ | ----------------------------- | ----------- |
| R10     | `clarify(text)`   | `timeline(sama)` | Prompt: "never ask questions" | Sửa prompt |
| R12     | `clarify(yes_no)` | `send(...)`      | Prompt: "just go ahead"       | Sửa prompt |
| R08     | no_tool + refuse    | `lookup(...)`    | Không có out-of-scope rule  | Thêm rule  |

### Bước 3: v1, v2, v3

```powershell
# Sửa 1 thứ → chạy → ghi log → lặp lại
python run_eval.py --provider openrouter --version v1 --suite base --eval-cases data/eval_base.json
python run_eval.py --provider openrouter --version v2 --suite base --eval-cases data/eval_base.json
python run_eval.py --provider openrouter --version v3 --suite base --eval-cases data/eval_base.json
```

### Bước 4: Chạy group eval

```powershell
python run_eval.py --provider openrouter --version v3 --suite group --eval-cases data/eval_group.json
```

### Bước 5: Chat live

```powershell
python chat.py --provider openrouter --version v3
```

Thử ít nhất 3 scenarios: research bình thường / thiếu info / action nhạy cảm.

---

## 7. Viết Tool mới

### Cấu trúc bắt buộc

```
tools/
└── your_tool_name/
    ├── TOOL.md          ← Tài liệu (BẮT BUỘC)
    └── tool.py          ← Implementation (BẮT BUỘC)
```

### Template TOOL.md

```markdown
# Tool: your_tool_name

## Mô tả
[1–2 câu: tool làm gì]

## Khi nào dùng
- [Use case 1]
- [Use case 2]

## Khi nào KHÔNG dùng
- [Anti-pattern 1]

## Arguments
| Tên | Kiểu | Required | Mặc định | Mô tả |
|---|---|---|---|---|
| query | string | ✅ | — | Từ khóa |
| max_results | integer | ❌ | 5 | Số kết quả |

## Return format
```json
{
  "items": [{"title": "...", "url": "...", "summary": "..."}],
  "error": null,
  "message": "OK"
}
```

## Quicktest

```bash
python -c "from pathlib import Path; from env_loader import load_lab_env; load_lab_env(Path.cwd()); from tools import TOOL_FUNCTIONS as T; r=T['your_tool_name'](query='test'); print(r)"
```

```

### Template tool.py

```python
"""your_tool_name — [mô tả ngắn]"""
from __future__ import annotations
import os
import requests
from typing import Any


def your_function(query: str, max_results: int = 5) -> dict[str, Any]:
    """[Docstring]"""
    api_key = os.getenv("YOUR_API_KEY")
    if not api_key:
        return {"error": "missing_api_key", "message": "YOUR_API_KEY not set", "items": []}

    try:
        response = requests.get(
            "https://api.your-service.com/search",
            headers={"Authorization": f"Bearer {api_key}"},
            params={"q": query, "limit": max_results},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        items = [
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "source": "your_service",
                "summary": item.get("snippet", ""),
            }
            for item in data.get("results", [])
        ]
        return {"items": items, "error": None, "message": f"Fetched {len(items)} results"}

    except requests.RequestException as exc:
        return {"error": "request_error", "message": str(exc), "items": []}
```

### Đăng ký tool (3 bước)

**1. `tools/__init__.py`** — Thêm 2 dòng:

```python
from .your_tool_name.tool import your_function   # import

TOOL_FUNCTIONS = {
    ...
    "your_tool_name": your_function,              # đăng ký
}
```

**2. `artifacts/tools.yaml`** — Thêm block mới:

```yaml
  - name: your_tool_name
    description: "Mô tả rõ khi nào dùng và khi nào KHÔNG dùng. Nêu convention args."
    parameters:
      type: object
      properties:
        query: {type: string, description: "Từ khóa"}
        max_results: {type: integer, default: 5, description: "Số kết quả"}
      required: [query]
```

**3. Smoke test**:

```powershell
python -c "from pathlib import Path; from env_loader import load_lab_env; load_lab_env(Path.cwd()); from tools import TOOL_FUNCTIONS as T; r=T['your_tool_name'](query='test'); print({'error': r.get('error'), 'count': len(r.get('items', []))})"
```

---

## 8. Viết Eval Cases

### Schema bắt buộc

```json
{
  "dataset_id": "day04_v2_group_2A202601602",
  "dataset_role": "group",
  "description": "10 eval cases tự viết — nhóm 2A202601602",
  "cases": [
    {
      "id": "G01_single_web_news",
      "phase": "B",
      "query": "Tin tức về Gemini 2.0 hôm nay?",
      "failure_type": "wrong_tool",
      "expect": {
        "tool_calls": [{"name": "lookup", "args": {"query": "Gemini 2.0", "topic": "news", "timeframe": "day"}}]
      },
      "metadata": {"what_it_tests": "Route đúng lookup với topic=news timeframe=day"}
    },
    {
      "id": "G06_multi_clarify_then_search",
      "phase": "B",
      "turns": [
        {"role": "user", "content": "Tìm tweet về chủ đề này"},
        {"role": "user", "content": "Chủ đề AI Agents"},
        {"role": "user", "content": "Chỉ lấy tweet mới nhất thôi"}
      ],
      "failure_type": "missing_info",
      "expect": {
        "tool_calls": [{"name": "social_search", "args": {"query": "AI Agents", "search_type": "Latest"}}]
      },
      "metadata": {"what_it_tests": "Multi-turn: carry topic từ turn 2, search_type=Latest từ turn 3"}
    }
  ]
}
```

### Checklist 10 cases

| #  | ID  | Loại       | failure_type     | Mục đích                            |
| -- | --- | ----------- | ---------------- | -------------------------------------- |
| 1  | G01 | single-turn | wrong_tool       | `lookup` với topic=news             |
| 2  | G02 | single-turn | wrong_arg_value  | `social_search` với search_type=Top |
| 3  | G03 | single-turn | missing_info     | `clarify` (thiếu URL)               |
| 4  | G04 | single-turn | out_of_scope     | no_tool — câu ngoài phạm vi        |
| 5  | G05 | single-turn | wrong_boundary   | `clarify(yes_no)` trước send       |
| 6  | G06 | multi-turn  | missing_info     | carry context từ turn 2               |
| 7  | G07 | multi-turn  | wrong_arg_value  | sửa limit từ turn trước            |
| 8  | G08 | multi-turn  | wrong_tool       | switch tool khi user yêu cầu         |
| 9  | G09 | multi-turn  | unnecessary_tool | no_tool ở turn cuối                  |
| 10 | G10 | multi-turn  | wrong_arg_value  | carry timeframe, đổi query           |

> **Quan trọng**: Multi-turn chỉ chấm **turn cuối cùng**. Turn đầu là context setup.

> **Failure types**: `wrong_tool`, `wrong_arg_value`, `wrong_boundary`, `unnecessary_tool`, `out_of_scope`, `missing_info`

---

## 9. Vòng lặp tối ưu

### v0 (Baseline) — Biết mình đang ở đâu

Chạy và ghi lại 4 số từ run JSON:

```
case_accuracy:          ____
tool_routing_accuracy:  ____
argument_accuracy:      ____
multiturn_accuracy:     ____
```

### v1 — Fix clarify routing

**Hypothesis**: "Prompt nói 'hates being asked questions → never ask back' nên agent không gọi `clarify` khi thiếu handle/URL"

**Sửa `artifacts/system_prompt.md`**:

```markdown
You are a research assistant with access to tools.

## MANDATORY: Always call `clarify` when:
- User asks for someone's tweets but does NOT specify a username/handle
- User says "this article" or "this post" but provides NO URL
- User asks to send/post/publish anything (ask yes_no for confirmation first)

## Out of scope (answer directly, NO tool):
- Math, coding questions, creative writing, general knowledge

## Tool selection rules:
- Specific URL given → use `fetch`
- Tweet by topic/keyword → use `social_search`
- Tweet by person → use `timeline` with their handle
- Web news → use `lookup` with topic=news
- Parallel needs → call multiple tools at once
```

### v2 — Fix tool description precision

**Hypothesis**: "Description của `lookup` và `social_search` quá vague → model confused"

**Sửa `artifacts/tools.yaml`** — cải thiện description:

```yaml
- name: lookup
  description: >
    Search the WEB (NOT Twitter/social media) for information.
    Use when: finding news articles (topic=news), general research.
    Do NOT use when: user asks about tweets, posts, or mentions on Twitter/X.
    timeframe convention: day=today, week=this week, month=this month, year=this year.
```

### v3 — Fix send boundary

**Hypothesis**: "Agent gọi `send` trực tiếp vì description không nói rõ confirmation required"

**Sửa `tools.yaml`** phần `send`:

```yaml
- name: send
  description: >
    Send text to Telegram. THIS IS AN IRREVERSIBLE ACTION.
    BEFORE calling this tool, you MUST first call clarify(response_type=yes_no) to get confirmation.
    Only call send with confirmed=true AFTER the user explicitly agrees.
```

### Ghi version_log.csv

```csv
version,author,changed_artifact,artifact_version,...
v0,HaiDang,baseline,v0.0,...,case_accuracy,,,0.35,runs/v0_base_XXX.json
v1,HaiDang,system_prompt.md,v1.0,...,Fix clarify routing,case_accuracy,0.35,0.55,runs/v1_base_XXX.json
v2,HaiDang,tools.yaml,v1.1,...,Fix lookup vs social_search,tool_routing_accuracy,0.60,0.75,runs/v2_base_XXX.json
v3,HaiDang,tools.yaml,v1.2,...,Fix send boundary,case_accuracy,0.70,0.85,runs/v3_base_XXX.json
```

---

## 10. UI Streamlit

### Thêm dependency

Trong `requirements.txt`, thêm:

```
streamlit>=1.30.0
```

Cài:

```powershell
python -m pip install "streamlit>=1.30.0"
```

### Template app.py

```python
"""app.py — Research Agent UI
Tái dùng run_model_tool_loop từ chat.py — không viết agent loop mới.
"""
import streamlit as st
from pathlib import Path
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import build_artifact_version
from chat import run_model_tool_loop

ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
load_lab_env(ROOT)

st.set_page_config(page_title="Research Agent", page_icon="🔍", layout="wide")
st.title("🤖 Research Agent — DAY04 Lab")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    provider_name = st.selectbox("Provider", ["openrouter", "openai", "anthropic", "gemini"])
    version_label = st.selectbox("Version", ["v0", "v1", "v2", "v3"])
    max_rounds = st.slider("Max Tool Rounds", 1, 8, 4)

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "tool_events" not in st.session_state:
    st.session_state.tool_events = []

# Display history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Tool trace
if st.session_state.tool_events:
    with st.expander(f"🔧 Tool Trace ({len(st.session_state.tool_events)} events)", expanded=False):
        for event in st.session_state.tool_events:
            st.json(event)

# Input
if user_input := st.chat_input("Nhập câu hỏi..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Đang xử lý..."):
            try:
                provider = make_provider(provider_name)
                tool_declarations = load_tool_declarations(ARTIFACTS_DIR / "tools.yaml")
                openai_tools = to_openai_tools(tool_declarations)
                system_prompt_text = (ARTIFACTS_DIR / "system_prompt.md").read_text(encoding="utf-8")

                messages = [
                    {"role": "system", "content": system_prompt_text},
                    *[m for m in st.session_state.messages if m["role"] != "system"],
                ]

                result = run_model_tool_loop(
                    provider=provider,
                    messages=messages,
                    tools=openai_tools,
                    model=None,
                    max_tool_rounds=max_rounds,
                )

                assistant_text = result["assistant_text"]
                st.markdown(assistant_text)
                st.session_state.messages.append({"role": "assistant", "content": assistant_text})
                st.session_state.tool_events = result.get("tool_events", [])

                if result["tool_events"]:
                    with st.expander(f"🔧 {len(result['tool_events'])} tool(s) called", expanded=True):
                        for event in result["tool_events"]:
                            col1, col2 = st.columns([1, 2])
                            with col1:
                                st.code(event["tool"])
                                st.json(event.get("args", {}))
                            with col2:
                                r = event.get("result", {})
                                if r.get("error"):
                                    st.error(f"Error: {r['error']}")
                                else:
                                    items = r.get("items", [])
                                    st.success(f"✅ {len(items)} items")

                st.caption(f"version={version_label} | rounds={len(result['rounds'])}")

            except Exception as exc:
                st.error(f"❌ Error: {exc}")

st.divider()
st.caption("DAY04 Lab — Research Agent | Nhóm 2A202601602")
```

### Chạy UI

```powershell
streamlit run app.py
```

### Deploy với Cloudflare Tunnel

```powershell
# Cài cloudflared
winget install --id Cloudflare.cloudflared

# Sau khi streamlit đang chạy (terminal khác):
cloudflared tunnel --url http://localhost:8501
```

→ Copy link `*.trycloudflare.com`, paste vào `REPORT.md` Phần A.

---

## 11. Checklist nộp bài

### Files bắt buộc trong `starter_v0/`

```
✅ artifacts/system_prompt.md
✅ artifacts/tools.yaml
✅ artifacts/version_log.csv   (v0, v1, v2, v3 đều có)
✅ artifacts/REPORT.md         (Phần A + Phần B đầy đủ)
✅ data/eval_group.json        (đúng 10 cases)
✅ runs/*.json                 (ít nhất 4 files: v0, v1, v2, v3)
✅ transcripts/*.transcript.json
✅ tools/YOUR_TOOL/TOOL.md
✅ tools/YOUR_TOOL/tool.py
✅ app.py
✅ requirements.txt            (có streamlit>=1.30.0)
```

### Files KHÔNG được nộp

```
❌ .env (chứa API keys)
❌ .venv/
❌ __pycache__/
❌ arxiv_papers/
❌ *.pyc
```

### Pre-submission checklist

- [ ] `python scripts/preflight_provider.py --provider openrouter` → PASS
- [ ] Smoke test tool mới → PASS (`error: None`)
- [ ] `streamlit run app.py` → mở được `http://localhost:8501`
- [ ] Cloudflare tunnel link còn sống, test từ máy khác
- [ ] `runs/*.json` có đủ v0–v3, `provider_error_cases=0`
- [ ] `version_log.csv` có đủ 4 rows với metric thật
- [ ] `eval_group.json` có đúng 10 cases (5 single + 5 multi)
- [ ] `REPORT.md` Phần A điền đầy đủ (xong trước 16:30)
- [ ] Không có `.env`, token, key nào trong git history

---

## 12. Tái tạo khi conflict

> **Kịch bản**: Merge conflict nặng, mất context, cần rebuild. Kéo file `NHOM.md` về là đủ.

### Cách dùng file này

```powershell
# Pull file MD mới nhất từ repo
git fetch origin
git checkout origin/main -- NHOM.md
```

1. **Đọc Mục 3** → hiểu cấu trúc file nào ai owns
2. **Đọc Mục 4** → biết phân công là gì
3. **Đọc Mục 7** → template để rebuild tool bị mất
4. **Đọc Mục 8** → rebuild `eval_group.json`
5. **Đọc Mục 10** → rebuild `app.py`
6. **Đọc Mục 9** → biết hypothesis nào đã chạy, đang ở version nào

### Trạng thái hiện tại (cập nhật sau mỗi milestone)

| Item            | Trạng thái | Ghi chú                      |
| --------------- | ------------ | ----------------------------- |
| Provider setup  | ✅ Done      | venv + requirements installed |
| API keys .env   | ⬜ Todo      | Điền đủ trước preflight |
| Preflight PASS  | ⬜ Todo      |                               |
| Baseline v0     | ⬜ Todo      |                               |
| Tool mới#1     | ⬜ Todo      | Người 2 — tên: ___        |
| Tool mới#2     | ⬜ Todo      | Người 3 — tên: ___        |
| v1              | ⬜ Todo      | Hypothesis: fix clarify       |
| v2              | ⬜ Todo      | Hypothesis: fix descriptions  |
| v3              | ⬜ Todo      | Hypothesis: fix boundary      |
| eval_group.json | ⬜ Todo      | Người 4                     |
| UI (app.py)     | ⬜ Todo      | Người 5                     |
| Deploy link     | ⬜ Todo      | Cloudflare tunnel             |
| REPORT Phần A  | ⬜ Todo      | Deadline 16:30                |
| REPORT Phần B  | ⬜ Todo      | Sau showdown                  |

**→ Update bảng này sau mỗi milestone để nhóm sync nhanh!**

---

## 📚 Tài liệu tham khảo

| Tài liệu                 | Đường dẫn                                         |
| -------------------------- | ----------------------------------------------------- |
| README Lab                 | `README.md`                                         |
| Tool Setup                 | `TOOL-SETUP.md`                                     |
| Eval schema mẫu           | `starter_v0/samples/eval_group.schema.example.json` |
| Version log mẫu           | `starter_v0/samples/version_log.example.csv`        |
| Base eval cases (20 cases) | `starter_v0/data/eval_base.json`                    |
| Tool registry              | `starter_v0/tools/__init__.py`                      |
| Provider implementations   | `starter_v0/providers/`                             |

---

*File này được viết để nhóm có thể tái tạo toàn bộ context chỉ từ 1 file duy nhất.*
*Kéo file MD về → đọc → có đủ mọi thứ để tiếp tục.*

**Cập nhật lần cuối**: 2026-07-29 | **Maintain**: Trịnh Hải Đăng (haidang2425)
