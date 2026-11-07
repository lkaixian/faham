"""File-safety checks (filecheck.py). Every fixture is built in code; nothing here is real malware."""
import io
import random
import struct
import zipfile

from fastapi.testclient import TestClient

from app import filecheck
from app.main import app

client = TestClient(app)


def zipped(files: dict[str, bytes | str]) -> bytes:
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w", zipfile.ZIP_DEFLATED) as z:
        for k, v in files.items():
            z.writestr(k, v)
    return b.getvalue()


def patch_cd(data: bytes, entry: int, offset: int, fmt: str, value: int) -> bytes:
    """Rewrite one field of the nth central-directory record (what a hostile zip does)."""
    p = -1
    for _ in range(entry + 1):
        p = data.index(b"PK\x01\x02", p + 1)
    out = bytearray(data)
    struct.pack_into(fmt, out, p + offset, value)
    return bytes(out)


def make_axml(package, perms=(), services=(), label=None, obfuscate=False):
    """A binary AndroidManifest.xml built with struct (UTF-16 pool). services: [(name, permission)]. obfuscate blanks the attribute
    names and keeps only the resource ids, the way packers do."""
    S = ["name", "label", "permission", "package", "manifest", "uses-permission", "application", "service"]
    ids = [0x01010003, 0x01010001, 0x01010006]
    def si(x):
        if x not in S:
            S.append(x)
        return S.index(x)
    def start(el, attrs):
        a = b"".join(struct.pack("<IIIHBBI", 0xFFFFFFFF, n, v, 8, 0, 3, v) for n, v in attrs)
        return struct.pack("<HHIIIIIHHHHHH", 0x102, 16, 36 + len(a), 1, 0xFFFFFFFF, 0xFFFFFFFF, si(el), 20, 20, len(attrs), 0, 0, 0) + a
    def end(el):
        return struct.pack("<HHIIIII", 0x103, 16, 24, 1, 0xFFFFFFFF, 0xFFFFFFFF, si(el))
    body = start("manifest", [(3, si(package))])
    for p in perms:
        body += start("uses-permission", [(0, si(p))]) + end("uses-permission")
    body += start("application", [(1, si(label))] if label else [])
    for n, perm in services:
        body += start("service", [(0, si(n)), (2, si(perm))]) + end("service")
    body += end("application") + end("manifest")
    shown = ["" if obfuscate and k < 3 else t for k, t in enumerate(S)]
    blobs = [struct.pack("<H", len(t)) + t.encode("utf-16-le") + b"\x00\x00" for t in shown]
    offs, o = [], 0
    for b in blobs:
        offs.append(o)
        o += len(b)
    pool_data = b"".join(blobs) + b"\x00" * (-o % 4)
    table = b"".join(struct.pack("<I", x) for x in offs)
    pool = struct.pack("<HHIIIIII", 1, 28, 28 + len(table) + len(pool_data), len(S), 0, 0, 28 + len(table), 0) + table + pool_data
    resmap = struct.pack("<HHI", 0x180, 8, 8 + 4 * len(ids)) + b"".join(struct.pack("<I", x) for x in ids)
    inner = pool + resmap + body
    return struct.pack("<HHI", 3, 8, 8 + len(inner)) + inner


def apk(package, perms=(), services=(), label=None, **kw):
    return zipped({"AndroidManifest.xml": make_axml(package, perms, services, label, **kw), "classes.dex": b"x"})


SMS, OVL = "android.permission.READ_SMS", "android.permission.SYSTEM_ALERT_WINDOW"
ACC = ("com.evil.Svc", "android.permission.BIND_ACCESSIBILITY_SERVICE")


def codes(name, data, via_chat=False):
    return filecheck.inspect(name, data, via_chat)[2]


def verdict(name, data, chat=False):
    h = {"X-Filename": name, "X-Via-Chat": "1" if chat else "0"}
    r = client.post("/api/analyze-file?language=en", content=data, headers=h)
    assert r.status_code == 200, r.text
    return r.json()["files"][0]["result"]["scam"]["verdict"]


def test_benign_zip_has_no_file_signals_and_never_reads_as_clear():
    z = zipped({"notice.pdf": b"%PDF-1.4", "photo.jpg": b"\xff\xd8\xff"})
    assert codes("documents.zip", z) == []
    assert verdict("documents.zip", z) == "caution"  # unknown sender: Tulen never says "no signals" for a file


def test_weak_signals_never_reach_likely_scam():
    enc = patch_cd(zipped({"a.txt": "hi"}), 0, 8, "<H", 1)  # encryption flag set
    assert "file_encrypted" in codes("a.zip", enc)
    assert verdict("a.zip", enc) == "caution"
    assert verdict("setup.exe", b"MZ" + b"\x00" * 60) == "caution"  # a bare program: strongest wording, still not a verdict


def test_disguised_or_chat_delivered_script_is_likely_scam():
    z = zipped({"Sila semak bil anda.pdf.exe": b"MZ"})
    assert "file_script_disguised" in codes("a.zip", z)
    assert verdict("a.zip", z) == "likely_scam"
    assert verdict("setup.exe", b"MZ" + b"\x00" * 60, chat=True) == "likely_scam"
    assert "file_script_disguised" in codes("jemputan.vbs", b"x" * 20, via_chat=True)


def test_name_tricks():
    assert "file_script_disguised" in codes("invoice‮gpj.exe", b"MZ")  # right-to-left override hides the real extension
    assert "file_script_disguised" in codes("slip.pdf.exe", b"MZ")
    assert "file_script_disguised" in codes("photo.jpg", b"MZ" + b"\x00" * 10)  # a program wearing an image name
    assert "file_name_trick" in codes("card​.zip", zipped({"a.txt": "x"}))
    assert "‮" not in filecheck.clean("a‮b\x00c")


def test_zip_tricks_are_strong():
    base = zipped({"a.txt": "a" * 50, "b.txt": "b" * 50})
    overlap = patch_cd(base, 1, 42, "<I", 10)  # second entry starts inside the first
    assert "file_zip_tricks" in codes("o.zip", overlap)
    assert "file_zip_tricks" in codes("c.zip", zipped({"a.txt": "x"}) + zipped({"b.txt": "y"}))  # appended archive
    assert "file_zip_tricks" in codes("t.zip", zipped({"../../evil.txt": "x"}))
    assert verdict("t.zip", zipped({"../../evil.txt": "x"})) == "likely_scam"
    assert "file_zip_tricks" not in codes("ok.zip", base)


def test_unreadable_is_a_weak_signal():
    odd = patch_cd(zipped({"a.txt": "hi"}), 0, 10, "<H", 99)  # unknown compression method (Konfety-style)
    assert "file_unreadable" in codes("a.zip", odd)
    assert "file_unreadable" in codes("x.zip", b"PK\x03\x04" + b"junk" * 10)
    assert "file_unreadable" in codes("x.7z", bytes.fromhex("377abcaf271c") + b"0" * 20)
    assert verdict("x.zip", b"PK\x03\x04" + b"junk" * 10) == "caution"


def test_lure_name_only_counts_with_another_signal():
    assert codes("JEMPUTAN MAJLIS PERKAHWINAN.pdf", b"%PDF-1.4") == []
    assert "file_lure_name" in codes("JEMPUTAN MAJLIS PERKAHWINAN.apk", zipped({"AndroidManifest.xml": b"x"}))


def test_hostile_input_never_raises():
    rnd = random.Random(7)
    good = zipped({f"f{i}.txt": "x" * 40 for i in range(20)})
    for _ in range(300):
        b = bytearray(good)
        for _ in range(rnd.randint(1, 8)):
            b[rnd.randrange(len(b))] = rnd.randrange(256)
        codes("x.zip", bytes(b[:rnd.randint(4, len(b))]))
    assert codes("big.zip", zipped({f"{i}.txt": "" for i in range(filecheck.MAX_ENTRIES + 10)}))  # over the entry cap: flagged, not read


def test_every_file_code_has_all_four_languages():
    from app.agent.i18n import TEXT
    from app.agent.tools import FILE_STRONG, FILE_WEAK
    for c in FILE_WEAK | FILE_STRONG:
        assert set(TEXT[c]) == {"en", "bm", "zh", "ta"}, c
        assert all(TEXT[c].values())
    assert not any(w in v.lower() for c in FILE_WEAK | FILE_STRONG for v in TEXT[c].values() for w in (" is safe", "virus-free", "no virus"))


def test_manifest_reader_reads_package_permissions_services_label():
    from app import apk as A
    m = A.parse_manifest(make_axml("com.example.pay", [SMS, OVL, "android.permission.INTERNET"], [ACC], "Pay"))
    assert m.ok and m.package == "com.example.pay" and m.label == "Pay"
    assert m.caps == {"sms", "overlay", "accessibility"} and "android.permission.INTERNET" in m.permissions
    o = A.parse_manifest(make_axml("com.example.pay", [SMS], obfuscate=True))  # attribute names blanked, resource ids kept
    assert o.ok and o.caps == {"sms"}


def test_apk_without_risky_powers_is_only_caution():
    a = apk("com.example.flashlight", ["android.permission.INTERNET"], label="Flashlight")
    assert codes("flashlight.apk", a) == ["file_apk"]
    assert verdict("flashlight.apk", a) == "caution"


def test_one_sensitive_power_alone_is_weak():
    a = apk("com.example.sms", [SMS], label="Messages")
    assert codes("sms.apk", a) == ["file_apk", "file_apk_perms"]
    assert verdict("sms.apk", a) == "caution"  # many innocent apps read SMS


def test_dangerous_combinations_are_likely_scam():
    assert "file_apk_takeover" in codes("a.apk", apk("com.x.a", [SMS], [ACC]))  # accessibility plus SMS
    assert "file_apk_takeover" in codes("b.apk", apk("com.x.b", [SMS, OVL]))  # the Tria profile
    assert verdict("b.apk", apk("com.x.b", [SMS, OVL])) == "likely_scam"
    assert "file_apk_takeover" not in codes("c.apk", apk("com.x.c", [SMS]))
    assert "file_apk_takeover" in codes("c.apk", apk("com.x.c", [SMS]), via_chat=True)  # one power plus a chat lure
    assert "file_apk_takeover" in codes("JEMPUTAN KAHWIN.apk", apk("com.x.c", [OVL]))  # one power plus a lure name


def test_brand_claim_needs_power_or_chat_and_ignores_the_real_package():
    fake = apk("com.evil.secure", [SMS], label="Maybank Secure")
    assert "file_apk_brand" in codes("update.apk", fake)
    assert "file_apk_brand" not in codes("update.apk", apk("com.evil.secure", [], label="Maybank Secure"))  # no power, no chat
    assert "file_apk_brand" in codes("update.apk", apk("com.evil.secure", [], label="Maybank Secure"), via_chat=True)
    assert "file_apk_brand" not in codes("maybank.apk", apk("com.maybank2u.life", [SMS], label="MAE"))  # the real ID is not a claim
    assert "file_apk_brand" in codes("x.apk", apk("com.maybank.update", [SMS]))  # claim made by the package name


def test_broken_or_hostile_manifest_is_a_sign_not_a_crash():
    broken = zipped({"AndroidManifest.xml": b"not binary xml at all", "classes.dex": b"x"})
    assert codes("b.apk", broken) == ["file_apk", "file_unreadable"]
    assert verdict("b.apk", broken) == "caution"
    good = make_axml("com.x.y", [SMS, OVL], [ACC], "L")
    rnd = random.Random(11)
    from app import apk as A
    for _ in range(500):
        b = bytearray(good)
        for _ in range(rnd.randint(1, 10)):
            b[rnd.randrange(len(b))] = rnd.randrange(256)
        A.parse_manifest(bytes(b[:rnd.randint(1, len(b))]))  # must return, never raise or hang
    assert not A.parse_manifest(good[:40]).ok


def test_two_manifests_and_a_fake_apk_name():
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr("AndroidManifest.xml", make_axml("com.a.a", [SMS]))
        z.writestr("AndroidManifest.xml", make_axml("com.b.b", [OVL]))
    assert "file_zip_tricks" in codes("d.apk", b.getvalue())
    assert "file_unreadable" in codes("photo.apk", b"hello world, not a zip")
