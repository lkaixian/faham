import io
import json
import urllib.request

from app import config, llm
from app.agent import tools as T


def test_name_anywhere_passport_dob_and_sweep():
    out, c = T.redact("Pemohon ALI BIN ABU dan RAJU A/L MUTHU hadir. Pasport A12345678. Tarikh lahir: 01 Jan 1990\nNo. siri 99887766 55")
    assert "ALI" not in out and "RAJU" not in out and c["name"] == 2
    assert "A12345678" not in out and c["id"] == 1
    assert "1990" not in out and c["dob"] == 1
    assert "99887766" not in out and c["other"] == 1


def test_sweep_keeps_amounts_dates_and_refs():
    out, _ = T.redact("Bayar RM 1,240.00 sebelum 15 Disember 2026. Rujukan LHDN/SAMPEL/TT2025/0001")
    assert "RM 1,240.00" in out and "15 Disember 2026" in out and "LHDN/SAMPEL/TT2025/0001" in out


def test_llm_blocks_residual_pii(monkeypatch):
    monkeypatch.setattr(config, "LLM_PROVIDER", "ilmu")
    monkeypatch.setattr(config, "ILMU_API_KEY", "sk-test")
    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: (_ for _ in ()).throw(AssertionError("must not call")))
    for leak in ("mail ali@contoh.example", "ic 900101-01-1234", "no 1234 5678 90"):
        assert llm.complete(leak, "en") is None


def test_llm_chain_falls_back_to_second_provider(monkeypatch):
    monkeypatch.setattr(config, "LLM_PROVIDER", "ilmu,anthropic")
    monkeypatch.setattr(config, "ILMU_API_KEY", "sk-test")
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "k2")
    assert config.llm_chain() == ["ilmu", "anthropic"]
    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: (_ for _ in ()).throw(OSError("down")))
    monkeypatch.setitem(llm.PROVIDERS, "anthropic", lambda system, user: "from anthropic")
    assert llm.complete("Notis cukai", "bm") == "from anthropic"
    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: io.BytesIO(json.dumps({"choices": [{"message": {"content": "from ilmu"}}]}).encode()))
    assert llm.complete("Notis cukai", "bm") == "from ilmu"


def test_providers_without_key_are_skipped(monkeypatch):
    monkeypatch.setattr(config, "LLM_PROVIDER", "ilmu,anthropic")
    monkeypatch.setattr(config, "ILMU_API_KEY", "")
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "k2")
    assert config.llm_chain() == ["anthropic"]
