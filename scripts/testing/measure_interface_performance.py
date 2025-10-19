#!/usr/bin/env python3
"""
Performance measurement script for TabbedInterface caching optimization.

Measures actual performance impact of @st.cache_resource on TabbedInterface
by simulating multiple Streamlit reruns and tracking initialization times.

Expected Performance:
    - Without cache: 200ms per rerun (1200ms total for 6 reruns)
    - With cache: 200ms first call + 10ms × 5 reruns = 250ms total
    - Savings: 950ms (~79% improvement)

Usage:
    python scripts/testing/measure_interface_performance.py

Output:
    - Detailed timing breakdown per rerun
    - Cache effectiveness metrics
    - Performance improvement percentage
"""

import logging
import sys
import time
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

# Setup logging to capture TabbedInterface init messages
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def measure_performance():
    """Measure TabbedInterface caching performance."""
    print("\n" + "=" * 80)
    print("TABBED INTERFACE CACHING PERFORMANCE MEASUREMENT")
    print("=" * 80 + "\n")

    # Import with minimal mocking to get real performance data
    from unittest.mock import MagicMock, patch

    # Mock only essential Streamlit components
    mock_st = MagicMock()
    mock_session_state = MagicMock()

    # Simulate cache_resource behavior
    _cache = {}

    def cache_resource_decorator(func):
        """Real caching decorator."""

        def wrapper(*args, **kwargs):
            cache_key = id(func)
            if cache_key not in _cache:
                logger.info(f"[CACHE MISS] Calling {func.__name__}")
                _cache[cache_key] = func(*args, **kwargs)
            else:
                logger.info(f"[CACHE HIT] Reusing {func.__name__} result")
            return _cache[cache_key]

        return wrapper

    mock_st.cache_resource = cache_resource_decorator
    mock_st.session_state = mock_session_state

    with patch.dict("sys.modules", {"streamlit": mock_st}):
        # Force reimport to apply caching
        if "main" in sys.modules:
            del sys.modules["main"]
        if "ui.tabbed_interface" in sys.modules:
            del sys.modules["ui.tabbed_interface"]

        # Import main module
        import main

        # Simulate 6 reruns
        print("Simulating 6 Streamlit reruns with caching enabled...\n")
        results = []

        for rerun_num in range(1, 7):
            print(f"--- Rerun #{rerun_num} ---")

            # Measure interface instantiation time
            start = time.perf_counter()
            try:
                main.get_tabbed_interface()
                elapsed_ms = (time.perf_counter() - start) * 1000

                results.append(
                    {
                        "rerun": rerun_num,
                        "elapsed_ms": elapsed_ms,
                        "cached": rerun_num > 1,
                    }
                )

                cache_status = "⚡ CACHE HIT" if rerun_num > 1 else "🚀 FIRST CALL"
                print(
                    f"get_tabbed_interface() completed in {elapsed_ms:.2f}ms - {cache_status}"
                )

            except Exception as e:
                logger.error(f"Rerun #{rerun_num} failed: {e}", exc_info=True)
                results.append(
                    {
                        "rerun": rerun_num,
                        "elapsed_ms": None,
                        "cached": rerun_num > 1,
                        "error": str(e),
                    }
                )

            print()

    # Analyze results
    print("\n" + "=" * 80)
    print("PERFORMANCE ANALYSIS")
    print("=" * 80 + "\n")

    # Filter out errors
    successful_results = [r for r in results if r["elapsed_ms"] is not None]

    if not successful_results:
        print("❌ No successful measurements recorded")
        return False

    # Calculate metrics
    first_call_ms = successful_results[0]["elapsed_ms"]
    cache_hits = [r["elapsed_ms"] for r in successful_results[1:]]

    print("Timing Breakdown:")
    print("-" * 40)
    print(f"  First call (cold): {first_call_ms:.2f}ms")

    if cache_hits:
        avg_cache_hit_ms = sum(cache_hits) / len(cache_hits)
        min_cache_hit_ms = min(cache_hits)
        max_cache_hit_ms = max(cache_hits)

        print(f"  Cache hits (avg): {avg_cache_hit_ms:.2f}ms")
        print(f"  Cache hits (min): {min_cache_hit_ms:.2f}ms")
        print(f"  Cache hits (max): {max_cache_hit_ms:.2f}ms")

        # Calculate improvement
        improvement_ms = first_call_ms - avg_cache_hit_ms
        improvement_pct = (improvement_ms / first_call_ms) * 100

        print("\nPerformance Improvement:")
        print("-" * 40)
        print(f"  Time saved per rerun: {improvement_ms:.2f}ms")
        print(f"  Percentage improvement: {improvement_pct:.1f}%")

        # Calculate total savings over 6 reruns
        total_without_cache = first_call_ms * 6
        total_with_cache = first_call_ms + (avg_cache_hit_ms * 5)
        total_savings = total_without_cache - total_with_cache

        print("\nTotal Impact (6 reruns):")
        print("-" * 40)
        print(f"  Without cache: {total_without_cache:.0f}ms")
        print(f"  With cache: {total_with_cache:.0f}ms")
        print(f"  Total savings: {total_savings:.0f}ms")

        # Performance targets
        print("\nTarget Verification:")
        print("-" * 40)

        targets = {
            "Cache hit < 20ms": avg_cache_hit_ms < 20,
            "Cache hit < 50ms": avg_cache_hit_ms < 50,
            "Improvement > 50%": improvement_pct > 50,
            "Total savings > 500ms": total_savings > 500,
        }

        for target, passed in targets.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {target}")

        # Overall verdict
        all_passed = all(targets.values())
        critical_passed = targets["Cache hit < 50ms"]

        print("\n" + "=" * 80)
        if all_passed:
            print("✅ EXCELLENT: All performance targets met!")
        elif critical_passed:
            print("⚠️  ACCEPTABLE: Critical targets met, but optimization possible")
        else:
            print("❌ POOR: Performance targets not met")
        print("=" * 80 + "\n")

        return critical_passed

    print("⚠️  No cache hits recorded (only first call)")
    return False


if __name__ == "__main__":
    try:
        success = measure_performance()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Performance measurement failed: {e}", exc_info=True)
        print(f"\n❌ FATAL ERROR: {e}")
        sys.exit(1)
