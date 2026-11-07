"""Fair concurrency limiter: at most N analyses run at once, the rest wait in a first-in first-out queue.

Waiters can ask "what is my place in line" so the SSE stream can tell the user "you are number 3".
Pure threading primitives (no event-loop binding), so it works from sync generators and the thread pool.
"""
from __future__ import annotations

import threading
import time
from collections import deque
from contextlib import contextmanager

from . import config


class Busy(Exception):
    """Raised when a request waited longer than its patience."""


class Limiter:
    def __init__(self, slots: int) -> None:
        self.slots = max(1, slots)
        self.active = 0
        self._q: deque[object] = deque()
        self._cv = threading.Condition()

    def enter(self) -> object:
        ticket = object()
        with self._cv:
            self._q.append(ticket)
        return ticket

    def position(self, ticket: object) -> int:
        """1 = next up. 0 when the ticket is no longer waiting."""
        with self._cv:
            try:
                return list(self._q).index(ticket) + 1
            except ValueError:
                return 0

    def acquire(self, ticket: object, timeout: float) -> bool:
        end = time.monotonic() + timeout
        with self._cv:
            while not (self._q and self._q[0] is ticket and self.active < self.slots):
                left = end - time.monotonic()
                if left <= 0:
                    return False
                self._cv.wait(left)
            self._q.popleft()
            self.active += 1
            self._cv.notify_all()
            return True

    def leave(self, ticket: object) -> None:
        with self._cv:
            try:
                self._q.remove(ticket)
            except ValueError:
                pass
            self._cv.notify_all()

    def release(self) -> None:
        with self._cv:
            self.active -= 1
            self._cv.notify_all()

    @contextmanager
    def slot(self, patience: float = 60.0):
        ticket = self.enter()
        if not self.acquire(ticket, patience):
            self.leave(ticket)
            raise Busy()
        try:
            yield
        finally:
            self.release()

    def waiting(self) -> int:
        with self._cv:
            return len(self._q)


LIMITER = Limiter(config.MAX_CONCURRENT)
