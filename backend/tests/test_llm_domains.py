from app import llm
from app.agent import tools as T

LETTER = "Notis LHDN. Bayar sebelum 15 Disember 2026 melalui ByrHASIL di hasil.gov.my. Rujukan LHDN/SAMPEL/TT2025/0001"


def explain_with(monkeypatch, text):
    monkeypatch.setattr(llm, "complete", lambda prompt, lang: text)
    return T.explain(LETTER, "LHDN", {"amount": "RM 50", "deadline": "15 Disember 2026"}, True, "en")


def test_model_text_with_wrong_domain_is_dropped(monkeypatch):
    out = explain_with(monkeypatch, "Pay on the results.gov.my website.")
    assert "results.gov.my" not in out and "Lembaga Hasil" in out  # fell back to the template


def test_model_text_with_letter_domain_is_kept(monkeypatch):
    assert explain_with(monkeypatch, "Pay via hasil.gov.my before 15 December.") == "Pay via hasil.gov.my before 15 December."


def test_model_text_without_domain_is_kept(monkeypatch):
    assert explain_with(monkeypatch, "Pay RM 50 by 15 December 2026.") == "Pay RM 50 by 15 December 2026."
