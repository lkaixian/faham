"""Read the Android manifest (binary XML) of an APK with the stdlib. Nothing is run or installed.

The format is a flat run of little-endian chunks: a string pool, an optional resource map, then start/end element chunks
(AOSP frameworks/base/libs/androidfw/include/androidfw/ResourceTypes.h). Only package, permissions, services, receivers and a literal
app label are collected. Every read is bounds-checked and the walk is capped, so a hostile or broken manifest ends in
`ok=False` (which the caller treats as a sign), never an exception or a hang.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass, field

MAX_STRINGS, MAX_ELEMENTS, MAX_ATTRS = 50_000, 20_000, 256
RES_STRING_POOL, RES_START_ELEMENT, RES_END_ELEMENT, RES_XML_RESOURCE_MAP = 0x0001, 0x0102, 0x0103, 0x0180
RES_NAME, RES_LABEL, RES_PERMISSION = 0x01010003, 0x01010001, 0x01010006  # android:name, android:label, android:permission
TYPE_STRING = 3

# What each capability lets a scam app do, in plain words. The keys are what filecheck's rules look for.
PERMS = {
    "android.permission.READ_SMS": "sms", "android.permission.RECEIVE_SMS": "sms",
    "android.permission.SYSTEM_ALERT_WINDOW": "overlay",
    "android.permission.REQUEST_INSTALL_PACKAGES": "install",
}
BINDS = {
    "android.permission.BIND_ACCESSIBILITY_SERVICE": "accessibility",
    "android.permission.BIND_DEVICE_ADMIN": "admin",
    "android.permission.BIND_NOTIFICATION_LISTENER_SERVICE": "notification",
}
WORDS = {"sms": "read your text messages", "overlay": "draw over other apps",
         "install": "install other apps", "accessibility": "see and control your screen (accessibility)",
         "admin": "act as a device administrator", "notification": "read your notifications"}


@dataclass
class Manifest:
    ok: bool = False
    package: str = ""
    label: str = ""  # only when written as text; many apps store a resource reference instead
    permissions: list[str] = field(default_factory=list)
    caps: set[str] = field(default_factory=set)


def _u16(b: bytes, o: int) -> int:
    return struct.unpack_from("<H", b, o)[0]


def _u32(b: bytes, o: int) -> int:
    return struct.unpack_from("<I", b, o)[0]


def _pool(b: bytes, start: int, end: int) -> list[str]:
    """The string pool chunk at b[start:end]: UTF-8 or UTF-16 strings addressed by an offset table."""
    count, flags, base = _u32(b, start + 8), _u32(b, start + 16), _u32(b, start + 20)
    if count > MAX_STRINGS:
        raise ValueError("too many strings")
    hsize, utf8, out = _u16(b, start + 2), bool(flags & 0x100), []
    for i in range(count):
        p = start + base + _u32(b, start + hsize + 4 * i)
        if not start <= p < end:
            out.append("")
            continue
        if utf8:  # a char count then a byte count, each one or two bytes
            p += 2 if b[p] & 0x80 else 1
            n = b[p]
            n, p = ((n & 0x7F) << 8 | b[p + 1], p + 2) if n & 0x80 else (n, p + 1)
            out.append(b[p:min(p + n, end)].decode("utf-8", "replace"))
        else:  # UTF-16: a char count (one or two units) then the chars
            n = _u16(b, p)
            n, p = (((n & 0x7FFF) << 16) | _u16(b, p + 2), p + 4) if n & 0x8000 else (n, p + 2)
            out.append(b[p:min(p + 2 * n, end)].decode("utf-16-le", "replace"))
    return out


def parse_manifest(b: bytes) -> Manifest:
    m = Manifest()
    try:
        if len(b) < 16 or _u16(b, 0) != 0x0003:
            return m
        pos, strings, resmap, stack, elements = _u16(b, 2), [], [], [], 0
        while pos + 8 <= len(b):
            typ, hsize, size = _u16(b, pos), _u16(b, pos + 2), _u32(b, pos + 4)
            if size < 8 or hsize > size or pos + size > len(b):
                return m  # a chunk that runs past the end of the file
            end = pos + size
            if typ == RES_STRING_POOL:
                strings = _pool(b, pos, end)
            elif typ == RES_XML_RESOURCE_MAP:
                resmap = [_u32(b, o) for o in range(pos + hsize, end - 3, 4)][:MAX_STRINGS]
            elif typ == RES_START_ELEMENT:
                elements += 1
                if elements > MAX_ELEMENTS:
                    return m
                name = strings[_u32(b, pos + 20)] if _u32(b, pos + 20) < len(strings) else ""
                astart, asize, acount = _u16(b, pos + 24), _u16(b, pos + 26), min(_u16(b, pos + 28), MAX_ATTRS)
                attrs: dict[str, str] = {}
                for i in range(acount):
                    a = pos + 16 + astart + i * (asize or 20)
                    if a + 20 > end:
                        break
                    ni, raw, vtype, data = _u32(b, a + 4), _u32(b, a + 8), b[a + 15], _u32(b, a + 16)
                    rid = resmap[ni] if ni < len(resmap) else 0  # obfuscated manifests blank the names but keep the ids
                    key = {RES_NAME: "name", RES_LABEL: "label", RES_PERMISSION: "permission"}.get(rid) or (strings[ni] if ni < len(strings) else "")
                    si = raw if raw != 0xFFFFFFFF else (data if vtype == TYPE_STRING else -1)
                    if 0 <= si < len(strings):
                        attrs[key] = strings[si]
                stack.append(name)
                _element(m, name, attrs, stack)
            elif typ == RES_END_ELEMENT and stack:
                stack.pop()
            pos = end
        m.ok = bool(m.package)
    except (struct.error, IndexError, ValueError, UnicodeError, RecursionError):
        m.ok = False
    return m


def _element(m: Manifest, name: str, a: dict[str, str], stack: list[str]) -> None:
    if name == "manifest":
        m.package = a.get("package", "")[:200]
    elif name == "uses-permission" and a.get("name"):
        p = a["name"][:120]
        if len(m.permissions) < 300:
            m.permissions.append(p)
        if p in PERMS:
            m.caps.add(PERMS[p])
    elif name == "application" and a.get("label") and not a["label"].startswith("@"):
        m.label = a["label"][:100]
    elif name in ("service", "receiver") and a.get("permission") in BINDS:
        m.caps.add(BINDS[a["permission"]])


def facts(m: Manifest) -> str:
    """One neutral sentence for the explainer. The package and label are attacker-controlled: callers clean them."""
    asks = ", ".join(WORDS[c] for c in sorted(m.caps)) or "no sensitive powers"
    return f"App package: {m.package}." + (f" App name: {m.label}." if m.label else "") + f" It asks to: {asks}."
