# Changelog

## Upgrade pass P0 to P4 (7 November 2026)

Numbers are the items of the upgrade request. Commits: P0 1-7 `a5411c2`, P1 8-9 `b70cac9`, 12-13 backend `e78e921`, P2 10-15 `94bf663`,
P3 16-18 `706e165`, P4 19-21 `09584d4`, 22 `615a2a0`, 23 and probes `9d75169`. 208 tests pass; the eval is at recall 1.000 and
false-positive rate 0.000 on its own dataset (see the caveat under item 22).

### P0: accuracy and safety
1. **Plate regex vs money.** `RM500`, `RM 500` and `rm500` are no longer masked as car plates; real plates still are.
2. **Family impersonation.** New rule (weight 55) that needs three parts together: a new-number or broken-phone excuse, a family address word, and a money ask. "Hi mak, ni nombor baru saya" alone does not fire. The verify list starts with "call the old number first".
3. **zh and ta lexicons.** Arrest, safe account, laundering, frozen account, TAC, secrecy, urgency and WhatsApp/Telegram patterns in Chinese and Tamil. Three new codes: `safe_account`, `laundering`, `account_frozen`.
4. **TNB false positive.** A legit TNB bill now reads as `no_signals`, with the amount and deadline extracted (test in `test_probes.py`). *Note:* I found no "details contradict each other" check anywhere in this repository, so I could not fix that specific behaviour. It probably came from the earlier TNB misclassification (fixed on the previous branch) or from the deployed LLM path. If you still see it live, send me the message.
5. **Determinism.** Temperature 0 for both providers; in-memory LRU+TTL cache (`cache.py`) keyed by a hash of redacted text, language, postcode and extra signals; a hit and a fresh run agree (tested). Raw text is never a key or value.
6. **Verdict from score.** `verdict_from_score` is the only place thresholds live (below 60 scam, 80 and above clear, else caution). Any flag or an unknown issuer caps the score at 79.
7. **Scam type.** `scam_type` is one of macau, family_impersonation, parcel, job, love, investment, phishing_refund, apk_install, other. Lesson, route and draft come from `scam_content.py` in all four languages. Non-agency messages never get an agency letter; an unknown sender gets a verify-first checklist.

### P1: reliability
8. **SSE stream** `POST /api/analyze/stream`: `queue`, `verdict` (rules only, first), `explanation`, `result`, `error`. Identical tool calls in one run are made once. The sample messages are cached at start-up when no LLM is set. *Gap:* the explanation arrives as one event, not token by token.
9. **Concurrency.** FIFO limiter (`FAHAM_MAX_CONCURRENT`), "you are number N" events, 503 with `Retry-After`; LLM calls retry with exponential backoff and fall back to the rules-only answer. Auth errors fail at once.

### P2: safety tools
10. **I already paid** card: offline, 4 languages, tel:997, a script to read out, copy and read aloud.
11. **Someone just called me**: four questions; a yes to "asked you to move money or give a TAC" or to "told you to keep it secret", or any two yeses, means hang up.
12. **Semak Mule shortcut.** Accounts, phones and company names found in the message are shown as text; one button opens the official portal in a new tab. No scraping, no API call.
13. **"Others checked" count.** SQLite table of fingerprint, count and two timestamps only; 90-day retention; no text.
14. **Voice input** (Web Speech, language-aware) and, for Tamil with no device voice, a clear message instead of reading Tamil with the wrong voice. *Not tested on a real microphone or a phone.*
15. **Family WhatsApp share** via `wa.me` with a ready message; the user presses send.

### P3: trust
16. **Privacy notice** (4 languages): DPO placeholder, retention, processors (ILMU or the configured LLM provider), breach notification, last-updated date. The blanket "no analytics" line is replaced with an accurate statement about the hash counter. `a_review` added for BM and EN.
17. **Source and last checked** on route sources, hotline and Semak Mule links; saved copies and demo office data are labelled "sample data".
18. **Prompt-injection tests** (`test_p3.py`): injected text cannot change the verdict, the draft or the explanation; the letter is wrapped as untrusted data; a model answer containing a foreign link is dropped; no endpoint sends or pays.

### P4: release
19. **PWA**: `manifest.webmanifest`, `sw.js` (shell only; never `/api/` or other origins), icons built from the logo pack (192, 512, maskable).
20. **Metadata**: Open Graph and Twitter card tags with a 1200x630 image, logo alt text, `lang` spans on bilingual intro text. *Open Graph URLs use `https://lkaixian.github.io/faham/` as an assumption: change them to the real site.*
21. **CSP**: production `nginx.conf` has `connect-src 'self'` and proxies `/api/`; `nginx.dev.conf` (used by docker compose) keeps localhost. `docs/DEPLOY.md` explains turning off Cloudflare Web Analytics and Bot Fight Mode. *These are dashboard settings: I could not check or change them.*
22. **Eval harness** in `backend/tests/eval/`: 88 labelled messages (22 per language), precision, recall, FPR, p50, p95, `docs/EVAL.md`, CI gate at recall 0.9 and FPR 0.1. **Caveat:** the first run scored recall 0.694 (dev) and 0.625 (held-out), exposing missing rules for job, investment, romance and prize scams. Rules were added (`guaranteed_returns`, `advance_fee`, `romance_money`, `prize_win`) and then tightened after they fired on ordinary sentences. The 1.000 now reported is on data the rules were written from, so it is a regression gate, not an accuracy figure.
23. **MCP server** `backend/app/mcp_server.py` (stdlib, stdio): `faham_check_message` and `faham_list_scam_types`; redacted text only; no send or pay tool. Documented in `docs/ARCHITECTURE.md`.

### Probes
The nine probes are in `tests/test_probes.py` (fake LHDN refund, fake Bukit Aman safe account, job scam, fake .apk, "Hi mak", Chinese police scam, Macau call script, TNB legit bill, real LHDN sample) and pass.

### Not done or partial
- **Commits are grouped, not one per item.** P0 items 1-7 are one commit, P2 frontend 10-15 one commit and P3 16-18 one commit, because the changes share files (`i18n.js`, `tools.py`, `app.js`).
- zh and ta registry steps for genuine agencies still fall back to English (BM is complete). Scam content is in all four languages.
- LLM explanation is not streamed token by token.
- Live retrieval of agency pages is not implemented; sources are saved copies with dates.
- zh and ta strings need a native-speaker review (the app shows a review notice).
- **Service worker not verified in a browser.** The built-in browser pane refuses every service-worker registration here (even for a minimal file), while `sw.js` itself is served correctly. Its rules (never `/api/`, same origin only, precache files exist) are covered by static tests, but offline start-up and installability have not been seen working. Test on Chrome or a phone over HTTPS before relying on it.
- Voice input and the WhatsApp link were checked for syntax and the page flow in the browser pane, not with a real microphone or on a phone.
- The DPO email is a placeholder.
