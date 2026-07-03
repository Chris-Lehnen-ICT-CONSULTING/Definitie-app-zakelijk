"""Tests voor DEF-514: opruimen van lege IP-keys in de rate-limiter.

Per-IP timestamps werden al geschoond, maar lege IP-keys bleven staan in
``request_tracking`` (memory-lek; ``blocked_ips`` werd wél opgeruimd).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

pytestmark = [pytest.mark.unit]


def _make_middleware():
    with (
        patch("security.security_middleware.get_validator", return_value=MagicMock()),
        patch("security.security_middleware.get_sanitizer", return_value=MagicMock()),
    ):
        from security.security_middleware import SecurityMiddleware

        return SecurityMiddleware()


def _request(ip: str):
    from security.security_middleware import ValidationRequest

    return ValidationRequest(
        endpoint="default",
        method="POST",
        data={},
        headers={},
        source_ip=ip,
        user_agent="pytest",
        timestamp=datetime.now(UTC),
    )


class TestRateLimitKeyCleanup:
    def test_empty_ip_key_removed_after_cleanup(self):
        """IP-key met alleen verlopen timestamps verdwijnt uit request_tracking."""
        middleware = _make_middleware()
        stale = datetime.now(UTC) - timedelta(hours=2)
        middleware.request_tracking["10.0.0.1"] = [stale, stale]

        allowed = middleware._check_rate_limit(_request("10.0.0.1"))

        assert allowed is True
        assert "10.0.0.1" not in middleware.request_tracking

    def test_recent_timestamps_are_kept(self):
        """Keys met recente requests blijven bestaan (alleen verlopen entries weg)."""
        middleware = _make_middleware()
        stale = datetime.now(UTC) - timedelta(hours=2)
        fresh = datetime.now(UTC) - timedelta(minutes=5)
        middleware.request_tracking["10.0.0.2"] = [stale, fresh]

        allowed = middleware._check_rate_limit(_request("10.0.0.2"))

        assert allowed is True
        assert middleware.request_tracking["10.0.0.2"] == [fresh]

    def test_unknown_ip_does_not_create_empty_key(self):
        """Een check voor een onbekend IP laat geen lege key achter."""
        middleware = _make_middleware()

        allowed = middleware._check_rate_limit(_request("10.0.0.3"))

        assert allowed is True
        assert "10.0.0.3" not in middleware.request_tracking

    def test_rate_limit_still_enforced(self):
        """Regressie: limieten blijven gehandhaafd na de cleanup-refactor."""
        middleware = _make_middleware()
        limit = middleware.rate_limits["default"]["requests_per_minute"]
        now = datetime.now(UTC)
        middleware.request_tracking["10.0.0.4"] = [
            now - timedelta(seconds=30) for _ in range(limit)
        ]

        assert middleware._check_rate_limit(_request("10.0.0.4")) is False

    def test_record_request_recreates_key(self):
        """_record_request werkt nog na key-verwijdering."""
        middleware = _make_middleware()
        middleware._record_request("10.0.0.5")
        assert len(middleware.request_tracking["10.0.0.5"]) == 1
