#!/usr/bin/env python3
"""
Measure Startup Performance - Verification Script for US-201 Optimizations

This script measures the impact of:
1. PromptOrchestrator singleton caching
2. Web lookup config caching

Expected improvements:
- Baseline: ~408ms
- After optimizations: ~218ms (47% improvement)
- Target: <250ms
"""

import logging
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def measure_component(name: str, func, *args, **kwargs):
    """Measure execution time of a component initialization."""
    start = time.perf_counter()
    try:
        result = func(*args, **kwargs)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(f"✅ {name}: {duration_ms:.2f}ms")
        return result, duration_ms, None
    except Exception as e:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.error(f"❌ {name}: {duration_ms:.2f}ms (FAILED: {e})")
        return None, duration_ms, str(e)


def test_orchestrator_singleton():
    """Test PromptOrchestrator singleton caching."""
    from services.prompts.modular_prompt_adapter import get_cached_orchestrator

    logger.info("\n" + "=" * 70)
    logger.info("TEST 1: PromptOrchestrator Singleton Caching")
    logger.info("=" * 70)

    # First call - should create orchestrator
    orch1, time1, err1 = measure_component(
        "First get_cached_orchestrator() call", get_cached_orchestrator
    )

    # Second call - should return cached instance
    orch2, time2, err2 = measure_component(
        "Second get_cached_orchestrator() call (cached)", get_cached_orchestrator
    )

    # Verify singleton behavior
    if orch1 is not None and orch2 is not None:
        is_singleton = orch1 is orch2
        module_count = len(orch1.modules)

        logger.info("\n📊 Results:")
        logger.info(
            f"  - Is singleton: {is_singleton} {'✅' if is_singleton else '❌'}"
        )
        logger.info(
            f"  - Modules registered: {module_count} {'✅' if module_count == 16 else '❌'}"
        )
        logger.info(f"  - First call: {time1:.2f}ms")
        logger.info(f"  - Second call: {time2:.2f}ms (cache hit)")
        logger.info(f"  - Speedup: {time1 / time2:.1f}x faster")

        return {
            "is_singleton": is_singleton,
            "module_count": module_count,
            "first_call_ms": time1,
            "second_call_ms": time2,
            "speedup": time1 / time2 if time2 > 0 else 0,
            "success": is_singleton and module_count == 16,
        }
    else:
        return {"success": False, "error": err1 or err2}


def test_config_caching():
    """Test web lookup config caching."""
    from services.web_lookup.config_loader import (clear_config_cache,
                                                   load_web_lookup_config)

    logger.info("\n" + "=" * 70)
    logger.info("TEST 2: Web Lookup Config Caching")
    logger.info("=" * 70)

    # Clear cache for clean measurement
    clear_config_cache()

    # First call - should load from disk
    config1, time1, err1 = measure_component(
        "First load_web_lookup_config() call", load_web_lookup_config
    )

    # Second call - should return cached config
    config2, time2, err2 = measure_component(
        "Second load_web_lookup_config() call (cached)", load_web_lookup_config
    )

    # Verify caching behavior
    if config1 is not None and config2 is not None:
        is_cached = config1 is config2  # Should be same object
        section_count = len(config1)

        logger.info("\n📊 Results:")
        logger.info(f"  - Is cached: {is_cached} {'✅' if is_cached else '❌'}")
        logger.info(
            f"  - Config sections: {section_count} {'✅' if section_count > 0 else '❌'}"
        )
        logger.info(f"  - First call: {time1:.2f}ms")
        logger.info(f"  - Second call: {time2:.2f}ms (cache hit)")
        logger.info(f"  - Speedup: {time1 / time2:.1f}x faster")

        return {
            "is_cached": is_cached,
            "section_count": section_count,
            "first_call_ms": time1,
            "second_call_ms": time2,
            "speedup": time1 / time2 if time2 > 0 else 0,
            "success": is_cached and section_count > 0,
        }
    else:
        return {"success": False, "error": err1 or err2}


def test_container_initialization():
    """Test full ServiceContainer initialization."""
    from utils.container_manager import get_cached_container

    logger.info("\n" + "=" * 70)
    logger.info("TEST 3: ServiceContainer Initialization (Full Startup)")
    logger.info("=" * 70)

    # Measure full container init
    container, time_ms, err = measure_component(
        "ServiceContainer initialization", get_cached_container
    )

    if container is not None:
        logger.info("\n📊 Results:")
        logger.info("  - Container initialized: ✅")
        logger.info(f"  - Total time: {time_ms:.2f}ms")
        logger.info(f"  - Target: <250ms {'✅' if time_ms < 250 else '❌'}")
        logger.info(f"  - Stretch goal: <200ms {'✅' if time_ms < 200 else '❌'}")

        return {
            "total_time_ms": time_ms,
            "meets_target": time_ms < 250,
            "meets_stretch": time_ms < 200,
            "success": True,
        }
    else:
        return {"success": False, "error": err}


def main():
    """Run all performance tests and generate summary."""
    logger.info("=" * 70)
    logger.info("PERFORMANCE OPTIMIZATION VERIFICATION")
    logger.info("US-201: PromptOrchestrator Singleton + Web Lookup Config Caching")
    logger.info("=" * 70)

    results = {}

    # Test 1: Orchestrator singleton
    results["orchestrator"] = test_orchestrator_singleton()

    # Test 2: Config caching
    results["config"] = test_config_caching()

    # Test 3: Full container initialization
    results["container"] = test_container_initialization()

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("SUMMARY")
    logger.info("=" * 70)

    all_success = all(r.get("success", False) for r in results.values())

    logger.info(f"\n✅ All tests passed: {all_success}")

    if results["orchestrator"].get("success"):
        logger.info(
            f"✅ Orchestrator singleton: "
            f"{results['orchestrator']['speedup']:.1f}x speedup on cache hit"
        )

    if results["config"].get("success"):
        logger.info(
            f"✅ Config caching: "
            f"{results['config']['speedup']:.1f}x speedup on cache hit"
        )

    if results["container"].get("success"):
        total_time = results["container"]["total_time_ms"]
        logger.info(f"✅ Total startup time: {total_time:.2f}ms")

        # Compare to baseline
        baseline = 408.1
        improvement = ((baseline - total_time) / baseline) * 100
        logger.info(f"📈 Improvement vs baseline ({baseline}ms): {improvement:.1f}%")

        if total_time < 200:
            logger.info("🎯 STRETCH GOAL ACHIEVED: <200ms startup!")
        elif total_time < 250:
            logger.info("🎯 TARGET ACHIEVED: <250ms startup!")
        else:
            logger.warning(f"⚠️  Target missed (got {total_time:.2f}ms, target <250ms)")

    # Exit code
    sys.exit(0 if all_success else 1)


if __name__ == "__main__":
    main()
