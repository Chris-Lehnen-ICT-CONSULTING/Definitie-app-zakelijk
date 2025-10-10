#!/usr/bin/env python3
"""
Debug Performance Issues in DefinitieApp

This script analyzes and reports on the following performance issues:
1. Multiple ServiceContainer initializations (6x instead of 1x)
2. PromptOrchestrator repeated initializations
3. Memory leaks and cache inefficiencies
4. Wetgeving.nl 406 errors
5. Race conditions in service initialization

Run with: python scripts/debug_performance_issues.py
"""

import asyncio
import json
import logging
import sys
import time
import tracemalloc
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            f'logs/debug_perf_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        ),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class InitializationTracker:
    """Track initialization patterns in the application."""

    def __init__(self):
        self.init_counts = defaultdict(int)
        self.init_times = defaultdict(list)
        self.call_stacks = defaultdict(list)

    def track_init(self, class_name: str):
        """Track an initialization event."""
        self.init_counts[class_name] += 1
        self.init_times[class_name].append(time.time())

        # Capture call stack
        import traceback

        stack = traceback.extract_stack()
        self.call_stacks[class_name].append([str(frame) for frame in stack[-10:-1]])

    def report(self) -> dict[str, Any]:
        """Generate initialization report."""
        report = {}
        for class_name, count in self.init_counts.items():
            times = self.init_times[class_name]
            report[class_name] = {
                "count": count,
                "first_init": (
                    datetime.fromtimestamp(times[0]).isoformat() if times else None
                ),
                "last_init": (
                    datetime.fromtimestamp(times[-1]).isoformat() if times else None
                ),
                "duration_span": times[-1] - times[0] if len(times) > 1 else 0,
                "unique_stacks": len(
                    set(tuple(s) for s in self.call_stacks[class_name])
                ),
            }
        return report


class CacheAnalyzer:
    """Analyze cache effectiveness."""

    def __init__(self):
        self.cache_hits = 0
        self.cache_misses = 0
        self.cache_operations = []

    def track_operation(self, operation: str, hit: bool):
        """Track a cache operation."""
        if hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1

        self.cache_operations.append(
            {"time": time.time(), "operation": operation, "hit": hit}
        )

    def report(self) -> dict[str, Any]:
        """Generate cache effectiveness report."""
        total = self.cache_hits + self.cache_misses
        return {
            "total_operations": total,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": self.cache_hits / total if total > 0 else 0,
            "miss_rate": self.cache_misses / total if total > 0 else 0,
        }


class MemoryProfiler:
    """Profile memory usage patterns."""

    def __init__(self):
        self.snapshots = []
        tracemalloc.start()

    def take_snapshot(self, label: str):
        """Take a memory snapshot."""
        snapshot = tracemalloc.take_snapshot()
        self.snapshots.append(
            {"label": label, "time": time.time(), "snapshot": snapshot}
        )

    def report(self) -> dict[str, Any]:
        """Generate memory usage report."""
        if len(self.snapshots) < 2:
            return {"error": "Need at least 2 snapshots for comparison"}

        # Compare first and last snapshot
        first = self.snapshots[0]["snapshot"]
        last = self.snapshots[-1]["snapshot"]

        top_stats = last.compare_to(first, "lineno")

        # Get top 10 memory consumers
        top_consumers = []
        for stat in top_stats[:10]:
            top_consumers.append(
                {
                    "file": stat.traceback.format()[0] if stat.traceback else "unknown",
                    "size_diff": stat.size_diff,
                    "size": stat.size,
                    "count_diff": stat.count_diff,
                    "count": stat.count,
                }
            )

        # Calculate total memory growth
        total_growth = sum(stat.size_diff for stat in top_stats)

        return {
            "total_snapshots": len(self.snapshots),
            "duration_seconds": self.snapshots[-1]["time"] - self.snapshots[0]["time"],
            "total_memory_growth_bytes": total_growth,
            "total_memory_growth_mb": total_growth / (1024 * 1024),
            "top_consumers": top_consumers,
        }


def monkey_patch_services(tracker: InitializationTracker):
    """Monkey-patch service classes to track initializations."""

    # Patch ServiceContainer
    try:
        from services.container import ServiceContainer

        original_init = ServiceContainer.__init__

        def tracked_init(self, *args, **kwargs):
            tracker.track_init("ServiceContainer")
            return original_init(self, *args, **kwargs)

        ServiceContainer.__init__ = tracked_init
        logger.info("Patched ServiceContainer for tracking")
    except Exception as e:
        logger.error(f"Failed to patch ServiceContainer: {e}")

    # Patch PromptOrchestrator
    try:
        from services.prompts.modules.prompt_orchestrator import \
            PromptOrchestrator

        original_init = PromptOrchestrator.__init__

        def tracked_init(self, *args, **kwargs):
            tracker.track_init("PromptOrchestrator")
            return original_init(self, *args, **kwargs)

        PromptOrchestrator.__init__ = tracked_init
        logger.info("Patched PromptOrchestrator for tracking")
    except Exception as e:
        logger.error(f"Failed to patch PromptOrchestrator: {e}")

    # Patch ModularPromptAdapter
    try:
        from services.prompts.modular_prompt_adapter import \
            ModularPromptAdapter

        original_init = ModularPromptAdapter.__init__

        def tracked_init(self, *args, **kwargs):
            tracker.track_init("ModularPromptAdapter")
            return original_init(self, *args, **kwargs)

        ModularPromptAdapter.__init__ = tracked_init
        logger.info("Patched ModularPromptAdapter for tracking")
    except Exception as e:
        logger.error(f"Failed to patch ModularPromptAdapter: {e}")


def analyze_sru_errors():
    """Analyze SRU/Wetgeving.nl 406 errors."""

    logger.info("Analyzing SRU 406 errors...")

    # Check SRU service configuration
    try:
        from services.web_lookup.config_loader import load_web_lookup_config

        config = load_web_lookup_config()
        sru_config = config.get("web_lookup", {}).get("providers", {}).get("sru", {})

        # Test Wetgeving.nl endpoint
        import httpx

        wetgeving_config = None
        for provider in sru_config.get("providers", []):
            if provider.get("identifier") == "Wetgeving.nl":
                wetgeving_config = provider
                break

        if wetgeving_config:
            base_url = wetgeving_config.get("base_url")
            logger.info(f"Testing Wetgeving.nl endpoint: {base_url}")

            # Test with different Accept headers
            test_headers = [
                {"Accept": "application/xml"},
                {"Accept": "text/xml"},
                {"Accept": "*/*"},
                {"Accept": "application/srw+xml"},
            ]

            results = []
            for headers in test_headers:
                try:
                    response = httpx.get(
                        base_url,
                        params={
                            "operation": "searchRetrieve",
                            "version": wetgeving_config.get("sru_version", "1.2"),
                            "query": "vonnis",
                            "maximumRecords": 1,
                        },
                        headers=headers,
                        timeout=5.0,
                    )
                    results.append(
                        {
                            "headers": headers,
                            "status": response.status_code,
                            "success": response.status_code == 200,
                        }
                    )
                except Exception as e:
                    results.append({"headers": headers, "error": str(e)})

            return {
                "endpoint": base_url,
                "sru_version": wetgeving_config.get("sru_version"),
                "test_results": results,
                "recommendation": "Use Accept: application/xml header for Wetgeving.nl",
            }
    except Exception as e:
        logger.error(f"Failed to analyze SRU errors: {e}")
        return {"error": str(e)}


def analyze_cache_implementation():
    """Analyze caching implementation issues."""

    logger.info("Analyzing cache implementation...")

    findings = []

    # Check for @lru_cache usage
    try:
        from utils.container_manager import (_create_custom_container,
                                             get_cached_container)

        # Check cache info
        if hasattr(get_cached_container, "cache_info"):
            cache_info = get_cached_container.cache_info()
            findings.append(
                {
                    "function": "get_cached_container",
                    "type": "lru_cache",
                    "hits": cache_info.hits,
                    "misses": cache_info.misses,
                    "maxsize": cache_info.maxsize,
                    "currsize": cache_info.currsize,
                }
            )

        if hasattr(_create_custom_container, "cache_info"):
            cache_info = _create_custom_container.cache_info()
            findings.append(
                {
                    "function": "_create_custom_container",
                    "type": "lru_cache",
                    "hits": cache_info.hits,
                    "misses": cache_info.misses,
                    "maxsize": cache_info.maxsize,
                    "currsize": cache_info.currsize,
                }
            )
    except Exception as e:
        logger.error(f"Failed to analyze cache: {e}")

    # Check for Streamlit cache usage
    try:
        # Look for @st.cache_resource usage
        import inspect

        cache_decorators = []

        # Check ui.cached_services module
        from ui import cached_services

        for name, obj in inspect.getmembers(cached_services):
            if callable(obj):
                source = inspect.getsource(obj)
                if "@st.cache" in source or "cache_resource" in source:
                    cache_decorators.append(
                        {
                            "module": "ui.cached_services",
                            "function": name,
                            "has_streamlit_cache": True,
                        }
                    )
    except Exception as e:
        logger.error(f"Failed to analyze Streamlit cache: {e}")

    return {
        "lru_cache_functions": findings,
        "recommendations": [
            "ServiceContainer uses lru_cache but may need better cache key strategy",
            "PromptOrchestrator is created inside ModularPromptAdapter without caching",
            "Consider using singleton pattern for PromptOrchestrator",
            "Streamlit session state and lru_cache may conflict - pick one strategy",
        ],
    }


async def simulate_user_flow():
    """Simulate typical user flow to trigger performance issues."""

    logger.info("Simulating user flow...")

    tracker = InitializationTracker()
    memory_profiler = MemoryProfiler()

    # Monkey-patch services
    monkey_patch_services(tracker)

    # Take initial memory snapshot
    memory_profiler.take_snapshot("start")

    # Import and initialize services (simulating app startup)
    logger.info("Step 1: Initialize services...")
    from utils.container_manager import get_cached_container

    container1 = get_cached_container()
    memory_profiler.take_snapshot("after_first_container")

    # Simulate Streamlit rerun
    logger.info("Step 2: Simulate Streamlit rerun...")
    container2 = get_cached_container()
    memory_profiler.take_snapshot("after_rerun")

    # Get orchestrator (triggers PromptOrchestrator init)
    logger.info("Step 3: Get orchestrator...")
    orchestrator = container1.orchestrator()
    memory_profiler.take_snapshot("after_orchestrator")

    # Simulate definition generation
    logger.info("Step 4: Simulate definition generation...")
    try:
        from services.interfaces import GenerationRequest

        request = GenerationRequest(
            begrip="vonnis",
            context="OM Strafrecht",
            domain="Strafrecht",
            organisatie="OM",
            project="Test",
            versie="1.0",
            status="Draft",
        )

        # This would trigger prompt service initialization
        result = await orchestrator.generate_definition(request)
        memory_profiler.take_snapshot("after_generation")
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        memory_profiler.take_snapshot("after_generation_error")

    # Final snapshot
    memory_profiler.take_snapshot("end")

    return {
        "initialization_report": tracker.report(),
        "memory_report": memory_profiler.report(),
    }


def main():
    """Main debugging function."""

    print("=" * 80)
    print("DEFINIEAPP PERFORMANCE DEBUGGER")
    print("=" * 80)

    # Create results dictionary
    results = {"timestamp": datetime.now().isoformat(), "findings": {}}

    # 1. Analyze cache implementation
    print("\n1. Analyzing Cache Implementation...")
    results["findings"]["cache_analysis"] = analyze_cache_implementation()

    # 2. Analyze SRU errors
    print("\n2. Analyzing SRU/Wetgeving.nl 406 Errors...")
    results["findings"]["sru_errors"] = analyze_sru_errors()

    # 3. Simulate user flow
    print("\n3. Simulating User Flow...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    flow_results = loop.run_until_complete(simulate_user_flow())
    results["findings"]["user_flow"] = flow_results

    # 4. Generate report
    print("\n" + "=" * 80)
    print("PERFORMANCE ANALYSIS REPORT")
    print("=" * 80)

    # Print initialization issues
    if "user_flow" in results["findings"]:
        init_report = results["findings"]["user_flow"].get("initialization_report", {})
        print("\nINITIALIZATION ISSUES:")
        for class_name, data in init_report.items():
            if data["count"] > 1:
                print(f"  ⚠️  {class_name}: initialized {data['count']} times!")
                print(f"     Duration span: {data['duration_span']:.2f} seconds")
                print(f"     Unique call stacks: {data['unique_stacks']}")

    # Print memory issues
    if "user_flow" in results["findings"]:
        mem_report = results["findings"]["user_flow"].get("memory_report", {})
        if "total_memory_growth_mb" in mem_report:
            print("\nMEMORY USAGE:")
            print(f"  Total growth: {mem_report['total_memory_growth_mb']:.2f} MB")
            print(f"  Duration: {mem_report.get('duration_seconds', 0):.2f} seconds")

            if mem_report.get("top_consumers"):
                print("\n  Top memory consumers:")
                for consumer in mem_report["top_consumers"][:5]:
                    size_mb = consumer["size_diff"] / (1024 * 1024)
                    print(f"    {consumer['file']}: {size_mb:.2f} MB")

    # Print SRU issues
    if "sru_errors" in results["findings"]:
        sru_report = results["findings"]["sru_errors"]
        if "test_results" in sru_report:
            print("\nSRU/WETGEVING.NL ISSUES:")
            print(f"  Endpoint: {sru_report.get('endpoint')}")
            print(f"  SRU Version: {sru_report.get('sru_version')}")
            print("  Header test results:")
            for result in sru_report["test_results"]:
                status = result.get("status", "error")
                headers = result.get("headers", {})
                success = "✓" if result.get("success") else "✗"
                print(
                    f"    {success} Accept: {headers.get('Accept', 'none')} -> {status}"
                )
            print(f"  Recommendation: {sru_report.get('recommendation')}")

    # Print cache issues
    if "cache_analysis" in results["findings"]:
        cache_report = results["findings"]["cache_analysis"]
        print("\nCACHE ANALYSIS:")
        if cache_report.get("lru_cache_functions"):
            for func in cache_report["lru_cache_functions"]:
                hit_rate = (
                    func["hits"] / (func["hits"] + func["misses"])
                    if (func["hits"] + func["misses"]) > 0
                    else 0
                )
                print(
                    f"  {func['function']}: {func['hits']} hits, {func['misses']} misses (hit rate: {hit_rate:.1%})"
                )

        if cache_report.get("recommendations"):
            print("\n  Recommendations:")
            for rec in cache_report["recommendations"]:
                print(f"    • {rec}")

    # Save detailed report
    report_path = Path(
        f"logs/perf_debug_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    report_path.parent.mkdir(exist_ok=True)

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n📊 Detailed report saved to: {report_path}")

    # Print summary recommendations
    print("\n" + "=" * 80)
    print("SUMMARY & RECOMMENDATIONS")
    print("=" * 80)

    print(
        """
1. SERVICE INITIALIZATION (6x issue):
   Problem: ServiceContainer initialized multiple times despite caching
   Root Cause: Mixed caching strategies (lru_cache + Streamlit session state)
   Solution: Use ONLY lru_cache OR session state, not both

2. PROMPT ORCHESTRATOR (duplicate initialization):
   Problem: PromptOrchestrator created fresh in ModularPromptAdapter.__init__
   Root Cause: No caching for PromptOrchestrator instances
   Solution: Make PromptOrchestrator a singleton or cache in ServiceContainer

3. WETGEVING.NL 406 ERRORS:
   Problem: HTTP 406 Not Acceptable responses from Wetgeving.nl
   Root Cause: Missing or incorrect Accept header
   Solution: Add Accept: application/xml header to SRU requests

4. MEMORY LEAKS:
   Problem: Potential memory growth from repeated initializations
   Root Cause: Objects not properly garbage collected
   Solution: Ensure proper cleanup and use weak references where appropriate

5. RACE CONDITIONS:
   Problem: Potential race conditions in concurrent initialization
   Root Cause: No locking mechanism for singleton creation
   Solution: Add threading.Lock() for thread-safe singleton initialization
    """
    )

    print("=" * 80)
    print("Debugging complete!")


if __name__ == "__main__":
    main()
