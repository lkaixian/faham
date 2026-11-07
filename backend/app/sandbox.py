"""Run the file inspection in a limited child process, so a hostile file can only hurt a process that is about to be thrown away.

What the child gets: a CPU limit, a memory limit, a zero file-size limit (it cannot write a file), a hard timeout, and an
environment with no keys or secrets. If the child crashes, hangs or prints nonsense the result is "could not read this file",
which is a sign in itself, never an error page. Where `prlimit` does not exist (Windows development) only the timeout applies.
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

log = logging.getLogger("faham.sandbox")
TIMEOUT_S, CPU_S, MEM_BYTES = 10, 8, 1024 * 1024 * 1024
ROOT = Path(__file__).resolve().parent.parent
KEEP_ENV = ("PATH", "SYSTEMROOT", "LANG", "LC_ALL")  # nothing else: no API keys, tokens or webhook secrets reach the child
FAILED = ("file", [], ["file_unreadable"], "")


def _cmd() -> list[str]:
    run = [sys.executable, "-B", "-s", "-m", "app.inspect_worker"]
    limits = shutil.which("prlimit")
    return [limits, f"--cpu={CPU_S}", f"--as={MEM_BYTES}", "--fsize=0", *run] if limits else run


def inspect_isolated(filename: str | None, data: bytes, via_chat: bool = False) -> tuple[str, list[str], list[str], str]:
    """Same result as filecheck.inspect, computed in a child process."""
    env = {k: v for k, v in os.environ.items() if k in KEEP_ENV}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    header = json.dumps({"filename": filename, "via_chat": via_chat}).encode() + b"\n"
    try:
        p = subprocess.run(_cmd(), input=header + data, capture_output=True, timeout=TIMEOUT_S, cwd=ROOT, env=env)
        out = json.loads(p.stdout.decode("utf-8"))
        if p.returncode != 0:
            raise ValueError("worker exit code %d" % p.returncode)
        return out["label"], list(out["inner"]), list(out["codes"]), str(out["facts"])
    except (subprocess.TimeoutExpired, OSError, ValueError, KeyError) as e:
        log.warning("file inspection failed in the child: %s", type(e).__name__)
        return FAILED
