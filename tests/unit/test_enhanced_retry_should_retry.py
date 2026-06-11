"""Unit tests for AdaptiveRetryManager.should_retry classification (DEF-429).

An invalid/missing API key surfaces as an authentication error. That is a
permanent failure, not a transient one, so it must NOT be retried — otherwise
generation hangs for minutes on backoff (and the UI freezes). Transient errors
(rate limit, connection, generic provider 5xx) must still be retried.
"""

from __future__ import annotations

import pytest

from services.ai.base_client import (
    AIAuthenticationClientError,
    AIClientError,
    AIConnectionClientError,
    AIRateLimitClientError,
)
from utils.enhanced_retry import AdaptiveRetryManager, RetryConfig

pytestmark = [pytest.mark.unit]


@pytest.fixture
def manager() -> AdaptiveRetryManager:
    """Fresh manager with a closed circuit and ample retry budget."""
    return AdaptiveRetryManager(RetryConfig(max_retries=5))


class TestShouldRetryClassification:
    """should_retry must fail fast on auth errors, retry transient ones."""

    async def test_authentication_error_is_not_retried(self, manager):
        """DEF-429: auth error (invalid/missing key) must not be retried."""
        assert (
            await manager.should_retry(AIAuthenticationClientError("bad key"), 1)
            is False
        )

    async def test_rate_limit_error_is_retried(self, manager):
        assert await manager.should_retry(AIRateLimitClientError("429"), 1) is True

    async def test_connection_error_is_retried(self, manager):
        assert await manager.should_retry(AIConnectionClientError("net"), 1) is True

    async def test_generic_client_error_is_retried(self, manager):
        """Generic AIClientError (e.g. mapped 5xx) stays retryable."""
        assert await manager.should_retry(AIClientError("5xx"), 1) is True

    async def test_authentication_error_not_retried_at_first_attempt(self, manager):
        """Even on the very first retry decision the auth error fails fast."""
        # attempt well below max_retries so only the type classification matters
        assert (
            await manager.should_retry(AIAuthenticationClientError("bad key"), 1)
            is False
        )
