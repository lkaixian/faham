import hashlib
import hmac
import json
from types import SimpleNamespace as NS

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import channels, ingest, reply

SECRET = "appsecret"
ENV = dict(MESSENGER_VERIFY_TOKEN="mv", MESSENGER_APP_SECRET=SECRET,
           MESSENGER_PAGE_TOKEN="pagetok", MESSENGER_PAGE_USERNAME="faham", FAHAM_PUBLIC_URL="https://faham.example")


def batch(verdict="likely_scam"):
    r = NS(scam=NS(verdict=verdict, verify_yourself=["Taip alamat rasmi sendiri", "Telefon talian rasmi", "tiga"],
                   reasons=[NS(kind="risk", text=f"sebab {i} http://evil.example/x") for i in range(4)]),
           route=NS(source_url="https://www.hasil.gov.my"))
    return NS(files=[NS(name="a", result=r)])


@pytest.fixture
def env(monkeypatch):
    for k, v in ENV.items():
        monkeypatch.setenv(k, v)
    for d in (channels._seen, channels._consent, channels._hits):
        d.clear()
    sent, calls = [], []

    def fake_json(url, payload):
        sent.append(payload)
        return {}
    monkeypatch.setattr(channels, "_json_req", fake_json)
    monkeypatch.setattr(channels, "_download", lambda url: calls.append(url) or (b"data", "image/png"))
    monkeypatch.setattr(ingest, "extract", lambda n, c, d, **k: [ingest.Doc(name=n, kind="image", text="x")])
    monkeypatch.setattr(ingest, "analyze_files", lambda docs, lang, pc: batch())
    app = FastAPI()
    app.include_router(channels.router)
    return TestClient(app), sent, calls


def post(client, path, payload, secret=SECRET, sign=True):
    raw = json.dumps(payload).encode()
    h = {"X-Hub-Signature-256": "sha256=" + hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()} if sign else {}
    return client.post(path, content=raw, headers=h)


def ms(text, mid="m1", atts=None):
    m = {"mid": mid, "text": text}
    if atts:
        m["attachments"] = atts
    return {"entry": [{"messaging": [{"sender": {"id": "9"}, "message": m}]}]}


def body(sent, i=-1):
    return sent[i]["message"]["text"]


URL = "/api/channels/messenger"


def test_handshake_and_unconfigured(env, monkeypatch):
    c, _, _ = env
    q = "?hub.mode=subscribe&hub.challenge=777&hub.verify_token="
    assert c.get(URL + q + "mv").text == "777"
    assert c.get(URL + q + "bad").status_code == 403
    monkeypatch.delenv("MESSENGER_APP_SECRET")
    assert c.get(URL + q + "mv").status_code == 404


def test_signature_enforced(env):
    c, sent, _ = env
    assert post(c, URL, ms("hi"), sign=False).status_code == 403
    assert post(c, URL, ms("hi"), secret="wrong").status_code == 403
    assert post(c, URL, ms("hi")).status_code == 200


def test_consent_gate_then_analysis_no_genuine_wording(env):
    c, sent, _ = env
    post(c, URL, ms("Sila bayar segera akaun anda", "a1"))
    assert len(sent) == 1 and "ILMU" in body(sent) and "OK" in body(sent)
    assert "Kemungkinan penipuan" not in body(sent)  # not analysed before consent
    post(c, URL, ms("OK", "a2"))
    post(c, URL, ms("Sila bayar segera akaun anda", "a3"))
    out = body(sent)
    assert out.startswith("Kemungkinan penipuan") and "997" in out and "bukan nasihat undang-undang" in out
    assert out.count("- sebab") == 3 and "Taip alamat" in out and "Telefon talian" in out and "tiga" not in out
    assert "evil.example" not in out and "https://www.hasil.gov.my" in out and len(out) <= 900
    assert not any(w in out.lower() for w in ("genuine", "sahih", "real", "—"))
    post(c, URL, ms("STOP", "a4"))
    post(c, URL, ms("hello again", "a5"))
    assert "ILMU" in body(sent, -1) or "OK" in body(sent)  # consent forgotten: asks again, no analysis
    assert "Kemungkinan" not in body(sent)


def test_english_reply_and_media_and_dedup(env):
    c, sent, calls = env
    img = [{"type": "image", "payload": {"url": "https://lookaside.fbsbx.com/m/1.png"}}]
    post(c, URL, ms("OK", "b0"))
    post(c, URL, ms("", "b1", img))
    n = len(sent)
    post(c, URL, ms("", "b1", img))  # same id: Meta retry
    assert len(sent) == n and len(calls) == 1
    post(c, URL, ms("Please pay your account now, this is urgent", "b2"))
    assert body(sent).startswith("Likely a scam")


def test_audio_attachment_gets_short_reply(env):
    c, sent, calls = env
    post(c, URL, ms("", "v1", [{"type": "audio", "payload": {"url": "https://lookaside.fbsbx.com/v.mp4"}}]))
    assert body(sent) == "I can read text, PDF, Word, email and photos." and not calls


def test_status_updates_ignored(env):
    c, sent, _ = env
    p = {"entry": [{"messaging": [{"sender": {"id": "9"}, "delivery": {"mids": ["x"]}}]}]}
    assert post(c, URL, p).status_code == 200 and not sent


def test_messenger_ssrf_and_echo(env, monkeypatch):
    c, sent, _ = env
    assert channels._media_host_ok("https://scontent.xx.fbcdn.net/a.png")
    assert channels._media_host_ok("https://lookaside.fbsbx.com/a")
    for bad in ("http://scontent.fbcdn.net/a", "https://evil.example/fbcdn.net", "https://fbcdn.net.evil.example/a",
                "https://169.254.169.254/x", "file:///etc/passwd"):
        assert not channels._media_host_ok(bad)
    ev = lambda m: {"entry": [{"messaging": [{"sender": {"id": "9"}, "message": m}]}]}
    post(c, "/api/channels/messenger", ev({"mid": "e1", "text": "hi", "is_echo": True}))
    assert not sent
    post(c, "/api/channels/messenger", ev({"mid": "e2", "text": "OK"}))
    post(c, "/api/channels/messenger", ev({"mid": "e3", "text": "Sila bayar akaun segera"}))
    assert sent[-1]["messaging_type"] == "RESPONSE" and sent[-1]["recipient"] == {"id": "9"}


def test_download_rejects_bad_host_and_oversize(monkeypatch):
    with pytest.raises(ValueError):
        channels._download("https://evil.example/a.png")

    class R:
        headers = {"Content-Type": "image/png"}
        def read(self, n): return b"x" * n
        def __enter__(self): return self
        def __exit__(self, *a): pass
    monkeypatch.setattr(channels, "_open", lambda req: R())
    with pytest.raises(ValueError):
        channels._download("https://x.fbcdn.net/a")


def test_rate_limit(env):
    c, sent, _ = env
    post(c, URL, ms("OK", "r0"))
    for i in range(14):
        post(c, URL, ms("Sila bayar akaun segera", f"r{i + 1}"))
    assert len(sent) == 11  # ok-ack + 9 replies, 1 rate notice, rest silent


def test_status_hides_secrets(env, monkeypatch):
    s = channels.status()
    dump = json.dumps(s)
    for v in ("mv", "appsecret", "pagetok"):
        assert f'"{v}"' not in dump
    assert "whatsapp" not in s
    assert s["messenger"]["link"] == "https://m.me/faham" and s["embed"] is True


def test_whatsapp_route_gone(env):
    c, _, _ = env
    assert c.get("/api/channels/whatsapp").status_code == 404
    assert c.post("/api/channels/whatsapp", content=b"{}").status_code == 404


def test_email_failed_spf_gets_no_reply(env, monkeypatch):
    out = []
    monkeypatch.setattr(channels, "_smtp_send", lambda *a: out.append(a))
    mk = lambda auth, frm="a@b.my": (f"From: {frm}\r\nSubject: Fwd\r\nAuthentication-Results: mx; {auth}\r\n\r\nhello".encode())
    assert channels.process_email(mk("spf=fail smtp.mailfrom=b.my", "x@b.my")) is False
    assert channels.process_email(mk("dkim=fail", "y@b.my")) is False
    assert channels.process_email(mk("dmarc=fail", "z@b.my")) is False
    assert not out
    assert channels.process_email(mk("spf=pass")) is True
    assert out[0][0] == "a@b.my" and out[0][1] == "Re: Fwd"
    assert channels.process_email(mk("spf=pass")) is False  # 1 reply per sender per hour


def test_email_webhook_secret(env, monkeypatch):
    c, _, _ = env
    assert c.post("/api/channels/email", content=b"x").status_code == 404
    monkeypatch.setenv("EMAIL_WEBHOOK_SECRET", "s3")
    assert c.post("/api/channels/email", content=b"x", headers={"X-FAHAM-Secret": "no"}).status_code == 403


def test_reply_languages_and_multi(monkeypatch):
    assert reply.detect("நீங்கள் பணம் செலுத்த") == "ta" and reply.detect("请付款") == "zh"
    assert reply.detect("Please pay your account") == "en" and reply.detect("Sila bayar akaun anda") == "bm"
    b = batch("no_signals")
    b.files.append(batch("caution").files[0])
    out = reply.summary(b, "bm", "messenger")
    assert out.splitlines()[0] == "Berhati-hati" and "Fail 1" in out and "genuine" not in out.lower()
    assert reply.summary(batch("no_signals"), "bm", "x").startswith("Tiada tanda penipuan ditemui (ini bukan bukti)")
    monkeypatch.setenv("FAHAM_PUBLIC_URL", "https://faham.example")
    assert "https://faham.example/terms" in reply.notice("en") and len(reply.notice("en").splitlines()) == 3


def test_mailtrap_inbound_replies_then_deletes(env, monkeypatch):
    monkeypatch.setenv("MAILTRAP_API_TOKEN", "tok")
    monkeypatch.setenv("MAILTRAP_INBOX_ID", "15")
    monkeypatch.setenv("SMTP_HOST", "smtp.example")
    assert channels.email_ready()
    now = channels.datetime.datetime.now(channels.datetime.timezone.utc)
    old = (now - channels.datetime.timedelta(hours=5)).isoformat()
    msgs = [{"id": "a", "received_at": now.isoformat()}, {"id": "b", "received_at": now.isoformat()},
            {"id": "old", "received_at": old}]
    calls = []

    def fake_mt(method, path):
        calls.append((method, path))
        if method == "GET" and path == "/messages":
            return {"data": msgs, "last_id": None}
        if method == "GET":
            return {"raw_message_url": "https://files.example/" + path.rsplit("/", 1)[1]}
        return {}
    monkeypatch.setattr(channels, "_mt", fake_mt)
    monkeypatch.setattr(channels, "_mt_raw", lambda url: url.encode())
    monkeypatch.setattr(channels, "process_email", lambda raw: raw.endswith(b"/a"))  # only "a" gets a reply
    channels._poll_mailtrap()
    assert ("DELETE", "/messages/a") in calls and ("DELETE", "/messages/b") not in calls
    assert not any("old" in p for _, p in calls)  # too old after a restart: untouched
    calls.clear()
    channels._poll_mailtrap()  # same ids again: nothing fetched twice
    assert calls == [("GET", "/messages")]


def test_mailtrap_raw_link_must_be_https_and_named_host(monkeypatch):
    for bad in ("http://files.example/x", "https://10.0.0.5/x", "file:///etc/passwd", "https://localhost/x"):
        with pytest.raises(ValueError):
            channels._mt_raw(bad)


def _capture_smtp(monkeypatch):
    seen = {}

    class FakeSMTP:
        def __init__(self, host, port, timeout=0):
            seen.update(cls=type(self).__name__, host=host, port=port, starttls=False)
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def starttls(self): seen["starttls"] = True
        def login(self, u, p): seen["user"] = u
        def send_message(self, m): seen["msg"] = m

    class FakeSSL(FakeSMTP):
        pass
    monkeypatch.setattr(channels.smtplib, "SMTP", FakeSMTP)
    monkeypatch.setattr(channels.smtplib, "SMTP_SSL", FakeSSL)
    return seen


def test_smtp_starttls_on_587_and_forced_tls_on_465(monkeypatch):
    seen = _capture_smtp(monkeypatch)
    for k, v in dict(SMTP_HOST="live.smtp.mailtrap.io", SMTP_USER="apismtp@mailtrap.io", SMTP_PASSWORD="p",
                     SMTP_FROM="FAHAM <faham@larmkx.com>").items():
        monkeypatch.setenv(k, v)
    monkeypatch.setenv("SMTP_PORT", "587")
    channels._smtp_send("user@example.org", "Re: x", "hello", "<orig@mail>")
    assert seen["cls"] == "FakeSMTP" and seen["starttls"] and seen["user"] == "apismtp@mailtrap.io"
    m = seen["msg"]
    assert m["Date"] and m["Message-ID"].endswith("@larmkx.com>") and m["In-Reply-To"] == m["References"] == "<orig@mail>"
    monkeypatch.setenv("SMTP_PORT", "465")
    channels._smtp_send("user@example.org", "Re: x", "hello", "")
    assert seen["cls"] == "FakeSSL" and seen["port"] == 465 and seen["starttls"] is False


def test_email_webhook_reply_mode(env, monkeypatch):
    c, _, _ = env
    monkeypatch.setenv("EMAIL_WEBHOOK_SECRET", "s3")
    got = []
    monkeypatch.setattr(channels, "process_email", lambda raw: got.append(raw) or True)
    h = {"X-FAHAM-Secret": "s3"}
    assert c.post("/api/channels/email?reply=1", content=b"mail", headers=h).status_code == 503  # no SMTP yet
    monkeypatch.setenv("SMTP_HOST", "smtp.example")
    assert c.post("/api/channels/email?reply=1", content=b"mail", headers={"X-FAHAM-Secret": "bad"}).status_code == 403
    r = c.post("/api/channels/email?reply=1", content=b"mail", headers=h)
    assert r.status_code == 200 and r.json() == {"ok": True} and got == [b"mail"]


def _mail_batch():
    sc = NS(verdict="likely_scam", verify_yourself=["Taip alamat rasmi <b>sendiri</b>", "Telefon talian rasmi", "tiga", "empat"],
            reasons=[NS(kind="risk", text="sebab <script>x</script> http://evil.example/x"), NS(kind="risk", text="Domain tidak rasmi"),
                     NS(kind="ok", text="baik"), NS(kind="info", text="info")])
    ok = NS(verdict="no_signals", verify_yourself=[], reasons=[NS(kind="info", text="x")])
    mk = lambda s: NS(scam=s, route=NS(source_url="https://www.hasil.gov.my"))
    return NS(files=[NS(name="secret-name.pdf", kind="eml", result=mk(sc)), NS(name="invoice.pdf", kind="pdf", result=mk(ok))])


def test_reply_email_html_is_safe_and_structured(monkeypatch):
    from app import mail_html
    monkeypatch.setenv("FAHAM_PUBLIC_URL", "https://faham.example")
    for lang in ("bm", "en", "zh", "ta"):
        h, t = mail_html.html_body(_mail_batch(), lang), mail_html.text(_mail_batch(), lang)
        assert "FAHAM" in h and "cid:faham-logo" in h and "NSRC 997" in h and "https://faham.example/terms" in h
        assert "<script>" not in h and "evil.example" not in h and "secret-name" not in h and "invoice" not in h and "secret-name" not in t
        assert "genuine" not in (h + t).lower() and "https://www.hasil.gov.my" in h
    en = mail_html.text(_mail_batch(), "en")
    assert "The email itself: Likely a scam" in en and "Attachment 1: No scam signs found" in en  # not "File 1 / File 2"
    assert "File 1" not in en and "&lt;b&gt;sendiri&lt;/b&gt;" in mail_html.html_body(_mail_batch(), "en")  # tags in the text are escaped in HTML
    assert "<html" in mail_html.html_body(NS(files=[]), "en") and "could not read" in mail_html.text(NS(files=[]), "en")


def test_reply_email_is_multipart_with_inline_logo(monkeypatch):
    from app import mail_html
    seen = _capture_smtp(monkeypatch)
    monkeypatch.setenv("SMTP_HOST", "smtp.example")
    monkeypatch.setenv("SMTP_FROM", "faham@larmkx.com")
    channels._smtp_send("u@example.org", "Re: x", mail_html.text(_mail_batch(), "en"), "", mail_html.html_body(_mail_batch(), "en"))
    m = seen["msg"]
    kinds = [p.get_content_type() for p in m.walk()]
    assert m.get_content_type() == "multipart/alternative" and "text/plain" in kinds and "text/html" in kinds and "image/png" in kinds
    assert "multipart/related" in kinds and any(p.get("Content-ID") == "<faham-logo>" for p in m.walk())
