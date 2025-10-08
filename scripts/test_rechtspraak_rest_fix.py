#!/usr/bin/env python3
"""
Test Rechtspraak.nl REST API fix - text search functionaliteit.
"""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(name)s - %(message)s")
logger = logging.getLogger(__name__)


async def test_rechtspraak_ecli_lookup():
    """Test ECLI lookup (bestaande functionaliteit)."""
    from services.web_lookup.rechtspraak_rest_service import rechtspraak_lookup

    print("\n" + "=" * 70)
    print("TEST 1: ECLI Lookup (bestaande functionaliteit)")
    print("=" * 70)

    # Test met een bekende ECLI
    result = await rechtspraak_lookup("ECLI:NL:RBARN:1998:AA1005")

    if result:
        print("✅ SUCCES: ECLI lookup werkt")
        print(f"   Title: {result.metadata.get('dc_title', 'N/A')[:60]}...")
        print(f"   URL: {result.source.url}")
        print(f"   Confidence: {result.source.confidence}")
    else:
        print("❌ FAILED: Geen resultaat voor ECLI lookup")


async def test_rechtspraak_text_skip():
    """Test dat text search wordt geskipt (geen full-text search support)."""
    from services.web_lookup.rechtspraak_rest_service import rechtspraak_lookup

    print("\n" + "=" * 70)
    print("TEST 2: Text Search Skipped (geen ECLI)")
    print("=" * 70)

    result = await rechtspraak_lookup("vonnis")

    if result is None:
        print("✅ CORRECT: Text search geskipt (geen ECLI gedetecteerd)")
        print("   Rechtspraak API heeft geen full-text search")
        print("   Voorkomt random irrelevante uitspraken in results")
    else:
        print("❌ FOUT: Zou None moeten retourneren voor niet-ECLI termen")


async def test_rechtspraak_integration():
    """Test integratie via modern_web_lookup_service."""
    from services.interfaces import LookupRequest
    from services.modern_web_lookup_service import ModernWebLookupService

    print("\n" + "=" * 70)
    print("TEST 3: Integration Test (via ModernWebLookupService)")
    print("=" * 70)

    service = ModernWebLookupService()

    # Test 3a: Geen ECLI (moet skippen)
    request = LookupRequest(
        term="onherroepelijk vonnis", sources=["rechtspraak"], max_results=3
    )
    results = await service.lookup(request)

    if not results:
        print("✅ CORRECT: Geen results voor niet-ECLI term")
        print("   Term: 'onherroepelijk vonnis' (geen ECLI)")
        print("   Rechtspraak wordt correct geskipt")
    else:
        print(f"⚠️  UNEXPECTED: {len(results)} result(s) gevonden")
        print("   (mogelijk cached van eerdere test?)")

    # Test 3b: Met ECLI (moet werken)
    request_ecli = LookupRequest(
        term="ECLI:NL:RBARN:1998:AA1005", sources=["rechtspraak"], max_results=1
    )
    results_ecli = await service.lookup(request_ecli)

    if results_ecli:
        print(f"\n✅ CORRECT: {len(results_ecli)} result(s) voor ECLI term")
        print("   ECLI lookup werkt zoals verwacht")
    else:
        print("\n❌ FOUT: Zou resultaat moeten geven voor expliciete ECLI")


async def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("RECHTSPRAAK.NL REST API FIX - TEST SUITE")
    print("=" * 70)

    try:
        await test_rechtspraak_ecli_lookup()
        await test_rechtspraak_text_skip()
        await test_rechtspraak_integration()

        print("\n" + "=" * 70)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 70)

    except Exception as e:
        logger.error(f"\n❌ TEST FAILED: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
