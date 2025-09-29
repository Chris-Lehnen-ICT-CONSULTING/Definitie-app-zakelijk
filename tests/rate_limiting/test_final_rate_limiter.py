#!/usr/bin/env python3
"""Finale test voor rate limiter met endpoint-specifieke configuraties."""

import asyncio
import pytest
import sys
import time
sys.path.insert(0, 'src')

from utils.integrated_resilience import get_integrated_system
from utils.smart_rate_limiter import RequestPriority

@pytest.mark.performance
@pytest.mark.integration
async def test_final_rate_limiting():
    """Test finale rate limiting met realistische scenario's."""
    print("🧪 Final Rate Limiting Test")
    print("=" * 50)

    system = await get_integrated_system()

    # Test 1: Voorbeelden generatie - 3 requests per seconde toegestaan
    print("\n📊 Test 1: Voorbeelden Generatie (3 req/s configured)")
    print("-" * 50)

    async def generate_examples(endpoint: str, example_id: int):
        """Simuleer voorbeelden generatie."""
        async def mock_generation():
            await asyncio.sleep(0.2)  # Simuleer API call
            return f"{endpoint} - Example {example_id}"

        return await system.execute_with_full_resilience(
            mock_generation,
            endpoint_name=endpoint,
            priority=RequestPriority.NORMAL,
            timeout=15.0  # Gebruik configuratie timeout
        )

    # Test met 5 parallelle requests (zou allemaal moeten slagen met 3 req/s)
    start_time = time.time()
    tasks = []

    for i in range(5):
        task = generate_examples("examples_generation_sentence", i)
        tasks.append(task)

    results = await asyncio.gather(*tasks, return_exceptions=True)

    success_count = 0
    for i, result in enumerate(results):
        elapsed = time.time() - start_time
        if isinstance(result, Exception):
            print(f"❌ [{elapsed:.2f}s] Request {i}: {type(result).__name__}")
        else:
            success_count += 1
            print(f"✅ [{elapsed:.2f}s] {result}")

    print(f"\nSuccess rate: {success_count}/5 ({success_count/5*100:.0f}%)")

    # Test 2: Web search - 1 request per seconde
    print("\n\n📊 Test 2: Web Search (1 req/s configured)")
    print("-" * 50)

    async def web_search(query_id: int):
        """Simuleer web search."""
        async def mock_search():
            await asyncio.sleep(0.5)  # Langzamere operatie
            return f"Search result {query_id}"

        return await system.execute_with_full_resilience(
            mock_search,
            endpoint_name="web_search",
            priority=RequestPriority.NORMAL,
            timeout=30.0
        )

    # Test met 3 requests
    start_time = time.time()

    for i in range(3):
        try:
            result = await web_search(i)
            elapsed = time.time() - start_time
            print(f"✅ [{elapsed:.2f}s] {result}")
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ [{elapsed:.2f}s] Request {i}: {type(e).__name__}")

    # Test 3: Verschillende prioriteiten
    print("\n\n📊 Test 3: Priority-based Rate Limiting")
    print("-" * 50)

    async def priority_call(priority: RequestPriority, call_id: int):
        """Test met verschillende prioriteiten."""
        async def mock_call():
            await asyncio.sleep(0.1)
            return f"{priority.name} call {call_id}"

        return await system.execute_with_full_resilience(
            mock_call,
            endpoint_name="definition_generation",
            priority=priority,
            timeout=10.0
        )

    # Mix van prioriteiten
    tasks = [
        priority_call(RequestPriority.CRITICAL, 1),
        priority_call(RequestPriority.NORMAL, 2),
        priority_call(RequestPriority.LOW, 3),
        priority_call(RequestPriority.HIGH, 4),
        priority_call(RequestPriority.BACKGROUND, 5),
    ]

    start_time = time.time()
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for i, result in enumerate(results):
        elapsed = time.time() - start_time
        if isinstance(result, Exception):
            print(f"❌ [{elapsed:.2f}s] Task {i+1}: {type(result).__name__}")
        else:
            print(f"✅ [{elapsed:.2f}s] {result}")

    # Toon finale status
    print("\n\n📊 System Status:")
    print("-" * 50)

    status = system.get_system_status()

    print(f"Active endpoints: {len(status['rate_limiters'])}")
    for endpoint, limiter_status in status['rate_limiters'].items():
        print(f"\n{endpoint}:")
        print(f"  - Current rate: {limiter_status['current_rate']:.1f} req/s")
        print(f"  - Total requests: {limiter_status['stats']['total_requests']}")
        print(f"  - Queued: {limiter_status['stats']['total_queued']}")
        print(f"  - Dropped: {limiter_status['stats']['total_dropped']}")
        print(f"  - Avg response time: {limiter_status['stats']['avg_response_time']:.2f}s")

    # Cleanup
    await system.stop()

if __name__ == "__main__":
    asyncio.run(test_final_rate_limiting())
