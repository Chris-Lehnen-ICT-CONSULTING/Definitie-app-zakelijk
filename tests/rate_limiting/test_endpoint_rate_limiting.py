#!/usr/bin/env python3
"""Test script voor endpoint-specifieke rate limiting."""

import asyncio
import sys
import time

import pytest

sys.path.insert(0, "src")

from utils.integrated_resilience import get_integrated_system
from utils.smart_rate_limiter import (
    RequestPriority,
    get_smart_limiter,
    with_smart_rate_limit,
)


@pytest.mark.performance
@pytest.mark.integration
async def test_endpoint_specific_rate_limiting():
    """Test dat verschillende endpoints hun eigen rate limiting hebben."""
    print("🧪 Testing Endpoint-Specific Rate Limiting")
    print("=" * 50)

    # Test data
    endpoints = [
        "examples_generation_sentence",
        "examples_generation_practical",
        "examples_generation_counter",
    ]

    # Simuleer API calls voor verschillende endpoints
    async def simulate_api_call(endpoint: str, call_id: int):
        """Simuleer een API call met rate limiting."""

        @with_smart_rate_limit(
            endpoint_name=endpoint, priority=RequestPriority.NORMAL, timeout=5.0
        )
        async def api_call():
            await asyncio.sleep(0.1)  # Simuleer API latency
            return f"{endpoint} - Call {call_id} completed"

        return await api_call()

    # Test 1: Parallel calls naar verschillende endpoints
    print("\n📊 Test 1: Parallel calls naar verschillende endpoints")
    print("-" * 50)

    start_time = time.time()
    tasks = []

    # Maak 3 calls per endpoint tegelijkertijd
    for endpoint in endpoints:
        for i in range(3):
            task = simulate_api_call(endpoint, i)
            tasks.append((endpoint, i, task))

    # Voer alle tasks parallel uit
    results = []
    for endpoint, call_id, task in tasks:
        try:
            result = await asyncio.wait_for(task, timeout=10.0)
            elapsed = time.time() - start_time
            print(f"✅ [{elapsed:.2f}s] {result}")
            results.append((endpoint, True))
        except TimeoutError:
            elapsed = time.time() - start_time
            print(f"❌ [{elapsed:.2f}s] {endpoint} - Call {call_id} TIMEOUT")
            results.append((endpoint, False))

    # Analyseer resultaten
    print("\n📊 Resultaten:")
    for endpoint in endpoints:
        successes = sum(1 for e, success in results if e == endpoint and success)
        failures = sum(1 for e, success in results if e == endpoint and not success)
        print(f"  {endpoint}: {successes} success, {failures} failures")

    # Test 2: Sequentiële calls naar hetzelfde endpoint
    print("\n📊 Test 2: Sequentiële calls naar hetzelfde endpoint")
    print("-" * 50)

    endpoint = "test_sequential"
    start_time = time.time()

    for i in range(5):
        try:
            result = await simulate_api_call(endpoint, i)
            elapsed = time.time() - start_time
            print(f"✅ [{elapsed:.2f}s] {result}")
        except TimeoutError:
            elapsed = time.time() - start_time
            print(f"❌ [{elapsed:.2f}s] {endpoint} - Call {i} TIMEOUT")

    # Test 3: Test met integrated resilience system
    print("\n📊 Test 3: Integrated resilience system")
    print("-" * 50)

    system = await get_integrated_system()

    async def resilient_call(endpoint: str, call_id: int):
        """Test call met volledig resilience systeem."""

        async def mock_api():
            await asyncio.sleep(0.1)
            return f"{endpoint} - Resilient call {call_id}"

        return await system.execute_with_full_resilience(
            mock_api,
            endpoint_name=endpoint,
            priority=RequestPriority.NORMAL,
            timeout=5.0,
        )

    # Test verschillende endpoints met resilience
    tasks = []
    for endpoint in endpoints:
        for i in range(2):
            task = resilient_call(endpoint, i)
            tasks.append(task)

    start_time = time.time()
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for _i, result in enumerate(results):
        elapsed = time.time() - start_time
        if isinstance(result, Exception):
            print(f"❌ [{elapsed:.2f}s] Error: {result}")
        else:
            print(f"✅ [{elapsed:.2f}s] {result}")

    # Toon systeem status
    status = system.get_system_status()
    print("\n📊 System Status:")
    print(f"  Active rate limiters: {len(status['rate_limiters'])}")
    for endpoint, limiter_status in status["rate_limiters"].items():
        print(f"  - {endpoint}: {limiter_status['current_rate']:.2f} req/s")

    # Cleanup
    await system.stop()


if __name__ == "__main__":
    asyncio.run(test_endpoint_specific_rate_limiting())
