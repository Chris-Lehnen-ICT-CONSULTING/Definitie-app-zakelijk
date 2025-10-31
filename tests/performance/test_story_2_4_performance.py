"""
Story 2.4 Performance Test Suite

Performance tests specifically for Story 2.4 interface migration to ensure
the new ValidationOrchestratorV2 layer doesn't introduce significant overhead.

Performance Criteria (from handover document):
- Maximum 5% performance overhead
- Response times comparable to direct calls
- No memory leaks in orchestrator layer
- Efficient batch processing

Test Categories:
1. Single validation performance
2. Batch validation performance
3. Memory usage tests
4. Concurrent validation performance
5. Baseline comparison tests
"""

import asyncio
import gc
import os
import statistics
import time
import uuid
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock

import psutil
import pytest

from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2
from services.validation.interfaces import ValidationContext, ValidationRequest
from services.validation.modular_validation_service import ModularValidationService


class TestStory24PerformanceBaseline:
    """Baseline performance tests for Story 2.4 interface migration."""

    @pytest.fixture
    def fast_mock_validation_service(self):
        """Create fast mock validation service for performance testing."""
        service = Mock()
        service.validate_definition = AsyncMock(
            return_value={
                "version": "1.0.0",
                "overall_score": 0.85,
                "is_acceptable": True,
                "violations": [],
                "passed_rules": ["PERF-TEST-001"],
                "detailed_scores": {"taal": 0.85},
                "system": {
                    "correlation_id": str(uuid.uuid4()),
                    "engine_version": "2.0.0",
                    "duration_ms": 10,  # Simulate fast validation
                },
            }
        )
        return service

    @pytest.fixture
    def performance_orchestrator(self, fast_mock_validation_service):
        """Create orchestrator optimized for performance testing."""
        return ValidationOrchestratorV2(
            validation_service=fast_mock_validation_service,
            cleaning_service=None,  # Disable cleaning for pure validation performance
        )

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_single_validation_performance(self, performance_orchestrator):
        """Test single validation performance meets baseline requirements."""
        # Warm up
        await performance_orchestrator.validate_text("warmup", "warmup text")

        # Performance measurement
        iterations = 100
        execution_times = []

        for _ in range(iterations):
            start_time = time.perf_counter()

            result = await performance_orchestrator.validate_text(
                begrip="performance-test",
                text="Performance test definitie voor Story 2.4 orchestrator.",
                ontologische_categorie="object",
            )

            end_time = time.perf_counter()
            execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
            execution_times.append(execution_time)

            assert result["is_acceptable"] is True

        # Performance analysis
        avg_time = statistics.mean(execution_times)
        statistics.median(execution_times)
        p95_time = sorted(execution_times)[int(0.95 * len(execution_times))]
        p99_time = sorted(execution_times)[int(0.99 * len(execution_times))]

        # Performance thresholds (in milliseconds)
        MAX_AVG_TIME = 50  # 50ms average
        MAX_P95_TIME = 100  # 100ms 95th percentile
        MAX_P99_TIME = 200  # 200ms 99th percentile

        assert (
            avg_time < MAX_AVG_TIME
        ), f"Average validation time {avg_time:.2f}ms exceeds threshold {MAX_AVG_TIME}ms"
        assert (
            p95_time < MAX_P95_TIME
        ), f"P95 validation time {p95_time:.2f}ms exceeds threshold {MAX_P95_TIME}ms"
        assert (
            p99_time < MAX_P99_TIME
        ), f"P99 validation time {p99_time:.2f}ms exceeds threshold {MAX_P99_TIME}ms"

        print(
            f"✅ Single validation performance: avg={avg_time:.2f}ms, p95={p95_time:.2f}ms, p99={p99_time:.2f}ms"
        )

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_batch_validation_performance(self, performance_orchestrator):
        """Test batch validation performance and scalability."""
        batch_sizes = [10, 50, 100, 200]

        for batch_size in batch_sizes:
            # Create batch requests
            requests = [
                ValidationRequest(
                    begrip=f"begrip-{i}",
                    text=f"Definitie nummer {i} voor batch performance test.",
                    ontologische_categorie="object",
                )
                for i in range(batch_size)
            ]

            # Measure batch processing time
            start_time = time.perf_counter()
            results = await performance_orchestrator.batch_validate(requests)
            end_time = time.perf_counter()

            batch_time = (end_time - start_time) * 1000  # milliseconds
            time_per_item = batch_time / batch_size

            # Verify results
            assert len(results) == batch_size
            assert all(result["is_acceptable"] for result in results)

            # Performance thresholds
            MAX_TIME_PER_ITEM = 60  # 60ms per item maximum

            assert (
                time_per_item < MAX_TIME_PER_ITEM
            ), f"Batch size {batch_size}: {time_per_item:.2f}ms per item exceeds {MAX_TIME_PER_ITEM}ms"

            print(
                f"✅ Batch size {batch_size}: {batch_time:.2f}ms total, {time_per_item:.2f}ms per item"
            )

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_validation_performance(self, performance_orchestrator):
        """Test concurrent validation performance under load."""
        concurrency_levels = [5, 10, 20]

        for concurrency in concurrency_levels:
            # Create concurrent tasks
            tasks = [
                performance_orchestrator.validate_text(
                    begrip=f"concurrent-{i}",
                    text=f"Concurrent validation {i} voor performance test.",
                    context=ValidationContext(
                        correlation_id=uuid.uuid4(), metadata={"concurrency_test": True}
                    ),
                )
                for i in range(concurrency)
            ]

            # Measure concurrent execution
            start_time = time.perf_counter()
            results = await asyncio.gather(*tasks)
            end_time = time.perf_counter()

            total_time = (end_time - start_time) * 1000  # milliseconds

            # Verify all succeeded
            assert len(results) == concurrency
            assert all(result["is_acceptable"] for result in results)

            # Performance threshold - concurrent should be faster than sequential
            sequential_estimate = concurrency * 50  # 50ms per validation estimate
            efficiency_ratio = total_time / sequential_estimate

            MAX_EFFICIENCY_RATIO = 0.8  # Should be at least 20% faster than sequential

            assert (
                efficiency_ratio < MAX_EFFICIENCY_RATIO
            ), f"Concurrency {concurrency}: efficiency ratio {efficiency_ratio:.2f} exceeds {MAX_EFFICIENCY_RATIO}"

            print(
                f"✅ Concurrency {concurrency}: {total_time:.2f}ms total, efficiency={efficiency_ratio:.2f}"
            )

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_memory_usage_performance(self, performance_orchestrator):
        """Test memory usage during validation operations."""
        process = psutil.Process(os.getpid())

        # Baseline memory
        gc.collect()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Perform many validations
        iterations = 1000
        for i in range(iterations):
            result = await performance_orchestrator.validate_text(
                begrip=f"memory-test-{i}",
                text=f"Memory test definitie nummer {i} voor geheugen performance analyse.",
                ontologische_categorie="object",
                context=ValidationContext(
                    correlation_id=uuid.uuid4(),
                    profile="memory-test",
                    metadata={"iteration": i},
                ),
            )
            assert result["is_acceptable"] is True

        # Check memory after operations
        gc.collect()
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - baseline_memory

        # Memory thresholds
        MAX_MEMORY_INCREASE = 50  # 50MB maximum increase

        assert (
            memory_increase < MAX_MEMORY_INCREASE
        ), f"Memory increase {memory_increase:.2f}MB exceeds threshold {MAX_MEMORY_INCREASE}MB"

        print(
            f"✅ Memory usage: baseline={baseline_memory:.2f}MB, final={final_memory:.2f}MB, increase={memory_increase:.2f}MB"
        )

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_orchestrator_overhead_measurement(
        self, fast_mock_validation_service
    ):
        """Test that ValidationOrchestratorV2 adds minimal overhead."""

        # Test direct service calls (baseline)
        direct_times = []
        for _ in range(100):
            start_time = time.perf_counter()

            await fast_mock_validation_service.validate_definition(
                begrip="direct-test",
                text="Direct validation test",
                ontologische_categorie="object",
                context=None,
            )

            end_time = time.perf_counter()
            direct_times.append((end_time - start_time) * 1000)

        # Test orchestrator calls
        orchestrator = ValidationOrchestratorV2(fast_mock_validation_service)
        orchestrator_times = []

        for _ in range(100):
            start_time = time.perf_counter()

            await orchestrator.validate_text(
                begrip="orchestrator-test",
                text="Orchestrator validation test",
                ontologische_categorie="object",
            )

            end_time = time.perf_counter()
            orchestrator_times.append((end_time - start_time) * 1000)

        # Calculate overhead
        direct_avg = statistics.mean(direct_times)
        orchestrator_avg = statistics.mean(orchestrator_times)
        overhead_ms = orchestrator_avg - direct_avg
        overhead_percent = (overhead_ms / direct_avg) * 100

        # Performance requirement: <5% overhead
        MAX_OVERHEAD_PERCENT = 5.0

        assert (
            overhead_percent < MAX_OVERHEAD_PERCENT
        ), f"Orchestrator overhead {overhead_percent:.2f}% exceeds {MAX_OVERHEAD_PERCENT}%"

        print(
            f"✅ Orchestrator overhead: {overhead_ms:.2f}ms ({overhead_percent:.2f}%)"
        )


class TestStory24PerformanceRegression:
    """Performance regression tests to ensure no performance degradation."""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_validation_context_conversion_performance(self):
        """Test performance impact of ValidationContext conversion."""
        mock_service = AsyncMock(
            return_value={
                "overall_score": 0.8,
                "is_acceptable": True,
                "violations": [],
                "system": {"correlation_id": str(uuid.uuid4())},
            }
        )

        orchestrator = ValidationOrchestratorV2(mock_service)

        # Test with complex context
        complex_context = ValidationContext(
            correlation_id=uuid.uuid4(),
            profile="performance-test",
            locale="nl-NL",
            trace_parent="complex-trace-parent",
            feature_flags={f"flag_{i}": i % 2 == 0 for i in range(50)},
            metadata={f"key_{i}": f"value_{i}" for i in range(100)},
        )

        # Measure context conversion performance
        conversion_times = []
        for _ in range(100):
            start_time = time.perf_counter()

            await orchestrator.validate_text(
                begrip="context-perf-test",
                text="Context conversion performance test",
                context=complex_context,
            )

            end_time = time.perf_counter()
            conversion_times.append((end_time - start_time) * 1000)

        avg_time = statistics.mean(conversion_times)

        # Context conversion should not add significant overhead
        MAX_CONTEXT_TIME = 30  # 30ms maximum

        assert (
            avg_time < MAX_CONTEXT_TIME
        ), f"Context conversion time {avg_time:.2f}ms exceeds {MAX_CONTEXT_TIME}ms"

        print(f"✅ Context conversion performance: {avg_time:.2f}ms average")

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_error_handling_performance(self):
        """Test performance of error handling paths."""
        # Mock service that fails
        failing_service = AsyncMock(side_effect=Exception("Performance test error"))
        orchestrator = ValidationOrchestratorV2(failing_service)

        # Measure error handling performance
        error_times = []
        for _ in range(50):
            start_time = time.perf_counter()

            result = await orchestrator.validate_text("error-test", "error test")

            end_time = time.perf_counter()
            error_times.append((end_time - start_time) * 1000)

            # Verify degraded result
            assert result["is_acceptable"] is False
            assert "error" in result["system"]

        avg_error_time = statistics.mean(error_times)

        # Error handling should be fast
        MAX_ERROR_TIME = 100  # 100ms maximum for error path

        assert (
            avg_error_time < MAX_ERROR_TIME
        ), f"Error handling time {avg_error_time:.2f}ms exceeds {MAX_ERROR_TIME}ms"

        print(f"✅ Error handling performance: {avg_error_time:.2f}ms average")

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_schema_compliance_performance(self):
        """Test performance impact of schema compliance validation."""
        mock_service = AsyncMock(
            return_value={
                # Minimal response that needs schema compliance
                "overall_score": 0.8,
                "is_acceptable": True,
            }
        )

        orchestrator = ValidationOrchestratorV2(mock_service)

        # Measure schema compliance overhead
        compliance_times = []
        for _ in range(100):
            start_time = time.perf_counter()

            result = await orchestrator.validate_text("schema-test", "schema test")

            end_time = time.perf_counter()
            compliance_times.append((end_time - start_time) * 1000)

            # Verify schema compliance was applied
            assert "version" in result
            assert "system" in result
            assert "correlation_id" in result["system"]

        avg_compliance_time = statistics.mean(compliance_times)

        # Schema compliance should add minimal overhead
        MAX_COMPLIANCE_TIME = 20  # 20ms maximum

        assert (
            avg_compliance_time < MAX_COMPLIANCE_TIME
        ), f"Schema compliance time {avg_compliance_time:.2f}ms exceeds {MAX_COMPLIANCE_TIME}ms"

        print(f"✅ Schema compliance performance: {avg_compliance_time:.2f}ms average")


class TestStory24PerformanceProfiler:
    """Advanced performance profiling for Story 2.4."""

    @pytest.mark.performance
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_comprehensive_performance_profile(self):
        """Comprehensive performance profile of ValidationOrchestratorV2."""

        # Setup realistic mock service with timing simulation
        mock_service = AsyncMock()

        async def realistic_validation(*args, **kwargs):
            # Simulate realistic validation time
            await asyncio.sleep(0.01)  # 10ms simulated processing
            return {
                "version": "1.0.0",
                "overall_score": 0.85,
                "is_acceptable": True,
                "violations": [],
                "passed_rules": ["PROFILE-001"],
                "detailed_scores": {"taal": 0.85, "juridisch": 0.85},
                "system": {
                    "correlation_id": str(uuid.uuid4()),
                    "engine_version": "2.0.0",
                    "duration_ms": 10,
                },
            }

        mock_service.validate_definition = realistic_validation

        orchestrator = ValidationOrchestratorV2(mock_service)

        # Performance scenarios
        scenarios = [
            ("simple_text", "Eenvoudige definitie", None),
            (
                "complex_text",
                "Complexe definitie met veel verschillende woorden en zinsdelen die gevalideerd moeten worden.",
                "object",
            ),
            (
                "with_context",
                "Definitie met context",
                ValidationContext(
                    correlation_id=uuid.uuid4(),
                    profile="advanced",
                    feature_flags={"detailed_analysis": True},
                ),
            ),
        ]

        performance_profile = {}

        for scenario_name, text, context in scenarios:
            times = []

            # Run scenario multiple times
            for _ in range(20):
                start_time = time.perf_counter()

                result = await orchestrator.validate_text(
                    begrip=f"profile-{scenario_name}", text=text, context=context
                )

                end_time = time.perf_counter()
                times.append((end_time - start_time) * 1000)

                assert result["is_acceptable"] is True

            # Calculate statistics
            performance_profile[scenario_name] = {
                "avg": statistics.mean(times),
                "median": statistics.median(times),
                "min": min(times),
                "max": max(times),
                "std": statistics.stdev(times) if len(times) > 1 else 0,
            }

        # Print performance profile
        print("\n" + "=" * 60)
        print("STORY 2.4 PERFORMANCE PROFILE")
        print("=" * 60)

        for scenario, stats in performance_profile.items():
            print(f"\n{scenario.upper()}:")
            print(f"  Average: {stats['avg']:.2f}ms")
            print(f"  Median:  {stats['median']:.2f}ms")
            print(f"  Range:   {stats['min']:.2f}ms - {stats['max']:.2f}ms")
            print(f"  StdDev:  {stats['std']:.2f}ms")

            # Verify performance is acceptable
            assert (
                stats["avg"] < 100
            ), f"Average time for {scenario} too high: {stats['avg']:.2f}ms"
            assert (
                stats["max"] < 200
            ), f"Max time for {scenario} too high: {stats['max']:.2f}ms"

        print("\n" + "=" * 60)
        print("✅ Comprehensive performance profile completed successfully")

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_load_test_simulation(self):
        """Simulate load test conditions for Story 2.4."""

        mock_service = AsyncMock(
            return_value={
                "overall_score": 0.8,
                "is_acceptable": True,
                "violations": [],
                "system": {"correlation_id": str(uuid.uuid4())},
            }
        )

        orchestrator = ValidationOrchestratorV2(mock_service)

        # Simulate high load
        concurrent_users = 10
        requests_per_user = 50

        async def simulate_user(user_id: int):
            """Simulate single user making multiple requests."""
            user_times = []

            for request_id in range(requests_per_user):
                start_time = time.perf_counter()

                result = await orchestrator.validate_text(
                    begrip=f"load-test-user-{user_id}-req-{request_id}",
                    text=f"Load test definitie van gebruiker {user_id}, verzoek {request_id}",
                    context=ValidationContext(
                        correlation_id=uuid.uuid4(),
                        metadata={"user_id": user_id, "request_id": request_id},
                    ),
                )

                end_time = time.perf_counter()
                user_times.append((end_time - start_time) * 1000)

                assert result["is_acceptable"] is True

                # Small delay between requests
                await asyncio.sleep(0.01)

            return user_times

        # Run load test
        print(
            f"\n🚀 Starting load test: {concurrent_users} users, {requests_per_user} requests each"
        )

        start_time = time.perf_counter()

        user_tasks = [simulate_user(user_id) for user_id in range(concurrent_users)]
        user_results = await asyncio.gather(*user_tasks)

        end_time = time.perf_counter()

        # Analyze results
        all_times = [time for user_times in user_results for time in user_times]
        total_requests = len(all_times)
        total_duration = end_time - start_time
        throughput = total_requests / total_duration  # requests per second

        avg_response_time = statistics.mean(all_times)
        p95_response_time = sorted(all_times)[int(0.95 * len(all_times))]

        # Performance assertions
        MIN_THROUGHPUT = 50  # requests per second
        MAX_AVG_RESPONSE_TIME = 100  # milliseconds
        MAX_P95_RESPONSE_TIME = 200  # milliseconds

        assert (
            throughput >= MIN_THROUGHPUT
        ), f"Throughput {throughput:.1f} req/s below minimum {MIN_THROUGHPUT} req/s"
        assert (
            avg_response_time <= MAX_AVG_RESPONSE_TIME
        ), f"Average response time {avg_response_time:.2f}ms above maximum {MAX_AVG_RESPONSE_TIME}ms"
        assert (
            p95_response_time <= MAX_P95_RESPONSE_TIME
        ), f"P95 response time {p95_response_time:.2f}ms above maximum {MAX_P95_RESPONSE_TIME}ms"

        print("✅ Load test completed:")
        print(f"   Total requests: {total_requests}")
        print(f"   Duration: {total_duration:.1f}s")
        print(f"   Throughput: {throughput:.1f} req/s")
        print(f"   Avg response: {avg_response_time:.2f}ms")
        print(f"   P95 response: {p95_response_time:.2f}ms")
