import base64

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
    assert {s["stage"] for s in d["trace"]} >= {"read", "verify", "explain", "teach", "route", "act"}  # plus "plan" when the agent loop is off or on


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


def test_practice_agent_agrees_with_label():
    items = client.get("/api/practice?n=99").json()
    assert len(items) >= 8
    for i in items:
        assert i["agent"]["genuine"] == (not i["is_scam"]), i["text"]
        assert i["agent"]["verdict"] in (("likely_scam", "caution") if i["is_scam"] else ("no_signals", "caution")), i["text"]
        assert set(i["agent"]) == {"genuine", "verdict", "score", "red_flags", "good_signs", "reasons", "verify_yourself"}


def test_verdict_levels_reasons_and_verify():
    ok = T.scam_check(LHDN, "LHDN")
    assert ok["verdict"] == "no_signals" and ok["genuine"]
    assert any("scammers copy this too" in g for g in ok["good_signs"])
    assert any("check the real destination" in g for g in ok["good_signs"])
    kinds = {r["kind"] for r in ok["reasons"]}
    assert kinds == {"ok", "info"} and any("email headers" in r["text"] for r in ok["reasons"])
    assert any("confirmed on the agency" in r["text"] for r in ok["reasons"])  # LHDN text mentions bayar
    assert 3 <= len(ok["verify_yourself"]) <= 4 and "https://www.hasil.gov.my" in ok["verify_yourself"][0]
    unk = T.scam_check("Hello there, please read this", "UNKNOWN")
    assert unk["verdict"] == "caution" and unk["genuine"]
    assert not any("confirmed on the agency" in r["text"] for r in unk["reasons"])
    assert "malaysia.gov.my" in unk["verify_yourself"][0]
    flagged = T.scam_check(LHDN + "\nSila sahkan akaun anda.", "LHDN")
    assert flagged["verdict"] == "caution" and flagged["score"] >= 60
    assert any(r["kind"] == "risk" for r in flagged["reasons"])
    bad = T.scam_check(SCAM, "PDRM")
    assert bad["verdict"] == "likely_scam" and not bad["genuine"]


def test_new_phishing_signals():
    flags = lambda s, i="LHDN": T.scam_check(s, i)["red_flags"]
    assert any("Looks like an official site" in f for f in flags("Log masuk hasil-gov.my.com"))
    assert any("Looks like an official site" in f for f in flags("Buka mytax-login.xyz"))
    assert any("Looks like an official site" in f for f in flags("Buka hasl.com"))
    assert not any("Looks like" in f for f in flags("Buka example.com"))
    assert not any("Looks like" in f for f in flags(LHDN))
    assert any("new or changed account" in f for f in flags("Sila bayar ke akaun baharu kami"))
    assert any("new or changed account" in f for f in flags("Our bank account has changed, use the new account"))
    assert any("'@' or an IP" in f for f in flags("Klik http://203.0.113.5/bayar"))
    assert any("'@' or an IP" in f for f in T.scam_check(T.redact("Klik https://hasil.gov.my@evil.example/x")[0], "LHDN")["red_flags"])
    assert any("verify" in f for f in flags("Please verify your account now"))
    assert any("verify" in f for f in flags("Akaun anda akan digantung"))
    assert not flags(LHDN)


def test_explain_adds_check_sentence_and_trace():
    for lang, s in T.CHECK_SENTENCE.items():
        assert T.explain("Notis LHDN", "LHDN", {}, True, lang).endswith(s)
    d = client.post("/api/analyze", json={"text": LHDN, "language": "en"}).json()
    assert d["scam"]["verdict"] == "no_signals" and d["scam"]["verify_yourself"]
    assert any(s["message"] == "verdict: NO SCAM SIGNALS FOUND (not proof, verify yourself)" for s in d["trace"])
    sc = client.post("/api/analyze", json={"text": SCAM, "language": "en"}).json()
    assert any(s["message"].startswith("verdict: LIKELY SCAM (") and s["flag"] for s in sc["trace"])
    ca = client.post("/api/analyze", json={"text": "Hello there, please read this letter", "language": "en"}).json()
    assert ca["scam"]["verdict"] == "caution" and any(s["message"] == "verdict: CAUTION" for s in ca["trace"])


PNG = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"0" * 20).decode()


def test_ocr_paths(monkeypatch):
    assert client.post("/api/analyze", json={"text": LHDN}).status_code == 200
    assert client.post("/api/analyze", json={}).status_code == 422
    assert client.post("/api/analyze", json={"text": "short"}).status_code == 422
    monkeypatch.setitem(T.TOOLS, "ocr.read", T.Tool("ocr.read", "", lambda text=None, image_bytes=None: ""))
    r = client.post("/api/analyze", json={"image_b64": PNG})
    assert r.status_code == 422 and "OCR unavailable" in r.json()["detail"]
    bad = base64.b64encode(b"GIF89a" + b"0" * 20).decode()
    assert client.post("/api/analyze", json={"image_b64": bad}).status_code == 422
    assert client.post("/api/analyze", json={"image_b64": "***"}).status_code == 422
    monkeypatch.setitem(T.TOOLS, "ocr.read", T.Tool("ocr.read", "", lambda text=None, image_bytes=None: LHDN))
    assert client.post("/api/analyze", json={"image_b64": PNG}).json()["fields"]["issuer"] == "LHDN"


def test_redact_widened():
    r = lambda s: T.redact(s)
    out, c = r("Tel 03-8888 1234 atau +60 3-8888 1234 atau 07-1234567")
    assert out.count("[PHONE]") == 3 and c["phone"] == 3
    out, c = r("Emel: ali.contoh@contoh.example")
    assert "@" not in out and c["email"] == 1
    out, c = r("Kereta WXY 1234 dan ABC1234 disaman")
    assert "WXY" not in out and "ABC1234" not in out and c["plate"] == 2
    out, c = r("Alamat:\nNo. 12, Jalan Contoh 3, Taman Fiktif\n50000 Kuala Lumpur\nSekian")
    assert "Jalan" not in out and "50000" not in out and c["address"] == 1 and "Sekian" in out
    assert r("Rumah di Jalan Contoh 3, 43000 Kajang.")[1]["address"] == 1
    out, c = r("Nama: SITI BINTI CONTOH\nDitujukan kepada Puan NUR AINA BINTI FIKTIF dan Encik LIM AH CONTOH.")
    assert "SITI" not in out and "AINA" not in out and "LIM" not in out and c["name"] == 3
    assert set(c) == {"ic", "phone", "account", "name", "email", "address", "plate", "id", "dob", "other"}


def test_redact_keeps_letter_content():
    out, c = T.redact(LHDN)
    assert "RM 1,240.00" in out and "LHDN/SAMPEL/TT2025/0001" in out and "15 Disember 2026" in out
    assert c["plate"] == 0 and c["address"] == 0
    out, c = T.redact(SCAM)
    assert "011-2345 6789" not in out and "RM 2,150.00" in out and c["plate"] == 0


def test_genuine_footer_links_are_not_scam_signs():
    """A real survey email: social footer, Google Form, WhatsApp only as a social-media name."""
    t = ("Jemputan kajian kepuasan pelanggan DOSM. Pautan: https://forms.gle/abc123xyz "
         "Portal: https://www.dosm.gov.my Facebook: https://www.facebook.com/StatsMalaysia "
         "TikTok: https://www.tiktok.com/@x YouTube: https://www.youtube.com/@x Instagram: https://www.instagram.com/x "
         "Media sosial: WhatsApp, Telegram. Soalan: perhubunganawam@dosm.gov.my")
    v = T.scam_check(t, "UNKNOWN", "en")
    assert v["verdict"] == "caution" and not v["red_flags"]
    assert {r["code"] for r in v["reasons"]} >= {"form_link", "social_links"}
    assert T.scam_check("Hubungi kami di WhatsApp 012 untuk sahkan akaun", "UNKNOWN", "en")["red_flags"]


def test_social_links_checked_against_registry(monkeypatch):
    monkeypatch.setitem(T.SOURCES["PTPTN"], "social", ["facebook.com/ptptn.official"])
    ok = T.scam_check("PTPTN: https://www.facebook.com/PTPTN.Official", "PTPTN", "en")
    fake = T.scam_check("PTPTN: https://facebook.com/ptptn.bantuan", "PTPTN", "en")
    assert any(r["code"] == "official_social" for r in ok["reasons"]) and not ok["red_flags"]
    assert any(r["code"] == "social_mismatch" for r in fake["reasons"]) and fake["verdict"] != "no_signals"


def test_reasons_carry_evidence_snippets():
    t = "Bayar dalam 24 jam ke https://hasil-gov.my.com/bayar. Ruj: LHDN/SAMPEL/TT2025/0001 Portal https://www.hasil.gov.my"
    v = T.scam_check(t, "LHDN", "en")
    ev = {r["code"]: r["evidence"] for r in v["reasons"]}
    assert ev["urgency"] == ["dalam 24 jam"] and ev["unofficial_domain"] == ["https://hasil-gov.my.com/bayar"]
    assert ev["ref_format"] == ["LHDN/SAMPEL/TT2025/0001"] and ev["official_domain"] == ["https://www.hasil.gov.my"]
    assert all(s in t for r in v["reasons"] for s in r["evidence"])
