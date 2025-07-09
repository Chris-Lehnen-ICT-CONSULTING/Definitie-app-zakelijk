"""
Integrated resilience system for DefinitieAgent.
Combines enhanced retry logic, smart rate limiting, resilience framework, and monitoring.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Callable, Any, Union
from dataclasses import dataclass
from datetime import datetime
from functools import wraps

from utils.enhanced_retry import (
    AdaptiveRetryManager, RetryConfig, with_enhanced_retry
)
from utils.smart_rate_limiter import (
    SmartRateLimiter, RateLimitConfig, RequestPriority, with_smart_rate_limit
)
from utils.resilience import (
    ResilienceFramework, ResilienceConfig, with_resilience
)
from monitoring.api_monitor import (
    get_metrics_collector, record_api_call
)

logger = logging.getLogger(__name__)


@dataclass
class IntegratedConfig:
    """Configuration for integrated resilience system."""
    # Retry configuration
    retry_config: RetryConfig = None
    
    # Rate limiting configuration
    rate_limit_config: RateLimitConfig = None
    
    # Resilience configuration
    resilience_config: ResilienceConfig = None
    
    # Monitoring configuration
    enable_monitoring: bool = True
    enable_cost_tracking: bool = True
    
    def __post_init__(self):
        """Initialize default configurations."""
        if self.retry_config is None:
            self.retry_config = RetryConfig(
                max_retries=5,
                base_delay=1.0,
                max_delay=60.0,
                strategy="adaptive",
                failure_threshold=3,
                recovery_timeout=30.0
            )
        
        if self.rate_limit_config is None:
            self.rate_limit_config = RateLimitConfig(
                tokens_per_second=2.0,
                bucket_capacity=10,
                burst_capacity=5,
                target_response_time=2.0,
                adjustment_factor=0.1
            )
        
        if self.resilience_config is None:
            self.resilience_config = ResilienceConfig(
                health_check_interval=30.0,
                degraded_threshold=0.8,
                unhealthy_threshold=0.5,
                enable_graceful_degradation=True,
                persist_failed_requests=True
            )


class IntegratedResilienceSystem:
    """Integrated system combining all resilience components."""
    
    def __init__(self, config: Optional[IntegratedConfig] = None):
        self.config = config or IntegratedConfig()
        
        # Initialize components
        self.retry_manager = AdaptiveRetryManager(self.config.retry_config)
        self.rate_limiter = SmartRateLimiter(self.config.rate_limit_config)
        self.resilience_framework = ResilienceFramework(self.config.resilience_config)
        self.metrics_collector = get_metrics_collector() if self.config.enable_monitoring else None
        
        # System state
        self._started = False
        self._shutdown = False
    
    async def start(self):
        """Start all resilience components."""
        if self._started:
            return
        
        await self.rate_limiter.start()
        await self.resilience_framework.start()
        
        self._started = True
        logger.info("🚀 Integrated resilience system started")
    
    async def stop(self):
        """Stop all resilience components."""
        if not self._started:
            return
        
        self._shutdown = True
        
        await self.rate_limiter.stop()
        await self.resilience_framework.stop()
        
        # Save retry manager history
        self.retry_manager._save_historical_data()
        
        logger.info("⏹️ Integrated resilience system stopped")
    
    async def execute_with_full_resilience(
        self,
        func: Callable,
        *args,
        endpoint_name: str = "",
        priority: RequestPriority = RequestPriority.NORMAL,
        timeout: Optional[float] = None,
        enable_fallback: bool = True,
        model: str = "gpt-4",
        expected_tokens: int = 0,
        **kwargs
    ) -> Any:
        """
        Execute function with full resilience support.
        
        Args:
            func: Function to execute
            *args: Function arguments
            endpoint_name: Name of the endpoint for monitoring
            priority: Request priority
            timeout: Request timeout
            enable_fallback: Whether to enable fallback responses
            model: AI model being used (for cost calculation)
            expected_tokens: Expected token usage
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
        """
        if not endpoint_name:
            endpoint_name = func.__name__
        
        start_time = time.time()
        request_id = f"{endpoint_name}_{int(time.time() * 1000)}"
        
        try:
            # Step 1: Check rate limiting
            if not await self.rate_limiter.acquire(priority, timeout, request_id):
                raise asyncio.TimeoutError(f"Rate limit timeout for {endpoint_name}")
            
            # Step 2: Execute with retry logic and resilience
            result = await self._execute_with_retry_and_resilience(
                func, *args,
                endpoint_name=endpoint_name,
                priority=priority,
                enable_fallback=enable_fallback,
                **kwargs
            )
            
            # Step 3: Record successful execution
            duration = time.time() - start_time
            await self.rate_limiter.record_response(duration, True, priority)
            
            if self.metrics_collector:
                await record_api_call(
                    endpoint=endpoint_name,
                    function_name=func.__name__,
                    duration=duration,
                    success=True,
                    tokens_used=expected_tokens,
                    model=model,
                    cache_hit=False,  # Would need to check cache
                    priority=priority.name.lower()
                )
            
            return result
            
        except Exception as e:
            # Record failure
            duration = time.time() - start_time
            await self.rate_limiter.record_response(duration, False, priority)
            
            if self.metrics_collector:
                await record_api_call(
                    endpoint=endpoint_name,
                    function_name=func.__name__,
                    duration=duration,
                    success=False,
                    error_type=type(e).__name__,
                    tokens_used=0,
                    model=model,
                    priority=priority.name.lower()
                )
            
            raise
    
    async def _execute_with_retry_and_resilience(
        self,
        func: Callable,
        *args,
        endpoint_name: str,
        priority: RequestPriority,
        enable_fallback: bool,
        **kwargs
    ) -> Any:
        """Execute function with retry logic and resilience framework."""
        last_error = None
        
        for attempt in range(self.config.retry_config.max_retries + 1):
            try:
                # Check if we should retry
                if attempt > 0:
                    if not await self.retry_manager.should_retry(last_error, attempt):
                        logger.error(f"Max retries exceeded for {endpoint_name}")
                        raise last_error
                    
                    # Wait before retry
                    delay = await self.retry_manager.get_retry_delay(last_error, attempt)
                    logger.info(f"Retrying {endpoint_name} in {delay:.2f}s (attempt {attempt + 1})")
                    await asyncio.sleep(delay)
                
                # Execute with resilience framework
                result = await self.resilience_framework.execute_with_resilience(
                    func, *args,
                    endpoint_name=endpoint_name,
                    priority=priority,
                    enable_fallback=enable_fallback,
                    **kwargs
                )
                
                # Record success
                duration = time.time() - time.time()  # This would be tracked properly
                await self.retry_manager.record_success(duration, endpoint_name)
                
                return result
                
            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed for {endpoint_name}: {str(e)}")
                
                if attempt == self.config.retry_config.max_retries:
                    raise e
        
        raise last_error
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        status = {
            'system_started': self._started,
            'retry_manager': self.retry_manager.get_health_metrics(),
            'rate_limiter': self.rate_limiter.get_queue_status(),
            'resilience_framework': self.resilience_framework.get_system_health(),
        }
        
        if self.metrics_collector:
            status['metrics'] = self.metrics_collector.get_realtime_metrics()
            status['cost_optimization'] = self.metrics_collector.generate_cost_optimization_report()
        
        return status


# Global integrated system
_integrated_system: Optional[IntegratedResilienceSystem] = None


async def get_integrated_system(config: Optional[IntegratedConfig] = None) -> IntegratedResilienceSystem:
    """Get or create global integrated resilience system."""
    global _integrated_system
    if _integrated_system is None:
        _integrated_system = IntegratedResilienceSystem(config)
        await _integrated_system.start()
    return _integrated_system


def with_full_resilience(
    endpoint_name: str = "",
    priority: RequestPriority = RequestPriority.NORMAL,
    timeout: Optional[float] = None,
    enable_fallback: bool = True,
    model: str = "gpt-4",
    expected_tokens: int = 0
):
    """
    Decorator providing full resilience support.
    
    Args:
        endpoint_name: Name of the endpoint for monitoring
        priority: Request priority
        timeout: Request timeout
        enable_fallback: Whether to enable fallback responses
        model: AI model being used
        expected_tokens: Expected token usage
        
    Example:
        @with_full_resilience(
            endpoint_name="gpt_definition",
            priority=RequestPriority.HIGH,
            timeout=30.0,
            model="gpt-4",
            expected_tokens=300
        )
        async def generate_definition(term: str, context: dict):
            return await call_gpt_api(term, context)
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            system = await get_integrated_system()
            return await system.execute_with_full_resilience(
                func, *args,
                endpoint_name=endpoint_name or func.__name__,
                priority=priority,
                timeout=timeout,
                enable_fallback=enable_fallback,
                model=model,
                expected_tokens=expected_tokens,
                **kwargs
            )
        return wrapper
    return decorator


# Convenience functions for different use cases
def with_critical_resilience(endpoint_name: str = "", timeout: float = 10.0):
    """Decorator for critical operations with high priority."""
    return with_full_resilience(
        endpoint_name=endpoint_name,
        priority=RequestPriority.CRITICAL,
        timeout=timeout,
        enable_fallback=True
    )


def with_background_resilience(endpoint_name: str = "", timeout: float = 60.0):
    """Decorator for background operations with low priority."""
    return with_full_resilience(
        endpoint_name=endpoint_name,
        priority=RequestPriority.BACKGROUND,
        timeout=timeout,
        enable_fallback=False
    )


def with_cost_optimized_resilience(endpoint_name: str = "", model: str = "gpt-3.5-turbo"):
    """Decorator for cost-optimized operations."""
    return with_full_resilience(
        endpoint_name=endpoint_name,
        priority=RequestPriority.LOW,
        model=model,
        enable_fallback=True
    )


async def test_integrated_system():
    """Test the integrated resilience system."""
    print("🧪 Testing Integrated Resilience System")
    print("=" * 45)
    
    # Test different scenarios
    call_count = 0
    
    @with_full_resilience(
        endpoint_name="test_api",
        priority=RequestPriority.HIGH,
        timeout=30.0,
        model="gpt-4",
        expected_tokens=200
    )
    async def test_function(should_fail: bool = False, delay: float = 0.5):
        nonlocal call_count
        call_count += 1
        
        await asyncio.sleep(delay)
        
        if should_fail and call_count <= 2:
            raise Exception(f"Simulated failure #{call_count}")
        
        return f"Success on attempt #{call_count}"
    
    try:
        # Test successful execution
        result = await test_function(should_fail=False, delay=0.2)
        print(f"✅ Success: {result}")
        
        # Test with failures (should retry and succeed)
        call_count = 0
        result = await test_function(should_fail=True, delay=0.1)
        print(f"✅ Retry success: {result}")
        
        # Test critical operation
        @with_critical_resilience(endpoint_name="critical_test")
        async def critical_function():
            return "Critical operation completed"
        
        result = await critical_function()
        print(f"✅ Critical: {result}")
        
        # Test background operation
        @with_background_resilience(endpoint_name="background_test")
        async def background_function():
            await asyncio.sleep(0.1)
            return "Background operation completed"
        
        result = await background_function()
        print(f"✅ Background: {result}")
        
        # Get system status
        system = await get_integrated_system()
        status = system.get_system_status()
        
        print(f"\n📊 System Status:")
        print(f"  Started: {status['system_started']}")
        print(f"  Retry Manager State: {status['retry_manager']['circuit_state']}")
        print(f"  Rate Limiter Rate: {status['rate_limiter']['current_rate']:.2f} req/sec")
        print(f"  Total Requests: {status['retry_manager']['total_requests']}")
        
        if 'metrics' in status:
            metrics = status['metrics']
            print(f"  Success Rate: {metrics['success_rate']:.1%}")
            print(f"  Avg Response Time: {metrics['avg_response_time']:.2f}s")
            print(f"  Total Cost: ${metrics['total_cost']:.4f}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    finally:
        # Clean up
        if _integrated_system:
            await _integrated_system.stop()


# Cleanup function for application shutdown
async def cleanup_integrated_system():
    """Clean up integrated system on application shutdown."""
    global _integrated_system
    if _integrated_system:
        await _integrated_system.stop()
        _integrated_system = None


if __name__ == "__main__":
    asyncio.run(test_integrated_system())