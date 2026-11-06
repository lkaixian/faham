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
