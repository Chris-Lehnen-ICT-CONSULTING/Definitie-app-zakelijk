#!/usr/bin/env python3
import pytest

"""
Test script voor DefinitionOrchestratorV2 via service factory.

Dit script test de nieuwe V2 orchestrator door een eenvoudige definitie
te genereren en te controleren of ontological categories correct werken.
"""

# Legacy compatibility: markeer deze suite als informatief en uitgesloten in PR-profiel
pytestmark = pytest.mark.xfail(
    reason="Legacy fallback/CLI-style script (excluded in PR)", strict=False
)

import asyncio
import os
import sys
import time
from pathlib import Path

# Voeg src toe aan Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from services.interfaces import GenerationRequest
from services.service_factory import get_definition_service


async def test_v2_orchestrator():
    """Test de V2 orchestrator met ontological category functionaliteit."""
    print("🚀 Testing DefinitionOrchestratorV2...")

    # Enable V2 orchestrator via environment variable
    os.environ["USE_V2_ORCHESTRATOR"] = "true"

    try:
        # Get service directly via container to avoid asyncio issues
        import uuid

        from services.container import get_container
        from services.interfaces import GenerationRequest

        container = get_container()
        orchestrator = container.orchestrator()  # Should be V2 orchestrator

        print(f"📊 Orchestrator type: {type(orchestrator).__name__}")

        # Test 1: Basic generation
        print("\n🧪 Test 1: Basic definition generation")
        start_time = time.time()

        request = GenerationRequest(
            id=str(uuid.uuid4()),
            begrip="verificatie",
            context="DJI",
            ontologische_categorie="proces",
            actor="test_script",
            legal_basis="testing",
        )

        response = await orchestrator.create_definition(request)

        duration = time.time() - start_time
        print(f"⏱️  Generation took: {duration:.2f}s")
        print(f"✅ Success: {response.success}")

        if response.success:
            print(f"📝 Definition: {response.definition.definitie[:100]}...")
            if response.validation_result:
                print(f"📊 Score: {response.validation_result.score or 0.0}")

            # Check if ontological category was properly handled
            if response.metadata:
                print(
                    f"🏷️  Ontological category: {response.metadata.get('ontological_category', 'Not found')}"
                )
                print(
                    f"🔧 Orchestrator version: {response.metadata.get('orchestrator_version', 'unknown')}"
                )

        else:
            print(f"❌ Error: {response.error}")
            return False

        # Test 2: Different ontological category
        print("\n🧪 Test 2: Type category generation")
        start_time = time.time()

        request2 = GenerationRequest(
            id=str(uuid.uuid4()),
            begrip="identiteitsbewijs",
            context="DJI",
            ontologische_categorie="type",
            actor="test_script",
            legal_basis="testing",
        )

        response2 = await orchestrator.create_definition(request2)

        duration2 = time.time() - start_time
        print(f"⏱️  Generation took: {duration2:.2f}s")
        print(f"✅ Success: {response2.success}")

        if response2.success:
            print(f"📝 Definition: {response2.definition.definitie[:100]}...")
            if response2.validation_result:
                print(f"📊 Score: {response2.validation_result.score or 0.0}")

        # Test 3: Performance comparison
        print("\n📈 Performance Analysis:")
        print(f"Process generation: {duration:.2f}s")
        print(f"Type generation: {duration2:.2f}s")
        print(f"Average: {(duration + duration2) / 2:.2f}s")

        target_time = 5.0  # V2 target is <5s
        avg_time = (duration + duration2) / 2

        if avg_time < target_time:
            print(f"🎯 Performance target MET: {avg_time:.2f}s < {target_time}s")
        else:
            print(f"⚠️  Performance target MISSED: {avg_time:.2f}s > {target_time}s")

        return True

    except Exception as e:
        print(f"💥 Test failed with exception: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_v1_fallback():
    """Test dat V1 orchestrator nog steeds werkt (fallback)."""
    print("\n🔄 Testing V1 Orchestrator fallback...")

    # Disable V2 orchestrator
    os.environ["USE_V2_ORCHESTRATOR"] = "false"

    try:
        service = get_definition_service()
        service_info = service.get_service_info()
        print(f"📊 Service info: {service_info}")

        # Quick generation test
        result = service.generate_definition(
            begrip="test", context_dict={"juridisch": ["test"]}, categorie="type"
        )

        print(f"✅ V1 Fallback works: {result.success}")
        return result.success

    except Exception as e:
        print(f"💥 V1 Fallback test failed: {e}")
        return False


async def main():
    """Main test runner."""
    print("🎭 DefinitionOrchestratorV2 Integration Test")
    print("=" * 50)

    # Test V2 orchestrator
    success_v2 = await test_v2_orchestrator()

    # Test V1 fallback
    success_v1 = test_v1_fallback()

    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"✅ V2 Orchestrator: {'PASSED' if success_v2 else 'FAILED'}")
    print(f"✅ V1 Fallback: {'PASSED' if success_v1 else 'FAILED'}")

    if success_v2 and success_v1:
        print("\n🎉 ALL TESTS PASSED! V2 orchestrator ready for UI testing.")
        return 0
    print("\n❌ SOME TESTS FAILED! Check implementation.")
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
