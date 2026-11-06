"""Runtime configuration read from environment variables."""
import os
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "FAHAM_ALLOWED_ORIGINS",
        "http://localhost:5500,http://127.0.0.1:5500,http://localhost:8080,http://127.0.0.1:8080",
    ).split(",")
    if o.strip()
]

ALLOW_NULL_ORIGIN = os.getenv("FAHAM_ALLOW_NULL_ORIGIN") == "1"  # file:// dev only

LLM_PROVIDER = os.getenv("FAHAM_LLM_PROVIDER", "none").lower()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ILMU_API_KEY = os.getenv("ILMU_API_KEY", "")
ILMU_BASE_URL = os.getenv("ILMU_BASE_URL", "https://api.ilmu.ai/v1").rstrip("/")
LLM_MODEL = os.getenv("FAHAM_LLM_MODEL") or ("ilmu-mini-v3.3" if LLM_PROVIDER == "ilmu" else "claude-sonnet-5-5")


def llm_ready() -> bool:
    """True when the selected provider has a key. Never exposes the key."""
    return bool({"anthropic": ANTHROPIC_API_KEY, "ilmu": ILMU_API_KEY}.get(LLM_PROVIDER))
