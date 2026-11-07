# AGENTS.md

Tulen (formerly FAHAM; the repo, env vars and URL keep that name): a scam and authenticity agent for official Malaysian letters and messages (LHDN, JPJ, PDRM, PTPTN, courts, councils, banks). It investigates whether the message is real, shows its evidence, explains in BM/EN/中文/தமிழ், teaches the rule behind it, routes the user, and drafts a reply for approval. Entry for the Agentic AI Challenge, Festival Idea Putrajaya, 19 Nov 2026. Research and open issues: `docs/NOTES.md`.

## Layout

- `backend/app/main.py`: FastAPI routes `/api/health`, `/api/tools`, `/api/analyze`, `/api/practice`.
- `backend/app/agent/orchestrator.py`: the pipeline read, verify, (agent loop), explain, teach, route, act, plus a `Trace`. `loop.py`: the agent (goal, plan, tools, observations, finish) and its guard rails. `backend/evals/run_suite.py` measures it on the 12 real documents.
- `backend/app/agent/tools.py`: `@tool`-registered functions in the `TOOLS` dict (12 tools), plus the official source registry (`SOURCES`) and the office directory (`OFFICES`), both loaded from JSON.
- `backend/app/models.py`: Pydantic contracts. `llm.py`: optional Anthropic call. `config.py`: env vars.
- `backend/app/data/*.json`: `official_sources.json`, `official_directory.json` (domains only, see `docs/DIRECTORY.md`), `offices.json` (demo), `practice.json`.
- `frontend/`: static HTML/CSS/JS, no build step. Falls back to a fully in-browser demo mode when the API is unreachable (`assets/js/data.js` holds the sample letters).
- `backend/app/agent/scam_content.py`: scam types and their lesson, route and draft in 4 languages. `cache.py`, `limiter.py`, `counter.py`, `mcp_server.py`. `frontend/assets/js/safety.js`: offline safety tools; `frontend/sw.js`: service worker.
- `backend/app/filecheck.py`, `apk.py`, `office.py`, `payload.py`, `data/known_apps.json`: static file-safety checks (ZIP, RAR, APK, scripts, programs, Office macros). Tulen is not an antivirus: never run, extract to disk or store a file; every decompression is bounded and charged to one `Budget` per request; weak signals can never alone give likely_scam (see FILE_WEAK/FILE_STRONG/FILE_INFO in `tools.py`). `sandbox.py` + `inspect_worker.py` run ALL untrusted parsing (inspection, letter extraction, OCR) in a limited child process with no secrets; rarfile only lists RAR and never runs an outside tool.
- `backend/tests/eval/`: labelled dataset and the recall / false-positive gate (see `docs/EVAL.md`).
- `docs/`: ARCHITECTURE, AGENT_FLOW, API, PRIVACY_SAFETY, DEPLOY, EVAL, PITCH_PLAN, NOTES.

## Commands

```bash
cd backend && pip install -r requirements-dev.txt
pytest -q                                   # all tests must pass (incl. tests/test_real_documents.py, 12-document suite)
uvicorn app.main:app --reload --port 8000   # docs at /docs
python -m http.server 5500 -d frontend      # dashboard
docker compose up --build                   # web :8080, api :8000
```

CI runs `pytest -q` and `python -m tests.eval.run --min-recall 0.9 --max-fpr 0.1` on Python 3.12 for every push. `pages.yml` deploys `frontend/` to GitHub Pages from `main`.

After changing anything under `frontend/assets`, run `python scripts/bust_cache.py` (it fingerprints the CSS and JS links so Cloudflare never serves an old copy next to a new page). `pytest` fails if you forget.

## Rules for working here

1. **The agent decides, the rules are the floor.** `agent/loop.py` runs an LLM in rounds of think, act, observe with a goal, a revisable plan and eight tools (some reach outside Tulen: an agency's real web page, a domain's registration date). The scam rules are one of its tools and always re-run last as a floor. The model can raise concern, never lower it; every signal needs a quote that really appears in the letter, and the words shown to the user are ours. It must stay optional: with no model or no usable answer the plain rule pipeline runs, so the offline demo always works. Only masked text reaches any model.
2. **Redact before anything else.** Every tool after `privacy.redact` and every LLM call gets redacted text only. Never log or store raw letters. The only server state is the redacted-result cache (`cache.py`, memory, 1 h) and the hash-only counter (`counter.py`). Both are documented in `docs/PRIVACY_SAFETY.md`; do not add more.
3. **Human approval gate.** `act.draft` never sends or pays. `requires_approval` stays `True`.
4. **Fictional data only.** Letters, names, ICs, accounts, phones and links are fake and marked SAMPEL/FIKTIF. No working links or real numbers in scam examples.
5. **Procedures come from the registry.** Do not invent agency steps. Add an issuer by adding an entry to `official_sources.json` (`keywords`, `domains`, `source_url`, steps, lesson, terms).
6. **Add a tool** with `@tool("name", "desc")` in `tools.py`, call it from `orchestrator.run()`, and log it with `tr.call(stage, name, msg)`. Add a test in `tests/test_agent.py`.
7. **Guidance, not legal advice.** Keep the disclaimer. Have a native speaker review zh/ta strings before the demo.
8. **Hostile bytes are parsed only in the sandbox child.** Web routes and channels call `ingest.extract_safe`, never `ingest.extract`; OCR goes through the `ocr.read` tool, never `pytesseract` directly; file-signal tiers live in `filecheck.py` only. Outbound fetches by the agent go through `loop._SafeHandler` (public addresses only). `tests/test_hardening.py` pins all of this.
   Files that are not letters take `orchestrator.run_file`, never the agent loop: no model sees a file name.
9. Trace step shape is `{stage, kind, tool?, message, flag}`; the frontend console renders it. Do not change it without updating `app.js`.

## Conventions

- Python 3.12 target, type hints, `from __future__ import annotations`, small pure functions.
- No new dependencies for things the stdlib covers. Optional deps (pytesseract, pillow, anthropic) stay commented in `requirements.txt`.
- Frontend: vanilla JS, no framework or bundler. UI changes go through the antislop rules (state purpose for each technique, real content or labeled placeholder, working click-through before delivery).
- Em dashes are banned in UI text and copy (antislop R-02).
- Commit trailer: `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
