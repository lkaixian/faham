"""Flag-only Office checks: macros, remote templates, DDE. Nothing is opened as a document, run or saved.

Modern Office files are zips, so the member list and a few bounded reads are enough. Old .doc/.xls files are OLE containers; their
directory names are stored as UTF-16, so a byte search finds the macro storage without parsing the container ("probable", not proof).
Decompressing the VBA source to look for AutoOpen or Shell is deliberately not done: "contains macros" is what a reader needs.
"""
from __future__ import annotations

import io
import re
import zipfile

MACRO_EXT = {"docm", "dotm", "xlsm", "xltm", "xlam", "xlsb", "pptm", "potm", "ppsm", "ppam", "sldm"}
OLE_MAGIC = bytes.fromhex("d0cf11e0a1b11ae1")
OLE_MACRO = "_VBA_PROJECT".encode("utf-16-le")  # the storage every VBA-bearing .doc/.xls/.ppt carries
OLE_ENCRYPTED = "EncryptedPackage".encode("utf-16-le")  # a password-protected .docx/.xlsx is an OLE container holding this stream
MAX_PART, MAX_RELS = 2 * 1024 * 1024, 40
DDE = re.compile(r"ddeauto|instrtext[^>]*>\s*dde\b|w:instr=.\s*dde\b")


def _read(z: zipfile.ZipFile, name: str) -> str:
    try:
        with z.open(name) as f:
            return f.read(MAX_PART).decode("utf-8", "replace").lower()  # a bounded read: declared sizes are never trusted
    except Exception:
        return ""


def scan_ooxml(data: bytes, ext: str, via_chat: bool) -> list[str]:
    """Codes for a docx/xlsx/pptx-style zip: file_macro, file_macro_hidden, file_office_remote."""
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
        names = [n.lower() for n in z.namelist()[:5000]]
    except Exception:
        return []
    out: list[str] = []
    macro = any(n.endswith("vbaproject.bin") or "macrosheets/" in n for n in names)  # VBA project or Excel 4.0 macro sheets
    if macro:
        out.append("file_macro")
        if ext not in MACRO_EXT and via_chat:  # a macro container wearing a plain .docx/.xlsx name
            out.append("file_macro_hidden")
    rels = [n for n in names if n.endswith(".rels")][:MAX_RELS]
    remote = any(("attachedtemplate" in r or "oleobject" in r) and 'targetmode="external"' in r
                 for n in rels for r in re.findall(r"<relationship\b[^>]*>", _read(z, n)))
    if remote or DDE.search(_read(z, "word/document.xml")):
        out.append("file_office_remote")
    return out


def scan_ole(data: bytes) -> list[str]:
    """Codes for an old OLE2 Office file or a password-protected modern one."""
    head = data[:25 * 1024 * 1024]
    if OLE_ENCRYPTED in head:
        return ["file_encrypted"]
    return ["file_macro"] if OLE_MACRO in head else []
