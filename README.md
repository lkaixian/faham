# FAHAM: Agentic AI letter companion

> **Faham surat. Faham langkah. Faham hak anda.**
> Every scary letter becomes a 60-second lesson, so people need help less each time.

FAHAM is the UTHM team's entry for the **Agentic AI Challenge** at **Festival Idea Putrajaya 2026** (19 Nov 2026, theme: *Edutainment & Innovation*). It helps people who struggle with official letters and messages from LHDN, JPJ, PDRM, PTPTN, courts, councils and banks, and it protects them from scams that copy those agencies.

Paste a message, upload a file, or pick a practice example. For each one the agent:

1. **Reads** it: text extraction (PDF, Word, text, Markdown, email, image OCR), personal-detail masking, issuer and field detection
2. **Checks** it for scam signs: official-domain check, red-flag rules and email-header checks. It reports *why* it reached a result and never says "genuine", because look-alike scams can copy every visible detail
3. **Explains** it in short steps in BM, English, 中文 or தமிழ், read aloud by default
4. **Teaches** the rule behind it ("Kenapa saya dapat surat ini?") and grows a personal *Kamus Surat* dictionary
5. **Routes** the user online or walk-in, with steps taken from an official-source registry
6. **Acts** by drafting a reply and a reminder. The user approves; nothing is sent or paid automatically

Also included: **Spot the scam** practice, **Family** mode, and **Connect** (website embed, Messenger and email forwarding).

Safety tools: **I already paid** (works offline, 4 languages), **Someone just called me** (4 questions), a **Semak Mule** shortcut (shows the account, phone and company found in the message and opens the police portal in a new tab; FAHAM never calls it), a privacy-safe **"others checked"** count, **voice input**, and a **WhatsApp warning** for family. The app is installable (PWA) and live results stream in, rules verdict first.

## What the verdict means

| Verdict | Meaning |
|---|---|
| `likely_scam` | Strong scam signs found. Do not pay, click or reply |
| `caution` | Mixed or unknown issuer. Verify before acting |
| `no_signals` | Known issuer and no red flags. **Still verify yourself**: FAHAM cannot see who really sent it |

Every result lists its reasons (risk, good sign, note), and the message sits beside the result with the matching parts highlighted (the original PDF or image has its own tab) and **steps to verify on your own**, independent of the letter. Social media and form links are shown as notes. If an agency has official accounts in the registry (`social` in `official_sources.json`), a different account claiming to be that agency is a red flag.

## Architecture

```mermaid
flowchart LR
  U[User] --> FE["Web app<br/>static HTML/JS"]
  CH["Messenger / email / embed"] --> API
  FE -- "text or file" --> API["FastAPI<br/>/api/analyze, /api/analyze-file"]
  FE -. "API down" .-> DEMO["In-browser demo mode"]
  API --> ING["Ingest<br/>PDF, DOCX, TXT, MD, EML, image"]
  ING --> O["Orchestrator<br/>read, verify, explain, teach, route, act"]
  O --> T["10 tools<br/>rules and regex"]
  T --> K[("Source registry<br/>and offices JSON")]
  O -. "masked text only, optional" .-> L[("LLM: ILMU or Anthropic")]
  FE -- "masked result text" --> TTS["/api/tts<br/>ILMU voice"]
  O --> G{"Verdict"}
  G -- "likely_scam" --> P["Protect and report"]
  G -- "caution / no_signals" --> H["Help comply"]
  H --> A["Draft needs user approval"]
  P --> A
```

- **Deterministic first, LLM second.** Classification, extraction and scam checks are testable rules. The LLM only rewrites the explanation and is optional, so the demo works offline.
- **Mask before anything else.** IC, phone, account, email, address, plate, names and long numbers are masked before any LLM or voice call. This is regex-based, best effort. The API is stateless and stores no letters.
- **The plan changes on evidence.** A scam verdict switches the agent from "help comply" to "protect and report".
- **Human in the loop.** Every action is a draft with `requires_approval: true`.

More detail: [Architecture](docs/ARCHITECTURE.md) · [Agent flow](docs/AGENT_FLOW.md) · [API](docs/API.md) · [Integrations](docs/INTEGRATIONS.md) · [Privacy and safety](docs/PRIVACY_SAFETY.md) · [Research](docs/RESEARCH.md) · [Notes](docs/NOTES.md)

## Repository layout

```
frontend/   static web app, no build step (config.js sets API_BASE); embed.html for websites
backend/
  app/main.py            routes: /api/health /api/tools /api/analyze /api/analyze-file /api/practice /api/tts
  app/agent/             orchestrator.py, tools.py (tool registry), scam_content.py (scam types), i18n.py (verdict text, 4 languages)
  app/cache.py limiter.py counter.py   result cache, fair queue, hash-only counter
  app/mcp_server.py      optional MCP server (stdio)
  app/ingest.py          file reading: PDF, DOCX, TXT, MD, EML, images
  app/channels.py        Messenger webhook and email forwarding
  app/llm.py, tts.py     ILMU and Anthropic text, ILMU read-aloud
  app/data/              official_sources.json, offices.json (demo), practice.json
  tests/                 pytest; tests/eval/ holds the scam-detection eval (88 messages, 4 languages)
docs/       design notes and research
```

## Setup

Requirements: Python 3.12 or newer. Docker is optional. Node is not needed.

### 1. Web app only (demo mode)
```bash
python -m http.server 5500 -d frontend
# open http://localhost:5500
```
With no API running, the app shows **Demo mode** and the agent runs in the browser.

### 2. Web app and API
```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 8000    # docs at http://localhost:8000/docs
```
In a second terminal serve the frontend on port 5500 as above. Opening `frontend/index.html` straight from disk needs `FAHAM_ALLOW_NULL_ORIGIN=1` in the API's environment.

### 3. Docker
```bash
cp backend/.env.example backend/.env     # add your own keys
docker compose up -d --build
# web http://localhost:8080    API http://localhost:8000/docs
```
If port 8080 is busy, put `WEB_PORT=8081` in a root `.env` file. The API image runs as a non-root user with a healthcheck and includes Tesseract for OCR. nginx adds security headers (`frontend/nginx.conf`).

The code is baked into the API image, so after changing backend code run `docker compose up -d --build`; a restart is not enough.

### Tests and eval
```bash
cd backend && pytest -q
python -m tests.eval.run --min-recall 0.9 --max-fpr 0.1   # precision, recall, false-positive rate, latency
python -m app.mcp_server                                  # optional MCP server on stdio
```
The eval gate fails CI if scam recall is below 0.9 or the legit false-positive rate is above 0.1. Read [docs/EVAL.md](docs/EVAL.md) before quoting a number: it is a small synthetic set.

## Configuration
Copy `backend/.env.example` to `backend/.env`. Never commit it.

| Variable | Default | Purpose |
|---|---|---|
| `FAHAM_ALLOWED_ORIGINS` | localhost :5500 and :8080 | Origins allowed by CORS. Add your site when hosting |
| `FAHAM_ALLOW_NULL_ORIGIN` | `0` | Set `1` only to call the API from a `file://` page |
| `FAHAM_LLM_PROVIDER` | `none` | One or more of `ilmu`, `anthropic`, tried in order (for example `ilmu,anthropic`). A provider without a key is skipped |
| `ILMU_API_KEY` / `ILMU_BASE_URL` | empty / `https://api.ilmu.ai/v1` | Needed for ILMU text and voice |
| `ANTHROPIC_API_KEY` | empty | Needed when the provider is `anthropic` |
| `FAHAM_LLM_MODEL_ILMU` / `FAHAM_LLM_MODEL_ANTHROPIC` | `ilmu-mini-v3.3` / `claude-sonnet-5-5` | Model per provider. Check ILMU `GET /v1/models` for current names |
| `FAHAM_MAX_CONCURRENT` / `FAHAM_QUEUE_PATIENCE` | `4` / `60` | Analyses at once; seconds a request may wait before 503 |
| `FAHAM_LLM_RETRIES` / `FAHAM_LLM_BACKOFF` | `3` / `0.4` (seconds, doubles each retry) | Retries with exponential backoff for LLM errors, then the rules-only answer |
| `FAHAM_COUNTER_DB` | `backend/var/counters.sqlite3` | Hash-only "others checked" counter |
| `FAHAM_TTS_MODEL` / `FAHAM_TTS_VOICE` | `ilmu-tts-v2.1` / `voice_1` | Read-aloud for BM, EN and 中文. Tamil uses the browser voice. About RM 0.08 per 1,000 characters |

Messenger and email forwarding have their own variables and stay off until set. See [docs/INTEGRATIONS.md](docs/INTEGRATIONS.md).

Only **masked** text is sent to a model or the voice service, and the call is skipped if personal details remain. Uploads are limited to 25 MB and are read in memory, not stored.

## Adding an agency
Add an entry to `backend/app/data/official_sources.json`: `keywords`, `domains`, `source_url`, steps, lesson, terms, and optionally `social` (the agency's official accounts, copied from its own website, for example `"facebook.com/handle"`). Steps must come from the agency's own site.

## Deploying
**GitHub Pages:** in *Settings → Pages* choose *GitHub Actions*. `pages.yml` publishes `frontend/` on every push to `main` in demo mode. To use a hosted API, set `API_BASE` in `frontend/assets/js/config.js`, add the site origin to `FAHAM_ALLOWED_ORIGINS`, and update `connect-src` in `frontend/nginx.conf` if you use it. Production nginx (`nginx.conf`) allows only the same origin; `docker compose` uses `nginx.dev.conf` for local development. Cloudflare Web Analytics and Bot Fight Mode must be off: see [docs/DEPLOY.md](docs/DEPLOY.md).

## Important
- All sample letters, names, IC numbers and accounts here are **fictional** (marked SAMPEL · FIKTIF). Never commit real people's letters.
- FAHAM gives **guidance, not legal advice**. Steps come from a cached official-source registry; every source is shown with its last-checked date and flagged as sample data, and office data is demo data.
- Not yet tested live: Messenger and email forwarding against real Meta and mail servers, and OCR on scanned documents.
- Chinese and Tamil text needs native-speaker review, and the Terms and Code of Conduct need UTHM review, before the demo.
- Known gaps and next steps are tracked in [docs/NOTES.md](docs/NOTES.md).

## Team
UTHM: Yb, Kevinraj, Muhammad Aqil, Larm Kai Xian. Advisor: Dr. Ramhuzaini bin Abd Rahman.

## License
MIT. See [LICENSE](LICENSE).
