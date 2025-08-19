"""
Smart rate limiting systeem voor DefinitieAgent.

Implementeert token bucket algoritme, dynamische rate aanpassing, en prioriteit wachtrijen
voor efficiënte API rate limiting met intelligente load balancing.
"""

import asyncio  # Asynchrone programmering voor niet-blokkerende rate limiting
import contextlib
import json  # JSON verwerking voor configuratie opslag
import logging  # Logging faciliteiten voor debug en monitoring
import time  # Tijd functies voor token bucket timing
from collections import deque  # Efficiënte queue implementatie
from collections.abc import Callable
from dataclasses import (  # Dataklassen voor gestructureerde configuratie
    dataclass,
    field,
)
from datetime import (  # Datum en tijd functionaliteit voor timestamps, timezone
    datetime,
    timezone,
)
from enum import Enum  # Enumeraties voor prioriteit levels
from pathlib import Path  # Object-georiënteerde pad manipulatie
from typing import (  # Type hints voor betere code documentatie
    Any,
)

logger = logging.getLogger(__name__)  # Logger instantie voor smart rate limiter module


class RequestPriority(Enum):
    """Request prioriteit levels voor intelligente queue management."""

    CRITICAL = 0  # Gebruiker-gerichte operaties, directe respons vereist
    HIGH = 1  # Belangrijke operaties, lichte vertraging acceptabel
    NORMAL = 2  # Standaard operaties, normale prioriteit
    LOW = 3  # Achtergrond taken, kunnen wachten
    BACKGROUND = 4  # Cleanup, analytics, niet-urgente taken


@dataclass
class RateLimitConfig:
    """Configuration for smart rate limiting."""

    # Token bucket settings
    tokens_per_second: float = 1.0
    bucket_capacity: int = 10
    burst_capacity: int = 5

    # Dynamic adjustment settings
    target_response_time: float = 2.0  # Target API response time in seconds
    adjustment_factor: float = 0.1  # How aggressively to adjust rates
    min_rate: float = 0.1  # Minimum requests per second
    max_rate: float = 10.0  # Maximum requests per second

    # Priority queue settings
    priority_weights: dict[RequestPriority, float] = field(
        default_factory=lambda: {
            RequestPriority.CRITICAL: 1.0,
            RequestPriority.HIGH: 0.8,
            RequestPriority.NORMAL: 0.6,
            RequestPriority.LOW: 0.4,
            RequestPriority.BACKGROUND: 0.2,
        }
    )

    # Monitoring settings
    response_time_window: int = 100  # Number of recent requests to analyze
    adjustment_interval: float = 30.0  # How often to adjust rates (seconds)


@dataclass
class QueuedRequest:
    """Request waiting in priority queue."""

    priority: RequestPriority
    timestamp: datetime
    request_id: str
    future: asyncio.Future
    timeout: float | None = None


@dataclass
class ResponseMetrics:
    """Metrics for API response tracking."""

    timestamp: datetime
    response_time: float
    success: bool
    priority: RequestPriority
    queue_wait_time: float = 0.0


class TokenBucket:
    """Token bucket implementation for rate limiting."""

    def __init__(self, rate: float, capacity: int):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> bool:
        """Acquire tokens from the bucket."""
        async with self._lock:
            now = time.time()
            # Add tokens based on elapsed time
            elapsed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    async def wait_for_tokens(self, tokens: int = 1) -> float:
        """Calculate wait time for required tokens."""
        async with self._lock:
            now = time.time()
            elapsed = now - self.last_update
            current_tokens = min(self.capacity, self.tokens + elapsed * self.rate)

            if current_tokens >= tokens:
                return 0.0

            tokens_needed = tokens - current_tokens
            return tokens_needed / self.rate

    def update_rate(self, new_rate: float):
        """Update the token generation rate."""
        self.rate = max(0.1, min(10.0, new_rate))  # Bounds check
        logger.debug(f"Token bucket rate updated to {self.rate:.2f} tokens/sec")


class SmartRateLimiter:
    """Smart rate limiter with dynamic adjustment and priority queuing."""

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.token_bucket = TokenBucket(
            config.tokens_per_second, config.bucket_capacity
        )

        # Priority queues for different request types
        self.priority_queues: dict[RequestPriority, deque] = {
            priority: deque() for priority in RequestPriority
        }

        # Response time tracking
        self.response_metrics: deque = deque(maxlen=config.response_time_window)

        # Dynamic adjustment state
        self.last_adjustment = time.time()
        self.current_rate = config.tokens_per_second

        # Log de configuratie voor debugging
        logger.debug(
            f"Initialized SmartRateLimiter with rate: {config.tokens_per_second} req/s, capacity: {config.bucket_capacity}"
        )

        # Statistics
        self.stats = {
            "total_requests": 0,
            "total_queued": 0,
            "total_dropped": 0,
            "avg_response_time": 0.0,
            "avg_queue_time": 0.0,
            "rate_adjustments": 0,
        }

        # Background task for processing queues
        self._processing_task = None
        self._shutdown = False

        # Load historical data
        self._load_historical_data()

    def _load_historical_data(self):
        """Load historical rate limiting data."""
        try:
            history_file = Path("cache/rate_limit_history.json")
            if history_file.exists():
                with open(history_file) as f:
                    data = json.load(f)
                    self.current_rate = data.get(
                        "optimal_rate", self.config.tokens_per_second
                    )
                    self.token_bucket.update_rate(self.current_rate)
                    logger.info(f"Loaded optimal rate: {self.current_rate:.2f} req/sec")
        except Exception as e:
            logger.warning(f"Could not load rate limit history: {e}")

    def _save_historical_data(self):
        """Save historical data for future optimization."""
        try:
            history_file = Path("cache/rate_limit_history.json")
            history_file.parent.mkdir(exist_ok=True)

            data = {
                "optimal_rate": self.current_rate,
                "avg_response_time": self.stats["avg_response_time"],
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "stats": self.stats,
            }

            with open(history_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save rate limit history: {e}")

    async def start(self):
        """Start the background processing task."""
        if self._processing_task is None:
            self._processing_task = asyncio.create_task(self._process_queues())
            logger.info("Smart rate limiter started")

    async def stop(self):
        """Stop the background processing task."""
        self._shutdown = True
        if self._processing_task:
            self._processing_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._processing_task
        self._save_historical_data()
        logger.info("Smart rate limiter stopped")

    async def acquire(
        self,
        priority: RequestPriority = RequestPriority.NORMAL,
        timeout: float | None = None,
        request_id: str | None = None,
    ) -> bool:
        """
        Acquire rate limit permission for a request.

        Args:
            priority: Request priority level
            timeout: Maximum time to wait for permission
            request_id: Unique identifier for the request

        Returns:
            True if permission granted, False if timeout/dropped
        """
        if request_id is None:
            request_id = f"req_{int(time.time() * 1000)}"

        self.stats["total_requests"] += 1

        # Try immediate acquisition for high priority requests
        if priority in [RequestPriority.CRITICAL, RequestPriority.HIGH]:
            if await self.token_bucket.acquire():
                return True

        # Queue the request
        future = asyncio.Future()
        queued_request = QueuedRequest(
            priority=priority,
            timestamp=datetime.now(timezone.utc),
            request_id=request_id,
            future=future,
            timeout=timeout,
        )

        self.priority_queues[priority].append(queued_request)
        self.stats["total_queued"] += 1

        try:
            # Wait for processing or timeout
            if timeout:
                result = await asyncio.wait_for(future, timeout=timeout)
            else:
                result = await future
            return result
        except asyncio.TimeoutError:
            # Remove from queue if still there
            try:
                self.priority_queues[priority].remove(queued_request)
            except ValueError:
                pass  # Already processed
            self.stats["total_dropped"] += 1
            return False

    async def _process_queues(self):
        """Background task to process priority queues."""
        while not self._shutdown:
            try:
                # Process requests in priority order
                for priority in RequestPriority:
                    queue = self.priority_queues[priority]

                    while queue and await self.token_bucket.acquire():
                        request = queue.popleft()

                        # Check if request hasn't timed out
                        if not request.future.done():
                            queue_wait_time = (
                                datetime.now(timezone.utc) - request.timestamp
                            ).total_seconds()

                            # Apply priority weighting to queue time
                            weight = self.config.priority_weights[priority]
                            if (
                                queue_wait_time * weight < 30.0
                            ):  # Max weighted wait time
                                request.future.set_result(True)

                                # Update queue time statistics
                                self._update_queue_stats(queue_wait_time)
                            else:
                                # Timeout due to priority weighting
                                request.future.set_result(False)
                                self.stats["total_dropped"] += 1

                    # Don't process all priorities in one cycle if tokens are limited
                    if not await self.token_bucket.acquire():
                        break

                # Dynamic rate adjustment
                await self._adjust_rate_if_needed()

                # Small delay to prevent busy waiting
                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Error in queue processing: {e}")
                await asyncio.sleep(1.0)

    def _update_queue_stats(self, queue_wait_time: float):
        """Update queue time statistics."""
        if self.stats["avg_queue_time"] == 0:
            self.stats["avg_queue_time"] = queue_wait_time
        else:
            # Exponential moving average
            alpha = 0.1
            self.stats["avg_queue_time"] = (
                alpha * queue_wait_time + (1 - alpha) * self.stats["avg_queue_time"]
            )

    async def record_response(
        self,
        response_time: float,
        success: bool,
        priority: RequestPriority = RequestPriority.NORMAL,
    ):
        """Record response metrics for dynamic rate adjustment."""
        metric = ResponseMetrics(
            timestamp=datetime.now(timezone.utc),
            response_time=response_time,
            success=success,
            priority=priority,
        )
        self.response_metrics.append(metric)

        # Update average response time
        if self.stats["avg_response_time"] == 0:
            self.stats["avg_response_time"] = response_time
        else:
            # Exponential moving average
            alpha = 0.1
            self.stats["avg_response_time"] = (
                alpha * response_time + (1 - alpha) * self.stats["avg_response_time"]
            )

    async def _adjust_rate_if_needed(self):
        """Dynamically adjust rate based on API performance."""
        now = time.time()
        if now - self.last_adjustment < self.config.adjustment_interval:
            return

        if len(self.response_metrics) < 10:  # Need minimum data
            return

        # Calculate recent average response time
        recent_metrics = list(self.response_metrics)[-20:]  # Last 20 requests
        successful_metrics = [m for m in recent_metrics if m.success]

        if not successful_metrics:
            return

        avg_response_time = sum(m.response_time for m in successful_metrics) / len(
            successful_metrics
        )
        target_time = self.config.target_response_time

        # Adjust rate based on response time
        if avg_response_time > target_time * 1.2:  # Too slow, reduce rate
            adjustment = -self.config.adjustment_factor
        elif avg_response_time < target_time * 0.8:  # Fast enough, increase rate
            adjustment = self.config.adjustment_factor
        else:
            adjustment = 0  # In acceptable range

        if adjustment != 0:
            old_rate = self.current_rate
            self.current_rate = max(
                self.config.min_rate,
                min(self.config.max_rate, self.current_rate * (1 + adjustment)),
            )

            if abs(self.current_rate - old_rate) > 0.01:  # Significant change
                self.token_bucket.update_rate(self.current_rate)
                self.stats["rate_adjustments"] += 1

                logger.info(
                    f"Rate adjusted: {old_rate:.2f} → {self.current_rate:.2f} req/sec "
                    f"(avg response: {avg_response_time:.2f}s, target: {target_time:.2f}s)"
                )

        self.last_adjustment = now

    def get_queue_status(self) -> dict[str, Any]:
        """Get current queue status and statistics."""
        queue_lengths = {
            priority.name: len(queue)
            for priority, queue in self.priority_queues.items()
        }

        return {
            "current_rate": self.current_rate,
            "token_bucket_tokens": self.token_bucket.tokens,
            "queue_lengths": queue_lengths,
            "total_queued": sum(queue_lengths.values()),
            "stats": self.stats.copy(),
            "recent_response_time": self.stats["avg_response_time"],
            "recent_queue_time": self.stats["avg_queue_time"],
        }

    async def get_estimated_wait_time(self, priority: RequestPriority) -> float:
        """Estimate wait time for a request of given priority."""
        # Count requests ahead in higher/equal priority queues
        requests_ahead = 0
        for p in RequestPriority:
            if p.value <= priority.value:
                requests_ahead += len(self.priority_queues[p])
            if p == priority:
                break

        # Estimate based on current rate
        base_wait = requests_ahead / self.current_rate

        # Apply priority weighting
        weight = self.config.priority_weights[priority]
        return base_wait / weight


# Endpoint-specifieke smart rate limiters
_smart_limiters: dict[str, SmartRateLimiter] = {}


async def get_smart_limiter(
    endpoint_name: str = "default", config: RateLimitConfig | None = None
) -> SmartRateLimiter:
    """Get or create endpoint-specific smart rate limiter.

    Args:
        endpoint_name: Naam van de endpoint voor endpoint-specifieke rate limiting
        config: Optionele configuratie voor de rate limiter

    Returns:
        SmartRateLimiter instance voor de specifieke endpoint
    """
    global _smart_limiters

    # Gebruik endpoint naam als key voor specifieke rate limiter
    if endpoint_name not in _smart_limiters:
        # Probeer endpoint-specifieke configuratie te laden
        if config is None:
            try:
                from config.rate_limit_config import get_rate_limit_config

                config = get_rate_limit_config(endpoint_name)
                logger.info(f"Loaded specific config for endpoint: {endpoint_name}")
            except ImportError:
                # Gebruik default configuratie als config module niet bestaat
                config = RateLimitConfig()
                logger.debug(f"Using default config for endpoint: {endpoint_name}")

        # Maak nieuwe rate limiter voor deze endpoint
        _smart_limiters[endpoint_name] = SmartRateLimiter(config)
        await _smart_limiters[endpoint_name].start()
        logger.info(f"Created new rate limiter for endpoint: {endpoint_name}")

    return _smart_limiters[endpoint_name]


def with_smart_rate_limit(
    endpoint_name: str = "",
    priority: RequestPriority = RequestPriority.NORMAL,
    timeout: float | None = None,
):
    """
    Decorator for smart rate limiting with priority queuing.

    Args:
        endpoint_name: Endpoint naam voor specifieke rate limiting
        priority: Request priority level
        timeout: Maximum time to wait for rate limit permission

    Example:
        @with_smart_rate_limit(endpoint_name="gpt_api", priority=RequestPriority.HIGH, timeout=10.0)
        async def important_api_call():
            return await some_api_call()
    """

    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            # Gebruik endpoint naam of functie naam voor endpoint-specifieke limiter
            actual_endpoint = endpoint_name or func.__name__
            limiter = await get_smart_limiter(actual_endpoint)
            request_id = f"{actual_endpoint}_{int(time.time() * 1000)}"

            # Wait for rate limit permission
            time.time()
            if not await limiter.acquire(priority, timeout, request_id):
                msg = f"Rate limit timeout for {func.__name__}"
                raise asyncio.TimeoutError(msg)

            try:
                # Execute function and record metrics
                function_start = time.time()
                result = await func(*args, **kwargs)
                response_time = time.time() - function_start

                await limiter.record_response(response_time, True, priority)
                return result

            except Exception:
                response_time = time.time() - function_start
                await limiter.record_response(response_time, False, priority)
                raise

        return wrapper

    return decorator


async def test_smart_rate_limiter():
    """Test the smart rate limiting system."""
    print("🧪 Testing Smart Rate Limiter")
    print("=" * 40)

    config = RateLimitConfig(
        tokens_per_second=2.0, bucket_capacity=5, target_response_time=1.0
    )

    limiter = SmartRateLimiter(config)
    await limiter.start()

    try:
        # Test different priority requests
        async def simulate_request(priority: RequestPriority, delay: float = 0.5):
            @with_smart_rate_limit(priority=priority)
            async def mock_api_call():
                await asyncio.sleep(delay)  # Simulate API call
                return f"Response for {priority.name} request"

            return await mock_api_call()

        # Submit various priority requests
        tasks = []
        for i in range(10):
            if i < 2:
                priority = RequestPriority.CRITICAL
            elif i < 5:
                priority = RequestPriority.HIGH
            else:
                priority = RequestPriority.NORMAL

            task = simulate_request(priority, delay=0.2 + i * 0.1)
            tasks.append(task)

        # Execute all requests
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time

        # Show results
        successful = sum(1 for r in results if not isinstance(r, Exception))
        print(f"✅ Completed {successful}/{len(tasks)} requests in {total_time:.2f}s")

        # Show queue status
        status = limiter.get_queue_status()
        print(f"📊 Current rate: {status['current_rate']:.2f} req/sec")
        print(f"📊 Total requests: {status['stats']['total_requests']}")
        print(f"📊 Average response time: {status['stats']['avg_response_time']:.2f}s")

    finally:
        await limiter.stop()


async def cleanup_smart_limiters():
    """Clean up all endpoint-specific rate limiters."""
    global _smart_limiters
    for endpoint_name, limiter in _smart_limiters.items():
        await limiter.stop()
        logger.info(f"Stopped rate limiter for endpoint: {endpoint_name}")
    _smart_limiters.clear()


if __name__ == "__main__":
    asyncio.run(test_smart_rate_limiter())
