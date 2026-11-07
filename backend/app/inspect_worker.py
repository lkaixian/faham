"""Child process for sandbox.py: one file in on stdin, findings out on stdout as JSON.

stdin is one JSON header line ({"filename", "via_chat"}) followed by the raw file bytes. The parent runs this with a CPU limit, a
memory limit and a zero file-size limit (it cannot write a file), a short timeout and an environment with no secrets in it.
"""
from __future__ import annotations

import json
import sys


def main() -> None:
    header = json.loads(sys.stdin.buffer.readline())
    data = sys.stdin.buffer.read()
    from . import filecheck  # imported late so a failure here is reported, not raised at start-up

    label, inner, codes, facts = filecheck.inspect(header.get("filename"), data, bool(header.get("via_chat")))
    sys.stdout.write(json.dumps({"label": label, "inner": inner, "codes": codes, "facts": facts}))


if __name__ == "__main__":
    main()
