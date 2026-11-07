"""Read scripts and Windows programs without running them: text patterns for scripts, header fields for .exe files.

Tulen is not an antivirus. This only reports what a reader can see in the first bytes (a script that downloads and starts
something, a program that is packed or unsigned) so the result can say why a file does not look like a letter. Everything is
bounded and bytes-in, facts-out: no import, no execution, no file written.
"""
from __future__ import annotations

import re
import struct

HEAD = 64 * 1024  # how much of a script or program is looked at
SCRIPT_EXT = {"vbs", "vbe", "js", "jse", "wsf", "wsh", "hta", "bat", "cmd", "ps1"}
DOWNLOAD = re.compile(r"xmlhttp|urldownloadtofile|downloadfile|downloadstring|invoke-webrequest|\biwr\b|adodb\.stream|bitsadmin|"
                      r"certutil[^\n]{0,60}urlcache|winhttp|start-bitstransfer|\bwget\b|\bcurl\b")
RUN = re.compile(r"wscript\.shell|\.run\b|\.exec\b|shell\.application|start-process|invoke-expression|\biex\b|createprocess|"
                 r"cmd(?:\.exe)?\s*/c|powershell|mshta|rundll32|regsvr32")
SCRAMBLED = re.compile(r"frombase64string|-enc(?:odedcommand)?\b|(?:chr|chrw)\(\s*\d+\s*\)\s*&\s*(?:chr|chrw)\(|\beval\(|\bexecute\(")
PACKERS = (b"upx0", b"upx1", b"upx2", b".aspack", b".adata", b".petite", b".mpress", b".themida", b".vmp0", b".vmp1", b"mew")


def _text(b: bytes) -> str:
    b = b[:HEAD]
    if b[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return b.decode("utf-16", "replace").lower()
    return b.decode("utf-8", "replace").lower()


def analyze_script(b: bytes) -> tuple[list[str], str]:
    """(codes, facts) for a script's text. A script that fetches something and starts it is strong; the rest is only described."""
    t = _text(b)
    dl, run, scr = bool(DOWNLOAD.search(t)), bool(RUN.search(t)), bool(SCRAMBLED.search(t))
    seen = [w for w, on in (("downloads from the internet", dl), ("starts other programs", run), ("contains scrambled text", scr)) if on]
    codes = ["file_script_dropper"] if (dl and run) or (scr and run) else []
    return codes, ("Script " + ", ".join(seen) + "." if seen else "")


def analyze_pe(b: bytes) -> tuple[list[str], str]:
    """(codes, facts) from a Windows program's header. Every offset is checked; anything odd returns nothing."""
    try:
        if b[:2] != b"MZ" or len(b) < 0x40:
            return [], ""
        pe = struct.unpack_from("<I", b, 0x3C)[0]
        if pe + 24 > len(b) or b[pe:pe + 4] != b"PE\0\0":
            return [], ""
        _, nsec, _, _, _, optsize, chars = struct.unpack_from("<HHIIIHH", b, pe + 4)
        opt = pe + 24
        magic = struct.unpack_from("<H", b, opt)[0]
        dirs = opt + (112 if magic == 0x20B else 96)
        signed = dirs + 40 <= len(b) and struct.unpack_from("<II", b, dirs + 32)[1] > 0  # data directory 4: the certificate table
        names = [b[o:o + 8].rstrip(b"\0").lower() for o in range(opt + optsize, opt + optsize + 40 * min(nsec, 96), 40) if o + 8 <= len(b)]
        packed = any(n in PACKERS or n.startswith(b"upx") for n in names)
        kind = ("library" if chars & 0x2000 else "program") + (" (64-bit)" if magic == 0x20B else " (32-bit)")
        facts = f"Windows {kind}, " + ("carries a digital signature that Tulen did not check" if signed else "has no digital signature") + (", packed or scrambled" if packed else "") + "."
        return (["file_exe_packed"] if packed else []), facts
    except (struct.error, IndexError):
        return [], ""
