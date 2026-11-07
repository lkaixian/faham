"""Child process for sandbox.py: one job in on stdin, the answer out on stdout as JSON.

stdin is one JSON header line ({"mode": "inspect" | "extract" | "ocr", ...}) followed by the raw bytes. The parent runs this under
limits (CPU, memory, file size), a timeout and an environment with no secrets; see sandbox.py.
"""
from __future__ import annotations

import base64
import json
import sys


def main() -> None:
    header = json.loads(sys.stdin.buffer.readline())
    data = sys.stdin.buffer.read()
    mode = header.get("mode")
    if mode == "inspect":
        from . import filecheck  # imported late so a failure here is reported, not raised at start-up
        label, inner, codes, facts = filecheck.inspect(header.get("filename"), data, bool(header.get("via_chat")))
        out = {"label": label, "inner": inner, "codes": codes, "facts": facts}
    elif mode == "extract":
        from . import ingest
        try:
            docs = ingest.extract(header.get("filename"), header.get("content_type"), data, via_chat=bool(header.get("via_chat")))
            out = {"docs": [{"name": d.name, "kind": d.kind, "text": d.text, "warnings": d.warnings, "signals": d.signals, "sha256": d.sha256,
                             "image": base64.b64encode(d.image).decode("ascii") if d.image else None} for d in docs]}
        except ingest.IngestError as e:
            out = {"error": {"status": e.status, "detail": e.detail}}
    elif mode == "ocr":
        from .agent import tools
        out = {"text": tools.tesseract(data)}
    else:
        raise SystemExit(2)
    sys.stdout.write(json.dumps(out))


if __name__ == "__main__":
    main()
