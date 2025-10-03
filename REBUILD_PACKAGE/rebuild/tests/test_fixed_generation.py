#!/usr/bin/env python3
"""Test if definition generation works after timeout fix."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.services.service_factory import get_definition_service
from src.ui.helpers.async_bridge import generate_definition_sync


def test_generation_with_fixed_timeout():
    """Test generation with fixed timeout."""
    print("=== TESTING WITH FIXED TIMEOUT ===\n")

    print("1. Getting service adapter...")
    service_adapter = get_definition_service()
    print(f"   Got: {type(service_adapter).__name__}")

    begrip = "overeenkomst"
    context_dict = {
        "organisatorisch": ["Rechtbank"],
        "juridisch": ["Burgerlijk recht"],
        "wettelijk": ["BW"],
    }

    print(f"2. Generating definition for: {begrip}")
    print(f"   Context: {context_dict}")

    try:
        # Use the fixed async_bridge with proper timeout
        result = generate_definition_sync(
            service_adapter, begrip=begrip, context_dict=context_dict
        )

        print("\n3. SUCCESS! Result received")
        print(f"   Type: {type(result)}")

        if isinstance(result, dict):
            print(f"   Keys: {list(result.keys())}")
            print(f"   Success: {result.get('success', False)}")

            if result.get("definitie_gecorrigeerd"):
                print(f"   Definition: {result['definitie_gecorrigeerd'][:100]}...")
            else:
                print("   WARNING: No 'definitie_gecorrigeerd' in result")

            if result.get("final_score") is not None:
                print(f"   Score: {result['final_score']}")

            if result.get("validation_details"):
                print(
                    f"   Validation: {result['validation_details'].get('overall_score', 'N/A')}"
                )

        return result

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = test_generation_with_fixed_timeout()
    if result and result.get("success"):
        print("\n✅ Test PASSED - Definition generation works!")
    else:
        print("\n❌ Test FAILED - Check the errors above")
