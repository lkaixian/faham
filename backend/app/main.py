"""FAHAM API — FastAPI entrypoint.

Run:  uvicorn app.main:app --reload --port 8000
Docs: http://localhost:8000/docs
"""
import base64
import binascii
import json
import random
import threading
import time
from contextlib import asynccontextmanager

from urllib.parse import unquote

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from . import channels, config, counter, ingest, limiter, tts
from .agent import orchestrator
from .agent.tools import TOOLS, classify_issuer, extract_entities, redact, scam_check
from .models import Entities, AnalyzeRequest, AnalyzeResponse, BatchResponse, Language, PracticeItem, TTSRequest

def _warm_cache() -> None:
    """Pre-run the bundled sample messages so the first tap on an example is instant. Skipped when an LLM is
    configured, so a restart never spends provider credit."""
    if config.llm_ready():
        return
    for item in PRACTICE:
        for lang in ("bm", "en", "zh", "ta"):
            try:
                orchestrator.run(AnalyzeRequest(text=item["text"], language=lang))
            except Exception:  # warming is best effort
                pass


@asynccontextmanager
async def lifespan(_app):
    threading.Thread(target=_warm_cache, daemon=True, name="warm-cache").start()
    yield


app = FastAPI(
    lifespan=lifespan,
    title="FAHAM Agent API",
    version="0.1.0",
    description="Agentic AI that reads official Malaysian letters, checks for scams, explains, teaches and prepares the next step.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS + (["null"] if config.ALLOW_NULL_ORIGIN else []),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Filename"],
)
app.include_router(channels.router)

PRACTICE = json.loads((config.DATA_DIR / "practice.json").read_text(encoding="utf-8"))


@app.get("/api/health")
def health():
    return {"status": "ok", "llm_provider": config.LLM_PROVIDER,
            "llm_configured": config.llm_ready(), "tools": list(TOOLS),
            "tts_available": tts.available(), "tts_languages": list(tts.LANGS),
            "upload": {"max_mb": ingest.MAX_BODY // 1024 // 1024,
                       "types": ["pdf", "docx", "txt", "md", "eml", "png", "jpg"]},
            "channels": channels.status()}


@app.post("/api/tts")
def speak(req: TTSRequest):
    """Read-aloud audio (mp3) for text the client got from /api/analyze."""
    try:
        return Response(tts.speak(req.text, req.language), media_type="audio/mpeg",
                        headers={"Cache-Control": "no-store"})
    except tts.TTSError as e:
        raise HTTPException(e.status, e.detail)


@app.get("/api/tools")
def list_tools():
    return [{"name": t.name, "description": t.description} for t in TOOLS.values()]


def _decode_image(b64: str | None) -> bytes | None:
    if not b64:
        return None
    try:
        image = base64.b64decode(b64, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(422, "image_b64 is not valid base64")
    if not image.startswith((b"\x89PNG\r\n\x1a\n", b"\xff\xd8\xff")):
        raise HTTPException(422, "image must be PNG or JPEG")
    return image


def _finish(req: AnalyzeRequest, res: AnalyzeResponse) -> AnalyzeResponse:
    """Add the per-request extras to a (possibly cached) analysis: the Semak Mule details come from this request's
    own text and are not cached; the "others checked" counter stores only a fingerprint of the redacted text."""
    res = res.model_copy(deep=True)
    if res.scam.verdict != "no_signals" and req.text.strip():
        res.entities = Entities(**extract_entities(req.text))
    if not req.sample_id:
        res.others_checked = counter.COUNTER.hit(res.redacted_text)
    return res


@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    """Run the full agent. The letter is processed in memory and not stored. Waits its turn when busy."""
    image = _decode_image(req.image_b64)
    try:
        with limiter.LIMITER.slot(patience=config.QUEUE_PATIENCE):
            return _finish(req, orchestrator.run(req, image))
    except orchestrator.OCRUnavailable as e:
        raise HTTPException(422, str(e))
    except limiter.Busy:
        raise HTTPException(503, "FAHAM is busy. Please try again in a moment.", headers={"Retry-After": "5"})


def _sse(event: str, data) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.post("/api/analyze/stream")
def analyze_stream(req: AnalyzeRequest):
    """Server-sent events: `queue` (place in line, only while waiting), `verdict` (rules only, fast),
    `explanation` (after the optional LLM), `result` (the full AnalyzeResponse), or `error`."""
    image = _decode_image(req.image_b64)
    t0 = time.monotonic()

    def events():
        lim = limiter.LIMITER
        ticket = lim.enter()
        got, first = False, True
        try:
            while not got:
                got = lim.acquire(ticket, 0 if first else 1.0)
                if not got:
                    yield _sse("queue", {"position": lim.position(ticket), "waiting": lim.waiting()})
                    if time.monotonic() - t0 > config.QUEUE_PATIENCE:
                        yield _sse("error", {"status": 503, "detail": "FAHAM is busy. Please try again in a moment."})
                        return
                first = False
            try:
                if (q := orchestrator.quick_verdict(req)) is not None:
                    yield _sse("verdict", q)
                res = _finish(req, orchestrator.run(req, image))
                yield _sse("explanation", {"text": res.explanation})
                yield _sse("result", res.model_dump())
            except orchestrator.OCRUnavailable as e:
                yield _sse("error", {"status": 422, "detail": str(e)})
            finally:
                lim.release()
        finally:
            lim.leave(ticket)  # no-op once admitted; frees the place if the client hung up while waiting

    return StreamingResponse(events(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"})


@app.post("/api/analyze-file", response_model=BatchResponse)
async def analyze_file(request: Request, language: Language = Query("bm"),
                       postcode: str | None = Query(None, pattern=r"^\d{1,5}$")):
    """Raw file bytes as the body (no multipart). Headers: X-Filename, Content-Type. Nothing is stored."""
    cl = request.headers.get("content-length", "")
    if cl.isdigit() and int(cl) > ingest.MAX_BODY:
        raise HTTPException(413, "File is larger than 25 MB")
    buf = bytearray()
    async for chunk in request.stream():
        buf += chunk
        if len(buf) > ingest.MAX_BODY:
            raise HTTPException(413, "File is larger than 25 MB")
    try:
        def work():
            docs = ingest.extract(unquote(request.headers.get("x-filename", "")) or None,
                                  request.headers.get("content-type"), bytes(buf))
            return ingest.analyze_files(docs, language, postcode)
        return await run_in_threadpool(work)
    except ingest.IngestError as e:
        raise HTTPException(e.status, e.detail)


@app.get("/api/practice", response_model=list[PracticeItem])
def practice(n: int = 5, lang: Language = Query("bm")):
    """A round of clearly fictional messages for Spot-the-scam. Clues and the agent verdict come back in `lang`."""
    items = random.sample(PRACTICE, k=min(n, len(PRACTICE)))
    out = []
    for i in items:
        red, _ = redact(i["text"])
        clues = i.get("clues_i18n", {}).get(lang, i["clues"])
        out.append(PracticeItem(**{k: v for k, v in i.items() if k != "clues_i18n"} | {"clues": clues},
                                agent=scam_check(red, classify_issuer(red)[0], lang)))
    return out
