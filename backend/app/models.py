"""Typed request/response models for the Tulen API."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator

Language = Literal["bm", "en", "zh", "ta"]
Stage = Literal["read", "plan", "agent", "verify", "explain", "teach", "route", "act"]
TraceKind = Literal["think", "tool", "ok", "bad", "warn"]


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=3000)
    language: Language = "bm"


class AnalyzeRequest(BaseModel):
    text: str = Field("", max_length=20000, description="Letter text (pasted). Optional if image_b64 is given.")
    image_b64: Optional[str] = Field(None, max_length=6_000_000, description="Base64 PNG/JPEG of the letter (max ~6 MB).")
    language: Language = "bm"
    postcode: Optional[str] = Field(None, pattern=r"^\d{1,5}$", description="Used to find the nearest office.")
    sample_id: Optional[str] = Field(None, description="ID of a bundled fictional sample, if used.")

    @model_validator(mode="after")
    def _need_input(self):
        if len(self.text) < 10 and not self.image_b64:
            raise ValueError("Provide text of at least 10 characters or image_b64")
        return self


class TraceStep(BaseModel):
    stage: Stage
    kind: TraceKind
    message: str
    tool: Optional[str] = None
    flag: bool = False
    facts: Optional[dict] = None  # structured result of a tool call, so the page can say it in plain words and in any language


class Fields(BaseModel):
    issuer: str = "Unknown"
    letter_type: str = "Unknown"
    amount: Optional[str] = None
    deadline: Optional[str] = None
    reference: Optional[str] = None


class Reason(BaseModel):
    kind: Literal["risk", "ok", "info"]
    text: str
    code: Optional[str] = None  # stable key, e.g. "urgency"; same in every language
    evidence: list[str] = []  # exact snippets of the checked text behind this reason, for highlighting


class ScamVerdict(BaseModel):
    genuine: bool  # = (verdict != "likely_scam"): means 'not flagged', not 'proven genuine'
    verdict: Literal["likely_scam", "caution", "no_signals"] = "caution"
    score: int = Field(..., ge=0, le=100)
    red_flags: list[str] = []
    good_signs: list[str] = []
    reasons: list[Reason] = []
    verify_yourself: list[str] = []
    scam_type: Optional[Literal["macau", "family_impersonation", "parcel", "job", "love", "investment",
                                "phishing_refund", "apk_install", "whatsapp_file", "other"]] = None  # set when the verdict is not "no_signals"


class Route(BaseModel):
    online_steps: list[str]
    walkin_steps: list[str]
    prepare_online: list[str]
    prepare_walkin: list[str]
    source_url: str
    retrieved_at: str
    confidence: Literal["High", "Medium", "Low"]


class Lesson(BaseModel):
    question: str
    answer: str
    terms: list[str]


class ExtraDraft(BaseModel):
    kind: str
    title: str
    text: str


class Attachment(BaseModel):
    filename: str
    mime: str
    content: str  # text, for example a calendar file the user may download


class Action(BaseModel):
    draft: str
    reminder: Optional[str] = None
    requires_approval: bool = True
    extra: list[ExtraDraft] = []  # drafts the agent chose to prepare (always need approval)
    attachments: list[Attachment] = []  # files the agent made for the user to download


class AgentInfo(BaseModel):
    mode: Literal["ai", "rules"] = "rules"  # "ai": the agent loop ran; "rules": plain rule pipeline (no model available)
    rounds: int = 0  # rounds of think, act, observe
    plan: list[str] = []  # the agent's final plan
    tools: list[str] = []  # tools it used, in order
    network: int = 0  # calls it made to the outside world (official pages, domain records)
    signals: int = 0  # extra scam signals it found that passed the quote check
    refused: int = 0  # proposals the guard rails rejected
    assessment: Optional[str] = None  # what the agent itself concluded
    summary: Optional[str] = None  # its reasoning in one or two sentences
    doubts: list[str] = []  # what could make it wrong
    filled: list[str] = []  # steps the agent skipped that the harness had to do for it


class Entities(BaseModel):
    """Details found in the message, for display and the Semak Mule shortcut only. Never stored."""
    accounts: list[str] = []
    phones: list[str] = []
    companies: list[str] = []


class AnalyzeResponse(BaseModel):
    redacted_text: str
    fields: Fields
    scam: ScamVerdict
    explanation: str
    lesson: Lesson
    route: Route
    action: Action
    trace: list[TraceStep]
    entities: Optional[Entities] = None  # raw details from this request only; not cached, not stored
    others_checked: int = 0  # how many other people checked a similar message (fingerprint counter)
    agent: AgentInfo = AgentInfo()
    disclaimer: str = "Tulen gives guidance, not legal advice. Verify on the official source shown."


class PracticeItem(BaseModel):
    sender: str
    channel: str
    text: str
    is_scam: bool
    clues: list[str]
    agent: Optional[ScamVerdict] = None  # what the real agent says about this text


class FileResult(BaseModel):
    name: str
    kind: str
    status: Literal["ok", "skipped", "error"]
    detail: Optional[str] = None
    warnings: list[str] = []
    sha256: Optional[str] = None  # fingerprint of an inspected file, for the person to look up on a scanner they choose
    result: Optional[AnalyzeResponse] = None


class BatchSummary(BaseModel):
    total: int = 0
    analysed: int = 0
    likely_scam: int = 0
    caution: int = 0
    no_signals: int = 0
    skipped: int = 0


class BatchResponse(BaseModel):
    files: list[FileResult]
    summary: BatchSummary
