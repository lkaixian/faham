"""FAHAM API — FastAPI entrypoint.

Run:  uvicorn app.main:app --reload --port 8000
Docs: http://localhost:8000/docs
"""
import base64
import binascii
import json
import queue
import random
import threading

from urllib.parse import unquote

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from . import channels, config, ingest, tts
from .agent import orchestrator
from .agent.tools import TOOLS, classify_issuer, redact, scam_check
from .models import AnalyzeRequest, AnalyzeResponse, BatchResponse, Language, PracticeItem, TTSRequest

app = FastAPI(
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


def _decode_image(req: AnalyzeRequest) -> bytes | None:
    if not req.image_b64:
        return None
    try:
        image = base64.b64decode(req.image_b64, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(422, "image_b64 is not valid base64")
    if not image.startswith((b"\x89PNG\r\n\x1a\n", b"\xff\xd8\xff")):
        raise HTTPException(422, "image must be PNG or JPEG")
    return image


@app.post("/api/analyze/stream")
def analyze_stream(req: AnalyzeRequest):
    """Same agent run as /api/analyze, as server-sent events: one `step` per thought, tool call and finding as it happens,
    then `result` (the full response) or `error`. Lets the page show the agent working instead of a spinner."""
    image = _decode_image(req)
    q: queue.Queue = queue.Queue()

    def work():
        try:
            q.put(("result", orchestrator.run(req, image, sink=lambda s: q.put(("step", s))).model_dump_json()))
        except orchestrator.OCRUnavailable as e:
            q.put(("error", json.dumps({"status": 422, "detail": str(e)})))
        except Exception:
            q.put(("error", json.dumps({"status": 500, "detail": "analysis failed"})))
        q.put(None)

    threading.Thread(target=work, daemon=True).start()

    def events():
        while (item := q.get()) is not None:
            kind, payload = item
            yield f"event: {kind}\ndata: {payload.model_dump_json() if kind == 'step' else payload}\n\n"
    return StreamingResponse(events(), media_type="text/event-stream", headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"})


async def _file_body(request: Request) -> bytearray:
    cl = request.headers.get("content-length", "")
    if cl.isdigit() and int(cl) > ingest.MAX_BODY:
        raise HTTPException(413, "File is larger than 25 MB")
    buf = bytearray()
    async for chunk in request.stream():
        buf += chunk
        if len(buf) > ingest.MAX_BODY:
            raise HTTPException(413, "File is larger than 25 MB")
    return buf


def _file_run(request: Request, buf: bytearray, language: str, postcode: str | None, sink=None):
    docs = ingest.extract(unquote(request.headers.get("x-filename", "")) or None,
                          request.headers.get("content-type"), bytes(buf))
    return ingest.analyze_files(docs, language, postcode, sink)


@app.post("/api/analyze-file", response_model=BatchResponse)
async def analyze_file(request: Request, language: Language = Query("bm"),
                       postcode: str | None = Query(None, pattern=r"^\d{1,5}$")):
    """Raw file bytes as the body (no multipart). Headers: X-Filename, Content-Type. Nothing is stored."""
    buf = await _file_body(request)
    try:
        return await run_in_threadpool(_file_run, request, buf, language, postcode)
    except ingest.IngestError as e:
        raise HTTPException(e.status, e.detail)


@app.post("/api/analyze-file/stream")
async def analyze_file_stream(request: Request, language: Language = Query("bm"),
                              postcode: str | None = Query(None, pattern=r"^\d{1,5}$")):
    """Same as /api/analyze-file, as server-sent events: `step` per agent step, then `result` (the BatchResponse) or `error`."""
    buf = await _file_body(request)
    q: queue.Queue = queue.Queue()

    def work():
        try:
            q.put(("result", _file_run(request, buf, language, postcode, lambda s: q.put(("step", s))).model_dump_json()))
        except ingest.IngestError as e:
            q.put(("error", json.dumps({"status": e.status, "detail": e.detail})))
        except Exception:
            q.put(("error", json.dumps({"status": 500, "detail": "analysis failed"})))
        q.put(None)

    threading.Thread(target=work, daemon=True).start()

    def events():
        while (item := q.get()) is not None:
            kind, payload = item
            yield f"event: {kind}\ndata: {payload.model_dump_json() if kind == 'step' else payload}\n\n"
    return StreamingResponse(events(), media_type="text/event-stream", headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"})


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
