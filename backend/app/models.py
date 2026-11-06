"""Typed request/response models for the FAHAM API."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

Language = Literal["bm", "en", "zh", "ta"]
Stage = Literal["read", "verify", "explain", "teach", "route", "act"]
TraceKind = Literal["think", "tool", "ok", "bad", "warn"]


class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=20000, description="Letter text (from OCR or pasted).")
    language: Language = "bm"
    postcode: Optional[str] = Field(None, pattern=r"^\d{1,5}$", description="Used to find the nearest office.")
    sample_id: Optional[str] = Field(None, description="ID of a bundled fictional sample, if used.")


class TraceStep(BaseModel):
    stage: Stage
    kind: TraceKind
    message: str
    tool: Optional[str] = None
    flag: bool = False


class Fields(BaseModel):
    issuer: str = "Unknown"
    letter_type: str = "Unknown"
    amount: Optional[str] = None
    deadline: Optional[str] = None
    reference: Optional[str] = None


class ScamVerdict(BaseModel):
    genuine: bool
    score: int = Field(..., ge=0, le=100)
    red_flags: list[str] = []
    good_signs: list[str] = []


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


class Action(BaseModel):
    draft: str
    reminder: Optional[str] = None
    requires_approval: bool = True


class AnalyzeResponse(BaseModel):
    redacted_text: str
    fields: Fields
    scam: ScamVerdict
    explanation: str
    lesson: Lesson
    route: Route
    action: Action
    trace: list[TraceStep]
    disclaimer: str = "FAHAM gives guidance, not legal advice. Verify on the official source shown."


class PracticeItem(BaseModel):
    sender: str
    channel: str
    text: str
    is_scam: bool
    clues: list[str]
