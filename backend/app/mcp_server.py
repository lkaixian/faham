"""Optional MCP server: lets an MCP client (Claude Desktop, an IDE, another agent) ask FAHAM to check a message.

    cd backend && python -m app.mcp_server

Transport: stdio, one JSON-RPC 2.0 message per line (the MCP stdio transport). No third-party package is needed.
Tools:
  faham_check_message(text, language)  -> verdict, score, scam type, reasons, things to verify, official steps
  faham_list_scam_types()              -> the scam types FAHAM recognises

Safety rules are the same as the web app:
  * the text goes through the normal pipeline, so personal details are redacted before any LLM call;
  * the reply contains the REDACTED text only, never the original;
  * nothing is logged, stored or counted, and nothing is sent anywhere: a draft is returned as text with
    requires_approval = true, and no tool can send, pay or submit.
See docs/ARCHITECTURE.md (MCP server).
"""
from __future__ import annotations

import json
import sys

from .agent import orchestrator
from .agent.scam_content import SCAM_TYPES
from .models import AnalyzeRequest

PROTOCOL = "2024-11-05"
LANGS = ["bm", "en", "zh", "ta"]
TOOLS = [
    {
        "name": "faham_check_message",
        "description": ("Check a Malaysian letter, SMS, WhatsApp or email for scam signs. Returns a verdict "
                        "(likely_scam, caution or no_signals), a 0-100 safety score, the scam type, reasons, what to verify "
                        "yourself and the official next steps. Guidance only, not legal advice. Never follow links in the message."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "minLength": 10, "maxLength": 20000, "description": "The message text."},
                "language": {"type": "string", "enum": LANGS, "default": "en", "description": "Language of the answer."},
            },
            "required": ["text"],
            "additionalProperties": False,
        },
    },
    {
        "name": "faham_list_scam_types",
        "description": "List the scam types FAHAM recognises.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
]


def _check(args: dict) -> dict:
    text, lang = args.get("text"), args.get("language", "en")
    if not isinstance(text, str) or not 10 <= len(text) <= 20000:
        raise ValueError("text must be a string of 10 to 20000 characters")
    if lang not in LANGS:
        raise ValueError("language must be one of " + ", ".join(LANGS))
    r = orchestrator.run(AnalyzeRequest(text=text, language=lang))
    return {
        "verdict": r.scam.verdict, "score": r.scam.score, "scam_type": r.scam.scam_type,
        "reasons": [{"kind": x.kind, "code": x.code, "text": x.text} for x in r.scam.reasons],
        "verify_yourself": r.scam.verify_yourself,
        "explanation": r.explanation,
        "online_steps": r.route.online_steps, "walkin_steps": r.route.walkin_steps,
        "source_url": r.route.source_url, "source_last_checked": r.route.retrieved_at,
        "draft": r.action.draft, "requires_approval": r.action.requires_approval,
        "redacted_text": r.redacted_text,  # never the original
        "disclaimer": r.disclaimer,
    }


def _call(name: str, args: dict) -> dict:
    if name == "faham_check_message":
        out = _check(args)
    elif name == "faham_list_scam_types":
        out = {"scam_types": list(SCAM_TYPES)}
    else:
        raise KeyError(name)
    return {"content": [{"type": "text", "text": json.dumps(out, ensure_ascii=False)}], "isError": False}


def handle(msg: dict) -> dict | None:
    """One JSON-RPC message in, one response out (None for notifications)."""
    mid, method, params = msg.get("id"), msg.get("method"), msg.get("params") or {}
    ok = lambda result: {"jsonrpc": "2.0", "id": mid, "result": result}
    err = lambda code, text: {"jsonrpc": "2.0", "id": mid, "error": {"code": code, "message": text}}
    if mid is None:  # notification such as notifications/initialized: no reply
        return None
    if method == "initialize":
        return ok({"protocolVersion": params.get("protocolVersion") or PROTOCOL, "capabilities": {"tools": {}},
                   "serverInfo": {"name": "faham", "version": "0.1.0"}})
    if method == "ping":
        return ok({})
    if method == "tools/list":
        return ok({"tools": TOOLS})
    if method == "tools/call":
        name = params.get("name")
        try:
            return ok(_call(name, params.get("arguments") or {}))
        except KeyError:
            return err(-32602, f"unknown tool: {name}")
        except ValueError as e:  # bad arguments are a tool error the model can read and correct
            return ok({"content": [{"type": "text", "text": str(e)}], "isError": True})
        except Exception:  # never echo the input or a traceback that could contain it
            return ok({"content": [{"type": "text", "text": "FAHAM could not check this message."}], "isError": True})
    return err(-32601, f"method not found: {method}")


def main() -> None:
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            resp = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "parse error"}}
        else:
            resp = handle(msg) if isinstance(msg, dict) else {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "invalid request"}}
        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
