---
name: policy_deadline
track: bonus
kind: local_knowledge
provider: markdown_folder
requires_env: []
inputs: [query, top_k]
outputs: [results, freshness, trust_boundary, scanned_docs]
side_effect: false
---
# policy_deadline

Team-authored bonus tool. Extracts structured `{date_text, iso_start,
iso_end, event}` entries from calendar/deadline-style docs in
`company_policy/` (docs whose `doc_id`/`title`/`tags` mention "deadline" or
"calendar" — currently `vinuni-general-2027-academic-calendar.md` and
`vinuni-admissions-key-admission-deadlines-admission.md`), instead of
returning raw paragraph text for date questions.

## Why this tool exists

These two source docs are scraped PDF/webpage dumps: the academic calendar
is a giant unstructured run-on string of calendar-grid digits and event
labels (`"1-2-Sep Independence Day 5-Sep Move in Day ..."`), and the
admissions deadlines page mixes real content with nav-menu link noise. A
generic keyword/paragraph search returns a wall of text for "when is X
due" — this tool regex-parses out individual `(date, event)` pairs so the
agent can answer with a specific date instead of a text dump.

## Date coverage & limitations

- `DD/MM/YYYY` and `DD/MM/YYYY – DD/MM/YYYY` ranges (e.g. admission
  rounds) parse to `iso_start`/`iso_end`.
- `D(-D)?-Mon` and `D-Mon-D-Mon` calendar-grid tokens (e.g. `8-12-Sep`,
  `18-Dec-3-Jan`) have **no year in the source text** — these come back
  with `iso_start: null` and a `note` field; treat `date_text` as
  best-effort, not authoritative.
- This is heuristic regex extraction over messy scraped text, not a real
  date parser. Always surface `source_url` alongside any date so the
  answer is verifiable.

## Notes

- `query` filters extracted events by keyword overlap on
  `event`/doc `title`; leave empty to list everything found.
- Results are sorted chronologically for ISO-dated entries; undated
  calendar-grid entries are appended after, in source order.
