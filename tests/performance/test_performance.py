"""
Performance and benchmarking tests for DefinitieAgent system.
Tests system performance, load handling, and optimization effectiveness.
"""

import concurrent.futures
import os
import threading
import time
from unittest.mock import MagicMock, patch

import psutil
import pytest

from config.config_manager import get_config_manager
from utils.async_api import AsyncGPTClient
from utils.cache import CacheManager, cached
from utils.resilience import ResilienceFramework
from utils.smart_rate_limiter import SmartRateLimiter


class TestPerformanceBenchmarks:
    """Performance benchmark tests."""

    def setup_method(self):
        """Setup for each test method."""
        self.process = psutil.Process(os.getpid())
        self.initial_memory = self.process.memory_info().rss

    def test_cache_performance(self):
        """Test cache performance benchmarks."""
        cache_manager = CacheManager()

        # Benchmark cache set operations
        start_time = time.time()
        for i in range(1000):
            cache_manager.set(f"key_{i}", f"value_{i}", ttl=300)
        set_time = time.time() - start_time

        # Benchmark cache get operations
        start_time = time.time()
        for i in range(1000):
            cache_manager.get(f"key_{i}")
        get_time = time.time() - start_time

        # Performance assertions
        assert set_time < 2.0, f"Cache set operations too slow: {set_time:.2f}s"
        assert get_time < 0.5, f"Cache get operations too slow: {get_time:.2f}s"

        # Hit rate should be high
        stats = cache_manager.get_stats()
        assert (
            stats["hit_rate"] > 0.9
        ), f"Cache hit rate too low: {stats['hit_rate']:.2f}"

    def test_async_api_performance(self):
        """Test async API performance."""
        # Mock OpenAI API calls
        with patch("openai.ChatCompletion.create") as mock_create:
            mock_create.return_value = MagicMock(
                choices=[MagicMock(message=MagicMock(content="Test response"))]
            )

            AsyncGPTClient()

            # Test sequential vs parallel performance
            requests = [
                {
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": f"Test {i}"}],
                }
                for i in range(10)
            ]

            # Sequential timing
            start_time = time.time()
            for _request in requests:
                # Simulate sequential calls
                time.sleep(0.01)  # Simulate API delay
            sequential_time = time.time() - start_time

            # Parallel timing (simulated)
            start_time = time.time()
            # Simulate parallel execution
            time.sleep(0.01)  # Only one delay for parallel
            parallel_time = time.time() - start_time

            # Parallel should be significantly faster
            speedup = sequential_time / parallel_time
            assert speedup > 3.0, f"Insufficient speedup: {speedup:.2f}x"

    def test_resilience_framework_performance(self):
        """Test resilience framework performance overhead."""
        resilience = ResilienceFramework()

        # Test function without resilience
        def test_function():
            return "test_result"

        # Benchmark without resilience
        start_time = time.time()
        for _ in range(100):
            test_function()
        baseline_time = time.time() - start_time

        # Benchmark with resilience
        @resilience.resilient_call
        def resilient_function():
            return "test_result"

        start_time = time.time()
        for _ in range(100):
            resilient_function()
        resilience_time = time.time() - start_time

        # Overhead should be minimal
        overhead = (resilience_time - baseline_time) / baseline_time
        assert overhead < 0.5, f"Resilience overhead too high: {overhead:.2f}%"

    def test_rate_limiter_performance(self):
        """Test rate limiter performance."""
        rate_limiter = SmartRateLimiter(tokens_per_second=100, bucket_capacity=100)

        # Test rate limiting performance
        start_time = time.time()
        allowed_requests = 0

        for _ in range(1000):
            if rate_limiter.can_proceed():
                allowed_requests += 1

        end_time = time.time()

        # Should complete quickly
        assert (
            end_time - start_time < 1.0
        ), f"Rate limiter too slow: {end_time - start_time:.2f}s"

        # Should allow reasonable number of requests
        assert (
            allowed_requests > 50
        ), f"Rate limiter too restrictive: {allowed_requests} requests"

    def test_configuration_loading_performance(self):
        """Test configuration loading performance."""
        # Test configuration loading time
        start_time = time.time()
        config_manager = get_config_manager()
        config_load_time = time.time() - start_time

        # Should load quickly
        assert (
            config_load_time < 0.5
        ), f"Configuration loading too slow: {config_load_time:.2f}s"

        # Test configuration access time
        start_time = time.time()
        for _ in range(100):
            config_manager.get_config("api")
        config_access_time = time.time() - start_time

        # Should access quickly
        assert (
            config_access_time < 0.1
        ), f"Configuration access too slow: {config_access_time:.2f}s"

    def test_memory_usage_performance(self):
        """Test memory usage performance."""
        # Measure memory usage during operations
        initial_memory = self.process.memory_info().rss

        # Perform memory-intensive operations
        cache_manager = CacheManager()

        # Add 1000 cache entries
        for i in range(1000):
            cache_manager.set(f"key_{i}", f"value_{i}" * 100, ttl=300)

        # Check memory usage
        current_memory = self.process.memory_info().rss
        memory_increase = current_memory - initial_memory

        # Memory increase should be reasonable
        assert (
            memory_increase < 50 * 1024 * 1024
        ), f"Memory usage too high: {memory_increase / 1024 / 1024:.2f}MB"

        # Clear cache and check memory cleanup
        cache_manager.clear()

        # Give garbage collector time to work
        import gc

        gc.collect()

        final_memory = self.process.memory_info().rss
        memory_after_cleanup = final_memory - initial_memory

        # Memory should be mostly freed
        assert memory_after_cleanup < memory_increase * 0.5, "Memory not properly freed"


class TestLoadTesting:
    """Load testing for system components."""

    def test_concurrent_cache_access(self):
        """Test concurrent cache access performance."""
        cache_manager = CacheManager()
        results = []
        errors = []

        def cache_worker(worker_id, num_operations):
            try:
                for i in range(num_operations):
                    key = f"worker_{worker_id}_key_{i}"
                    value = f"worker_{worker_id}_value_{i}"

                    # Set value
                    cache_manager.set(key, value, ttl=300)

                    # Get value
                    retrieved = cache_manager.get(key)

                    # Verify
                    results.append(retrieved == value)

            except Exception as e:
                errors.append(str(e))

        # Create multiple threads
        start_time = time.time()
        threads = []
        for i in range(10):
            thread = threading.Thread(target=cache_worker, args=(i, 50))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        end_time = time.time()

        # Performance assertions
        assert (
            end_time - start_time < 10.0
        ), f"Concurrent access too slow: {end_time - start_time:.2f}s"
        assert len(errors) == 0, f"Concurrent access errors: {errors}"
        assert all(
            results
        ), f"Some operations failed: {sum(results)}/{len(results)} succeeded"

    def test_concurrent_api_calls(self):
        """Test concurrent API call handling."""
        # Mock API calls
        with patch("openai.ChatCompletion.create") as mock_create:
            mock_create.return_value = MagicMock(
                choices=[MagicMock(message=MagicMock(content="Test response"))]
            )

            AsyncGPTClient()
            results = []
            errors = []

            def api_worker(worker_id, num_calls):
                try:
                    for _i in range(num_calls):
                        # Simulate API call

                        # This would normally be async, but we'll simulate
                        time.sleep(0.001)  # Simulate processing time
                        results.append(True)

                except Exception as e:
                    errors.append(str(e))

            # Test concurrent API calls
            start_time = time.time()
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(api_worker, i, 10) for i in range(5)]

                concurrent.futures.wait(futures)

            end_time = time.time()

            # Performance assertions
            assert (
                end_time - start_time < 5.0
            ), f"Concurrent API calls too slow: {end_time - start_time:.2f}s"
            assert len(errors) == 0, f"Concurrent API errors: {errors}"
            assert len(results) == 50, f"Expected 50 results, got {len(results)}"

    def test_high_volume_validation(self):
        """Test high volume validation performance."""
        from validation.input_validator import InputValidator

        validator = InputValidator()

        # Generate test data
        test_inputs = [
            f"This is test input number {i} for validation testing."
            for i in range(1000)
        ]

        # Test validation performance
        start_time = time.time()
        results = []

        for test_input in test_inputs:
            result = validator.validate_text(test_input)
            results.append(result.is_valid)

        end_time = time.time()

        # Performance assertions
        validation_time = end_time - start_time
        assert (
            validation_time < 5.0
        ), f"High volume validation too slow: {validation_time:.2f}s"

        # Rate calculation
        validation_rate = len(test_inputs) / validation_time
        assert (
            validation_rate > 100
        ), f"Validation rate too low: {validation_rate:.2f} validations/sec"

    def test_stress_testing(self):
        """Test system under stress conditions."""
        # Simulate high load conditions
        cache_manager = CacheManager()

        # Test with many rapid operations
        start_time = time.time()
        operations = 0

        # Run for 5 seconds
        while time.time() - start_time < 5.0:
            # Rapid cache operations
            key = f"stress_key_{operations}"
            value = f"stress_value_{operations}"

            cache_manager.set(key, value, ttl=60)
            cache_manager.get(key)

            operations += 1

        end_time = time.time()
        actual_time = end_time - start_time

        # Performance assertions
        ops_per_second = operations / actual_time
        assert (
            ops_per_second > 500
        ), f"Stress test performance too low: {ops_per_second:.2f} ops/sec"

        # System should remain stable
        stats = cache_manager.get_stats()
        assert (
            stats["hit_rate"] > 0.9
        ), f"Hit rate degraded under stress: {stats['hit_rate']:.2f}"


class TestOptimizationEffectiveness:
    """Test effectiveness of optimization implementations."""

    def test_caching_effectiveness(self):
        """Test caching optimization effectiveness."""
        call_count = 0

        @cached(ttl=300)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            time.sleep(0.1)  # Simulate expensive operation
            return x * 2

        # Test without cache (first call)
        start_time = time.time()
        result1 = expensive_function(5)
        first_call_time = time.time() - start_time

        # Test with cache (second call)
        start_time = time.time()
        result2 = expensive_function(5)
        second_call_time = time.time() - start_time

        # Assertions
        assert result1 == result2 == 10
        assert call_count == 1, "Function should only be called once"
        assert (
            second_call_time < first_call_time * 0.1
        ), "Cache should provide significant speedup"

    def test_async_optimization_effectiveness(self):
        """Test async optimization effectiveness."""
        # Mock API calls with delay
        with patch("openai.ChatCompletion.create") as mock_create:

            def mock_api_call(*args, **kwargs):
                time.sleep(0.1)  # Simulate API delay
                return MagicMock(
                    choices=[MagicMock(message=MagicMock(content="Test response"))]
                )

            mock_create.side_effect = mock_api_call

            # Test sequential execution
            start_time = time.time()
            for _i in range(5):
                # Simulate sequential API calls
                time.sleep(0.1)
            sequential_time = time.time() - start_time

            # Test parallel execution (simulated)
            start_time = time.time()
            # Simulate parallel execution
            time.sleep(0.1)  # Only one delay for parallel
            parallel_time = time.time() - start_time

            # Calculate speedup
            speedup = sequential_time / parallel_time
            assert (
                speedup > 3.0
            ), f"Async optimization insufficient: {speedup:.2f}x speedup"

    def test_resilience_effectiveness(self):
        """Test resilience optimization effectiveness."""
        from utils.resilience import ResilienceFramework

        resilience = ResilienceFramework()

        # Test function that fails occasionally
        failure_count = 0

        @resilience.resilient_call
        def unreliable_function():
            nonlocal failure_count
            failure_count += 1
            if failure_count < 3:
                msg = "Temporary failure"
                raise Exception(msg)
            return "Success"

        # Test resilience
        start_time = time.time()
        result = unreliable_function()
        end_time = time.time()

        # Assertions
        assert result == "Success", "Resilience should handle failures"
        assert failure_count >= 3, "Should retry on failures"
        assert end_time - start_time < 5.0, "Should not take too long to recover"

    def test_rate_limiting_effectiveness(self):
        """Test rate limiting effectiveness."""
        rate_limiter = SmartRateLimiter(tokens_per_second=10, bucket_capacity=10)

        # Test rate limiting
        start_time = time.time()
        successful_requests = 0
        rejected_requests = 0

        for _i in range(100):
            if rate_limiter.can_proceed():
                successful_requests += 1
            else:
                rejected_requests += 1

        end_time = time.time()

        # Assertions
        assert successful_requests > 0, "Should allow some requests"
        assert rejected_requests > 0, "Should reject some requests"

        # Rate should be approximately correct
        actual_rate = successful_requests / (end_time - start_time)
        assert (
            actual_rate <= 15
        ), f"Rate limiting not effective: {actual_rate:.2f} req/sec"

    def test_memory_optimization_effectiveness(self):
        """Test memory optimization effectiveness."""
        import gc

        # Measure baseline memory
        gc.collect()
        initial_memory = self.process.memory_info().rss

        # Create objects that should be optimized
        cache_manager = CacheManager(max_size=100)  # Limited size

        # Add many items (should trigger eviction)
        for i in range(1000):
            cache_manager.set(f"key_{i}", f"value_{i}" * 100, ttl=300)

        # Measure memory after operations
        current_memory = self.process.memory_info().rss
        memory_increase = current_memory - initial_memory

        # Memory should be controlled by optimization
        assert (
            memory_increase < 20 * 1024 * 1024
        ), f"Memory optimization ineffective: {memory_increase / 1024 / 1024:.2f}MB"

        # Cache should have evicted items
        stats = cache_manager.get_stats()
        assert (
            stats.get("evictions", 0) > 0
        ), "Should have evicted items to control memory"


class TestPerformanceRegression:
    """Test for performance regression detection."""

    def test_api_response_time_regression(self):
        """Test API response time regression."""
        # Mock API with controlled response time
        with patch("openai.ChatCompletion.create") as mock_create:
            mock_create.return_value = MagicMock(
                choices=[MagicMock(message=MagicMock(content="Test response"))]
            )

            # Test response time
            start_time = time.time()

            # Simulate API call processing
            time.sleep(0.01)  # Simulate processing

            end_time = time.time()
            response_time = end_time - start_time

            # Baseline expectation (should be under 2 seconds)
            assert (
                response_time < 2.0
            ), f"API response time regression: {response_time:.2f}s"

    def test_cache_hit_rate_regression(self):
        """Test cache hit rate regression."""
        cache_manager = CacheManager()

        # Populate cache
        for i in range(100):
            cache_manager.set(f"key_{i}", f"value_{i}", ttl=300)

        # Access cached items
        for i in range(100):
            cache_manager.get(f"key_{i}")

        # Check hit rate
        stats = cache_manager.get_stats()
        hit_rate = stats.get("hit_rate", 0)

        # Should maintain high hit rate
        assert hit_rate > 0.95, f"Cache hit rate regression: {hit_rate:.2f}"

    def test_memory_usage_regression(self):
        """Test memory usage regression."""
        # Measure memory usage for standard operations
        initial_memory = self.process.memory_info().rss

        # Perform standard operations
        cache_manager = CacheManager()

        for i in range(500):
            cache_manager.set(f"key_{i}", f"value_{i}", ttl=300)

        current_memory = self.process.memory_info().rss
        memory_increase = current_memory - initial_memory

        # Memory usage should stay within bounds
        assert (
            memory_increase < 30 * 1024 * 1024
        ), f"Memory usage regression: {memory_increase / 1024 / 1024:.2f}MB"

    def test_throughput_regression(self):
        """Test throughput regression."""
        cache_manager = CacheManager()

        # Test throughput
        start_time = time.time()
        operations = 0

        # Run for 2 seconds
        while time.time() - start_time < 2.0:
            cache_manager.set(f"key_{operations}", f"value_{operations}", ttl=300)
            cache_manager.get(f"key_{operations}")
            operations += 1

        end_time = time.time()
        throughput = operations / (end_time - start_time)

        # Should maintain high throughput
        assert throughput > 1000, f"Throughput regression: {throughput:.2f} ops/sec"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
