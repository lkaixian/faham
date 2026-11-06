import io
import json
import urllib.request

from fastapi.testclient import TestClient

from app import config, tts
from app.main import app

client = TestClient(app)


def configured(monkeypatch):
    monkeypatch.setattr(config, "ILMU_API_KEY", "sk-test")
    monkeypatch.setattr(tts, "_calls", [])


def test_health_reports_tts(monkeypatch):
    monkeypatch.setattr(config, "ILMU_API_KEY", "")
    j = client.get("/api/health").json()
    assert j["tts_available"] is False and j["tts_languages"] == ["bm", "en", "zh"]


def test_tts_not_configured_is_503(monkeypatch):
    monkeypatch.setattr(config, "ILMU_API_KEY", "")
    assert client.post("/api/tts", json={"text": "Notis cukai", "language": "bm"}).status_code == 503


def test_tts_tamil_unsupported_and_pii_refused(monkeypatch):
    configured(monkeypatch)
    assert client.post("/api/tts", json={"text": "Notis", "language": "ta"}).status_code == 422
    assert client.post("/api/tts", json={"text": "emel ali@contoh.example", "language": "bm"}).status_code == 422
    assert client.post("/api/tts", json={"text": "x" * 3001, "language": "bm"}).status_code == 422


def test_tts_success_sends_documented_fields(monkeypatch):
    configured(monkeypatch)
    seen = {}

    def fake(req, timeout=0):
        seen["url"], seen["auth"], seen["body"] = req.full_url, req.headers["Authorization"], json.loads(req.data)
        return io.BytesIO(b"ID3audio")

    monkeypatch.setattr(urllib.request, "urlopen", fake)
    r = client.post("/api/tts", json={"text": "Bayar sebelum 15 Disember.", "language": "bm"})
    assert r.status_code == 200 and r.headers["content-type"] == "audio/mpeg" and r.content == b"ID3audio"
    assert seen["url"].endswith("/audio/speech") and seen["auth"] == "Bearer sk-test"
    assert seen["body"]["language"] == "ms" and seen["body"]["model"] == "ilmu-tts-v2.1" and seen["body"]["response_format"] == "mp3"


def test_tts_upstream_failure_is_502_and_rate_limited(monkeypatch):
    configured(monkeypatch)
    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: (_ for _ in ()).throw(OSError("down")))
    assert client.post("/api/tts", json={"text": "Notis", "language": "en"}).status_code == 502
    monkeypatch.setattr(tts, "RATE_PER_MIN", 1)
    assert client.post("/api/tts", json={"text": "Notis", "language": "en"}).status_code == 429
