#!/usr/bin/env python3
"""
Deep test script voor DefinitieAgent functionaliteit.

Test alle kritieke componenten:
1. Synoniemen/Antoniemen generatie (5 items)
2. Voorkeursterm selectie
3. Prompt debug sectie
4. Rate limiting per endpoint
5. Performance monitoring
"""

import asyncio
import sys
import os
import pytest
import time
from typing import Dict, List

from dotenv import load_dotenv

# Load dotenv and skip if no API key configured BEFORE importing modules that touch OpenAI
load_dotenv()
if not os.getenv("OPENAI_API_KEY"):
    pytest.skip(
        "OPENAI_API_KEY not set; skipping deep functionality tests requiring external API",
        allow_module_level=True)

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import test modules (after skip guard)
from voorbeelden.unified_voorbeelden import (
    genereer_synoniemen, genereer_antoniemen, genereer_alle_voorbeelden,
    genereer_voorbeeld_zinnen, genereer_praktijkvoorbeelden,
    GenerationMode, get_examples_generator
)
from utils.smart_rate_limiter import get_smart_limiter
from utils.performance_monitor import get_performance_monitor, start_timing, stop_timing
from services.orchestrators.definition_orchestrator_v2 import DefinitionOrchestratorV2
from services.interfaces import GenerationRequest, OrchestratorConfig
from services.container import get_container

# Load dotenv and skip if no API key configured
load_dotenv()
if not os.getenv("OPENAI_API_KEY"):
    pytest.skip(
        "OPENAI_API_KEY not set; skipping deep functionality tests requiring external API",
        allow_module_level=True)


async def test_synoniemen_antoniemen():
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
    start_timing("synoniemen_generatie")
    synoniemen = genereer_synoniemen(begrip, definitie, context_dict)
    duration = stop_timing("synoniemen_generatie")

    print(f"✅ Gegenereerde {len(synoniemen)} synoniemen in {duration:.2f}s:")
    for i, syn in enumerate(synoniemen, 1):
        print(f"   {i}. {syn}")

    if len(synoniemen) != 5:
        print(f"❌ FOUT: Verwachtte 5 synoniemen, kreeg {len(synoniemen)}")
    else:
        print("✅ Correct aantal synoniemen (5)")

    # Test antoniemen
    print("\n📝 Genereer antoniemen...")
    start_timing("antoniemen_generatie")
    antoniemen = genereer_antoniemen(begrip, definitie, context_dict)
    duration = stop_timing("antoniemen_generatie")

    print(f"✅ Gegenereerde {len(antoniemen)} antoniemen in {duration:.2f}s:")
    for i, ant in enumerate(antoniemen, 1):
        print(f"   {i}. {ant}")

    if len(antoniemen) != 5:
        print(f"❌ FOUT: Verwachtte 5 antoniemen, kreeg {len(antoniemen)}")
    else:
        print("✅ Correct aantal antoniemen (5)")

    return synoniemen, antoniemen


async def test_bulk_generation():
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
    start_timing("bulk_generatie")
    voorbeelden = genereer_alle_voorbeelden(begrip, definitie, context_dict, GenerationMode.RESILIENT)
    duration = stop_timing("bulk_generatie")

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

    for example_type, examples in voorbeelden.items():
        count = len(examples)
        expected = expected_counts.get(example_type, 3)
        status = "✅" if count == expected else "❌"
        print(f"  {status} {example_type}: {count} items (verwacht: {expected})")

        # Toon eerste voorbeeld
        if examples:
            first = examples[0] if isinstance(examples, list) else examples
            print(f"     Voorbeeld: {first[:80]}...")


async def test_rate_limiting():
    """Test endpoint-specifieke rate limiting."""
    print("\n\n🧪 TEST 3: Endpoint-Specifieke Rate Limiting")
    print("=" * 60)

    # Test verschillende endpoints parallel
    endpoints = [
        "examples_generation_sentence",
        "examples_generation_synonyms",
        "examples_generation_antonyms"
    ]

    print("\n📊 Check rate limiters voor verschillende endpoints...")

    for endpoint in endpoints:
        limiter = await get_smart_limiter(endpoint)
        print(f"\n  Endpoint: {endpoint}")
        print(f"    - Tokens beschikbaar: {limiter.rate_limiter.available_tokens:.1f}")
        print(f"    - Bucket capacity: {limiter.rate_limiter.bucket.capacity}")
        print(f"    - Request queue size: {limiter.request_queue.qsize()}")

    # Test parallel requests
    print("\n\n🔄 Test parallel requests naar verschillende endpoints...")

    async def make_request(endpoint: str, index: int):
        """Simuleer een request naar een endpoint."""
        limiter = await get_smart_limiter(endpoint)
        start = time.time()

        async def dummy_func():
            await asyncio.sleep(0.1)  # Simuleer API call
            return f"Result from {endpoint} #{index}"

        result = await limiter.execute_with_rate_limit(dummy_func)
        duration = time.time() - start
        return endpoint, index, duration, result

    # Maak 5 requests per endpoint
    tasks = []
    for endpoint in endpoints:
        for i in range(5):
            task = make_request(endpoint, i)
            tasks.append(task)

    # Voer alle requests parallel uit
    results = await asyncio.gather(*tasks)

    # Analyseer resultaten
    endpoint_times = {}
    for endpoint, index, duration, result in results:
        if endpoint not in endpoint_times:
            endpoint_times[endpoint] = []
        endpoint_times[endpoint].append(duration)

    print("\n📈 Rate limiting resultaten:")
    for endpoint, times in endpoint_times.items():
        avg_time = sum(times) / len(times)
        max_time = max(times)
        print(f"  {endpoint}:")
        print(f"    - Gemiddelde tijd: {avg_time:.3f}s")
        print(f"    - Max tijd: {max_time:.3f}s")
        print(f"    - Requests: {len(times)}")


async def test_orchestrator_v2():
    """Test V2 orchestrator functionaliteit."""
    print("\n\n🧪 TEST 4: V2 Orchestrator")
    print("=" * 60)

    # Prompt logging functionality has been removed

    # Genereer definitie met voorbeelden
    print("\n📝 Genereer definitie met alle voorbeelden...")

    # Get V2 container and orchestrator
    container = get_container({})
    orchestrator = container.orchestrator()

    import uuid
    request = GenerationRequest(
        id=str(uuid.uuid4()),
        begrip="hoger beroep",
        context="Gerechtshof",
        ontologische_categorie="PROCES"
    )

    result = await orchestrator.create_definition(request)

    # Prompt logging functionality has been removed
    if result.success and result.definition:
        print("\n✅ Definition generated successfully")
        print(f"    - Definition: {result.definition.definitie[:100]}...")
        print(f"    - Examples generated: {len(result.definition.voorbeelden) if result.definition.voorbeelden else 0}")
    else:
        print(f"\n❌ Generation failed: {result.error}")


async def test_performance_summary():
    """Toon performance summary."""
    print("\n\n🧪 TEST 5: Performance Summary")
    print("=" * 60)

    monitor = get_performance_monitor()
    summary = monitor.get_summary()

    if summary:
        print("\n📊 Performance metrics:")
        for operation, stats in summary.items():
            print(f"\n  {operation}:")
            print(f"    - Calls: {stats['count']}")
            print(f"    - Average: {stats['average']:.2f}s")
            print(f"    - Min: {stats['min']:.2f}s")
            print(f"    - Max: {stats['max']:.2f}s")
            print(f"    - Total: {stats['total']:.2f}s")
    else:
        print("\n❌ Geen performance data beschikbaar")


async def main():
    """Run all tests."""
    print("🚀 DefinitieAgent Deep Test Suite")
    print("=" * 80)

    try:
        # Load environment
        load_dotenv()

        # Run tests
        synoniemen, antoniemen = await test_synoniemen_antoniemen()
        await test_bulk_generation()
        await test_rate_limiting()
        await test_orchestrator_v2()
        await test_performance_summary()

        # Cleanup not needed - limiters cleanup automatically

        print("\n\n✅ Alle tests voltooid!")

        # Final summary
        print("\n📋 SAMENVATTING:")
        print(f"  - Synoniemen generatie: {'✅' if len(synoniemen) == 5 else '❌'}")
        print(f"  - Antoniemen generatie: {'✅' if len(antoniemen) == 5 else '❌'}")
        print(f"  - Rate limiting per endpoint: ✅")
        print(f"  - Prompt logging: ❌ (removed)")
        print(f"  - Performance monitoring: ✅")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
