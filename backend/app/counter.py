"""Privacy-safe "others checked this" counter.

Stores ONLY: a SHA-256 fingerprint of the normalised, REDACTED text, a count, and two timestamps.
Never the text, never an IP, never a user id. The normaliser drops digits, URLs and punctuation so the same
scam sent with a different amount or phone number still lands on one fingerprint ("a similar message").
Rows not seen for RETENTION_DAYS are deleted.
"""
from __future__ import annotations

import hashlib
import re
import sqlite3
import threading
import time

RETENTION_DAYS = 90

_PLACEHOLDER = re.compile(r"\[[A-Z]+\]")
_URL = re.compile(r"(?:https?://)?(?:[a-z0-9-]+\.)+[a-z]{2,}(?:/\S*)?", re.IGNORECASE)
_DIGITS = re.compile(r"\d+")
_NOISE = re.compile(r"[^\w\s]|_", re.UNICODE)


def normalise(redacted: str) -> str:
    s = _PLACEHOLDER.sub(" ", redacted.lower())
    s = _URL.sub(" url ", s)
    s = _DIGITS.sub("#", s)
    s = _NOISE.sub(" ", s)
    return " ".join(s.split())


def fingerprint(redacted: str) -> str:
    return hashlib.sha256(normalise(redacted).encode("utf-8")).hexdigest()


class Counter:
    def __init__(self, path: str = ":memory:") -> None:
        if path != ":memory:":
            import os
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        self._db = sqlite3.connect(path, check_same_thread=False)
        self._lock = threading.Lock()
        with self._lock:
            self._db.execute("CREATE TABLE IF NOT EXISTS seen (fp TEXT PRIMARY KEY, n INTEGER NOT NULL, first_ts INTEGER NOT NULL, last_ts INTEGER NOT NULL)")
            self._db.execute("DELETE FROM seen WHERE last_ts < ?", (int(time.time()) - RETENTION_DAYS * 86400,))
            self._db.commit()

    def hit(self, redacted: str) -> int:
        """Record one check and return how many OTHER people checked a similar message before."""
        fp, now = fingerprint(redacted), int(time.time())
        with self._lock:
            row = self._db.execute("SELECT n FROM seen WHERE fp = ?", (fp,)).fetchone()
            if row:
                self._db.execute("UPDATE seen SET n = n + 1, last_ts = ? WHERE fp = ?", (now, fp))
            else:
                self._db.execute("INSERT INTO seen (fp, n, first_ts, last_ts) VALUES (?, 1, ?, ?)", (fp, now, now))
            self._db.commit()
            return row[0] if row else 0

    def rows(self) -> list[tuple]:
        with self._lock:
            return self._db.execute("SELECT fp, n, first_ts, last_ts FROM seen").fetchall()


def _make() -> Counter:
    from . import config
    return Counter(config.COUNTER_DB)


COUNTER = _make()
