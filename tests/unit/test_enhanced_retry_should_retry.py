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
from utils import enhanced_retry
from utils.enhanced_retry import (
    AdaptiveRetryManager,
    RetryConfig,
    with_enhanced_retry,
)

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


@pytest.fixture
def reset_retry_manager():
    """Reset the module-level retry-manager singleton around a test.

    with_enhanced_retry uses the global manager; resetting it gives the
    decorator a fresh, closed-circuit manager with the test's config.
    """
    enhanced_retry._retry_manager = None
    yield
    enhanced_retry._retry_manager = None


class TestWithEnhancedRetryFailFast:
    """DEF-429: the decorator must not retry auth errors end-to-end."""

    async def test_decorator_does_not_retry_authentication_error(
        self, reset_retry_manager
    ):
        """An auth error propagates after exactly one call — no backoff retries."""
        calls = 0

        @with_enhanced_retry(config=RetryConfig(max_retries=3, base_delay=0.01))
        async def always_auth_fails():
            nonlocal calls
            calls += 1
            raise AIAuthenticationClientError("invalid api key")

        with pytest.raises(AIAuthenticationClientError):
            await always_auth_fails()

        # Fail fast: wrapped function invoked once, not max_retries + 1 times.
        assert calls == 1

    async def test_decorator_still_retries_transient_error(self, reset_retry_manager):
        """A transient error is retried (control: proves the fail-fast is specific)."""
        calls = 0

        @with_enhanced_retry(config=RetryConfig(max_retries=2, base_delay=0.01))
        async def fails_then_succeeds():
            nonlocal calls
            calls += 1
            if calls < 2:
                raise AIConnectionClientError("transient")
            return "ok"

        result = await fails_then_succeeds()
        assert result == "ok"
        assert calls == 2  # retried once, then succeeded
