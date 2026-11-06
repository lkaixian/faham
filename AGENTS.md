# AGENTS.md

FAHAM: an agent that reads official Malaysian letters (LHDN, JPJ, PDRM, PTPTN, courts, councils, banks), checks for scams, explains in BM/EN/中文/தமிழ், teaches the rule behind it, routes the user, and drafts a reply for approval. Entry for the Agentic AI Challenge, Festival Idea Putrajaya, 19 Nov 2026. Research and open issues: `docs/NOTES.md`.

## Layout

- `backend/app/main.py`: FastAPI routes `/api/health`, `/api/tools`, `/api/analyze`, `/api/practice`.
- `backend/app/agent/orchestrator.py`: fixed pipeline read, verify, explain, teach, route, act, plus a `Trace`.
- `backend/app/agent/tools.py`: `@tool`-registered functions in the `TOOLS` dict (10 tools), plus the official source registry (`SOURCES`) and the office directory (`OFFICES`), both loaded from JSON.
- `backend/app/models.py`: Pydantic contracts. `llm.py`: optional Anthropic call. `config.py`: env vars.
- `backend/app/data/*.json`: `official_sources.json`, `offices.json` (demo), `practice.json`.
- `frontend/`: static HTML/CSS/JS, no build step. Falls back to a fully in-browser demo mode when the API is unreachable (`assets/js/data.js` holds the sample letters).
- `docs/`: ARCHITECTURE, AGENT_FLOW, API, PRIVACY_SAFETY, PITCH_PLAN, NOTES.

## Commands

```bash
cd backend && pip install -r requirements-dev.txt
pytest -q                                   # all tests must pass (incl. tests/test_real_documents.py, 12-document suite)
uvicorn app.main:app --reload --port 8000   # docs at /docs
python -m http.server 5500 -d frontend      # dashboard
docker compose up --build                   # web :8080, api :8000
```

CI runs `pytest -q` on Python 3.12 for every push. `pages.yml` deploys `frontend/` to GitHub Pages from `main`.

## Rules for working here

1. **Deterministic first, LLM second.** Classification, extraction and scam checks are regex/rules. The LLM only rewrites the explanation and must stay optional; the offline demo must always work.
2. **Redact before anything else.** Every tool after `privacy.redact` and every LLM call gets redacted text only. Never log or store raw letters. The API is stateless.
3. **Human approval gate.** `act.draft` never sends or pays. `requires_approval` stays `True`.
4. **Fictional data only.** Letters, names, ICs, accounts, phones and links are fake and marked SAMPEL/FIKTIF. No working links or real numbers in scam examples.
5. **Procedures come from the registry.** Do not invent agency steps. Add an issuer by adding an entry to `official_sources.json` (`keywords`, `domains`, `source_url`, steps, lesson, terms).
6. **Add a tool** with `@tool("name", "desc")` in `tools.py`, call it from `orchestrator.run()`, and log it with `tr.call(stage, name, msg)`. Add a test in `tests/test_agent.py`.
7. **Guidance, not legal advice.** Keep the disclaimer. Have a native speaker review zh/ta strings before the demo.
8. Trace step shape is `{stage, kind, tool?, message, flag}`; the frontend console renders it. Do not change it without updating `app.js`.

## Conventions

- Python 3.12 target, type hints, `from __future__ import annotations`, small pure functions.
- No new dependencies for things the stdlib covers. Optional deps (pytesseract, pillow, anthropic) stay commented in `requirements.txt`.
- Frontend: vanilla JS, no framework or bundler. UI changes go through the antislop rules (state purpose for each technique, real content or labeled placeholder, working click-through before delivery).
- Em dashes are banned in UI text and copy (antislop R-02).
- Commit trailer: `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
