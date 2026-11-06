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
ILMU_TTS_MODEL = os.getenv("FAHAM_TTS_MODEL", "ilmu-tts-v2.1")
ILMU_TTS_VOICE = os.getenv("FAHAM_TTS_VOICE", "voice_1")
# FAHAM_LLM_PROVIDER may list several, tried in order, e.g. "ilmu,anthropic".
MODELS = {"ilmu": os.getenv("FAHAM_LLM_MODEL_ILMU", "ilmu-mini-v3.3"),
          "anthropic": os.getenv("FAHAM_LLM_MODEL_ANTHROPIC") or os.getenv("FAHAM_LLM_MODEL", "claude-sonnet-5-5")}


def llm_chain() -> list[str]:
    """Providers that are selected AND have a key, in order. Never exposes keys."""
    keys = {"anthropic": ANTHROPIC_API_KEY, "ilmu": ILMU_API_KEY}
    return [p for p in (x.strip() for x in LLM_PROVIDER.split(",")) if keys.get(p)]


def llm_ready() -> bool:
    return bool(llm_chain())
