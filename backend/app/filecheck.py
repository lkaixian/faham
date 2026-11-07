"""Static file-safety checks for files people get over WhatsApp, SMS and email.

Names, magic bytes and the archive listing only. Nothing is extracted, executed or saved, and no member is
decompressed, so a zip bomb has nothing to bomb. Every finding is a code that scam_check turns into points;
the codes live in i18n.TEXT. Weak codes can never give "likely scam" alone (see FILE_WEAK in tools.py).
"""
from __future__ import annotations

import io
import re
import struct
import zipfile

MAX_ENTRIES, MAX_NAMES = 5000, 20
EXEC = {"exe", "scr", "msi", "bat", "cmd", "com", "pif", "ps1", "vbs", "vbe", "wsf", "wsh", "hta", "js", "jse", "jar", "dll"}
DISK = {"iso", "img", "lnk"}
ARCHIVE = {"zip", "7z", "rar", "tar", "gz", "cab"}
DOC = {"pdf", "doc", "docx", "xls", "xlsx", "jpg", "jpeg", "png", "txt", "mp4", "mp3", "ppt", "pptx"}
LURE = re.compile(r"jemputan|perkahwinan|kad|semak|saman|bil\b|resit|parcel|pos|notis|lhdn|jpj|pdrm|bank|invoice|statement|debt|denda", re.I)
DOC_STYLE = re.compile(r"pdf|doc|invoice|bil|resit|statement|notis|saman|jemputan|bukti|slip", re.I)
HIDDEN = re.compile("[‪-‮⁦-⁩​-‍﻿]")  # bidi overrides and zero-width characters
CTRL = re.compile(r"[\x00-\x1f\x7f]")
EOCD = b"PK\x05\x06"


def clean(s: str, n: int = 80) -> str:
    """Names are attacker-controlled: strip control, bidi and zero-width characters before they are shown or analysed."""
    return CTRL.sub("", HIDDEN.sub("", s)).strip()[:n]


def _exts(name: str) -> list[str]:
    parts = name.rsplit("/", 1)[-1].lower().split(".")
    return parts[1:] if len(parts) > 1 else []


def _disguised(raw: str) -> bool:
    """A script or executable that tries not to look like one: hidden characters, a document extension in front, or padding."""
    e = _exts(clean(raw, 300))
    return bool(HIDDEN.search(raw)) or bool(re.search(r"\s{4,}\.\w+$", raw)) or (len(e) >= 2 and e[-1] in EXEC and e[-2] in DOC)


def _eocd_count(data: bytes) -> int:
    """Real end-of-central-directory records (disk fields zero, comment fits). Two or more means appended archives."""
    n, p = 0, data.find(EOCD)
    while p >= 0:
        if len(data) >= p + 22 and data[p + 4:p + 8] == b"\0\0\0\0" and p + 22 + struct.unpack_from("<H", data, p + 20)[0] <= len(data):
            n += 1
        p = data.find(EOCD, p + 4)
    return n


def _zip_scan(data: bytes) -> dict:
    """Listing-only look at a zip: names, encryption, odd compression, overlap, traversal, appended archives."""
    r = {"names": [], "encrypted": False, "unreadable": False, "tricks": False, "apk": False}
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
        infos = z.infolist()
    except (zipfile.BadZipFile, ValueError, OSError, NotImplementedError):
        r["unreadable"] = True
        return r
    if len(infos) > MAX_ENTRIES:
        r["unreadable"] = True
        infos = infos[:MAX_ENTRIES]
    r["names"] = [i.filename for i in infos]
    r["apk"] = "AndroidManifest.xml" in r["names"]
    r["encrypted"] = any(i.flag_bits & 1 for i in infos)
    r["unreadable"] |= any(i.compress_type not in (0, 8) for i in infos)
    for i in infos:  # traversal, absolute paths, drive letters, alternate data streams
        parts = i.filename.replace("\\", "/").split("/")
        if ".." in parts or i.filename[:1] in "/\\" or re.match(r"[A-Za-z]:", i.filename) or ":" in parts[-1]:
            r["tricks"] = True
    offs = sorted((i.header_offset, 30 + len(i.filename.encode("utf-8", "ignore")) + i.compress_size) for i in infos)
    r["tricks"] |= any(a + size > b for (a, size), (b, _) in zip(offs, offs[1:]))  # entries that overlap: a Fifield-style bomb
    r["tricks"] |= _eocd_count(data) > 1
    return r


def inspect(filename: str | None, data: bytes, via_chat: bool = False) -> tuple[str, list[str], list[str]]:
    """(kind label, names inside, signal codes). Pure and cheap: safe on hostile input, never raises."""
    raw = (filename or "file").replace("\\", "/").rsplit("/", 1)[-1]
    name, ext = clean(raw), (_exts(clean(raw)) or [""])[-1]
    scan = {"names": [], "encrypted": False, "unreadable": False, "tricks": False, "apk": False}
    if data[:4] in (b"PK\x03\x04", b"PK\x05\x06"):
        scan = _zip_scan(data)
        label = "Android app (APK)" if scan["apk"] or ext == "apk" else "ZIP archive"
    elif data[:6] in (b"7z\xbc\xaf\x27\x1c",) or data[:5] == b"Rar!\x1a":
        scan["unreadable"], label = True, "archive that Tulen cannot open"
    elif data[:2] == b"MZ":
        label = "Windows program"
    else:
        label = "file"
    inner = [clean(n, 100) for n in scan["names"]]
    execs = [n for n in scan["names"] if (_exts(clean(n, 300)) or [""])[-1] in EXEC]
    loose = ext in EXEC or data[:2] == b"MZ"
    codes: list[str] = []
    bad_name = (loose and (_disguised(raw) or (data[:2] == b"MZ" and ext in DOC))) or any(_disguised(n) for n in execs)
    if execs or loose:
        context = bad_name or via_chat or (label == "ZIP archive" and DOC_STYLE.search(name))
        codes.append("file_script_disguised" if context else "file_script")
    elif HIDDEN.search(raw):
        codes.append("file_name_trick")
    if scan["apk"] or ext == "apk":
        codes.append("file_apk")
    if ext in DISK or any((_exts(n) or [""])[-1] in DISK for n in inner):
        codes.append("file_disk_image")
    if scan["tricks"]:
        codes.append("file_zip_tricks")
    if scan["encrypted"]:
        codes.append("file_encrypted")
    if scan["unreadable"]:
        codes.append("file_unreadable")
    if codes and (LURE.search(name) or any(LURE.search(n) for n in inner[:MAX_NAMES])):
        codes.append("file_lure_name")
    return label, inner, codes


def describe(filename: str | None, label: str, inner: list[str], via_chat: bool) -> str:
    """A neutral fact line the agent can read. Names are cleaned; the file's bytes never reach the agent."""
    dots = lambda n: n.replace(".", "․")  # .zip and .pdf are real web endings: keep names from being read as links
    s = f"Uploaded file: {dots(clean(filename or 'file'))}. Type: {label}."
    if inner:
        s += " Inside: " + ", ".join(dots(n) for n in inner[:MAX_NAMES]) + (f" and {len(inner) - MAX_NAMES} more." if len(inner) > MAX_NAMES else ".")
    return s + (" The person says it arrived by chat, SMS or a link." if via_chat else "")
