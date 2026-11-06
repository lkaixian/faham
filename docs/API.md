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
  "scam": { "verdict": "no_signals", "genuine": true, "score": 95, "red_flags": [], "good_signs": ["..."], "reasons": [{ "kind": "ok", "text": "..." }, { "kind": "info", "text": "We only read the text you gave us. ..." }], "verify_yourself": ["Type the website address yourself ...", "..."] },
  "explanation": "Surat ini daripada Lembaga Hasil Dalam Negeri Malaysia ...",
  "lesson": { "question": "Kenapa saya dapat surat ini?", "answer": "...", "terms": ["Taksiran", "PCB"] },
  "route": { "online_steps": ["..."], "walkin_steps": ["..."], "source_url": "https://www.hasil.gov.my", "retrieved_at": "2026-11-06T05:00:00+00:00", "confidence": "High" },
  "action": { "draft": "...", "reminder": "7 days before 15 Disember 2026", "requires_approval": true },
  "trace": [{ "stage": "read", "kind": "tool", "tool": "ocr.read", "message": "93 words read", "flag": false }],
  "disclaimer": "FAHAM gives guidance, not legal advice. ..."
}
```

## `GET /api/practice?n=5`
Returns `n` fictional messages for Spot-the-scam:
```json
[{ "sender": "...", "channel": "SMS", "text": "...", "is_scam": true, "clues": ["..."] }]
```
