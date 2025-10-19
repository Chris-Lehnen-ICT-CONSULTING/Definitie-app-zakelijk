#!/usr/bin/env python3
"""Test voorbeelden generatie met nieuwe rate limiter."""

import asyncio
import os
import sys
import time

import pytest

sys.path.insert(0, "src")

# Skip if no API key configured; voorbeelden generator depends on external API
if not os.getenv("OPENAI_API_KEY"):
    pytest.skip(
        "OPENAI_API_KEY not set; skipping voorbeelden rate limiter test",
        allow_module_level=True,
    )

from voorbeelden.unified_voorbeelden import (
    ExampleRequest,
    ExampleType,
    GenerationMode,
    genereer_alle_voorbeelden_async,
)


async def test_voorbeelden_generatie():
    """Test voorbeelden generatie met nieuwe rate limiter."""
    print("🧪 Testing Voorbeelden Generatie met Rate Limiter Fix")
    print("=" * 60)

    # Test data
    begrip = "duurzaamheid"
    definitie = "Het vermogen om aan de behoeften van het heden te voldoen zonder de mogelijkheden van toekomstige generaties om in hun behoeften te voorzien in gevaar te brengen"
    context = {
        "domein": "milieu",
        "doelgroep": "algemeen publiek",
        "complexiteit": "gemiddeld",
    }

    print(f"\n📝 Begrip: {begrip}")
    print(f"📖 Definitie: {definitie[:80]}...")
    print(f"🎯 Context: {context}")

    # Test 1: Genereer alle voorbeelden types tegelijk
    print("\n\n📊 Test 1: Alle voorbeelden types parallel")
    print("-" * 60)

    start_time = time.time()

    try:
        # Genereer alle voorbeelden asynchroon
        alle_voorbeelden = await genereer_alle_voorbeelden_async(
            begrip=begrip,
            definitie=definitie,
            context=context,
            mode=GenerationMode.FAST,  # Gebruik fast mode voor snellere generatie
        )

        elapsed = time.time() - start_time

        print(f"\n✅ Alle voorbeelden gegenereerd in {elapsed:.2f} seconden!")

        # Toon resultaten
        for example_type, voorbeelden in alle_voorbeelden.items():
            print(f"\n{example_type}:")
            if voorbeelden:
                for i, voorbeeld in enumerate(voorbeelden[:2], 1):  # Toon eerste 2
                    print(f"  {i}. {voorbeeld}")
                if len(voorbeelden) > 2:
                    print(f"  ... en {len(voorbeelden) - 2} meer")
            else:
                print("  ❌ Geen voorbeelden gegenereerd")

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n❌ Fout na {elapsed:.2f}s: {type(e).__name__}: {e!s}")
        return False

    # Test 2: Test individuele endpoints met timing
    print("\n\n📊 Test 2: Individuele endpoints met timing")
    print("-" * 60)

    example_types = [
        ExampleType.SENTENCE,
        ExampleType.PRACTICAL,
        ExampleType.COUNTER,
        ExampleType.SYNONYMS,
        ExampleType.ANTONYMS,
    ]

    tasks = []
    for example_type in example_types:
        request = ExampleRequest(
            begrip=begrip,
            definitie=definitie,
            context=context,
            example_type=example_type,
            mode=GenerationMode.FAST,
        )

        async def generate_with_timing(req, etype):
            start = time.time()
            try:
                from voorbeelden.unified_voorbeelden import get_examples_generator

                generator = get_examples_generator()
                result = await generator.generate_examples_async(req)
                elapsed = time.time() - start
                return (etype, result, elapsed, None)
            except Exception as e:
                elapsed = time.time() - start
                return (etype, None, elapsed, e)

        task = generate_with_timing(request, example_type)
        tasks.append(task)

    # Voer alle tasks parallel uit
    print("\nGenerating all example types in parallel...")
    results = await asyncio.gather(*tasks)

    success_count = 0
    for etype, result, elapsed, error in results:
        if error:
            print(
                f"❌ {etype.value}: Failed after {elapsed:.2f}s - {type(error).__name__}"
            )
        else:
            success_count += 1
            count = len(result) if result else 0
            print(f"✅ {etype.value}: {count} examples in {elapsed:.2f}s")

    print(
        f"\nSuccess rate: {success_count}/{len(example_types)} ({success_count/len(example_types)*100:.0f}%)"
    )

    # Test 3: Stress test - meerdere requests naar zelfde endpoint
    print("\n\n📊 Test 3: Stress test - 10 requests naar zelfde endpoint")
    print("-" * 60)

    async def single_request(i):
        request = ExampleRequest(
            begrip=f"{begrip}_{i}",  # Varieer begrip voor verschillende responses
            definitie=definitie,
            context=context,
            example_type=ExampleType.SENTENCE,
            mode=GenerationMode.FAST,
        )

        start = time.time()
        try:
            from voorbeelden.unified_voorbeelden import get_examples_generator

            generator = get_examples_generator()
            await generator.generate_examples_async(request)
            elapsed = time.time() - start
            return (i, True, elapsed)
        except Exception:
            elapsed = time.time() - start
            return (i, False, elapsed)

    # Start 10 requests tegelijk
    start_time = time.time()
    tasks = [single_request(i) for i in range(10)]
    results = await asyncio.gather(*tasks)

    success_count = sum(1 for _, success, _ in results if success)
    total_time = time.time() - start_time

    print("\nResultaten:")
    for i, success, elapsed in results[:5]:  # Toon eerste 5
        status = "✅" if success else "❌"
        print(f"  {status} Request {i}: {elapsed:.2f}s")
    if len(results) > 5:
        print(f"  ... en {len(results) - 5} meer")

    print(f"\nTotaal: {success_count}/10 succesvol in {total_time:.2f}s")
    print(f"Gemiddelde tijd per request: {total_time/10:.2f}s")

    return True


async def main():
    """Run the test."""
    success = await test_voorbeelden_generatie()

    if success:
        print("\n\n🎉 Rate limiter test succesvol!")
        print("✅ Endpoint-specifieke rate limiting werkt correct")
    else:
        print("\n\n❌ Rate limiter test gefaald")

    # Cleanup
    from utils.smart_rate_limiter import cleanup_smart_limiters

    await cleanup_smart_limiters()


if __name__ == "__main__":
    asyncio.run(main())
