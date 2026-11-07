"""Short chat/email replies built from a BatchResponse. Pure functions, no I/O.

Never states a document is genuine: the best verdict is 'no signs found, not proof'.
Never echoes user text (file names are replaced by 'Fail N'). Only URL allowed is the registry source_url.
zh/ta strings need native-speaker review before the demo.
"""
from __future__ import annotations

import os
import re

_URL = re.compile(r"\(?(?:https?://|www\.)\S+", re.I)  # an opening bracket right before a link goes with it
_RANK = {"likely_scam": 2, "caution": 1, "no_signals": 0}
_MS = set("anda yang dan untuk telah kepada sila jangan akaun bayar saya dengan ini itu tidak boleh dalam atau kami tuan puan segera".split())
_EN = set("the you your and to is are please account pay payment this that with not from will have urgent".split())

T = {
    "bm": dict(v={"likely_scam": "Kemungkinan penipuan", "caution": "Berhati-hati",
                  "no_signals": "Tiada tanda penipuan ditemui (ini bukan bukti)"},
               why="Sebab:", check="Semak sendiri:", nsrc="Hubungi NSRC 997 jika anda sudah berkongsi maklumat atau membayar.",
               src="Sumber rasmi:", foot="FAHAM bukan nasihat undang-undang", file="Fail",
               n1="FAHAM membaca teks/gambar/dokumen yang anda hantar. Maklumat peribadi ditutup dahulu dan tiada apa disimpan.",
               n2="Teks yang telah ditutup mungkin dihantar kepada ILMU untuk penjelasan. Balas BERHENTI atau STOP untuk berhenti; tiada apa disimpan.",
               n3="Terma", ask="Balas OK untuk teruskan.", ok="Terima kasih. Hantar mesej, gambar, atau dokumen untuk disemak.",
               stop="Anda telah berhenti. Tiada apa disimpan. Balas OK untuk mula semula.",
               err="Maaf, FAHAM tidak dapat membaca ini. Cuba hantar teks atau gambar yang lebih jelas.",
               rate="Terlalu banyak mesej. Cuba lagi sejam lagi."),
    "en": dict(v={"likely_scam": "Likely a scam", "caution": "Be careful",
                  "no_signals": "No scam signs found (this is not proof)"},
               why="Why:", check="Check it yourself:", nsrc="Call NSRC 997 if you already shared details or paid.",
               src="Official source:", foot="FAHAM is not legal advice", file="File",
               n1="FAHAM reads the text, image or document you send. Personal details are masked first and nothing is stored.",
               n2="Masked text may be sent to ILMU to write the explanation. Reply STOP or BERHENTI to leave; nothing is kept.",
               n3="Terms", ask="Reply OK to continue.", ok="Thank you. Send a message, photo or document to check.",
               stop="You have left. Nothing is kept. Reply OK to start again.",
               err="Sorry, FAHAM could not read this. Try sending clearer text or a clearer image.",
               rate="Too many messages. Please try again in an hour."),
    "zh": dict(v={"likely_scam": "可能是诈骗", "caution": "请小心", "no_signals": "未发现诈骗迹象（这不是证明）"},
               why="原因：", check="请自行核实：", nsrc="如果您已提供资料或付款，请致电 NSRC 997。",
               src="官方来源：", foot="FAHAM 不是法律意见", file="文件",
               n1="FAHAM 会读取您发送的文字、图片或文件。个人资料会先被遮盖，不会保存任何内容。",
               n2="遮盖后的文字可能会发送给 ILMU 生成说明。回复 STOP 或 BERHENTI 即可退出，不会保留任何内容。",
               n3="条款", ask="回复 同意 继续。", ok="谢谢。请发送信息、照片或文件进行检查。",
               stop="您已退出，不会保留任何内容。回复 同意 可重新开始。",
               err="抱歉，FAHAM 无法读取此内容。请发送更清晰的文字或图片。", rate="信息过多，请一小时后再试。"),
    "ta": dict(v={"likely_scam": "மோசடியாக இருக்கலாம்", "caution": "எச்சரிக்கை",
                  "no_signals": "மோசடி அறிகுறிகள் இல்லை (இது ஆதாரம் அல்ல)"},
               why="காரணங்கள்:", check="நீங்களே சரிபார்க்கவும்:", nsrc="தகவல் பகிர்ந்திருந்தால் அல்லது பணம் செலுத்தியிருந்தால் NSRC 997 அழைக்கவும்.",
               src="அதிகாரப்பூர்வ மூலம்:", foot="FAHAM சட்ட ஆலோசனை அல்ல", file="கோப்பு",
               n1="நீங்கள் அனுப்பும் உரை, படம் அல்லது ஆவணத்தை FAHAM படிக்கும். தனிப்பட்ட விவரங்கள் முதலில் மறைக்கப்படும்; எதுவும் சேமிக்கப்படாது.",
               n2="விளக்கத்திற்காக மறைக்கப்பட்ட உரை ILMU-க்கு அனுப்பப்படலாம். நிறுத்த STOP அல்லது BERHENTI என பதிலளிக்கவும்.",
               n3="விதிமுறைகள்", ask="தொடர சம்மதம் என பதிலளிக்கவும்.", ok="நன்றி. சரிபார்க்க செய்தி, படம் அல்லது ஆவணத்தை அனுப்பவும்.",
               stop="நீங்கள் வெளியேறினீர்கள். எதுவும் சேமிக்கப்படவில்லை. மீண்டும் தொடங்க சம்மதம் என பதிலளிக்கவும்.",
               err="மன்னிக்கவும், இதைப் படிக்க முடியவில்லை. தெளிவான உரை அல்லது படத்தை அனுப்பவும்.",
               rate="அதிக செய்திகள். ஒரு மணி நேரம் கழித்து முயற்சிக்கவும்."),
}


def t(lang: str, key: str):
    return T.get(lang, T["bm"])[key]


def detect(text: str) -> str:
    if re.search(r"[஀-௿]", text):
        return "ta"
    if re.search(r"[一-鿿]", text):
        return "zh"
    words = re.findall(r"[a-z]+", text.lower())
    return "en" if sum(w in _EN for w in words) > sum(w in _MS for w in words) else "bm"


def _clean(s: str, allowed: str = "", n: int = 200) -> str:
    s = _URL.sub(lambda m: m.group(0) if allowed and m.group(0).lstrip("(").rstrip(".,)") == allowed else "", s)
    s = re.sub(r"\(\s*\)", "", s)
    s = s.replace("—", ",").replace("–", "-")
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def notice(language: str) -> str:
    url = os.getenv("FAHAM_PUBLIC_URL", "").rstrip("/")
    return "\n".join([t(language, "n1"), t(language, "n2"), f"{t(language, 'n3')}: {url}/terms" if url else t(language, "n3") + ": (FAHAM_PUBLIC_URL)"])


def summary(batch, language: str, channel: str) -> str:
    limit = 3000 if channel == "email" else 900
    L = language if language in T else "bm"
    res = [f.result for f in batch.files if getattr(f, "result", None)]
    if not res:
        return f"{t(L, 'err')}\n{t(L, 'foot')}"
    worst = max(res, key=lambda r: _RANK.get(r.scam.verdict, 1))
    src = getattr(getattr(worst, "route", None), "source_url", "") or ""
    v = t(L, "v")
    lines = [v.get(worst.scam.verdict, v["caution"])]
    if len(res) > 1:
        lines += [f"{t(L, 'file')} {i}: {v.get(r.scam.verdict, v['caution'])}" for i, r in enumerate(res, 1)]
    reasons = [x for x in worst.scam.reasons if x.kind == "risk"] or list(worst.scam.reasons)
    reasons = [_clean(x.text, src) for x in reasons[:3]]
    steps = [_clean(s, src) for s in worst.scam.verify_yourself[:2]]
    tail = ([t(L, "nsrc")] if worst.scam.verdict == "likely_scam" else []) + ([f"{t(L, 'src')} {src}"] if src else []) + [t(L, "foot")]
    for nr, ns in ((3, 2), (2, 2), (1, 2), (1, 1), (0, 1), (0, 0)):
        body = lines + ([t(L, "why")] + [f"- {x}" for x in reasons[:nr]] if nr and reasons else []) \
            + ([t(L, "check")] + [f"- {x}" for x in steps[:ns]] if ns and steps else []) + tail
        out = "\n".join(body)
        if len(out) <= limit:
            return out
    return "\n".join(lines[:1] + tail)[:limit]
