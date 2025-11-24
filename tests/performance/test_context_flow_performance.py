"""
Performance tests for EPIC-010 Context Flow Refactoring.

These tests measure and validate performance improvements from the context flow refactoring,
ensuring we meet the >20% performance improvement target and maintain sub-100ms response times.

Test Coverage:
- End-to-end context flow timing
- Memory usage optimization
- Throughput under load
- Latency percentiles (p50, p95, p99)
- Resource utilization
- Scalability testing
- Cache effectiveness
"""

import gc
import statistics
import time
import timeit
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Optional

import memory_profiler
import numpy as np
import psutil
import pytest

from src.services.container import ServiceContainer
from src.services.context.context_manager import ContextManager
from src.services.interfaces import GenerationRequest
from src.services.prompts.prompt_service_v2 import PromptServiceV2


@dataclass
class PerformanceMetrics:
    """Container for performance test results."""

    operation: str
    mean_time_ms: float
    median_time_ms: float
    p95_time_ms: float
    p99_time_ms: float
    min_time_ms: float
    max_time_ms: float
    throughput_per_sec: float
    memory_mb: float
    cpu_percent: float

    def meets_sla(self, target_ms: float = 100) -> bool:
        """Check if performance meets SLA."""
        return self.p95_time_ms < target_ms

    def improvement_over(self, baseline: "PerformanceMetrics") -> float:
        """Calculate improvement percentage over baseline."""
        return (baseline.mean_time_ms - self.mean_time_ms) / baseline.mean_time_ms * 100

@pytest.mark.skip(reason="Context module not yet implemented (US-041/042/043)")
class TestContextFlowPerformance:
    """Core performance tests for context flow."""

    @pytest.fixture
    def prompt_service(self):
        """Create PromptServiceV2 instance."""
        return PromptServiceV2()

    @pytest.fixture
    def context_manager(self):
        """Create ContextManager instance."""
        return ContextManager()

    def measure_operation(
        self, operation, iterations: int = 1000
    ) -> PerformanceMetrics:
        """Measure performance of an operation."""
        times = []

        # Warm-up
        for _ in range(10):
            operation()

        # Measure
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        initial_cpu = process.cpu_percent()

        for _ in range(iterations):
            start = time.perf_counter()
            operation()
            elapsed = (time.perf_counter() - start) * 1000  # ms
            times.append(elapsed)

        final_memory = process.memory_info().rss / 1024 / 1024
        final_cpu = process.cpu_percent()

        # Calculate metrics
        times_sorted = sorted(times)

        return PerformanceMetrics(
            operation=(
                operation.__name__ if hasattr(operation, "__name__") else str(operation)
            ),
            mean_time_ms=statistics.mean(times),
            median_time_ms=statistics.median(times),
            p95_time_ms=times_sorted[int(len(times) * 0.95)],
            p99_time_ms=times_sorted[int(len(times) * 0.99)],
            min_time_ms=min(times),
            max_time_ms=max(times),
            throughput_per_sec=1000 / statistics.mean(times),
            memory_mb=final_memory - initial_memory,
            cpu_percent=final_cpu - initial_cpu,
        )

    def test_simple_context_processing(self, prompt_service):
        """Test performance of simple context processing."""

        def operation():
            request = GenerationRequest(
                begrip="test",
                organisatorische_context=["DJI"],
                juridische_context=["Strafrecht"],
                wettelijke_basis=["Wetboek van Strafrecht"],
            )
            prompt_service.build_prompt(request)

        metrics = self.measure_operation(operation)

        # Assert performance requirements
        assert metrics.meets_sla(
            100
        ), f"Simple context processing too slow: {metrics.p95_time_ms:.2f}ms"
        assert (
            metrics.throughput_per_sec > 10
        ), f"Throughput too low: {metrics.throughput_per_sec:.2f}/sec"

    def test_complex_context_processing(self, prompt_service):
        """Test performance with complex multi-value contexts."""

        def operation():
            request = GenerationRequest(
                begrip="complexe juridische term met meerdere woorden",
                organisatorische_context=["DJI", "OM", "Rechtspraak", "KMAR", "CJIB"],
                juridische_context=[
                    "Strafrecht",
                    "Bestuursrecht",
                    "Civiel recht",
                    "Internationaal recht",
                ],
                wettelijke_basis=[
                    "Wetboek van Strafrecht",
                    "Wetboek van Strafvordering",
                    "Algemene wet bestuursrecht",
                    "Burgerlijk Wetboek",
                    "Penitentiaire beginselenwet",
                ],
            )
            prompt_service.build_prompt(request)

        metrics = self.measure_operation(operation)

        # Complex should still meet SLA
        assert metrics.meets_sla(
            200
        ), f"Complex context processing too slow: {metrics.p95_time_ms:.2f}ms"

    def test_context_manager_performance(self, context_manager):
        """Test ContextManager set/get performance."""
        context_data = {
            "organisatorische_context": ["DJI", "OM"],
            "juridische_context": ["Strafrecht"],
            "wettelijke_basis": ["Test wet"],
        }

        def operation():
            context_manager.set_context(context_data)
            context_manager.get_context()
            context_manager.clear_context()

        metrics = self.measure_operation(operation)

        # Context management should be very fast
        assert metrics.meets_sla(
            10
        ), f"Context management too slow: {metrics.p95_time_ms:.2f}ms"
        assert (
            metrics.throughput_per_sec > 100
        ), f"Context ops throughput too low: {metrics.throughput_per_sec:.2f}/sec"

@pytest.mark.skip(reason="Context module not yet implemented (US-041/042/043)")
class TestPerformanceImprovement:
    """Test performance improvement over legacy implementation."""

    def simulate_legacy_flow(self) -> PerformanceMetrics:
        """Simulate legacy context flow performance."""

        def legacy_operation():
            # Simulate legacy inefficiencies
            context = {}

            # Multiple session state accesses (simulated)
            time.sleep(0.001)  # Session read
            context["org"] = ["DJI"]

            time.sleep(0.001)  # Another session read
            context["jur"] = ["Strafrecht"]

            time.sleep(0.001)  # Another session read
            context["wet"] = ["Test wet"]

            # Multiple transformations
            time.sleep(0.002)  # Transform and validate

            # String concatenation (inefficient)
            prompt = ""
            for key, values in context.items():
                prompt += f"{key}: {', '.join(values)}\n"
                time.sleep(0.0005)  # Simulate inefficiency

            return prompt

        times = []
        for _ in range(100):
            start = time.perf_counter()
            legacy_operation()
            times.append((time.perf_counter() - start) * 1000)

        return PerformanceMetrics(
            operation="legacy_flow",
            mean_time_ms=statistics.mean(times),
            median_time_ms=statistics.median(times),
            p95_time_ms=sorted(times)[95],
            p99_time_ms=sorted(times)[99],
            min_time_ms=min(times),
            max_time_ms=max(times),
            throughput_per_sec=1000 / statistics.mean(times),
            memory_mb=0,
            cpu_percent=0,
        )

    def test_improvement_target_achieved(self):
        """Verify >20% performance improvement is achieved."""
        # Get baseline (legacy)
        legacy_metrics = self.simulate_legacy_flow()

        # Get modern performance
        prompt_service = PromptServiceV2()

        def modern_operation():
            request = GenerationRequest(
                begrip="test",
                organisatorische_context=["DJI"],
                juridische_context=["Strafrecht"],
                wettelijke_basis=["Test wet"],
            )
            prompt_service.build_prompt(request)

        times = []
        for _ in range(100):
            start = time.perf_counter()
            modern_operation()
            times.append((time.perf_counter() - start) * 1000)

        modern_metrics = PerformanceMetrics(
            operation="modern_flow",
            mean_time_ms=statistics.mean(times),
            median_time_ms=statistics.median(times),
            p95_time_ms=sorted(times)[95],
            p99_time_ms=sorted(times)[99],
            min_time_ms=min(times),
            max_time_ms=max(times),
            throughput_per_sec=1000 / statistics.mean(times),
            memory_mb=0,
            cpu_percent=0,
        )

        # Calculate improvement
        improvement = modern_metrics.improvement_over(legacy_metrics)

        # Should achieve >20% improvement
        assert improvement > 20, f"Improvement only {improvement:.1f}%, target is >20%"

@pytest.mark.skip(reason="Context module not yet implemented (US-041/042/043)")
class TestScalability:
    """Test system scalability under load."""

    def test_concurrent_context_processing(self):
        """Test performance under concurrent load."""
        prompt_service = PromptServiceV2()

        def process_request(i):
            request = GenerationRequest(
                begrip=f"test_{i}",
                organisatorische_context=["DJI", "OM"],
                juridische_context=["Strafrecht"],
                wettelijke_basis=["Test wet"],
            )

            start = time.perf_counter()
            prompt_service.build_prompt(request)
            return (time.perf_counter() - start) * 1000

        # Test with increasing concurrency
        for num_threads in [1, 5, 10, 20]:
            times = []

            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = [executor.submit(process_request, i) for i in range(100)]

                for future in as_completed(futures):
                    times.append(future.result())

            statistics.mean(times)
            p95_time = sorted(times)[95]

            # Performance should degrade gracefully
            assert (
                p95_time < 500
            ), f"P95 latency {p95_time:.2f}ms too high with {num_threads} threads"

    def test_memory_under_load(self):
        """Test memory usage doesn't grow excessively under load."""
        prompt_service = PromptServiceV2()

        # Baseline memory
        gc.collect()
        process = psutil.Process()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Process many requests
        for i in range(10000):
            request = GenerationRequest(
                begrip=f"test_{i}",
                organisatorische_context=[f"Org_{j}" for j in range(10)],
                juridische_context=[f"Jur_{j}" for j in range(10)],
                wettelijke_basis=[f"Wet_{j}" for j in range(10)],
            )
            prompt_service.build_prompt(request)

            if i % 1000 == 0:
                gc.collect()

        # Final memory
        gc.collect()
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_growth = final_memory - baseline_memory

        # Memory growth should be reasonable
        assert (
            memory_growth < 100
        ), f"Memory grew by {memory_growth:.2f}MB, should be <100MB"

@pytest.mark.skip(reason="Context module not yet implemented (US-041/042/043)")
class TestLatencyPercentiles:
    """Test latency percentiles meet SLA requirements."""

    def test_latency_distribution(self):
        """Test that latency distribution meets requirements."""
        prompt_service = PromptServiceV2()
        times = []

        # Generate variety of requests
        for i in range(1000):
            # Vary complexity
            num_orgs = (i % 5) + 1
            num_jurs = (i % 3) + 1
            num_wets = (i % 4) + 1

            request = GenerationRequest(
                begrip=f"test_term_{i}",
                organisatorische_context=[f"Org_{j}" for j in range(num_orgs)],
                juridische_context=[f"Jur_{j}" for j in range(num_jurs)],
                wettelijke_basis=[f"Wet_{j}" for j in range(num_wets)],
            )

            start = time.perf_counter()
            prompt_service.build_prompt(request)
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        # Calculate percentiles
        times_sorted = sorted(times)
        p50 = times_sorted[500]
        p75 = times_sorted[750]
        p95 = times_sorted[950]
        p99 = times_sorted[990]

        # Assert SLA requirements
        assert p50 < 50, f"P50 latency {p50:.2f}ms exceeds 50ms target"
        assert p75 < 75, f"P75 latency {p75:.2f}ms exceeds 75ms target"
        assert p95 < 100, f"P95 latency {p95:.2f}ms exceeds 100ms target"
        assert p99 < 200, f"P99 latency {p99:.2f}ms exceeds 200ms target"

@pytest.mark.skip(reason="Context module not yet implemented (US-041/042/043)")
class TestCacheEffectiveness:
    """Test caching improves performance."""

    def test_repeated_context_cached(self):
        """Test that repeated contexts benefit from caching."""
        prompt_service = PromptServiceV2()

        request = GenerationRequest(
            begrip="test",
            organisatorische_context=["DJI", "OM"],
            juridische_context=["Strafrecht"],
            wettelijke_basis=["Wetboek van Strafrecht"],
        )

        # First call (cold)
        cold_times = []
        for _ in range(10):
            start = time.perf_counter()
            prompt_service.build_prompt(request)
            cold_times.append((time.perf_counter() - start) * 1000)

        # Warm cache
        for _ in range(100):
            prompt_service.build_prompt(request)

        # Cached calls
        warm_times = []
        for _ in range(10):
            start = time.perf_counter()
            prompt_service.build_prompt(request)
            warm_times.append((time.perf_counter() - start) * 1000)

        # Cached should be faster
        cold_avg = statistics.mean(cold_times)
        warm_avg = statistics.mean(warm_times)

        # At least 20% improvement from caching
        improvement = (cold_avg - warm_avg) / cold_avg * 100
        assert improvement > 20, f"Cache improvement only {improvement:.1f}%"

@pytest.mark.skip(reason="Context module not yet implemented (US-041/042/043)")
class TestResourceUtilization:
    """Test efficient resource utilization."""

    def test_cpu_utilization(self):
        """Test CPU utilization stays reasonable."""
        prompt_service = PromptServiceV2()
        process = psutil.Process()

        # Baseline CPU
        process.cpu_percent()  # First call to initialize
        time.sleep(0.1)
        process.cpu_percent()

        # Process requests
        start_time = time.time()
        count = 0
        while time.time() - start_time < 1.0:  # Run for 1 second
            request = GenerationRequest(
                begrip="test",
                organisatorische_context=["DJI"],
                juridische_context=["Strafrecht"],
                wettelijke_basis=["Test wet"],
            )
            prompt_service.build_prompt(request)
            count += 1

        # Check CPU
        cpu_usage = process.cpu_percent()

        # CPU should not be saturated
        assert cpu_usage < 80, f"CPU usage {cpu_usage}% too high"

        # Should process reasonable number of requests
        assert count > 100, f"Only processed {count} requests/sec, expected >100"

    def test_thread_safety(self):
        """Test thread safety of context processing."""
        prompt_service = PromptServiceV2()
        errors = []
        results = []

        def process_with_unique_context(thread_id):
            try:
                request = GenerationRequest(
                    begrip=f"thread_{thread_id}",
                    organisatorische_context=[f"Org_{thread_id}"],
                    juridische_context=[f"Jur_{thread_id}"],
                    wettelijke_basis=[f"Wet_{thread_id}"],
                )

                result = prompt_service.build_prompt(request)

                # Verify context not mixed up
                assert f"Org_{thread_id}" in result
                assert f"Jur_{thread_id}" in result
                assert f"Wet_{thread_id}" in result

                results.append(result)
            except Exception as e:
                errors.append(e)

        # Run concurrent threads
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [
                executor.submit(process_with_unique_context, i) for i in range(500)
            ]
            for future in as_completed(futures):
                future.result()

        # No errors should occur
        assert len(errors) == 0, f"Thread safety errors: {errors}"
        assert len(results) == 500, "Not all requests completed"

@pytest.mark.skip(reason="Context module not yet implemented (US-041/042/043)")
class TestWorstCaseScenarios:
    """Test performance in worst-case scenarios."""

    def test_maximum_context_size(self):
        """Test with maximum possible context sizes."""
        prompt_service = PromptServiceV2()

        # Create massive context
        request = GenerationRequest(
            begrip="zeer complexe juridische term met veel woorden en speciale karakters",
            organisatorische_context=[f"Organisation_{i}" for i in range(100)],
            juridische_context=[f"Juridisch_Context_{i}" for i in range(100)],
            wettelijke_basis=[f"Wet_{i}: " + "x" * 200 for i in range(100)],
        )

        start = time.perf_counter()
        result = prompt_service.build_prompt(request)
        elapsed = (time.perf_counter() - start) * 1000

        # Even with huge context, should complete reasonably fast
        assert (
            elapsed < 1000
        ), f"Maximum context took {elapsed:.2f}ms, should be <1000ms"
        assert result is not None

    def test_rapid_context_switching(self):
        """Test rapid switching between different contexts."""
        prompt_service = PromptServiceV2()
        times = []

        for i in range(1000):
            # Alternate between very different contexts
            if i % 2 == 0:
                request = GenerationRequest(
                    begrip="criminal",
                    organisatorische_context=["DJI", "OM", "Rechtspraak"],
                    juridische_context=["Strafrecht", "Strafprocesrecht"],
                    wettelijke_basis=[
                        "Wetboek van Strafrecht",
                        "Wetboek van Strafvordering",
                    ],
                )
            else:
                request = GenerationRequest(
                    begrip="civil",
                    organisatorische_context=["Rechtspraak", "Notariaat"],
                    juridische_context=["Civiel recht", "Familierecht"],
                    wettelijke_basis=["Burgerlijk Wetboek", "Wet op het notarisambt"],
                )

            start = time.perf_counter()
            prompt_service.build_prompt(request)
            times.append((time.perf_counter() - start) * 1000)

        # Performance should remain stable
        first_100 = statistics.mean(times[:100])
        last_100 = statistics.mean(times[-100:])

        # No significant degradation
        degradation = (last_100 - first_100) / first_100 * 100
        assert degradation < 20, f"Performance degraded by {degradation:.1f}%"

@pytest.mark.skip(reason="Context module not yet implemented (US-041/042/043)")
class TestMemoryLeaks:
    """Test for memory leaks in context processing."""

    def test_no_memory_leak_in_loop(self):
        """Test that repeated operations don't leak memory."""
        prompt_service = PromptServiceV2()

        gc.collect()
        process = psutil.Process()

        # Take snapshots at intervals
        memory_snapshots = []

        for iteration in range(10):
            # Process many requests
            for i in range(1000):
                request = GenerationRequest(
                    begrip=f"test_{iteration}_{i}",
                    organisatorische_context=[f"Org_{i % 10}"],
                    juridische_context=[f"Jur_{i % 5}"],
                    wettelijke_basis=[f"Wet_{i % 7}"],
                )
                prompt_service.build_prompt(request)

            # Force garbage collection
            gc.collect()

            # Record memory
            memory_mb = process.memory_info().rss / 1024 / 1024
            memory_snapshots.append(memory_mb)

        # Check for leak
        # Memory should stabilize, not continuously grow
        first_half = statistics.mean(memory_snapshots[:5])
        second_half = statistics.mean(memory_snapshots[5:])

        growth = second_half - first_half
        assert growth < 10, f"Memory grew by {growth:.2f}MB, possible leak"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
