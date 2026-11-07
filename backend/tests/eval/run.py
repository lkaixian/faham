"""Scam-detection evaluation: precision, recall, false-positive rate and latency on a labelled set.

    cd backend && python -m tests.eval.run                 # print the report
    python -m tests.eval.run --json report.json            # also write it
    python -m tests.eval.run --min-recall 0.9 --max-fpr 0.1   # exit 1 when a threshold is missed (CI does this)

Dataset: tests/eval/dataset.json, fictional messages in BM, EN, 中文 and தமிழ், half "scam" and half "legit".
"dev" items (72) were used while building the rules; "held_out" items (16) were written afterwards. Their first run missed prize scams (recall 0.625),
so a prize_win rule was added: after that fix the split is no longer clean. See docs/EVAL.md.
"Predicted scam" means the agent's verdict is `likely_scam`. `caution` is reported separately and does not count as a hit
or as a false alarm, because it tells the user to verify rather than to stop.
The LLM is always off here: this measures the deterministic rules, which are the safety floor.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

from app import cache, config
from app.agent import orchestrator
from app.models import AnalyzeRequest

DATASET = Path(__file__).with_name("dataset.json")
LANGS = ("bm", "en", "zh", "ta")


def load() -> list[dict]:
    return json.loads(DATASET.read_text(encoding="utf-8"))


def _pct(sorted_ms: list[float], p: float) -> float:
    if not sorted_ms:
        return 0.0
    i = min(len(sorted_ms) - 1, max(0, round(p / 100 * (len(sorted_ms) - 1))))
    return sorted_ms[i]


def _ratio(a: int, b: int) -> float:
    return a / b if b else 0.0


def evaluate(items: list[dict] | None = None) -> dict:
    items = items if items is not None else load()
    rows, times = [], []
    saved = config.llm_chain
    config.llm_chain = lambda: []  # rules only: deterministic, offline, nothing leaves the machine
    try:
        for it in items:
            cache.ANALYSES.clear()  # measure real work, not a cache hit
            t0 = time.perf_counter()
            r = orchestrator.run(AnalyzeRequest(text=it["text"], language=it["lang"]))
            ms = (time.perf_counter() - t0) * 1000
            times.append(ms)
            rows.append({**it, "verdict": r.scam.verdict, "score": r.scam.score, "scam_type": r.scam.scam_type, "ms": round(ms, 2)})
    finally:
        config.llm_chain = saved  # do not leak the override into other tests
        cache.ANALYSES.clear()

    def stats(rs: list[dict]) -> dict:
        tp = sum(1 for x in rs if x["label"] == "scam" and x["verdict"] == "likely_scam")
        fn = sum(1 for x in rs if x["label"] == "scam" and x["verdict"] != "likely_scam")
        fp = sum(1 for x in rs if x["label"] == "legit" and x["verdict"] == "likely_scam")
        tn = sum(1 for x in rs if x["label"] == "legit" and x["verdict"] != "likely_scam")
        scams = [x for x in rs if x["label"] == "scam"]
        legit = [x for x in rs if x["label"] == "legit"]
        return {
            "n": len(rs), "tp": tp, "fn": fn, "fp": fp, "tn": tn,
            "precision": round(_ratio(tp, tp + fp), 4), "recall": round(_ratio(tp, tp + fn), 4),
            "fpr": round(_ratio(fp, fp + tn), 4),
            "scam_missed_entirely": sum(1 for x in scams if x["verdict"] == "no_signals"),  # not even a caution
            "legit_cautioned": sum(1 for x in legit if x["verdict"] == "caution"),
        }

    s = sorted(times)
    return {
        "overall": stats(rows),
        "by_language": {lg: stats([x for x in rows if x["lang"] == lg]) for lg in LANGS},
        "by_split": {sp: stats([x for x in rows if x.get("split") == sp]) for sp in ("dev", "held_out")},
        "latency_ms": {"p50": round(statistics.median(s), 2), "p95": round(_pct(s, 95), 2), "max": round(s[-1], 2)},
        "errors": [{k: x[k] for k in ("id", "lang", "label", "kind", "verdict", "score", "text")} for x in rows
                   if (x["label"] == "scam") != (x["verdict"] == "likely_scam")],
    }


def render(rep: dict) -> str:
    o = rep["overall"]
    out = [f"Messages: {o['n']}   TP {o['tp']}  FN {o['fn']}  FP {o['fp']}  TN {o['tn']}",
           f"Precision {o['precision']:.3f}   Recall {o['recall']:.3f}   False-positive rate {o['fpr']:.3f}",
           f"Scams with no signal at all: {o['scam_missed_entirely']}   Legit messages cautioned: {o['legit_cautioned']}",
           f"Latency (rules only, in process): p50 {rep['latency_ms']['p50']} ms   p95 {rep['latency_ms']['p95']} ms   max {rep['latency_ms']['max']} ms", "",
           "Per language:      n   recall  fpr   precision"]
    for lg, s in rep["by_language"].items():
        out.append(f"  {lg:<14} {s['n']:>3}   {s['recall']:.3f}   {s['fpr']:.3f}   {s['precision']:.3f}")
    out += ["", "By split (dev = used while building the rules, held_out = written afterwards; see docs/EVAL.md):"]
    for sp, s in rep["by_split"].items():
        out.append(f"  {sp:<14} {s['n']:>3}   recall {s['recall']:.3f}   fpr {s['fpr']:.3f}   precision {s['precision']:.3f}")
    if rep["errors"]:
        out += ["", "Misclassified:"]
        out += [f"  {e['id']:<14} {e['kind']:<20} label={e['label']:<5} verdict={e['verdict']:<11} score={e['score']}  {e['text'][:70]}" for e in rep["errors"]]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--json", help="write the full report here")
    ap.add_argument("--min-recall", type=float, help="fail if scam recall is below this")
    ap.add_argument("--max-fpr", type=float, help="fail if the legit false-positive rate is above this")
    a = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")
    rep = evaluate()
    print(render(rep))
    if a.json:
        Path(a.json).write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    bad = []
    if a.min_recall is not None and rep["overall"]["recall"] < a.min_recall:
        bad.append(f"recall {rep['overall']['recall']:.3f} < {a.min_recall}")
    if a.max_fpr is not None and rep["overall"]["fpr"] > a.max_fpr:
        bad.append(f"false-positive rate {rep['overall']['fpr']:.3f} > {a.max_fpr}")
    if bad:
        print("\nFAIL: " + "; ".join(bad))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
