# Research notes

Snapshot taken 2026-11-06 from reading the whole repo (13 days before the 19 Nov 2026 competition). Tests: 7 passed locally on Python 3.14; CI uses 3.12. Nothing below has been fixed yet; items marked *verified by reading* are from code, not from running a probe.

## What the system is

A fixed six-stage pipeline, not a planner. `orchestrator.run()` calls tools in a hard-coded order; the only branch is `genuine` from `scam.check`, which swaps the explanation, lesson (forced to PDRM), route (PDRM) and draft (scam report). Calling it an agent rests on the trace, the tool registry and that one plan switch.

| Piece | Size | Notes |
|---|---|---|
| `tools.py` | 12 registry tools | rules + regex; OCR via optional pytesseract, falls back to the supplied text. The agent (`loop.py`) calls 8 tools of its own, see AGENT.md |
| `orchestrator.py` | 1 function | builds `Trace`, assembles `AnalyzeResponse` |
| `llm.py` | 1 function | Anthropic only, returns `None` on any failure |
| Frontend | `app.js` 519, `data.js` 359, `index.html` 411, `styles.css` 578 lines | state in `localStorage` (`faham_*`), read-aloud via `speechSynthesis`, local demo trace if the API is down |
| Data | 9 issuers (LHDN JPJ PTPTN PDRM COURT COUNCIL UTILITY KWSP_PERKESO BANK), 6 practice items | offices are demo data |

## Findings (ranked)

### Correctness and trust
1. **`retrieved_at` is fake freshness.** `gov.retrieve` returns cached JSON (the code says "Production: fetch `source_url` here"), but the orchestrator stamps `retrieved_at=now_iso()`. The UI and `API.md` present it as a live retrieval. Same for `confidence`: `"High"` just means `genuine`, not that anything was checked. *Verified by reading.* This contradicts the PRIVACY_SAFETY promise ("shown with `retrieved_at` and confidence"). Fix: stamp the registry file date, or label it "cached".
2. **Redaction is narrower than the docs claim.**
   - The name is masked only after `Kepada:` and up to the next comma or newline; a name elsewhere in the letter passes through to every tool and the LLM.
   - `PHONE_RE` covers mobile numbers (`01x`), not landlines (`03-…`, `07-…`) or `+60 3`.
   - No address, email or vehicle-plate masking, though JPJ letters carry plates.
   - Order matters: IC runs before account, which is correct, but a 12-digit account without dashes can be read as an IC.
3. **Scam check has false negatives by design.** An unknown issuer with no red-flag hit gets `genuine=True` and score 80. A short phishing message with no keyword (for example only a lookalike domain ending in `.my`) passes: any `.my` domain is treated as safe (`not d.endswith(".my")` is the only unofficial test). Only domains ending `.gov.my` or the issuer's list count as good signs, but a `.my` lookalike raises no flag.
4. **Scam check has false positives.** `atas nama` ("on behalf of") and `rahsia` ("secret") are plain substrings and appear in genuine letters. `otp` has no word boundary, so it matches inside other words. `whatsapp` flags a genuine agency that lists a WhatsApp helpline. One hit costs 22 points, so two hits flip a genuine letter to "SCAM" (80 + 5×good − 22×2). The test suite only covers one clean genuine and one obvious scam letter.
5. **Deadline logic.** `extract.fields` overwrites any deadline with `"24 hours (pressure tactic)"` when it sees "24 jam". A genuine letter with a "24 jam" clause loses its real date, and the reminder in `act.draft` then reads "7 days before 24 hours (pressure tactic)". If no "sebelum" is present it takes the last date in the text, which may be an issue date.
6. **Language leaks.** The scam draft and the genuine draft are always Bahasa Melayu regardless of `language`. The `teach.lesson` scam branch is hard-coded English/BM mix. zh/ta templates are unreviewed.
7. **Only the generic explanation exists offline.** Without an LLM key the explanation is a template (issuer, type, amount, deadline). It never says what the letter is asking for, so "explain" is thin in the default demo.
8. **LLM error path is silent.** Failures log a warning and fall back, so a bad key looks like working offline mode. `/api/health` reports the configured provider, not whether the call succeeds.

### Product and process
9. **Docs vs reality gaps:** README says Tesseract OCR is wired in, but the API takes text only (`AnalyzeRequest.text`, `min_length=10`) and there is no image upload endpoint. `ocr.read` takes `image_bytes` that nothing passes. The Dockerfile installs Tesseract `msa` but the default path never uses it. "On-device OCR", live retrieval, geolocated offices and the repeat-letter metric are roadmap only.
10. **Design system conflicts with antislop.** README specifies frosted glass with `backdrop-filter: blur(18px)`, animated violet orbs and a 12-column bento grid. Those hit R-01, R-05, R-10 and R-13 (glass, orbs, bento, glow). Needs a decision from the owner (R-37 conflict protocol) before any restyle: keep as brand identity with written reasons, or change.
11. **CORS** allows origin `"null"` so `index.html` from disk works. Fine for the demo; remove for any hosted API.
12. **Python version drift:** local 3.14, CI/Docker 3.12.
13. **Test gaps:** no tests for `act.draft`, `gov.retrieve`/`office.locate`, `practice` content validity, the four languages, `llm.complete`, oversize input, or the false-positive cases in item 4.
14. **No input limits.** `text` has a minimum length but no maximum; regexes run on whatever is sent.

## Strengths worth keeping
- Clean separation: the agent gathers evidence, the rules are the floor and decide the verdict, offline always works.
- Typed contracts and a trace the UI can render, which is the strongest demo asset.
- Privacy and demo rules are written down (`PRIVACY_SAFETY.md`).
- Small enough to explain in the 5 minute video.

## Suggested order before 19 Nov
1. Fix items 1, 4 and 5 (honest metadata, word-boundary regexes, deadline logic) and add tests for each.
2. Widen redaction (item 2) and state its limits in `PRIVACY_SAFETY.md`.
3. Make `act.draft` and the lesson follow `language`; get zh/ta reviewed.
4. Decide the design direction (item 10), then pick the three demo letter types and write the SAMPEL letters (see `PITCH_PLAN.md` checklist).
5. Record the video; confirm the submission deadline with the organisers.

## Open questions for the team
- Which three letter types are in the demo, and which two languages beyond BM/EN?
- Keep the glass/orb look as brand identity, or redesign?
- Is an image upload path needed for the demo, or is pasted text enough?
- Will a hosted API be used (needs `API_BASE` and `FAHAM_ALLOWED_ORIGINS`)?

## Scope check against the project plan

Source: the Claude Doc "FAHAM – Agentic AI Challenge 2026 Plan" (read 2026-11-06, rev 7). The repo's `README.md` and `PITCH_PLAN.md` were written from it. Track chosen: Agentic AI (19 Nov); Creative Technology & Innovation (18 Nov) is the alternative. Theme: Edutainment & Innovation.

| Plan item | In the repo | Gap |
|---|---|---|
| Read: scan, classify issuer, extract amount/deadline | Text in only; classify and extract work on pasted text | The video says "scan". No image/PDF upload path; `ocr.read` is never given bytes |
| Verify: scam check | Done (rules), see findings 3 and 4 | False positives/negatives |
| Explain in BM/EN/中文/தமிழ், read-aloud | Templates in 4 languages, Web Speech in the UI | Template explanation is generic; zh/ta unreviewed |
| Teach: "Kenapa?" card, Kamus Surat | `teach.lesson` plus glossary in `localStorage` | One lesson per issuer, 7 total |
| Route: online click-by-click, walk-in with office, hours, booking, documents | 2 to 4 cached steps per issuer; BANK has 1 walk-in step; offices are demo data | "Retrieve at time of use" is not implemented (finding 1). Queue-app info is absent |
| Act: reminder, draft, user approves | `act.draft` returns text and a reminder string, `requires_approval=True` | No real reminder (calendar/ICS) and no approval endpoint; approval exists only as UI state |
| Practice: "agent generates clearly fictional letters" | 6 static items in `practice.json` | Not generated by the agent; the plan says it must reuse the same agent. Readiness levels exist in `data.js` |
| Family: child scans, explanation sent to the parent's language | Selector view in the frontend | Nothing is sent; it re-renders the same result in another language |
| Plan's decision flow: 2 decisions, 3 outcomes | 1 branch (`genuine`) | The doc's flow diagram has one more decision (online vs walk-in) that the orchestrator does not make; it always returns both |
| Metric: less full help on repeat letter types | Not tracked | Only the glossary is stored on the device |
| Demo: 3 letter types | LHDN, JPJ, PTPTN samples are the natural pick | Not yet confirmed by the team |

Priority for the 13 days left: (1) make the online/walk-in decision explicit in the orchestrator and trace, since it is what makes the demo look like an agent; (2) make the practice mode reuse `scam.check` on its items so it is the same agent; (3) fix findings 1, 4, 5; (4) add a paste-or-upload path that actually reaches `ocr.read`, or change the video wording from "scan" to "paste".

## Status update 2026-11-06 (after first fix round)
Done: scam-check boundaries and lookalike domains, deadline logic, honest `retrieved_at`/confidence, explicit route decision in the trace, input caps, CORS null off by default, LLM prompt guards, non-root Docker, nginx headers. Practice items now carry the real `scam.check` verdict (`agent` field). `/api/analyze` accepts `image_b64` (422 if OCR is unavailable). Redaction now covers names after titles and `Nama:`, landlines, emails, address lines and plates. Frontend has a consent gate, "Clear my data", a paste-or-upload box and the agent verdict in practice. 20 tests pass; the API was smoke-tested live. Not done: browser click-through of the frontend, real Malay OCR accuracy test, Docker build, post-redaction digit guard in the redactor itself, fixing the generic offline explanation for UNKNOWN issuers ("an unknown sender (notice)").
Findings 1, 2 (partly), 3, 4, 5, 9 (partly), 11, 14 above are addressed; 6, 7, 8, 10, 12, 13 remain.
