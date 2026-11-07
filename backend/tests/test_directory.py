"""The domain-only directory of real banks, councils, states, universities and companies."""
from __future__ import annotations

import json
import re

from app import config
from app.agent import tools as T

DIR = json.loads((config.DATA_DIR / "official_directory.json").read_text(encoding="utf-8"))
DOM = re.compile(r"^([a-z0-9-]+\.)+[a-z]{2,}$")


def test_directory_is_well_formed_and_has_no_shared_domain():
    seen = {}
    for e in DIR:
        assert e["id"] and e["name"] and e["category"] and isinstance(e["domains"], list)
        assert "online_steps" not in e  # the directory names websites; procedures come only from official_sources.json
        for d in e["domains"]:
            assert DOM.match(d) and not d.startswith("www."), d
            assert seen.setdefault(d, e["id"]) == e["id"], f"{d} listed for {seen[d]} and {e['id']}"
    assert len(DIR) > 400


def test_real_bank_and_university_links_are_official_not_flagged():
    for text in ("Log in at https://www.maybank2u.com.my to check", "Sertai hackathon di https://www.xmu.edu.my/events",
                 "Semak di https://www.mbpj.gov.my/bayaran", "Pantau di https://www.cimbclicks.com.my"):
        r = T.scam_check(text, "UNKNOWN")
        assert not any("unofficial" in x.lower() or "not an official" in x.lower() for x in r["red_flags"]), (text, r["red_flags"])
        assert any(g["code"] == "official_domain" for g in r["reasons"]), text


def test_lookalike_of_a_bank_is_flagged_but_ordinary_names_are_not():
    assert T._lookalike("maybnk-login.com") and T._lookalike("cimb-claim.xyz")
    assert not T._lookalike("selangorjournal.com") and not T._lookalike("wise-tutor.com") and not T._lookalike("mybusiness-shop.com")
    assert any(r["code"] == "unofficial_domain" for r in T.scam_check("Kemas kini di https://maybank-secure.top/login", "UNKNOWN")["reasons"])


def test_lookup_registry_finds_a_directory_name_without_inventing_steps():
    r = T.registry_lookup("Xiamen University Malaysia")
    assert r["known"] and "xmu.edu.my" in r["domains"] and r["online_steps"] == []
    assert T.registry_lookup("DOSM")["known"] and not T.registry_lookup("Nonexistent Agency Pte")["known"]
    assert T.registry_lookup("LHDN")["online_steps"]  # registry entries keep their steps


def test_edu_my_is_fetchable_but_lookalikes_are_not():
    assert T._is_official("www.xmu.edu.my") and T._is_official("shop.maybank2u.com.my")
    assert not T._is_official("xmu.edu.my.evil.com") and not T._is_official("maybank2u.com.my.login.top")
