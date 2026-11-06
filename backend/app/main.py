"""FAHAM API — FastAPI entrypoint.

Run:  uvicorn app.main:app --reload --port 8000
Docs: http://localhost:8000/docs
"""
import base64
import binascii
import json
import random

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import config
from .agent import orchestrator
from .agent.tools import TOOLS, classify_issuer, redact, scam_check
from .models import AnalyzeRequest, AnalyzeResponse, PracticeItem

app = FastAPI(
    title="FAHAM Agent API",
    version="0.1.0",
    description="Agentic AI that reads official Malaysian letters, checks for scams, explains, teaches and prepares the next step.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS + (["null"] if config.ALLOW_NULL_ORIGIN else []),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

PRACTICE = json.loads((config.DATA_DIR / "practice.json").read_text(encoding="utf-8"))


@app.get("/api/health")
def health():
    return {"status": "ok", "llm_provider": config.LLM_PROVIDER,
            "llm_configured": config.LLM_PROVIDER != "none" and bool(config.ANTHROPIC_API_KEY), "tools": list(TOOLS)}


@app.get("/api/tools")
def list_tools():
    return [{"name": t.name, "description": t.description} for t in TOOLS.values()]


@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    """Run the full agent. The letter is processed in memory and not stored."""
    image = None
    if req.image_b64:
        try:
            image = base64.b64decode(req.image_b64, validate=True)
        except (binascii.Error, ValueError):
            raise HTTPException(422, "image_b64 is not valid base64")
        if not image.startswith((b"\x89PNG\r\n\x1a\n", b"\xff\xd8\xff")):
            raise HTTPException(422, "image must be PNG or JPEG")
    try:
        return orchestrator.run(req, image)
    except orchestrator.OCRUnavailable as e:
        raise HTTPException(422, str(e))


@app.get("/api/practice", response_model=list[PracticeItem])
def practice(n: int = 5):
    """A round of clearly fictional messages for Spot-the-scam."""
    items = random.sample(PRACTICE, k=min(n, len(PRACTICE)))
    out = []
    for i in items:
        red, _ = redact(i["text"])
        out.append(PracticeItem(**i, agent=scam_check(red, classify_issuer(red)[0])))
    return out
