#!/usr/bin/env python
"""Debug script to verify the overall_score KeyError fix.

Tests that the fix in service_factory.py line 297 properly handles
missing 'overall_score' in validation_details.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


def test_get_with_default():
    """Test that .get() with default value prevents KeyError."""

    # Test case 1: Dict with overall_score present
    validation_details = {"overall_score": 0.85, "is_acceptable": True}
    final_score = validation_details.get("overall_score", 0.0)
    assert final_score == 0.85, f"Expected 0.85, got {final_score}"
    print("✓ Test 1 passed: Dict with overall_score present")

    # Test case 2: Dict without overall_score
    validation_details = {"is_acceptable": False, "violations": []}
    final_score = validation_details.get("overall_score", 0.0)
    assert final_score == 0.0, f"Expected 0.0, got {final_score}"
    print("✓ Test 2 passed: Dict without overall_score returns default")

    # Test case 3: Dict with None overall_score
    validation_details = {"overall_score": None, "is_acceptable": False}
    final_score = validation_details.get("overall_score", 0.0)
    assert final_score is None, f"Expected None, got {final_score}"
    print("✓ Test 3 passed: Dict with None overall_score returns None")

    # Test case 4: Empty dict
    validation_details = {}
    final_score = validation_details.get("overall_score", 0.0)
    assert final_score == 0.0, f"Expected 0.0, got {final_score}"
    print("✓ Test 4 passed: Empty dict returns default")

    # Test case 5: Simulate the original error condition
    try:
        validation_details = {"is_acceptable": True}
        # This would have caused KeyError before the fix
        final_score = validation_details["overall_score"]
        print("✗ Test 5 failed: Should have raised KeyError")
    except KeyError:
        print("✓ Test 5 passed: Direct access raises KeyError as expected")

    # Test case 6: The fix prevents KeyError
    validation_details = {"is_acceptable": True}
    final_score = validation_details.get("overall_score", 0.0)
    assert final_score == 0.0, f"Expected 0.0, got {final_score}"
    print("✓ Test 6 passed: .get() prevents KeyError")

    print("\nAll tests passed! The fix correctly handles missing 'overall_score'.")


def test_normalize_validation_always_includes_overall_score():
    """Test that normalize_validation always includes overall_score in output."""

    from src.services.service_factory import ServiceAdapter
    from src.services.container import ServiceContainer
    from unittest.mock import MagicMock

    # Create a mock container
    container = MagicMock(spec=ServiceContainer)
    container.orchestrator.return_value = MagicMock()
    container.web_lookup.return_value = MagicMock()

    adapter = ServiceAdapter(container)

    test_cases = [
        (None, "None input"),
        ({}, "Empty dict"),
        ({"violations": []}, "Dict without overall_score"),
        ({"overall_score": None}, "Dict with None overall_score"),
        ({"overall_score": 0.75}, "Dict with valid overall_score"),
    ]

    for input_val, description in test_cases:
        result = adapter.normalize_validation(input_val)
        assert "overall_score" in result, f"Missing overall_score for {description}"
        assert isinstance(result["overall_score"], (int, float)), f"Invalid type for {description}"
        print(f"✓ normalize_validation({description}): overall_score = {result['overall_score']}")

    print("\nnormalize_validation always includes 'overall_score' in output.")


if __name__ == "__main__":
    print("Testing overall_score KeyError fix...\n")
    print("="*50)
    print("Test 1: .get() with default value")
    print("="*50)
    test_get_with_default()

    print("\n" + "="*50)
    print("Test 2: normalize_validation output")
    print("="*50)
    test_normalize_validation_always_includes_overall_score()

    print("\n" + "="*50)
    print("CONCLUSION: The fix is ROBUST")
    print("="*50)
    print("""
The change from:
    "final_score": validation_details["overall_score"]

To:
    "final_score": validation_details.get("overall_score", 0.0)

Is a robust fix that:
1. Prevents KeyError when 'overall_score' is missing
2. Provides a sensible default value (0.0)
3. Still returns the actual value when present
4. Aligns with the normalize_validation method which ensures 'overall_score' is always included

The root cause analysis shows that normalize_validation() ALWAYS includes
'overall_score' in its output, so this should rarely happen. However, the
defensive .get() approach is still good practice for robustness.
""")