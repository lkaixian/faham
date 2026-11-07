"""Tulen orchestrator.

read (fixed: text out of the file, personal details masked) -> the AGENT (loop.py: plans, uses tools, reasons, decides)
-> build the answer from what the agent found: verdict (rules re-run as a floor, plus the agent's quoted evidence),
explanation, lesson, route, and the drafts and files the agent chose to prepare. Everything that leaves the person's
hands needs their approval. With no model, the same pipeline runs on rules alone.
"""
from __future__ import annotations

from ..models import (Action, AgentInfo, AnalyzeRequest, AnalyzeResponse, Attachment, ExtraDraft, Fields, Lesson,
                      Route, ScamVerdict, TraceStep)
from .. import cache
from . import loop
from . import tools as T
from .i18n import render


class OCRUnavailable(Exception):
    pass


class Trace:
    """The reasoning trace. `sink`, if given, is called with each step as it happens (the live stream uses it)."""

    def __init__(self, sink=None) -> None:
        self.steps: list[TraceStep] = []
        self.sink = sink

    def _add(self, step: TraceStep) -> None:
        self.steps.append(step)
        if self.sink:
            self.sink(step)

    def think(self, stage, msg):
        self._add(TraceStep(stage=stage, kind="think", message=msg))

    def call(self, stage, tool, msg, facts=None):
        self._add(TraceStep(stage=stage, kind="tool", tool=tool, message=msg, facts=facts))

    def note(self, stage, kind, msg, flag=False):
        self._add(TraceStep(stage=stage, kind=kind, message=msg, flag=flag))


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


def _report(lang: str, issuer: str, verdict: dict) -> str:
    who = T.SOURCES.get(issuer, {}).get("name") or render("the_agency", lang)
    risks = [r["text"] for r in verdict["reasons"] if r["kind"] == "risk"]
    return "\n".join([render("report_intro", lang, who=who)] + [f"- {x}" for x in risks] + ["", render("report_outro", lang)])


def run(req: AnalyzeRequest, image_bytes: bytes | None = None, extra_signals: tuple | list = (), sink=None) -> AnalyzeResponse:
    tr = Trace(sink)

    # ---- READ (fixed): text out of the input, personal details masked before anything else sees it
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

    # ---- AGENT: plan, use tools, observe, decide (or nothing, if no model is available)
    d = loop.run(redacted, req.language, req.postcode, tr)
    filled: list[str] = []
    if d.issuer is None:
        d.issuer, d.conf = T.TOOLS["classify.issuer"].fn(redacted)
        tr.call("read", "classify.issuer", f"issuer = {d.issuer} (confidence {d.conf})", {"issuer": d.issuer, "name": T.SOURCES.get(d.issuer, {}).get("name")})
        filled += ["classify_issuer"] if d.mode == "ai" else []
    if d.fields is None:
        d.fields = T.TOOLS["extract.fields"].fn(redacted)
        tr.call("read", "extract.fields", f"amount = {d.fields['amount']} · deadline = {d.fields['deadline']} · ref = {d.fields['reference']}",
            {"amount": d.fields["amount"], "deadline": d.fields["deadline"], "reference": d.fields["reference"]})
        filled += ["extract_fields"] if d.mode == "ai" else []
    issuer, f = d.issuer, d.fields

    # ---- VERIFY: the rules always run last as a floor; the agent's evidence (quotes that really appear) can only add concern
    tr.think("verify", "Final check: the rules run on the message together with the evidence the agent found." if d.signals
             else "Before explaining anything, I must check this is not a scam.")
    memo = _Memo()
    verdict = memo.call("scam.check", redacted, issuer, req.language, tuple(extra_signals), tuple(d.signals))
    en = memo.call("scam.check", redacted, issuer, "en", tuple(extra_signals), tuple(d.signals))  # trace stays English; same args as above run once
    tr.call("verify", "scam.check", "domain allowlist · red-flag rules · reference pattern" + (" · agent evidence" if d.signals else ""))
    for g in en["good_signs"]:
        tr.note("verify", "ok", "✓ " + g)
    for r in en["red_flags"]:
        tr.note("verify", "bad", "✗ " + r)
    genuine = verdict["genuine"]
    if d.mode == "ai" and d.assessment and d.assessment != verdict["verdict"]:
        tr.note("verify", "warn", f"the agent concluded '{d.assessment}', the evidence-checked verdict is '{verdict['verdict']}'; the verdict follows the checked evidence")
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

    # ---- ACT (human-in-the-loop): the base draft, plus what the agent chose to prepare. Nothing is sent or paid.
    act = T.TOOLS["act.draft"].fn(issuer, f, genuine, req.language)
    tr.call("act", "act.draft", "draft prepared" + (f" · reminder {act['reminder']}" if act["reminder"] else ""))
    extra = []
    for kind, title, text in d.extras:
        if kind == "family_warning" and genuine:
            tr.note("act", "warn", "dropped the relatives' warning the agent prepared: the checked verdict is not a scam")
            continue
        extra.append(ExtraDraft(kind=kind, title=title, text=text))
        tr.call("act", "prepare_draft", f"{kind} (the agent's choice)")
    if "scam_report" in d.wants and not genuine:
        extra.append(ExtraDraft(kind="scam_report", title=render("report_h", req.language), text=_report(req.language, issuer, verdict)))
        tr.call("act", "prepare_draft", "scam_report built from the final findings")
    files = []
    for fname, mime, content in d.attachments:
        if not genuine:
            tr.note("act", "warn", f"dropped {fname}: a reminder for a likely scam makes no sense")
            continue
        files.append(Attachment(filename=fname, mime=mime, content=content))
        tr.call("act", "prepare_draft", f"{fname} (calendar file, the agent's choice)")
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
        action=Action(draft=act["draft"], reminder=act["reminder"], extra=extra, attachments=files),
        trace=tr.steps,
        agent=AgentInfo(mode=d.mode, rounds=d.rounds, plan=d.plan, tools=list(dict.fromkeys(d.used)), network=d.net,
                        signals=len(d.signals), refused=d.refused, assessment=d.assessment, summary=d.summary,
                        doubts=d.doubts, filled=filled),
    )
    cache.ANALYSES.set(key, resp.model_copy(deep=True))
    return resp
