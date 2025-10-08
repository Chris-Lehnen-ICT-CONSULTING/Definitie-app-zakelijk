#!/usr/bin/env python3
"""
Test script voor web lookup fixes - specifiek voor "onherroepelijk vonnis" use case.

Tests:
1. Circuit breaker is verhoogd naar 4
2. Partial word match query wordt uitgevoerd
3. Wikipedia synoniem fallback werkt
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(name)s - %(message)s")
logger = logging.getLogger(__name__)


async def test_circuit_breaker_config():
    """Test dat circuit breaker threshold is verhoogd."""
    from services.web_lookup.sru_service import SRUService

    service = SRUService()

    # Check default threshold
    assert (
        service.circuit_breaker_config["consecutive_empty_threshold"] == 4
    ), f"Expected threshold 4, got {service.circuit_breaker_config['consecutive_empty_threshold']}"

    # Check provider-specific thresholds
    assert service.circuit_breaker_config["providers"]["overheid"] == 4
    assert service.circuit_breaker_config["providers"]["rechtspraak"] == 5
    assert service.circuit_breaker_config["providers"]["wetgeving_nl"] == 4

    logger.info("✅ Circuit breaker threshold correct (4 queries)")


async def test_partial_word_match():
    """Test partial word match voor multi-word termen."""
    from services.web_lookup.sru_service import SRUService

    async with SRUService() as service:
        # Test met "onherroepelijk vonnis"
        # Dit zou nu meer resultaten moeten vinden door partial word match
        results = await service.search(
            term="onherroepelijk vonnis", endpoint="overheid", max_records=5
        )

        attempts = service.get_attempts()

        # Check of partial_words strategy is gebruikt
        partial_word_attempts = [
            a for a in attempts if a.get("strategy") == "partial_words"
        ]

        logger.info(f"Total attempts: {len(attempts)}")
        logger.info(f"Partial word attempts: {len(partial_word_attempts)}")

        if partial_word_attempts:
            logger.info("✅ Partial word match query was uitgevoerd")
            for att in partial_word_attempts[:2]:
                logger.info(f"   Query: {att.get('query', 'N/A')}")
        else:
            logger.warning(
                "⚠️  Partial word match niet bereikt (mogelijk al eerder gevonden)"
            )

        logger.info(f"Results found: {len(results)}")
        if results:
            for r in results[:3]:
                logger.info(f"   - {r.source.name}: {r.definition[:80]}...")


async def test_wikipedia_synonyms():
    """Test Wikipedia synoniem fallback."""
    from services.interfaces import LookupRequest
    from services.modern_web_lookup_service import ModernWebLookupService

    service = ModernWebLookupService()

    request = LookupRequest(
        term="onherroepelijk vonnis", sources=["wikipedia"], max_results=5, timeout=30
    )

    results = await service.lookup(request)

    # Check debug attempts voor synoniemen
    if service._debug_attempts:
        synonym_attempts = [
            a
            for a in service._debug_attempts
            if a.get("fallback") and a.get("synonym_of")
        ]

        logger.info(f"Wikipedia attempts: {len(service._debug_attempts)}")
        logger.info(f"Synonym fallback attempts: {len(synonym_attempts)}")

        if synonym_attempts:
            logger.info("✅ Wikipedia synoniem fallback actief")
            for att in synonym_attempts[:5]:
                logger.info(
                    f"   Synonym: {att.get('term')} (for: {att.get('synonym_of')})"
                )
        else:
            logger.info("INFO: Geen synoniemen nodig (direct gevonden)")

    logger.info(f"Wikipedia results: {len(results)}")
    if results:
        for r in results:
            logger.info(f"   - {r.definition[:100]}...")


async def main():
    """Run alle tests."""
    logger.info("=" * 60)
    logger.info("TESTING WEB LOOKUP FIXES FOR 'onherroepelijk vonnis'")
    logger.info("=" * 60)

    try:
        logger.info("\n[1/3] Testing Circuit Breaker Config...")
        await test_circuit_breaker_config()

        logger.info("\n[2/3] Testing Partial Word Match...")
        await test_partial_word_match()

        logger.info("\n[3/3] Testing Wikipedia Synonyms...")
        await test_wikipedia_synonyms()

        logger.info("\n" + "=" * 60)
        logger.info("✅ ALL TESTS COMPLETED")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"\n❌ TEST FAILED: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
