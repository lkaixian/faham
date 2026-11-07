"""P1: SSE stream, queue, burst of concurrent requests, LLM retry/backoff and rules-only fallback."""
import json
import threading
import time
import urllib.error

from fastapi.testclient import TestClient

from app import cache, config, limiter, llm
from app.agent import tools as T
from app.main import app

client = TestClient(app)
SCAM = "NOTIS PDRM: Bayar RM 2,150.00 dalam masa 24 JAM ke akaun Maybank 1234 5678 9012 atau waran tangkap. Jangan beritahu sesiapa."


def parse_sse(body: str):
    out = []
    for block in body.strip().split("\n\n"):
        ev, data = block.split("\n", 1)
        out.append((ev.removeprefix("event: "), json.loads(data.removeprefix("data: "))))
    return out


def test_stream_order_and_fast_verdict():
    cache.ANALYSES.clear()
    t0 = time.monotonic()
    r = client.post("/api/analyze/stream", json={"text": SCAM, "language": "en"})
    evs = parse_sse(r.text)
    assert [n for n, _ in evs] == ["verdict", "explanation", "result"]
    assert evs[0][1]["verdict"] == "likely_scam" and evs[0][1]["scam_type"] == "macau"
    assert evs[2][1]["scam"]["verdict"] == evs[0][1]["verdict"]
    assert time.monotonic() - t0 < 2
    assert r.headers["content-type"].startswith("text/event-stream")


def test_stream_error_when_nothing_to_read():
    r = client.post("/api/analyze/stream", json={"text": "", "language": "en"})
    assert r.status_code == 422  # validated before the stream starts


def test_limiter_fifo_and_positions():
    lim = limiter.Limiter(1)
    a, b, c = lim.enter(), lim.enter(), lim.enter()
    assert lim.acquire(a, 0.1)
    assert lim.position(b) == 1 and lim.position(c) == 2
    assert not lim.acquire(c, 0.05)  # c is not next
    lim.release()
    assert lim.acquire(b, 0.1) and lim.position(c) == 1
    lim.release()
    assert lim.acquire(c, 0.1)
    lim.release()
    assert lim.active == 0 and lim.waiting() == 0


def test_burst_of_eight_never_502(monkeypatch):
    monkeypatch.setattr(limiter, "LIMITER", limiter.Limiter(2))
    codes = []

    def hit(i):
        codes.append(client.post("/api/analyze", json={"text": SCAM + f" ref{i}", "language": "en"}).status_code)

    ts = [threading.Thread(target=hit, args=(i,)) for i in range(8)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert codes == [200] * 8


def test_busy_returns_503_not_502(monkeypatch):
    lim = limiter.Limiter(1)
    monkeypatch.setattr(limiter, "LIMITER", lim)
    monkeypatch.setattr(config, "QUEUE_PATIENCE", 0.1)
    held = lim.enter()
    assert lim.acquire(held, 0.1)
    r = client.post("/api/analyze", json={"text": "Notis LHDN RM 5", "language": "en"})
    assert r.status_code == 503 and r.headers["retry-after"]
    lim.release()


def test_queue_event_when_waiting(monkeypatch):
    lim = limiter.Limiter(1)
    monkeypatch.setattr(limiter, "LIMITER", lim)
    held = lim.enter()
    assert lim.acquire(held, 0.1)
    threading.Timer(0.3, lim.release).start()
    r = client.post("/api/analyze/stream", json={"text": SCAM + " q", "language": "en"})
    evs = parse_sse(r.text)
    assert evs[0][0] == "queue" and evs[0][1]["position"] == 1 and evs[-1][0] == "result"


def test_llm_retry_with_backoff(monkeypatch):
    calls = []

    def flaky(system, user):
        calls.append(1)
        if len(calls) < 3:
            raise urllib.error.HTTPError("u", 503, "x", {}, None)
        return "OK EXPLANATION"

    monkeypatch.setattr(config, "LLM_BACKOFF", 0.001)
    monkeypatch.setitem(llm.PROVIDERS, "ilmu", flaky)
    monkeypatch.setattr(config, "llm_chain", lambda: ["ilmu"])
    assert llm.complete("Notis LHDN", "en") == "OK EXPLANATION" and len(calls) == 3


def test_llm_auth_error_not_retried(monkeypatch):
    calls = []

    def bad(system, user):
        calls.append(1)
        raise urllib.error.HTTPError("u", 401, "x", {}, None)

    monkeypatch.setitem(llm.PROVIDERS, "ilmu", bad)
    monkeypatch.setattr(config, "llm_chain", lambda: ["ilmu"])
    assert llm.complete("Notis LHDN", "en") is None and len(calls) == 1


def test_rules_only_fallback_when_llm_down(monkeypatch):
    def down(system, user):
        raise TimeoutError()

    monkeypatch.setattr(config, "LLM_BACKOFF", 0.001)
    monkeypatch.setitem(llm.PROVIDERS, "ilmu", down)
    monkeypatch.setattr(config, "llm_chain", lambda: ["ilmu"])
    cache.ANALYSES.clear()
    r = client.post("/api/analyze", json={"text": "NOTIS LHDN taksiran RM 5 sebelum 1 Disember 2026 di mytax.hasil.gov.my", "language": "en"})
    assert r.status_code == 200
    j = r.json()
    assert j["scam"]["verdict"] == "no_signals" and "Lembaga Hasil" in j["explanation"]


def test_memo_runs_identical_calls_once():
    from app.agent.orchestrator import _Memo
    m, n = _Memo(), []
    T.TOOLS["_t"] = T.Tool("_t", "", lambda *a: n.append(a) or "x")
    try:
        m.call("_t", 1)
        m.call("_t", 1)
        m.call("_t", 2)
    finally:
        del T.TOOLS["_t"]
    assert len(n) == 2 and m.skipped == 1
