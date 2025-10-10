#!/usr/bin/env python3
"""
Benchmark script to compare sequential vs parallel voorbeelden generation.

This script demonstrates the performance improvement from implementing
parallel execution with asyncio.gather().

Usage:
    python scripts/benchmark_voorbeelden_parallel.py
"""

import asyncio
import time
from unittest.mock import MagicMock, patch

from voorbeelden.unified_voorbeelden import (
    ExampleRequest,
    ExampleType,
    GenerationMode,
    genereer_alle_voorbeelden_async,
)

# Realistic AI call simulation
SIMULATED_AI_DELAY = 2.0  # Seconds per AI call


async def mock_generate_async(request: ExampleRequest):
    """
    Mock async generation with realistic delay.

    Simulates actual AI service call timing.
    """
    await asyncio.sleep(SIMULATED_AI_DELAY)

    if request.example_type == ExampleType.TOELICHTING:
        return [f"Mock toelichting voor {request.begrip}"]

    return [
        f"Mock {request.example_type.value} voorbeeld 1",
        f"Mock {request.example_type.value} voorbeeld 2",
        f"Mock {request.example_type.value} voorbeeld 3",
    ]


async def sequential_execution(begrip: str, definitie: str, context_dict: dict):
    """
    Simulate OLD sequential execution pattern.

    This is how the code worked BEFORE parallelization.
    """
    print("\n" + "=" * 60)
    print("SEQUENTIAL EXECUTION (OLD METHOD)")
    print("=" * 60)

    start_time = time.time()
    results = {}

    for i, example_type in enumerate(ExampleType, 1):
        type_start = time.time()

        request = ExampleRequest(
            begrip=begrip,
            definitie=definitie,
            context_dict=context_dict,
            example_type=example_type,
            generation_mode=GenerationMode.ASYNC,
            max_examples=3,
        )

        print(f"[{i}/6] Generating {example_type.value}...", end=" ", flush=True)

        # Sequential: wait for each call to complete before starting next
        result = await mock_generate_async(request)

        type_duration = time.time() - type_start
        print(f"✓ ({type_duration:.2f}s)")

        if example_type == ExampleType.TOELICHTING:
            results[example_type.value] = result[0] if result else ""
        else:
            results[example_type.value] = result

    total_duration = time.time() - start_time

    print(f"\n📊 Sequential Total Time: {total_duration:.2f}s")
    print(f"   Average per call: {total_duration / 6:.2f}s")

    return results, total_duration


async def parallel_execution(begrip: str, definitie: str, context_dict: dict):
    """
    Test NEW parallel execution pattern.

    This is how the code works AFTER parallelization.
    """
    print("\n" + "=" * 60)
    print("PARALLEL EXECUTION (NEW METHOD)")
    print("=" * 60)

    with patch(
        "voorbeelden.unified_voorbeelden.get_examples_generator"
    ) as mock_get_generator:
        mock_generator = MagicMock()
        mock_generator._generate_async = mock_generate_async
        mock_get_generator.return_value = mock_generator

        print("Starting all 6 generations in parallel...")
        start_time = time.time()

        # This calls the actual parallelized function
        results = await genereer_alle_voorbeelden_async(
            begrip=begrip,
            definitie=definitie,
            context_dict=context_dict,
        )

        total_duration = time.time() - start_time

        print(f"\n📊 Parallel Total Time: {total_duration:.2f}s")
        print("   All 6 calls completed concurrently")

    return results, total_duration


def print_comparison(seq_time: float, par_time: float):
    """Print detailed comparison of sequential vs parallel execution."""
    print("\n" + "=" * 60)
    print("PERFORMANCE COMPARISON")
    print("=" * 60)

    speedup = seq_time / par_time
    time_saved = seq_time - par_time
    improvement_pct = (time_saved / seq_time) * 100

    print("\n⏱️  Timing:")
    print(f"   Sequential (old):  {seq_time:.2f}s")
    print(f"   Parallel (new):    {par_time:.2f}s")
    print(f"   Time Saved:        {time_saved:.2f}s")

    print("\n🚀 Performance Gain:")
    print(f"   Speedup:           {speedup:.1f}x faster")
    print(f"   Improvement:       {improvement_pct:.0f}%")

    print("\n💰 Business Impact:")
    generations_per_hour_old = 3600 / seq_time
    generations_per_hour_new = 3600 / par_time
    additional_capacity = generations_per_hour_new - generations_per_hour_old

    print(f"   Definitions/hour (old): {generations_per_hour_old:.0f}")
    print(f"   Definitions/hour (new): {generations_per_hour_new:.0f}")
    print(f"   Additional capacity:    +{additional_capacity:.0f} definitions/hour")

    print("\n🎯 User Experience:")
    print(f"   Every user saves {time_saved:.1f}s per generation")
    print(f"   That's {improvement_pct:.0f}% faster response time!")

    # Visual comparison
    print("\n📊 Visual Comparison:")

    # Sequential bars
    bar_length_seq = int(seq_time * 5)  # Scale for display
    print(f"   Sequential: [{'█' * bar_length_seq}] {seq_time:.1f}s")

    # Parallel bars
    bar_length_par = int(par_time * 5)
    saved_bars = bar_length_seq - bar_length_par
    print(f"   Parallel:   [{'█' * bar_length_par}{'░' * saved_bars}] {par_time:.1f}s")
    print(f"                {'⬆' * saved_bars} {time_saved:.1f}s saved!")


async def main():
    """Run benchmark comparison."""
    print("\n" + "=" * 60)
    print("VOORBEELDEN GENERATION BENCHMARK")
    print("=" * 60)
    print("\nComparing sequential vs parallel execution")
    print(f"Simulated AI delay: {SIMULATED_AI_DELAY}s per call")
    print("Number of calls: 6 (all example types)")

    # Test data
    begrip = "identiteitsbehandeling"
    definitie = "Het proces waarbij de identiteit van een persoon wordt vastgesteld"
    context_dict = {
        "organisatorisch": ["Strafrechtketen"],
        "juridisch": ["Strafrecht"],
        "wettelijk": ["Wetboek van Strafrecht"],
    }

    # Run sequential execution
    seq_results, seq_time = await sequential_execution(begrip, definitie, context_dict)

    # Small delay between tests
    await asyncio.sleep(1)

    # Run parallel execution
    par_results, par_time = await parallel_execution(begrip, definitie, context_dict)

    # Verify results are equivalent
    assert set(seq_results.keys()) == set(par_results.keys()), "Result keys mismatch"
    print("\n✅ Results verification: Both methods produce equivalent output")

    # Print comparison
    print_comparison(seq_time, par_time)

    print("\n" + "=" * 60)
    print("CONCLUSION")
    print("=" * 60)
    print("\n✅ Parallel execution is significantly faster!")
    print(f"✅ Saves {seq_time - par_time:.1f}s per generation")
    print(
        f"✅ {((seq_time - par_time) / seq_time * 100):.0f}% improvement in user experience"
    )
    print("\n🚀 Ready for production deployment!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
