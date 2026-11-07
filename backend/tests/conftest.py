import pytest

from app import cache, counter


@pytest.fixture(autouse=True)
def _isolated_state(monkeypatch):
    """Each test gets an empty in-memory counter and cache, so nothing is written to disk or leaks between tests."""
    monkeypatch.setattr(counter, "COUNTER", counter.Counter(":memory:"))
    cache.ANALYSES.clear()
    yield
