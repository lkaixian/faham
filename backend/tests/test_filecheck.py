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


def test_apk_alone_is_only_caution():
    apk = zipped({"AndroidManifest.xml": b"x", "classes.dex": b"x"})
    assert codes("app.apk", apk) == ["file_apk"]
    assert verdict("app.apk", apk) == "caution"


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
