"""
Comprehensive tests for the resilience system.
Tests enhanced retry logic, smart rate limiting, and monitoring integration.
"""

import asyncio
import pytest
import random
import time
from unittest.mock import Mock

from utils.enhanced_retry import AdaptiveRetryManager, RetryConfig, with_enhanced_retry
from utils.smart_rate_limiter import SmartRateLimiter, RateLimitConfig, RequestPriority
from utils.resilience import ResilienceFramework, ResilienceConfig
from utils.integrated_resilience import IntegratedResilienceSystem, IntegratedConfig, with_full_resilience
from monitoring.api_monitor import get_metrics_collector, record_api_call


class TestEnhancedRetry:
    """Test suite for enhanced retry logic."""
    
    @pytest.fixture
    async def retry_manager(self):
        """Create retry manager for testing."""
        config = RetryConfig(
            max_retries=3,
            base_delay=0.1,
            max_delay=1.0,
            failure_threshold=2,
            recovery_timeout=1.0
        )
        return AdaptiveRetryManager(config)
    
    async def test_exponential_backoff(self, retry_manager):
        """Test exponential backoff calculation."""
        error = Exception("Test error")
        
        delay1 = await retry_manager.get_retry_delay(error, 1)
        delay2 = await retry_manager.get_retry_delay(error, 2)
        delay3 = await retry_manager.get_retry_delay(error, 3)
        
        assert delay1 < delay2 < delay3
        assert delay3 <= retry_manager.config.max_delay
    
    async def test_circuit_breaker_open(self, retry_manager):
        """Test circuit breaker opening after failures."""
        error = Exception("Test error")
        
        # Trigger failures to open circuit breaker
        for _ in range(retry_manager.config.failure_threshold + 1):
            await retry_manager._record_failure(error)
        
        # Should not retry when circuit is open
        should_retry = await retry_manager.should_retry(error, 1)
        assert not should_retry
    
    async def test_circuit_breaker_recovery(self, retry_manager):
        """Test circuit breaker recovery."""
        error = Exception("Test error")
        
        # Open circuit breaker
        for _ in range(retry_manager.config.failure_threshold + 1):
            await retry_manager._record_failure(error)
        
        # Wait for recovery timeout
        await asyncio.sleep(retry_manager.config.recovery_timeout + 0.1)
        
        # Should transition to HALF_OPEN
        should_retry = await retry_manager.should_retry(error, 1)
        assert should_retry
    
    async def test_retry_decorator_success(self):
        """Test retry decorator with eventual success."""
        call_count = 0
        
        @with_enhanced_retry(config=RetryConfig(max_retries=3, base_delay=0.01))
        async def failing_function():
            nonlocal call_count
            call_count += 1
            
            if call_count <= 2:
                raise Exception(f"Failure #{call_count}")
            return f"Success on attempt {call_count}"
        
        result = await failing_function()
        assert result == "Success on attempt 3"
        assert call_count == 3
    
    async def test_retry_decorator_failure(self):
        """Test retry decorator with ultimate failure."""
        call_count = 0
        
        @with_enhanced_retry(config=RetryConfig(max_retries=2, base_delay=0.01))
        async def always_failing_function():
            nonlocal call_count
            call_count += 1
            raise Exception(f"Failure #{call_count}")
        
        with pytest.raises(Exception) as exc_info:
            await always_failing_function()
        
        assert "Failure #3" in str(exc_info.value)
        assert call_count == 3  # Initial + 2 retries


class TestSmartRateLimiter:
    """Test suite for smart rate limiting."""
    
    @pytest.fixture
    async def rate_limiter(self):
        """Create rate limiter for testing."""
        config = RateLimitConfig(
            tokens_per_second=2.0,
            bucket_capacity=5,
            target_response_time=1.0,
            adjustment_interval=0.1
        )
        limiter = SmartRateLimiter(config)
        await limiter.start()
        yield limiter
        await limiter.stop()
    
    async def test_token_bucket_acquire(self, rate_limiter):
        """Test token bucket acquisition."""
        # Should be able to acquire tokens up to capacity
        for _ in range(rate_limiter.config.bucket_capacity):
            result = await rate_limiter.token_bucket.acquire()
            assert result is True
        
        # Should fail when bucket is empty
        result = await rate_limiter.token_bucket.acquire()
        assert result is False
    
    async def test_priority_queuing(self, rate_limiter):
        """Test priority-based request queuing."""
        # Fill up token bucket
        for _ in range(rate_limiter.config.bucket_capacity):
            await rate_limiter.token_bucket.acquire()
        
        # Queue requests with different priorities
        tasks = []
        for i, priority in enumerate([RequestPriority.LOW, RequestPriority.HIGH, RequestPriority.CRITICAL]):
            task = asyncio.create_task(
                rate_limiter.acquire(priority=priority, timeout=2.0, request_id=f"req_{i}")
            )
            tasks.append((priority, task))
        
        # Wait briefly for all requests to be queued
        await asyncio.sleep(0.1)
        
        # Check queue lengths
        status = rate_limiter.get_queue_status()
        assert status['total_queued'] == 3
    
    async def test_rate_adjustment(self, rate_limiter):
        """Test dynamic rate adjustment."""
        initial_rate = rate_limiter.current_rate
        
        # Record slow responses to trigger rate decrease
        for _ in range(10):
            await rate_limiter.record_response(5.0, True, RequestPriority.NORMAL)  # 5 second response
        
        # Trigger adjustment
        await rate_limiter._adjust_rate_if_needed()
        
        # Rate should have decreased
        assert rate_limiter.current_rate < initial_rate
    
    async def test_estimated_wait_time(self, rate_limiter):
        """Test wait time estimation."""
        # Queue some requests
        for _ in range(3):
            await rate_limiter.priority_queues[RequestPriority.NORMAL].append(
                Mock(priority=RequestPriority.NORMAL, timestamp=time.time())
            )
        
        wait_time = await rate_limiter.get_estimated_wait_time(RequestPriority.NORMAL)
        assert wait_time > 0


class TestResilienceFramework:
    """Test suite for resilience framework."""
    
    @pytest.fixture
    async def framework(self):
        """Create resilience framework for testing."""
        config = ResilienceConfig(
            health_check_interval=0.1,
            degraded_threshold=0.8,
            unhealthy_threshold=0.5,
            fallback_cache_duration=1.0
        )
        framework = ResilienceFramework(config)
        await framework.start()
        yield framework
        await framework.stop()
    
    async def test_health_monitoring(self, framework):
        """Test health monitoring functionality."""
        # Record successful requests
        for _ in range(10):
            await framework.health_monitor.record_request("test_api", True, 0.5)
        
        # Record some failures
        for _ in range(2):
            await framework.health_monitor.record_request("test_api", False, 1.0)
        
        status = framework.health_monitor.get_health_status("test_api")
        assert status['total_requests'] == 12
        assert status['success_rate'] > 0.5
    
    async def test_fallback_cache(self, framework):
        """Test fallback cache functionality."""
        async def test_function(param):
            return f"result_{param}"
        
        # Execute function to cache result
        result = await framework.execute_with_resilience(
            test_function, "test", endpoint_name="test_api"
        )
        assert result == "result_test"
        
        # Verify result is cached
        cached_result = await framework._get_fallback_response(test_function, ("test",), {})
        assert cached_result == "result_test"
    
    async def test_dead_letter_queue(self, framework):
        """Test dead letter queue functionality."""
        async def failing_function():
            raise Exception("Always fails")
        
        # Execute failing function
        try:
            await framework.execute_with_resilience(
                failing_function, endpoint_name="failing_api"
            )
        except Exception:
            pass  # Expected
        
        # Check dead letter queue
        stats = framework.dead_letter_queue.get_stats()
        assert stats['queue_size'] > 0


class TestIntegratedSystem:
    """Test suite for integrated resilience system."""
    
    @pytest.fixture
    async def integrated_system(self):
        """Create integrated system for testing."""
        config = IntegratedConfig()
        # Use faster settings for testing
        config.retry_config.base_delay = 0.01
        config.rate_limit_config.tokens_per_second = 10.0
        config.resilience_config.health_check_interval = 0.1
        
        system = IntegratedResilienceSystem(config)
        await system.start()
        yield system
        await system.stop()
    
    async def test_full_resilience_success(self, integrated_system):
        """Test successful execution with full resilience."""
        @with_full_resilience(
            endpoint_name="test_success",
            priority=RequestPriority.HIGH,
            expected_tokens=100
        )
        async def test_function():
            return "Success"
        
        result = await test_function()
        assert result == "Success"
    
    async def test_full_resilience_with_retries(self, integrated_system):
        """Test execution with retries."""
        call_count = 0
        
        @with_full_resilience(
            endpoint_name="test_retry",
            priority=RequestPriority.NORMAL,
            expected_tokens=150
        )
        async def test_function():
            nonlocal call_count
            call_count += 1
            
            if call_count <= 2:
                raise Exception(f"Failure #{call_count}")
            return f"Success on attempt {call_count}"
        
        result = await test_function()
        assert result == "Success on attempt 3"
        assert call_count == 3
    
    async def test_system_status(self, integrated_system):
        """Test system status reporting."""
        status = integrated_system.get_system_status()
        
        assert 'system_started' in status
        assert 'retry_manager' in status
        assert 'rate_limiter' in status
        assert 'resilience_framework' in status
        assert status['system_started'] is True
    
    async def test_priority_handling(self, integrated_system):
        """Test different priority levels."""
        results = []
        
        async def make_request(priority: RequestPriority, request_id: str):
            @with_full_resilience(
                endpoint_name=f"test_{priority.name.lower()}",
                priority=priority
            )
            async def test_function():
                await asyncio.sleep(0.01)
                return f"Result for {request_id}"
            
            return await test_function()
        
        # Create concurrent requests with different priorities
        tasks = []
        for i, priority in enumerate([RequestPriority.LOW, RequestPriority.HIGH, RequestPriority.CRITICAL]):
            task = asyncio.create_task(make_request(priority, f"req_{i}"))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        assert len(results) == 3
        assert all("Result for req_" in result for result in results)


class TestMonitoringIntegration:
    """Test suite for monitoring integration."""
    
    async def test_metrics_collection(self):
        """Test metrics collection during API calls."""
        collector = get_metrics_collector()
        
        # Record some API calls
        for i in range(5):
            await record_api_call(
                endpoint="test_endpoint",
                function_name="test_function",
                duration=random.uniform(0.1, 2.0),
                success=random.choice([True, True, False]),  # 66% success rate
                tokens_used=random.randint(50, 200),
                cache_hit=random.choice([True, False])
            )
        
        # Get metrics
        metrics = collector.get_realtime_metrics()
        
        assert metrics['total_calls'] == 5
        assert 'success_rate' in metrics
        assert 'avg_response_time' in metrics
        assert 'total_cost' in metrics
    
    async def test_cost_optimization_report(self):
        """Test cost optimization report generation."""
        collector = get_metrics_collector()
        
        # Generate some data
        for i in range(20):
            await record_api_call(
                endpoint="test_endpoint",
                function_name="test_function",
                duration=random.uniform(0.5, 3.0),
                success=random.choice([True, True, True, False]),  # 75% success rate
                tokens_used=random.randint(100, 500),
                cache_hit=random.choice([True, False, False])  # 33% cache hit rate
            )
        
        report = collector.generate_cost_optimization_report()
        
        assert 'total_cost' in report
        assert 'recommendations' in report
        assert 'cache_hit_rate' in report
        assert 'error_rate' in report
    
    async def test_performance_benchmark(self):
        """Benchmark performance improvements."""
        # Test sequential vs parallel execution
        async def mock_api_call(delay: float):
            await asyncio.sleep(delay)
            return f"Result after {delay}s"
        
        # Sequential execution
        start_time = time.time()
        sequential_results = []
        for i in range(5):
            result = await mock_api_call(0.1)
            sequential_results.append(result)
        sequential_time = time.time() - start_time
        
        # Parallel execution
        start_time = time.time()
        tasks = [mock_api_call(0.1) for _ in range(5)]
        parallel_results = await asyncio.gather(*tasks)
        parallel_time = time.time() - start_time
        
        # Parallel should be significantly faster
        speedup = sequential_time / parallel_time
        assert speedup > 2.0  # Should be at least 2x faster
        assert len(parallel_results) == len(sequential_results)


# Test runner
async def run_all_tests():
    """Run all resilience system tests."""
    print("🧪 Running Resilience System Tests")
    print("=" * 40)
    
    test_classes = [
        TestEnhancedRetry,
        TestSmartRateLimiter,
        TestResilienceFramework,
        TestIntegratedSystem,
        TestMonitoringIntegration
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for test_class in test_classes:
        print(f"\n📋 Running {test_class.__name__}...")
        
        # Get test methods
        test_methods = [method for method in dir(test_class) if method.startswith('test_')]
        
        for method_name in test_methods:
            total_tests += 1
            try:
                # Create test instance
                test_instance = test_class()
                
                # Get fixtures if needed
                fixtures = {}
                if hasattr(test_instance, f'{method_name.replace("test_", "")}_fixture'):
                    fixture_method = getattr(test_instance, f'{method_name.replace("test_", "")}_fixture')
                    fixtures['fixture'] = await fixture_method()
                
                # Run test method
                test_method = getattr(test_instance, method_name)
                if asyncio.iscoroutinefunction(test_method):
                    await test_method(**fixtures)
                else:
                    test_method(**fixtures)
                
                print(f"  ✅ {method_name}")
                passed_tests += 1
                
            except Exception as e:
                print(f"  ❌ {method_name}: {str(e)}")
    
    print(f"\n📊 Test Results: {passed_tests}/{total_tests} passed ({passed_tests/total_tests*100:.1f}%)")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed!")
    else:
        print("⚠️ Some tests failed - check implementation")


if __name__ == "__main__":
    asyncio.run(run_all_tests())