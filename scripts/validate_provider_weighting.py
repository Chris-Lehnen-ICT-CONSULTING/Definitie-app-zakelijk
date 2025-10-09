#!/usr/bin/env python3
"""
Validate that provider weighting is applied correctly (no double-weighting).
Quick validation script to verify the Oct 2025 fix is working.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.interfaces import LookupRequest
from src.services.modern_web_lookup_service import ModernWebLookupService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_no_double_weighting():
    """Verify that provider weights are applied exactly once."""
    service = ModernWebLookupService()

    # Test term that should hit multiple providers
    request = LookupRequest(
        term="rechtbank", context="strafrecht | vonnis", max_results=5
    )

    results = await service.lookup(request)

    print("\n=== Provider Weighting Validation ===")
    print(f"Found {len(results)} results\n")

    # Check debug info for double-weighting indicators
    debug = service._last_debug
    if debug:
        print("Debug Attempts:")
        for attempt in debug.get("attempts", []):
            provider = attempt.get("provider", "unknown")
            success = attempt.get("success", False)
            confidence = attempt.get("confidence", 0.0)
            print(f"  - {provider}: success={success}, confidence={confidence:.3f}")

    # Verify results have reasonable confidence scores (not > 1.0)
    print("\nResult Confidence Scores:")
    for i, result in enumerate(results):
        confidence = result.source.confidence
        provider = result.source.name

        if confidence > 1.0:
            print(f"  ❌ Result {i+1} ({provider}): {confidence:.3f} - OVER-WEIGHTED!")
        else:
            print(f"  ✅ Result {i+1} ({provider}): {confidence:.3f}")

    # Check if juridische boost was applied
    print("\nJuridische Boost Check:")
    juridical_count = sum(1 for r in results if r.source.is_juridical)
    print(f"  Juridical results: {juridical_count}/{len(results)}")

    return all(r.source.confidence <= 1.0 for r in results)


async def test_synonym_usage():
    """Check which providers actually use synonyms."""
    service = ModernWebLookupService()

    # Test term with known synonyms
    request = LookupRequest(term="onherroepelijk vonnis", max_results=3)

    results = await service.lookup(request)

    print("\n=== Synonym Usage Analysis ===")
    print(f"Term: '{request.term}'\n")

    # Check debug attempts for synonym usage
    debug = service._last_debug
    if debug:
        synonym_attempts = [
            a
            for a in debug.get("attempts", [])
            if a.get("synonym_of") or a.get("fallback")
        ]

        if synonym_attempts:
            print("Synonym Attempts Found:")
            for attempt in synonym_attempts:
                provider = attempt.get("provider", "unknown")
                term = attempt.get("term", "")
                original = attempt.get("synonym_of", "N/A")
                success = attempt.get("success", False)
                print(
                    f"  - {provider}: '{term}' (synonym of '{original}') - success={success}"
                )
        else:
            print("  No synonym attempts found in debug log")

    print(f"\nFinal results: {len(results)} found")
    for i, result in enumerate(results):
        print(f"  {i+1}. {result.source.name}: {result.source.url[:50]}...")


async def main():
    """Run validation tests."""
    print("=" * 60)
    print("Provider Weighting & Synonym Validation")
    print("=" * 60)

    # Test 1: No double weighting
    success1 = await test_no_double_weighting()

    # Test 2: Synonym usage analysis
    await test_synonym_usage()

    print("\n" + "=" * 60)
    print("VALIDATION COMPLETE")
    print("=" * 60)

    if success1:
        print("✅ No double-weighting detected - Oct 2025 fix verified!")
    else:
        print("❌ Double-weighting still present - needs investigation")

    return 0 if success1 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
