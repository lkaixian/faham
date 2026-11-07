"""P0 accuracy and safety: plate vs money, family impersonation, zh/ta lexicons, thresholds, cache, scam types."""
import pytest
from fastapi.testclient import TestClient

from app import cache
from app.agent import tools as T
from app.agent.scam_content import SCAM_TYPES
from app.main import app

client = TestClient(app)


def analyze(text, lang="en"):
    cache.ANALYSES.clear()
    r = client.post("/api/analyze", json={"text": text, "language": lang})
    assert r.status_code == 200
    return r.json()


# ---- 1. plates vs money
@pytest.mark.parametrize("s", ["Bayar RM500 sekarang", "Jumlah RM1,200.50 kena dibayar", "RM 500 sahaja", "Caj rm500"])
def test_money_is_not_a_plate(s):
    out, counts = T.redact(s)
    assert "[PLATE]" not in out and counts["plate"] == 0


def test_real_plate_still_masked():
    out, counts = T.redact("Kereta JQR1234 disaman")
    assert "[PLATE]" in out and "JQR1234" not in out and counts["plate"] == 1


# ---- 2. family impersonation
FAMILY = {
    "bm": "Hi mak, ni nombor baru Ali. Phone Ali rosak. Boleh tolong transfer RM800 sekarang? Nanti Ali ganti.",
    "en": "Hi mum, this is my new number, my phone broke. Can you transfer RM800 for me today? I will pay you back.",
    "zh": "妈，这是我的新号码，我手机坏了。你能马上转账 RM800 给我吗？",
}


@pytest.mark.parametrize("lang", FAMILY)
def test_family_impersonation_is_high_risk(lang):
    v = T.scam_check(FAMILY[lang], "UNKNOWN", lang)
    assert v["verdict"] == "likely_scam" and v["score"] < 40
    assert v["scam_type"] == "family_impersonation"
    assert any(r["code"] == "family_impersonation" for r in v["reasons"])
    assert "OLD" in v["verify_yourself"][0] or "LAMA" in v["verify_yourself"][0] or "旧号码" in v["verify_yourself"][0]


def test_family_rule_needs_all_three_parts():
    assert T.scam_check("Hi mak, ni nombor baru saya.", "UNKNOWN")["scam_type"] != "family_impersonation"
    assert T.scam_check("Mak, jom makan. Abang bayar.", "UNKNOWN")["scam_type"] != "family_impersonation"


# ---- 3. zh and ta lexicons
ZH_POLICE = "我们是警察局。你涉嫌洗钱，将被逮捕，账户会被冻结。请立即把钱转到安全账户，不要告诉任何人。"
TA_POLICE = "நாங்கள் காவல்துறை. உங்கள் மீது பணமோசடி வழக்கு உள்ளது, கைது செய்வோம். பாதுகாப்பான கணக்கிற்கு பணம் அனுப்புங்கள். யாரிடமும் சொல்ல வேண்டாம்."


@pytest.mark.parametrize("text,lang", [(ZH_POLICE, "zh"), (TA_POLICE, "ta")])
def test_fake_police_in_zh_and_ta_is_scam(text, lang):
    v = T.scam_check(text, "UNKNOWN", lang)
    assert v["verdict"] == "likely_scam"
    codes = {r["code"] for r in v["reasons"] if r["kind"] == "risk"}
    assert {"arrest", "safe_account", "secret"} <= codes
    assert v["scam_type"] == "macau"


# ---- 4. legitimate utility bill stays clear
def test_legit_utility_bill_no_contradiction():
    bill = ("TENAGA NASIONAL BERHAD (TNB)\nRujukan: TNB/AKTA447/BORANG-A/2026/5512\nTunggakan RM 215.40 hendaklah dijelaskan "
            "sebelum 18 Disember 2026 melalui myTNB https://www.mytnb.com.my atau kaunter Kedai Tenaga TNB.")
    out = analyze(bill, "bm")
    assert out["fields"]["issuer"] == "UTILITY"
    assert out["scam"]["verdict"] == "no_signals" and out["scam"]["red_flags"] == []
    assert out["scam"]["scam_type"] is None


# ---- 5. determinism + cache never holds raw text
def test_same_text_same_verdict_and_cached():
    text = "Notis LHDN: baki RM 100 sebelum 1 Disember 2026 di mytax.hasil.gov.my. Tel 012-345 6789"
    cache.ANALYSES.clear()
    a = client.post("/api/analyze", json={"text": text, "language": "en"}).json()
    assert len(cache.ANALYSES) == 1
    b = client.post("/api/analyze", json={"text": text, "language": "en"}).json()
    a.pop("others_checked"), b.pop("others_checked")  # the counter is meant to change between checks
    assert a == b
    assert "012-345 6789" not in str(list(cache.ANALYSES._d.keys())) and "012-345 6789" not in a["redacted_text"]
    c = client.post("/api/analyze", json={"text": text, "language": "bm"}).json()
    assert c["lesson"]["question"] != a["lesson"]["question"]  # language is part of the key


def test_cache_ttl_and_lru():
    t = [0.0]
    c = cache.TTLCache(maxsize=2, ttl=10, clock=lambda: t[0])
    c.set("a", 1); c.set("b", 2); c.set("c", 3)
    assert c.get("a") is None and c.get("b") == 2
    t[0] = 11
    assert c.get("b") is None


def test_fingerprint_normalises_and_includes_language():
    assert cache.fingerprint("Hello  World", "en") == cache.fingerprint("hello world", "en")
    assert cache.fingerprint("hello", "en") != cache.fingerprint("hello", "bm")


# ---- 6. verdict is a pure function of score
@pytest.mark.parametrize("score,v", [(0, "likely_scam"), (59, "likely_scam"), (60, "caution"), (79, "caution"), (80, "no_signals"), (100, "no_signals")])
def test_thresholds(score, v):
    assert T.verdict_from_score(score) == v


def test_verdict_never_disagrees_with_score():
    samples = [FAMILY["en"], ZH_POLICE, TA_POLICE, "Hello there", "Notis LHDN taksiran RM 5 di hasil.gov.my",
               "Bayar RM2,150.00 dalam masa 24 JAM ke akaun Maybank 1234 5678 9012. Waran tangkap. Jangan beritahu sesiapa."]
    for s in samples:
        for issuer in ("UNKNOWN", "LHDN", "PDRM"):
            v = T.scam_check(s, issuer)
            assert v["verdict"] == T.verdict_from_score(v["score"]), (s, issuer, v["score"], v["verdict"])
            assert v["genuine"] == (v["verdict"] != "likely_scam")


# ---- 7. scam type -> lesson, route, draft, language
def test_fake_lhdn_refund_gets_no_police_steps():
    t = "LHDN: Anda layak terima lebihan bayaran balik RM 1,870.00. Klik bit.ly/lhdn-refund dan masukkan TAC dalam 24 jam."
    out = analyze(t, "en")
    assert out["scam"]["scam_type"] == "phishing_refund"
    steps = " ".join(out["route"]["online_steps"] + out["route"]["walkin_steps"]).lower()
    assert "summons" not in steps and "mybayar" not in steps and "saman" not in steps
    assert "official website yourself" in steps
    assert "refund" in out["lesson"]["answer"].lower()


@pytest.mark.parametrize("lang,needle", [("bm", "Kenapa"), ("zh", "为什么"), ("ta", "ஏன்")])
def test_lesson_route_draft_follow_language(lang, needle):
    out = analyze(FAMILY["en"], lang)
    assert needle in out["lesson"]["question"]
    assert out["route"]["online_steps"][0] != analyze(FAMILY["en"], "en")["route"]["online_steps"][0]
    assert out["action"]["requires_approval"] is True


def test_bm_genuine_letter_is_not_english():
    out = analyze("NOTIS LHDN taksiran. Baki RM 1,240.00 sebelum 15 Disember 2026 melalui ByrHASIL di mytax.hasil.gov.my", "bm")
    assert out["route"]["online_steps"][0].startswith("Log masuk")
    assert out["action"]["draft"].startswith("Kepada:")


def test_no_agency_template_for_unknown_sender():
    out = analyze("Hello, please read this note about our meeting.", "en")
    assert out["fields"]["issuer"] == "UNKNOWN"
    assert not out["action"]["draft"].startswith(("To:", "Kepada:")) and "agency" not in out["action"]["draft"].lower().split("\n")[0]


def test_every_scam_type_has_full_content():
    from app.agent import scam_content as C
    for t in SCAM_TYPES:
        for lang in ("bm", "en", "zh", "ta"):
            assert C.scam_lesson(t, lang)["answer"]
            assert C.scam_route(t, lang, "2026-11-06")["online_steps"][0]
