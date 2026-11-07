"""P4: PWA (19), page metadata (20), production CSP and deploy docs (21)."""
import json
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FE = ROOT / "frontend"


def png_size(p: Path) -> tuple[int, int]:
    b = p.read_bytes()
    assert b[:8] == b"\x89PNG\r\n\x1a\n", p
    return struct.unpack(">II", b[16:24])


# ---------- 19 PWA
def test_manifest_is_complete_and_icons_exist_with_declared_sizes():
    m = json.loads((FE / "manifest.webmanifest").read_text(encoding="utf-8"))
    for k in ("name", "short_name", "start_url", "display", "theme_color", "background_color", "icons"):
        assert m.get(k), k
    assert m["display"] == "standalone"
    purposes = set()
    for i in m["icons"]:
        w, h = map(int, i["sizes"].split("x"))
        assert png_size(FE / i["src"]) == (w, h), i["src"]
        purposes.add(i.get("purpose"))
    assert {"any", "maskable"} <= purposes
    assert any(i["sizes"] == "192x192" for i in m["icons"]) and any(i["sizes"] == "512x512" for i in m["icons"])


def test_index_links_manifest_and_app_registers_service_worker():
    assert 'rel="manifest" href="manifest.webmanifest"' in (FE / "index.html").read_text(encoding="utf-8")
    assert 'serviceWorker.register("sw.js")' in (FE / "assets/js/app.js").read_text(encoding="utf-8")


def test_service_worker_never_touches_api_or_other_origins_and_precaches_the_offline_tools():
    sw = (FE / "sw.js").read_text(encoding="utf-8")
    assert '"/api/"' in sw and "u.origin !== self.location.origin" in sw and 'r.method !== "GET"' in sw
    for f in ("index.html", "assets/js/safety.js", "assets/js/i18n.js", "assets/css/styles.css"):
        assert f'"{f}"' in sw, f
    # every precached file must actually exist
    for f in re.findall(r'"((?:assets/[^"]+|index\.html|embed\.html|manifest\.webmanifest))"', sw):
        assert (FE / f).exists(), f


# ---------- 20 metadata
def test_open_graph_and_twitter_tags():
    h = (FE / "index.html").read_text(encoding="utf-8")
    for tag in ('property="og:title"', 'property="og:description"', 'property="og:image"', 'name="twitter:card" content="summary_large_image"'):
        assert tag in h, tag
    assert re.search(r'og:image" content="https://[^"]+og-image\.png"', h)  # absolute URL, as crawlers require
    assert png_size(FE / "assets/img/og-image.png") == (1200, 630)


def test_lang_attributes_and_logo_alt_text():
    for name in ("index.html", "embed.html"):
        h = (FE / name).read_text(encoding="utf-8")
        assert re.search(r"<html lang=\"(ms|en|zh|ta)\"", h), name
        for img in re.findall(r"<img[^>]*class=\"logo[^>]*>", h):
            assert 'alt="FAHAM logo"' in img, (name, img)
    js = (FE / "assets/js/app.js").read_text(encoding="utf-8")
    assert "document.documentElement.lang = HTML_LANG[state.lang]" in js  # follows the chosen language


# ---------- 21 CSP and deploy doc
def test_production_csp_has_no_localhost_and_dev_csp_does():
    prod = (FE / "nginx.conf").read_text(encoding="utf-8")
    for origin in ("localhost:8000", "127.0.0.1:8000"):  # not a bare "127.0.0.1": the nginx resolver line is 127.0.0.11
        assert origin not in prod
    assert prod.count("connect-src 'self';") == 2  # main CSP and the embed.html CSP
    dev = (FE / "nginx.dev.conf").read_text(encoding="utf-8")
    assert "localhost:8000" in dev
    assert "nginx.dev.conf" in (ROOT / "docker-compose.yml").read_text(encoding="utf-8")


def test_deploy_doc_covers_cloudflare_settings():
    d = (ROOT / "docs/DEPLOY.md").read_text(encoding="utf-8")
    assert "Web Analytics" in d and "Bot Fight Mode" in d and "connect-src 'self'" in d
