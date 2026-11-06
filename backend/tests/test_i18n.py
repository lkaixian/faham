import re

import pytest
from fastapi.testclient import TestClient

from app.agent import tools as T
from app.agent.i18n import LANGS, TEXT
from app.main import app
from tests.test_agent import LHDN, SCAM

client = TestClient(app)
PH = lambda s: set(re.findall(r"\{(\w+)\}", s))


def test_every_code_in_all_languages_with_same_placeholders():
    for code, by in TEXT.items():
        assert set(by) == set(LANGS), code
        assert all(by[lg].strip() for lg in LANGS), code
        assert all(PH(by[lg]) == PH(by["en"]) for lg in LANGS), code
        assert not any("—" in by[lg] for lg in LANGS), code  # no em dashes


def test_every_red_flag_key_has_text():
    assert all(k in TEXT for _, k in T.RED_FLAGS)


def test_english_unchanged():
    ok = T.scam_check(LHDN, "LHDN")
    assert ok["good_signs"][1] == "Wording matches typical LHDN letters (scammers copy this too)"
    assert ok["verify_yourself"][1].startswith("Find the phone number on ") and ok["verify_yourself"][3] == "Do not pay or share any TAC/OTP until you have done these steps."
    bad = T.scam_check(SCAM, "PDRM")
    assert "Shortened link (bit.ly) instead of an official site" in bad["red_flags"]
    assert "Creates fake urgency" in bad["red_flags"]
    assert [r["code"] for r in bad["reasons"] if r["kind"] == "risk"][:2] == ["transfer_account", "urgency"]
    assert T.scam_check("Hello there", "UNKNOWN")["verify_yourself"][1].startswith("Find the phone number on the agency's")


def test_scam_check_bm():
    ok, bad = T.scam_check(LHDN, "LHDN", "bm"), T.scam_check(SCAM, "PDRM", "bm")
    en_ok, en_bad = T.scam_check(LHDN, "LHDN"), T.scam_check(SCAM, "PDRM")
    assert ok["good_signs"][1] == "Bahasa sepadan dengan surat LHDN biasa (penipu pun boleh meniru ini)"
    assert "Pautan pendek (bit.ly) dan bukan laman web rasmi" in bad["red_flags"]
    assert "Mencipta rasa tergesa-gesa yang palsu" in bad["red_flags"]
    assert "https://www.hasil.gov.my" in ok["verify_yourself"][0]
    # same codes, same scores, only the words change
    assert [r["code"] for r in bad["reasons"]] == [r["code"] for r in en_bad["reasons"]]
    assert (bad["score"], bad["verdict"], ok["score"]) == (en_bad["score"], en_bad["verdict"], en_ok["score"])
    assert not set(bad["red_flags"]) & set(en_bad["red_flags"])


@pytest.mark.parametrize("lang", ["zh", "ta"])
def test_api_analyze_localised(lang):
    d = client.post("/api/analyze", json={"text": SCAM, "language": lang}).json()
    assert d["scam"]["reasons"] and all(not r["text"].isascii() for r in d["scam"]["reasons"])
    assert all(not s.isascii() for s in d["scam"]["verify_yourself"])
    assert all(not s.isascii() for s in d["scam"]["red_flags"])
    assert all(r["code"] for r in d["scam"]["reasons"])
    assert any("Creates fake urgency" in x["message"] for x in d["trace"])


@pytest.mark.parametrize("lang", ["bm", "en", "zh", "ta"])
def test_practice_lang(lang):
    items = client.get(f"/api/practice?n=99&lang={lang}").json()
    assert len(items) >= 8
    for i in items:
        assert i["clues"] and (lang in ("en",) or any(not c.isascii() for c in i["clues"]) or lang == "bm")
        assert i["agent"]["verify_yourself"]
    if lang in ("zh", "ta"):
        assert all(not c.isascii() for i in items for c in i["clues"])
        assert all(not v.isascii() for i in items for v in i["agent"]["verify_yourself"])
    if lang == "en":
        assert any("Domain is not hasil.gov.my" in i["clues"] for i in items)


def test_practice_rejects_bad_lang():
    assert client.get("/api/practice?lang=xx").status_code == 422
