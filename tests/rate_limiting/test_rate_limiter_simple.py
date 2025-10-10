#!/usr/bin/env python3
"""Simpele test voor rate limiter met mock API calls."""

import asyncio
import sys
import time

import pytest

sys.path.insert(0, "src")

from utils.integrated_resilience import get_integrated_system, with_full_resilience
from utils.smart_rate_limiter import RequestPriority

pytestmark = [pytest.mark.performance, pytest.mark.integration, pytest.mark.slow]


async def test_rate_limiter():
    """Test rate limiter met gesimuleerde API calls."""
    print("🧪 Rate Limiter Test - Endpoint-Specific Limiting")
    print("=" * 60)

    # Get integrated system
    system = await get_integrated_system()

    # Simuleer API calls voor verschillende endpoints
    async def simulate_api_call(endpoint: str, call_id: int, delay: float = 0.1):
        """Simuleer een API call."""

        @with_full_resilience(
            endpoint_name=endpoint, priority=RequestPriority.NORMAL, timeout=15.0
        )
        async def api_call():
            await asyncio.sleep(delay)
            return f"{endpoint} - Call {call_id} completed"

        return await api_call()

    # Test 1: Parallel calls naar verschillende endpoints
    print("\n📊 Test 1: Parallel calls naar 3 verschillende endpoints")
    print("Elke endpoint heeft eigen rate limiter (3 req/s voor examples)")
    print("-" * 60)

    endpoints = [
        "examples_generation_sentence",
        "examples_generation_practical",
        "examples_generation_counter",
    ]

    # Start 5 calls per endpoint tegelijk
    tasks = []
    start_time = time.time()

    for endpoint in endpoints:
        for i in range(5):
            task = simulate_api_call(endpoint, i)
            tasks.append((endpoint, i, task))

    print(f"\nStarting {len(tasks)} parallel requests...")

    # Track results
    results_by_endpoint = {ep: {"success": 0, "timeout": 0} for ep in endpoints}

    for endpoint, call_id, task in tasks:
        try:
            result = await asyncio.wait_for(task, timeout=20.0)
            elapsed = time.time() - start_time
            print(f"✅ [{elapsed:5.2f}s] {result}")
            results_by_endpoint[endpoint]["success"] += 1
        except TimeoutError:
            elapsed = time.time() - start_time
            print(f"❌ [{elapsed:5.2f}s] {endpoint} - Call {call_id} TIMEOUT")
            results_by_endpoint[endpoint]["timeout"] += 1
        except Exception as e:
            elapsed = time.time() - start_time
            print(
                f"❌ [{elapsed:5.2f}s] {endpoint} - Call {call_id} ERROR: {type(e).__name__}"
            )

    # Resultaten samenvatting
    print(f"\n📊 Resultaten na {time.time() - start_time:.2f}s:")
    for endpoint, stats in results_by_endpoint.items():
        total = stats["success"] + stats["timeout"]
        success_rate = (stats["success"] / total * 100) if total > 0 else 0
        print(f"  {endpoint}: {stats['success']}/{total} ({success_rate:.0f}% success)")

    # Test 2: Sequentiële calls naar 1 endpoint
    print("\n\n📊 Test 2: 10 sequentiële calls naar 1 endpoint")
    print("Met 3 req/s configuratie")
    print("-" * 60)

    endpoint = "examples_generation_sentence"
    success_count = 0
    start_time = time.time()

    for i in range(10):
        try:
            result = await simulate_api_call(endpoint, i, delay=0.2)
            elapsed = time.time() - start_time
            print(f"✅ [{elapsed:5.2f}s] {result}")
            success_count += 1
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ [{elapsed:5.2f}s] Call {i} failed: {type(e).__name__}")

    total_time = time.time() - start_time
    print(f"\nTotaal: {success_count}/10 succesvol in {total_time:.2f}s")
    print(f"Effectieve rate: {10/total_time:.2f} req/s")

    # Test 3: Toon system status
    print("\n\n📊 System Status")
    print("-" * 60)

    status = system.get_system_status()

    print(f"\nActieve rate limiters: {len(status['rate_limiters'])}")
    for endpoint, limiter_status in status["rate_limiters"].items():
        print(f"\n{endpoint}:")
        print(f"  Current rate: {limiter_status['current_rate']:.1f} req/s")
        print(f"  Total requests: {limiter_status['stats']['total_requests']}")
        print(f"  Queued: {limiter_status['stats']['total_queued']}")
        print(f"  Dropped: {limiter_status['stats']['total_dropped']}")

        # Queue status
        queue_total = sum(limiter_status["queue_lengths"].values())
        if queue_total > 0:
            print("  Queue status:")
            for priority, count in limiter_status["queue_lengths"].items():
                if count > 0:
                    print(f"    {priority}: {count}")

    # Cleanup
    await system.stop()

    print("\n\n✅ Test completed!")


if __name__ == "__main__":
    asyncio.run(test_rate_limiter())
