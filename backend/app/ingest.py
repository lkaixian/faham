"""Safe, in-memory file ingestion: bytes in, plain text (plus links and email signals) out.

Nothing is written to disk. Every parser has size/page/depth caps. Only types and
sizes are logged, never contents or file names.
"""
from __future__ import annotations

import base64
import hashlib
import io
import logging
import re
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass, field
from email import policy
from email.parser import BytesParser
from html.parser import HTMLParser
from urllib.parse import urlparse

from . import filecheck, office, sandbox
from .models import AnalyzeRequest, BatchResponse, BatchSummary, FileResult

log = logging.getLogger("faham.ingest")

MAX_BODY = 25 * 1024 * 1024
MAX_XML = 10 * 1024 * 1024
MAX_PDF_PAGES, MAX_PDF_IMAGES = 20, 3
MAX_ATTACH, MAX_DEPTH, MAX_DOCS = 5, 2, 10
UNSUPPORTED = "This file type is not supported. Use PDF, Word (.docx), text, Markdown, email (.eml) or an image."
REJECT_EXT = {"doc", "docm", "xlsm", "xlsx", "xls", "pptx", "ppt", "html", "htm"}
CHECK_ONLY = filecheck.EXEC | filecheck.DISK | {"apk"}  # not read as letters: only the name, the listing and the magic bytes are inspected


class IngestError(Exception):
    def __init__(self, status: int, detail: str):
        super().__init__(detail)
        self.status, self.detail = status, detail


@dataclass
class Doc:
    name: str
    kind: str  # pdf docx text eml image skipped
    text: str
    image: bytes | None = None
    warnings: list[str] = field(default_factory=list)
    signals: list[str] = field(default_factory=list)
    sha256: str = ""  # of an inspected file (never of a letter), shown to the person so they can look it up themselves


def _skipped(name: str, reason: str) -> Doc:
    return Doc(name, "skipped", "", warnings=[reason])


# ------------------------------------------------------------------ detection
def _ext(filename: str | None) -> str:
    return filename.rsplit(".", 1)[-1].lower() if filename and "." in filename else ""


def detect(filename: str | None, content_type: str | None, data: bytes) -> str:
    ext, ct = _ext(filename), (content_type or "").split(";")[0].strip().lower()
    if data[:4] == b"%PDF":
        return "pdf"
    if data[:8] == b"\x89PNG\r\n\x1a\n" or data[:3] == b"\xff\xd8\xff":
        return "image"
    if data[:8] == office.OLE_MAGIC:
        if office.scan_ole(data):
            return "file_risk"  # macros (or a password) in an old Office file: report it, do not refuse it
        raise IngestError(415, "Old Word/Excel files are not accepted because they can hold macros. Save as PDF or DOCX.")
    if data[:4] in (b"PK\x03\x04", b"PK\x05\x06"):
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                names = set(z.namelist())
        except zipfile.BadZipFile:
            if ext == "docx":
                raise IngestError(422, "The file is damaged")
            return "file_risk"  # a broken archive is itself a sign (some scam files break parsers on purpose)
        office_like = "word/document.xml" in names or "[Content_Types].xml" in names
        if office_like and (ext in office.MACRO_EXT or "file_macro" in office.scan_ooxml(data, ext, False)):
            return "file_risk"  # macros are reported as signs, never executed
        if "word/document.xml" in names:
            return "docx"
        if "[Content_Types].xml" in names:
            raise IngestError(415, "Only Word (DOCX) is accepted from Office formats")
        return "file_risk"  # a zip or an APK: inspect the listing, never open it
    if data[:6] == bytes.fromhex("377abcaf271c") or data[:5] == bytes.fromhex("526172211a") or data[:2] == b"MZ" or ext in CHECK_ONLY:
        return "file_risk"
    if data[:3] == b"ID3" or data[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2", b"\xff\xe3") \
            or data[:4] in (b"OggS", b"fLaC", b"\x1a\x45\xdf\xa3") or data[4:8] == b"ftyp" \
            or (data[:4] == b"RIFF" and data[8:12] == b"WAVE"):
        raise IngestError(415, UNSUPPORTED)
    if ext in REJECT_EXT:
        raise IngestError(415, f"Files of type .{ext} are not accepted")
    if b"\x00" in data[:8192]:
        raise IngestError(415, UNSUPPORTED)
    if ext == "eml" or ct == "message/rfc822":
        return "eml"
    if ext in ("txt", "md", "markdown") or (not ext and ct in ("text/plain", "text/markdown")):
        return "text"
    raise IngestError(415, UNSUPPORTED)


# ------------------------------------------------------------------ helpers
def _host(url: str) -> str:
    try:
        return (urlparse(url if "://" in url else "http://" + url).hostname or "").lower()
    except ValueError:
        return ""


def _same(a: str, b: str) -> bool:
    return bool(a and b) and (a == b or a.endswith("." + b) or b.endswith("." + a))


def _links(urls) -> str:
    return "\n".join(f"[link: {u}]" for u in dict.fromkeys(urls))


def _safe_xml(data: bytes) -> ET.Element:
    if len(data) > MAX_XML:
        raise IngestError(413, "Document is too large when unpacked")
    if re.search(rb"<!(DOCTYPE|ENTITY)", data, re.I):
        raise IngestError(422, "Document XML contains a DOCTYPE or entity and was rejected")
    try:
        return ET.fromstring(data)
    except ET.ParseError:
        raise IngestError(422, "Document XML is damaged")


def _read_member(z: zipfile.ZipFile, name: str, limit: int) -> bytes:
    with z.open(name) as f:
        out = f.read(limit + 1)
    if len(out) > limit:
        raise IngestError(413, "File is too large when unpacked")
    return out


# ------------------------------------------------------------------ parsers
def _pdf(name: str, data: bytes) -> Doc:
    from pypdf import PdfReader

    from .agent.tools import TOOLS
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            raise IngestError(422, "The PDF is password protected. Remove the password and send it again.")
        pages = reader.pages[:MAX_PDF_PAGES]
        warns = [f"Only the first {MAX_PDF_PAGES} pages were read"] if len(reader.pages) > MAX_PDF_PAGES else []
        texts, urls, ocr_tried, ocr_ok = [], [], 0, False
        for page in pages:
            t = (page.extract_text() or "").strip()
            for a in page.get("/Annots") or []:
                try:
                    uri = a.get_object().get("/A", {}).get("/URI")
                except Exception:
                    uri = None
                if uri:
                    urls.append(str(uri))
            if len(t) < 20 and ocr_tried < MAX_PDF_IMAGES:  # nearly empty page: probably a scan
                try:
                    for img in page.images[:MAX_PDF_IMAGES - ocr_tried]:
                        ocr_tried += 1
                        got = TOOLS["ocr.read"].fn(image_bytes=img.data).strip()
                        ocr_ok = ocr_ok or bool(got)
                        t = (t + "\n" + got).strip()
                except Exception:
                    pass
            texts.append(t)
        if ocr_tried and not ocr_ok:
            warns.append("Scanned PDF, OCR not available")
        elif not any(texts):
            warns.append("Scanned PDF, OCR not available")
    except IngestError:
        raise
    except Exception as e:
        log.info("pdf parse failed: %s", type(e).__name__)
        raise IngestError(422, "The PDF could not be read")
    return Doc(name, "pdf", "\n\n".join(x for x in texts if x) + "\n" + _links(urls), warnings=warns)


W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def _docx(name: str, data: bytes) -> Doc:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            root = _safe_xml(_read_member(z, "word/document.xml", MAX_XML))
            rels = _safe_xml(_read_member(z, "word/_rels/document.xml.rels", MAX_XML)) \
                if "word/_rels/document.xml.rels" in z.namelist() else None
    except zipfile.BadZipFile:
        raise IngestError(422, "The DOCX file is damaged")
    paras = []
    for p in root.iter(W + "p"):
        paras.append("".join((e.text or "") if e.tag == W + "t" else "\t" if e.tag == W + "tab" else ""
                             for e in p.iter()))
    urls = [r.get("Target", "") for r in rels if r.get("Type", "").endswith("/hyperlink")
            and r.get("TargetMode") == "External"] if rels is not None else []
    return Doc(name, "docx", "\n".join(paras) + "\n" + _links(urls))


def _text(name: str, data: bytes) -> Doc:
    warns = []
    try:
        s = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        s = data.decode("latin-1")
        warns.append("Not valid UTF-8, read as Latin-1; some characters may look wrong")
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)[^)]*\)", r"\1 [link: \2]", s)
    s = re.sub(r"^\s{0,3}(?:#{1,6}\s+|>\s?|[-*+]\s+)", "", s, flags=re.M)
    s = re.sub(r"(\*\*|__|`)", "", s)
    return Doc(name, "text", s.strip(), warnings=warns)


class _Html(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.anchors: list[tuple[str, str]] = []  # (href, text)
        self._href: str | None = None
        self._atext: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip += 1
        elif tag in ("br", "p", "div", "tr", "li"):
            self.parts.append("\n")
        elif tag == "a":
            self._href, self._atext = dict(attrs).get("href") or "", []

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self._skip = max(0, self._skip - 1)
        elif tag == "a" and self._href is not None:
            self.anchors.append((self._href, "".join(self._atext).strip()))
            self._href = None

    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)
            if self._href is not None:
                self._atext.append(data)


DOMAIN_IN_TEXT = re.compile(r"(?:https?://)?((?:[a-z0-9-]+\.)+[a-z]{2,})\b", re.I)


def _eml(name: str, data: bytes, depth: int) -> list[Doc]:
    msg = BytesParser(policy=policy.default).parsebytes(data)
    signals: list[str] = []

    def add(code):
        if code not in signals:
            signals.append(code)

    def addr_domain(header):
        try:
            return (msg[header].addresses[0].domain or "").lower() if msg[header] else ""
        except Exception:
            return ""

    frm = addr_domain("From")
    for h in ("Reply-To", "Return-Path"):
        d = addr_domain(h) if h == "Reply-To" else (str(msg[h] or "").rpartition("@")[2].strip("<> ").lower())
        if frm and d and not _same(frm, d):
            add("mail_replyto_mismatch")
    auth = " ".join(str(v) for k, v in msg.items() if k.lower() in ("authentication-results", "received-spf"))
    if re.search(r"\b(?:spf|dkim|dmarc)\s*=\s*(?:soft)?fail", auth, re.I) or re.search(r"^\s*(?:soft)?fail\b", str(msg["Received-SPF"] or ""), re.I):
        add("mail_spf_fail")
    try:
        shown = DOMAIN_IN_TEXT.search(msg["From"].addresses[0].display_name or "")
        if shown and frm and not _same(shown.group(1).lower(), frm):
            add("mail_display_spoof")
    except Exception:
        pass

    body_html = msg.get_body(("html",))
    body_plain = msg.get_body(("plain",))
    urls: list[str] = []
    htext = ""
    if body_html is not None:
        p = _Html()
        p.feed(body_html.get_content())
        htext = "".join(p.parts)
        for href, label in p.anchors:
            if href.lower().startswith(("mailto:", "tel:", "#")) or not href:
                continue
            urls.append(href)
            m = DOMAIN_IN_TEXT.search(label)
            if m and not _same(m.group(1).lower(), _host(href)):
                add("mail_link_mismatch")
    body = body_plain.get_content() if body_plain is not None else htext
    text = f"Subject: {msg['Subject'] or ''}\n{body.strip()}\n{_links(urls)}"
    out = [Doc(name, "eml", text, signals=signals)]
    for i, part in enumerate(msg.iter_attachments()):
        label = f"{name} > {part.get_filename() or 'attachment'}"
        if i >= MAX_ATTACH:
            out.append(_skipped(label, f"Only the first {MAX_ATTACH} attachments are read"))
            continue
        try:
            out += extract(part.get_filename(), part.get_content_type(), part.get_payload(decode=True) or b"", depth=depth + 1, via_chat=True)
        except IngestError as e:
            out.append(_skipped(label, e.detail))
    return out


# ------------------------------------------------------------------ public API
def extract(filename: str | None, content_type: str | None, data: bytes, *,
            depth: int = 0, via_chat: bool = False) -> list[Doc]:
    if depth > MAX_DEPTH:
        raise IngestError(422, "Files are nested too deeply")
    if not data:
        raise IngestError(422, "The file is empty")
    kind = detect(filename, content_type, data)
    log.info("ingest kind=%s bytes=%d depth=%d", kind, len(data), depth)
    name = re.sub(r"[\x00-\x1f]", "", (filename or "file").replace("\\", "/").rsplit("/", 1)[-1])[:100] or "file"
    if kind == "file_risk":
        label, inner, codes, facts = sandbox.inspect_isolated(filename, data, via_chat)  # in a limited child process
        info = ["file_checked"] + ([] if codes else ["file_out_of_scope"])  # what was and was not looked at; no sign found
        return [Doc(name, kind, filecheck.describe(filename, label, inner, via_chat, facts), signals=codes + info,
                    sha256=hashlib.sha256(data).hexdigest())]
    if kind == "pdf":
        return [_pdf(name, data)]
    if kind == "docx":
        d = _docx(name, data)
        d.signals += office.scan_ooxml(data, _ext(filename), via_chat)  # remote template or DDE in an otherwise normal letter
        return [d]
    if kind == "text":
        return [_text(name, data)]
    if kind == "eml":
        return _eml(name, data, depth)
    return [Doc(name, "image", "", image=data)]


def extract_safe(filename: str | None, content_type: str | None, data: bytes, *, via_chat: bool = False) -> list[Doc]:
    """`extract` in a limited child process (see sandbox.py): what the web routes and channels call, so no hostile file is
    ever parsed inside the API process. A crash, hang or overload becomes an IngestError, never a 500 and never a pass."""
    if sandbox.IN_WORKER:
        return extract(filename, content_type, data, via_chat=via_chat)
    try:
        out = sandbox.extract_isolated(filename, content_type, data, via_chat)
    except sandbox.Busy:
        raise IngestError(503, "Tulen is reading other files right now. Please try again in a moment.")
    except sandbox.Failed:
        raise IngestError(422, "This file could not be read safely.")
    if "error" in out:
        raise IngestError(int(out["error"]["status"]), str(out["error"]["detail"]))
    return [Doc(name=str(d["name"])[:200], kind=str(d["kind"]), text=str(d["text"]), warnings=[str(w) for w in d["warnings"]][:20],
                signals=[str(c) for c in d["signals"]][:40], sha256=str(d.get("sha256") or "")[:64],
                image=base64.b64decode(d["image"]) if d.get("image") else None) for d in out["docs"][:50]]


def analyze_files(docs: list[Doc], language: str, postcode: str | None, sink=None) -> BatchResponse:
    from .agent import orchestrator  # late: the sandbox child imports this module and must stay light
    files: list[FileResult] = []
    for n, d in enumerate(docs):
        fr = FileResult(name=d.name, kind=d.kind, status="ok", warnings=list(d.warnings), sha256=d.sha256 or None)
        if d.kind == "skipped":
            fr.status, fr.detail, fr.warnings = "skipped", (d.warnings or ["Skipped"])[0], []
        elif n >= MAX_DOCS:
            fr.status, fr.detail = "skipped", f"Only the first {MAX_DOCS} files are analysed per request"
        elif len(d.text.strip()) < 10 and not d.image:
            fr.status, fr.detail = "skipped", "Not enough readable text in this file"
        else:
            req = AnalyzeRequest.model_construct(text=d.text[:20000], image_b64=None, language=language,
                                                 postcode=postcode, sample_id=None)
            try:
                fr.result = orchestrator.run(req, d.image if not d.text.strip() else None, d.signals, sink=sink)
            except orchestrator.OCRUnavailable:
                fr.status, fr.detail = "error", "Could not read text from this image. OCR is not available."
            except Exception as e:  # one bad file must not fail the batch
                log.warning("analyze failed: %s", type(e).__name__)
                fr.status, fr.detail = "error", "Could not analyse this file"
        files.append(fr)
    s = BatchSummary(total=len(files))
    for f in files:
        if f.status == "skipped":
            s.skipped += 1
        elif f.result:
            s.analysed += 1
            setattr(s, f.result.scam.verdict, getattr(s, f.result.scam.verdict) + 1)
    return BatchResponse(files=files, summary=s)
