"""Stamps every CSS and JS link in frontend/*.html with a fingerprint of the file: assets/js/app.js?v=1a2b3c4d.
A CDN (Cloudflare) caches files for hours; a changed file then gets a new address, so an old copy can never be paired with a new page.
Run after any change under frontend/assets:   python scripts/bust_cache.py
A backend test fails if the stamps are out of date."""
import hashlib
import re
from pathlib import Path

FRONT = Path(__file__).resolve().parent.parent / "frontend"
LINK = re.compile(r'((?:src|href)="assets/(?:js|css)/[\w.-]+\.(?:js|css))(?:\?v=[0-9a-f]+)?(")')


def stamp(write: bool = False) -> list[str]:
    """Returns the pages whose stamps were wrong (and fixes them when write=True)."""
    stale = []
    for page in sorted(FRONT.glob("*.html")):
        s = page.read_text(encoding="utf-8")

        def fix(m):
            f = FRONT / m.group(1).split('"', 1)[1]
            return f'{m.group(1)}?v={hashlib.md5(f.read_bytes()).hexdigest()[:8]}{m.group(2)}'
        new = LINK.sub(fix, s)
        if new != s:
            stale.append(page.name)
            if write:
                page.write_text(new, encoding="utf-8", newline="")
    return stale


if __name__ == "__main__":
    print("updated:", stamp(write=True) or "nothing to change")
