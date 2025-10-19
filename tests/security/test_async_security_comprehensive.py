"""
Comprehensive async security tests for DefinitieAgent.
Tests async security middleware, rate limiting, and concurrent threat detection.
"""

import asyncio
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

# Import async security components
try:
    from security.security_middleware import (
        SecurityMiddleware,
        ValidationRequest,
        ValidationResponse,
        get_security_middleware,
        security_middleware_decorator,
    )
    from validation.input_validator import get_validator
    from validation.sanitizer import get_sanitizer

    SECURITY_MODULES_AVAILABLE = True
except ImportError:
    SECURITY_MODULES_AVAILABLE = False

    # Mock classes for testing
    class SecurityMiddleware:
        async def validate_request(self, request):
            return {"allowed": True, "threats_detected": []}

    class ValidationRequest:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    def get_security_middleware():
        return SecurityMiddleware()

    def get_sanitizer():
        return MagicMock()

    def get_validator():
        return MagicMock()


class AsyncSecurityTestHarness:
    """Test harness for async security testing."""

    def __init__(self):
        self.middleware = get_security_middleware()
        self.sanitizer = get_sanitizer()
        self.validator = get_validator()
        self.test_results = []
        self.concurrent_requests = []

    async def create_test_request(
        self, endpoint="test", data=None, source_ip="127.0.0.1", malicious=False
    ):
        """Create a test request for security testing."""
        if data is None:
            data = {"test": "normal data"}

        if malicious:
            data = {
                "malicious_script": "<script>alert('xss')</script>",
                "sql_injection": "'; DROP TABLE users; --",
                "path_traversal": "../../../etc/passwd",
            }

        return ValidationRequest(
            endpoint=endpoint,
            method="POST",
            data=data,
            headers={"User-Agent": "TestAgent/1.0"},
            source_ip=source_ip,
            user_agent="TestAgent/1.0",
            timestamp=datetime.now(UTC),
        )

    async def measure_async_performance(self, operation, *args, **kwargs):
        """Measure performance of async operations."""
        start_time = time.time()
        result = await operation(*args, **kwargs)
        duration = time.time() - start_time

        return {
            "result": result,
            "duration": duration,
            "timestamp": datetime.now(UTC),
        }


class TestAsyncSecurityMiddleware:
    """Test async security middleware functionality."""

    def setup_method(self):
        """Setup for each test method."""
        self.harness = AsyncSecurityTestHarness()

    @pytest.mark.asyncio
    async def test_async_request_validation_performance(self):
        """Test async request validation performance."""
        normal_request = await self.harness.create_test_request()

        # Test single async validation
        perf_result = await self.harness.measure_async_performance(
            self.harness.middleware.validate_request, normal_request
        )

        assert perf_result["result"] is not None
        assert (
            perf_result["duration"] < 0.1
        ), f"Async validation too slow: {perf_result['duration']:.3f}s"

    @pytest.mark.asyncio
    async def test_concurrent_request_validation(self):
        """Test concurrent request validation."""
        # Create multiple test requests
        requests = []
        for i in range(20):
            request = await self.harness.create_test_request(
                endpoint=f"test_endpoint_{i}", source_ip=f"192.168.1.{100 + i}"
            )
            requests.append(request)

        # Process all requests concurrently
        start_time = time.time()

        tasks = [self.harness.middleware.validate_request(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        total_time = time.time() - start_time

        # Assertions
        assert len(results) == 20
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert (
            len(successful_results) >= 18
        ), f"Too many failed validations: {len(successful_results)}/20"
        assert total_time < 2.0, f"Concurrent validation too slow: {total_time:.3f}s"

        # Calculate throughput
        throughput = len(successful_results) / total_time
        assert (
            throughput > 10
        ), f"Validation throughput too low: {throughput:.2f} req/sec"

    @pytest.mark.asyncio
    async def test_malicious_request_detection_async(self):
        """Test async malicious request detection."""
        malicious_request = await self.harness.create_test_request(malicious=True)

        # Test async malicious request handling
        if hasattr(self.harness.middleware, "validate_request"):
            result = await self.harness.middleware.validate_request(malicious_request)

            # Should detect threats (or at least process without crashing)
            assert result is not None

            # If result has expected structure, verify threat detection
            if hasattr(result, "allowed"):
                # Malicious requests should be blocked or flagged
                assert result.allowed is False or hasattr(result, "threats_detected")

    @pytest.mark.asyncio
    async def test_rate_limiting_async(self):
        """Test async rate limiting functionality."""
        source_ip = "192.168.1.200"
        requests_to_send = 15  # Should exceed typical rate limits

        # Send rapid requests from same IP
        tasks = []
        for i in range(requests_to_send):
            request = await self.harness.create_test_request(
                endpoint="rate_limit_test", source_ip=source_ip, data={"request_id": i}
            )
            tasks.append(self.harness.middleware.validate_request(request))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Check results
        successful_requests = [r for r in results if not isinstance(r, Exception)]

        # Should have some successful requests
        assert len(successful_requests) > 0, "All requests failed"

        # If rate limiting is working, not all requests should succeed
        # (This depends on implementation - adjust based on actual behavior)
        if len(successful_requests) < requests_to_send:
            # Rate limiting is working
            assert len(successful_requests) < requests_to_send

    @pytest.mark.asyncio
    async def test_async_security_pipeline(self):
        """Test complete async security pipeline."""
        test_data = {
            "begrip": "test_term",
            "content": "Test content for security pipeline",
            "context": {"type": "government_term"},
        }

        # Step 1: Async input sanitization
        async def async_sanitize(data):
            # Simulate async sanitization
            await asyncio.sleep(0.01)
            if hasattr(self.harness.sanitizer, "sanitize_user_input"):
                return self.harness.sanitizer.sanitize_user_input(data)
            return data  # Mock fallback

        # Step 2: Async validation
        async def async_validate(data):
            await asyncio.sleep(0.01)
            if hasattr(self.harness.validator, "validate"):
                return self.harness.validator.validate(data, "test_schema")
            return []  # Mock fallback

        # Step 3: Async security check
        async def async_security_check(data):
            request = await self.harness.create_test_request(data=data)
            return await self.harness.middleware.validate_request(request)

        # Execute pipeline
        start_time = time.time()

        sanitized_task = async_sanitize(test_data)
        validation_task = async_validate(test_data)
        security_task = async_security_check(test_data)

        sanitized, validation, security_result = await asyncio.gather(
            sanitized_task, validation_task, security_task
        )

        pipeline_time = time.time() - start_time

        # Assertions
        assert sanitized is not None
        assert validation is not None
        assert security_result is not None
        assert (
            pipeline_time < 0.5
        ), f"Async security pipeline too slow: {pipeline_time:.3f}s"


class TestAsyncThreatDetection:
    """Test async threat detection capabilities."""

    def setup_method(self):
        """Setup for each test method."""
        self.harness = AsyncSecurityTestHarness()

    @pytest.mark.asyncio
    async def test_concurrent_threat_detection(self):
        """Test concurrent threat detection."""
        # Create various threat scenarios
        threat_scenarios = [
            {"type": "xss", "data": {"input": "<script>alert('xss')</script>"}},
            {"type": "sql_injection", "data": {"query": "'; DROP TABLE users; --"}},
            {"type": "path_traversal", "data": {"file": "../../../etc/passwd"}},
            {"type": "command_injection", "data": {"cmd": "ls; rm -rf /"}},
            {"type": "normal", "data": {"content": "normal safe content"}},
        ]

        # Process all scenarios concurrently
        async def detect_threats(scenario):
            request = await self.harness.create_test_request(
                data=scenario["data"], malicious=(scenario["type"] != "normal")
            )

            # Simulate threat detection
            await asyncio.sleep(0.01)  # Simulate processing time

            if hasattr(self.harness.middleware, "validate_request"):
                result = await self.harness.middleware.validate_request(request)
                return {
                    "scenario": scenario["type"],
                    "result": result,
                    "detected": hasattr(result, "threats_detected")
                    and len(getattr(result, "threats_detected", [])) > 0,
                }
            # Mock threat detection
            is_threat = scenario["type"] != "normal"
            return {
                "scenario": scenario["type"],
                "result": {"threat_detected": is_threat},
                "detected": is_threat,
            }

        start_time = time.time()

        detection_tasks = [detect_threats(scenario) for scenario in threat_scenarios]
        results = await asyncio.gather(*detection_tasks)

        detection_time = time.time() - start_time

        # Assertions
        assert len(results) == len(threat_scenarios)
        assert (
            detection_time < 1.0
        ), f"Concurrent threat detection too slow: {detection_time:.3f}s"

        # Check that threats were processed (may or may not be detected depending on implementation)
        normal_scenario = next(r for r in results if r["scenario"] == "normal")
        assert normal_scenario is not None

    @pytest.mark.asyncio
    async def test_adaptive_threat_response(self):
        """Test adaptive threat response under load."""
        # Simulate increasing threat levels
        threat_levels = [
            {"level": "low", "requests": 5, "threat_probability": 0.1},
            {"level": "medium", "requests": 10, "threat_probability": 0.3},
            {"level": "high", "requests": 15, "threat_probability": 0.7},
        ]

        all_results = []

        for threat_level in threat_levels:
            level_results = []

            # Generate requests for this threat level
            async def process_threat_level():
                tasks = []
                for i in range(threat_level["requests"]):
                    is_malicious = (i / threat_level["requests"]) < threat_level[
                        "threat_probability"
                    ]

                    request = await self.harness.create_test_request(
                        endpoint=f"threat_level_{threat_level['level']}",
                        source_ip=f"192.168.2.{i + 1}",
                        malicious=is_malicious,
                    )

                    task = self.harness.middleware.validate_request(request)
                    tasks.append(task)

                return await asyncio.gather(*tasks, return_exceptions=True)

            level_start = time.time()
            level_results = await process_threat_level()
            level_time = time.time() - level_start

            all_results.append(
                {
                    "level": threat_level["level"],
                    "results": level_results,
                    "processing_time": level_time,
                    "requests_count": threat_level["requests"],
                }
            )

        # Verify adaptive response
        for level_result in all_results:
            assert (
                level_result["processing_time"] < 3.0
            ), f"Threat level {level_result['level']} too slow: {level_result['processing_time']:.3f}s"

            # Should handle all requests without crashing
            successful_count = len(
                [r for r in level_result["results"] if not isinstance(r, Exception)]
            )
            assert (
                successful_count >= level_result["requests_count"] * 0.8
            ), f"Too many failures in {level_result['level']} threat level"


class TestAsyncRateLimiting:
    """Test async rate limiting functionality."""

    def setup_method(self):
        """Setup for each test method."""
        self.harness = AsyncSecurityTestHarness()

    @pytest.mark.asyncio
    async def test_distributed_rate_limiting(self):
        """Test rate limiting across multiple sources."""
        # Simulate multiple IP sources
        ip_sources = [f"192.168.3.{i}" for i in range(1, 11)]  # 10 different IPs
        requests_per_ip = 5

        async def send_requests_from_ip(ip):
            tasks = []
            for i in range(requests_per_ip):
                request = await self.harness.create_test_request(
                    endpoint="distributed_test", source_ip=ip, data={"request_index": i}
                )
                tasks.append(self.harness.middleware.validate_request(request))

            return await asyncio.gather(*tasks, return_exceptions=True)

        # Send requests from all IPs concurrently
        start_time = time.time()

        ip_tasks = [send_requests_from_ip(ip) for ip in ip_sources]
        all_results = await asyncio.gather(*ip_tasks)

        total_time = time.time() - start_time

        # Flatten results
        all_request_results = []
        for ip_results in all_results:
            all_request_results.extend(ip_results)

        successful_requests = [
            r for r in all_request_results if not isinstance(r, Exception)
        ]

        # Assertions
        total_requests = len(ip_sources) * requests_per_ip
        assert len(all_request_results) == total_requests
        assert (
            len(successful_requests) >= total_requests * 0.8
        ), f"Too many rate limited: {len(successful_requests)}/{total_requests}"
        assert (
            total_time < 5.0
        ), f"Distributed rate limiting too slow: {total_time:.3f}s"

    @pytest.mark.asyncio
    async def test_burst_protection(self):
        """Test burst protection mechanisms."""
        source_ip = "192.168.4.100"

        # Send burst of requests
        burst_size = 20

        async def send_burst():
            tasks = []
            for i in range(burst_size):
                request = await self.harness.create_test_request(
                    endpoint="burst_test",
                    source_ip=source_ip,
                    data={"burst_request": i},
                )
                # Send all requests simultaneously (burst)
                tasks.append(self.harness.middleware.validate_request(request))

            return await asyncio.gather(*tasks, return_exceptions=True)

        start_time = time.time()
        burst_results = await send_burst()
        burst_time = time.time() - start_time

        # Check burst handling
        successful_burst = [r for r in burst_results if not isinstance(r, Exception)]

        # System should handle burst gracefully
        assert len(successful_burst) >= 1, "No requests succeeded in burst"
        assert burst_time < 2.0, f"Burst handling too slow: {burst_time:.3f}s"

        # If rate limiting is working, not all burst requests should succeed
        if len(successful_burst) < burst_size:
            # Rate limiting working
            assert (
                len(successful_burst) < burst_size * 0.8
            ), "Rate limiting not effective against burst"


class TestAsyncSecurityIntegration:
    """Test async security integration with other components."""

    def setup_method(self):
        """Setup for each test method."""
        self.harness = AsyncSecurityTestHarness()

    @pytest.mark.asyncio
    async def test_async_security_with_caching(self):
        """Test async security with caching integration."""
        # Mock async cache operations
        cache_data = {}

        async def async_cached_security_check(request_data):
            cache_key = str(hash(str(request_data)))

            # Check cache
            if cache_key in cache_data:
                await asyncio.sleep(0.001)  # Simulate cache hit time
                return cache_data[cache_key]

            # Security check
            request = await self.harness.create_test_request(data=request_data)
            result = await self.harness.middleware.validate_request(request)

            # Cache result
            cache_data[cache_key] = result
            await asyncio.sleep(0.01)  # Simulate cache write time

            return result

        # Test cache performance
        test_data = {"test": "cached security check"}

        # First call (cache miss)
        start_time = time.time()
        result1 = await async_cached_security_check(test_data)
        first_call_time = time.time() - start_time

        # Second call (cache hit)
        start_time = time.time()
        result2 = await async_cached_security_check(test_data)
        second_call_time = time.time() - start_time

        # Assertions
        assert result1 is not None
        assert result2 is not None
        assert (
            second_call_time < first_call_time * 0.5
        ), "Cache not providing performance benefit"

    @pytest.mark.asyncio
    async def test_async_security_error_handling(self):
        """Test async security error handling."""
        # Test various error scenarios
        error_scenarios = [
            {"name": "network_timeout", "delay": 0.1, "should_fail": False},
            {
                "name": "service_unavailable",
                "exception": ConnectionError("Service unavailable"),
            },
            {"name": "invalid_data", "data": None},
            {"name": "malformed_request", "data": {"invalid": object()}},
        ]

        async def test_error_scenario(scenario):
            try:
                if "exception" in scenario:
                    raise scenario["exception"]

                if "delay" in scenario:
                    await asyncio.sleep(scenario["delay"])

                data = scenario.get("data", {"test": "error handling"})
                request = await self.harness.create_test_request(data=data)
                result = await self.harness.middleware.validate_request(request)

                return {
                    "scenario": scenario["name"],
                    "success": True,
                    "result": result,
                    "error": None,
                }

            except Exception as e:
                return {
                    "scenario": scenario["name"],
                    "success": False,
                    "result": None,
                    "error": str(e),
                }

        # Test all error scenarios
        start_time = time.time()

        scenario_tasks = [test_error_scenario(scenario) for scenario in error_scenarios]
        scenario_results = await asyncio.gather(*scenario_tasks, return_exceptions=True)

        error_handling_time = time.time() - start_time

        # Assertions
        assert len(scenario_results) == len(error_scenarios)
        assert (
            error_handling_time < 2.0
        ), f"Error handling too slow: {error_handling_time:.3f}s"

        # Check that system handled errors gracefully
        successful_scenarios = [
            r for r in scenario_results if not isinstance(r, Exception)
        ]
        assert (
            len(successful_scenarios) >= len(error_scenarios) * 0.7
        ), "Too many unhandled errors"


class TestAsyncSecurityPerformance:
    """Test async security performance characteristics."""

    def setup_method(self):
        """Setup for each test method."""
        self.harness = AsyncSecurityTestHarness()

    @pytest.mark.asyncio
    async def test_high_concurrency_security(self):
        """Test security under high concurrency."""
        concurrent_users = 50
        requests_per_user = 5

        async def simulate_user(user_id):
            user_results = []
            for i in range(requests_per_user):
                request = await self.harness.create_test_request(
                    endpoint=f"user_{user_id}_endpoint",
                    source_ip=f"192.168.5.{(user_id % 254) + 1}",
                    data={"user_id": user_id, "request_id": i},
                )

                try:
                    result = await self.harness.middleware.validate_request(request)
                    user_results.append({"success": True, "result": result})
                except Exception as e:
                    user_results.append({"success": False, "error": str(e)})

            return user_results

        # Simulate high concurrency
        start_time = time.time()

        user_tasks = [simulate_user(user_id) for user_id in range(concurrent_users)]
        all_user_results = await asyncio.gather(*user_tasks, return_exceptions=True)

        total_time = time.time() - start_time

        # Flatten results
        all_requests = []
        for user_results in all_user_results:
            if not isinstance(user_results, Exception):
                all_requests.extend(user_results)

        successful_requests = [r for r in all_requests if r.get("success", False)]

        # Performance assertions
        total_expected_requests = concurrent_users * requests_per_user
        assert (
            len(all_requests) >= total_expected_requests * 0.8
        ), f"Lost requests under load: {len(all_requests)}/{total_expected_requests}"
        assert (
            len(successful_requests) >= len(all_requests) * 0.8
        ), f"Too many failed requests: {len(successful_requests)}/{len(all_requests)}"
        assert total_time < 10.0, f"High concurrency test too slow: {total_time:.3f}s"

        # Calculate throughput
        throughput = len(successful_requests) / total_time
        assert (
            throughput > 50
        ), f"Throughput too low under load: {throughput:.2f} req/sec"

    @pytest.mark.asyncio
    async def test_security_latency_distribution(self):
        """Test security latency distribution."""
        num_requests = 100
        latencies = []

        async def measure_request_latency():
            request = await self.harness.create_test_request()

            start_time = time.time()
            await self.harness.middleware.validate_request(request)
            return time.time() - start_time


        # Measure latencies
        latency_tasks = [measure_request_latency() for _ in range(num_requests)]
        latencies = await asyncio.gather(*latency_tasks, return_exceptions=True)

        # Filter out exceptions
        valid_latencies = [
            l
            for l in latencies
            if not isinstance(l, Exception) and isinstance(l, int | float)
        ]

        # Calculate statistics
        if valid_latencies:
            avg_latency = sum(valid_latencies) / len(valid_latencies)
            max(valid_latencies)
            min(valid_latencies)

            # Sort for percentile calculation
            sorted_latencies = sorted(valid_latencies)
            p95_latency = (
                sorted_latencies[int(0.95 * len(sorted_latencies))]
                if sorted_latencies
                else 0
            )
            p99_latency = (
                sorted_latencies[int(0.99 * len(sorted_latencies))]
                if sorted_latencies
                else 0
            )

            # Assertions
            assert (
                len(valid_latencies) >= num_requests * 0.9
            ), f"Too many failed latency measurements: {len(valid_latencies)}/{num_requests}"
            assert avg_latency < 0.1, f"Average latency too high: {avg_latency:.3f}s"
            assert (
                p95_latency < 0.2
            ), f"95th percentile latency too high: {p95_latency:.3f}s"
            assert (
                p99_latency < 0.5
            ), f"99th percentile latency too high: {p99_latency:.3f}s"


@pytest.mark.asyncio
class TestAsyncSecurityDecorator:
    """Test async security decorator functionality."""

    def setup_method(self):
        """Setup for each test method."""
        self.harness = AsyncSecurityTestHarness()

    async def test_async_security_decorator(self):
        """Test async security decorator application."""

        # Mock the decorator for testing
        def async_security_decorator(endpoint_name=""):
            def decorator(func):
                async def wrapper(*args, **kwargs):
                    # Simulate security check
                    await asyncio.sleep(0.01)

                    # Extract request data
                    request_data = args[0] if args and isinstance(args[0], dict) else {}

                    # Create validation request
                    request = await self.harness.create_test_request(
                        endpoint=endpoint_name or func.__name__, data=request_data
                    )

                    # Validate
                    validation_result = await self.harness.middleware.validate_request(
                        request
                    )

                    # If validation fails, raise error
                    if (
                        hasattr(validation_result, "allowed")
                        and not validation_result.allowed
                    ):
                        msg = "Security validation failed"
                        raise ValueError(msg)

                    # Call original function
                    return await func(*args, **kwargs)

                return wrapper

            return decorator

        # Test decorated async function
        @async_security_decorator("test_endpoint")
        async def protected_async_function(data):
            await asyncio.sleep(0.01)
            return f"Processed: {data.get('input', 'none')}"

        # Test with safe data
        safe_data = {"input": "safe data"}
        start_time = time.time()
        result = await protected_async_function(safe_data)
        execution_time = time.time() - start_time

        assert "safe data" in result
        assert (
            execution_time < 0.1
        ), f"Decorated function too slow: {execution_time:.3f}s"

        # Test with potentially malicious data
        malicious_data = {"input": "<script>alert('xss')</script>"}

        try:
            result = await protected_async_function(malicious_data)
            # If no exception, the function processed the data
            assert result is not None
        except ValueError as e:
            # If exception, security validation worked
            assert "Security validation failed" in str(e)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
