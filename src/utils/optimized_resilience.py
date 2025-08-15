"""
Optimized resilience system for DefinitieAgent.
Consolidates resilience.py, integrated_resilience.py, and resilience_summary.py.
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

from monitoring.api_monitor import get_metrics_collector, record_api_call

# Import existing components
from utils.enhanced_retry import AdaptiveRetryManager, RetryConfig
from utils.smart_rate_limiter import RateLimitConfig, RequestPriority, SmartRateLimiter

logger = logging.getLogger(__name__)


class ResilienceMode(Enum):
    """Resilience operation modes."""

    BASIC = "basic"  # Basic error handling
    ENHANCED = "enhanced"  # With retry logic
    SMART = "smart"  # With rate limiting
    FULL = "full"  # Complete resilience
    CRITICAL = "critical"  # Maximum protection


class HealthStatus(Enum):
    """Health status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    DOWN = "down"


@dataclass
class ResilienceConfig:
    """Unified configuration for resilience system."""

    # Retry configuration
    retry_config: Optional[RetryConfig] = None

    # Rate limiting configuration
    rate_limit_config: Optional[RateLimitConfig] = None

    # Health monitoring
    health_check_interval: float = 30.0
    degraded_threshold: float = 0.8
    unhealthy_threshold: float = 0.5

    # Fallback settings
    enable_fallback: bool = True
    fallback_cache_duration: float = 300.0

    # Monitoring
    enable_monitoring: bool = True
    enable_cost_tracking: bool = True

    # Graceful degradation
    enable_graceful_degradation: bool = True
    persist_failed_requests: bool = True

    def __post_init__(self):
        """Initialize default configurations."""
        if self.retry_config is None:
            self.retry_config = RetryConfig(
                max_retries=3,
                base_delay=1.0,
                max_delay=30.0,
                strategy="adaptive",
                failure_threshold=3,
                recovery_timeout=30.0,
            )

        if self.rate_limit_config is None:
            self.rate_limit_config = RateLimitConfig(
                tokens_per_second=2.0,
                bucket_capacity=10,
                burst_capacity=5,
                target_response_time=2.0,
                adjustment_factor=0.1,
            )


@dataclass
class HealthMetrics:
    """Health metrics for an endpoint."""

    endpoint_name: str
    status: HealthStatus
    success_rate: float
    avg_response_time: float
    total_requests: int
    failed_requests: int
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    consecutive_failures: int = 0


class OptimizedResilienceSystem:
    """Optimized resilience system combining all resilience features."""

    def __init__(self, config: Optional[ResilienceConfig] = None):
        self.config = config or ResilienceConfig()

        # Initialize components
        self.retry_manager = AdaptiveRetryManager(self.config.retry_config)
        self.rate_limiter = SmartRateLimiter(self.config.rate_limit_config)
        self.metrics_collector = (
            get_metrics_collector() if self.config.enable_monitoring else None
        )

        # Health monitoring
        self.health_metrics: Dict[str, HealthMetrics] = {}
        self.fallback_cache: Dict[str, Any] = {}
        self.failed_requests: List[Dict[str, Any]] = []

        # System state
        self._started = False
        self._shutdown = False
        self._health_check_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the resilience system."""
        if self._started:
            return

        await self.rate_limiter.start()

        # Start health monitoring
        if self.config.health_check_interval > 0:
            self._health_check_task = asyncio.create_task(self._health_check_loop())

        self._started = True
        logger.info("🚀 Optimized resilience system started")

    async def stop(self):
        """Stop the resilience system."""
        if not self._started:
            return

        self._shutdown = True

        # Stop components
        await self.rate_limiter.stop()

        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        # Save retry manager history
        self.retry_manager._save_historical_data()

        logger.info("⏹️ Optimized resilience system stopped")

    async def execute_with_resilience(
        self,
        func: Callable,
        *args,
        endpoint_name: str = "",
        priority: RequestPriority = RequestPriority.NORMAL,
        timeout: Optional[float] = None,
        mode: ResilienceMode = ResilienceMode.FULL,
        model: str = "gpt-4",
        expected_tokens: int = 0,
        **kwargs,
    ) -> Any:
        """
        Execute function with configurable resilience.

        Args:
            func: Function to execute
            *args: Function arguments
            endpoint_name: Name of the endpoint for monitoring
            priority: Request priority
            timeout: Request timeout
            mode: Resilience mode to use
            model: AI model being used
            expected_tokens: Expected token usage
            **kwargs: Function keyword arguments

        Returns:
            Function result
        """
        if not endpoint_name:
            endpoint_name = func.__name__

        start_time = time.time()
        f"{endpoint_name}_{int(time.time() * 1000)}"

        try:
            # Execute based on resilience mode
            if mode == ResilienceMode.BASIC:
                result = await self._execute_basic(func, *args, **kwargs)
            elif mode == ResilienceMode.ENHANCED:
                result = await self._execute_enhanced(
                    func, *args, endpoint_name=endpoint_name, **kwargs
                )
            elif mode == ResilienceMode.SMART:
                result = await self._execute_smart(
                    func,
                    *args,
                    endpoint_name=endpoint_name,
                    priority=priority,
                    timeout=timeout,
                    **kwargs,
                )
            elif mode == ResilienceMode.FULL:
                result = await self._execute_full(
                    func,
                    *args,
                    endpoint_name=endpoint_name,
                    priority=priority,
                    timeout=timeout,
                    **kwargs,
                )
            elif mode == ResilienceMode.CRITICAL:
                result = await self._execute_critical(
                    func,
                    *args,
                    endpoint_name=endpoint_name,
                    priority=priority,
                    timeout=timeout,
                    **kwargs,
                )
            else:
                raise ValueError(f"Unsupported resilience mode: {mode}")

            # Record success
            duration = time.time() - start_time
            await self._record_success(endpoint_name, duration)

            if self.metrics_collector:
                await record_api_call(
                    endpoint=endpoint_name,
                    function_name=func.__name__,
                    duration=duration,
                    success=True,
                    tokens_used=expected_tokens,
                    model=model,
                    cache_hit=False,
                    priority=priority.name.lower(),
                )

            return result

        except Exception as e:
            # Record failure
            duration = time.time() - start_time
            await self._record_failure(endpoint_name, duration, e)

            if self.metrics_collector:
                await record_api_call(
                    endpoint=endpoint_name,
                    function_name=func.__name__,
                    duration=duration,
                    success=False,
                    error_type=type(e).__name__,
                    tokens_used=0,
                    model=model,
                    priority=priority.name.lower(),
                )

            # Try fallback if enabled
            if self.config.enable_fallback:
                fallback_result = await self._try_fallback(
                    func, args, kwargs, endpoint_name
                )
                if fallback_result is not None:
                    return fallback_result

            raise

    async def _execute_basic(self, func: Callable, *args, **kwargs) -> Any:
        """Basic execution with minimal resilience."""
        return await self._call_function(func, *args, **kwargs)

    async def _execute_enhanced(
        self, func: Callable, *args, endpoint_name: str, **kwargs
    ) -> Any:
        """Enhanced execution with retry logic."""
        last_error = None

        for attempt in range(self.config.retry_config.max_retries + 1):
            try:
                if attempt > 0:
                    if not await self.retry_manager.should_retry(last_error, attempt):
                        break

                    delay = await self.retry_manager.get_retry_delay(
                        last_error, attempt
                    )
                    await asyncio.sleep(delay)

                result = await self._call_function(func, *args, **kwargs)

                # Record success
                duration = time.time() - time.time()  # Would be tracked properly
                await self.retry_manager.record_success(duration, endpoint_name)

                return result

            except Exception as e:
                last_error = e
                logger.warning(
                    f"Attempt {attempt + 1} failed for {endpoint_name}: {str(e)}"
                )

                if attempt == self.config.retry_config.max_retries:
                    raise e

        raise last_error

    async def _execute_smart(
        self,
        func: Callable,
        *args,
        endpoint_name: str,
        priority: RequestPriority,
        timeout: Optional[float],
        **kwargs,
    ) -> Any:
        """Smart execution with rate limiting."""
        request_id = f"{endpoint_name}_{int(time.time() * 1000)}"

        # Check rate limiting
        if not await self.rate_limiter.acquire(priority, timeout, request_id):
            raise asyncio.TimeoutError(f"Rate limit timeout for {endpoint_name}")

        try:
            result = await self._call_function(func, *args, **kwargs)

            # Record response
            duration = time.time() - time.time()  # Would be tracked properly
            await self.rate_limiter.record_response(duration, True, priority)

            return result

        except Exception:
            # Record failure
            duration = time.time() - time.time()  # Would be tracked properly
            await self.rate_limiter.record_response(duration, False, priority)
            raise

    async def _execute_full(
        self,
        func: Callable,
        *args,
        endpoint_name: str,
        priority: RequestPriority,
        timeout: Optional[float],
        **kwargs,
    ) -> Any:
        """Full execution with all resilience features."""
        request_id = f"{endpoint_name}_{int(time.time() * 1000)}"

        # Check rate limiting
        if not await self.rate_limiter.acquire(priority, timeout, request_id):
            raise asyncio.TimeoutError(f"Rate limit timeout for {endpoint_name}")

        # Execute with retry logic
        return await self._execute_enhanced(
            func, *args, endpoint_name=endpoint_name, **kwargs
        )

    async def _execute_critical(
        self,
        func: Callable,
        *args,
        endpoint_name: str,
        priority: RequestPriority,
        timeout: Optional[float],
        **kwargs,
    ) -> Any:
        """Critical execution with maximum protection."""
        # Force critical priority
        priority = RequestPriority.CRITICAL

        # Use full resilience with extended timeout
        extended_timeout = (timeout or 30.0) * 2

        return await self._execute_full(
            func,
            *args,
            endpoint_name=endpoint_name,
            priority=priority,
            timeout=extended_timeout,
            **kwargs,
        )

    async def _call_function(self, func: Callable, *args, **kwargs) -> Any:
        """Call function with proper async handling."""
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)

    async def _record_success(self, endpoint_name: str, duration: float):
        """Record successful request."""
        if endpoint_name not in self.health_metrics:
            self.health_metrics[endpoint_name] = HealthMetrics(
                endpoint_name=endpoint_name,
                status=HealthStatus.HEALTHY,
                success_rate=1.0,
                avg_response_time=duration,
                total_requests=1,
                failed_requests=0,
                last_success=datetime.now(),
                consecutive_failures=0,
            )
        else:
            metrics = self.health_metrics[endpoint_name]
            metrics.total_requests += 1
            metrics.success_rate = (
                metrics.total_requests - metrics.failed_requests
            ) / metrics.total_requests
            metrics.avg_response_time = (metrics.avg_response_time + duration) / 2
            metrics.last_success = datetime.now()
            metrics.consecutive_failures = 0

            # Update health status
            self._update_health_status(metrics)

    async def _record_failure(
        self, endpoint_name: str, duration: float, error: Exception
    ):
        """Record failed request."""
        if endpoint_name not in self.health_metrics:
            self.health_metrics[endpoint_name] = HealthMetrics(
                endpoint_name=endpoint_name,
                status=HealthStatus.UNHEALTHY,
                success_rate=0.0,
                avg_response_time=duration,
                total_requests=1,
                failed_requests=1,
                last_failure=datetime.now(),
                consecutive_failures=1,
            )
        else:
            metrics = self.health_metrics[endpoint_name]
            metrics.total_requests += 1
            metrics.failed_requests += 1
            metrics.success_rate = (
                metrics.total_requests - metrics.failed_requests
            ) / metrics.total_requests
            metrics.last_failure = datetime.now()
            metrics.consecutive_failures += 1

            # Update health status
            self._update_health_status(metrics)

        # Store failed request for debugging
        if self.config.persist_failed_requests:
            self.failed_requests.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "endpoint": endpoint_name,
                    "error": str(error),
                    "error_type": type(error).__name__,
                    "duration": duration,
                }
            )

            # Keep only recent failures
            if len(self.failed_requests) > 100:
                self.failed_requests.pop(0)

    def _update_health_status(self, metrics: HealthMetrics):
        """Update health status based on metrics."""
        if metrics.success_rate >= self.config.degraded_threshold:
            metrics.status = HealthStatus.HEALTHY
        elif metrics.success_rate >= self.config.unhealthy_threshold:
            metrics.status = HealthStatus.DEGRADED
        elif metrics.consecutive_failures >= 5:
            metrics.status = HealthStatus.DOWN
        else:
            metrics.status = HealthStatus.UNHEALTHY

    async def _try_fallback(
        self, func: Callable, args: tuple, kwargs: dict, endpoint_name: str
    ) -> Any:
        """Try to get fallback response."""
        if not self.config.enable_fallback:
            return None

        # Create cache key
        cache_key = f"{endpoint_name}_{hash(str(args) + str(kwargs))}"

        # Check if we have a cached response
        if cache_key in self.fallback_cache:
            cached_entry = self.fallback_cache[cache_key]
            if datetime.now() - cached_entry["timestamp"] < timedelta(
                seconds=self.config.fallback_cache_duration
            ):
                logger.info(f"Using fallback response for {endpoint_name}")
                return cached_entry["response"]

        return None

    async def _health_check_loop(self):
        """Background health check loop."""
        while not self._shutdown:
            try:
                await asyncio.sleep(self.config.health_check_interval)

                # Check health of all endpoints
                for endpoint_name, metrics in self.health_metrics.items():
                    if metrics.status == HealthStatus.DOWN:
                        logger.warning(f"Endpoint {endpoint_name} is DOWN")
                    elif metrics.status == HealthStatus.UNHEALTHY:
                        logger.warning(f"Endpoint {endpoint_name} is UNHEALTHY")
                    elif metrics.status == HealthStatus.DEGRADED:
                        logger.info(f"Endpoint {endpoint_name} is DEGRADED")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        return {
            "system_started": self._started,
            "retry_manager": self.retry_manager.get_health_metrics(),
            "rate_limiter": self.rate_limiter.get_queue_status(),
            "health_metrics": {
                endpoint: {
                    "status": metrics.status.value,
                    "success_rate": metrics.success_rate,
                    "avg_response_time": metrics.avg_response_time,
                    "total_requests": metrics.total_requests,
                    "failed_requests": metrics.failed_requests,
                    "consecutive_failures": metrics.consecutive_failures,
                }
                for endpoint, metrics in self.health_metrics.items()
            },
            "failed_requests_count": len(self.failed_requests),
            "fallback_cache_size": len(self.fallback_cache),
            "metrics": (
                self.metrics_collector.get_realtime_metrics()
                if self.metrics_collector
                else {}
            ),
        }

    def get_health_report(self) -> Dict[str, Any]:
        """Get detailed health report."""
        healthy_endpoints = [
            m for m in self.health_metrics.values() if m.status == HealthStatus.HEALTHY
        ]
        degraded_endpoints = [
            m for m in self.health_metrics.values() if m.status == HealthStatus.DEGRADED
        ]
        unhealthy_endpoints = [
            m
            for m in self.health_metrics.values()
            if m.status == HealthStatus.UNHEALTHY
        ]
        down_endpoints = [
            m for m in self.health_metrics.values() if m.status == HealthStatus.DOWN
        ]

        return {
            "overall_health": (
                "healthy"
                if len(unhealthy_endpoints) == 0 and len(down_endpoints) == 0
                else "degraded"
            ),
            "total_endpoints": len(self.health_metrics),
            "healthy_count": len(healthy_endpoints),
            "degraded_count": len(degraded_endpoints),
            "unhealthy_count": len(unhealthy_endpoints),
            "down_count": len(down_endpoints),
            "recent_failures": (
                self.failed_requests[-10:] if self.failed_requests else []
            ),
            "generated_at": datetime.now().isoformat(),
        }


# Global resilience system
_global_resilience: Optional[OptimizedResilienceSystem] = None


async def get_resilience_system(
    config: Optional[ResilienceConfig] = None,
) -> OptimizedResilienceSystem:
    """Get or create global resilience system."""
    global _global_resilience
    if _global_resilience is None:
        _global_resilience = OptimizedResilienceSystem(config)
        await _global_resilience.start()
    return _global_resilience


# Decorators for different resilience modes
def with_basic_resilience(endpoint_name: str = ""):
    """Decorator for basic resilience."""

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            system = await get_resilience_system()
            return await system.execute_with_resilience(
                func,
                *args,
                endpoint_name=endpoint_name or func.__name__,
                mode=ResilienceMode.BASIC,
                **kwargs,
            )

        return wrapper

    return decorator


def with_enhanced_resilience(endpoint_name: str = ""):
    """Decorator for enhanced resilience with retry logic."""

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            system = await get_resilience_system()
            return await system.execute_with_resilience(
                func,
                *args,
                endpoint_name=endpoint_name or func.__name__,
                mode=ResilienceMode.ENHANCED,
                **kwargs,
            )

        return wrapper

    return decorator


def with_smart_resilience(
    endpoint_name: str = "",
    priority: RequestPriority = RequestPriority.NORMAL,
    timeout: Optional[float] = None,
):
    """Decorator for smart resilience with rate limiting."""

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            system = await get_resilience_system()
            return await system.execute_with_resilience(
                func,
                *args,
                endpoint_name=endpoint_name or func.__name__,
                priority=priority,
                timeout=timeout,
                mode=ResilienceMode.SMART,
                **kwargs,
            )

        return wrapper

    return decorator


def with_full_resilience(
    endpoint_name: str = "",
    priority: RequestPriority = RequestPriority.NORMAL,
    timeout: Optional[float] = None,
    model: str = "gpt-4",
    expected_tokens: int = 0,
):
    """Decorator for full resilience with all features."""

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            system = await get_resilience_system()
            return await system.execute_with_resilience(
                func,
                *args,
                endpoint_name=endpoint_name or func.__name__,
                priority=priority,
                timeout=timeout,
                mode=ResilienceMode.FULL,
                model=model,
                expected_tokens=expected_tokens,
                **kwargs,
            )

        return wrapper

    return decorator


def with_critical_resilience(endpoint_name: str = "", timeout: Optional[float] = None):
    """Decorator for critical resilience with maximum protection."""

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            system = await get_resilience_system()
            return await system.execute_with_resilience(
                func,
                *args,
                endpoint_name=endpoint_name or func.__name__,
                priority=RequestPriority.CRITICAL,
                timeout=timeout,
                mode=ResilienceMode.CRITICAL,
                **kwargs,
            )

        return wrapper

    return decorator


# Cleanup function
async def cleanup_resilience_system():
    """Clean up resilience system on shutdown."""
    global _global_resilience
    if _global_resilience:
        await _global_resilience.stop()
        _global_resilience = None


async def test_optimized_resilience():
    """Test the optimized resilience system."""
    print("🛡️ Testing Optimized Resilience System")
    print("=" * 45)

    # Test different modes
    @with_basic_resilience("test_basic")
    async def basic_function():
        return "Basic resilience working"

    @with_enhanced_resilience("test_enhanced")
    async def enhanced_function():
        return "Enhanced resilience working"

    @with_smart_resilience("test_smart", priority=RequestPriority.HIGH)
    async def smart_function():
        return "Smart resilience working"

    @with_full_resilience("test_full", model="gpt-4", expected_tokens=100)
    async def full_function():
        return "Full resilience working"

    @with_critical_resilience("test_critical")
    async def critical_function():
        return "Critical resilience working"

    # Test all modes
    try:
        result = await basic_function()
        print(f"✅ Basic: {result}")

        result = await enhanced_function()
        print(f"✅ Enhanced: {result}")

        result = await smart_function()
        print(f"✅ Smart: {result}")

        result = await full_function()
        print(f"✅ Full: {result}")

        result = await critical_function()
        print(f"✅ Critical: {result}")

        # Get system status
        system = await get_resilience_system()
        status = system.get_system_status()

        print("\n📊 System Status:")
        print(f"  Started: {status['system_started']}")
        print(f"  Endpoints monitored: {len(status['health_metrics'])}")
        print(f"  Failed requests: {status['failed_requests_count']}")

        # Get health report
        health = system.get_health_report()
        print("\n🏥 Health Report:")
        print(f"  Overall health: {health['overall_health']}")
        print(
            f"  Healthy endpoints: {health['healthy_count']}/{health['total_endpoints']}"
        )

    except Exception as e:
        print(f"❌ Test failed: {e}")

    finally:
        await cleanup_resilience_system()


if __name__ == "__main__":
    asyncio.run(test_optimized_resilience())
