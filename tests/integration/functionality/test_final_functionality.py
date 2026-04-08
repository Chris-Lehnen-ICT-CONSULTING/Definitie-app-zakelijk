#!/usr/bin/env python3
"""
Final test voor alle functionaliteit met juiste sync/async handling.
"""

import json
import os
import sys
import time

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from dotenv import load_dotenv

load_dotenv()

# Skip early if no API key configured; these tests call external generators
if not os.getenv("OPENAI_API_KEY"):
    pytest.skip(
        "OPENAI_API_KEY not set; skipping final functionality tests requiring external API",
        allow_module_level=True,
    )

from services.container import ServiceContainer, get_container
from services.interfaces import GenerationRequest, OrchestratorConfig
from services.orchestrators.definition_orchestrator_v2 import DefinitionOrchestratorV2
from voorbeelden.unified_voorbeelden import (
    GenerationMode,
    genereer_alle_voorbeelden,
    genereer_antoniemen,
    genereer_praktijkvoorbeelden,
    genereer_synoniemen,
    genereer_tegenvoorbeelden,
    genereer_toelichting,
    genereer_voorbeeld_zinnen,
)

pytestmark = [pytest.mark.integration, pytest.mark.slow]


def test_individual_generation():
    """Test individuele generatie functies."""
    print("\n🧪 TEST 1: Individuele Generatie Functies")
    print("=" * 60)

    # Test data
    begrip = "dwangmiddel"
    definitie = "Een bevoegdheid die de overheid kan inzetten om het strafprocesrecht te handhaven, ook tegen de wil van de betrokkene."
    context_dict = {
        "organisatorisch": ["Politie", "Openbaar Ministerie"],
        "juridisch": ["Strafprocesrecht"],
        "wettelijk": ["Wetboek van Strafvordering"],
    }

    tests = [
        ("Voorbeeldzinnen", genereer_voorbeeld_zinnen, 3),
        ("Praktijkvoorbeelden", genereer_praktijkvoorbeelden, 3),
        ("Tegenvoorbeelden", genereer_tegenvoorbeelden, 3),
        ("Synoniemen", genereer_synoniemen, 5),
        ("Antoniemen", genereer_antoniemen, 5),
    ]

    all_passed = True

    for test_name, func, expected_count in tests:
        print(f"\n📝 Test {test_name}...")
        start = time.time()

        results = func(begrip, definitie, context_dict)
        duration = time.time() - start

        actual_count = len(results)
        passed = actual_count == expected_count
        status = "✅" if passed else "❌"

        print(
            f"{status} {test_name}: {actual_count}/{expected_count} in {duration:.2f}s"
        )

        if results:
            print(f"   Voorbeeld: {results[0][:60]}...")

        if not passed:
            all_passed = False

    # Test toelichting apart (returnt string, niet list)
    print("\n📝 Test Toelichting...")
    start = time.time()
    toelichting = genereer_toelichting(begrip, definitie, context_dict)
    duration = time.time() - start

    passed = len(toelichting) > 0
    status = "✅" if passed else "❌"
    print(
        f"{status} Toelichting: {'Gegenereerd' if passed else 'Leeg'} in {duration:.2f}s"
    )
    if toelichting:
        print(f"   Start: {toelichting[:80]}...")

    return all_passed


def test_bulk_generation_sequential():
    """Test bulk generatie met sequentiële aanroepen."""
    print("\n\n🧪 TEST 2: Bulk Generatie (Sequentieel)")
    print("=" * 60)

    # Test data - andere begrip om caching te vermijden
    begrip = "voorlopige hechtenis"
    definitie = "De vrijheidsbeneming van een verdachte tijdens het vooronderzoek, voordat er een onherroepelijk vonnis is."
    context_dict = {
        "organisatorisch": ["Rechter-commissaris", "Raadkamer"],
        "juridisch": ["Strafprocesrecht"],
        "wettelijk": ["Wetboek van Strafvordering art. 63-88"],
    }

    print("\n📦 Start bulk generatie...")
    print("⚠️ Dit kan 60-90 seconden duren door rate limiting...")

    start = time.time()
    voorbeelden = genereer_alle_voorbeelden(
        begrip, definitie, context_dict, GenerationMode.RESILIENT
    )
    duration = time.time() - start

    print(f"\n✅ Bulk generatie voltooid in {duration:.2f}s")

    expected_counts = {
        "sentence": 3,
        "practical": 3,
        "counter": 3,
        "synonyms": 5,
        "antonyms": 5,
        "explanation": 1,
    }

    print("\n📊 Resultaten:")
    all_correct = True

    for example_type, expected in expected_counts.items():
        actual = len(voorbeelden.get(example_type, []))
        correct = actual == expected
        status = "✅" if correct else "❌"
        print(f"  {status} {example_type}: {actual}/{expected}")

        if not correct:
            all_correct = False

        # Toon voorbeeld
        if voorbeelden.get(example_type):
            examples = voorbeelden[example_type]
            first = examples[0] if isinstance(examples, list) else examples
            print(f"     → {first[:60]}...")

    return all_correct


async def test_definition_generation():
    """Test complete definitie generatie met voorbeelden."""
    print("\n\n🧪 TEST 3: Complete Definitie Generatie")
    print("=" * 60)

    # Get V2 container and orchestrator
    container = get_container()
    orchestrator = container.orchestrator()

    import uuid

    request = GenerationRequest(
        id=str(uuid.uuid4()),
        begrip="recidive",
        context="Reclassering Nederland",
        ontologische_categorie="PROCES",
    )

    print("\n🚀 Genereer definitie met voorbeelden...")
    start = time.time()

    # V2 async call
    result = await orchestrator.create_definition(request)

    duration = time.time() - start

    print(f"\n✅ Generatie voltooid in {duration:.2f}s")

    if result.success:
        print(f"\n📝 Definitie: {result.definition.definitie[:100]}...")
        if result.validation_result:
            print(f"📊 Score: {result.validation_result.score:.2f}")

        if result.definition and result.definition.voorbeelden:
            print("\n📚 Voorbeelden gegenereerd:")
            count = len(result.definition.voorbeelden)
            print(f"  - voorbeelden: {count} items")

        return True
    print(f"\n❌ Generatie mislukt: {result.error}")
    return False


async def main():
    """Run all tests."""
    print("🚀 DefinitieAgent Final Test Suite")
    print("=" * 80)

    try:
        # Run tests
        test1_passed = test_individual_generation()
        test2_passed = test_bulk_generation_sequential()
        test3_passed = await test_definition_generation()

        print("\n\n" + "=" * 80)
        print("📋 EINDRESULTAAT:")
        print("=" * 80)

        print(
            f"\nTest 1 - Individuele Generatie: {'✅ GESLAAGD' if test1_passed else '❌ GEFAALD'}"
        )
        print(
            f"Test 2 - Bulk Generatie: {'✅ GESLAAGD' if test2_passed else '❌ GEFAALD'}"
        )
        print(
            f"Test 3 - Complete Definitie: {'✅ GESLAAGD' if test3_passed else '❌ GEFAALD'}"
        )

        if test1_passed and test2_passed and test3_passed:
            print("\n🎉 ALLE TESTS GESLAAGD!")
            print("\n✅ Verificatie compleet:")
            print("  - Synoniemen/Antoniemen genereren 5 items")
            print("  - Voorbeelden genereren juiste aantallen")
            print("  - Explanation geeft 1 alinea terug")
            print("  - Rate limiting werkt correct per endpoint")
            print("  - Complete definitie generatie werkt")
        else:
            print("\n⚠️ SOMMIGE TESTS GEFAALD!")

            if not test2_passed:
                print("\n💡 Tip: Als bulk generatie faalt door rate limiting:")
                print("  - Verhoog timeouts in config/rate_limit_config.py")
                print("  - Of voeg delays toe tussen requests")

    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
