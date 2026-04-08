#!/usr/bin/env python3
"""
Story 2.4 Integration Test
Tests the complete refactoring from legacy to modular architecture.
"""

import asyncio

import pytest

from services.container import ServiceContainer
from services.interfaces import GenerationRequest

pytestmark = [pytest.mark.regression]


async def test_story_2_4_integration():
    """Test that the refactored architecture works end-to-end."""

    print("=" * 60)
    print("STORY 2.4 INTEGRATION TEST")
    print("=" * 60)

    # 1. Initialize container
    print("\n1. Initializing container...")
    container = ServiceContainer()
    orchestrator = container.orchestrator()

    # Verify types
    print(f"   ✓ Orchestrator type: {type(orchestrator).__name__}")
    print(
        f"   ✓ Validation service type: {type(orchestrator.validation_service).__name__}"
    )

    # Check that it's the right type
    from services.orchestrators.validation_orchestrator_v2 import (
        ValidationOrchestratorV2,
    )

    assert isinstance(
        orchestrator.validation_service, ValidationOrchestratorV2
    ), "DefinitionOrchestratorV2 should use ValidationOrchestratorV2"

    # 2. Test validation through orchestrator
    print("\n2. Testing validation through orchestrator...")

    # Create a test request
    import uuid

    request = GenerationRequest(
        id=str(uuid.uuid4()),
        begrip="testbegrip",
        context="Dit is een test context voor validatie.",
    )

    # Call create_definition which internally uses validation
    print("   - Creating definition (triggers validation)...")
    try:
        result = await orchestrator.create_definition(request)

        # Check result structure
        assert result is not None, "Result should not be None"
        assert hasattr(result, "definitie"), "Result should have definitie"
        assert hasattr(
            result, "validation_result"
        ), "Result should have validation_result"

        print("   ✓ Definition created successfully")
        print(f"   ✓ Validation result present: {result.validation_result is not None}")

        # Check validation result structure (if present)
        if result.validation_result:
            val_result = result.validation_result
            assert (
                "is_acceptable" in val_result
            ), "Validation result should have is_acceptable"
            assert (
                "overall_score" in val_result
            ), "Validation result should have overall_score"
            print(f"   ✓ Validation score: {val_result.get('overall_score', 'N/A')}")
            print(f"   ✓ Is acceptable: {val_result.get('is_acceptable', 'N/A')}")

    except Exception as e:
        print(f"   ✗ Error during orchestration: {e}")
        raise

    # 3. Test direct validation through ValidationOrchestratorV2
    print("\n3. Testing direct validation through ValidationOrchestratorV2...")

    import uuid

    from services.validation.interfaces import ValidationContext

    validation_context = ValidationContext(
        correlation_id=uuid.uuid4(), metadata={"test": "story_2_4"}
    )

    val_result = await orchestrator.validation_service.validate_text(
        begrip="testbegrip",
        text="Een test definitie voor Story 2.4 implementatie.",
        ontologische_categorie=None,
        context=validation_context,
    )

    # Check result
    assert val_result is not None, "Validation result should not be None"
    assert "is_acceptable" in val_result, "Should have is_acceptable"
    assert "overall_score" in val_result, "Should have overall_score"
    assert "violations" in val_result, "Should have violations"

    print("   ✓ Direct validation successful")
    print(f"   ✓ Score: {val_result['overall_score']}")
    print(f"   ✓ Acceptable: {val_result['is_acceptable']}")
    print(f"   ✓ Violations: {len(val_result.get('violations', []))}")

    print("\n" + "=" * 60)
    print("✅ STORY 2.4 INTEGRATION TEST PASSED!")
    print("=" * 60)

    return True


if __name__ == "__main__":
    # Run the async test
    result = asyncio.run(test_story_2_4_integration())
    if result:
        print("\n🎉 All Story 2.4 tests passed successfully!")
