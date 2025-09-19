"""Performance baseline tests for ModularValidationService."""

import pytest
import os
import time
import statistics
from typing import List, Dict
import asyncio


@pytest.mark.performance
@pytest.mark.asyncio
async def test_performance_vs_v1_baseline():
    """Test that V2 performance meets or exceeds V1 baseline."""
    # Try to import both V1 and V2
    try:
        from services.definition_validator import DefinitionValidator
        from services.interfaces import Definition
        v1_available = True
    except ImportError:
        v1_available = False

    m = pytest.importorskip(
        "services.validation.modular_validation_service",
        reason="ModularValidationService not implemented yet",
    )

    if not v1_available:
        pytest.skip("V1 validator not available for comparison")

    # Setup V1 validator
    v1_validator = DefinitionValidator()

    # Setup V2 validator
    svc = m.ModularValidationService
    try:
        v2_validator = svc(toetsregel_manager=None, cleaning_service=None, config=None)
    except TypeError:
        v2_validator = svc()

    # Test definitions
    test_cases = [
        ("kort", "Een korte definitie."),
        ("gemiddeld", "Een gemiddelde definitie met voldoende inhoud om verschillende validatieregels te triggeren."),
        ("lang", "Een zeer uitgebreide definitie die alle aspecten van het concept behandelt, inclusief voorbeelden, uitzonderingen, relaties met andere concepten, historische context, praktische toepassingen, theoretische grondslagen, en mogelijke misverstanden die kunnen ontstaan bij het interpreteren van dit concept in verschillende contexten." * 2),
    ]

    # Measure V1 performance
    v1_times = []
    for begrip, text in test_cases:
        definition = Definition(begrip=begrip, definitie=text)

        start = time.perf_counter()
        for _ in range(5):  # Multiple runs for average
            v1_result = v1_validator.validate(definition)
        v1_time = (time.perf_counter() - start) / 5
        v1_times.append(v1_time)

    # Measure V2 performance
    v2_times = []
    for begrip, text in test_cases:
        start = time.perf_counter()
        for _ in range(5):  # Multiple runs for average
            v2_result = await v2_validator.validate_definition(
                begrip=begrip,
                text=text,
                ontologische_categorie=None,
                context=None,
            )
        v2_time = (time.perf_counter() - start) / 5
        v2_times.append(v2_time)

    # Compare performance
    v1_avg = statistics.mean(v1_times)
    v2_avg = statistics.mean(v2_times)

    # V2 should not be more than 20% slower than V1
    performance_ratio = v2_avg / v1_avg
    assert performance_ratio <= 1.2, \
        f"V2 ({v2_avg:.3f}s) is {performance_ratio:.1f}x slower than V1 ({v1_avg:.3f}s)"

    # Ideally V2 should be faster
    if performance_ratio < 1.0:
        improvement = (1 - performance_ratio) * 100
        print(f"✓ V2 is {improvement:.1f}% faster than V1")


@pytest.mark.performance
@pytest.mark.asyncio
async def test_validation_latency_bounds():
    """Test that validation latency stays within acceptable bounds."""
    m = pytest.importorskip(
        "services.validation.modular_validation_service",
        reason="ModularValidationService not implemented yet",
    )

    svc = m.ModularValidationService
    try:
        service = svc(toetsregel_manager=None, cleaning_service=None, config=None)
    except TypeError:
        service = svc()

    # Test different text sizes
    test_cases = [
        ("small", "x" * 10, 50),  # Small text, max 50ms
        ("medium", "x" * 100, 100),  # Medium text, max 100ms
        ("large", "x" * 1000, 200),  # Large text, max 200ms
        ("xlarge", "x" * 5000, 500),  # XLarge text, max 500ms
    ]

    for name, text, max_ms in test_cases:
        times = []

        # Run multiple times for statistical significance
        for _ in range(10):
            start = time.perf_counter()
            result = await service.validate_definition(
                begrip=f"test_{name}",
                text=text,
                ontologische_categorie=None,
                context=None,
            )
            elapsed_ms = (time.perf_counter() - start) * 1000
            times.append(elapsed_ms)

        # Check 95th percentile is within bounds
        p95 = statistics.quantiles(times, n=20)[18]  # 95th percentile
        assert p95 <= max_ms, \
            f"{name} text: 95th percentile {p95:.1f}ms exceeds limit {max_ms}ms"

        # Check median is well within bounds
        median = statistics.median(times)
        assert median <= max_ms * 0.7, \
            f"{name} text: median {median:.1f}ms too close to limit {max_ms}ms"


SKIP_TIMING = pytest.mark.skipif(
    bool(os.getenv("CI") or os.getenv("GITHUB_ACTIONS")),
    reason="Timing-gevoelige test; overslaan in CI",
)


@pytest.mark.performance
@pytest.mark.asyncio
@SKIP_TIMING
@pytest.mark.xfail(reason="Timeoutbescherming nog niet geïmplementeerd in adapter; timing-gevoelig", strict=False)
async def test_rule_evaluation_overhead():
    """Test overhead of individual rule evaluation."""
    m = pytest.importorskip(
        "services.validation.module_adapter",
        reason="ValidationModuleAdapter not implemented yet",
    )
    t = pytest.importorskip(
        "services.validation.types_internal",
        reason="types_internal not implemented yet",
    )

    adapter = m.ValidationModuleAdapter()

    # Create simple test rule
    class FastRule:
        code = "FAST-01"
        def validate(self, context):
            return {"score": 0.8, "violations": []}

    class SlowRule:
        code = "SLOW-01"
        def validate(self, context):
            time.sleep(0.01)  # Simulate slow validation
            return {"score": 0.7, "violations": []}

    # Create context
    ctx = t.EvaluationContext(
        raw_text="test",
        cleaned_text="test",
        locale=None,
        profile=None,
        correlation_id="perf-test",
        tokens=[],
        metadata={},
    )

    # Measure fast rule overhead
    fast_times = []
    for _ in range(100):
        start = time.perf_counter()
        await adapter.evaluate(FastRule(), ctx)
        elapsed = time.perf_counter() - start
        fast_times.append(elapsed * 1000)

    # Fast rule overhead should be minimal (< 1ms)
    median_overhead = statistics.median(fast_times)
    assert median_overhead < 1.0, f"Rule evaluation overhead {median_overhead:.2f}ms is too high"

    # Test timeout protection
    class InfiniteRule:
        code = "INF-01"
        def validate(self, context):
            time.sleep(10)  # Way too long
            return {"score": 1.0, "violations": []}

    # Should timeout and return errored result
    start = time.perf_counter()
    result = await adapter.evaluate(InfiniteRule(), ctx)
    elapsed = time.perf_counter() - start

    assert elapsed < 2.0, "Timeout protection failed"
    assert result.get("errored", False), "Timed out rule should be marked as errored"


@pytest.mark.performance
@pytest.mark.asyncio
@SKIP_TIMING
@pytest.mark.xfail(reason="Concurrencyschaal-test is timing-gevoelig; heuristiek nog niet gestabiliseerd", strict=False)
async def test_concurrent_validation_scaling():
    """Test that concurrent validations scale efficiently."""
    m = pytest.importorskip(
        "services.validation.modular_validation_service",
        reason="ModularValidationService not implemented yet",
    )

    svc = m.ModularValidationService
    try:
        service = svc(toetsregel_manager=None, cleaning_service=None, config=None)
    except TypeError:
        service = svc()

    test_text = "Een test definitie voor concurrent validation performance testing."

    # Test different concurrency levels
    for n_concurrent in [1, 5, 10, 20]:
        start = time.perf_counter()

        # Create concurrent tasks
        tasks = [
            service.validate_definition(
                begrip=f"test_{i}",
                text=test_text,
                ontologische_categorie=None,
                context={"correlation_id": f"perf-{i}"},
            )
            for i in range(n_concurrent)
        ]

        # Run concurrently
        results = await asyncio.gather(*tasks)

        elapsed = time.perf_counter() - start

        # Time should not scale linearly with concurrency
        # (i.e., 10 concurrent should not take 10x as long as 1)
        time_per_validation = elapsed / n_concurrent

        # First validation to establish baseline
        if n_concurrent == 1:
            baseline_time = elapsed
        else:
            # Should be less than 50% overhead per doubling of concurrency
            expected_max = baseline_time * (1 + 0.5 * (n_concurrent - 1) / 10)
            assert elapsed <= expected_max, \
                f"Concurrent {n_concurrent}: {elapsed:.2f}s exceeds expected {expected_max:.2f}s"

        # All results should be valid
        assert len(results) == n_concurrent
        for result in results:
            assert "overall_score" in result


@pytest.mark.performance
def test_memory_usage_stability():
    """Test that memory usage remains stable during repeated validations."""
    m = pytest.importorskip(
        "services.validation.modular_validation_service",
        reason="ModularValidationService not implemented yet",
    )

    import gc
    import sys

    # Skip if memory profiling not available
    if not hasattr(sys, 'getsizeof'):
        pytest.skip("Memory profiling not available")

    svc = m.ModularValidationService
    try:
        service = svc(toetsregel_manager=None, cleaning_service=None, config=None)
    except TypeError:
        service = svc()

    # Force garbage collection
    gc.collect()

    # Measure initial memory (simplified - real profiling would use tracemalloc)
    initial_objects = len(gc.get_objects())

    # Run many validations
    async def run_validations():
        for i in range(100):
            await service.validate_definition(
                begrip=f"test_{i}",
                text=f"Test definitie nummer {i} voor memory leak detection.",
                ontologische_categorie=None,
                context=None,
            )

    # Run the async function
    import asyncio
    asyncio.run(run_validations())

    # Force garbage collection
    gc.collect()

    # Check memory didn't grow excessively
    final_objects = len(gc.get_objects())
    object_growth = final_objects - initial_objects

    # Allow some growth but not linear with iterations
    assert object_growth < 1000, \
        f"Possible memory leak: {object_growth} new objects after 100 validations"


@pytest.mark.performance
@pytest.mark.benchmark
def test_validation_throughput(benchmark):
    """Benchmark validation throughput (if pytest-benchmark available)."""
    m = pytest.importorskip(
        "services.validation.modular_validation_service",
        reason="ModularValidationService not implemented yet",
    )

    svc = m.ModularValidationService
    try:
        service = svc(toetsregel_manager=None, cleaning_service=None, config=None)
    except TypeError:
        service = svc()

    async def validate_once():
        return await service.validate_definition(
            begrip="benchmark",
            text="Een benchmark definitie om de throughput te meten van de validatie service.",
            ontologische_categorie=None,
            context=None,
        )

    # Run benchmark
    import asyncio
    result = benchmark(lambda: asyncio.run(validate_once()))

    # Verify result is valid
    assert "overall_score" in result

    # Benchmark stats will be automatically reported by pytest-benchmark
