"""The nine probes from the upgrade request, as fixtures. Every message here is fictional.

Scam probes must be a likely scam with the right scam type, a lesson and route in the chosen language, a draft that is a
verify-and-report note (never a reply addressed to an agency) and an approval gate. Genuine probes must never be flagged.
"""
import json
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import cache
from app.main import app

client = TestClient(app)
REAL = json.loads((Path(__file__).parent / "fixtures" / "real" / "suite.json").read_text(encoding="utf-8"))
CJK, TAMIL = re.compile(r"[一-鿿]"), re.compile(r"[஀-௿]")

SCAMS = {
    "fake_lhdn_refund": ("bm", "phishing_refund",
                         "LHDN: Anda layak terima bayaran balik cukai RM 1,284. Klik http://hasil-refund.xyz/tuntut dan masukkan butiran kad serta TAC untuk terima wang dalam 24 jam."),
    "fake_bukit_aman_safe_account": ("en", "macau",
                                     "Bukit Aman CCID: you are linked to a money laundering case. Move your savings to the safe account 8001234567 today to prove you are innocent. Do not tell your family or bank."),
    "job_scam": ("en", "job",
                 "Part-time job from home! RM 300 a day for liking TikTok videos. WhatsApp 011-2345 6789 to register, RM 100 deposit needed to activate your account."),
    "fake_apk": ("bm", "apk_install",
                 "Tahniah, pakej Pos Malaysia anda sedia. Muat turun aplikasi penjejakan (pos-track.apk) dari pautan ini dan pasang untuk lihat status."),
    "hi_mak_family": ("bm", "family_impersonation",
                      "Hi mak, ni nombor baru Ali. Phone Ali rosak. Boleh tolong transfer RM800 sekarang? Nanti Ali ganti. Jangan bagitahu abah."),
    "chinese_police_scam": ("zh", "macau",
                            "武吉免登警察局：您涉嫌洗黑钱案，我们将发出逮捕令。请立刻把钱转入安全账户 8001234567 进行核实。不要告诉任何人。"),
    "macau_call_script": ("bm", "macau",
                          "Panggilan: Helo, saya Inspektor dari Bukit Aman. Nama anda dikaitkan dengan kes pengubahan wang haram. Jangan putuskan talian dan jangan beritahu sesiapa. Pindahkan wang ke akaun selamat untuk disahkan, atau waran tangkap dikeluarkan."),
}


def run(text, lang):
    cache.ANALYSES.clear()
    r = client.post("/api/analyze", json={"text": text, "language": lang})
    assert r.status_code == 200
    return r.json()


@pytest.mark.parametrize("name", SCAMS)
def test_scam_probe(name):
    lang, stype, text = SCAMS[name]
    d = run(text, lang)
    s = d["scam"]
    assert s["verdict"] == "likely_scam" and s["score"] < 60, (name, s["score"], s["verdict"])
    assert s["scam_type"] == stype, (name, s["scam_type"])
    assert d["action"]["requires_approval"] is True
    # a scam message is never answered with an agency letter template
    assert not re.match(r"(?i)\s*(kepada|to|致|பெறுநர்)\b.*(lembaga hasil|lhdn|jpj|ptptn)", d["action"]["draft"])
    assert d["route"]["online_steps"] or d["route"]["walkin_steps"]
    # lesson and route are in the language the user chose
    if lang == "zh":
        assert CJK.search(d["lesson"]["answer"]) and CJK.search(" ".join(d["route"]["walkin_steps"]))
    if lang == "ta":
        assert TAMIL.search(d["lesson"]["answer"])
    if lang == "bm":
        assert not CJK.search(d["lesson"]["answer"]) and "NSRC 997" in " ".join(d["route"]["walkin_steps"] + d["route"]["online_steps"] + [d["lesson"]["answer"]])


def test_hi_mak_tells_you_to_call_the_old_number_first():
    d = run(SCAMS["hi_mak_family"][2], "bm")
    assert d["scam"]["verify_yourself"][0].lower().startswith(("telefon orang ini", "call this person"))
    assert any(r["code"] == "family_impersonation" for r in d["scam"]["reasons"])


def test_apk_probe_names_the_install_risk():
    d = run(SCAMS["fake_apk"][2], "en")
    assert d["scam"]["scam_type"] == "apk_install" and d["scam"]["verdict"] == "likely_scam"


def test_tnb_legit_bill_is_not_flagged():
    text = ("TENAGA NASIONAL BERHAD. Bil elektrik anda untuk Oktober 2026 ialah RM 142.30. Bayar sebelum 25 November 2026 "
            "melalui myTNB di www.mytnb.com.my atau di kaunter. Rujukan akaun TNB/SAMPEL/2026/0001")
    d = run(text, "bm")
    assert d["scam"]["verdict"] == "no_signals" and d["scam"]["scam_type"] is None
    assert d["fields"]["issuer"] == "UTILITY" and d["fields"]["amount"] == "RM 142.30"  # registry key for utilities (TNB)
    assert d["fields"]["deadline"] == "25 November 2026"
    assert not any(r["kind"] == "risk" for r in d["scam"]["reasons"])


def test_real_lhdn_sample_is_not_flagged_and_is_read_correctly():
    doc = next(x for x in REAL if "HASIL DALAM NEGERI" in x["request_payload"]["text"].upper() and x["category"] == "genuine_statutory_notice")
    d = client.post("/api/analyze", json=doc["request_payload"]).json()
    assert d["scam"]["verdict"] != "likely_scam"
    assert "LHDN" in d["fields"]["issuer"].upper() or "HASIL" in d["fields"]["issuer"].upper()
    assert d["action"]["requires_approval"] is True


def test_all_nine_probes_are_present():
    assert len(SCAMS) + 2 == 9  # seven scam probes, the TNB bill and the real LHDN sample
