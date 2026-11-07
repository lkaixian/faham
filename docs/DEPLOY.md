# Deploying FAHAM

Last updated: 7 November 2026.

## Pieces

| Piece | What it is | Where it runs |
|---|---|---|
| `frontend/` | Static files, no build step | nginx (`frontend/nginx.conf`), GitHub Pages (demo mode), or any static host |
| `backend/` | FastAPI app, `uvicorn app.main:app` | Docker image in `backend/Dockerfile` |

`docker compose up --build` is the **development** setup: the web container uses `frontend/nginx.dev.conf`, whose
Content-Security-Policy allows the API on `localhost:8000`. Production uses `frontend/nginx.conf` instead.

## Production Content-Security-Policy (item 21)

`frontend/nginx.conf` sets `connect-src 'self'`. There is no `localhost:8000` or `127.0.0.1:8000` in it.
The browser reaches the API on the same origin, and nginx proxies `/api/` to the backend (`location /api/`, SSE buffering off).
`assets/js/config.js` already uses a relative API base (`""`) on any host that is not `localhost`/`127.0.0.1`.

If you host the API on a different origin, add exactly that origin to `connect-src` and to `FAHAM_ALLOWED_ORIGINS`. Do not add localhost.

## Backend environment

| Variable | Default | Meaning |
|---|---|---|
| `FAHAM_ALLOWED_ORIGINS` | none | CORS origins, comma separated. Not needed when the API is same-origin |
| `FAHAM_LLM_PROVIDER` | `none` | `ilmu`, `anthropic`, or a comma list. `none` = rules and templates only |
| `FAHAM_MAX_CONCURRENT` | `4` | Analyses running at once. Others wait and get "you are number N" events |
| `FAHAM_QUEUE_PATIENCE` | `60` | Seconds a request may wait before 503 + `Retry-After` |
| `FAHAM_LLM_RETRIES`, `FAHAM_LLM_BACKOFF` | `3`, `0.4` (seconds, doubles each retry) | Retry and exponential backoff for transient LLM errors |
| `FAHAM_COUNTER_DB` | `backend/var/counters.sqlite3` | Hash-only "others checked" counter. Put it on a persistent volume if you want it to survive restarts |

## Cloudflare: turn these two things off

If the site is behind Cloudflare, check the dashboard for these. They are dashboard settings, not code, so nothing in
this repository can switch them off, and this repository cannot tell whether they are on.

1. **Web Analytics (the JavaScript beacon).** Cloudflare can inject `static.cloudflareinsights.com/beacon.min.js` into every page.
   FAHAM's privacy notice says there are no analytics beacons and no tracking cookies. Switch it off under
   *Analytics & Logs, Web Analytics* (delete the site, or turn off automatic setup). The CSP would block the script anyway
   and fill the console with errors, but do not rely on that. Test: open the site, view source, search for `cloudflareinsights`.
   `backend/tests/test_p3.py` checks that this repository's HTML contains no beacon, but injection happens at the edge, so check the live page.
2. **Bot Fight Mode.** It can show a JavaScript challenge to real visitors, including older people on slow phones or
   screen readers, and it can break `fetch`, the server-sent-events stream and the service worker for them.
   Switch it off under *Security, Bots*. Use a rate-limit rule on `/api/analyze*` instead if abuse is a worry.

Also in Cloudflare: do not cache `/api/*` (Cache Rule: bypass), and keep "Always Use HTTPS" on, because the service worker and
the microphone button only work on HTTPS (or localhost).

## Before launch checklist

- [ ] Replace the DPO placeholder (`pv_1` in `frontend/assets/js/i18n.js`, all four languages) with a real mailbox.
- [ ] Set the real site URL in the `og:*` / `twitter:*` tags in `frontend/index.html` (they currently use `https://lkaixian.github.io/faham/`).
- [ ] Confirm `foot_src` dates and the registry `retrieved_at` dates after checking each official source again.
- [ ] Native-speaker review of zh and ta strings (the page shows a review notice for them).
- [ ] Confirm the two Cloudflare settings above.
- [ ] `pytest -q` and `python -m tests.eval.run` pass.

## PWA

`manifest.webmanifest` and `sw.js` are served from the site root. The service worker caches only same-origin shell files and
never `/api/` or other origins. After a deploy that changes shell files, bump `VERSION` in `sw.js`.
