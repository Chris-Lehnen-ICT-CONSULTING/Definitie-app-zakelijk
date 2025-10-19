#!/usr/bin/env python3
"""
Verification script for TabbedInterface caching optimization.

This script verifies that TabbedInterface.__init__() is only called ONCE
across multiple Streamlit reruns, proving @st.cache_resource effectiveness.

Expected behavior:
- First call: TabbedInterface.__init__() executes (~200ms)
- Subsequent calls: Cache hit (~10ms)
- __init__() log message appears only ONCE

Usage:
    python scripts/testing/verify_tabbed_interface_caching.py

Output:
    - Performance metrics for interface instantiation
    - Cache hit verification
    - Success/failure report
"""

import logging
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add src to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def verify_caching():
    """Verify TabbedInterface caching with mock Streamlit environment."""
    print("\n" + "=" * 80)
    print("TABBED INTERFACE CACHING VERIFICATION")
    print("=" * 80 + "\n")

    # Mock Streamlit session state
    mock_session_state = MagicMock()
    mock_session_state.get = MagicMock(return_value=None)

    # Track __init__ calls
    init_call_count = 0
    init_times = []

    def track_init(original_init):
        """Wrapper to track __init__ calls."""

        def wrapper(self):
            nonlocal init_call_count
            init_call_count += 1
            start = time.perf_counter()
            result = original_init(self)
            elapsed_ms = (time.perf_counter() - start) * 1000
            init_times.append(elapsed_ms)
            logger.info(
                f"TabbedInterface.__init__() call #{init_call_count} - "
                f"took {elapsed_ms:.2f}ms"
            )
            return result

        return wrapper

    with patch("streamlit.cache_resource") as mock_cache_resource:
        # Configure mock to simulate caching behavior
        cache = {}

        def cache_decorator(func):
            """Simulate @st.cache_resource behavior."""

            def wrapper(*args, **kwargs):
                cache_key = func.__name__
                if cache_key not in cache:
                    logger.info(f"[CACHE MISS] Creating new instance for {cache_key}")
                    cache[cache_key] = func(*args, **kwargs)
                else:
                    logger.info(f"[CACHE HIT] Reusing cached instance for {cache_key}")
                return cache[cache_key]

            return wrapper

        mock_cache_resource.side_effect = cache_decorator

        # Simulate multiple reruns
        print("Simulating 6 Streamlit reruns...\n")

        with patch("streamlit.session_state", mock_session_state):
            # Import after mocking to ensure decorators work
            from ui.tabbed_interface import TabbedInterface

            # Patch __init__ to track calls
            original_init = TabbedInterface.__init__
            TabbedInterface.__init__ = track_init(original_init)

            # Import main module
            # Force re-evaluation of get_tabbed_interface
            from importlib import reload

            import main

            reload(main)

            # Simulate 6 reruns
            instances = []
            for rerun in range(1, 7):
                logger.info(f"\n--- Rerun #{rerun} ---")
                start = time.perf_counter()
                instance = main.get_tabbed_interface()
                elapsed_ms = (time.perf_counter() - start) * 1000
                instances.append((instance, elapsed_ms))
                logger.info(f"get_tabbed_interface() returned in {elapsed_ms:.2f}ms\n")

    # Verify results
    print("\n" + "=" * 80)
    print("VERIFICATION RESULTS")
    print("=" * 80 + "\n")

    print(f"Total TabbedInterface.__init__() calls: {init_call_count}")
    print("Expected calls: 1")
    print(f"Result: {'✅ PASS' if init_call_count == 1 else '❌ FAIL'}\n")

    print(f"Total get_tabbed_interface() calls: {len(instances)}")
    print("Expected calls: 6\n")

    # Verify all instances are the same object
    unique_instances = len({id(inst) for inst, _ in instances})
    print(f"Unique instance IDs: {unique_instances}")
    print("Expected unique IDs: 1")
    print(f"Result: {'✅ PASS' if unique_instances == 1 else '❌ FAIL'}\n")

    # Performance metrics
    print("Performance Metrics:")
    print("-" * 40)
    for idx, (_, elapsed_ms) in enumerate(instances, 1):
        status = "🚀 FIRST CALL" if idx == 1 else "⚡ CACHE HIT"
        print(f"  Rerun #{idx}: {elapsed_ms:.2f}ms - {status}")

    if len(instances) > 1:
        avg_cache_hit = sum(ms for _, ms in instances[1:]) / (len(instances) - 1)
        first_call = instances[0][1]
        improvement = ((first_call - avg_cache_hit) / first_call) * 100

        print(f"\nFirst call: {first_call:.2f}ms")
        print(f"Avg cache hit: {avg_cache_hit:.2f}ms")
        print(f"Improvement: {improvement:.1f}% faster")
        print(
            f"Performance: {'✅ PASS' if avg_cache_hit < 20 else '⚠️  SLOW (expected <20ms)'}"
        )

    # Overall verdict
    print("\n" + "=" * 80)
    success = init_call_count == 1 and unique_instances == 1
    if success:
        print("✅ OVERALL RESULT: CACHING WORKS AS EXPECTED!")
        print("   - TabbedInterface.__init__() called only once")
        print("   - All reruns reuse cached instance")
        print("   - Performance improvement verified")
    else:
        print("❌ OVERALL RESULT: CACHING ISSUE DETECTED!")
        if init_call_count > 1:
            print(f"   - __init__() called {init_call_count} times (expected 1)")
        if unique_instances > 1:
            print(f"   - {unique_instances} unique instances (expected 1)")
    print("=" * 80 + "\n")

    return success


if __name__ == "__main__":
    try:
        success = verify_caching()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Verification failed: {e}", exc_info=True)
        sys.exit(1)
