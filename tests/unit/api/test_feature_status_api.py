"""Unit tests voor feature_status_api hardening (DEF-473).

Borgt drie fixes:
1. TTL-berekening gebruikt total_seconds() i.p.v. .seconds (geen 24u-rollover-bug).
2. HTTP 500 lekt geen interne exception-tekst (info-disclosure).
3. De module-cache wordt thread-safe gelezen/geschreven (lock aanwezig).
"""

import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import mock_open

import pytest

from api import feature_status_api as fsa

pytestmark = [pytest.mark.unit]


@pytest.fixture(autouse=True)
def _reset_cache():
    """Reset de module-cache rond elke test."""
    fsa._feature_cache = None
    fsa._cache_timestamp = None
    yield
    fsa._feature_cache = None
    fsa._cache_timestamp = None


def _call():
    return asyncio.run(fsa.get_feature_status())


class TestCacheTTL:
    def test_fresh_cache_is_served_without_reload(self, monkeypatch):
        """Een verse cache (< CACHE_DURATION) wordt teruggegeven zonder file-read."""
        fsa._feature_cache = {"sentinel": "CACHED"}
        fsa._cache_timestamp = datetime.now(UTC) - timedelta(seconds=10)

        def _boom(*a, **k):  # file mag niet gelezen worden
            raise AssertionError("file mag niet gelezen worden bij verse cache")

        monkeypatch.setattr("builtins.open", _boom)
        assert _call() == {"sentinel": "CACHED"}

    def test_cache_older_than_24h_is_expired(self, monkeypatch):
        """Regressie .seconds-bug: een cache van 24u+10s is STALE en moet herladen.

        Met .seconds zou timedelta(days=1, seconds=10).seconds == 10 (< 300) de
        stale cache onterecht als vers serveren. Met total_seconds() == 86410
        verloopt de cache correct.
        """
        fsa._feature_cache = {"sentinel": "STALE"}
        fsa._cache_timestamp = datetime.now(UTC) - timedelta(days=1, seconds=10)

        monkeypatch.setattr("builtins.open", mock_open(read_data="{}"))
        monkeypatch.setattr(fsa.json, "load", lambda f: {"sentinel": "FRESH"})

        assert _call() == {"sentinel": "FRESH"}


class TestInfoDisclosure:
    def test_500_does_not_leak_exception_text(self, monkeypatch):
        """Een file-load-fout met gevoelig pad mag niet in de HTTP 500-body lekken."""
        secret = "/secret/internal/path/feature-status.json"

        def _raise(*a, **k):
            raise FileNotFoundError(secret)

        monkeypatch.setattr("builtins.open", _raise)

        with pytest.raises(fsa.HTTPException) as exc_info:
            _call()

        assert exc_info.value.status_code == 500
        assert secret not in str(exc_info.value.detail)
        assert "internal" in str(exc_info.value.detail).lower()


class TestThreadSafety:
    def test_module_has_cache_lock(self):
        """Er is een lock voor de cache (thread-safe lezen/schrijven)."""
        lock = getattr(fsa, "_cache_lock", None)
        assert lock is not None
        # Een threading.Lock heeft acquire/release (geen loop-gebonden asyncio.Lock).
        assert hasattr(lock, "acquire") and hasattr(lock, "release")
