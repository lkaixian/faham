"""Messaging channels: Messenger, email (IMAP or Mailtrap Inbound poll, plus webhook).

Env-configured; unconfigured channels are inert. Stdlib only. State is in memory by design
(ponytail: a restart forgets consent, dedup and rate limits; move to Redis if that matters).
Never logs ids, numbers or content; never fetches URLs found in messages.
"""
from __future__ import annotations

import collections
import datetime
import hashlib
import hmac
import imaplib
import json
import logging
import mimetypes
import os
import re
import smtplib
import threading
import time
import urllib.parse
import urllib.request
from email import message_from_bytes
from email.header import decode_header, make_header
from email.message import EmailMessage
from email.utils import formatdate, make_msgid, parseaddr
from typing import Callable

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import PlainTextResponse
from starlette.concurrency import run_in_threadpool

from . import ingest, mail_html, reply

log = logging.getLogger("faham.channels")
router = APIRouter(prefix="/api/channels", tags=["channels"])

CAP = 25 * 1024 * 1024
TIMEOUT = 20
MEDIA_HOSTS = ("fbcdn.net", "facebook.com", "fbsbx.com")
HOUR, TTL = 3600, 30 * 86400
PER_SENDER, PER_CHANNEL = 10, 300
AGREE = {"OK", "SETUJU", "AGREE", "同意", "சம்மதம்"}
STOP = {"STOP", "BERHENTI"}
AUDIO_HINT = "I can read text, PDF, Word, email and photos."
_KEY = os.urandom(32)


def env(k: str) -> str:
    return os.getenv(k, "").strip()


# ---------- tiny in-memory state ----------
_lock = threading.Lock()
_seen: collections.OrderedDict[str, None] = collections.OrderedDict()   # message-id dedup (LRU 1000)
_consent: collections.OrderedDict[str, list] = collections.OrderedDict()  # hash -> [ok, ts, lang]
_hits: dict[str, collections.deque] = {}


def _hid(channel: str, sender: str) -> str:
    key = env("CHANNEL_HASH_KEY").encode() or _KEY
    return hmac.new(key, f"{channel}:{sender}".encode(), hashlib.sha256).hexdigest()[:32]


def _dup(channel: str, mid: str) -> bool:
    k = f"{channel}:{mid}"
    with _lock:
        if k in _seen:
            return True
        _seen[k] = None
        while len(_seen) > 1000:
            _seen.popitem(last=False)
    return False


def _count(key: str) -> int:
    """Record one hit in the last hour and return how many there are."""
    now = time.time()
    with _lock:
        q = _hits.setdefault(key, collections.deque())
        while q and q[0] < now - HOUR:
            q.popleft()
        q.append(now)
        return len(q)


def _state(h: str):
    with _lock:
        s = _consent.get(h)
        if s and s[1] < time.time() - TTL:
            del _consent[h]
            return None
        return s


def _set(h: str, ok: bool, lang: str) -> None:
    with _lock:
        _consent[h] = [ok, time.time(), lang]
        while len(_consent) > 50000:
            _consent.popitem(last=False)


# ---------- HTTP ----------
class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):  # a redirect could leave the allowed hosts
        return None


_opener = urllib.request.build_opener(_NoRedirect)


def _open(req: urllib.request.Request):
    return _opener.open(req, timeout=TIMEOUT)


def _graph(path: str) -> str:
    return f"https://graph.facebook.com/{env('GRAPH_VERSION') or 'v21.0'}/{path}"


def _json_req(url: str, payload: dict):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with _open(req) as r:
        return json.loads(r.read(1_000_000) or b"{}")


def _media_host_ok(url: str) -> bool:
    u = urllib.parse.urlparse(url)
    host = (u.hostname or "").lower()
    return u.scheme == "https" and any(host == d or host.endswith("." + d) for d in MEDIA_HOSTS)


def _download(url: str) -> tuple[bytes, str]:
    if not _media_host_ok(url):
        raise ValueError("host not allowed")
    with _open(urllib.request.Request(url)) as r:
        data = r.read(CAP + 1)
        if len(data) > CAP:
            raise ValueError("too large")
        return data, (r.headers.get("Content-Type") or "application/octet-stream").split(";")[0].strip()


def _name(base: str, ctype: str) -> str:
    return base if "." in base else base + (mimetypes.guess_extension(ctype) or "")


def _sig_ok(raw: bytes, header: str | None, secret: str) -> bool:
    want = "sha256=" + hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    return bool(header) and hmac.compare_digest(want.encode(), header.encode())


# ---------- shared pipeline ----------
def handle(channel: str, sender: str, mid: str, text: str,
           media: Callable[[], list[tuple[str, str, bytes]]], send: Callable[[str], None]) -> None:
    """Consent, rate limit, analyse, reply. Runs in a background task."""
    try:
        if mid and _dup(channel, mid):
            return
        h = _hid(channel, sender)
        st = _state(h)
        lang = reply.detect(text) if text else (st[2] if st else "bm")
        if _count("c:" + channel) > PER_CHANNEL:
            return
        n = _count("s:" + h)
        if n > PER_SENDER:
            if n == PER_SENDER + 1:
                send(reply.t(lang, "rate"))
            return
        word = text.strip().strip(".!。 ").upper()
        if word in STOP:
            with _lock:
                _consent.pop(h, None)
            return send(reply.t(lang, "stop"))
        if word in AGREE:
            _set(h, True, lang)
            return send(reply.t(lang, "ok"))
        if not st or not st[0]:
            first = st is None
            _set(h, False, lang)
            return send((reply.notice(lang) + "\n" if first else "") + reply.t(lang, "ask"))
        _set(h, True, lang)
        docs = [ingest.Doc(name="message", kind="text", text=text)] if text.strip() else []
        for name, ctype, data in media():
            docs += ingest.extract_safe(name, ctype, data)
        if not docs:
            return
        send(reply.summary(ingest.analyze_files(docs, lang, None), lang, channel))
    except Exception as e:  # type only: messages and ids are never logged
        log.warning("channel %s failed: %s", channel, type(e).__name__)
        try:
            send(reply.t(reply.detect(text) if text else "bm", "err"))
        except Exception:
            pass


def _verify(request: Request, token_env: str, enabled: bool) -> PlainTextResponse:
    if not enabled:
        raise HTTPException(404)
    q = request.query_params
    tok = q.get("hub.verify_token", "")
    if q.get("hub.mode") != "subscribe" or not hmac.compare_digest(tok.encode(), env(token_env).encode()):
        raise HTTPException(403)
    return PlainTextResponse(q.get("hub.challenge", ""))


async def _body(request: Request, secret: str) -> dict:
    raw = await request.body()
    if not _sig_ok(raw, request.headers.get("x-hub-signature-256"), secret):
        raise HTTPException(403)
    try:
        return json.loads(raw)
    except ValueError:
        raise HTTPException(400)


# ---------- Messenger ----------
def ms_ready() -> bool:
    return all(env(k) for k in ("MESSENGER_VERIFY_TOKEN", "MESSENGER_APP_SECRET", "MESSENGER_PAGE_TOKEN"))


def _ms_send(psid: str, body: str) -> None:
    url = _graph("me/messages?" + urllib.parse.urlencode({"access_token": env("MESSENGER_PAGE_TOKEN")}))
    _json_req(url, {"recipient": {"id": psid}, "messaging_type": "RESPONSE", "message": {"text": body}})


def _ms_media(atts: list) -> list[tuple[str, str, bytes]]:
    out = []
    for a in atts[:3]:
        if not isinstance(a, dict) or a.get("type") not in ("image", "file"):
            continue
        url = str((a.get("payload") or {}).get("url", ""))
        data, ctype = _download(url)  # host allow-list enforced inside
        out.append((_name(os.path.basename(urllib.parse.urlparse(url).path) or a["type"], ctype), ctype, data))
    return out


@router.get("/messenger")
def ms_verify(request: Request):
    return _verify(request, "MESSENGER_VERIFY_TOKEN", ms_ready())


@router.post("/messenger")
async def ms_hook(request: Request, bg: BackgroundTasks):
    if not ms_ready():
        raise HTTPException(404)
    payload = await _body(request, env("MESSENGER_APP_SECRET"))
    for e in payload.get("entry") or []:
        for ev in e.get("messaging") or []:
            m, psid = ev.get("message"), str((ev.get("sender") or {}).get("id", ""))
            if not isinstance(m, dict) or m.get("is_echo") or not psid:
                continue
            atts = [a for a in m.get("attachments") or [] if isinstance(a, dict)]
            if any(a.get("type") == "audio" for a in atts):  # voice notes are not read
                atts = [a for a in atts if a.get("type") != "audio"]
                if not atts and not m.get("text"):
                    mid = str(m.get("mid", ""))
                    if not (mid and _dup("messenger", mid)) and _count("s:" + _hid("messenger", psid)) <= PER_SENDER:
                        bg.add_task(_ms_send, psid, AUDIO_HINT)
                    continue
            bg.add_task(handle, "messenger", psid, str(m.get("mid", "")), m.get("text") or "",
                        lambda atts=atts: _ms_media(atts), lambda b, psid=psid: _ms_send(psid, b))
    return {"ok": True}


# ---------- Email ----------
_BAD_AUTH = re.compile(r"\b(spf|dkim|dmarc)=fail\b", re.I)
_ADDR = re.compile(r"[^@\s<>,;\"]+@[^@\s<>,;\"]+\.[^@\s<>,;\"]+")


def _subject(msg) -> str:
    try:
        s = str(make_header(decode_header(msg.get("Subject", ""))))
    except Exception:
        s = ""
    s = re.sub(r"[\x00-\x1f\x7f]", " ", s).strip()[:100]
    return "Re: " + re.sub(r"^(re:\s*)+", "", s, flags=re.I)


def _smtp_send(to: str, subject: str, body: str, msgid: str, html: str | None = None) -> None:
    sender = env("SMTP_FROM") or env("EMAIL_PUBLIC_ADDRESS") or env("SMTP_USER")
    m = EmailMessage()
    m["From"], m["To"], m["Subject"] = sender, to, subject
    m["Date"] = formatdate()  # smtplib adds neither Date nor Message-ID; mail without them is often marked as spam
    m["Message-ID"] = make_msgid(domain=parseaddr(sender)[1].rpartition("@")[2] or None)
    m["Auto-Submitted"] = "auto-replied"
    if msgid and not re.search(r"[\r\n]", msgid):
        m["In-Reply-To"] = m["References"] = msgid
    m.set_content(body)
    if html:  # plain text stays as the fallback; the logo travels inside the message (no remote images)
        m.add_alternative(html, subtype="html")
        try:
            m.get_payload()[1].add_related(mail_html.LOGO.read_bytes(), "image", "png", cid="<" + mail_html.CID + ">")
        except OSError:
            pass
    port = int(env("SMTP_PORT") or 587)
    # 465 is TLS from the first byte (Mailtrap: "forced TLS"); 587, 2525 and 25 start plain and upgrade with STARTTLS
    with (smtplib.SMTP_SSL(env("SMTP_HOST"), port, timeout=TIMEOUT) if port == 465
          else smtplib.SMTP(env("SMTP_HOST"), port, timeout=TIMEOUT)) as s:
        if port != 465:
            s.starttls()
        if env("SMTP_USER"):
            s.login(env("SMTP_USER"), env("SMTP_PASSWORD"))
        s.send_message(m)


def process_email(raw: bytes) -> bool:
    """Analyse a forwarded email and reply to its sender. Returns True if a reply was sent."""
    msg = message_from_bytes(raw)
    sender = parseaddr(str(msg.get("From", "")))[1]
    auth = " ".join(str(x) for x in msg.get_all("Authentication-Results") or [])
    auto = str(msg.get("Auto-Submitted", "no")).lower() != "no" or str(msg.get("Precedence", "")).lower() in ("bulk", "junk", "list")
    if (not _ADDR.fullmatch(sender) or _BAD_AUTH.search(auth) or auto
            or re.search(r"(no-?reply|mailer-daemon|postmaster)", sender, re.I)):
        return False  # forged or automated senders get nothing (no backscatter)
    if _count("e:" + _hid("email", sender.lower())) > 1:
        return False
    docs = ingest.extract_safe("message.eml", "message/rfc822", raw)
    lang = reply.detect(" ".join(d.text for d in docs if d.text)[:2000])
    batch = ingest.analyze_files(docs, lang, None)
    _smtp_send(sender, _subject(msg), mail_html.text(batch, lang), str(msg.get("Message-ID", "")), mail_html.html_body(batch, lang))
    return True


def mt_ready() -> bool:
    """Mailtrap Inbound (REST, API token) instead of IMAP."""
    return bool(env("MAILTRAP_API_TOKEN")) and env("MAILTRAP_INBOX_ID").isdigit()


def email_ready() -> bool:
    return bool(env("SMTP_HOST")) and (mt_ready() or all(env(k) for k in ("IMAP_HOST", "IMAP_USER", "IMAP_PASSWORD")))


MT_API = "https://mailtrap.io/api/inbound/inboxes/"
MT_MAX_AGE = 2 * HOUR  # after a restart, older mail is left alone rather than answered twice


def _mt(method: str, path: str):
    req = urllib.request.Request(MT_API + env("MAILTRAP_INBOX_ID") + path, method=method, headers={
        "Authorization": "Bearer " + env("MAILTRAP_API_TOKEN"), "Accept": "application/json", "User-Agent": "faham/0.1"})
    with _open(req) as r:
        return json.loads(r.read(1_000_000) or b"{}")


def _mt_raw(url: str) -> bytes:
    """Raw .eml from the signed link Mailtrap returns. https only, no redirects, no token sent, size capped."""
    host = (urllib.parse.urlparse(url).hostname or "").lower()
    if urllib.parse.urlparse(url).scheme != "https" or "." not in host or host.replace(".", "").isdigit():
        raise ValueError("link not allowed")
    with _open(urllib.request.Request(url, headers={"User-Agent": "faham/0.1"})) as r:
        data = r.read(CAP + 1)
    if len(data) > CAP:
        raise ValueError("too large")
    return data


def _mt_recent(m: dict) -> bool:
    try:
        ts = datetime.datetime.fromisoformat(str(m.get("received_at", "")).replace("Z", "+00:00"))
        return (datetime.datetime.now(datetime.timezone.utc) - ts).total_seconds() < MT_MAX_AGE
    except ValueError:
        return True


def _poll_mailtrap() -> None:
    j = _mt("GET", "/messages")
    # Newest first. A message we answered is deleted from Mailtrap; anything else (such as Cloudflare's
    # address-verification mail) stays so you can read it in the Mailtrap inbox.
    for m in ((j if isinstance(j, list) else j.get("data")) or [])[:10]:
        mid = str(m.get("id") or "")
        if not mid or not _mt_recent(m) or _dup("mailtrap", mid):
            continue
        try:
            if process_email(_mt_raw(_mt("GET", "/messages/" + mid).get("raw_message_url") or "")):
                _mt("DELETE", "/messages/" + mid)
        except Exception as e:
            log.warning("mailtrap message failed: %s", type(e).__name__)


def _poll_once() -> None:
    M = imaplib.IMAP4_SSL(env("IMAP_HOST"), int(env("IMAP_PORT") or 993), timeout=TIMEOUT)
    try:
        M.login(env("IMAP_USER"), env("IMAP_PASSWORD"))
        M.select("INBOX")
        for i in (M.search(None, "UNSEEN")[1][0] or b"").split()[:5]:
            size = re.search(rb"RFC822\.SIZE (\d+)", b" ".join(x if isinstance(x, bytes) else x[0] for x in M.fetch(i, "(RFC822.SIZE)")[1]))
            raw = b"" if size and int(size.group(1)) > CAP else M.fetch(i, "(RFC822)")[1][0][1]  # fetch marks Seen; nothing is deleted
            M.store(i, "+FLAGS", "\\Seen")
            if raw:
                try:
                    process_email(raw)
                except Exception as e:
                    log.warning("email failed: %s", type(e).__name__)
    finally:
        try:
            M.logout()
        except Exception:
            pass


def _loop() -> None:
    while True:
        try:
            (_poll_mailtrap if mt_ready() else _poll_once)()
        except Exception as e:
            log.warning("email poll failed: %s", type(e).__name__)
        time.sleep(max(10, int(env("IMAP_POLL_SECONDS") or 60)))


_worker: threading.Thread | None = None


def start_email_worker() -> threading.Thread | None:
    global _worker
    with _lock:
        if _worker is None and email_ready():
            _worker = threading.Thread(target=_loop, name="faham-email", daemon=True)
            _worker.start()
        return _worker


ensure_worker = start_email_worker  # status() calls it, so the first /api/health-style poll starts it


def _reply_task(raw: bytes) -> None:
    try:
        process_email(raw)
    except Exception as e:
        log.warning("email reply failed: %s", type(e).__name__)


@router.post("/email")
async def email_hook(request: Request, bg: BackgroundTasks):
    """Raw RFC822 push (for example from a Cloudflare Email Worker). Without ?reply=1 it returns the analysis;
    with ?reply=1 it answers the sender by email (same rules as the mailbox worker) and returns {"ok": true}."""
    secret = env("EMAIL_WEBHOOK_SECRET")
    if not secret:
        raise HTTPException(404)
    if not hmac.compare_digest(request.headers.get("x-faham-secret", "").encode(), secret.encode()):
        raise HTTPException(403)
    raw = await request.body()
    if not raw or len(raw) > CAP:
        raise HTTPException(413 if raw else 400)
    if request.query_params.get("reply") == "1":
        if not env("SMTP_HOST"):
            raise HTTPException(503, "SMTP is not configured")
        bg.add_task(_reply_task, raw)
        return {"ok": True}
    def work():
        docs = ingest.extract_safe("message.eml", "message/rfc822", raw)
        return ingest.analyze_files(docs, reply.detect(" ".join(d.text for d in docs if d.text)[:2000]), None)
    try:
        return await run_in_threadpool(work)
    except ingest.IngestError as e:
        raise HTTPException(e.status, e.detail)


# ---------- status ----------
def status() -> dict:
    """Public, secret-free summary. Also lazily starts the email worker once."""
    ensure_worker()
    pg, ad = env("MESSENGER_PAGE_USERNAME"), env("EMAIL_PUBLIC_ADDRESS")
    return {
        "messenger": {"configured": ms_ready(), "link": f"https://m.me/{pg}" if ms_ready() and pg else None},
        "email": {"configured": email_ready() or bool(env("EMAIL_WEBHOOK_SECRET")), "address": ad or None},
        "embed": True,
        "allowed_embed_origins": [o.strip() for o in env("FAHAM_EMBED_ORIGINS").split(",") if o.strip()],
    }
