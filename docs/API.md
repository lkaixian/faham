# API reference

Base URL (local): `http://localhost:8000`. Interactive docs are at `/docs`.

## `GET /api/health`
```json
{ "status": "ok", "llm_provider": "none", "tools": ["ocr.read", "..."] }
```

## `GET /api/tools`
Lists each registered tool with its description.

## `POST /api/analyze`
Request:
```json
{
  "text": "NOTIS TAKSIRAN ... RM 1,240.00 sebelum 15 Disember 2026 ...",
  "language": "bm",
  "postcode": "84000"
}
```
`scam.verdict` is `likely_scam` (score < 60), `no_signals` (known issuer, no red flags, score >= 80; not proof) or `caution` (everything else). `genuine` is kept and means "not flagged", not "proven". `reasons[].kind` is `risk | ok | info`. `reasons[].evidence` lists the exact snippets of `redacted_text` behind a reason (a link, a phrase, a reference number); the web app highlights them beside the result.

Response (abridged):
```json
{
  "redacted_text": "... Kepada: [NAME] ...",
  "fields": { "issuer": "LHDN", "letter_type": "Tax assessment", "amount": "RM 1,240.00", "deadline": "15 Disember 2026", "reference": "LHDN/SAMPEL/TT2025/0001" },
  "scam": { "verdict": "no_signals", "genuine": true, "score": 95, "red_flags": [], "good_signs": ["..."], "reasons": [{ "kind": "ok", "text": "..." }, { "kind": "info", "text": "We only read the text you gave us. ..." }], "verify_yourself": ["Type the website address yourself ...", "..."], "scam_type": null },
  "explanation": "Surat ini daripada Lembaga Hasil Dalam Negeri Malaysia ...",
  "lesson": { "question": "Kenapa saya dapat surat ini?", "answer": "...", "terms": ["Taksiran", "PCB"] },
  "route": { "online_steps": ["..."], "walkin_steps": ["..."], "source_url": "https://www.hasil.gov.my", "retrieved_at": "2026-11-06T05:00:00+00:00", "confidence": "High" },
  "action": { "draft": "...", "reminder": "7 days before 15 Disember 2026", "requires_approval": true },
  "trace": [{ "stage": "read", "kind": "tool", "tool": "ocr.read", "message": "93 words read", "flag": false }],
  "entities": { "accounts": ["8001234567"], "phones": ["012-3456789"], "companies": [] },
  "others_checked": 3,
  "disclaimer": "Tulen gives guidance, not legal advice. ..."
}
```
`scam.scam_type` is `macau | family_impersonation | parcel | job | love | investment | phishing_refund | apk_install | other`, or `null` when the verdict is `no_signals`. Lesson, route and draft follow it, in the requested language.

`entities` (only when the verdict is not `no_signals`) are bank accounts, phone numbers and company names taken from this request's own text, so the user can type them into the official Semak Mule portal. Tulen does not call Semak Mule and stores nothing. IC numbers are never returned. `others_checked` is how many people checked a similar message (a one-way fingerprint counter, 90-day retention; `0` for bundled samples).

`route.retrieved_at` is the date of the saved registry copy and ends with `(cached)`: it is not a live lookup. Office lines are labelled `sample data`.

Errors: `422` bad input or OCR unavailable, `503` with `Retry-After: 5` when the queue is full for longer than `FAHAM_QUEUE_PATIENCE`.

## `POST /api/analyze/stream`
Same request body. Response is `text/event-stream` (send it with `fetch`, not `EventSource`, because it is a POST):
```
event: queue
data: {"position": 2, "waiting": 2}

event: verdict
data: {"verdict": "likely_scam", "score": 40, "scam_type": "macau", "issuer": "PDRM", "fields": {...}, "reasons": [...], "verify_yourself": [...]}

event: explanation
data: {"text": "..."}

event: result
data: { ...the full AnalyzeResponse... }
```
`queue` appears only while waiting. `verdict` is rules-only and arrives first. A failure is `event: error` with `{status, detail}`.


## `GET /api/practice?n=5`
Returns `n` fictional messages for Spot-the-scam:
```json
[{ "sender": "...", "channel": "SMS", "text": "...", "is_scam": true, "clues": ["..."] }]
```
