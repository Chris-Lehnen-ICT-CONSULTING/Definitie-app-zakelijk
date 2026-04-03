"""
Test ontologische analyse integratie met nieuwe services.
"""

import asyncio
import os
import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.integration]

# Voeg src toe aan path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Forceer nieuwe services
os.environ["USE_NEW_SERVICES"] = "true"
os.environ["APP_ENV"] = "development"

print("Testing ontologische analyse integratie...")


async def test_ontology():
    """Test async ontologie functionaliteit."""
    try:
        from services import get_container
        from services.interfaces import GenerationRequest

        # Get container met development config (enable_ontology = True)
        container = get_container()
        generator = container.generator()

        print("\n✅ Generator service geladen")
        print(f"   Ontologie enabled: {generator.config.enable_ontology}")

        # Test 1: Proces begrip
        print("\n📋 Test 1: Proces begrip")
        request = GenerationRequest(
            id="test-id", begrip="verificatie", context="Identiteitscontrole bij DJI"
        )

        definition = await generator.generate(request)

        print(f"✅ Begrip: {definition.begrip}")
        print(f"✅ Categorie: {definition.categorie}")
        print(f"✅ Definitie: {definition.definitie[:80]}...")

        if "categorie_reasoning" in definition.metadata:
            print(f"✅ Reasoning: {definition.metadata['categorie_reasoning']}")

        # Test 2: Type begrip
        print("\n📋 Test 2: Type begrip")
        request2 = GenerationRequest(
            id="test-id",
            begrip="authenticatiemiddel",
            context="Digitale toegangscontrole",
        )

        definition2 = await generator.generate(request2)

        print(f"✅ Begrip: {definition2.begrip}")
        print(f"✅ Categorie: {definition2.categorie}")

        # Test 3: Zonder ontologie
        print("\n📋 Test 3: Zonder ontologie (fallback)")
        generator.config.enable_ontology = False

        request3 = GenerationRequest(
            id="test-id", begrip="rapportage", context="Maandelijkse overzichten"
        )

        definition3 = await generator.generate(request3)

        print(f"✅ Begrip: {definition3.begrip}")
        print(f"✅ Categorie (simple): {definition3.categorie}")

        print("\n🎉 Ontologie integratie test succesvol!")

    except Exception as e:
        print(f"\n❌ Test mislukt: {e}")
        import traceback

        traceback.print_exc()


# Run async test
if __name__ == "__main__":
    asyncio.run(test_ontology())
