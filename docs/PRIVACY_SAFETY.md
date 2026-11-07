# Trust, privacy and safety

Judges are likely to ask three questions: *Can it be wrong? What happens to my letter? Why not just use a general chatbot?*

| Risk | Mitigation in Tulen |
|---|---|
| Wrong or outdated procedure | Steps come from the official source registry at the time of use and are shown with the source link, a `retrieved_at` timestamp and a confidence level, labelled "not legal advice". |
| Privacy of letters (IC numbers, addresses) | `privacy.redact` runs first. Only redacted text reaches the other tools and the LLM. The API does not store letters. PDPA compliance is a design goal. |
| "A general chatbot can do this" | Tulen adds Malaysia-specific procedures, the nearest office with queue and booking details, scam checks, and a practice mode on the same agent. |
| Instructions hidden in a letter (prompt injection) | The letter is untrusted data: wrapped in tags, the model is told to ignore instructions inside it, a model answer with a web address that is not in the letter is dropped, the verdict comes from rules, and no tool can send, pay or submit. Tests: `tests/test_p3.py`. |
| Panic after paying | The **I already paid** card works with no server: bank hotline, NSRC 997, a script to read out, what to prepare, in four languages. |
| Harmful action by the agent | The agent only drafts and pre-fills. `requires_approval: true` is set on every action, and the user approves before anything is sent or paid. |

## Data handling
1. **Read:** text comes out of the input. Images are read by OCR on the server (production target: on-device OCR).
2. **Redact:** `privacy.redact` masks IC numbers, emails, display names, phone numbers, account numbers, addresses, plates, names (after Kepada/Nama, titles, BIN/BINTI/A/L forms), passport-style IDs, dates of birth, and any leftover run of 8 or more digits. It is regex-based and best effort.
3. **Hide again for models:** in the agent's prompts, runs of 7 or more digits become `[NUMBER]`; tool results are masked too; a guard blocks any model call that still contains something that looks like an email, an IC or a long digit run.
4. **Process:** the agent and the explanation work on the masked text only. Scam verdicts use fixed templates, not model text.
5. **Reach outside:** only official URLs (never the message) and domain names that appear in the message leave the server for the agent's lookups.
6. **Discard:** the letter is not stored. Only learned glossary terms stay, on the user's device.

The pattern-by-pattern list, what each service receives, and the known gaps (free-form names, unusual address styles, words inside links) are in [AGENT.md, section 9](AGENT.md#9-personal-data-pii).

## Files that can carry malware (ZIP, RAR, APK, scripts, programs, Office macros)
Tulen is not an antivirus. It asks whether a file should have reached you, not whether its code is malicious, and says so on every file result ("what we checked, what we did not check").

- **Never run, installed or saved.** Files are inspected in memory. Nothing is executed, extracted to disk or kept.
- **Archives.** ZIP and RAR contents are listed. For a plain ZIP, the first bytes of up to 50 members are sniffed and up to 10 interesting members (apps, programs, scripts, Office files, nested ZIPs) are read in memory and inspected, one level deep. Every read is bounded and charged to one 16 MB budget per request, so a zip bomb cannot expand: the byte counter stops the read whatever the headers claim. Only stored and deflate members are read; protected, overlapping or oddly built archives are reported and never decompressed. RAR is listed with `rarfile` in pure Python; its contents are not read, because that would need an outside program, and no outside tool is ever run.
- **A limited child process for ALL untrusted parsing.** File inspection, letter extraction (PDF, DOCX, text, email, with their attachments) and image OCR all run in a separate process (`app/sandbox.py`, `app/inspect_worker.py`), never in the API process. Each job has a CPU limit, a memory limit, a file-size limit (inspection cannot write a file at all; extraction and OCR may write small temporary files in RAM-backed `/tmp`), a hard timeout, and an environment with no API keys or secrets. At most `TULEN_WORKERS` (default 4) run at once; the rest wait briefly and then get "busy" (503). If a child crashes or hangs the file is refused ("could not be read safely") or, for inspection, counted as unreadable: never an error page and never a pass. In `docker-compose.yml` the API container also has a read-only filesystem (RAM-backed `/tmp` and `/app/var` only), no extra Linux capabilities, and memory and process caps. This is isolation, not a full sandbox: a bug in a parser or in Python's own libraries is the remaining risk, so keep the image patched.
- **What is read.** An Android app's manifest (package name and requested permissions), the first 64 KB of a script (text patterns such as downloading and starting something) and the header of a Windows program (signed or not, packed or not). The file's bytes never reach any model: the agent sees one neutral line with names stripped of hidden characters.
- **Fingerprint.** The SHA-256 of an inspected file is shown to the person with a VirusTotal link. The link opens only when they click; Tulen sends nothing to VirusTotal. Letters (PDF, DOCX, text, email, images) are never fingerprinted.
- **Verdicts.** A file can come out as "caution" at best, never as safe. The optional "I got this on WhatsApp, SMS or a link" tick adds context and is sent as the `X-Via-Chat: 1` header; nothing about it is stored.

## Outbound requests and web headers
- **No server-side request forgery.** The agent may fetch a page only if it is https on an official agency site, and only when every address the name resolves to is a public internet address (loopback, private ranges, link-local and cloud-metadata addresses and multicast are refused). The connection goes to the address that was checked, not to a second DNS answer, and every redirect is checked again. This matters because any `.edu.my` name counts as official and anyone can run one.
- **nginx:** a strict Content-Security-Policy (scripts only from our own origin), `Permissions-Policy`, `Cross-Origin-Opener-Policy`, no framing, `nosniff`, no referrer; API responses carry `Cache-Control: no-store` because they are private analysis results; per-client rate limits and an upload size cap.
- **Dependencies:** CI runs `pip-audit` on the runtime requirements on every push and weekly, and the workflow token is read-only.

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
