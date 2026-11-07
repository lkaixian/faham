# Trust, privacy and safety

Judges are likely to ask three questions: *Can it be wrong? What happens to my letter? Why not just use a general chatbot?*

| Risk | Mitigation in FAHAM |
|---|---|
| Wrong or outdated procedure | Steps come from the official source registry at the time of use and are shown with the source link, a `retrieved_at` timestamp and a confidence level, labelled "not legal advice". |
| Privacy of letters (IC numbers, addresses) | `privacy.redact` runs first. Only redacted text reaches the other tools and the LLM. The API does not store letters. PDPA compliance is a design goal. |
| "A general chatbot can do this" | FAHAM adds Malaysia-specific procedures, the nearest office with queue and booking details, scam checks, and a practice mode on the same agent. |
| Instructions hidden in a letter (prompt injection) | The letter is untrusted data: wrapped in tags, the model is told to ignore instructions inside it, a model answer with a web address that is not in the letter is dropped, the verdict comes from rules, and no tool can send, pay or submit. Tests: `tests/test_p3.py`. |
| Panic after paying | The **I already paid** card works with no server: bank hotline, NSRC 997, a script to read out, what to prepare, in four languages. |
| Harmful action by the agent | The agent only drafts and pre-fills. `requires_approval: true` is set on every action, and the user approves before anything is sent or paid. |

## Data handling
1. **Scan:** the image stays on the device until it is redacted (production target: on-device OCR).
2. **Redact:** IC, phone, account and addressee are masked.
3. **Process:** the agent works on the redacted text only.
4. **Discard:** the letter is not stored. Only the learned glossary terms stay, on the user's device.

## What the server keeps

| Item | What | How long |
|---|---|---|
| Letter or message text | Held in memory while it is checked. Not written anywhere, not logged | Seconds |
| Analysis cache | The finished result for the **redacted** text, key = hash of redacted text, language, postcode | Up to 1 hour, memory only |
| "Others checked" counter | A one-way fingerprint of the redacted text, a count and first/last timestamps (SQLite). No text, name or number | 90 days |
| Semak Mule details | Accounts, phones, companies from the request, returned to that user only | Not kept |

The browser keeps the user's dictionary, points, language and consent tick, and a service-worker copy of the app shell (never `/api/`).

## Processors
If the optional AI service is on, the **redacted** text goes to ILMU (a Malaysian AI provider) or the configured LLM provider, only to write the explanation, and is skipped if personal details remain. Text-to-speech receives the explanation text, not the letter. Tamil is read by the browser's own voice.

## Notices and analytics
The privacy notice is in the app (About and privacy, `pv_*` strings, four languages): data protection contact (placeholder until a real address is set), retention, processors, breach notification and last-updated date. There are no ads, no analytics beacons and no tracking cookies in this repository; the Cloudflare Web Analytics beacon and Bot Fight Mode are edge settings and must be switched off, see [DEPLOY.md](DEPLOY.md). Every official number, link and office is shown with a last-checked date and flagged as a saved copy or sample data.

## Demo rules
- Use only clearly fictional letters, marked **SAMPEL · FIKTIF**.
- Never use real people's letters or IC numbers.
- Scam examples must not include working links or real phone numbers.
