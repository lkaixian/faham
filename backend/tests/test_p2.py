"""P2 backend: Semak Mule entities, privacy-safe counter, no raw text persisted."""
import sqlite3

from fastapi.testclient import TestClient

from app import cache, counter
from app.agent import tools as T
from app.main import app

client = TestClient(app)
SCAM = ("NOTIS SEGERA PDRM. Bayar RM 2,150.00 dalam masa 24 JAM ke akaun Maybank 1234-5678-9012 atas nama Syarikat Penyelesaian Sdn Bhd "
        "atau waran tangkap. WhatsApp 011-2345 6789. Jangan beritahu sesiapa. No. KP 900101-01-1234")


def test_entities_found_and_ic_excluded():
    e = T.extract_entities(SCAM)
    assert "1234-5678-9012" in e["accounts"]
    assert "011-2345 6789" in e["phones"]
    assert any("Sdn Bhd" in c for c in e["companies"])
    assert not any("900101" in a for a in e["accounts"])
    assert "011-2345 6789" not in " ".join(e["accounts"])


def test_entities_in_response_only_when_not_clear():
    r = client.post("/api/analyze", json={"text": SCAM, "language": "en"}).json()
    assert r["entities"]["accounts"] and r["scam"]["verdict"] == "likely_scam"
    ok = client.post("/api/analyze", json={"text": "NOTIS LHDN taksiran RM 5 sebelum 1 Disember 2026 di mytax.hasil.gov.my", "language": "en"}).json()
    assert ok["scam"]["verdict"] == "no_signals" and ok["entities"] is None


def test_entities_not_in_cache_or_counter():
    client.post("/api/analyze", json={"text": SCAM, "language": "en"})
    blob = repr(list(cache.ANALYSES._d.values())) + repr(counter.COUNTER.rows())
    assert "1234-5678-9012" not in blob and "011-2345 6789" not in blob


def test_others_checked_counts_similar_messages():
    a = client.post("/api/analyze", json={"text": SCAM, "language": "en"}).json()
    assert a["others_checked"] == 0
    # same scam, different amount and phone: still "similar"
    b = client.post("/api/analyze", json={"text": SCAM.replace("2,150.00", "9,999.00").replace("011-2345 6789", "012-9999 8888"), "language": "en"}).json()
    assert b["others_checked"] == 1
    c = client.post("/api/analyze", json={"text": "Hello this is a totally different note about lunch plans tomorrow", "language": "en"}).json()
    assert c["others_checked"] == 0


def test_counter_stores_only_hash_count_timestamps(tmp_path):
    db = tmp_path / "c.sqlite3"
    c = counter.Counter(str(db))
    c.hit("Secret message about RM 100 to account [ACCOUNT]")
    c.hit("Secret message about RM 999 to account [ACCOUNT]")
    raw = sqlite3.connect(db)
    cols = [r[1] for r in raw.execute("PRAGMA table_info(seen)")]
    assert cols == ["fp", "n", "first_ts", "last_ts"]
    ((fp, n, _t1, _t2),) = raw.execute("SELECT * FROM seen").fetchall()
    assert len(fp) == 64 and n == 2
    raw.close()
    assert b"Secret" not in db.read_bytes() and b"message" not in db.read_bytes()


def test_counter_retention_purges_old_rows(tmp_path):
    db = tmp_path / "c.sqlite3"
    c = counter.Counter(str(db))
    c.hit("old message")
    raw = sqlite3.connect(db)
    raw.execute("UPDATE seen SET last_ts = 1")
    raw.commit()
    raw.close()
    assert counter.Counter(str(db)).rows() == []


def test_sample_requests_are_not_counted():
    r = client.post("/api/analyze", json={"text": SCAM, "language": "en", "sample_id": "x"}).json()
    assert r["others_checked"] == 0 and counter.COUNTER.rows() == []
