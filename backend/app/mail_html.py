"""The reply email: a branded HTML message plus a plain-text twin. Pure functions, no I/O.

Same rules as reply.py: never says a document is genuine, never echoes the sender's text or file names,
and the only link is the registry's official source (https only) plus the Terms page.
Every string from analysis is HTML-escaped. The logo is embedded by the sender (Content-ID), not fetched.
zh/ta strings need native-speaker review.
"""
from __future__ import annotations

import html
import os
from pathlib import Path

from . import reply

LOGO = Path(__file__).parent / "data" / "logo-mark.png"
CID = "faham-logo"

S = {
    "bm": dict(title="Keputusan semakan Tulen", msg="E-mel ini", att="Lampiran", sum="Ringkasan",
               auto="Ini balasan automatik. Tulen tidak dapat melihat siapa penghantar sebenar mesej anda, atau pautan sebenar di sebalik butang.",
               pre="Keputusan semakan untuk mesej yang anda hantar", rep="Lapor penipuan:"),
    "en": dict(title="Tulen check result", msg="The email itself", att="Attachment", sum="Summary",
               auto="This is an automatic reply. Tulen cannot see who really sent your message, or the real link behind a button.",
               pre="The check result for the message you sent", rep="Report a scam:"),
    "zh": dict(title="Tulen 检查结果", msg="邮件本身", att="附件", sum="摘要",
               auto="这是自动回复。Tulen 无法看到您收到的信息的真正发送者，也看不到按钮背后的真实链接。",
               pre="您发送的信息的检查结果", rep="举报诈骗："),
    "ta": dict(title="Tulen சரிபார்ப்பு முடிவு", msg="மின்னஞ்சல்", att="இணைப்பு", sum="சுருக்கம்",
               auto="இது தானியங்கி பதில். உங்கள் செய்தியை உண்மையில் அனுப்பியவர் யார் என்பதையும், பொத்தானின் பின்னுள்ள உண்மையான இணைப்பையும் Tulen பார்க்க முடியாது.",
               pre="நீங்கள் அனுப்பிய செய்திக்கான சரிபார்ப்பு முடிவு", rep="மோசடியைப் புகாரளிக்க:"),
}
PAL = {"likely_scam": ("#a3190f", "#fdecea"), "caution": ("#7a4b00", "#fff3d1"), "no_signals": ("#1d5a3a", "#e6f2ec")}
INK, LAV, MIST = "#2a1e4d", "#8b7cc7", "#f1eff7"
FONT = "-apple-system,'Segoe UI',Roboto,'Noto Sans','Noto Sans SC','Noto Sans Tamil',Arial,sans-serif"


def _digest(batch, language: str) -> dict | None:
    L = language if language in reply.T else "bm"
    files = [f for f in batch.files if getattr(f, "result", None)]
    if not files:
        return None
    res = [f.result for f in files]
    worst = max(res, key=lambda r: reply._RANK.get(r.scam.verdict, 1))
    src = getattr(getattr(worst, "route", None), "source_url", "") or ""
    v = reply.t(L, "v")
    sc = worst.scam
    pick = [x for x in sc.reasons if x.kind == "risk"][:5] or [x for x in sc.reasons if x.kind in ("ok", "info")][:4]
    items = []
    if len(files) > 1:
        n = 0
        for f in files:
            if getattr(f, "kind", "") == "eml":
                label = S[L]["msg"]
            else:
                n += 1
                label = f"{S[L]['att']} {n}"
            items.append((label, f.result.scam.verdict, v.get(f.result.scam.verdict, v["caution"])))
    return dict(L=L, verdict=sc.verdict, head=v.get(sc.verdict, v["caution"]), src=src, items=items,
                why=[reply._clean(x.text, src, 240) for x in pick], check=[reply._clean(s, src, 240) for s in sc.verify_yourself[:4]])


def _terms_url() -> str:
    u = os.getenv("FAHAM_PUBLIC_URL", "").rstrip("/")
    return f"{u}/terms" if u.startswith("https://") else ""


def text(batch, language: str) -> str:
    d = _digest(batch, language)
    if d is None:
        L = language if language in reply.T else "bm"
        return f"{reply.t(L, 'err')}\n\n{reply.t(L, 'foot')}"
    L, out = d["L"], [S[d["L"]]["title"].upper(), "=" * 32, d["head"], ""]
    if d["items"]:
        out += [f"{S[L]['sum']}:"] + [f"  {lab}: {txt}" for lab, _, txt in d["items"]] + [""]
    if d["why"]:
        out += [reply.t(L, "why")] + [f"  - {x}" for x in d["why"]] + [""]
    if d["check"]:
        out += [reply.t(L, "check")] + [f"  {i}. {x}" for i, x in enumerate(d["check"], 1)] + [""]
    if d["verdict"] == "likely_scam":
        out += [reply.t(L, "nsrc"), ""]
    if d["src"].startswith("https://"):
        out += [f"{reply.t(L, 'src')} {d['src']}", ""]
    out += ["-" * 32, S[L]["auto"], reply.notice(L), reply.t(L, "foot")]
    return "\n".join(out)


def html_body(batch, language: str, with_logo: bool = True) -> str:
    d = _digest(batch, language)
    L = language if language in reply.T else "bm"
    e = html.escape
    if d is None:
        main = f'<p style="margin:0;font-size:16px;line-height:1.6;color:{INK}">{e(reply.t(L, "err"))}</p>'
        verdict_box = ""
    else:
        L = d["L"]
        fg, bg = PAL.get(d["verdict"], PAL["caution"])
        verdict_box = (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse"><tr>'
                       f'<td style="background:{bg};border-left:6px solid {fg};border-radius:8px;padding:18px 20px">'
                       f'<div style="font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:{fg};font-weight:700">{e(S[L]["title"])}</div>'
                       f'<div style="font-size:22px;line-height:1.3;font-weight:700;color:{fg};margin-top:6px">{e(d["head"])}</div></td></tr></table>')
        parts = []

        def block(title, inner):
            parts.append(f'<h2 style="margin:26px 0 8px;font-size:16px;color:{INK}">{e(title)}</h2>{inner}')
        if d["items"]:
            rows = "".join(
                f'<tr><td style="padding:8px 0;border-bottom:1px solid #e4e0ee;font-size:15px;color:{INK}">{e(lab)}</td>'
                f'<td align="right" style="padding:8px 0;border-bottom:1px solid #e4e0ee;font-size:14px;font-weight:700;color:{PAL.get(v, PAL["caution"])[0]}">{e(txt)}</td></tr>'
                for lab, v, txt in d["items"])
            block(S[L]["sum"], f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse">{rows}</table>')
        if d["why"]:
            block(reply.t(L, "why").rstrip(":："), "<ul style=\"margin:0;padding-left:20px;font-size:15px;line-height:1.6;color:#2b2540\">"
                  + "".join(f"<li style=\"margin:0 0 6px\">{e(x)}</li>" for x in d["why"]) + "</ul>")
        if d["check"]:
            block(reply.t(L, "check").rstrip(":："), "<ol style=\"margin:0;padding-left:22px;font-size:15px;line-height:1.6;color:#2b2540\">"
                  + "".join(f"<li style=\"margin:0 0 6px\">{e(x)}</li>" for x in d["check"]) + "</ol>")
        if d["verdict"] == "likely_scam":
            parts.append(f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-top:22px"><tr>'
                         f'<td style="background:{MIST};border-radius:8px;padding:14px 16px;font-size:15px;line-height:1.5;color:{INK}"><b>{e(reply.t(L, "nsrc"))}</b></td></tr></table>')
        if d["src"].startswith("https://"):
            parts.append(f'<p style="margin:22px 0 0;font-size:14px;color:#4a4560">{e(reply.t(L, "src"))} '
                         f'<a href="{e(d["src"], quote=True)}" style="color:{INK};font-weight:700">{e(d["src"].removeprefix("https://"))}</a></p>')
        main = "".join(parts)
    terms = _terms_url()
    terms_a = f' &nbsp;·&nbsp; <a href="{e(terms, quote=True)}" style="color:{LAV}">{e(reply.t(L, "n3"))}</a>' if terms else ""
    logo = f'<img src="cid:{CID}" width="31" height="40" alt="" style="display:block;border:0">' if with_logo else ""
    return f"""<!doctype html>
<html lang="{ {'bm': 'ms', 'en': 'en', 'zh': 'zh', 'ta': 'ta'}[L] }"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light"><title>{e(S[L]["title"])}</title></head>
<body style="margin:0;padding:0;background:{MIST};font-family:{FONT}">
<div style="display:none;max-height:0;overflow:hidden;opacity:0">{e(S[L]["pre"])}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{MIST}"><tr><td align="center" style="padding:24px 12px">
 <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="width:100%;max-width:600px;border-collapse:collapse;background:#ffffff;border-radius:12px;overflow:hidden">
  <tr><td style="background:{INK};padding:20px 28px;border-bottom:4px solid {LAV}">
   <table role="presentation" cellpadding="0" cellspacing="0"><tr>
    <td style="padding-right:12px">{logo}</td>
    <td><div style="font-size:22px;font-weight:800;letter-spacing:.08em;color:#ffffff">Tulen</div>
     <div style="font-size:12px;color:#cfc8ea;margin-top:2px">Tulen atau tipu? Semak dulu.</div></td>
   </tr></table>
  </td></tr>
  <tr><td style="padding:28px 28px 8px">{verdict_box}{main}</td></tr>
  <tr><td style="padding:8px 28px 28px"><p style="margin:18px 0 0;font-size:13px;line-height:1.5;color:#6a6486">{e(S[L]["auto"])}</p></td></tr>
  <tr><td style="background:{INK};padding:22px 28px;border-top:4px solid {LAV}">
   <p style="margin:0 0 8px;font-size:12px;line-height:1.6;color:#cfc8ea">{e(reply.t(L, "n1"))}</p>
   <p style="margin:0 0 12px;font-size:12px;line-height:1.6;color:#cfc8ea">{e(reply.t(L, "n2"))}</p>
   <p style="margin:0;font-size:12px;color:#ffffff"><b>Tulen</b> &nbsp;·&nbsp; {e(reply.t(L, "foot"))}{terms_a}</p>
   <p style="margin:8px 0 0;font-size:12px;color:#cfc8ea">{e(S[L]["rep"])} <a href="tel:997" style="color:#ffffff;font-weight:700">NSRC 997</a></p>
  </td></tr>
 </table>
</td></tr></table>
</body></html>"""
