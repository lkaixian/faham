"""Security hardening and architecture guards. Each test pins one decision so it cannot quietly regress."""
import re
import socket
from pathlib import Path

import pytest

from app import filecheck, ingest, limiter, sandbox
from app.agent import loop, tools
from app.agent.i18n import TEXT
from tests.test_filecheck import client, docx_zip, zipped

APP = Path(__file__).resolve().parent.parent / "app"
ROOT = APP.parent.parent


# ---------------------------------------------------------------- SSRF: the agent fetches only public addresses
def fake_dns(monkeypatch, mapping):
    def getaddrinfo(host, port, *a, **kw):
        return [(socket.AF_INET6 if ":" in ip else socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, port)) for ip in mapping[host]]
    monkeypatch.setattr(loop.socket, "getaddrinfo", getaddrinfo)


@pytest.mark.parametrize("ip", ["127.0.0.1", "10.1.2.3", "172.16.0.9", "192.168.1.1", "169.254.169.254", "0.0.0.0", "::1", "fe80::1", "224.0.0.1", "100.64.0.1"])
def test_non_public_addresses_are_refused(monkeypatch, ip):
    fake_dns(monkeypatch, {"x.edu.my": [ip]})
    with pytest.raises(loop.ToolError):
        loop._public_ips("x.edu.my", 443)


def test_one_private_answer_among_public_ones_refuses_the_host(monkeypatch):
    fake_dns(monkeypatch, {"x.edu.my": ["8.8.8.8", "10.0.0.5"]})  # a DNS answer mixing both is how rebinding tricks start
    with pytest.raises(loop.ToolError):
        loop._public_ips("x.edu.my", 443)
    fake_dns(monkeypatch, {"x.edu.my": ["8.8.8.8", "2606:4700:10::1"]})
    assert loop._public_ips("x.edu.my", 443) == ["8.8.8.8", "2606:4700:10::1"]


def test_a_trusted_looking_host_that_points_inside_is_not_fetched(monkeypatch):
    fake_dns(monkeypatch, {"student.uni.edu.my": ["10.0.0.5"]})  # any .edu.my name counts as official, and anyone can run one
    d = loop.Dossier(letter="x", language="en", postcode=None)
    with pytest.raises(loop.ToolError, match="not a public website"):
        loop.t_fetch_official_page(d, "https://student.uni.edu.my/page")


def test_redirects_are_checked_on_every_hop():
    with pytest.raises(loop.ToolError, match="redirects away"):
        loop._Hop().redirect_request(None, None, 302, "Found", {}, "https://evil.example/")
    with pytest.raises(loop.ToolError):
        loop._Hop().redirect_request(None, None, 302, "Found", {}, "http://www.hasil.gov.my/")  # https only


# ---------------------------------------------------------------- untrusted bytes are parsed in the child, never in the API process
def test_no_route_parses_a_file_in_the_api_process():
    for p in APP.rglob("*.py"):
        if p.name in ("inspect_worker.py", "ingest.py", "sandbox.py"):
            continue
        assert "ingest.extract(" not in p.read_text(encoding="utf-8"), f"{p.name} calls ingest.extract directly: use extract_safe"
    assert "tesseract(" not in (APP / "main.py").read_text(encoding="utf-8")


def test_an_upload_is_extracted_by_the_child_not_the_parent(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("the API process parsed the file itself")
    monkeypatch.setattr(ingest, "extract", boom)
    r = client.post("/api/analyze-file?language=en", content=docx_zip(), headers={"X-Filename": "letter.docx"})
    assert r.status_code == 200 and r.json()["files"][0]["status"] == "ok"


def test_a_failing_child_is_refused_not_passed_and_not_a_500(monkeypatch):
    def crash(*a, **k):
        raise sandbox.Failed("TimeoutExpired")
    monkeypatch.setattr(sandbox, "_run", crash)
    r = client.post("/api/analyze-file?language=en", content=docx_zip(), headers={"X-Filename": "letter.docx"})
    assert r.status_code == 422 and "could not be read safely" in r.json()["detail"]
    monkeypatch.setattr(sandbox, "_run", lambda *a, **k: (_ for _ in ()).throw(sandbox.Busy()))
    r = client.post("/api/analyze-file?language=en", content=docx_zip(), headers={"X-Filename": "letter.docx"})
    assert r.status_code == 503


def test_child_output_is_not_trusted_blindly(monkeypatch):
    evil = {"docs": [{"name": "a" * 5000, "kind": "text", "text": "hello there world", "warnings": ["w"] * 99, "signals": ["file_checked"] * 99,
                      "sha256": "f" * 500, "image": None}] * 80}
    monkeypatch.setattr(sandbox, "extract_isolated", lambda *a, **k: evil)
    docs = ingest.extract_safe("a.txt", None, b"x")
    assert len(docs) == 50 and len(docs[0].name) == 200 and len(docs[0].warnings) == 20 and len(docs[0].signals) == 40 and len(docs[0].sha256) == 64


def test_the_worker_gets_no_secrets_and_ocr_runs_in_the_child(monkeypatch):
    seen = []
    monkeypatch.setattr(sandbox, "_run", lambda mode, meta, data: seen.append(mode) or {"text": "TEKS DARIPADA GAMBAR"})
    assert tools.ocr_read(image_bytes=b"\x89PNG....") == "TEKS DARIPADA GAMBAR" and seen == ["ocr"]
    monkeypatch.setattr(sandbox, "_run", lambda *a, **k: (_ for _ in ()).throw(sandbox.Failed("x")))
    assert tools.ocr_read(text="fallback", image_bytes=b"x") == "fallback"  # a failed child never raises into the request
    assert set(sandbox.KEEP_ENV).isdisjoint({"ANTHROPIC_API_KEY", "ILMU_API_KEY", "EMAIL_WEBHOOK_SECRET", "MESSENGER_APP_SECRET"})


def test_every_job_has_limits_and_inspect_cannot_write():
    assert set(sandbox.LIMITS) == {"inspect", "extract", "ocr"}
    timeout, cpu, mem, fsize = sandbox.LIMITS["inspect"]
    assert fsize == 0 and timeout <= 10 and cpu <= timeout and mem <= 2 * 1024**3
    assert all(v[0] > 0 and v[1] > 0 and v[2] > 0 for v in sandbox.LIMITS.values())


def test_file_routes_share_the_request_limiter(monkeypatch):
    class Full:
        def slot(self, patience=0):
            raise limiter.Busy()
    monkeypatch.setattr(limiter, "LIMITER", Full())
    r = client.post("/api/analyze-file?language=en", content=docx_zip(), headers={"X-Filename": "letter.docx"})
    assert r.status_code == 503 and r.headers["retry-after"] == "5"


# ---------------------------------------------------------------- one source of truth for file signals
def test_every_file_code_in_the_code_base_is_classified_and_translated():
    emitted = set()
    for name in ("filecheck.py", "office.py", "payload.py", "ingest.py"):
        emitted |= set(re.findall(r'"(file_[a-z_]+)"', (APP / name).read_text(encoding="utf-8")))
    emitted -= {"file_risk"}  # that is the name of a file KIND in ingest, not a signal
    weak, strong, info = filecheck.FILE_WEAK, filecheck.FILE_STRONG, filecheck.FILE_INFO
    assert not (weak & strong or weak & info or strong & info), "a code is in two tiers"
    assert emitted <= weak | strong | info, f"unclassified: {emitted - (weak | strong | info)}"
    assert tools.FILE_WEAK is weak and tools.FILE_STRONG is strong and tools.FILE_INFO is info  # tools.py reads the lists, it does not copy them
    for c in weak | strong | info:
        assert set(TEXT[c]) == {"en", "bm", "zh", "ta"} and all(TEXT[c].values()), c


# ---------------------------------------------------------------- web server and containers
def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


@pytest.mark.parametrize("conf", ["frontend/nginx.conf", "frontend/nginx.dev.conf"])
def test_nginx_headers_and_private_api_responses(conf):
    s = read(conf)
    for h in ("Content-Security-Policy", "X-Content-Type-Options", "Referrer-Policy", "Permissions-Policy", "Cross-Origin-Opener-Policy"):
        assert h in s, h
    assert "frame-ancestors 'none'" in s and "script-src" not in s.replace("default-src 'self'", "")  # scripts only from our own origin
    assert s.count('add_header Cache-Control "no-store"') == 2  # the stream route and /api/: analysis results are private
    assert "limit_req zone=faham_api" in s and "client_max_body_size" in s


def test_compose_hardens_both_services():
    s = read("docker-compose.yml")
    for key in ("read_only: true", "cap_drop: [ALL]", 'no-new-privileges:true', "mem_limit:", "pids_limit:"):
        assert s.count(key) >= 2, key  # api and web
    assert '127.0.0.1:8000:8000' in s  # the API itself is not published on every interface


def test_ci_audits_dependencies_with_a_read_only_token():
    s = read(".github/workflows/ci.yml")
    assert "pip-audit" in s and "contents: read" in s and "schedule:" in s


def test_secrets_stay_out_of_git():
    gi = read(".gitignore")
    assert ".env" in gi and "!.env.example" in gi
    assert not re.search(r"(sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,})", read(".env.example"))


def test_zip_helper_still_builds():
    assert zipped({"a.txt": "x"})[:2] == b"PK"
