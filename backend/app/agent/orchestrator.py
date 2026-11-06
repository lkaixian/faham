"""FAHAM orchestrator — the agent's decision flow.

read → verify → explain → teach → route → act, with a human-approval gate.
The planner changes course on evidence: a likely scam switches the plan from
"help the user comply" to "protect the user and report".
"""
from __future__ import annotations

from ..models import (Action, AnalyzeRequest, AnalyzeResponse, Fields, Lesson,
                      Route, ScamVerdict, TraceStep)
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
    issuer, conf = T.TOOLS["classify.issuer"].fn(redacted)
    tr.call("read", "classify.issuer", f"issuer = {issuer} (confidence {conf})")
    f = T.TOOLS["extract.fields"].fn(redacted)
    tr.call("read", "extract.fields", f"amount = {f['amount']} · deadline = {f['deadline']} · ref = {f['reference']}")

    # ---- VERIFY
    tr.think("verify", "Before explaining anything, I must check this is not a scam.")
    verdict = T.TOOLS["scam.check"].fn(redacted, issuer, req.language, extra_signals)
    en = verdict if req.language == "en" else T.TOOLS["scam.check"].fn(redacted, issuer, "en", extra_signals)  # trace stays English
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
    lesson = T.TOOLS["teach.lesson"].fn(issuer, genuine)
    tr.call("teach", "teach.lesson", f"lesson card + {len(lesson['terms'])} Kamus Surat terms: {', '.join(lesson['terms'])}")

    # ---- ROUTE
    route = T.TOOLS["gov.retrieve"].fn(issuer, genuine)
    office = T.TOOLS["office.locate"].fn(issuer if genuine else "PDRM", req.postcode)
    if office:
        route["walkin_steps"] = [f"Nearest: {office['name']} · hours: {office['hours']} · booking: {office['booking']}"] + route["walkin_steps"]
    online_first = genuine and bool(route["online_steps"])
    tr.think("route", "Decision: genuine and online steps exist -> online first, walk-in as backup." if online_first
             else "Decision: " + ("no online steps" if genuine else "likely scam; never use links in the message") + " -> walk-in / official channel first.")
    calls = [("gov.retrieve", f"steps from cached registry ({route['retrieved_at']}) · {route['source_url']} · confidence {route['confidence']}"),
             ("office.locate", f"{office['name'] if office else 'no office data'}")]
    for name, msg in (calls if online_first else calls[::-1]):
        tr.call("route", name, msg)

    # ---- ACT (human-in-the-loop)
    act = T.TOOLS["act.draft"].fn(issuer, f, genuine)
    tr.call("act", "act.draft", "draft prepared" + (f" · reminder {act['reminder']}" if act["reminder"] else ""))
    tr.note("act", "warn", "⏸ waiting for user approval — nothing is sent or paid automatically")

    src = T.SOURCES.get(issuer, {})
    return AnalyzeResponse(
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
