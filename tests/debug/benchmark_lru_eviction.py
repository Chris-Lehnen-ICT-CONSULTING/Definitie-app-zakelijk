#!/usr/bin/env python3
"""
Benchmark script to demonstrate O(1) LRU eviction in SynonymOrchestrator.

This script verifies that the OrderedDict-based LRU cache has constant-time
eviction, compared to the previous O(n) implementation using min().
"""

import time
from collections import OrderedDict
from datetime import UTC, datetime


# Mock WeightedSynonym for testing
class MockWeightedSynonym:
    def __init__(self, term: str, weight: float):
        self.term = term
        self.weight = weight


def benchmark_old_lru_eviction(cache_size: int, iterations: int) -> float:
    """
    Benchmark OLD O(n) LRU eviction using min().

    This is the BEFORE implementation that scans all cache entries.
    """
    cache: dict[str, tuple[list[MockWeightedSynonym], datetime]] = {}

    start_time = time.perf_counter()

    for i in range(iterations):
        term = f"term_{i}"
        synonyms = [MockWeightedSynonym(f"syn_{i}", 1.0)]

        # Enforce max size (OLD O(n) eviction)
        if len(cache) >= cache_size and cache:
            # O(n) operation - scans all entries!
            oldest_term = min(cache.items(), key=lambda x: x[1][1])[0]
            del cache[oldest_term]

        cache[term] = (synonyms, datetime.now(UTC))

    return time.perf_counter() - start_time


def benchmark_new_lru_eviction(cache_size: int, iterations: int) -> float:
    """
    Benchmark NEW O(1) LRU eviction using OrderedDict.popitem().

    This is the AFTER implementation using OrderedDict.
    """
    cache: OrderedDict[str, tuple[list[MockWeightedSynonym], datetime, int]] = (
        OrderedDict()
    )
    cache_version = 0

    start_time = time.perf_counter()

    for i in range(iterations):
        term = f"term_{i}"
        synonyms = [MockWeightedSynonym(f"syn_{i}", 1.0)]

        # Enforce max size (NEW O(1) eviction)
        if len(cache) >= cache_size and cache:
            # O(1) operation - removes first item!
            oldest_term, _ = cache.popitem(last=False)

        cache[term] = (synonyms, datetime.now(UTC), cache_version)
        cache.move_to_end(term)  # Mark as recently used

    return time.perf_counter() - start_time


def main():
    print("=" * 70)
    print("LRU EVICTION PERFORMANCE BENCHMARK")
    print("=" * 70)
    print()
    print("Testing O(n) min() vs O(1) OrderedDict.popitem() performance")
    print()

    # Test configurations: (cache_size, iterations)
    test_configs = [
        (100, 1000),  # Small cache
        (500, 5000),  # Medium cache
        (1000, 10000),  # Large cache
    ]

    for cache_size, iterations in test_configs:
        print(f"Cache size: {cache_size}, Iterations: {iterations:,}")
        print("-" * 70)

        # Benchmark OLD implementation
        old_time = benchmark_old_lru_eviction(cache_size, iterations)
        print(f"  OLD (O(n) min):          {old_time:.4f}s")

        # Benchmark NEW implementation
        new_time = benchmark_new_lru_eviction(cache_size, iterations)
        print(f"  NEW (O(1) OrderedDict):  {new_time:.4f}s")

        # Calculate speedup
        speedup = old_time / new_time if new_time > 0 else float("inf")
        improvement = ((old_time - new_time) / old_time * 100) if old_time > 0 else 0

        print(f"  Speedup:                 {speedup:.2f}x")
        print(f"  Improvement:             {improvement:.1f}% faster")
        print()

    print("=" * 70)
    print("CONCLUSION:")
    print("=" * 70)
    print("The OrderedDict implementation provides O(1) eviction with")
    print("predictable performance regardless of cache size, while the")
    print("old min() approach scales linearly (O(n)) with cache size.")
    print()


if __name__ == "__main__":
    main()
