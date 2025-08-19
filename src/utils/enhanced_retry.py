"""
Enhanced retry logic and resilience framework for DefinitieAgent.
Provides circuit breaker patterns, adaptive retry strategies, and intelligent error handling.
"""

import asyncio
import json
import logging
import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import Any

from openai import APIConnectionError, APIError, RateLimitError

logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """Retry strategy types."""

    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"
    ADAPTIVE = "adaptive"


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_retries: int = 5
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    strategy: RetryStrategy = RetryStrategy.ADAPTIVE

    # Circuit breaker settings
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    success_threshold: int = 2

    # Error-specific settings
    rate_limit_multiplier: float = 2.0
    connection_error_multiplier: float = 1.5
    api_error_multiplier: float = 1.0


@dataclass
class RequestMetrics:
    """Metrics for individual requests."""

    timestamp: datetime
    duration: float
    success: bool
    error_type: str | None = None
    retry_count: int = 0
    endpoint: str = ""


@dataclass
class CircuitBreakerState:
    """State of circuit breaker."""

    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: datetime | None = None
    last_success_time: datetime | None = None
    total_requests: int = 0
    total_failures: int = 0


class AdaptiveRetryManager:
    """Manages adaptive retry strategies with circuit breaker pattern."""

    def __init__(self, config: RetryConfig):
        self.config = config
        self.circuit_state = CircuitBreakerState()
        self.request_history: list[RequestMetrics] = []
        self.error_patterns: dict[str, list[float]] = {}
        self.adaptive_delays: dict[str, float] = {}
        self._lock = asyncio.Lock()

        # Load historical data if available
        self._load_historical_data()

    def _load_historical_data(self):
        """Load historical retry data for adaptive learning."""
        try:
            history_file = Path("cache/retry_history.json")
            if history_file.exists():
                with open(history_file) as f:
                    data = json.load(f)
                    self.error_patterns = data.get("error_patterns", {})
                    self.adaptive_delays = data.get("adaptive_delays", {})
                    logger.info("Loaded retry history for adaptive learning")
        except Exception as e:
            logger.warning(f"Could not load retry history: {e}")

    def _save_historical_data(self):
        """Save historical data for future adaptive learning."""
        try:
            history_file = Path("cache/retry_history.json")
            history_file.parent.mkdir(exist_ok=True)

            data = {
                "error_patterns": self.error_patterns,
                "adaptive_delays": self.adaptive_delays,
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }

            with open(history_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save retry history: {e}")

    async def should_retry(self, error: Exception, attempt: int) -> bool:
        """Determine if request should be retried based on circuit breaker state."""
        async with self._lock:
            if self.circuit_state.state == CircuitState.OPEN:
                # Check if we should try to recover
                if self.circuit_state.last_failure_time and datetime.now(
                    timezone.utc
                ) - self.circuit_state.last_failure_time > timedelta(
                    seconds=self.config.recovery_timeout
                ):
                    self.circuit_state.state = CircuitState.HALF_OPEN
                    self.circuit_state.success_count = 0
                    logger.info("Circuit breaker transitioning to HALF_OPEN")
                else:
                    logger.warning("Circuit breaker OPEN - rejecting request")
                    return False

            # Check max retries
            if attempt >= self.config.max_retries:
                await self._record_failure(error)
                return False

            # Allow retry for specific error types
            return bool(
                isinstance(error, RateLimitError | APIConnectionError | APIError)
            )

    async def get_retry_delay(self, error: Exception, attempt: int) -> float:
        """Calculate adaptive retry delay based on error type and history."""
        error_type = type(error).__name__

        # Get base delay using configured strategy
        if self.config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = self.config.base_delay * (self.config.exponential_base**attempt)
        elif self.config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = self.config.base_delay * (attempt + 1)
        elif self.config.strategy == RetryStrategy.FIXED_DELAY:
            delay = self.config.base_delay
        elif self.config.strategy == RetryStrategy.ADAPTIVE:
            delay = await self._get_adaptive_delay(error_type, attempt)
        else:
            delay = self.config.base_delay

        # Apply error-specific multipliers
        if isinstance(error, RateLimitError):
            delay *= self.config.rate_limit_multiplier
        elif isinstance(error, APIConnectionError):
            delay *= self.config.connection_error_multiplier
        elif isinstance(error, APIError):
            delay *= self.config.api_error_multiplier

        # Apply jitter to prevent thundering herd
        if self.config.jitter:
            jitter_factor = 0.1  # ±10% jitter
            delay *= 1 + random.uniform(-jitter_factor, jitter_factor)

        # Ensure delay is within bounds
        delay = min(delay, self.config.max_delay)
        delay = max(delay, 0.1)  # Minimum 100ms

        logger.debug(
            f"Calculated retry delay: {delay:.2f}s for {error_type} (attempt {attempt})"
        )
        return delay

    async def _get_adaptive_delay(self, error_type: str, attempt: int) -> float:
        """Calculate adaptive delay based on historical success rates."""
        # Get historical delay for this error type
        if error_type in self.adaptive_delays:
            base_delay = self.adaptive_delays[error_type]
        else:
            base_delay = self.config.base_delay

        # Analyze recent patterns for this error type
        if error_type in self.error_patterns:
            recent_delays = self.error_patterns[error_type][-10:]  # Last 10 occurrences
            if recent_delays:
                # Use median of recent successful delays
                recent_delays.sort()
                median_delay = recent_delays[len(recent_delays) // 2]
                base_delay = (base_delay + median_delay) / 2

        # Apply exponential backoff on top of adaptive base
        return base_delay * (1.5**attempt)

    async def record_success(self, duration: float, endpoint: str = ""):
        """Record successful request for adaptive learning."""
        async with self._lock:
            now = datetime.now(timezone.utc)

            # Update circuit breaker state
            if self.circuit_state.state == CircuitState.HALF_OPEN:
                self.circuit_state.success_count += 1
                if self.circuit_state.success_count >= self.config.success_threshold:
                    self.circuit_state.state = CircuitState.CLOSED
                    self.circuit_state.failure_count = 0
                    logger.info("Circuit breaker recovered - transitioning to CLOSED")

            self.circuit_state.last_success_time = now
            self.circuit_state.total_requests += 1

            # Record metrics
            metrics = RequestMetrics(
                timestamp=now, duration=duration, success=True, endpoint=endpoint
            )
            self.request_history.append(metrics)

            # Keep only recent history
            cutoff = now - timedelta(hours=24)
            self.request_history = [
                m for m in self.request_history if m.timestamp > cutoff
            ]

            # Save periodically
            if self.circuit_state.total_requests % 100 == 0:
                self._save_historical_data()

    async def _record_failure(self, error: Exception):
        """Record request failure for circuit breaker logic."""
        now = datetime.now(timezone.utc)
        error_type = type(error).__name__

        # Update circuit breaker state
        self.circuit_state.failure_count += 1
        self.circuit_state.last_failure_time = now
        self.circuit_state.total_requests += 1
        self.circuit_state.total_failures += 1

        # Check if we should open the circuit
        if (
            self.circuit_state.state == CircuitState.CLOSED
            and self.circuit_state.failure_count >= self.config.failure_threshold
        ):
            self.circuit_state.state = CircuitState.OPEN
            logger.warning(
                f"Circuit breaker OPEN after {self.circuit_state.failure_count} failures"
            )

        # Record error pattern
        if error_type not in self.error_patterns:
            self.error_patterns[error_type] = []

        # Record the time since last error of this type
        recent_errors = [
            m
            for m in self.request_history
            if not m.success and m.error_type == error_type
        ]
        if recent_errors:
            time_since_last = (now - recent_errors[-1].timestamp).total_seconds()
            self.error_patterns[error_type].append(time_since_last)

            # Keep only recent patterns
            self.error_patterns[error_type] = self.error_patterns[error_type][-50:]

    def get_health_metrics(self) -> dict[str, Any]:
        """Get current health and performance metrics."""
        total_requests = self.circuit_state.total_requests
        total_failures = self.circuit_state.total_failures

        success_rate = 0.0
        if total_requests > 0:
            success_rate = (total_requests - total_failures) / total_requests

        # Calculate recent performance
        recent_cutoff = datetime.now(timezone.utc) - timedelta(minutes=10)
        recent_requests = [
            m for m in self.request_history if m.timestamp > recent_cutoff
        ]
        recent_success_rate = 0.0
        if recent_requests:
            recent_successes = sum(1 for m in recent_requests if m.success)
            recent_success_rate = recent_successes / len(recent_requests)

        return {
            "circuit_state": self.circuit_state.state.value,
            "total_requests": total_requests,
            "total_failures": total_failures,
            "success_rate": success_rate,
            "recent_success_rate": recent_success_rate,
            "failure_count": self.circuit_state.failure_count,
            "last_failure_time": (
                self.circuit_state.last_failure_time.isoformat()
                if self.circuit_state.last_failure_time
                else None
            ),
            "error_patterns": {k: len(v) for k, v in self.error_patterns.items()},
            "adaptive_delays": self.adaptive_delays,
        }


# Global retry manager instance
_retry_manager: AdaptiveRetryManager | None = None


def get_retry_manager(config: RetryConfig | None = None) -> AdaptiveRetryManager:
    """Get or create global retry manager."""
    global _retry_manager
    if _retry_manager is None:
        _retry_manager = AdaptiveRetryManager(config or RetryConfig())
    return _retry_manager


def with_enhanced_retry(config: RetryConfig | None = None, endpoint_name: str = ""):
    """
    Decorator for enhanced retry logic with circuit breaker pattern.

    Args:
        config: Retry configuration
        endpoint_name: Name of the endpoint for metrics

    Example:
        @with_enhanced_retry(config=RetryConfig(max_retries=3))
        async def my_api_call():
            return await some_api_call()
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            retry_manager = get_retry_manager(config)
            last_error = None
            start_time = time.time()

            for attempt in range(retry_manager.config.max_retries + 1):
                try:
                    # Check circuit breaker before attempt
                    if attempt > 0:
                        if not await retry_manager.should_retry(last_error, attempt):
                            logger.error(
                                f"Max retries exceeded or circuit breaker open for {func.__name__}"
                            )
                            raise last_error

                        # Wait before retry
                        delay = await retry_manager.get_retry_delay(last_error, attempt)
                        logger.info(
                            f"Retrying {func.__name__} in {delay:.2f}s (attempt {attempt + 1})"
                        )
                        await asyncio.sleep(delay)

                    # Execute function
                    result = await func(*args, **kwargs)

                    # Record success
                    duration = time.time() - start_time
                    await retry_manager.record_success(duration, endpoint_name)

                    if attempt > 0:
                        logger.info(
                            f"Function {func.__name__} succeeded after {attempt} retries"
                        )

                    return result

                except Exception as e:
                    last_error = e
                    logger.warning(
                        f"Attempt {attempt + 1} failed for {func.__name__}: {e!s}"
                    )

                    # Record failure internally
                    await retry_manager._record_failure(e)

                    # If this is the last attempt, raise the error
                    if attempt == retry_manager.config.max_retries:
                        logger.error(
                            f"All retry attempts exhausted for {func.__name__}"
                        )
                        raise e

            # This should never be reached, but just in case
            raise last_error

        return wrapper

    return decorator


async def test_retry_system():
    """Test the enhanced retry system."""
    print("🧪 Testing Enhanced Retry System")
    print("=" * 40)

    retry_manager = get_retry_manager()

    # Simulate various error scenarios
    @with_enhanced_retry(config=RetryConfig(max_retries=3, base_delay=0.1))
    async def failing_function(fail_count: int = 2):
        if hasattr(failing_function, "call_count"):
            failing_function.call_count += 1
        else:
            failing_function.call_count = 1

        if failing_function.call_count <= fail_count:
            msg = "Simulated rate limit error"
            raise RateLimitError(msg, response=None, body=None)

        return f"Success after {failing_function.call_count} attempts"

    try:
        # Test successful retry
        result = await failing_function(2)
        print(f"✅ {result}")

        # Test circuit breaker
        for _i in range(6):  # Trigger circuit breaker
            try:
                failing_function.call_count = 0  # Reset counter
                await failing_function(10)  # Will always fail
            except Exception:
                pass

        # Show health metrics
        metrics = retry_manager.get_health_metrics()
        print(f"📊 Circuit State: {metrics['circuit_state']}")
        print(f"📊 Success Rate: {metrics['success_rate']:.2%}")
        print(f"📊 Total Requests: {metrics['total_requests']}")

    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_retry_system())
