import importlib.util
from pathlib import Path


def test_asset_links_carry_current_fingerprints():
    """If this fails run `python scripts/bust_cache.py`: otherwise a CDN may serve an old script next to a new page."""
    spec = importlib.util.spec_from_file_location("bust_cache", Path(__file__).resolve().parents[2] / "scripts" / "bust_cache.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.stamp() == []
