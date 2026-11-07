"""Tulen agent tools.

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
from .i18n import TEXT, render
from .registry_i18n import localize
from .scam_content import (LETTER_DRAFT, LETTER_Q, AMOUNT_PIECE, REMINDER, SCAM_REPORT_DRAFT, VERIFY_NOTE_DRAFT,
                           detect_scam_type, scam_lesson, scam_route)

SOURCES: dict = {k: v for k, v in json.loads((DATA_DIR / "official_sources.json").read_text(encoding="utf-8")).items() if not k.startswith("_")}
OFFICES: dict = json.loads((DATA_DIR / "offices.json").read_text(encoding="utf-8"))

# Domain-only directory of real banks, councils, states, universities and companies (see docs/DIRECTORY.md). It says who a
# website belongs to; it carries no procedures, so steps still come from SOURCES only.
_dir_file = DATA_DIR / "official_directory.json"
DIRECTORY: list[dict] = json.loads(_dir_file.read_text(encoding="utf-8")) if _dir_file.exists() else []
# Suffixes only registered to government and accredited education bodies, so a whole suffix is safe to trust (like .gov.my).
TRUSTED_SUFFIXES = (".gov.my", ".edu.my")
_DIR_DOMAINS = {d: e for e in DIRECTORY for d in e["domains"]}
_GENERIC = {"bank", "islam", "islamic", "malaysia", "universiti", "university", "college", "kolej", "majlis", "negeri", "jabatan", "institut",
            "group", "online", "digital", "mobile", "life", "care", "health", "insurance", "takaful", "finance", "capital", "credit", "media",
            "star", "post", "fast", "smart", "asia", "global", "world", "first", "royal", "golden", "prima", "perdana", "utama", "jaya",
            "bandar", "taman", "city", "town", "state", "holdings", "berhad", "services", "time", "grab", "yes", "unifi", "tune", "mydin", "wise", "sains", "boost", "business", "apac", "guardian"}


def _dir_entry(host: str) -> dict | None:
    """The directory entry whose domain is this host or a parent of it."""
    parts = host.lower().split(".")
    return next((_DIR_DOMAINS[".".join(parts[i:])] for i in range(len(parts) - 1) if ".".join(parts[i:]) in _DIR_DOMAINS), None)


def _dir_find(name: str) -> dict | None:
    """Find an entry by id, name, alias or domain; whole-word match, longest alias first (so 'maybank islamic' beats 'maybank')."""
    low = " " + re.sub(r"[^a-z0-9.]+", " ", name.lower()).strip() + " "
    best, blen = None, 0
    for e in DIRECTORY:
        for a in [e["id"], e["name"], *e.get("aliases", [])]:
            a = re.sub(r"[^a-z0-9.]+", " ", a.lower()).strip()
            if len(a) >= 3 and len(a) > blen and f" {a} " in low:
                best, blen = e, len(a)
        for d in e["domains"]:
            if len(d) > blen and d in low:
                best, blen = e, len(d)
    return best


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
PLATE_RE = re.compile(r"(?<![\w/-])(?!RM ?\d)(?!RM\b)[A-Z]{1,3} ?[1-9]\d{0,3}(?: ?[A-Z])?(?![\w/-])")
NAME_RE = re.compile(r"((?:Kepada|Nama)\s*:\s*)([^,\n\[]+)", re.IGNORECASE)
# Malay/Indian name forms anywhere in the text: ALI BIN ABU, SITI BINTI HASAN, RAJU A/L MUTHU.
PATRONYM_RE = re.compile(r"\b(?:[A-Z][A-Z'.@]+[ \t]+){1,3}(?:BIN|BINTI|BT|B\.|A/L|A/P|S/O|D/O|ANAK)[ \t]+[A-Z][A-Z'.@]+(?:[ \t]+[A-Z][A-Z'.@]+){0,3}")
PASSPORT_RE = re.compile(r"\b[A-Z]\d{7,8}\b")
DOB_RE = re.compile(r"((?:Tarikh\s+lahir|Date\s+of\s+birth|DOB)\s*:\s*)[^\n]+", re.IGNORECASE)
# Final sweep: any leftover run of 8+ digits (spaces/dashes allowed) is masked rather than trusted.
SWEEP_RE = re.compile(r"(?<![\w/])(?:\d[ -]?){8,}\d(?![\w/])")
TITLE_NAME_RE = re.compile(r"\b((?:Encik|Puan|Cik|Tuan|Dato['’]?)[ \t]+)([A-Z][A-Z'.@]+(?:[ \t]+[A-Z][A-Z'.@/]+)+)")


EMAIL_NAME_RE = re.compile(r"(?:[A-Z][\w'’.-]*[ 	]+){1,4}<\[EMAIL\]>")  # email display name: "Ali Bin Abu <[EMAIL]>"


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
    out = EMAIL_NAME_RE.sub(lambda m: (counts.__setitem__("name", counts["name"] + 1), "[NAME] <[EMAIL]>")[1], out)
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
REF_RE = re.compile(r"\b([A-Z]{2,6}(?:/[A-Z0-9]+(?:-[A-Z0-9]+)*){2,})\b")


@tool("extract.fields", "Extract amount, deadline and reference number.")
def extract_fields(text: str) -> dict:
    amounts = AMOUNT_RE.findall(text)
    dates = DATE_RE.findall(text)
    ref = REF_RE.search(text)
    deadline = None
    # Last "sebelum <date>" wins: a notice may cite the original due date first and the new deadline after.
    ms = list(re.finditer(rf"(?:sebelum|before|selewat-lewatnya)\s+({DATE_RE.pattern})", text, re.IGNORECASE))
    if ms:
        deadline = ms[-1].group(1)
    elif dates:
        deadline = dates[-1]
    if not deadline and re.search(r"24\s*jam|24\s*hours", text, re.IGNORECASE):
        deadline = "24 hours (pressure tactic)"
    return {
        "amount": f"RM {amounts[0]}" if amounts else None,
        "deadline": deadline,
        "reference": ref.group(1) if ref else None,
    }


# ---------------------------------------------------------------- entities (for the Semak Mule shortcut)
_ACCT = re.compile(r"(?<![\d-])(?:\d[ -]?){10,16}(?![\d-])")
_COMPANY = re.compile(r"\b(?:[A-Z][\w&.'-]*\s+){1,4}(?:Sdn\.?\s*Bhd\.?|Bhd\.?|Berhad|Enterprise|Trading|Resources|Holdings|Services|Solutions|Ventures)\b|(?:Syarikat|Kedai|Company|Co\.)\s+(?:[A-Z][\w&.'-]*\s?){1,4}")


def extract_entities(raw: str) -> dict:
    """Bank accounts, phone numbers and company names found in the RAW message, for display only.

    Called on the request text after the analysis and never cached or stored: the user sees their own message's
    details so they can type them into the official Semak Mule check. IC numbers are never returned."""
    digits = lambda x: re.sub(r"\D", "", x)
    ics = {digits(m) for m in IC_RE.findall(raw)}
    phones = [m.group(0).strip() for m in PHONE_RE.finditer(raw)]
    pd = {digits(p) for p in phones}
    accounts = [re.sub(r"\s+", " ", m).strip() for m in _ACCT.findall(raw)]
    accounts = [a for a in accounts if digits(a) not in ics and digits(a) not in pd and len(digits(a)) >= 10]
    companies = [re.sub(r"\s+", " ", m.group(0)).strip(" .,") for m in _COMPANY.finditer(raw)]
    uniq = lambda xs: list(dict.fromkeys(xs))[:5]
    return {"accounts": uniq(accounts), "phones": uniq(phones), "companies": uniq(companies)}


# ---------------------------------------------------------------- verify
URL_RE = re.compile(r"\b((?:https?://)?(?:[a-z0-9-]+\.)+[a-z]{2,}(?:/[^\s]*)?)", re.IGNORECASE)
# Social/mail/form hosts: seen in genuine footers and email print-outs, so they are noted, not scored as scam signs.
SOCIAL = ("facebook.com", "x.com", "twitter.com", "instagram.com", "tiktok.com", "youtube.com", "youtu.be",
          "linkedin.com", "whatsapp.com", "telegram.org", "mail.google.com")
FORMS = ("forms.gle", "docs.google.com", "forms.office.com", "typeform.com")
SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "s.id", "cutt.ly", "shorturl.at", "rb.gy"}

RED_FLAGS: list[tuple[str, str]] = [
    (r"akaun\s+(?:peribadi|maybank|cimb|public bank|rhb|bank islam)|personal account|转账到|汇款到|转到.{0,8}(?:账户|户口|帐户)|(?:账户|户口)\s*[:：]?\s*\d|(?:bayar|transfer|pindah)\w*[^.\n]{0,40}akaun[^.\n]{0,40}atas nama", "transfer_account"),
    (r"24\s*jam|24\s*hours|dalam\s+(?:masa\s+)?\d+\s*jam|hari ini sahaja|today only|24\s*小时|立即|马上|立刻|今天之内|24\s*மணி", "urgency"),
    (r"waran\s+tangkap|arrest|ditangkap|逮捕|通缉|拘留|கைது", "arrest"),
    (r"akaun\s+selamat|safe\s+account|安全(?:账户|户口|帐户)|பாதுகாப்பு\s*கணக்கு|பாதுகாப்பான\s*கணக்", "safe_account"),
    (r"pengubahan\s+wang\s+haram|money\s+laundering|洗钱|洗錢|பணமோசடி|பணச்?\s*சலவை", "laundering"),
    (r"dibekukan|bekukan|akaun[^.\n]{0,20}beku|account[^.\n]{0,20}(?:frozen|freeze)|冻结|凍結|முடக்க", "account_frozen"),
    (r"\btac\b|\botp\b|kata laluan|password|验证码|密码|கடவுச்சொல்", "tac_otp"),
    (r"(?:hubungi|contact|mesej|message|klik|click|tambah|add|sertai|join|chat)\W+(?:\w+\W+){0,4}(?:whatsapp|telegram|wasap)|wa\.me/|t\.me/|加.{0,6}(?:whatsapp|telegram|微信)|வாட்ஸ்அப்|டெலிகிராம்", "chat_app"),
    (r"jangan\s+beritahu|(?:simpan|jaga|kekalkan)\s+(?:ini\s+)?\brahsia\b|keep (?:it )?secret|(?:don'?t|do not) tell (?:anyone|anybody)|不要告诉|不可告诉|不得告诉|切勿告诉|请保密|யாரிடமும்\s*சொல்ல", "secret"),
    (r"gambar\s+ic|ic\s+depan|photo of (?:your )?ic|身份证.{0,4}(?:照片|正反面|相片)|அடையாள\s*அட்டை.{0,12}படம்", "ic_photo"),
    (r"diskaun\s+\d+%", "discount"),
    (r"akaun\s+(?:bank\s+)?(?:baharu|baru)|new (?:bank )?account|(?:changed|updated) (?:bank )?account|(?:tukar|bertukar|ditukar)\w*\s+akaun|akaun[^.\n]{0,30}(?:telah|sudah)\s+(?:berubah|ditukar)", "new_account"),
    (r"https?://(?:[^\s/]*@|\[email\])|https?://\d{1,3}(?:\.\d{1,3}){3}", "hidden_link"),
    (r"dijamin\s+(?:untung|keuntungan|pulangan)|guaranteed\s+(?:profit|return|income)|(?:profit|untung|keuntungan|pulangan)[^.\n]{0,25}(?:every month|sebulan|setiap bulan|per month)|保证[^。\n]{0,8}(?:赚|收益|回报|盈利)|每月[^。\n]{0,4}赚|லாபம்\s*உறுதி|உறுதி[^.\n]{0,12}லாபம்", "guaranteed_returns"),
    (r"deposit\w*\s+(?:of\s+)?rm\s?\d[^.\n]{0,40}(?:activate|aktif|daftar|register)|rm\s?\d[\d,.]*\s+deposit[^.\n]{0,40}(?:activate|aktif|daftar|register)|yuran\s+pendaftaran|registration fee|押金|订金|வைப்புத்?\s*தொகை", "advance_fee"),
    (r"(?:army|military|tentera|soldier|军医|军人|ராணுவ)[^.\n]{0,25}(?:doctor|doktor|engineer|jurutera|医|மருத்துவர்)[^.\n]{0,40}(?:syria|afghanistan|yemen|iraq|overseas|abroad|luar negara|mission|misi|海外|国外|叙利亚|阿富汗|சிரியா|ஆப்கான்|வெளிநாடு)|(?:doctor|doktor|医生)\s*(?:army|tentera|military)[^.\n]{0,20}(?:syria|afghanistan|yemen|iraq|overseas|abroad|luar negara|mission|misi|海外|国外|叙利亚|阿富汗|சிரியா|ஆப்கான்|வெளிநாடு)|(?:send|hantar)[^.\n]{0,30}(?:money|wang|duit)[^.\n]{0,30}(?:friend'?s|kawan)[^.\n]{0,15}(?:account|akaun)|钱[^。\n]{0,6}(?:汇|转)[^。\n]{0,10}朋友[^。\n]{0,6}(?:户口|账户)|நண்பர[^.\n]{0,12}கணக்[^.\n]{0,20}பணம்[^.\n]{0,10}அனுப்பு", "romance_money"),
    (r"(?:you(?:'ve| have)?\s+won|anda\s+(?:telah\s+)?menang|congratulations[^.\n]{0,30}won)[^.\n]{0,30}(?:prize|lottery|lucky draw|rm\s?\d|cash|hadiah|cabutan|iphone|voucher)|menang[^.\n]{0,25}(?:hadiah|cabutan)|(?:won|win)[^.\n]{0,25}(?:prize|lottery|lucky draw)|中奖|中獎|லாட்டரி[^.\n]{0,25}வென்ற|பரிசு[^.\n]{0,25}வென்ற", "prize_win"),
    (r"ignore (?:all |any )?(?:the )?(?:previous|prior|above) instructions|abaikan (?:semua )?arahan|system prompt|(?:you are|anda ialah) (?:an? )?(?:ai|language model|assistant)|(?:say|state|report|nyatakan|laporkan) (?:that )?(?:this|it|ini)(?: is| sebagai| adalah)? (?:genuine|safe|legit|sah|selamat)", "prompt_injection"),
    (r"verify your account|confirm your details|sahkan (?:akaun|maklumat)|akaun anda (?:akan )?(?:di)?(?:gantung|sekat|bekukan|tutup)|your account (?:will be|has been) (?:suspended|blocked|closed)", "credential_harvest"),
]


def _lev(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _brands() -> set[str]:
    return {lab for s in SOURCES.values() for d in s["domains"] for lab in d.split(".") if len(lab) >= 3 and lab not in ("gov", "my", "com", "net", "org", "www")}


# Look-alike names come from companies and federal bodies only. Places and campuses (selangor, perak, a university's short name) also
# appear in innocent site names, so a name match there would wrongly condemn an ordinary link. Those links still count as "unofficial".
_BRAND_CATS = {"bank", "insurer", "payment", "regulator", "investment", "credit", "telco", "utility", "courier", "ecommerce", "toll", "airline", "retail", "service", "federal"}
_BRAND_MIN = {"bank": 4, "insurer": 5, "payment": 5, "investment": 5}
_DIR_BRANDS = {lab for d, e in _DIR_DOMAINS.items() if e["category"] in _BRAND_CATS and not d.endswith(TRUSTED_SUFFIXES)
               for lab in [d.split(".")[0]] if len(lab) >= _BRAND_MIN.get(e["category"], 6) and lab not in _GENERIC and not lab.isdigit()}


def _lookalike(domain: str) -> bool:
    """Unofficial domain that contains or nearly spells an agency name (hasil-gov.my.com, mytax-login.xyz)."""
    tokens = re.split(r"[-.]", domain)
    # directory names are stricter (a whole token, a long name inside, or one typo in a long name) because there are hundreds of them
    return any(b in tokens or (len(b) >= 4 and b in domain) or (len(b) >= 5 and any(len(t) >= 4 and _lev(t, b) <= 2 for t in tokens))
               for b in _brands()) or any(b in tokens or (len(b) >= 6 and b in domain) or (len(b) >= 7 and any(len(t) >= 6 and _lev(t, b) <= 1 for t in tokens))
                                          for b in _DIR_BRANDS)


def _domains(text: str) -> list[str]:
    out = []
    for u in URL_RE.findall(text):
        host = urlparse(u if "://" in u else "http://" + u).hostname or ""
        if "." in host and not host.replace(".", "").isdigit():
            out.append(host.lower())
    return out


def _urls(text: str) -> list[tuple[str, str]]:
    """(url as written, host) for every link in the text."""
    out = []
    for u in URL_RE.findall(text):
        u = u.rstrip(".,;:)]'\"")
        host = urlparse(u if "://" in u else "http://" + u).hostname or ""
        out.append((u, host.lower()))
    return out


def _social_handles(text: str) -> list[str]:
    """Social URLs in the text as 'host/handle' (www and @ stripped, lowercase), each once."""
    out = []
    for u in URL_RE.findall(text):
        pu = urlparse(u if "://" in u else "http://" + u)
        host = (pu.hostname or "").lower().removeprefix("www.")
        if any(host == n or host.endswith("." + n) for n in SOCIAL if n != "mail.google.com"):
            out.append(host + "/" + pu.path.strip("/").split("/")[0].lstrip("@").lower())
    return list(dict.fromkeys(out))


# Fixed thresholds: score 0-100 is "how safe it looks". Below SCAM_BELOW is a likely scam, from CLEAR_FROM up is "no signals".
SCAM_BELOW, CLEAR_FROM = 60, 80
FLAG_WEIGHT = {"family_impersonation": 55, "safe_account": 30, "laundering": 25}  # default weight is 22


def verdict_from_score(score: int) -> str:
    return "likely_scam" if score < SCAM_BELOW else "no_signals" if score >= CLEAR_FROM else "caution"


# "Hi mak, this is my new number": a new-number or broken-phone excuse, a family address and a money ask, all three.
_FAM_EXCUSE = (r"nombor\s+(?:baru|baharu)|no\.?\s*(?:ni|ini)\s+(?:nombor\s+)?baru|(?:telefon|phone|handphone|hp|fon)\s+(?:saya\s+|aku\s+)?(?:rosak|hilang|jatuh)|"
               r"new\s+(?:phone\s+)?number|changed\s+(?:my\s+)?number|(?:lost|broke|broken|damaged|dropped)\s+(?:my\s+)?phone|phone\s+(?:is\s+|was\s+|got\s+)?(?:broken|lost|damaged|stolen)|"
               r"新号码|新號碼|换了(?:新)?号|手机(?:坏|丢|掉|摔)|号码换了|"
               r"புதிய\s*(?:எண்|நம்பர்)|போன்\s*(?:உடைந்|தொலைந்|கெட்)|எண்ணை\s*மாற்றி")
_FAM_ADDRESS = (r"\b(?:mak|emak|ibu|mama|ayah|abah|abang|kakak|kak|along|angah|mum|mom|mummy|dad|papa|pak\s*cik|mak\s*cik|auntie|uncle)\b|"
                r"妈|爸|哥|姐|阿姨|叔叔|அம்மா|அப்பா|அண்ணா|அக்கா")
_FAM_MONEY = (r"transfer|pindah|bayar|duit|wang\b|rm\s?\d|send\s+(?:me\s+)?(?:money|rm)|tolong\s+(?:bayar|hantar|topup|top up)|urgent|"
              r"转账|汇款|转钱|付款|借钱|钱|பணம்|அனுப்ப|கட்ட")


def _family_impersonation(low: str):
    """Match of the new-number excuse when all three parts are present, else None."""
    m = re.search(_FAM_EXCUSE, low)
    return m if m and re.search(_FAM_ADDRESS, low) and re.search(_FAM_MONEY, low) else None

AI_SIGNALS = ("ai_payment_demand", "ai_threat", "ai_credential", "ai_remote_access", "ai_impersonation",
              "ai_too_good", "ai_secrecy", "ai_chat_move", "ai_inconsistent", "ai_new_domain", "ai_official_mismatch")
# What the agent's evidence can do. A quote proves the words exist, not that the agent's JUDGEMENT of them is right, so:
#  - hard signals are objective and checkable (an unusual way to pay, a request for credentials or remote access, a website the
#    agent verified was registered days ago). They weigh more than a rule flag (30 against 22) and can make a likely scam on their own, even on a letter with a valid reference number.
#  - soft signals are judgement calls (impersonation, a mismatch with the agency's site, pressure, "too good", secrecy, a chat move,
#    inconsistency). They raise caution but can never alone say "scam": a real survey sent through a Google Form looks "unusual" to a model.
AI_HARD = {"ai_payment_demand", "ai_credential", "ai_remote_access", "ai_new_domain"}
AI_SOFT = set(AI_SIGNALS) - AI_HARD
# File signals (filecheck.py). Weak ones are real but common in innocent files (an APK exists, a zip is encrypted, a lure-like
# name), so like the soft AI signals they weigh 12 and can never alone give "likely scam". Strong ones are deliberate evasion
# or a disguised script and weigh 30.
FILE_WEAK = {"file_script", "file_apk", "file_encrypted", "file_unreadable", "file_disk_image", "file_name_trick", "file_lure_name", "file_apk_perms", "file_macro", "file_archive_closed"}
FILE_STRONG = {"file_script_disguised", "file_zip_tricks", "file_apk_takeover", "file_apk_brand", "file_macro_hidden", "file_office_remote"}
SOFT, HARD = AI_SOFT | FILE_WEAK, AI_HARD | FILE_STRONG


@tool("scam.check", "Domain allowlist + red-flag rules. Returns verdict and evidence.")
def scam_check(text: str, issuer: str, language: str = "en", extra: tuple | list = (), ai: tuple | list = ()) -> dict:
    """Verdict plus reasons. Sentences come from i18n.TEXT in `language`; each reason carries its stable `code`."""
    low = text.lower()
    r = lambda code, **kw: render(code, language, **kw)
    ev: dict[tuple[str, str], list[str]] = {}  # (code, text) -> exact snippets of the input that caused it
    flags: list[tuple[str, str]] = []  # (code, text)
    for pat, k in RED_FLAGS:
        m = re.search(pat, low)
        if m:
            flags.append((k, r(k)))
            ev[flags[-1]] = [text[m.start():m.end()][:80]]
    fam = _family_impersonation(low)
    if fam:
        flags.append(("family_impersonation", r("family_impersonation"))); ev[flags[-1]] = [text[fam.start():fam.end()][:80]]
    flags += [(c, r(c)) for c in extra if c in TEXT]  # extra risk codes, e.g. email header signals
    for c, quote in ai:  # signals the AI planner found; the planner already checked each quote against the letter
        if c in AI_SIGNALS and (c, r(c)) not in flags:
            flags.append((c, r(c)))
            ev[flags[-1]] = [quote]
    good: list[tuple[str, str]] = []
    official = SOURCES.get(issuer, {}).get("domains", [])
    info: list[tuple[str, str]] = []
    for d in dict.fromkeys(_domains(text)):  # each host once
        hit = lambda names: any(d == n or d.endswith("." + n) for n in names)
        links = [u for u, h in _urls(text) if h == d]
        if d in SHORTENERS:
            flags.append(("shortener", r("shortener", d=d))); ev[flags[-1]] = links
        elif d.endswith(TRUSTED_SUFFIXES) or _dir_entry(d) or any(d == o or d.endswith("." + o) for o in official if o != ".gov.my"):
            good.append(("official_domain", r("official_domain", d=d))); ev[good[-1]] = links
        elif hit(SOCIAL):
            if not SOURCES.get(issuer, {}).get("social"):
                if not any(c == "social_links" for c, _ in info):
                    info.append(("social_links", r("social_links")))
                ev.setdefault(info[[c for c, _ in info].index("social_links")], []).extend(links)
        elif hit(FORMS):
            info.append(("form_link", r("form_link", d=d))); ev[info[-1]] = links
        else:
            flags.append(("unofficial_domain", r("unofficial_domain", d=d))); ev[flags[-1]] = links
            if _lookalike(d):
                flags.append(("lookalike", r("lookalike", d=d))); ev[flags[-1]] = links
    known = {h.lower().removeprefix("www.") for h in SOURCES.get(issuer, {}).get("social", [])}
    if known:  # the registry lists this agency's real accounts: anything else claiming to be them is suspect
        for h in _social_handles(text):
            links = [u for u, _ in _urls(text) if _social_handles(u) == [h]]
            if h in known:
                good.append(("official_social", r("official_social", d=h))); ev[good[-1]] = links
            else:
                flags.append(("social_mismatch", r("social_mismatch", d=h))); ev[flags[-1]] = links
    if issuer != "UNKNOWN" and not flags:
        good.append(("known_pattern", r("known_pattern", issuer=issuer)))
    ref = REF_RE.search(text)
    if ref:
        good.append(("ref_format", r("ref_format"))); ev[good[-1]] = [ref.group(1)]
    score = max(0, min(100, 80 + 5 * len(good) - sum(FLAG_WEIGHT.get(c, 12 if c in SOFT else 30 if c in HARD else 22) for c, _ in flags)))
    if flags or issuer == "UNKNOWN":
        score = min(score, CLEAR_FROM - 1)  # any red flag or an unknown sender can never read as clear
    if flags and all(c in SOFT for c, _ in flags):
        score = max(score, SCAM_BELOW)  # judgement calls alone never condemn a message; the rules or hard evidence must agree
    verdict = verdict_from_score(score)  # the verdict is a pure function of the score: they cannot disagree
    R = lambda kind, c, t: {"kind": kind, "code": c, "text": t, "evidence": list(dict.fromkeys(ev.get((c, t), [])))}
    reasons = ([R("risk", c, t) for c, t in flags] + [R("ok", c, t) for c, t in good]
               + [R("info", c, t) for c, t in info]
               + [R("info", "cannot_see", r("cannot_see"))])
    if re.search(r"payment|account|akaun|bayar", low):
        reasons.append(R("info", "pay_confirmed", r("pay_confirmed")))
    src = SOURCES.get(issuer, {})
    verify = [r("type_url", site=src.get("source_url") or "https://www.malaysia.gov.my"),
              r("call_official", who=src.get("name") or r("the_agency")),
              r("check_ref"), r("no_pay_tac")]
    if fam:  # the one check that beats this scam: hear their real voice on the number you already have
        verify.insert(0, r("call_old_number"))
    stype = detect_scam_type(low, family=bool(fam)) if verdict != "no_signals" else None
    if verdict != "no_signals" and any(c.startswith("file_apk") for c, _ in flags):
        stype = "apk_install"  # the lesson for apps sent in a message; file names never reach the text rules
    return {"genuine": verdict != "likely_scam",  # means 'not flagged', not 'proven genuine'
            "verdict": verdict, "score": score, "red_flags": [t for _, t in flags], "good_signs": [t for _, t in good],
            "reasons": reasons, "verify_yourself": verify, "scam_type": stype}


ODD_TLDS = (".top", ".xyz", ".icu", ".click", ".buzz", ".cfd", ".sbs", ".cyou", ".rest", ".monster", ".cam")
ASK_WORDS = ("login", "log-in", "verify", "secure", "pay", "bayar", "akaun", "account", "update", "refund", "claim")


def _is_official(host: str) -> bool:
    return host.endswith(TRUSTED_SUFFIXES) or _dir_entry(host) is not None or any(host == d or host.endswith("." + d) for s in SOURCES.values() for d in s["domains"] if d != ".gov.my")


@tool("link.inspect", "Inspect every link in the message for tricks: bare IP, punycode, @ trick, look-alike name, odd ending, shortener.")
def inspect_links(text: str) -> list[dict]:
    out, seen = [], set()
    for u, host in _urls(text):
        if not host or host in seen:
            continue
        seen.add(host)
        p = urlparse(u if "://" in u else "http://" + u)
        official, f = _is_official(host), []
        if host.replace(".", "").isdigit():
            f.append("the address is a bare IP number")
        if "xn--" in host:
            f.append("uses punycode, which can imitate letters")
        if "@" in (p.netloc or ""):
            f.append("has an @ in the address, which hides the real site")
        if host in SHORTENERS:
            f.append("is a link shortener that hides the destination")
        if host.endswith(ODD_TLDS):
            f.append("uses an ending common on scam sites")
        if not official and host.count(".") >= 3:
            f.append("has many subdomain parts")
        known_platform = any(host == n or host.endswith("." + n) for n in SOCIAL + FORMS)
        if not official and not known_platform and _lookalike(host):
            f.append("looks like an agency name but is not its website")
        if p.scheme == "http":
            f.append("is not encrypted (http)")
        if any(w in (p.path or "").lower() for w in ASK_WORDS):
            f.append("the path asks you to log in, verify or pay")
        out.append({"host": host, "official": official, "findings": f})
    return out


@tool("registry.lookup", "Look up the claimed agency in the official registry: its real websites and how it takes payment.")
def registry_lookup(issuer: str) -> dict:
    s = SOURCES.get(issuer)
    if not s:
        e = _dir_find(issuer) if issuer else None  # a name, alias or domain from the directory (no steps: those come from SOURCES only)
        if not e:
            return {"known": False}
        return {"known": True, "name": e["name"], "domains": e["domains"], "source_url": "https://" + e["domains"][0] if e["domains"] else "https://www.malaysia.gov.my",
                "online_steps": [], "category": e["category"]}
    return {"known": True, "name": s["name"], "domains": s["domains"], "source_url": s["source_url"],
            "online_steps": s.get("online_steps", [])[:3]}


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
CHECK_SENTENCE = {
    "bm": "Semak sendiri sebelum membayar: lihat langkah di bawah.",
    "en": "Check it yourself before paying: see the steps below.",
    "zh": "付款前请自行核实：见下方步骤。",
    "ta": "பணம் செலுத்தும் முன் நீங்களே சரிபார்க்கவும்: கீழே உள்ள படிகளைப் பார்க்கவும்.",
}
PIECES = {
    "bm": (" Jumlah: {a}.", " Tarikh akhir: {d}."),
    "en": (" Amount: {a}.", " Deadline: {d}."),
    "zh": (" 金额：{a}。", " 截止日期：{d}。"),
    "ta": (" தொகை: {a}.", " கடைசி நாள்: {d}."),
}


def _only_known_domains(generated: str, letter: str) -> bool:
    """Reject model text that names a website not in the letter or the official registry (e.g. hasil -> results)."""
    known = set(_domains(letter)) | {d for s in SOURCES.values() for d in s["domains"]} | set(_DIR_DOMAINS)
    return all(any(d == k or d.endswith("." + k) for k in known) for d in _domains(generated))


@tool("llm.explain", "Plain-language explanation in the user's language (LLM optional).")
def explain(redacted_text: str, issuer: str, fields: dict, genuine: bool, language: str) -> str:
    if not genuine:
        return SCAM_TEMPLATES[language]
    generated = llm.complete(f"Explain this official letter:\n\n{redacted_text}", language)
    if generated and _only_known_domains(generated, redacted_text):
        return generated + " " + CHECK_SENTENCE[language]
    src = SOURCES.get(issuer, {})
    a, d = PIECES[language]
    return TEMPLATES[language].format(
        issuer=src.get("name", "an unknown sender"),
        ltype=src.get("letter_type", "notice"),
        amount=a.format(a=fields["amount"]) if fields.get("amount") else "",
        deadline=d.format(d=fields["deadline"]) if fields.get("deadline") else "",
    ) + " " + CHECK_SENTENCE[language]


@tool("teach.lesson", "Create the 'Kenapa saya dapat surat ini?' card and glossary terms, in the user's language.")
def teach(issuer: str, genuine: bool, language: str = "en", scam_type: str | None = None) -> dict:
    if not genuine:
        return scam_lesson(scam_type or "other", language)  # lesson follows the scam type, not a fixed police story
    src = SOURCES.get(issuer) or SOURCES["PDRM"]
    return {"question": LETTER_Q[language], "answer": localize(issuer, src, language)["lesson_a"], "terms": src["terms"]}


# ---------------------------------------------------------------- route / act
@tool("gov.retrieve", "Get current steps from the official source registry (or scam-reporting steps for a scam).")
def retrieve(issuer: str, genuine: bool, language: str = "en", scam_type: str | None = None) -> dict:
    if not genuine:  # a scam never gets the impersonated agency's steps: report it and protect yourself
        return scam_route(scam_type or "other", language, SOURCES["PDRM"]["retrieved_at"])
    src = SOURCES.get(issuer)
    if not src:
        return {"online_steps": ["Find the agency's official .gov.my site yourself and check there."],
                "walkin_steps": ["Visit the agency counter with the letter and IC."],
                "prepare_online": ["IC number"], "prepare_walkin": ["IC (original)", "This letter"],
                "source_url": "https://www.malaysia.gov.my", "retrieved_at": SOURCES["PDRM"]["retrieved_at"], "confidence": "Low"}
    # Production: fetch src["source_url"] here and refresh steps; cached steps are the fallback.
    loc = localize(issuer, src, language)
    return {k: loc[k] for k in ("online_steps", "walkin_steps", "prepare_online", "prepare_walkin")} | {
        "source_url": src["source_url"], "retrieved_at": src["retrieved_at"], "confidence": "Medium"}  # cached registry, not a live fetch


@tool("office.locate", "Nearest office, hours and booking info from postcode (demo data).")
def locate(issuer: str, postcode: str | None) -> dict | None:
    offices = OFFICES.get(issuer, [])
    if postcode:
        for o in offices:
            if postcode.startswith(o["postcode_prefix"]):
                return o
    return offices[0] if offices else None


@tool("act.draft", "Prepare a reply draft and a reminder. Never sends: needs user approval.")
def draft(issuer: str, fields: dict, genuine: bool, language: str = "bm") -> dict:
    if not genuine:
        return {"draft": SCAM_REPORT_DRAFT[language], "reminder": None}
    if issuer not in SOURCES:  # no known agency: never invent an agency letter
        return {"draft": VERIFY_NOTE_DRAFT[language], "reminder": None}
    ref = fields.get("reference") or "[rujukan]"
    amount = AMOUNT_PIECE[language].format(a=fields["amount"]) if fields.get("amount") else ""
    body = LETTER_DRAFT[language].format(agency=SOURCES[issuer]["name"], ref=ref, amount=amount)
    reminder = REMINDER[language].format(d=fields["deadline"]) if fields.get("deadline") else None
    return {"draft": body, "reminder": reminder}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
