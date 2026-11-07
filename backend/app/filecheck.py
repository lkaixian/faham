"""Static file-safety checks for files people get over WhatsApp, SMS and email.

Tulen is not an antivirus: these checks ask whether a file should have reached you, not whether its code is malicious.
Nothing is executed, installed or written to disk. Archives are listed; a few members are read in memory, a bounded number of
bytes at a time, against one shared budget per request (so a zip bomb cannot expand: the byte counter stops the read, whatever
the headers claim). Every finding is a code that scam_check turns into points; the codes live in i18n.TEXT. Weak codes can never
give "likely scam" alone (see FILE_WEAK in tools.py). The caller runs this in a limited child process (sandbox.py).
"""
from __future__ import annotations

import io
import json
import re
import struct
import zipfile

from . import apk as apkmod
from . import office, payload
from .config import DATA_DIR

try:  # RAR listing is pure Python. Reading inside a RAR needs an outside program, so it is switched off for good.
    import rarfile
    rarfile.NEED_COMMENTS = 0
    for _t in ("UNRAR_TOOL", "UNAR_TOOL", "BSDTAR_TOOL", "SEVENZIP_TOOL", "SEVENZIP2_TOOL"):
        setattr(rarfile, _t, "tulen-never-runs-a-tool")
except ImportError:  # pragma: no cover
    rarfile = None

MAX_ENTRIES, MAX_NAMES, MAX_MANIFEST = 5000, 20, 5 * 1024 * 1024
BUDGET_BYTES = 16 * 1024 * 1024  # all decompression for one request, however many members
MEMBER_CAP, SNIFF, HEAD_PROBES, DEEP_MEMBERS = 4 * 1024 * 1024, 8, 50, 10
KNOWN_APPS = json.loads((DATA_DIR / "known_apps.json").read_text(encoding="utf-8"))["apps"]
EXEC = {"exe", "scr", "msi", "bat", "cmd", "com", "pif", "ps1", "vbs", "vbe", "wsf", "wsh", "hta", "js", "jse", "jar", "dll"}
DISK = {"iso", "img", "lnk"}
ARCHIVE = {"zip", "7z", "rar", "tar", "gz", "cab"}
OFFICE_EXT = office.MACRO_EXT | {"docx", "xlsx", "pptx", "doc", "xls", "ppt"}
DOC = {"pdf", "doc", "docx", "xls", "xlsx", "jpg", "jpeg", "png", "txt", "mp4", "mp3", "ppt", "pptx"}
LURE = re.compile(r"jemputan|perkahwinan|kad|semak|saman|bil\b|resit|parcel|pos|notis|lhdn|jpj|pdrm|bank|invoice|statement|debt|denda", re.I)
DOC_STYLE = re.compile(r"pdf|doc|invoice|bil|resit|statement|notis|saman|jemputan|bukti|slip", re.I)
HIDDEN = re.compile("[‪-‮⁦-⁩​-‍﻿]")  # bidi overrides and zero-width characters
CTRL = re.compile(r"[\x00-\x1f\x7f]")
EOCD = b"PK\x05\x06"
ZIP_MAGIC, RAR_MAGIC, SEVENZ_MAGIC = (b"PK\x03\x04", b"PK\x05\x06"), bytes.fromhex("526172211a"), bytes.fromhex("377abcaf271c")


class Budget:
    """How many more bytes this request may decompress. Headers lie about sizes; this counter does not."""

    def __init__(self, left: int = BUDGET_BYTES) -> None:
        self.left, self.hit = left, False

    def allow(self, n: int) -> bool:
        """True if n more bytes may be read. A read that would overspend is refused whole: half a member proves nothing."""
        if n > self.left:
            self.hit = True
            return False
        return True


def clean(s: str, n: int = 80) -> str:
    """Names are attacker-controlled: strip control, bidi and zero-width characters before they are shown or analysed."""
    return CTRL.sub("", HIDDEN.sub("", s)).strip()[:n]


def _exts(name: str) -> list[str]:
    parts = name.rsplit("/", 1)[-1].lower().split(".")
    return parts[1:] if len(parts) > 1 else []


def _last(name: str) -> str:
    return (_exts(clean(name, 300)) or [""])[-1]


def _disguised(raw: str) -> bool:
    """A script or executable that tries not to look like one: hidden characters, a document extension in front, or padding."""
    e = _exts(clean(raw, 300))
    return bool(HIDDEN.search(raw)) or bool(re.search(r"\s{4,}\.\w+$", raw)) or (len(e) >= 2 and e[-1] in EXEC and e[-2] in DOC)


def _bad_path(n: str) -> bool:
    """Traversal, absolute paths, drive letters, alternate data streams."""
    parts = n.replace("\\", "/").split("/")
    return ".." in parts or n[:1] in "/\\" or bool(re.match(r"[A-Za-z]:", n)) or ":" in parts[-1]


def _eocd_count(data: bytes) -> int:
    """Real end-of-central-directory records (disk fields zero, comment fits). Two or more means appended archives."""
    n, p = 0, data.find(EOCD)
    while p >= 0:
        if len(data) >= p + 22 and data[p + 4:p + 8] == b"\0\0\0\0" and p + 22 + struct.unpack_from("<H", data, p + 20)[0] <= len(data):
            n += 1
        p = data.find(EOCD, p + 4)
    return n


def _blank() -> dict:
    return {"names": [], "encrypted": False, "unreadable": False, "tricks": False, "apk": False, "manifest": None, "read": None, "closed": False, "sizes": []}


def _zip_scan(data: bytes, budget: Budget) -> dict:
    """A look at a zip: names, encryption, odd compression, overlap, traversal, appended archives. `read(i, n)` returns at most n bytes of member i."""
    r = _blank()
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
    r["encrypted"] = any(i.flag_bits & 1 for i in infos)
    r["unreadable"] |= any(i.compress_type not in (0, 8) for i in infos)  # only stored and deflate are ever read (lzma and bzip2 can eat memory)

    def read(i: int, n: int) -> bytes | None:
        info = infos[i]
        if info.flag_bits & 1 or info.compress_type not in (0, 8) or not budget.allow(n):
            return None
        try:
            with z.open(info) as f:
                b = f.read(n)  # decompresses at most n bytes, whatever the member claims to hold
        except Exception:  # corrupt stream, bad checksum (a header that lies about the size ends here), bad header
            r["unreadable"] = True
            return None
        budget.left -= len(b)
        return b

    r["read"] = read
    r["sizes"] = [i.file_size for i in infos]  # what each header claims; compared with what a bounded read really yields
    r["apk"] = "AndroidManifest.xml" in r["names"]
    if r["apk"]:  # one bounded read of the manifest; a second manifest or a broken one is a sign, not a crash
        mans = [i for i, n in enumerate(r["names"]) if n == "AndroidManifest.xml"]
        r["tricks"] |= len(mans) > 1
        raw = read(mans[0], MAX_MANIFEST + 1)
        r["manifest"] = apkmod.parse_manifest(raw) if raw is not None and len(raw) <= MAX_MANIFEST else None
    r["tricks"] |= any(_bad_path(i.filename) for i in infos)
    offs = sorted((i.header_offset, 30 + len(i.filename.encode("utf-8", "ignore")) + i.compress_size) for i in infos)
    r["tricks"] |= any(a + size > b for (a, size), (b, _) in zip(offs, offs[1:]))  # entries that overlap: a Fifield-style bomb
    r["tricks"] |= _eocd_count(data) > 1
    return r


def _rar_scan(data: bytes) -> dict:
    """List a RAR with rarfile (pure Python). Nothing inside is read: that would need an outside program."""
    r = _blank()
    if rarfile is None:  # pragma: no cover
        r["closed"] = True
        return r
    try:
        rf = rarfile.RarFile(io.BytesIO(data))
        infos = rf.infolist()
        r["encrypted"] = bool(rf.needs_password()) or any(i.needs_password() for i in infos[:MAX_ENTRIES])
    except rarfile.RarCannotExec:  # an old archive comment would need a tool: say plainly that Tulen does not open this one
        r["closed"] = True
        return r
    except Exception:  # damaged, truncated, multi-volume part
        r["unreadable"] = True
        return r
    if len(infos) > MAX_ENTRIES:
        r["unreadable"] = True
        infos = infos[:MAX_ENTRIES]
    r["names"] = [i.filename for i in infos]
    r["tricks"] = any(_bad_path(i.filename) or i.is_symlink() for i in infos)
    r["unreadable"] |= not infos and not r["encrypted"]  # a RAR with nothing in it is not a real archive
    return r


def _brand(m: "apkmod.Manifest", name: str) -> str:
    """The brand an app claims (by file name, label or package) when its package is not one of that brand's known IDs, else empty."""
    hay = f"{name} {m.label} {m.package}".lower()
    for a in KNOWN_APPS:
        if any(re.search(rf"\b{re.escape(k.strip())}\b", hay) for k in a["keywords"]) and m.package not in a["packages"]:
            return a["brand"]
    return ""


def _members(scan: dict, via_chat: bool, depth: int, budget: Budget) -> tuple[list[str], list[str]]:
    """Look inside a plain zip: sniff the first bytes of up to 50 members, read up to 10 interesting ones (4 MB each) and inspect them."""
    codes, facts, deep, read = [], [], 0, scan["read"]
    for i, n in enumerate(scan["names"][:HEAD_PROBES]):
        head = read(i, SNIFF)
        if head is None:
            if budget.hit:
                break
            continue
        e = _last(n)
        if head[:2] == b"MZ" and e in DOC:  # a program wearing a document name
            codes.append("file_script_disguised")
        wants = e in EXEC or e == "apk" or e in OFFICE_EXT or e in ARCHIVE or head[:2] == b"MZ" or head[:4] in ZIP_MAGIC or head[:8] == office.OLE_MAGIC
        if wants and deep < DEEP_MEMBERS:
            deep += 1
            size = scan["sizes"][i]
            if size > MEMBER_CAP:
                continue  # too big to read inside the archive: its name already counts
            data = read(i, size)  # never more than the header admits (zipfile stops there, and a lie fails its checksum)
            if data is None:
                continue
            _, _, mcodes, mfacts = inspect(n, data, via_chat, depth + 1, budget)
            codes += mcodes
            if mfacts:
                facts.append(f"Inside {clean(n, 60)}: {mfacts}")
    if budget.hit:
        codes.append("file_unreadable")
    return codes, facts


def inspect(filename: str | None, data: bytes, via_chat: bool = False, depth: int = 0, budget: Budget | None = None) -> tuple[str, list[str], list[str], str]:
    """(kind label, names inside, signal codes, facts for the explainer). Safe on hostile input and never raises."""
    budget = budget or Budget()
    raw = (filename or "file").replace("\\", "/").rsplit("/", 1)[-1]
    name, ext = clean(raw), _last(raw)
    scan, extra, facts = _blank(), [], []
    if data[:4] in ZIP_MAGIC:
        scan = _zip_scan(data, budget)
        label = "Android app (APK)" if scan["apk"] or ext == "apk" else "ZIP archive"
        if "[Content_Types].xml" in scan["names"]:  # an Office file
            label, extra = "Office document", office.scan_ooxml(data, ext, via_chat)
    elif data[:8] == office.OLE_MAGIC:
        label, extra = "Old Office file", office.scan_ole(data)
    elif data[:5] == RAR_MAGIC:
        scan = _rar_scan(data)
        label = "RAR archive"
        if scan["closed"]:
            label = "archive that Tulen cannot open"
            extra.append("file_archive_closed")
    elif data[:6] == SEVENZ_MAGIC:
        extra.append("file_archive_closed")
        label = "archive that Tulen cannot open"
    elif data[:2] == b"MZ":
        label = "Windows program"
        c, f = payload.analyze_pe(data[:payload.HEAD])
        extra += c
        facts.append(f)
    else:
        label = "file"
        if ext in payload.SCRIPT_EXT:
            c, f = payload.analyze_script(data)
            extra += c
            facts.append(f)
    inner = [clean(n, 100) for n in scan["names"]]
    execs = [n for n in scan["names"] if _last(n) in EXEC]
    loose = ext in EXEC or data[:2] == b"MZ"
    codes: list[str] = []
    bad_name = (loose and (_disguised(raw) or (data[:2] == b"MZ" and ext in DOC))) or any(_disguised(n) for n in execs)
    if execs or loose:
        context = bad_name or via_chat or (label in ("ZIP archive", "RAR archive") and DOC_STYLE.search(name))
        codes.append("file_script_disguised" if context else "file_script")
    elif HIDDEN.search(raw):
        codes.append("file_name_trick")
    if scan["apk"] or ext == "apk":
        codes.append("file_apk")
        m = scan["manifest"]
        if m is None or not m.ok:
            codes.append("file_unreadable")  # a manifest that will not parse is itself a sign
        else:
            facts.append(apkmod.facts(m))
            claim, context = _brand(m, name), via_chat or bool(LURE.search(name))
            heavy = ("accessibility" in m.caps and len(m.caps) > 1) or {"sms", "overlay"} <= m.caps or {"sms", "notification"} <= m.caps
            if m.caps:
                codes.append("file_apk_perms")
            if heavy or (m.caps and context):
                codes.append("file_apk_takeover")
            if claim and (m.caps or via_chat):
                codes.append("file_apk_brand")
    elif any(_last(n) == "apk" for n in inner):
        codes.append("file_apk")  # an app tucked inside an archive
    if label == "ZIP archive" and scan["read"] and not scan["tricks"] and not scan["encrypted"] and depth == 0:
        mc, mf = _members(scan, via_chat, depth, budget)  # a flagged or protected archive is never decompressed
        extra += mc
        facts += mf
    if ext in DISK or any(_last(n) in DISK for n in inner):
        codes.append("file_disk_image")
    if scan["tricks"]:
        codes.append("file_zip_tricks")
    if scan["encrypted"]:
        codes.append("file_encrypted")
    if scan["unreadable"]:
        codes.append("file_unreadable")
    if codes and (LURE.search(name) or any(LURE.search(n) for n in inner[:MAX_NAMES])):
        codes.append("file_lure_name")
    codes = list(dict.fromkeys(codes + extra))
    if "file_script_disguised" in codes and "file_script" in codes:
        codes.remove("file_script")  # one script signal, the stronger one
    return label, inner, codes, clean(" ".join(f for f in facts if f), 600)


def describe(filename: str | None, label: str, inner: list[str], via_chat: bool, facts: str = "") -> str:
    """A neutral fact line the agent can read. Names are cleaned; the file's bytes never reach the agent."""
    dots = lambda n: n.replace(".", "․")  # .zip and .pdf are real web endings: keep names from being read as links
    s = f"Uploaded file: {dots(clean(filename or 'file'))}. Type: {label}."
    if inner:
        s += " Inside: " + ", ".join(dots(n) for n in inner[:MAX_NAMES]) + (f" and {len(inner) - MAX_NAMES} more." if len(inner) > MAX_NAMES else ".")
    s += " " + dots(facts) if facts else ""
    return s + (" The person says it arrived by chat, SMS or a link." if via_chat else "")
