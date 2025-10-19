#!/usr/bin/env python3
"""
Script om SRU Circuit Breaker performance verbetering te meten.

Vergelijkt search execution time met en zonder circuit breaker voor
searches die geen resultaten opleveren.

Expected results:
- MET circuit breaker: ~12 seconden (2 queries × ~6s)
- ZONDER circuit breaker: ~30 seconden (5 queries × ~6s)
- Performance verbetering: ~60%
"""

import asyncio
import time

from src.services.web_lookup.sru_service import SRUService


async def measure_search_performance(
    term: str,
    endpoint: str,
    circuit_breaker_enabled: bool,
    threshold: int = 2,
) -> dict:
    """Meet performance van een SRU search."""

    config = {
        "enabled": circuit_breaker_enabled,
        "consecutive_empty_threshold": threshold,
        "providers": {
            "overheid": threshold,
            "rechtspraak": threshold,
            "wetgeving_nl": threshold,
        },
    }

    service = SRUService(circuit_breaker_config=config)

    async with service:
        start = time.time()

        try:
            results = await service.search(term=term, endpoint=endpoint, max_records=5)
        except Exception as e:
            print(f"Error during search: {e}")
            results = []

        elapsed = time.time() - start

        # Get attempt metadata
        attempts = service.get_attempts()
        strategies = {a.get("strategy") for a in attempts if a.get("strategy")}

        return {
            "term": term,
            "endpoint": endpoint,
            "circuit_breaker_enabled": circuit_breaker_enabled,
            "threshold": threshold if circuit_breaker_enabled else "N/A",
            "execution_time": elapsed,
            "results_count": len(results),
            "total_attempts": len(attempts),
            "strategies_used": list(strategies),
            "strategies_count": len(strategies),
        }


async def run_comparison():
    """Vergelijk performance met en zonder circuit breaker."""

    print("=" * 80)
    print("SRU CIRCUIT BREAKER PERFORMANCE MEASUREMENT")
    print("=" * 80)
    print()

    # Test scenarios: zoektermen die waarschijnlijk geen resultaten opleveren
    test_cases = [
        ("xyzabc123nonexistent999", "overheid"),
        ("verylongnonsenseterm12345", "overheid"),
    ]

    results: list[dict] = []

    for term, endpoint in test_cases:
        print(f"Testing search: term='{term}', endpoint='{endpoint}'")
        print("-" * 80)

        # Test WITH circuit breaker (threshold=2)
        print("1. WITH circuit breaker (threshold=2)...")
        result_with = await measure_search_performance(
            term=term,
            endpoint=endpoint,
            circuit_breaker_enabled=True,
            threshold=2,
        )
        results.append(result_with)

        print(f"   Execution time: {result_with['execution_time']:.2f}s")
        print(f"   Strategies used: {result_with['strategies_count']}")
        print(f"   Total attempts: {result_with['total_attempts']}")
        print()

        # Test WITHOUT circuit breaker (effectively disabled with high threshold)
        print("2. WITHOUT circuit breaker (threshold=999)...")
        result_without = await measure_search_performance(
            term=term,
            endpoint=endpoint,
            circuit_breaker_enabled=True,  # Still enabled, but threshold very high
            threshold=999,
        )
        results.append(result_without)

        print(f"   Execution time: {result_without['execution_time']:.2f}s")
        print(f"   Strategies used: {result_without['strategies_count']}")
        print(f"   Total attempts: {result_without['total_attempts']}")
        print()

        # Calculate improvement
        time_saved = result_without["execution_time"] - result_with["execution_time"]
        improvement = (
            (time_saved / result_without["execution_time"]) * 100
            if result_without["execution_time"] > 0
            else 0
        )

        print("IMPROVEMENT:")
        print(f"   Time saved: {time_saved:.2f}s")
        print(f"   Performance gain: {improvement:.1f}%")
        print(
            f"   Queries saved: {result_without['strategies_count'] - result_with['strategies_count']}"
        )
        print()
        print("=" * 80)
        print()

    # Summary
    print("\nSUMMARY")
    print("=" * 80)

    # Calculate averages
    with_cb = [r for r in results if r["threshold"] == 2]
    without_cb = [
        r for r in results if r["threshold"] == "N/A" or r["threshold"] == 999
    ]

    if with_cb and without_cb:
        avg_time_with = sum(r["execution_time"] for r in with_cb) / len(with_cb)
        avg_time_without = sum(r["execution_time"] for r in without_cb) / len(
            without_cb
        )
        avg_improvement = (
            ((avg_time_without - avg_time_with) / avg_time_without) * 100
            if avg_time_without > 0
            else 0
        )

        print(f"Average execution time WITH circuit breaker:    {avg_time_with:.2f}s")
        print(
            f"Average execution time WITHOUT circuit breaker: {avg_time_without:.2f}s"
        )
        print(f"Average performance improvement:                {avg_improvement:.1f}%")
        print()
        print(f"✓ Circuit breaker reduces execution time by ~{avg_improvement:.0f}%")
        print(f"✓ Saves ~{avg_time_without - avg_time_with:.1f}s per empty search")


if __name__ == "__main__":
    try:
        asyncio.run(run_comparison())
    except KeyboardInterrupt:
        print("\n\nMeasurement interrupted by user.")
    except Exception as e:
        print(f"\nError during measurement: {e}")
        import traceback

        traceback.print_exc()
