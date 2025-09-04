#!/usr/bin/env python3
"""
Simplified deep test voor kritieke functionaliteit.
"""

import asyncio
import sys
import os
import pytest
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
load_dotenv()

# Skip early if no API key configured; these tests call external generators
if not os.getenv("OPENAI_API_KEY"):
    pytest.skip(
        "OPENAI_API_KEY not set; skipping simple functionality tests requiring external API",
        allow_module_level=True,
    )

# Import test modules
from voorbeelden.unified_voorbeelden import (
    genereer_synoniemen, genereer_antoniemen, genereer_alle_voorbeelden,
    GenerationMode
)


def test_synoniemen_antoniemen():
    """Test synoniemen en antoniemen generatie (moet 5 items returnen)."""
    print("\n🧪 TEST 1: Synoniemen/Antoniemen Generatie")
    print("=" * 60)

    # Test data
    begrip = "verdachte"
    definitie = "Een persoon die wordt verdacht van het plegen van een strafbaar feit."
    context_dict = {
        "organisatorisch": ["Openbaar Ministerie"],
        "juridisch": ["Strafrecht"],
        "wettelijk": ["Wetboek van Strafvordering"]
    }

    # Test synoniemen
    print("\n📝 Genereer synoniemen...")
    start = time.time()
    synoniemen = genereer_synoniemen(begrip, definitie, context_dict)
    duration = time.time() - start

    print(f"✅ Gegenereerde {len(synoniemen)} synoniemen in {duration:.2f}s:")
    for i, syn in enumerate(synoniemen, 1):
        print(f"   {i}. {syn}")

    if len(synoniemen) != 5:
        print(f"❌ FOUT: Verwachtte 5 synoniemen, kreeg {len(synoniemen)}")
    else:
        print("✅ Correct aantal synoniemen (5)")

    # Test antoniemen
    print("\n📝 Genereer antoniemen...")
    start = time.time()
    antoniemen = genereer_antoniemen(begrip, definitie, context_dict)
    duration = time.time() - start

    print(f"✅ Gegenereerde {len(antoniemen)} antoniemen in {duration:.2f}s:")
    for i, ant in enumerate(antoniemen, 1):
        print(f"   {i}. {ant}")

    if len(antoniemen) != 5:
        print(f"❌ FOUT: Verwachtte 5 antoniemen, kreeg {len(antoniemen)}")
    else:
        print("✅ Correct aantal antoniemen (5)")

    return len(synoniemen) == 5 and len(antoniemen) == 5


def test_bulk_generation():
    """Test bulk generatie met alle voorbeeld types."""
    print("\n\n🧪 TEST 2: Bulk Generatie (alle types)")
    print("=" * 60)

    # Test data
    begrip = "strafblad"
    definitie = "Een officieel document waarin de strafrechtelijke veroordelingen van een persoon worden geregistreerd."
    context_dict = {
        "organisatorisch": ["Justitiële Informatiedienst"],
        "juridisch": ["Strafrecht"],
        "wettelijk": ["Wet justitiële en strafvorderlijke gegevens"]
    }

    print("\n📦 Start bulk generatie...")
    start = time.time()
    voorbeelden = genereer_alle_voorbeelden(begrip, definitie, context_dict, GenerationMode.RESILIENT)
    duration = time.time() - start

    print(f"\n✅ Bulk generatie voltooid in {duration:.2f}s")
    print("\nResultaten:")

    expected_counts = {
        'sentence': 3,
        'practical': 3,
        'counter': 3,
        'synonyms': 5,
        'antonyms': 5,
        'explanation': 1
    }

    all_correct = True
    for example_type, examples in voorbeelden.items():
        count = len(examples)
        expected = expected_counts.get(example_type, 3)
        correct = count == expected
        status = "✅" if correct else "❌"
        print(f"  {status} {example_type}: {count} items (verwacht: {expected})")

        if not correct:
            all_correct = False

        # Toon eerste voorbeeld
        if examples:
            first = examples[0] if isinstance(examples, list) else examples
            print(f"     Voorbeeld: {first[:80]}...")

    return all_correct


def main():
    """Run all tests."""
    print("🚀 DefinitieAgent Simplified Test Suite")
    print("=" * 80)

    try:
        # Run tests
        test1_passed = test_synoniemen_antoniemen()
        test2_passed = test_bulk_generation()

        print("\n\n✅ Alle tests voltooid!")

        # Final summary
        print("\n📋 SAMENVATTING:")
        print(f"  - Synoniemen/Antoniemen (5 items): {'✅' if test1_passed else '❌'}")
        print(f"  - Bulk generatie met juiste aantallen: {'✅' if test2_passed else '❌'}")

        if test1_passed and test2_passed:
            print("\n🎉 ALLE TESTS GESLAAGD!")
        else:
            print("\n⚠️ SOMMIGE TESTS GEFAALD!")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
