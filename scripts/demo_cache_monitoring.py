#!/usr/bin/env python
"""
Demo script for cache monitoring functionality.

This script demonstrates the cache monitoring infrastructure with
RuleCache and generates example snapshot output.
"""
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

import time

from toetsregels.rule_cache import get_rule_cache


def main():
    print("=" * 60)
    print("Cache Monitoring Demo - RuleCache")
    print("=" * 60)
    print()

    # Get the rule cache
    cache = get_rule_cache()

    # Clear any existing monitoring data
    if hasattr(cache, "_monitor") and cache._monitor:
        cache._monitor.clear_operations()
        print("✓ Monitoring enabled and cleared")
    else:
        print("✗ Monitoring not available")
        return

    print()
    print("Performing cache operations...")
    print("-" * 60)

    # First call - should be a cache miss
    print("\n1. First get_all_rules() call (cache MISS expected)")
    start = time.perf_counter()
    rules1 = cache.get_all_rules()
    duration1 = (time.perf_counter() - start) * 1000
    print(f"   Loaded {len(rules1)} rules in {duration1:.2f}ms")

    # Second call - should be a cache hit
    print("\n2. Second get_all_rules() call (cache HIT expected)")
    start = time.perf_counter()
    rules2 = cache.get_all_rules()
    duration2 = (time.perf_counter() - start) * 1000
    print(f"   Loaded {len(rules2)} rules in {duration2:.2f}ms")
    print(f"   Speedup: {duration1 / duration2:.1f}x faster")

    # Get specific rules
    if rules1:
        print("\n3. Getting specific rules (should be cache HITs)")
        rule_ids = list(rules1.keys())[:3]
        for rule_id in rule_ids:
            start = time.perf_counter()
            rule = cache.get_rule(rule_id)
            duration = (time.perf_counter() - start) * 1000
            print(f"   get_rule('{rule_id}'): {duration:.2f}ms")

    print()
    print("-" * 60)
    print("Getting Cache Statistics and Snapshot")
    print("-" * 60)
    print()

    # Get stats with monitoring
    stats = cache.get_stats()

    print("Cache Statistics:")
    print(f"  Total rules cached: {stats['total_rules_cached']}")
    print(f"  get_all_calls: {stats['get_all_calls']}")
    print(f"  get_single_calls: {stats['get_single_calls']}")

    if "monitoring" in stats:
        mon = stats["monitoring"]
        print()
        print("Monitoring Metrics:")
        print(f"  Hit rate: {mon['hit_rate']:.2%}")
        print(f"  Total operations: {mon['total_operations']}")
        print(f"  Hits: {mon['hits']}")
        print(f"  Misses: {mon['misses']}")
        print(f"  Average operation time: {mon['avg_operation_ms']:.2f}ms")

    # Get detailed snapshot
    if cache._monitor:
        print()
        print("Detailed Cache Snapshot:")
        print("-" * 60)
        snapshot = cache._monitor.get_snapshot()
        print(f"  Cache Name: {snapshot.cache_name}")
        print(f"  Timestamp: {snapshot.timestamp}")
        print(f"  Total Entries: {snapshot.total_entries}")
        print(f"  Hit Rate: {snapshot.hit_rate:.2%}")
        print(f"  Hits: {snapshot.hits}")
        print(f"  Misses: {snapshot.misses}")
        print(f"  Evictions: {snapshot.evictions}")
        print(f"  Avg Operation Time: {snapshot.avg_operation_ms:.2f}ms")

        # Show recent operations
        print()
        print("Recent Operations (last 5):")
        operations = cache._monitor.get_operations(limit=5)
        for i, op in enumerate(operations, 1):
            print(
                f"  {i}. {op.operation}({op.key or 'N/A'}): "
                f"{op.result} from {op.source or 'N/A'} "
                f"in {op.duration_ms:.2f}ms"
            )

    print()
    print("=" * 60)
    print("Demo Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
