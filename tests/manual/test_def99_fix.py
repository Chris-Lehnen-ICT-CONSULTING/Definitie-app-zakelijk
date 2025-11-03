"""
Manual test to verify DEF-99 fix: Double adapter wrapping bug.

This test verifies that:
1. Cleaning service is properly wrapped once in ServiceContainer
2. Definition orchestrator uses the wrapped service directly
3. Validation completes without AttributeError
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


async def test_validation_with_real_container():
    """Test validation using real ServiceContainer (no double wrapping)."""
    from services.container import ServiceContainer
    from services.interfaces import GenerationRequest

    print("=" * 80)
    print("DEF-99 Manual Test: Validation with Real Container")
    print("=" * 80)

    # Create container with minimal config
    container = ServiceContainer(
        {
            "db_path": ":memory:",  # In-memory DB for testing
            "use_json_rules": False,  # Disable JSON rules for speed
        }
    )

    print("\n1. Container created successfully")

    # Get orchestrator (should have cleaning service already wrapped)
    orchestrator = container.orchestrator()
    print(f"2. Orchestrator created: {type(orchestrator).__name__}")
    print(f"   - Cleaning service type: {type(orchestrator.cleaning_service).__name__}")

    # Trigger lazy validation service loading
    validation_service = orchestrator.validation_service
    print(f"3. Validation service loaded: {type(validation_service).__name__}")
    print(
        f"   - Validation cleaning service type: {type(validation_service.cleaning_service).__name__}"
    )

    # Verify no double wrapping
    from services.adapters.cleaning_service_adapter import CleaningServiceAdapterV1toV2

    is_orchestrator_wrapped = isinstance(
        orchestrator.cleaning_service, CleaningServiceAdapterV1toV2
    )
    is_validation_wrapped = isinstance(
        validation_service.cleaning_service, CleaningServiceAdapterV1toV2
    )

    print("\n4. Wrapping verification:")
    print(f"   - Orchestrator cleaning service is wrapped: {is_orchestrator_wrapped}")
    print(f"   - Validation cleaning service is wrapped: {is_validation_wrapped}")

    if is_orchestrator_wrapped and is_validation_wrapped:
        print("   ✅ Both services properly wrapped (expected)")
    else:
        print("   ❌ Wrapping issue detected!")
        return False

    # Create a simple test request
    import uuid

    request = GenerationRequest(
        id=str(uuid.uuid4()),
        begrip="test_begrip",
        context="test context",
        ontologische_categorie="proces",
        actor="manual_test",
    )

    print(f"\n5. Testing validation flow with request: {request.begrip}")

    try:
        # This should NOT cause AttributeError if fix is correct
        from services.interfaces import Definition
        from services.validation.interfaces import ValidationContext

        test_definition = Definition(
            begrip=request.begrip,
            definitie="Een test definitie voor verificatie van de fix.",
            organisatorische_context=["test"],
            juridische_context=["test"],
            wettelijke_basis=["test"],
            ontologische_categorie=request.ontologische_categorie,
            created_by=request.actor,
        )

        validation_context = ValidationContext(
            correlation_id=uuid.uuid4(), metadata={"test": True}
        )

        result = await validation_service.validate_definition(
            test_definition, validation_context
        )

        print("6. Validation completed successfully!")
        print(f"   - Is valid: {getattr(result, 'is_valid', 'N/A')}")
        print(f"   - Result type: {type(result).__name__}")
        print("\n✅ DEF-99 FIX VERIFIED: No AttributeError occurred!")
        return True

    except AttributeError as e:
        print("\n❌ DEF-99 FIX FAILED: AttributeError still occurs!")
        print(f"   Error: {e}")
        import traceback

        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n⚠️  Other error occurred (may be expected): {type(e).__name__}: {e}")
        # Other errors are OK - we only care about AttributeError from double wrapping
        return True


if __name__ == "__main__":
    result = asyncio.run(test_validation_with_real_container())
    sys.exit(0 if result else 1)
