from fastapi.testclient import TestClient

from app.agent import tools as T
from app.main import app

client = TestClient(app)

LHDN = """NOTIS TAKSIRAN CUKAI PENDAPATAN — TAHUN TAKSIRAN 2025
Daripada: Lembaga Hasil Dalam Negeri Malaysia (LHDN) hasil.gov.my
Rujukan: LHDN/SAMPEL/TT2025/0001
Kepada: AHMAD BIN CONTOH, No. KP 900101-01-1234
Baki cukai kena dibayar: RM 1,240.00 sebelum 15 Disember 2026 melalui ByrHASIL di MyTax."""

SCAM = """NOTIS SEGERA PDRM. Bayar RM 2,150.00 dalam masa 24 JAM ke akaun Maybank 1234-5678-9012
atas nama Syarikat Penyelesaian Saman atau waran tangkap dikeluarkan. Klik bit.ly/saman-pdrm-bayar.
WhatsApp 011-2345 6789. Jangan beritahu sesiapa."""


def test_redact_masks_ic_phone_account_and_name():
    out, counts = T.redact(LHDN + "\nTel 012-345 6789\nAkaun 1234-5678-9012")
    assert "900101-01-1234" not in out and "[IC]" in out
    assert "012-345 6789" not in out
    assert "1234-5678-9012" not in out
    assert "AHMAD" not in out
    assert counts["ic"] == 1 and counts["name"] == 1


def test_classify_issuer():
    assert T.classify_issuer(LHDN)[0] == "LHDN"
    assert T.classify_issuer("Notis saman JPJ kamera AwAS had laju")[0] == "JPJ"


def test_extract_fields():
    f = T.extract_fields(LHDN)
    assert f["amount"] == "RM 1,240.00"
    assert f["deadline"].lower() == "15 disember 2026"
    assert f["reference"] == "LHDN/SAMPEL/TT2025/0001"


def test_scam_check_flags_scam_and_passes_genuine():
    bad = T.scam_check(SCAM, "PDRM")
    good = T.scam_check(LHDN, "LHDN")
    assert not bad["genuine"] and len(bad["red_flags"]) >= 4
    assert good["genuine"] and good["score"] > 80


def test_api_analyze_genuine():
    r = client.post("/api/analyze", json={"text": LHDN, "language": "en"})
    assert r.status_code == 200
    d = r.json()
    assert d["fields"]["issuer"] == "LHDN"
    assert d["scam"]["genuine"] is True
    assert d["action"]["requires_approval"] is True
    assert "900101" not in d["redacted_text"]
    assert {s["stage"] for s in d["trace"]} == {"read", "verify", "explain", "teach", "route", "act"}


def test_api_analyze_scam_switches_plan():
    d = client.post("/api/analyze", json={"text": SCAM, "language": "bm"}).json()
    assert d["scam"]["genuine"] is False
    assert any(s["flag"] for s in d["trace"])
    assert "SCAM" in d["explanation"]
    assert "NSRC 997" in d["lesson"]["terms"]


def test_health_and_practice():
    assert client.get("/api/health").json()["status"] == "ok"
    items = client.get("/api/practice?n=4").json()
    assert len(items) == 4 and all("is_scam" in i for i in items)


def test_scam_check_no_false_positives():
    letter = LHDN + "\nHubungi talian bantuan WhatsApp kami. Bayaran atas nama anda sendiri. Maklumat dilindungi. Hospital dan potensi."
    r = T.scam_check(letter, "LHDN")
    assert r["genuine"] and not any("OTP" in f or "secret" in f for f in r["red_flags"])
    assert not any("OTP" in f for f in T.scam_check("Sila hubungi kotak potongan", "LHDN")["red_flags"])
    assert any("secret" in f for f in T.scam_check("Jangan beritahu sesiapa", "PDRM")["red_flags"])
    assert any("OTP" in f for f in T.scam_check("Beri OTP anda", "PDRM")["red_flags"])


def test_lookalike_my_domain_and_unknown_issuer():
    r = T.scam_check("Bayar di hasil-bayar.com.my sekarang", "LHDN")
    assert any("hasil-bayar.com.my" in f for f in r["red_flags"])
    assert not any("Content matches" in g for g in T.scam_check("Hello there", "UNKNOWN")["good_signs"])


def test_deadline_keeps_real_date_over_24_jam():
    f = T.extract_fields("Bayar dalam 24 jam sebelum 15 Disember 2026. Surat bertarikh 1 Januari 2026.")
    assert f["deadline"].lower() == "15 disember 2026"
    assert "pressure" in T.extract_fields("Bayar dalam 24 jam")["deadline"]


def test_route_is_honest_and_decision_traced():
    d = client.post("/api/analyze", json={"text": LHDN, "language": "en"}).json()
    assert d["route"]["confidence"] == "Medium" and "cached" in d["route"]["retrieved_at"]
    assert d["route"]["retrieved_at"].startswith("2026-11-06")
    route = [s for s in d["trace"] if s["stage"] == "route"]
    assert "online first" in route[0]["message"] and route[1]["tool"] == "gov.retrieve"
    assert "cached registry" in route[1]["message"]
    s = client.post("/api/analyze", json={"text": SCAM, "language": "en"}).json()
    route = [x for x in s["trace"] if x["stage"] == "route"]
    assert "walk-in" in route[0]["message"] and route[1]["tool"] == "office.locate"
