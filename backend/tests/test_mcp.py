"""P4 item 23: the optional MCP server (stdlib JSON-RPC over stdio)."""
import json
import subprocess
import sys
from pathlib import Path

from app import mcp_server as M

BACKEND = Path(__file__).resolve().parents[1]
SCAM = "PDRM: waran tangkap dikeluarkan. Pindahkan wang ke akaun selamat 8001234567 sekarang. Jangan beritahu sesiapa. Hubungi 012-3456789."


def call(name, args, mid=1):
    return M.handle({"jsonrpc": "2.0", "id": mid, "method": "tools/call", "params": {"name": name, "arguments": args}})


def test_initialize_and_tools_list():
    r = M.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05"}})
    assert r["result"]["serverInfo"]["name"] == "faham" and "tools" in r["result"]["capabilities"]
    names = {t["name"] for t in M.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})["result"]["tools"]}
    assert names == {"faham_check_message", "faham_list_scam_types"}


def test_notification_gets_no_reply():
    assert M.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None


def test_check_message_returns_verdict_and_never_the_original_text():
    r = call("faham_check_message", {"text": SCAM, "language": "en"})["result"]
    assert r["isError"] is False
    out = json.loads(r["content"][0]["text"])
    assert out["verdict"] == "likely_scam" and out["scam_type"] == "macau" and out["requires_approval"] is True
    blob = r["content"][0]["text"]
    assert "8001234567" not in blob and "012-3456789" not in blob  # redacted before anything leaves the process
    assert "[PHONE]" in out["redacted_text"]


def test_bad_arguments_are_a_tool_error_not_a_crash():
    for args in ({"text": "short"}, {"text": SCAM, "language": "fr"}, {}):
        r = call("faham_check_message", args)["result"]
        assert r["isError"] is True


def test_unknown_tool_and_method():
    assert call("nope", {})["error"]["code"] == -32602
    assert M.handle({"jsonrpc": "2.0", "id": 9, "method": "x/y"})["error"]["code"] == -32601


def test_no_tool_can_send_or_pay():
    for t in M.TOOLS:
        assert not any(w in t["name"] for w in ("send", "pay", "submit", "transfer"))


def test_stdio_round_trip_in_a_real_process():
    lines = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
             {"jsonrpc": "2.0", "method": "notifications/initialized"},
             {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "faham_list_scam_types", "arguments": {}}}]
    p = subprocess.run([sys.executable, "-m", "app.mcp_server"], cwd=BACKEND, capture_output=True, timeout=60,
                       input=("\n".join(json.dumps(x) for x in lines) + "\nnot json\n").encode("utf-8"))
    out = [json.loads(x) for x in p.stdout.decode("utf-8").splitlines()]
    assert [o.get("id") for o in out] == [1, 2, None]  # initialize, tool call, parse error; the notification got nothing
    assert "macau" in out[1]["result"]["content"][0]["text"] and out[2]["error"]["code"] == -32700
