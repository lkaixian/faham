"""FAHAM agent tools.

Each tool is a plain, typed function registered in TOOLS so the orchestrator
can call it by name and log the call in the reasoning trace. Tools are
deterministic and offline-friendly; the LLM is only used to polish wording.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable
from urllib.parse import urlparse

from .. import llm
from ..config import DATA_DIR

SOURCES: dict = {k: v for k, v in json.loads((DATA_DIR / "official_sources.json").read_text(encoding="utf-8")).items() if not k.startswith("_")}
OFFICES: dict = json.loads((DATA_DIR / "offices.json").read_text(encoding="utf-8"))


@dataclass
class Tool:
    name: str
    description: str
    fn: Callable


TOOLS: dict[str, Tool] = {}


def tool(name: str, description: str):
    def deco(fn):
        TOOLS[name] = Tool(name, description, fn)
        return fn
    return deco


# ---------------------------------------------------------------- read
@tool("ocr.read", "Image or PDF to text. Falls back to the given text.")
def ocr_read(text: str | None = None, image_bytes: bytes | None = None) -> str:
    if image_bytes:
        try:
            import io

            import pytesseract
            from PIL import Image

            return pytesseract.image_to_string(Image.open(io.BytesIO(image_bytes)), lang="msa+eng")
        except Exception:  # OCR not installed — caller must supply text
            pass
    return text or ""


IC_RE = re.compile(r"\b\d{6}-?\d{2}-?\d{4}\b")
PHONE_RE = re.compile(r"(?<!\w)(?:\+?60|0)1\d[-\s]?\d{3,4}[-\s]?\d{4}\b")
LANDLINE_RE = re.compile(r"(?<!\w)(?:\+60[-\s]?|0)[3-9][-\s]?\d{3,4}[-\s]?\d{4}\b")
ACCOUNT_RE = re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}(?:[-\s]?\d{1,4})?\b")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
# Whole line is masked: starts with "No." or has Jalan/Lorong/Taman, plus a 5-digit postcode on it or the next line.
ADDRESS_RE = re.compile(r"^[ \t]*(?:No\.|[^\n]*?\b(?:Jalan|Lorong|Taman)\b)[^\n]*?(?:\b\d{5}\b|\n[ \t]*\d{5}\b)[^\n]*", re.IGNORECASE | re.MULTILINE)
# ponytail: 1-3 letters + 1-4 digits; may over-mask odd uppercase tokens (RM excluded). Tighten with a state-prefix list if it bites.
PLATE_RE = re.compile(r"(?<![\w/-])(?!RM\b)[A-Z]{1,3} ?[1-9]\d{0,3}(?: ?[A-Z])?(?![\w/-])")
NAME_RE = re.compile(r"((?:Kepada|Nama)\s*:\s*)([^,\n\[]+)", re.IGNORECASE)
# Malay/Indian name forms anywhere in the text: ALI BIN ABU, SITI BINTI HASAN, RAJU A/L MUTHU.
PATRONYM_RE = re.compile(r"\b(?:[A-Z][A-Z'.@]+[ \t]+){1,3}(?:BIN|BINTI|BT|B\.|A/L|A/P|S/O|D/O|ANAK)[ \t]+[A-Z][A-Z'.@]+(?:[ \t]+[A-Z][A-Z'.@]+){0,3}")
PASSPORT_RE = re.compile(r"\b[A-Z]\d{7,8}\b")
DOB_RE = re.compile(r"((?:Tarikh\s+lahir|Date\s+of\s+birth|DOB)\s*:\s*)[^\n]+", re.IGNORECASE)
# Final sweep: any leftover run of 8+ digits (spaces/dashes allowed) is masked rather than trusted.
SWEEP_RE = re.compile(r"(?<![\w/])(?:\d[ -]?){8,}\d(?![\w/])")
TITLE_NAME_RE = re.compile(r"\b((?:Encik|Puan|Cik|Tuan|Dato['’]?)[ \t]+)([A-Z][A-Z'.@]+(?:[ \t]+[A-Z][A-Z'.@/]+)+)")


@tool("privacy.redact", "Mask IC numbers, phones, account numbers, emails, addresses, plates and names before processing.")
def redact(text: str) -> tuple[str, dict[str, int]]:
    # Decision: all phone numbers are masked, including official agency lines.
    counts = {"ic": 0, "phone": 0, "account": 0, "name": 0, "email": 0, "address": 0, "plate": 0, "id": 0, "dob": 0, "other": 0}

    def sub(pattern, label, key, s):
        def repl(_):
            counts[key] += 1
            return f"[{label}]"
        return pattern.sub(repl, s)

    out = sub(IC_RE, "IC", "ic", text)
    out = sub(EMAIL_RE, "EMAIL", "email", out)
    out = sub(PHONE_RE, "PHONE", "phone", out)
    out = sub(LANDLINE_RE, "PHONE", "phone", out)
    out = sub(ACCOUNT_RE, "ACCOUNT", "account", out)
    out = sub(ADDRESS_RE, "ADDRESS", "address", out)
    out = sub(PLATE_RE, "PLATE", "plate", out)

    def name_repl(m):
        counts["name"] += 1
        return m.group(1) + "[NAME]"

    out = NAME_RE.sub(name_repl, out)
    out = TITLE_NAME_RE.sub(name_repl, out)
    out = PATRONYM_RE.sub(lambda m: (counts.__setitem__("name", counts["name"] + 1), "[NAME]")[1], out)
    out = sub(PASSPORT_RE, "ID", "id", out)
    out = DOB_RE.sub(lambda m: (counts.__setitem__("dob", counts["dob"] + 1), m.group(1) + "[DOB]")[1], out)
    out = sub(SWEEP_RE, "NUMBER", "other", out)
    return out, counts


@tool("classify.issuer", "Identify the issuing agency from keywords and domains.")
def classify_issuer(text: str) -> tuple[str, float]:
    low = text.lower()
    best, best_hits = "UNKNOWN", 0
    for key, src in SOURCES.items():
        hits = sum(low.count(k) for k in src["keywords"]) + 2 * sum(low.count(d) for d in src["domains"] if d != ".gov.my")
        if hits > best_hits:
            best, best_hits = key, hits
    confidence = min(0.99, 0.5 + 0.1 * best_hits) if best_hits else 0.2
    return best, round(confidence, 2)


AMOUNT_RE = re.compile(r"RM\s?([\d,]+(?:\.\d{2})?)", re.IGNORECASE)
MONTHS = "januari|februari|mac|april|mei|jun|julai|ogos|september|oktober|november|disember|january|february|march|may|june|july|august|october|december"
DATE_RE = re.compile(rf"\b(\d{{1,2}}\s+(?:{MONTHS})\s+\d{{4}})\b", re.IGNORECASE)
REF_RE = re.compile(r"\b([A-Z]{2,6}(?:/[A-Z0-9]+){2,})\b")


@tool("extract.fields", "Extract amount, deadline and reference number.")
def extract_fields(text: str) -> dict:
    amounts = AMOUNT_RE.findall(text)
    dates = DATE_RE.findall(text)
    ref = REF_RE.search(text)
    deadline = None
    m = re.search(rf"(?:sebelum|before|selewat-lewatnya)\s+({DATE_RE.pattern})", text, re.IGNORECASE)
    if m:
        deadline = m.group(1)
    elif dates:
        deadline = dates[-1]
    if not deadline and re.search(r"24\s*jam|24\s*hours", text, re.IGNORECASE):
        deadline = "24 hours (pressure tactic)"
    return {
        "amount": f"RM {amounts[0]}" if amounts else None,
        "deadline": deadline,
        "reference": ref.group(1) if ref else None,
    }


# ---------------------------------------------------------------- verify
URL_RE = re.compile(r"\b((?:https?://)?(?:[a-z0-9-]+\.)+[a-z]{2,}(?:/[^\s]*)?)", re.IGNORECASE)
SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "s.id", "cutt.ly", "shorturl.at", "rb.gy"}

RED_FLAGS: list[tuple[str, str]] = [
    (r"akaun\s+(?:peribadi|maybank|cimb|public bank|rhb|bank islam)|personal account|(?:bayar|transfer|pindah)\w*[^.\n]{0,40}akaun[^.\n]{0,40}atas nama", "Asks you to transfer money to a personal or company account"),
    (r"24\s*jam|24\s*hours|dalam\s+(?:masa\s+)?\d+\s*jam|hari ini sahaja|today only", "Creates fake urgency"),
    (r"waran\s+tangkap|arrest|ditangkap", "Threatens arrest"),
    (r"\btac\b|\botp\b|kata laluan|password", "Asks for a TAC, OTP or password"),
    (r"whatsapp|telegram|wasap", "Moves you to a chat app"),
    (r"jangan\s+beritahu|(?:simpan|jaga|kekalkan)\s+(?:ini\s+)?\brahsia\b|keep (?:it )?secret", "Asks you to keep it secret"),
    (r"gambar\s+ic|ic\s+depan|photo of (?:your )?ic", "Asks for photos of your IC"),
    (r"diskaun\s+\d+%", "Offers an unusual discount"),
]


def _domains(text: str) -> list[str]:
    out = []
    for u in URL_RE.findall(text):
        host = urlparse(u if "://" in u else "http://" + u).hostname or ""
        if "." in host and not host.replace(".", "").isdigit():
            out.append(host.lower())
    return out


@tool("scam.check", "Domain allowlist + red-flag rules. Returns verdict and evidence.")
def scam_check(text: str, issuer: str) -> dict:
    low = text.lower()
    flags = [msg for pat, msg in RED_FLAGS if re.search(pat, low)]
    good: list[str] = []
    official = SOURCES.get(issuer, {}).get("domains", [])
    for d in _domains(text):
        if d in SHORTENERS:
            flags.append(f"Shortened link ({d}) instead of an official site")
        elif d.endswith(".gov.my") or any(d == o or d.endswith("." + o) for o in official if o != ".gov.my"):
            good.append(f"Link points to official domain {d}")
        else:
            flags.append(f"Unofficial domain {d}")
    if issuer != "UNKNOWN" and not flags:
        good.append(f"Content matches a known {issuer} letter pattern")
    if REF_RE.search(text):
        good.append("Reference number in an official-looking format")
    score = max(0, min(100, 80 + 5 * len(good) - 22 * len(flags)))
    return {"genuine": score >= 60, "score": score, "red_flags": flags, "good_signs": good}


# ---------------------------------------------------------------- explain / teach
TEMPLATES = {
    "bm": "Surat ini daripada {issuer} ({ltype}).{amount}{deadline} Ikut langkah di bawah melalui saluran rasmi sahaja.",
    "en": "This letter is from {issuer} ({ltype}).{amount}{deadline} Follow the steps below using official channels only.",
    "zh": "这封信来自 {issuer}（{ltype}）。{amount}{deadline} 请只通过官方渠道按照以下步骤处理。",
    "ta": "இந்தக் கடிதம் {issuer} அனுப்பியது ({ltype}).{amount}{deadline} கீழே உள்ள படிகளை அதிகாரப்பூர்வ வழிகளில் மட்டும் பின்பற்றவும்.",
}
SCAM_TEMPLATES = {
    "bm": "Mesej ini kelihatan seperti SCAM. Jangan klik pautan atau buat bayaran. Semak sendiri melalui saluran rasmi dan hubungi NSRC 997 jika anda sudah tertipu.",
    "en": "This message looks like a SCAM. Do not click links or pay. Check yourself through official channels and call NSRC 997 if you have already been tricked.",
    "zh": "这条信息看起来是诈骗。不要点击链接或付款。请通过官方渠道自行查证；如已受骗，请拨打 NSRC 997。",
    "ta": "இந்தச் செய்தி மோசடி போலத் தெரிகிறது. இணைப்பைக் கிளிக் செய்யவோ பணம் செலுத்தவோ வேண்டாம். அதிகாரப்பூர்வ வழிகளில் சரிபார்க்கவும்; ஏமாற்றப்பட்டிருந்தால் NSRC 997-ஐ அழைக்கவும்.",
}
PIECES = {
    "bm": (" Jumlah: {a}.", " Tarikh akhir: {d}."),
    "en": (" Amount: {a}.", " Deadline: {d}."),
    "zh": (" 金额：{a}。", " 截止日期：{d}。"),
    "ta": (" தொகை: {a}.", " கடைசி நாள்: {d}."),
}


def _only_known_domains(generated: str, letter: str) -> bool:
    """Reject model text that names a website not in the letter or the official registry (e.g. hasil -> results)."""
    known = set(_domains(letter)) | {d for s in SOURCES.values() for d in s["domains"]}
    return all(any(d == k or d.endswith("." + k) for k in known) for d in _domains(generated))


@tool("llm.explain", "Plain-language explanation in the user's language (LLM optional).")
def explain(redacted_text: str, issuer: str, fields: dict, genuine: bool, language: str) -> str:
    if not genuine:
        return SCAM_TEMPLATES[language]
    generated = llm.complete(f"Explain this official letter:\n\n{redacted_text}", language)
    if generated and _only_known_domains(generated, redacted_text):
        return generated
    src = SOURCES.get(issuer, {})
    a, d = PIECES[language]
    return TEMPLATES[language].format(
        issuer=src.get("name", "an unknown sender"),
        ltype=src.get("letter_type", "notice"),
        amount=a.format(a=fields["amount"]) if fields.get("amount") else "",
        deadline=d.format(d=fields["deadline"]) if fields.get("deadline") else "",
    )


@tool("teach.lesson", "Create the 'Kenapa saya dapat surat ini?' card and glossary terms.")
def teach(issuer: str, genuine: bool) -> dict:
    key = issuer if genuine else "PDRM"
    src = SOURCES.get(key) or SOURCES["PDRM"]
    if not genuine:
        return {"question": "Kenapa saya dapat mesej ini?",
                "answer": "Scammers copy official words and add a short deadline so you act before you think or ask someone.",
                "terms": ["Waran tangkap", "NSRC 997", "Domain rasmi"]}
    return {"question": src["lesson"]["q"], "answer": src["lesson"]["a"], "terms": src["terms"]}


# ---------------------------------------------------------------- route / act
@tool("gov.retrieve", "Get current steps from the official source registry.")
def retrieve(issuer: str, genuine: bool) -> dict:
    src = SOURCES.get(issuer) if genuine else SOURCES["PDRM"]
    if not src:
        return {"online_steps": ["Find the agency's official .gov.my site yourself and check there."],
                "walkin_steps": ["Visit the agency counter with the letter and IC."],
                "prepare_online": ["IC number"], "prepare_walkin": ["IC (original)", "This letter"],
                "source_url": "https://www.malaysia.gov.my", "retrieved_at": SOURCES["PDRM"]["retrieved_at"], "confidence": "Low"}
    # Production: fetch src["source_url"] here and refresh steps; cached steps are the fallback.
    return {k: src[k] for k in ("online_steps", "walkin_steps", "prepare_online", "prepare_walkin", "source_url", "retrieved_at")} | {"confidence": "Medium"}  # cached registry, not a live fetch


@tool("office.locate", "Nearest office, hours and booking info from postcode (demo data).")
def locate(issuer: str, postcode: str | None) -> dict | None:
    offices = OFFICES.get(issuer, [])
    if postcode:
        for o in offices:
            if postcode.startswith(o["postcode_prefix"]):
                return o
    return offices[0] if offices else None


@tool("act.draft", "Prepare a reply draft and a reminder. Never sends — needs user approval.")
def draft(issuer: str, fields: dict, genuine: bool) -> dict:
    if not genuine:
        return {"draft": "LAPORAN SCAM (draf)\nSaluran: SMS / WhatsApp / e-mel\nKandungan: [ringkasan mesej]\nTindakan saya: Tidak membuat bayaran. Tidak klik pautan.\n[Nama penuh]",
                "reminder": None}
    ref = fields.get("reference") or "[rujukan]"
    body = (f"Kepada: {SOURCES.get(issuer, {}).get('name', '[agensi]')}\nPerkara: Pertanyaan / Permohonan berkaitan rujukan {ref}\n\n"
            f"Tuan/Puan,\nSaya merujuk kepada notis {ref}" + (f" berjumlah {fields['amount']}" if fields.get("amount") else "") +
            ".\n[Nyatakan permohonan anda]\n\nSekian, terima kasih.\n[Nama penuh]")
    reminder = f"7 days before {fields['deadline']}" if fields.get("deadline") else None
    return {"draft": body, "reminder": reminder}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
