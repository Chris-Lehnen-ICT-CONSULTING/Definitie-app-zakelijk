#!/usr/bin/env python3
"""
Measure the impact of lazy loading on container startup time.

This script benchmarks:
1. Container init time
2. Generator tab scenario (critical services only)
3. Edit tab scenario (lazy services loaded)
4. Export scenario (more lazy services)
"""

import logging
import time

# Suppress logging for clean benchmark output
logging.basicConfig(level=logging.WARNING)


def measure_container_init() -> float:
    """Measure container initialization time."""
    start = time.perf_counter()
    from services.container import ServiceContainer

    ServiceContainer()
    return (time.perf_counter() - start) * 1000


def measure_generator_scenario() -> dict[str, float]:
    """Measure Generator tab scenario (critical services)."""
    from services.container import ServiceContainer

    init_start = time.perf_counter()
    container = ServiceContainer()
    init_time = (time.perf_counter() - init_start) * 1000

    # Access critical services for generator
    critical_start = time.perf_counter()
    _ = container.repository()
    _ = container.orchestrator()
    _ = container.validation_orchestrator()
    critical_time = (time.perf_counter() - critical_start) * 1000

    return {
        "init": init_time,
        "critical": critical_time,
        "total": init_time + critical_time,
        "eager": len(container._instances),
        "lazy": len(container._lazy_instances),
    }


def measure_edit_scenario() -> dict[str, float]:
    """Measure Edit tab scenario (+ lazy services)."""
    from services.container import ServiceContainer

    init_start = time.perf_counter()
    container = ServiceContainer()
    init_time = (time.perf_counter() - init_start) * 1000

    # Critical services
    critical_start = time.perf_counter()
    _ = container.repository()
    _ = container.orchestrator()
    critical_time = (time.perf_counter() - critical_start) * 1000

    # Edit services (lazy)
    edit_start = time.perf_counter()
    _ = container.duplicate_detector()
    edit_time = (time.perf_counter() - edit_start) * 1000

    return {
        "init": init_time,
        "critical": critical_time,
        "edit": edit_time,
        "total": init_time + critical_time + edit_time,
        "eager": len(container._instances),
        "lazy": len(container._lazy_instances),
    }


def measure_export_scenario() -> dict[str, float]:
    """Measure Export scenario (+ more lazy services)."""
    from services.container import ServiceContainer

    init_start = time.perf_counter()
    container = ServiceContainer()
    init_time = (time.perf_counter() - init_start) * 1000

    # Critical services
    critical_start = time.perf_counter()
    _ = container.repository()
    _ = container.orchestrator()
    critical_time = (time.perf_counter() - critical_start) * 1000

    # Export services (lazy)
    export_start = time.perf_counter()
    _ = container.export_service()
    _ = container.data_aggregation_service()
    export_time = (time.perf_counter() - export_start) * 1000

    return {
        "init": init_time,
        "critical": critical_time,
        "export": export_time,
        "total": init_time + critical_time + export_time,
        "eager": len(container._instances),
        "lazy": len(container._lazy_instances),
    }


def run_benchmark(name: str, func, iterations: int = 5) -> dict[str, float]:
    """Run benchmark with multiple iterations."""
    results: list[dict[str, float]] = []

    for _ in range(iterations):
        # Reset imports to get clean measurement
        import sys

        if "services.container" in sys.modules:
            del sys.modules["services.container"]

        result = func()
        results.append(result)

    # Calculate averages
    avg_result = {}
    for key in results[0]:
        if isinstance(results[0][key], int | float):
            avg_result[key] = sum(r[key] for r in results) / len(results)
        else:
            avg_result[key] = results[0][key]  # Use first value for non-numeric

    return avg_result


def main():
    """Run all benchmarks and display results."""
    print("=" * 70)
    print("LAZY LOADING PERFORMANCE BENCHMARK")
    print("=" * 70)
    print()

    print("Running benchmarks (5 iterations each)...\n")

    # Benchmark 1: Container init only
    print("1. Container Init Only")
    print("-" * 70)
    init_times = [measure_container_init() for _ in range(5)]
    avg_init = sum(init_times) / len(init_times)
    print(f"   Average: {avg_init:.1f}ms")
    print(f"   Min: {min(init_times):.1f}ms, Max: {max(init_times):.1f}ms")
    print()

    # Benchmark 2: Generator scenario
    print("2. Generator Tab Scenario (Critical Services)")
    print("-" * 70)
    gen_result = run_benchmark("generator", measure_generator_scenario)
    print(f"   Container init: {gen_result['init']:.1f}ms")
    print(f"   Critical services: {gen_result['critical']:.1f}ms")
    print(f"   Total: {gen_result['total']:.1f}ms")
    print(f"   Services loaded: {gen_result['eager']} eager, {gen_result['lazy']} lazy")
    print()

    # Benchmark 3: Edit scenario
    print("3. Edit Tab Scenario (+ Lazy Services)")
    print("-" * 70)
    edit_result = run_benchmark("edit", measure_edit_scenario)
    print(f"   Container init: {edit_result['init']:.1f}ms")
    print(f"   Critical services: {edit_result['critical']:.1f}ms")
    print(f"   Edit services (lazy): {edit_result['edit']:.1f}ms")
    print(f"   Total: {edit_result['total']:.1f}ms")
    print(
        f"   Services loaded: {edit_result['eager']} eager, {edit_result['lazy']} lazy"
    )
    print()

    # Benchmark 4: Export scenario
    print("4. Export Scenario (+ More Lazy Services)")
    print("-" * 70)
    export_result = run_benchmark("export", measure_export_scenario)
    print(f"   Container init: {export_result['init']:.1f}ms")
    print(f"   Critical services: {export_result['critical']:.1f}ms")
    print(f"   Export services (lazy): {export_result['export']:.1f}ms")
    print(f"   Total: {export_result['total']:.1f}ms")
    print(
        f"   Services loaded: {export_result['eager']} eager, {export_result['lazy']} lazy"
    )
    print()

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Generator tab (most common): {gen_result['total']:.1f}ms")
    print(
        f"Edit tab overhead: +{edit_result['edit']:.1f}ms (lazy load on first access)"
    )
    print(
        f"Export overhead: +{export_result['export']:.1f}ms (lazy load on first access)"
    )
    print()
    print("✅ Target: <250ms for generator-only scenario")
    if gen_result["total"] < 250:
        print(f"✅ PASS: {gen_result['total']:.1f}ms < 250ms")
    else:
        print(f"❌ FAIL: {gen_result['total']:.1f}ms >= 250ms")
    print()


if __name__ == "__main__":
    main()
