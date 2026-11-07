import io
import zipfile
from email.message import EmailMessage

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter
from pypdf.generic import ArrayObject, DictionaryObject, FloatObject, NameObject, TextStringObject

from app import ingest
from app.main import app

client = TestClient(app)
LHDN_TXT = "LHDN notis: sila semak akaun di https://mytax.hasil.gov.my sebelum 30 Disember 2026. Rujukan 12345."
SCAM_TXT = "URGENT arrest warrant. Transfer RM2000 to account now, TAC needed. Click https://bit.ly/abc123"


def zipped(files: dict[str, bytes | str], compress=zipfile.ZIP_DEFLATED) -> bytes:
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w", compress) as z:
        for k, v in files.items():
            z.writestr(k, v)
    return b.getvalue()


def docx(text: str, url: str | None = None, doc_xml: str | None = None) -> bytes:
    ns = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
    xml = doc_xml or f'<w:document {ns}><w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body></w:document>'
    rels = ('<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f'<Relationship Id="r1" Type="http://x/relationships/hyperlink" Target="{url}" TargetMode="External"/></Relationships>')
    return zipped({"[Content_Types].xml": "<x/>", "word/document.xml": xml, "word/_rels/document.xml.rels": rels if url else "<Relationships/>"})


def pdf(text_url: str | None = None, blank_pages=1, encrypt=False) -> bytes:
    w = PdfWriter()
    for _ in range(blank_pages):
        w.add_blank_page(200, 200)
    if text_url:
        a = DictionaryObject({NameObject("/Type"): NameObject("/Annot"), NameObject("/Subtype"): NameObject("/Link"),
                              NameObject("/Rect"): ArrayObject([FloatObject(0)] * 4),
                              NameObject("/A"): DictionaryObject({NameObject("/S"): NameObject("/URI"), NameObject("/URI"): TextStringObject(text_url)})})
        w.pages[0][NameObject("/Annots")] = ArrayObject([w._add_object(a)])
    if encrypt:
        w.encrypt("secret")
    b = io.BytesIO()
    w.write(b)
    return b.getvalue()


def test_text_and_markdown_links():
    d = ingest.extract("a.md", None, b"# Notis\n**Bayar** di [portal](https://evil.example/x)")[0]
    assert "Notis" in d.text and "**" not in d.text and "[link: https://evil.example/x]" in d.text


def test_latin1_fallback_warns():
    d = ingest.extract("a.txt", None, "caf\xe9 notis".encode("latin-1"))[0]
    assert d.warnings and "caf" in d.text


def test_pdf_link_annotation_and_scanned_warning():
    d = ingest.extract("x.pdf", "application/pdf", pdf("https://evil.example/pay"))[0]
    assert d.kind == "pdf" and "[link: https://evil.example/pay]" in d.text
    assert any("OCR" in w for w in d.warnings)


def test_encrypted_pdf_422():
    with pytest.raises(ingest.IngestError) as e:
        ingest.extract("x.pdf", None, pdf(encrypt=True))
    assert e.value.status == 422


def test_pdf_page_cap():
    d = ingest.extract("x.pdf", None, pdf(blank_pages=25))[0]
    assert any("20 pages" in w for w in d.warnings)


def test_docx_text_and_hyperlink():
    d = ingest.extract("a.docx", None, docx("Sila bayar segera", "https://evil.example/pay"))[0]
    assert d.kind == "docx" and "Sila bayar segera" in d.text and "[link: https://evil.example/pay]" in d.text


def test_docx_doctype_rejected():
    xml = '<?xml version="1.0"?><!DOCTYPE d [<!ENTITY x "boom">]><w:document xmlns:w="urn:w"/>'
    with pytest.raises(ingest.IngestError) as e:
        ingest.extract("a.docx", None, docx("", doc_xml=xml))
    assert e.value.status == 422


def test_macro_files_are_flagged_not_refused_and_plain_legacy_doc_still_refused():
    ole = bytes.fromhex("d0cf11e0a1b11ae1")
    with pytest.raises(ingest.IngestError) as e:  # an old file with no macro marker: still unreadable as a letter
        ingest.extract("a.doc", None, ole + b"0" * 50)
    assert e.value.status == 415
    d = ingest.extract("a.docm", None, docx("hi"))[0]
    assert d.kind == "file_risk"
    macro = zipped({"[Content_Types].xml": "<x/>", "word/document.xml": "<a/>", "word/vbaProject.bin": "x"})
    d = ingest.extract("a.docx", None, macro)[0]
    assert d.kind == "file_risk" and "file_macro" in d.signals


def test_bad_magic_rejected():
    for name, data in [("a.bin", b"\x00\x01\x02\x03" * 10), ("a.pdf", b"not a pdf at all but text")]:
        with pytest.raises(ingest.IngestError) as e:
            ingest.extract(name, None, data)
        assert e.value.status == 415


def test_audio_unsupported_415():
    mp3 = b"ID3\x03\x00\x00\x00\x00\x00\x00" + b"\x00" * 20
    wav = b"RIFF\x00\x00\x00\x00WAVEfmt "
    for name, data in (("v.mp3", mp3), ("v.wav", wav)):
        with pytest.raises(ingest.IngestError) as e:
            ingest.extract(name, None, data)
        assert e.value.status == 415 and "not supported" in e.value.detail
        r = client.post("/api/analyze-file", content=data, headers={"X-Filename": name})
        assert r.status_code == 415
    msg = EmailMessage()
    msg.set_content("hi there, see attached")
    msg.add_attachment(zipped({"a.txt": "x"}), maintype="application", subtype="zip", filename="a.zip")
    docs = ingest.extract("m.eml", None, msg.as_bytes())
    assert docs[1].kind == "file_risk"  # a zip is no longer refused: its listing is inspected (see test_filecheck.py)


def eml(**h) -> bytes:
    m = EmailMessage()
    m["Subject"] = "Notis LHDN"
    m["From"] = h.get("frm", '"hasil.gov.my" <alert@evil.example>')
    m["To"] = "me@example.com"
    if "reply" in h:
        m["Reply-To"] = h["reply"]
    m["Authentication-Results"] = "mx; spf=fail smtp.mailfrom=evil.example; dkim=none"
    m.set_content("Plain body")
    m.add_alternative('<p>Bayar di <a href="https://evil.example/pay">www.hasil.gov.my</a></p>', subtype="html")
    m.add_attachment(LHDN_TXT.encode(), maintype="text", subtype="plain", filename="n.txt")
    return m.as_bytes()


def test_eml_signals_and_attachment():
    docs = ingest.extract("m.eml", None, eml(reply="boss@other.example"))
    assert docs[0].kind == "eml" and "Notis LHDN" in docs[0].text and "[link: https://evil.example/pay]" in docs[0].text
    assert set(docs[0].signals) == {"mail_spf_fail", "mail_replyto_mismatch", "mail_link_mismatch", "mail_display_spoof"}
    assert docs[1].kind == "text"


def test_batch_summary_and_email_reasons():
    docs = ingest.extract("a.txt", None, LHDN_TXT.encode()) + ingest.extract("b.txt", None, SCAM_TXT.encode())
    docs.append(ingest._skipped("c.exe", "Files of type .exe are not accepted"))
    b = ingest.analyze_files(docs, "en", None)
    assert b.summary.total == 3 and b.summary.analysed == 2 and b.summary.skipped == 1
    assert b.summary.likely_scam == 1 and b.summary.no_signals + b.summary.caution == 1
    r = ingest.analyze_files(ingest.extract("m.eml", None, eml()), "en", None).files[0].result
    codes = {x.code for x in r.scam.reasons if x.kind == "risk"}
    assert {"mail_spf_fail", "mail_link_mismatch", "mail_display_spoof"} <= codes


def test_batch_caps_and_error_isolated():
    docs = [ingest.Doc(f"{i}.txt", "text", LHDN_TXT) for i in range(12)]
    b = ingest.analyze_files(docs, "en", None)
    assert b.summary.analysed == 10 and b.summary.skipped == 2
    img = ingest.analyze_files([ingest.Doc("s.png", "image", "", image=b"\x89PNG\r\n\x1a\nxx")], "en", None).files[0]
    assert img.status == "error"


def test_oversized_body_413_and_bad_inputs():
    big = b"a" * (ingest.MAX_BODY + 1)
    assert client.post("/api/analyze-file", content=big, headers={"X-Filename": "a.txt"}).status_code == 413
    assert client.post("/api/analyze-file?language=xx", content=b"hello world", headers={"X-Filename": "a.txt"}).status_code == 422
    assert client.post("/api/analyze-file", content=b"\x00\x01\x02", headers={"X-Filename": "a.bin"}).status_code == 415


def test_endpoint_txt_and_health():
    r = client.post("/api/analyze-file?language=en", content=SCAM_TXT.encode(), headers={"X-Filename": "m.txt", "Content-Type": "text/plain"})
    assert r.status_code == 200 and r.json()["summary"]["analysed"] == 1
    h = client.get("/api/health").json()
    assert h["upload"]["max_mb"] == 25 and "eml" in h["upload"]["types"] and "channels" in h
    assert not {"zip", "mp3", "wav"} & set(h["upload"]["types"]) and "audio_available" not in h["upload"]
    assert "whatsapp" not in h["channels"] and "messenger" in h["channels"]


def test_file_stream_sends_steps_then_result():
    r = client.post("/api/analyze-file/stream?language=en", content=SCAM_TXT.encode(), headers={"X-Filename": "m.txt", "Content-Type": "text/plain"})
    assert r.status_code == 200
    assert r.text.count("event: step") > 1 and "event: result" in r.text
