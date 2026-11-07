"""Eval gate: scam recall >= 0.9 and legit false-positive rate <= 0.1 on tests/eval/dataset.json.

CI runs `pytest -q`, so a rules change that breaks either threshold fails the build.
Details and the full report: `python -m tests.eval.run`, docs/EVAL.md.
"""
import pytest

from tests.eval import run

MIN_RECALL, MAX_FPR = 0.9, 0.1


@pytest.fixture(scope="module")
def report():
    return run.evaluate()


def test_dataset_is_big_enough_and_balanced_across_languages():
    items = run.load()
    assert len(items) >= 60
    for lang in run.LANGS:
        for label in ("scam", "legit"):
            assert sum(1 for i in items if i["lang"] == lang and i["label"] == label) >= 8, (lang, label)
    assert {i["label"] for i in items} == {"scam", "legit"}
    assert len({i["id"] for i in items}) == len(items)
    assert all(len(i["text"]) >= 10 for i in items)


def test_scam_recall_meets_threshold(report):
    assert report["overall"]["recall"] >= MIN_RECALL, run.render(report)


def test_legit_false_positive_rate_meets_threshold(report):
    assert report["overall"]["fpr"] <= MAX_FPR, run.render(report)


@pytest.mark.parametrize("lang", run.LANGS)
def test_every_language_meets_both_thresholds_on_its_own(report, lang):
    s = report["by_language"][lang]
    assert s["recall"] >= MIN_RECALL and s["fpr"] <= MAX_FPR, (lang, s)


def test_no_scam_passes_as_completely_clear(report):
    assert report["overall"]["scam_missed_entirely"] == 0  # at worst a scam gets "caution", never "no signals"


def test_latency_is_reported_and_small(report):
    lat = report["latency_ms"]
    assert 0 < lat["p50"] <= lat["p95"] <= lat["max"]
    assert lat["p95"] < 2000  # the rules verdict must arrive well inside the 2 s target of the stream endpoint


# Near-misses: ordinary sentences that share a word with a scam rule must not raise that rule.
@pytest.mark.parametrize("text", [
    "Wow you won the badminton game yesterday, well done!",
    "Anda menang dalam perlawanan semalam, tahniah abang!",
    "Please deposit your cheque at the counter to register for the course.",
    "Send the notes to my friend's account on Google Drive please",
    "The army doctor at the camp was kind to my uncle last year",
])
def test_ordinary_sentences_do_not_trip_the_new_scam_rules(text):
    from app.agent import tools as T
    codes = {r["code"] for r in T.scam_check(text, "UNKNOWN", "en")["reasons"] if r["kind"] == "risk"}
    assert not codes & {"prize_win", "advance_fee", "romance_money", "guaranteed_returns"}, codes


@pytest.mark.parametrize("text,code", [
    ("Guaranteed gold investment, 30% profit every month, only RM 500 to start.", "guaranteed_returns"),
    ("RM 100 deposit needed to activate your account.", "advance_fee"),
    ("I am an army doctor in Syria. Send the money through my friend's account.", "romance_money"),
    ("Congratulations, you have won a prize of RM 10,000!", "prize_win"),
])
def test_new_rules_fire_on_their_scam(text, code):
    from app.agent import tools as T
    assert code in {r["code"] for r in T.scam_check(text, "UNKNOWN", "en")["reasons"] if r["kind"] == "risk"}
