"""ILMU text-to-speech proxy (POST {ILMU_BASE_URL}/audio/speech).

The API key stays on the server. The client may only send text it got back from
/api/analyze (already redacted); anything that still looks like PII is refused.
ILMU documents Malay, English and Mandarin only, so Tamil falls back to the
browser voice in the frontend.
"""
from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request

from . import config
from .llm import RESIDUAL_PII

log = logging.getLogger("faham.tts")

LANGS = {"bm": "ms", "en": "en", "zh": "zh"}
MAX_CHARS = 3000
# ponytail: one global window, not per client. Add per-IP limits if the API goes public.
RATE_PER_MIN = 30
_calls: list[float] = []


class TTSError(Exception):
    def __init__(self, status: int, detail: str):
        self.status, self.detail = status, detail


def available() -> bool:
    return bool(config.ILMU_API_KEY)


def speak(text: str, language: str) -> bytes:
    if not available():
        raise TTSError(503, "Text to speech is not configured")
    if language not in LANGS:
        raise TTSError(422, "This language has no ILMU voice, use the browser voice")
    if RESIDUAL_PII.search(text):
        raise TTSError(422, "Text still contains personal details, not sent")
    now = time.monotonic()
    _calls[:] = [t for t in _calls if now - t < 60]
    if len(_calls) >= RATE_PER_MIN:
        raise TTSError(429, "Too many requests, try again in a minute")
    _calls.append(now)
    body = json.dumps({"model": config.ILMU_TTS_MODEL, "input": text, "voice": config.ILMU_TTS_VOICE,
                       "language": LANGS[language], "response_format": "mp3"}).encode()
    req = urllib.request.Request(config.ILMU_BASE_URL + "/audio/speech", data=body, headers={
        "Content-Type": "application/json", "Authorization": "Bearer " + config.ILMU_API_KEY})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.read()
    except urllib.error.HTTPError as exc:
        log.warning("ILMU TTS HTTP %s", exc.code)
        raise TTSError(502, "Text to speech failed upstream")
    except Exception as exc:
        log.warning("ILMU TTS failed: %s", type(exc).__name__)
        raise TTSError(502, "Text to speech failed upstream")
