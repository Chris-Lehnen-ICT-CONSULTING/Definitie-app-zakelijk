#!/usr/bin/env python3
"""Test script voor rate limit configuratie verificatie."""

import asyncio
import sys

import pytest

sys.path.insert(0, "src")

from config.rate_limit_config import (
    get_all_endpoints,
    get_endpoint_timeout,
    get_rate_limit_config,
)
from utils.smart_rate_limiter import get_smart_limiter

pytestmark = [pytest.mark.integration]


async def test_config_loading():
    """Test dat configuraties correct worden geladen."""
    print("🧪 Testing Rate Limit Configuration Loading")
    print("=" * 50)

    # Test 1: Controleer dat configuraties correct geladen worden
    print("\n📊 Test 1: Configuration Loading")
    print("-" * 50)

    endpoints_to_test = [
        "examples_generation_sentence",
        "examples_generation_practical",
        "definition_generation",
        "web_search",
        "non_existent_endpoint",
    ]

    for endpoint in endpoints_to_test:
        config = get_rate_limit_config(endpoint)
        timeout = get_endpoint_timeout(endpoint)

        print(f"\n{endpoint}:")
        print(f"  - Tokens per second: {config.tokens_per_second}")
        print(f"  - Bucket capacity: {config.bucket_capacity}")
        print(f"  - Burst capacity: {config.burst_capacity}")
        print(f"  - Target response time: {config.target_response_time}s")
        print(f"  - Timeout: {timeout}s")

    # Test 2: Verifieer dat smart limiter de juiste configuratie gebruikt
    print("\n\n📊 Test 2: Smart Limiter Configuration")
    print("-" * 50)

    for endpoint in ["examples_generation_sentence", "web_search"]:
        limiter = await get_smart_limiter(endpoint)
        status = limiter.get_queue_status()

        print(f"\n{endpoint} limiter status:")
        print(f"  - Current rate: {status['current_rate']} req/s")
        print(f"  - Token bucket tokens: {status['token_bucket_tokens']}")
        print(f"  - Queue lengths: {status['queue_lengths']}")

    # Test 3: Laat alle geconfigureerde endpoints zien
    print("\n\n📊 Test 3: All Configured Endpoints")
    print("-" * 50)

    all_endpoints = get_all_endpoints()
    print(f"\nTotal configured endpoints: {len(all_endpoints)}")
    for i, endpoint in enumerate(all_endpoints, 1):
        print(f"  {i}. {endpoint}")

    # Cleanup
    from utils.smart_rate_limiter import cleanup_smart_limiters

    await cleanup_smart_limiters()


if __name__ == "__main__":
    asyncio.run(test_config_loading())
