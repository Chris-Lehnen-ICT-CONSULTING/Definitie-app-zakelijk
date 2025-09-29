#!/usr/bin/env python3
"""Test script om te checken of rate limiter endpoints correct werken."""

import asyncio
import pytest
import sys
sys.path.insert(0, 'src')

from utils.integrated_resilience import IntegratedResilienceSystem

pytestmark = [pytest.mark.performance, pytest.mark.integration]

async def test_endpoints():
    """Test verschillende endpoints."""
    resilience = IntegratedResilienceSystem()

    # Test data
    endpoints = [
        "examples_generation_sentence",
        "examples_generation_practical",
        "examples_generation_counter"
    ]

    for endpoint in endpoints:
        print(f"\nTesting endpoint: {endpoint}")
        try:
            # Dummy call
            result = await resilience.resilient_call(
                endpoint_name=endpoint,
                func=lambda: f"Test result for {endpoint}",
                timeout=5.0
            )
            print(f"✅ {endpoint}: Success - {result}")
        except Exception as e:
            print(f"❌ {endpoint}: Failed - {e}")

if __name__ == "__main__":
    asyncio.run(test_endpoints())
