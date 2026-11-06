"""Writes CODE_OF_CONDUCT.md and docs/TERMS_AND_PRIVACY.md (English) from frontend/assets/legal.json.
The website reads the same JSON, so edit the JSON and run:  python scripts/legal_md.py"""
import json
from pathlib import Path

root = Path(__file__).resolve().parent.parent
d = json.loads((root / "frontend/assets/legal.json").read_text(encoding="utf-8"))
en = d["en"]
NOTE = "<!-- Generated from frontend/assets/legal.json by scripts/legal_md.py. Edit the JSON, not this file. -->\n"


def part(p, level="##"):
    out = [f"{level} {p['h']}\n"]
    if p.get("intro"):
        out.append(p["intro"] + "\n")
    for i, s in enumerate(p["sections"], 1):
        out.append(f"### {i}. {s['h']}\n")
        out += [x + "\n" for x in s.get("p", [])]
        if s.get("ul"):
            out += [f"- {x}" for x in s["ul"]] + [""]
    return "\n".join(out)


def doc(title, parts, lead):
    return NOTE + f"# {title}\n\n{en['updated']}. {en['draft']}\n\n{lead}\n\n" + "\n".join(part(p) for p in parts)


terms, privacy, coc = en["parts"]
summary = f"**{en['summary_h']}**\n\n" + "\n".join(f"- {x}" for x in en["summary"])
(root / "CODE_OF_CONDUCT.md").write_text(doc("FAHAM Code of Conduct", [coc], ""), encoding="utf-8")
(root / "docs/TERMS_AND_PRIVACY.md").write_text(doc("FAHAM Terms of Use and Privacy Notice", [terms, privacy], summary), encoding="utf-8")
print("written")
