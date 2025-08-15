"""
Resilience framework for DefinitieAgent.
Provides health monitoring, failover strategies, and request queue persistence.
"""

import asyncio
import json
import logging
import pickle
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from utils.enhanced_retry import AdaptiveRetryManager
from utils.smart_rate_limiter import RequestPriority, SmartRateLimiter

logger = logging.getLogger(__name__)


class ServiceHealth(Enum):
    """Service health status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    DOWN = "down"


class FailoverStrategy(Enum):
    """Failover strategy types."""

    CIRCUIT_BREAKER = "circuit_breaker"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    QUEUE_AND_RETRY = "queue_and_retry"
    FALLBACK_SERVICE = "fallback_service"


@dataclass
class HealthMetrics:
    """Health metrics for a service endpoint."""

    endpoint_name: str
    status: ServiceHealth
    last_check: datetime
    response_time: float
    success_rate: float
    error_count: int
    consecutive_failures: int
    total_requests: int
    availability: float


@dataclass
class FailedRequest:
    """Failed request stored for retry."""

    request_id: str
    function_name: str
    args: tuple
    kwargs: dict
    priority: RequestPriority
    timestamp: datetime
    retry_count: int = 0
    max_retries: int = 5
    last_error: Optional[str] = None


@dataclass
class ResilienceConfig:
    """Configuration for resilience framework."""

    # Health check settings
    health_check_interval: float = 30.0
    health_check_timeout: float = 5.0
    degraded_threshold: float = 0.8  # Success rate threshold for degraded status
    unhealthy_threshold: float = 0.5  # Success rate threshold for unhealthy status

    # Queue persistence settings
    persist_failed_requests: bool = True
    max_queue_size: int = 1000
    queue_persist_interval: float = 60.0

    # Failover settings
    enable_graceful_degradation: bool = True
    degraded_mode_timeout: float = 300.0  # 5 minutes
    fallback_cache_duration: float = 3600.0  # 1 hour

    # Recovery settings
    recovery_test_requests: int = 3
    recovery_success_threshold: float = 0.8


class DeadLetterQueue:
    """Queue for failed requests that couldn't be processed."""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.queue: List[FailedRequest] = []
        self._lock = asyncio.Lock()
        self.stats = {
            "total_added": 0,
            "total_removed": 0,
            "total_processed": 0,
            "total_expired": 0,
        }

    async def add(self, failed_request: FailedRequest):
        """Add a failed request to the dead letter queue."""
        async with self._lock:
            if len(self.queue) >= self.max_size:
                # Remove oldest item
                expired = self.queue.pop(0)
                self.stats["total_expired"] += 1
                logger.warning(
                    f"Expired request from dead letter queue: {expired.request_id}"
                )

            self.queue.append(failed_request)
            self.stats["total_added"] += 1
            logger.debug(
                f"Added request to dead letter queue: {failed_request.request_id}"
            )

    async def get_retryable_requests(self) -> List[FailedRequest]:
        """Get requests that can be retried."""
        async with self._lock:
            now = datetime.now()
            retryable = []

            for req in self.queue[
                :
            ]:  # Copy list to avoid modification during iteration
                # Check if request should be retried
                time_since_failure = (now - req.timestamp).total_seconds()
                min_wait_time = min(
                    300, 2**req.retry_count
                )  # Exponential backoff, max 5 min

                if (
                    req.retry_count < req.max_retries
                    and time_since_failure >= min_wait_time
                ):
                    retryable.append(req)

            return retryable

    async def remove(self, request_id: str, processed: bool = True):
        """Remove a request from the queue."""
        async with self._lock:
            self.queue = [req for req in self.queue if req.request_id != request_id]
            if processed:
                self.stats["total_processed"] += 1
            self.stats["total_removed"] += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        return {
            "queue_size": len(self.queue),
            "max_size": self.max_size,
            "stats": self.stats.copy(),
        }


class HealthMonitor:
    """Monitors health of API endpoints and services."""

    def __init__(self, config: ResilienceConfig):
        self.config = config
        self.endpoints: Dict[str, HealthMetrics] = {}
        self.health_history: Dict[str, List[Tuple[datetime, ServiceHealth]]] = {}
        self._monitoring_task: Optional[asyncio.Task] = None
        self._shutdown = False

    async def start_monitoring(self):
        """Start health monitoring background task."""
        if self._monitoring_task is None:
            self._monitoring_task = asyncio.create_task(self._monitor_health())
            logger.info("Health monitoring started")

    async def stop_monitoring(self):
        """Stop health monitoring."""
        self._shutdown = True
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Health monitoring stopped")

    async def register_endpoint(
        self, name: str, health_check_func: Optional[Callable] = None
    ):
        """Register an endpoint for health monitoring."""
        self.endpoints[name] = HealthMetrics(
            endpoint_name=name,
            status=ServiceHealth.HEALTHY,
            last_check=datetime.now(),
            response_time=0.0,
            success_rate=1.0,
            error_count=0,
            consecutive_failures=0,
            total_requests=0,
            availability=1.0,
        )
        self.health_history[name] = []
        logger.info(f"Registered endpoint for monitoring: {name}")

    async def record_request(self, endpoint: str, success: bool, response_time: float):
        """Record a request result for health metrics."""
        if endpoint not in self.endpoints:
            await self.register_endpoint(endpoint)

        metrics = self.endpoints[endpoint]
        metrics.total_requests += 1
        metrics.last_check = datetime.now()

        # Update response time (exponential moving average)
        alpha = 0.1
        metrics.response_time = (
            alpha * response_time + (1 - alpha) * metrics.response_time
        )

        if success:
            metrics.consecutive_failures = 0
            # Update success rate
            metrics.success_rate = (
                metrics.success_rate * (metrics.total_requests - 1) + 1.0
            ) / metrics.total_requests
        else:
            metrics.error_count += 1
            metrics.consecutive_failures += 1
            # Update success rate
            metrics.success_rate = (
                metrics.success_rate * (metrics.total_requests - 1) + 0.0
            ) / metrics.total_requests

        # Update health status
        await self._update_health_status(endpoint)

    async def _update_health_status(self, endpoint: str):
        """Update health status based on metrics."""
        metrics = self.endpoints[endpoint]
        old_status = metrics.status

        # Determine new status based on success rate and consecutive failures
        if (
            metrics.consecutive_failures >= 5
            or metrics.success_rate < self.config.unhealthy_threshold
        ):
            new_status = ServiceHealth.UNHEALTHY
        elif (
            metrics.consecutive_failures >= 3
            or metrics.success_rate < self.config.degraded_threshold
        ):
            new_status = ServiceHealth.DEGRADED
        else:
            new_status = ServiceHealth.HEALTHY

        # Check response time for degraded status
        if new_status == ServiceHealth.HEALTHY and metrics.response_time > 10.0:
            new_status = ServiceHealth.DEGRADED

        metrics.status = new_status

        # Record status change
        if old_status != new_status:
            self.health_history[endpoint].append((datetime.now(), new_status))
            logger.warning(
                f"Health status changed for {endpoint}: {old_status.value} → {new_status.value}"
            )

    async def _monitor_health(self):
        """Background task for periodic health monitoring."""
        while not self._shutdown:
            try:
                # Update availability metrics
                for endpoint, metrics in self.endpoints.items():
                    # Calculate availability over last hour
                    now = datetime.now()
                    hour_ago = now - timedelta(hours=1)

                    recent_history = [
                        (timestamp, status)
                        for timestamp, status in self.health_history[endpoint]
                        if timestamp > hour_ago
                    ]

                    if recent_history:
                        healthy_time = 0
                        total_time = 3600  # 1 hour in seconds

                        for i, (timestamp, status) in enumerate(recent_history):
                            if status in [
                                ServiceHealth.HEALTHY,
                                ServiceHealth.DEGRADED,
                            ]:
                                if i < len(recent_history) - 1:
                                    next_timestamp = recent_history[i + 1][0]
                                    healthy_time += (
                                        next_timestamp - timestamp
                                    ).total_seconds()
                                else:
                                    healthy_time += (now - timestamp).total_seconds()

                        metrics.availability = healthy_time / total_time

                    # Cleanup old history (keep last 24 hours)
                    day_ago = now - timedelta(hours=24)
                    self.health_history[endpoint] = [
                        (timestamp, status)
                        for timestamp, status in self.health_history[endpoint]
                        if timestamp > day_ago
                    ]

                await asyncio.sleep(self.config.health_check_interval)

            except Exception as e:
                logger.error(f"Error in health monitoring: {e}")
                await asyncio.sleep(5.0)

    def get_health_status(self, endpoint: Optional[str] = None) -> Dict[str, Any]:
        """Get current health status."""
        if endpoint:
            if endpoint in self.endpoints:
                return asdict(self.endpoints[endpoint])
            return {}

        return {name: asdict(metrics) for name, metrics in self.endpoints.items()}


class ResilienceFramework:
    """Main resilience framework coordinating all components."""

    def __init__(self, config: Optional[ResilienceConfig] = None):
        self.config = config or ResilienceConfig()
        self.health_monitor = HealthMonitor(self.config)
        self.dead_letter_queue = DeadLetterQueue(self.config.max_queue_size)
        self.retry_manager: Optional[AdaptiveRetryManager] = None
        self.rate_limiter: Optional[SmartRateLimiter] = None

        # Cached responses for graceful degradation
        self.fallback_cache: Dict[str, Tuple[Any, datetime]] = {}

        # Background tasks
        self._queue_processor_task: Optional[asyncio.Task] = None
        self._cache_cleanup_task: Optional[asyncio.Task] = None
        self._shutdown = False

        # Load persistent state
        self._load_persistent_state()

    def _load_persistent_state(self):
        """Load persistent state from disk."""
        try:
            state_file = Path("cache/resilience_state.pkl")
            if state_file.exists():
                with open(state_file, "rb") as f:
                    state = pickle.load(f)
                    self.dead_letter_queue.queue = state.get("dead_letter_queue", [])
                    self.fallback_cache = state.get("fallback_cache", {})
                    logger.info("Loaded persistent resilience state")
        except Exception as e:
            logger.warning(f"Could not load persistent state: {e}")

    def _save_persistent_state(self):
        """Save persistent state to disk."""
        try:
            state_file = Path("cache/resilience_state.pkl")
            state_file.parent.mkdir(exist_ok=True)

            state = {
                "dead_letter_queue": self.dead_letter_queue.queue,
                "fallback_cache": self.fallback_cache,
                "timestamp": datetime.now(),
            }

            with open(state_file, "wb") as f:
                pickle.dump(state, f)
        except Exception as e:
            logger.warning(f"Could not save persistent state: {e}")

    async def start(self):
        """Start the resilience framework."""
        await self.health_monitor.start_monitoring()

        # Start background tasks
        self._queue_processor_task = asyncio.create_task(
            self._process_dead_letter_queue()
        )
        self._cache_cleanup_task = asyncio.create_task(self._cleanup_fallback_cache())

        logger.info("Resilience framework started")

    async def stop(self):
        """Stop the resilience framework."""
        self._shutdown = True

        await self.health_monitor.stop_monitoring()

        # Cancel background tasks
        for task in [self._queue_processor_task, self._cache_cleanup_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Save persistent state
        self._save_persistent_state()

        logger.info("Resilience framework stopped")

    async def execute_with_resilience(
        self,
        func: Callable,
        *args,
        endpoint_name: str = "",
        priority: RequestPriority = RequestPriority.NORMAL,
        enable_fallback: bool = True,
        **kwargs,
    ) -> Any:
        """
        Execute a function with full resilience support.

        Args:
            func: Function to execute
            *args: Function arguments
            endpoint_name: Name of the endpoint for monitoring
            priority: Request priority
            enable_fallback: Whether to use fallback cache
            **kwargs: Function keyword arguments

        Returns:
            Function result or fallback value
        """
        if not endpoint_name:
            endpoint_name = func.__name__

        request_id = f"{endpoint_name}_{int(time.time() * 1000)}"
        start_time = time.time()

        try:
            # Check health status
            health_status = self.health_monitor.get_health_status(endpoint_name)
            if (
                health_status
                and health_status.get("status") == ServiceHealth.DOWN.value
            ):
                if enable_fallback:
                    fallback_result = await self._get_fallback_response(
                        func, args, kwargs
                    )
                    if fallback_result is not None:
                        logger.info(f"Using fallback response for {endpoint_name}")
                        return fallback_result

                raise Exception(
                    f"Service {endpoint_name} is down and no fallback available"
                )

            # Execute function
            result = await func(*args, **kwargs)

            # Record success
            response_time = time.time() - start_time
            await self.health_monitor.record_request(endpoint_name, True, response_time)

            # Cache successful response for fallback
            if enable_fallback:
                await self._cache_fallback_response(func, args, kwargs, result)

            return result

        except Exception as e:
            # Record failure
            response_time = time.time() - start_time
            await self.health_monitor.record_request(
                endpoint_name, False, response_time
            )

            # Add to dead letter queue for retry
            if self.config.persist_failed_requests:
                failed_request = FailedRequest(
                    request_id=request_id,
                    function_name=func.__name__,
                    args=args,
                    kwargs=kwargs,
                    priority=priority,
                    timestamp=datetime.now(),
                    last_error=str(e),
                )
                await self.dead_letter_queue.add(failed_request)

            # Try fallback
            if enable_fallback:
                fallback_result = await self._get_fallback_response(func, args, kwargs)
                if fallback_result is not None:
                    logger.warning(
                        f"Using fallback response for {endpoint_name} after error: {e}"
                    )
                    return fallback_result

            # Re-raise original exception
            raise

    async def _get_fallback_response(
        self, func: Callable, args: tuple, kwargs: dict
    ) -> Optional[Any]:
        """Get fallback response from cache."""
        cache_key = self._generate_cache_key(func, args, kwargs)

        if cache_key in self.fallback_cache:
            cached_result, timestamp = self.fallback_cache[cache_key]

            # Check if cache is still valid
            age = (datetime.now() - timestamp).total_seconds()
            if age < self.config.fallback_cache_duration:
                return cached_result
            else:
                # Remove expired cache entry
                del self.fallback_cache[cache_key]

        return None

    async def _cache_fallback_response(
        self, func: Callable, args: tuple, kwargs: dict, result: Any
    ):
        """Cache successful response for fallback."""
        cache_key = self._generate_cache_key(func, args, kwargs)
        self.fallback_cache[cache_key] = (result, datetime.now())

    def _generate_cache_key(self, func: Callable, args: tuple, kwargs: dict) -> str:
        """Generate cache key for function call."""
        key_data = {
            "function": func.__name__,
            "args": str(args),
            "kwargs": str(sorted(kwargs.items())),
        }
        return json.dumps(key_data, sort_keys=True)

    async def _process_dead_letter_queue(self):
        """Background task to process failed requests."""
        while not self._shutdown:
            try:
                retryable_requests = (
                    await self.dead_letter_queue.get_retryable_requests()
                )

                for request in retryable_requests:
                    try:
                        # Attempt to retry the request
                        # Note: In a real implementation, you would need a registry
                        # of functions to call by name
                        logger.info(
                            f"Retrying request: {request.request_id} (attempt {request.retry_count + 1})"
                        )

                        # Increment retry count
                        request.retry_count += 1

                        # If max retries exceeded, remove from queue
                        if request.retry_count >= request.max_retries:
                            await self.dead_letter_queue.remove(
                                request.request_id, processed=False
                            )
                            logger.error(
                                f"Max retries exceeded for request: {request.request_id}"
                            )

                    except Exception as e:
                        logger.error(
                            f"Error retrying request {request.request_id}: {e}"
                        )

                # Save state periodically
                if len(retryable_requests) > 0:
                    self._save_persistent_state()

                await asyncio.sleep(self.config.queue_persist_interval)

            except Exception as e:
                logger.error(f"Error in dead letter queue processing: {e}")
                await asyncio.sleep(5.0)

    async def _cleanup_fallback_cache(self):
        """Background task to cleanup expired fallback cache entries."""
        while not self._shutdown:
            try:
                now = datetime.now()
                expired_keys = []

                for key, (_, timestamp) in self.fallback_cache.items():
                    age = (now - timestamp).total_seconds()
                    if age > self.config.fallback_cache_duration:
                        expired_keys.append(key)

                for key in expired_keys:
                    del self.fallback_cache[key]

                if expired_keys:
                    logger.debug(
                        f"Cleaned up {len(expired_keys)} expired fallback cache entries"
                    )

                await asyncio.sleep(300)  # Cleanup every 5 minutes

            except Exception as e:
                logger.error(f"Error in fallback cache cleanup: {e}")
                await asyncio.sleep(60.0)

    def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health information."""
        return {
            "health_monitor": self.health_monitor.get_health_status(),
            "dead_letter_queue": self.dead_letter_queue.get_stats(),
            "fallback_cache": {
                "size": len(self.fallback_cache),
                "entries": list(self.fallback_cache.keys())[:10],  # Sample of keys
            },
            "config": asdict(self.config),
        }


# Global resilience framework instance
_resilience_framework: Optional[ResilienceFramework] = None


async def get_resilience_framework(
    config: Optional[ResilienceConfig] = None,
) -> ResilienceFramework:
    """Get or create global resilience framework."""
    global _resilience_framework
    if _resilience_framework is None:
        _resilience_framework = ResilienceFramework(config)
        await _resilience_framework.start()
    return _resilience_framework


def with_resilience(
    endpoint_name: str = "",
    priority: RequestPriority = RequestPriority.NORMAL,
    enable_fallback: bool = True,
):
    """
    Decorator for resilient function execution.

    Args:
        endpoint_name: Name of the endpoint for monitoring
        priority: Request priority
        enable_fallback: Whether to use fallback cache

    Example:
        @with_resilience(endpoint_name="gpt_api", priority=RequestPriority.HIGH)
        async def call_gpt_api():
            return await some_gpt_call()
    """

    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            framework = await get_resilience_framework()
            return await framework.execute_with_resilience(
                func,
                *args,
                endpoint_name=endpoint_name or func.__name__,
                priority=priority,
                enable_fallback=enable_fallback,
                **kwargs,
            )

        return wrapper

    return decorator


async def test_resilience_framework():
    """Test the resilience framework."""
    print("🧪 Testing Resilience Framework")
    print("=" * 40)

    framework = ResilienceFramework()
    await framework.start()

    try:
        # Test function with failures
        call_count = 0

        @with_resilience(endpoint_name="test_api", enable_fallback=True)
        async def test_function(should_fail: bool = False):
            nonlocal call_count
            call_count += 1

            if should_fail and call_count <= 3:
                raise Exception(f"Simulated failure #{call_count}")

            return f"Success on call #{call_count}"

        # Test successful execution
        result = await test_function(should_fail=False)
        print(f"✅ {result}")

        # Test with failures (should use fallback)
        call_count = 0
        try:
            result = await test_function(should_fail=True)
            print(f"✅ Fallback: {result}")
        except Exception as e:
            print(f"❌ Failed: {e}")

        # Show system health
        health = framework.get_system_health()
        print("📊 System Health:")
        for endpoint, metrics in health["health_monitor"].items():
            print(f"  {endpoint}: {metrics.get('status', 'unknown')}")

        print(
            f"📊 Dead Letter Queue: {health['dead_letter_queue']['queue_size']} items"
        )
        print(f"📊 Fallback Cache: {health['fallback_cache']['size']} entries")

    finally:
        await framework.stop()


if __name__ == "__main__":
    asyncio.run(test_resilience_framework())
