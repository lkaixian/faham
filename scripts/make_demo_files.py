"""Builds the fictional, harmless files used in the demo video into ./demo-files/ (ignored by git).

    cd backend && python ../scripts/make_demo_files.py

Nothing here is malware: the "program" is two bytes ("MZ") and zeros, the "app" is a hand-built manifest with no code, the "macro"
file is a zip that merely contains a file named vbaProject.bin. They exist so Tulen has something realistic to look at. Every file
name says SAMPEL so the video can never be mistaken for a real scam. Rule 5.4: no real names, numbers or addresses anywhere.
"""
import shutil
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

from tests.test_filecheck import SMS, OVL, apk, docx_zip, zipped  # noqa: E402
from tests.test_filecheck_deep import make_pe  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "demo-files"
OUT.mkdir(exist_ok=True)

files = {
    # Scene C1: a ZIP that WhatsApp contacts forward. A "PDF" that is really a program. Tick "I got this on WhatsApp".
    "C1_SAMPEL_bil-anda.zip": zipped({"Sila semak bil anda.pdf.exe": make_pe()}),
    # Scene C2: an Android app that asks to read SMS and draw over other apps, named like a wedding card.
    "C2_SAMPEL_JEMPUTAN-MAJLIS-PERKAHWINAN.apk": apk("com.sampel.kad", [SMS, OVL], label="Kad Jemputan"),
    # Scene C3: a harmless ZIP of two PDFs: Tulen finds nothing wrong, and says it is not a letter either (never "safe").
    "C3_SAMPEL_penyata-gaji.zip": zipped({"jan.pdf": b"%PDF-1.4 SAMPEL", "feb.pdf": b"%PDF-1.4 SAMPEL"}),
    # Scene C4 (optional): a Word file that hides a macro container under a plain .docx name. Tick "I got this on WhatsApp".
    "C4_SAMPEL_notis-lhdn.docx": docx_zip({"word/vbaProject.bin": "SAMPEL"}),
}
for name, data in files.items():
    (OUT / name).write_bytes(data)

# Scene C5 (optional): an ordinary download in a RAR (a tiny archive from the rarfile project's own tests): "not a letter", ask the sender.
rar = BACKEND / "tests" / "fixtures" / "rar" / "rar5-solid.rar"
if rar.exists():
    shutil.copy(rar, OUT / "C5_SAMPEL_perisian.rar")

# Scene A: a fictional loan SMS to paste (the agent looks the bank up and reads its own website).
(OUT / "A_SAMPEL_sms-pinjaman.txt").write_text(
    "SAMPEL, FIKTIF.\nRHB Bank: Tahniah! Anda layak mendapat pinjaman peribadi sehingga RM30,000 tanpa dokumen. "
    "Balas YA untuk teruskan. Tawaran terhad.\n", encoding="utf-8")
print("built", len(list(OUT.iterdir())), "files in", OUT)
