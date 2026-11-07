"""The one place where untrusted bytes are parsed: in a limited child process, never in the API process.

Why: PDF, Word, email, archive and image parsers all take hostile input, and a bug in one (an endless loop, a memory blow-up, a crash)
should only hurt a process that is about to be thrown away. Three jobs run here: `inspect` (file-safety checks), `extract` (letters:
PDF, DOCX, text, email) and `ocr` (images). Each has a CPU limit, a memory limit, a file-size limit, a hard timeout and an environment
with no keys or secrets; at most TULEN_WORKERS run at once, the rest wait briefly and then get "busy". A child that crashes, hangs or
prints nonsense is reported as "could not be read safely", never as an error page and never as "fine".
`prlimit` (Linux) enforces the limits; where it is missing (Windows development) only the timeout applies.
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys
import threading
from pathlib import Path

log = logging.getLogger("faham.sandbox")
IN_WORKER = os.environ.get("TULEN_WORKER") == "1"  # inside the child: do the work directly instead of starting another child
ROOT = Path(__file__).resolve().parent.parent
MB = 1024 * 1024
# mode -> (timeout s, cpu s, address space bytes, largest file it may write). inspect cannot write a file at all; extract and ocr may
# write small temporary files (tesseract does), in RAM-backed /tmp.
LIMITS = {"inspect": (10, 8, 1024 * MB, 0), "extract": (30, 25, 2048 * MB, 64 * MB), "ocr": (30, 25, 2048 * MB, 64 * MB)}
KEEP_ENV = ("PATH", "SYSTEMROOT", "LANG", "LC_ALL", "TMPDIR", "TEMP", "TMP", "TESSDATA_PREFIX")  # no API keys, tokens or webhook secrets
SLOT_WAIT_S = 15
_slots = threading.BoundedSemaphore(max(1, int(os.getenv("TULEN_WORKERS", "4"))))


class Busy(Exception):
    """Every worker slot stayed taken for SLOT_WAIT_S."""


class Failed(Exception):
    """The child crashed, hung, ran out of its limits or printed nonsense."""


def _cmd(mode: str) -> list[str]:
    run = [sys.executable, "-B", "-s", "-m", "app.inspect_worker"]
    limits = shutil.which("prlimit")
    if not limits:
        return run
    _, cpu, mem, fsize = LIMITS[mode]
    return [limits, f"--cpu={cpu}", f"--as={mem}", f"--fsize={fsize}", *run]


def _run(mode: str, meta: dict, data: bytes) -> dict:
    env = {k: v for k, v in os.environ.items() if k in KEEP_ENV}
    env.update(PYTHONDONTWRITEBYTECODE="1", TULEN_WORKER="1", OMP_THREAD_LIMIT="1")
    header = json.dumps({**meta, "mode": mode}).encode() + b"\n"
    if not _slots.acquire(timeout=SLOT_WAIT_S):
        raise Busy()
    try:
        p = subprocess.run(_cmd(mode), input=header + data, capture_output=True, timeout=LIMITS[mode][0], cwd=ROOT, env=env)
        if p.returncode != 0:
            raise ValueError("worker exit code %d" % p.returncode)
        return json.loads(p.stdout.decode("utf-8"))
    except (subprocess.TimeoutExpired, OSError, ValueError) as e:
        log.warning("%s failed in the child: %s", mode, type(e).__name__)
        raise Failed(type(e).__name__) from None
    finally:
        _slots.release()


def inspect_isolated(filename: str | None, data: bytes, via_chat: bool = False) -> tuple[str, list[str], list[str], str]:
    """filecheck.inspect, computed in a child. If the child fails the file counts as unreadable: a sign, never an error page."""
    if IN_WORKER:
        from . import filecheck
        return filecheck.inspect(filename, data, via_chat)
    try:
        o = _run("inspect", {"filename": filename, "via_chat": via_chat}, data)
        return o["label"], list(o["inner"]), list(o["codes"]), str(o["facts"])
    except (Failed, KeyError):
        return "file", [], ["file_unreadable"], ""


def extract_isolated(filename: str | None, content_type: str | None, data: bytes, via_chat: bool = False) -> dict:
    """ingest.extract, computed in a child: {"docs": [...]} or {"error": {"status", "detail"}}. Raises Busy or Failed."""
    return _run("extract", {"filename": filename, "content_type": content_type, "via_chat": via_chat}, data)


def ocr_isolated(image: bytes) -> str:
    """Text from an image, read by tesseract and PIL in a child. Empty when OCR is unavailable, busy or failed."""
    if IN_WORKER:
        from .agent import tools
        return tools.tesseract(image)
    try:
        return str(_run("ocr", {}, image).get("text", ""))
    except (Busy, Failed):
        return ""
