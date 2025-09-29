#!/usr/bin/env python3
"""Direct test van smart rate limiter zonder dependencies."""

import asyncio
import pytest
import sys
import time
sys.path.insert(0, 'src')

pytestmark = [pytest.mark.performance, pytest.mark.integration]

async def test_direct_rate_limiter():
    """Test smart rate limiter direct."""
    print("🧪 Direct Smart Rate Limiter Test")
    print("=" * 50)

    # Import hier om circular imports te vermijden
    from utils.smart_rate_limiter import get_smart_limiter, RequestPriority

    # Test 1: Maak verschillende rate limiters
    print("\n📊 Test 1: Endpoint-specifieke rate limiters")
    print("-" * 50)

    endpoints = ["endpoint_A", "endpoint_B", "endpoint_C"]

    for endpoint in endpoints:
        limiter = await get_smart_limiter(endpoint)
        print(f"✅ Created rate limiter for: {endpoint}")
        status = limiter.get_queue_status()
        print(f"   Rate: {status['current_rate']} req/s")
        print(f"   Capacity: {limiter.token_bucket.capacity}")

    # Test 2: Test rate limiting
    print("\n\n📊 Test 2: Rate limiting in actie")
    print("-" * 50)

    limiter_a = await get_smart_limiter("endpoint_A")
    limiter_b = await get_smart_limiter("endpoint_B")

    # Test parallel requests
    async def make_request(limiter, endpoint, req_id):
        start = time.time()
        acquired = await limiter.acquire(
            priority=RequestPriority.NORMAL,
            timeout=2.0,
            request_id=f"{endpoint}_req_{req_id}"
        )
        elapsed = time.time() - start
        return (endpoint, req_id, acquired, elapsed)

    # Maak 5 requests per endpoint
    print("\nMaking 5 parallel requests per endpoint...")
    tasks = []

    for i in range(5):
        tasks.append(make_request(limiter_a, "endpoint_A", i))
        tasks.append(make_request(limiter_b, "endpoint_B", i))

    results = await asyncio.gather(*tasks)

    # Analyseer resultaten
    for endpoint in ["endpoint_A", "endpoint_B"]:
        endpoint_results = [r for r in results if r[0] == endpoint]
        success = sum(1 for r in endpoint_results if r[2])
        print(f"\n{endpoint}:")
        print(f"  Success: {success}/5")
        for _, req_id, acquired, elapsed in endpoint_results:
            status = "✅" if acquired else "❌"
            print(f"  {status} Request {req_id}: {elapsed:.2f}s")

    # Test 3: Verificatie dat limiters onafhankelijk zijn
    print("\n\n📊 Test 3: Onafhankelijkheid verificatie")
    print("-" * 50)

    # Check dat we verschillende instanties hebben
    limiter_a2 = await get_smart_limiter("endpoint_A")
    limiter_c = await get_smart_limiter("endpoint_C")

    print(f"endpoint_A same instance: {limiter_a is limiter_a2}")
    print(f"endpoint_A vs endpoint_C: {limiter_a is limiter_c}")

    # Cleanup
    from utils.smart_rate_limiter import cleanup_smart_limiters
    await cleanup_smart_limiters()

    print("\n✅ Test completed!")

if __name__ == "__main__":
    asyncio.run(test_direct_rate_limiter())
