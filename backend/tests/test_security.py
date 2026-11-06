from fastapi.testclient import TestClient

from app import config, llm
from app.main import app

c = TestClient(app)
TXT = "Notis LHDN: bayar cukai anda sebelum tarikh akhir."


def test_text_too_long_422():
    assert c.post("/api/analyze", json={"text": "a" * 20001}).status_code == 422


def test_postcode_digits_only():
    assert c.post("/api/analyze", json={"text": TXT, "postcode": "12ab"}).status_code == 422
    assert c.post("/api/analyze", json={"text": TXT, "postcode": "123456"}).status_code == 422


def test_null_origin_off_by_default():
    r = c.get("/api/health", headers={"Origin": "null"})
    assert "access-control-allow-origin" not in r.headers


def test_health_llm_configured_no_secret():
    j = c.get("/api/health").json()
    assert isinstance(j["llm_configured"], bool) and "key" not in str(j).lower()


def test_llm_skips_on_residual_digits(monkeypatch):
    monkeypatch.setattr(config, "LLM_PROVIDER", "anthropic")
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "x")
    assert llm.complete("ref 1234567890", "en") is None


def test_ilmu_provider_calls_chat_completions(monkeypatch):
    import io, json, urllib.request
    seen = {}

    def fake(req, timeout=0):
        seen["url"], seen["auth"] = req.full_url, req.headers["Authorization"]
        seen["body"] = json.loads(req.data)
        return io.BytesIO(b'{"choices":[{"message":{"content":" ok "}}]}')

    monkeypatch.setattr(config, "LLM_PROVIDER", "ilmu")
    monkeypatch.setattr(config, "ILMU_API_KEY", "sk-test")
    monkeypatch.setattr(urllib.request, "urlopen", fake)
    assert llm.complete("Notis cukai", "bm") == "ok"
    assert seen["url"].endswith("/chat/completions") and seen["auth"] == "Bearer sk-test"
    assert "<letter>" in seen["body"]["messages"][1]["content"]
