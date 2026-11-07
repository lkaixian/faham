"""FAHAM orchestrator — the agent's decision flow.

read → verify → explain → teach → route → act, with a human-approval gate.
The planner changes course on evidence: a likely scam switches the plan from
"help the user comply" to "protect the user and report".
"""
from __future__ import annotations

from ..models import (Action, AnalyzeRequest, AnalyzeResponse, Fields, Lesson,
                      Route, ScamVerdict, TraceStep)
from .. import cache
from . import tools as T


class OCRUnavailable(Exception):
    pass


class Trace:
    def __init__(self) -> None:
        self.steps: list[TraceStep] = []

    def think(self, stage, msg):
        self.steps.append(TraceStep(stage=stage, kind="think", message=msg))

    def call(self, stage, tool, msg):
        self.steps.append(TraceStep(stage=stage, kind="tool", tool=tool, message=msg))

    def note(self, stage, kind, msg, flag=False):
        self.steps.append(TraceStep(stage=stage, kind=kind, message=msg, flag=flag))


def quick_verdict(req: AnalyzeRequest) -> dict | None:
    """Rules-only verdict for the SSE stream's first event (no LLM, no OCR). None if the request has only an image."""
    if not req.text.strip():
        return None
    redacted, _ = T.redact(req.text)
    issuer, _ = T.classify_issuer(redacted)
    v = T.scam_check(redacted, issuer, req.language)
    f = T.extract_fields(redacted)
    return {"verdict": v["verdict"], "score": v["score"], "scam_type": v["scam_type"], "issuer": issuer,
            "fields": f, "reasons": v["reasons"], "verify_yourself": v["verify_yourself"]}


class _Memo:
    """Tool calls with the same name and arguments run once per analysis (the planner may ask twice)."""

    def __init__(self) -> None:
        self.seen: dict[tuple, object] = {}
        self.skipped = 0

    def call(self, name: str, *args):
        k = (name, repr(args))
        if k in self.seen:
            self.skipped += 1
            return self.seen[k]
        self.seen[k] = T.TOOLS[name].fn(*args)
        return self.seen[k]


def run(req: AnalyzeRequest, image_bytes: bytes | None = None, extra_signals: tuple | list = ()) -> AnalyzeResponse:
    tr = Trace()
    tr.think("read", "Goal: help the user understand this letter, confirm it is real, and decide the next action.")

    # ---- READ
    raw = T.TOOLS["ocr.read"].fn(text=req.text, image_bytes=image_bytes)
    if not raw.strip():
        raise OCRUnavailable("OCR unavailable, paste the text instead")
    tr.call("read", "ocr.read", f"{len(raw.split())} words read")
    redacted, counts = T.TOOLS["privacy.redact"].fn(raw)
    tr.call("read", "privacy.redact", "masked: " + ", ".join(f"{k} ×{v}" for k, v in counts.items()) + " — only redacted text is processed")
    # Same redacted text + language (+ postcode, extra signals) gives the same answer: serve it from cache for up to an hour.
    key = cache.fingerprint(redacted, req.language, req.postcode or "", tuple(extra_signals))
    if (hit := cache.ANALYSES.get(key)) is not None:
        return hit.model_copy(deep=True)
    issuer, conf = T.TOOLS["classify.issuer"].fn(redacted)
    tr.call("read", "classify.issuer", f"issuer = {issuer} (confidence {conf})")
    f = T.TOOLS["extract.fields"].fn(redacted)
    tr.call("read", "extract.fields", f"amount = {f['amount']} · deadline = {f['deadline']} · ref = {f['reference']}")

    # ---- VERIFY
    tr.think("verify", "Before explaining anything, I must check this is not a scam.")
    memo = _Memo()
    verdict = memo.call("scam.check", redacted, issuer, req.language, tuple(extra_signals))
    en = memo.call("scam.check", redacted, issuer, "en", tuple(extra_signals))  # trace stays English; same args as above run once
    tr.call("verify", "scam.check", "domain allowlist · red-flag rules · reference pattern")
    for g in en["good_signs"]:
        tr.note("verify", "ok", "✓ " + g)
    for r in en["red_flags"]:
        tr.note("verify", "bad", "✗ " + r)
    genuine = verdict["genuine"]
    if verdict["verdict"] == "no_signals":
        tr.note("verify", "ok", "verdict: NO SCAM SIGNALS FOUND (not proof, verify yourself)")
    elif genuine:
        tr.note("verify", "warn", "verdict: CAUTION")
    else:
        tr.note("verify", "bad", f"verdict: LIKELY SCAM ({verdict['score']}/100) -> switch plan: protect the user, do not pay", flag=True)

    # ---- EXPLAIN
    tr.think("explain", f"Explaining in '{req.language}', short sentences, amount and deadline first.")
    explanation = T.TOOLS["llm.explain"].fn(redacted, issuer, f, genuine, req.language)
    tr.call("explain", "llm.explain", "plain-language explanation ready")

    # ---- TEACH
    stype = verdict.get("scam_type")
    lesson = T.TOOLS["teach.lesson"].fn(issuer, genuine, req.language, stype)
    tr.call("teach", "teach.lesson", f"lesson card + {len(lesson['terms'])} Kamus Surat terms: {', '.join(lesson['terms'])}")

    # ---- ROUTE
    route = T.TOOLS["gov.retrieve"].fn(issuer, genuine, req.language, stype)
    office = T.TOOLS["office.locate"].fn(issuer if genuine else "PDRM", req.postcode)
    if office:
        route["walkin_steps"] = [f"Nearest: {office['name']} · hours: {office['hours']} · booking: {office['booking']} · sample data, verify on the official site"] + route["walkin_steps"]
    online_first = genuine and bool(route["online_steps"])
    tr.think("route", "Decision: genuine and online steps exist -> online first, walk-in as backup." if online_first
             else "Decision: " + ("no online steps" if genuine else "likely scam; never use links in the message") + " -> walk-in / official channel first.")
    calls = [("gov.retrieve", f"steps from cached registry ({route['retrieved_at']}) · {route['source_url']} · confidence {route['confidence']}"),
             ("office.locate", f"{office['name'] if office else 'no office data'}")]
    for name, msg in (calls if online_first else calls[::-1]):
        tr.call("route", name, msg)

    # ---- ACT (human-in-the-loop)
    act = T.TOOLS["act.draft"].fn(issuer, f, genuine, req.language)
    tr.call("act", "act.draft", "draft prepared" + (f" · reminder {act['reminder']}" if act["reminder"] else ""))
    tr.note("act", "warn", "⏸ waiting for user approval — nothing is sent or paid automatically")

    src = T.SOURCES.get(issuer, {})
    resp = AnalyzeResponse(
        redacted_text=redacted,
        fields=Fields(issuer=issuer, letter_type=src.get("letter_type", "Unknown") if genuine else "Suspicious message",
                      amount=f["amount"], deadline=f["deadline"], reference=f["reference"]),
        scam=ScamVerdict(**verdict),
        explanation=explanation,
        lesson=Lesson(**lesson),
        route=Route(online_steps=route["online_steps"], walkin_steps=route["walkin_steps"],
                    prepare_online=route["prepare_online"], prepare_walkin=route["prepare_walkin"],
                    source_url=route["source_url"], retrieved_at=f"{route['retrieved_at']} (cached)", confidence=route["confidence"]),
        action=Action(draft=act["draft"], reminder=act["reminder"]),
        trace=tr.steps,
    )
    cache.ANALYSES.set(key, resp.model_copy(deep=True))
    return resp
