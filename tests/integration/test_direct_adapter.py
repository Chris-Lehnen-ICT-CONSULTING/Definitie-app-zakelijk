#!/usr/bin/env python3
"""Test ServiceAdapter directly."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.services.service_factory import get_definition_service


async def test_service_adapter():
    """Test ServiceAdapter directly."""
    print("1. Getting definition service (ServiceAdapter)...")
    adapter = get_definition_service()
    print(f"2. Got adapter: {type(adapter).__name__}")

    begrip = "overeenkomst"
    context_dict = {
        "organisatorisch": ["Rechtbank"],
        "juridisch": ["Burgerlijk recht"],
        "wettelijk": ["BW"],
    }

    print("3. Calling generate_definition (async method)...")
    try:
        result = await adapter.generate_definition(begrip, context_dict)
        print(
            f"4. Success! Result keys: {list(result.keys()) if isinstance(result, dict) else type(result)}"
        )
        if result.get("success"):
            print(f"   Definition: {result.get('definitie_gecorrigeerd', '')[:100]}...")
        return result
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("Testing ServiceAdapter async generation...")
    result = asyncio.run(test_service_adapter())
    if result:
        print(f"\nFinal success: {result.get('success', False)}")
