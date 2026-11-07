"""In-memory LRU cache with a time-to-live. Holds finished analyses keyed by a hash of the REDACTED text.

Raw letter text is never a key or a value. A cache miss only costs time: the pipeline is deterministic
(rules first, LLM at temperature 0), so a hit and a fresh run give the same verdict and score.
"""
from __future__ import annotations

import hashlib
import threading
import time
from collections import OrderedDict
from typing import Any


class TTLCache:
    def __init__(self, maxsize: int = 512, ttl: float = 3600.0, clock=time.monotonic) -> None:
        self.maxsize, self.ttl, self._clock = maxsize, ttl, clock
        self._d: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: str):
        with self._lock:
            hit = self._d.get(key)
            if not hit:
                return None
            if self._clock() - hit[0] > self.ttl:
                del self._d[key]
                return None
            self._d.move_to_end(key)
            return hit[1]

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._d[key] = (self._clock(), value)
            self._d.move_to_end(key)
            while len(self._d) > self.maxsize:
                self._d.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._d.clear()

    def __len__(self) -> int:
        return len(self._d)


def fingerprint(redacted: str, *parts: object) -> str:
    """SHA-256 of the normalised redacted text plus language and other context. Never of raw text."""
    norm = " ".join(redacted.lower().split())
    return hashlib.sha256(("\x1f".join(str(p) for p in parts) + "\x1e" + norm).encode("utf-8")).hexdigest()


ANALYSES = TTLCache()
