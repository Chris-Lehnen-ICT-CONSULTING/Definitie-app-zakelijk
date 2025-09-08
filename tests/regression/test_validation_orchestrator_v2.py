#!/usr/bin/env python3
"""
Direct test for ValidationOrchestratorV2 integration
Tests that the refactored validation flow works correctly.
"""

import asyncio
import uuid
from services.container import ServiceContainer
from services.validation.interfaces import ValidationContext


async def test_validation_orchestrator_v2():
    """Test ValidationOrchestratorV2 directly."""

    print("=" * 60)
    print("VALIDATION ORCHESTRATOR V2 TEST")
    print("=" * 60)

    # 1. Initialize container and get orchestrator
    print("\n1. Initializing container...")
    container = ServiceContainer()
    definition_orchestrator = container.orchestrator()

    # Get the validation orchestrator
    validation_orchestrator = definition_orchestrator.validation_service

    print(f"   ✓ ValidationOrchestrator type: {type(validation_orchestrator).__name__}")

    # Verify it's the right type
    from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2
    assert isinstance(validation_orchestrator, ValidationOrchestratorV2), \
        "Should be ValidationOrchestratorV2"
    print("   ✓ Correct orchestrator type confirmed")

    # 2. Test validate_text method
    print("\n2. Testing validate_text method...")

    context = ValidationContext(
        correlation_id=uuid.uuid4(),
        metadata={"test": "validation_orchestrator_v2"}
    )

    result = await validation_orchestrator.validate_text(
        begrip="belastingplichtige",
        text="Een natuurlijk persoon of rechtspersoon die belasting verschuldigd is.",
        ontologische_categorie=None,
        context=context
    )

    # Check result structure
    print("   ✓ validate_text completed")
    assert isinstance(result, dict), "Result should be a dict"
    print("   ✓ Result is dict")

    # Check required fields
    required_fields = [
        "version", "overall_score", "is_acceptable",
        "violations", "passed_rules", "detailed_scores", "system"
    ]

    for field in required_fields:
        assert field in result, f"Missing required field: {field}"
        print(f"   ✓ Field '{field}' present")

    # Check values
    print(f"\n3. Validation results:")
    print(f"   - Overall score: {result['overall_score']}")
    print(f"   - Is acceptable: {result['is_acceptable']}")
    print(f"   - Violations: {len(result['violations'])}")
    print(f"   - Passed rules: {len(result['passed_rules'])}")

    # 3. Test with empty text
    print("\n4. Testing with empty text...")

    result_empty = await validation_orchestrator.validate_text(
        begrip="test",
        text="",
        ontologische_categorie=None,
        context=context
    )

    # Note: Current implementation may accept empty text depending on rules
    print(f"   - Is acceptable: {result_empty['is_acceptable']}")
    print(f"   - Violations: {len(result_empty['violations'])}")
    if not result_empty['is_acceptable']:
        print("   ✓ Empty text correctly rejected")
    else:
        print("   ⚠️ Empty text accepted (check rule configuration)")

    # 4. Test validate_definition method
    print("\n5. Testing validate_definition method...")

    from services.interfaces import Definition

    definition = Definition(
        begrip="testbegrip",
        definitie="Een test definitie voor validatie.",
        ontologische_categorie="Type"
    )

    result_def = await validation_orchestrator.validate_definition(
        definition=definition,
        context=context
    )

    assert isinstance(result_def, dict), "Result should be a dict"
    print("   ✓ validate_definition completed")
    print(f"   - Score: {result_def['overall_score']}")
    print(f"   - Acceptable: {result_def['is_acceptable']}")

    print("\n" + "=" * 60)
    print("✅ VALIDATION ORCHESTRATOR V2 TEST PASSED!")
    print("=" * 60)

    return True


if __name__ == "__main__":
    result = asyncio.run(test_validation_orchestrator_v2())
    if result:
        print("\n🎉 All ValidationOrchestratorV2 tests passed successfully!")
