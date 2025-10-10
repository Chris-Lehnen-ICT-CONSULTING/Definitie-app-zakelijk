#!/usr/bin/env python3
"""
Live test script voor web lookup endpoints.

Test de werkelijke API calls naar wetten.nl en rechtspraak.nl
om te verifiëren welke endpoints werken en welke queries succesvol zijn.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_sru_wetgeving():
    """Test Wetgeving.nl SRU endpoint met verschillende query strategieën."""
    from services.web_lookup.sru_service import SRUService

    logger.info("=" * 80)
    logger.info("TEST 1: Wetgeving.nl (SRU via zoekservice.overheid.nl)")
    logger.info("=" * 80)

    test_terms = [
        "onherroepelijk vonnis",
        "strafrecht",
        "artikel 81",
        "wetboek van strafrecht",
    ]

    async with SRUService() as sru:
        for term in test_terms:
            logger.info(f"\n--- Testing term: '{term}' ---")
            try:
                results = await sru.search(
                    term=term, endpoint="wetgeving_nl", max_records=3
                )

                if results:
                    logger.info(f"✅ SUCCESS: {len(results)} results gevonden")
                    for i, result in enumerate(results, 1):
                        logger.info(
                            f"  {i}. {result.source.name}: {result.definition[:100]}..."
                        )
                        logger.info(f"     URL: {result.source.url}")
                        logger.info(f"     Confidence: {result.source.confidence:.2f}")
                else:
                    logger.warning("❌ FAIL: Geen resultaten gevonden")

                # Log query attempts
                attempts = sru.get_attempts()
                logger.info(f"Query attempts: {len(attempts)}")
                for attempt in attempts[-3:]:  # Laatste 3 attempts
                    status = "✓" if attempt.get("success") else "✗"
                    logger.info(
                        f"  {status} {attempt.get('strategy', 'unknown')}: "
                        f"{attempt.get('query', 'N/A')[:60]}..."
                    )

            except Exception as e:
                logger.error(f"❌ ERROR: {e}", exc_info=True)


async def test_sru_overheid():
    """Test Overheid.nl SRU endpoint (ter vergelijking - dit werkt wel)."""
    from services.web_lookup.sru_service import SRUService

    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: Overheid.nl (SRU via repository.overheid.nl)")
    logger.info("=" * 80)

    test_terms = ["onherroepelijk vonnis", "strafrecht"]

    async with SRUService() as sru:
        for term in test_terms:
            logger.info(f"\n--- Testing term: '{term}' ---")
            try:
                results = await sru.search(
                    term=term, endpoint="overheid", max_records=3
                )

                if results:
                    logger.info(f"✅ SUCCESS: {len(results)} results gevonden")
                    for i, result in enumerate(results, 1):
                        logger.info(
                            f"  {i}. {result.source.name}: {result.definition[:100]}..."
                        )
                else:
                    logger.warning("❌ FAIL: Geen resultaten gevonden")

            except Exception as e:
                logger.error(f"❌ ERROR: {e}", exc_info=True)


async def test_rechtspraak_rest():
    """Test Rechtspraak.nl REST API."""
    from services.web_lookup.rechtspraak_rest_service import (
        RechtspraakRESTService, rechtspraak_lookup)

    logger.info("\n" + "=" * 80)
    logger.info("TEST 3: Rechtspraak.nl (REST API)")
    logger.info("=" * 80)

    # Test 1: ECLI lookup (zou moeten werken)
    logger.info("\n--- Test 3A: ECLI lookup ---")
    ecli_term = "ECLI:NL:HR:2021:123"  # Voorbeeld ECLI
    try:
        result = await rechtspraak_lookup(ecli_term)
        if result:
            logger.info("✅ SUCCESS: ECLI lookup werkt")
            logger.info(f"   Definition: {result.definition[:100]}...")
        else:
            logger.info("⚠️  ECLI niet gevonden (mogelijk ongeldig test ECLI)")
    except Exception as e:
        logger.error(f"❌ ERROR: {e}", exc_info=True)

    # Test 2: Text search (nieuwe functionaliteit)
    logger.info("\n--- Test 3B: Text search ---")
    test_terms = ["onherroepelijk vonnis", "strafrecht", "hoger beroep"]

    for term in test_terms:
        logger.info(f"\nTesting: '{term}'")
        try:
            result = await rechtspraak_lookup(term)
            if result:
                logger.info(f"✅ SUCCESS: Text search werkt voor '{term}'")
                logger.info(f"   Definition: {result.definition[:100]}...")
                logger.info(f"   URL: {result.source.url}")
            else:
                logger.warning(f"❌ FAIL: Geen resultaten voor '{term}'")
        except Exception as e:
            logger.error(f"❌ ERROR voor '{term}': {e}", exc_info=True)


async def test_modern_web_lookup_integrated():
    """Test de geïntegreerde ModernWebLookupService."""
    from services.interfaces import LookupRequest
    from services.modern_web_lookup_service import ModernWebLookupService

    logger.info("\n" + "=" * 80)
    logger.info("TEST 4: Geïntegreerde ModernWebLookupService")
    logger.info("=" * 80)

    service = ModernWebLookupService()

    test_cases = [
        ("onherroepelijk vonnis", "OM | Strafrecht | Sv"),
        ("wetboek van strafrecht", "OM | Strafrecht"),
        ("artikel 81 sv", "OM | Strafrecht | Sv"),
    ]

    for term, context in test_cases:
        logger.info(f"\n--- Testing: '{term}' (context: {context}) ---")

        request = LookupRequest(term=term, context=context, max_results=5)

        try:
            results = await service.lookup(request)

            if results:
                logger.info(f"✅ SUCCESS: {len(results)} totale resultaten")

                # Group by provider
                by_provider = {}
                for result in results:
                    provider = result.source.name
                    by_provider.setdefault(provider, []).append(result)

                for provider, provider_results in by_provider.items():
                    logger.info(f"  📦 {provider}: {len(provider_results)} resultaten")
                    for i, r in enumerate(provider_results[:2], 1):  # Eerste 2
                        logger.info(f"     {i}. {r.definition[:80]}...")
                        logger.info(f"        Confidence: {r.source.confidence:.2f}")
            else:
                logger.warning("❌ FAIL: Geen resultaten")

            # Debug info
            debug = service._last_debug
            if debug:
                logger.info("\nDebug info:")
                logger.info(f"  Selected sources: {debug.get('selected_sources', [])}")
                logger.info(f"  Total attempts: {len(debug.get('attempts', []))}")

        except Exception as e:
            logger.error(f"❌ ERROR: {e}", exc_info=True)


async def main():
    """Run all tests."""
    logger.info("🚀 Starting Web Lookup Live Tests")
    logger.info("=" * 80)

    try:
        # Test 1: Wetgeving.nl SRU
        await test_sru_wetgeving()

        # Test 2: Overheid.nl SRU (ter vergelijking)
        await test_sru_overheid()

        # Test 3: Rechtspraak.nl REST
        await test_rechtspraak_rest()

        # Test 4: Geïntegreerde service
        await test_modern_web_lookup_integrated()

        logger.info("\n" + "=" * 80)
        logger.info("✅ All tests completed")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
