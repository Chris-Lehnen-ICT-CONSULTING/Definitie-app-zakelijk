#!/usr/bin/env python3
"""Test of WebLookupService daadwerkelijk API calls maakt."""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


async def test_weblookup():
    """Test directe WebLookup calls."""
    print("\n" + "=" * 80)
    print("🧪 TEST: WebLookup Service - Maakt het ECHTE API calls?")
    print("=" * 80 + "\n")

    from services.interfaces import LookupRequest
    from services.modern_web_lookup_service import ModernWebLookupService

    service = ModernWebLookupService()

    # Test 1: Wikipedia lookup
    print("📚 TEST 1: Wikipedia lookup voor 'validatie'")
    print("-" * 80)

    request = LookupRequest(term="validatie", sources=["wikipedia"], max_results=3)

    import time

    start = time.time()
    results = await service.lookup(request)
    elapsed = time.time() - start

    print(f"⏱️  Tijd: {elapsed:.3f}s")
    print(f"📊 Resultaten: {len(results)}")

    if results:
        for i, r in enumerate(results, 1):
            print(f"\n   Resultaat {i}:")
            print(f"   - Source: {r.source.name}")
            print(f"   - URL: {r.source.url}")
            print(f"   - Confidence: {r.source.confidence:.3f}")
            print(
                f"   - Definition: {r.definition[:100] if r.definition else 'EMPTY'}..."
            )
            print(f"   - Success: {r.success}")
    else:
        print("   ❌ GEEN RESULTATEN")

        # Check debug info
        debug = service._last_debug
        if debug:
            print("\n🔍 DEBUG INFO:")
            print(f"   - Selected sources: {debug.get('selected_sources', [])}")
            print(f"   - Attempts: {len(debug.get('attempts', []))}")
            for att in debug.get("attempts", []):
                print(
                    f"      • {att.get('provider')}: success={att.get('success')}, stage={att.get('stage', 'N/A')}"
                )

    # Test 2: Wiktionary lookup
    print("\n" + "=" * 80)
    print("📖 TEST 2: Wiktionary lookup voor 'sanctie'")
    print("-" * 80)

    request2 = LookupRequest(term="sanctie", sources=["wiktionary"], max_results=3)

    start = time.time()
    results2 = await service.lookup(request2)
    elapsed = time.time() - start

    print(f"⏱️  Tijd: {elapsed:.3f}s")
    print(f"📊 Resultaten: {len(results2)}")

    if results2:
        for i, r in enumerate(results2, 1):
            print(f"\n   Resultaat {i}:")
            print(f"   - Source: {r.source.name}")
            print(f"   - Success: {r.success}")
            print(f"   - Text: {r.definition[:100] if r.definition else 'EMPTY'}...")
    else:
        print("   ❌ GEEN RESULTATEN")

    # Test 3: SRU (juridische bronnen)
    print("\n" + "=" * 80)
    print("🏛️  TEST 3: SRU lookup (Wetten.nl) voor 'bestuurlijke boete'")
    print("-" * 80)

    request3 = LookupRequest(
        term="bestuurlijke boete",
        sources=["wetgeving"],
        max_results=3,
        context="bestuursrecht",
    )

    start = time.time()
    results3 = await service.lookup(request3)
    elapsed = time.time() - start

    print(f"⏱️  Tijd: {elapsed:.3f}s")
    print(f"📊 Resultaten: {len(results3)}")

    if results3:
        for i, r in enumerate(results3, 1):
            print(f"\n   Resultaat {i}:")
            print(f"   - Source: {r.source.name}")
            print(f"   - Success: {r.success}")
    else:
        print("   ❌ GEEN RESULTATEN")
        debug = service._last_debug
        if debug:
            print("\n🔍 DEBUG INFO:")
            for att in debug.get("attempts", []):
                print(f"      • {att}")

    print("\n" + "=" * 80)
    print("✅ TEST VOLTOOID")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(test_weblookup())
