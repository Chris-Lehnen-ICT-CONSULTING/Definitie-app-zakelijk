#!/usr/bin/env python3
"""
Comprehensive test van ALLE web lookup endpoints voor "onherroepelijk vonnis".

Tests alle providers:
- Wikipedia
- Wiktionary
- SRU Overheid.nl
- SRU Wetgeving.nl
- SRU Rechtspraak.nl
- SRU Overheid Zoekservice
"""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

logging.basicConfig(
    level=logging.INFO, format="%(levelname)-8s %(name)-35s %(message)s"
)
logger = logging.getLogger(__name__)

# Suppress verbose logs
logging.getLogger("services.web_lookup.wikipedia_service").setLevel(logging.WARNING)
logging.getLogger("services.web_lookup.sru_service").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)


async def test_endpoint(name: str, coro):
    """Test een endpoint en log resultaten."""
    print(f"\n{'='*70}")
    print(f"TESTING: {name}")
    print("=" * 70)

    try:
        results = await coro

        if results:
            print(f"✅ SUCCES: {len(results)} result(s) gevonden")
            for i, r in enumerate(results[:3], 1):
                conf = getattr(r.source, "confidence", 0.0)
                title = getattr(r, "definition", "")[:80]
                print(f"   [{i}] Confidence: {conf:.2f} - {title}...")
        else:
            print("❌ GEEN RESULTATEN")

        return len(results) if results else 0

    except Exception as e:
        print(f"💥 ERROR: {e}")
        return 0


async def test_sru_endpoints():
    """Test alle SRU endpoints."""
    from services.web_lookup.sru_service import SRUService

    results_count = {}

    async with SRUService() as sru:
        # Test elke SRU endpoint
        endpoints = {
            "SRU Overheid.nl": "overheid",
            "SRU Wetgeving.nl": "wetgeving_nl",
            "SRU Rechtspraak.nl": "rechtspraak",
            "SRU Overheid Zoekservice": "overheid_zoek",
        }

        for name, endpoint_key in endpoints.items():
            count = await test_endpoint(
                name,
                sru.search(
                    term="onherroepelijk vonnis", endpoint=endpoint_key, max_records=5
                ),
            )
            results_count[name] = count

            # Show query attempts
            attempts = sru.get_attempts()
            if attempts:
                strategies = {}
                for att in attempts:
                    strat = att.get("strategy", "unknown")
                    strategies[strat] = strategies.get(strat, 0) + 1

                print(f"   Queries uitgevoerd: {len(attempts)}")
                for strat, count in strategies.items():
                    print(f"      - {strat}: {count}x")

    return results_count


async def test_mediawiki_endpoints():
    """Test Wikipedia en Wiktionary."""
    from services.interfaces import LookupRequest
    from services.modern_web_lookup_service import ModernWebLookupService

    service = ModernWebLookupService()
    results_count = {}

    # Test Wikipedia
    wiki_request = LookupRequest(
        term="onherroepelijk vonnis", sources=["wikipedia"], max_results=5
    )
    wiki_results = await service.lookup(wiki_request)
    count = await test_endpoint("Wikipedia", asyncio.sleep(0, result=wiki_results))
    results_count["Wikipedia"] = count

    # Show Wikipedia attempts
    wiki_attempts = [
        a
        for a in service._debug_attempts
        if "wikipedia" in a.get("provider", "").lower()
    ]
    if wiki_attempts:
        print(f"   Wikipedia pogingen: {len(wiki_attempts)}")
        synonyms = [a for a in wiki_attempts if a.get("fallback")]
        if synonyms:
            print(f"      - Synoniemen geprobeerd: {len(synonyms)}")
            for syn in synonyms[:3]:
                term = syn.get("term", "?")
                success = "✓" if syn.get("success") else "✗"
                print(f"        {success} {term}")

    # Test Wiktionary
    service._debug_attempts = []  # Reset
    wikt_request = LookupRequest(
        term="onherroepelijk vonnis", sources=["wiktionary"], max_results=5
    )
    wikt_results = await service.lookup(wikt_request)
    count = await test_endpoint("Wiktionary", asyncio.sleep(0, result=wikt_results))
    results_count["Wiktionary"] = count

    return results_count


async def test_full_lookup():
    """Test complete lookup met ALLE providers tegelijk."""
    from services.interfaces import LookupRequest
    from services.modern_web_lookup_service import ModernWebLookupService

    print(f"\n{'='*70}")
    print("TESTING: FULL LOOKUP (alle providers tegelijk)")
    print("=" * 70)

    service = ModernWebLookupService()
    request = LookupRequest(
        term="onherroepelijk vonnis", context="OM | Strafrecht | Sv", max_results=10
    )

    results = await service.lookup(request)

    print(f"✅ TOTAAL: {len(results)} result(s) na ranking & dedup")

    # Group by provider
    by_provider = {}
    for r in results:
        prov = getattr(r.source, "name", "Unknown")
        by_provider[prov] = by_provider.get(prov, 0) + 1

    print("\n   Verdeling per provider:")
    for prov, count in sorted(by_provider.items(), key=lambda x: -x[1]):
        print(f"      - {prov}: {count}")

    print("\n   Top 3 resultaten:")
    for i, r in enumerate(results[:3], 1):
        conf = getattr(r.source, "confidence", 0.0)
        prov = getattr(r.source, "name", "?")
        title = getattr(r, "definition", "")[:60]
        print(f"      [{i}] {prov} (conf={conf:.2f}): {title}...")

    return len(results)


async def main():
    """Run comprehensive endpoint tests."""
    print("\n" + "=" * 70)
    print("COMPREHENSIVE WEB LOOKUP ENDPOINT TEST")
    print("Term: 'onherroepelijk vonnis'")
    print("=" * 70)

    # Test SRU endpoints
    print("\n🔵 FASE 1: SRU Endpoints")
    sru_counts = await test_sru_endpoints()

    # Test MediaWiki endpoints
    print("\n\n🔵 FASE 2: MediaWiki Endpoints")
    wiki_counts = await test_mediawiki_endpoints()

    # Test full lookup
    print("\n\n🔵 FASE 3: Full Integrated Lookup")
    total_count = await test_full_lookup()

    # Summary
    print("\n" + "=" * 70)
    print("SAMENVATTING")
    print("=" * 70)

    all_counts = {**sru_counts, **wiki_counts}

    print("\nResultaten per provider:")
    for name, count in sorted(all_counts.items(), key=lambda x: -x[1]):
        status = "✅" if count > 0 else "❌"
        print(f"  {status} {name:35s} {count:2d} result(s)")

    print(f"\n📊 TOTAAL na ranking/dedup: {total_count} resultaten")

    success_rate = sum(1 for c in all_counts.values() if c > 0) / len(all_counts) * 100
    print(
        f"📈 SUCCESS RATE: {success_rate:.0f}% providers ({sum(1 for c in all_counts.values() if c > 0)}/{len(all_counts)})"
    )

    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
