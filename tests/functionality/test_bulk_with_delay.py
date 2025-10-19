#!/usr/bin/env python3
"""
Test bulk generatie met delay tussen synoniemen/antoniemen.
"""

import asyncio
import os
import sys
import time

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from dotenv import load_dotenv

load_dotenv()

# Skip this functionality test when no API key is configured
if not os.getenv("OPENAI_API_KEY"):
    pytest.skip(
        "OPENAI_API_KEY not set; skipping bulk-with-delay functionality test",
        allow_module_level=True,
    )

from voorbeelden.unified_voorbeelden import (
    ExampleRequest,
    ExampleType,
    GenerationMode,
    get_examples_generator,
)


async def test_bulk_generation_with_delay():
    """Test bulk generatie met delay voor rate limiting."""
    print("🧪 Bulk Generatie Test met Delay")
    print("=" * 60)

    # Test data
    begrip = "hoger beroep"
    definitie = "Het rechtsmiddel waarbij een partij die het niet eens is met een uitspraak van de rechter in eerste aanleg, de zaak aan een hogere rechter kan voorleggen."
    context_dict = {
        "organisatorisch": ["Gerechtshof"],
        "juridisch": ["Strafprocesrecht"],
        "wettelijk": ["Wetboek van Strafvordering"],
    }

    generator = get_examples_generator()
    results = {}

    # Define order and delays
    example_configs = [
        (ExampleType.VOORBEELDZINNEN, 3, 0),  # No delay
        (ExampleType.PRAKTIJKVOORBEELDEN, 3, 0),  # No delay
        (ExampleType.TEGENVOORBEELDEN, 3, 0),  # No delay
        (ExampleType.TOELICHTING, 1, 2),  # 2s delay before
        (ExampleType.SYNONIEMEN, 5, 3),  # 3s delay before
        (ExampleType.ANTONIEMEN, 5, 3),  # 3s delay before
    ]

    print("\n📦 Start generatie met delays...")
    total_start = time.time()

    for example_type, max_examples, delay in example_configs:
        if delay > 0:
            print(f"\n⏳ Wacht {delay}s voor {example_type.value}...")
            await asyncio.sleep(delay)

        print(f"\n📝 Genereer {example_type.value} ({max_examples} items)...")
        start = time.time()

        request = ExampleRequest(
            begrip=begrip,
            definitie=definitie,
            context_dict=context_dict,
            example_type=example_type,
            generation_mode=GenerationMode.RESILIENT,
            max_examples=max_examples,
        )

        response = generator.generate_examples(request)
        duration = time.time() - start

        if response.success:
            results[example_type.value] = response.examples
            count = len(response.examples)
            print(f"✅ {example_type.value}: {count} items in {duration:.2f}s")
            if response.examples:
                print(f"   Voorbeeld: {response.examples[0][:60]}...")
        else:
            results[example_type.value] = []
            print(f"❌ {example_type.value}: FAILED - {response.error_message}")

    total_duration = time.time() - total_start
    print(f"\n✅ Totale tijd: {total_duration:.2f}s")

    # Check results
    expected_counts = {
        "sentence": 3,
        "practical": 3,
        "counter": 3,
        "synonyms": 5,
        "antonyms": 5,
        "explanation": 1,
    }

    print("\n📊 RESULTATEN:")
    all_correct = True
    for example_type, expected in expected_counts.items():
        actual = len(results.get(example_type, []))
        correct = actual == expected
        status = "✅" if correct else "❌"
        print(f"  {status} {example_type}: {actual}/{expected}")
        if not correct:
            all_correct = False

    return all_correct


async def main():
    """Run test."""
    print("🚀 Bulk Generation Test with Rate Limit Management")
    print("=" * 80)

    try:
        success = await test_bulk_generation_with_delay()

        if success:
            print("\n🎉 ALLE TESTS GESLAAGD!")
        else:
            print("\n⚠️ SOMMIGE TESTS GEFAALD!")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
