#!/usr/bin/env python3
"""
Manual Testing Script voor SynonymOrchestrator (PHASE 2.1).

Dit script test de SynonymOrchestrator funcionaliteit zonder unit test framework.
Gebruikt voor snelle verificatie tijdens development.

Usage:
    python scripts/test_synonym_orchestrator_manual.py

Architecture Reference:
    docs/architectuur/synonym-orchestrator-architecture-v3.1.md
    docs/integration/synonym_orchestrator_integration.md
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from config.synonym_config import SynonymPolicy, get_synonym_config, reload_config
from repositories.synonym_registry import get_synonym_registry
from services.gpt4_synonym_suggester import GPT4SynonymSuggester
from services.synonym_orchestrator import SynonymOrchestrator


def print_separator(title: str = ""):
    """Print visuele separator."""
    if title:
        print(f"\n{'=' * 60}")
        print(f"  {title}")
        print("=" * 60)
    else:
        print("-" * 60)


def test_initialization():
    """Test 1: Orchestrator initialisatie."""
    print_separator("TEST 1: Initialization")

    try:
        # Get dependencies
        registry = get_synonym_registry()
        gpt4_suggester = GPT4SynonymSuggester()

        # Create orchestrator
        orchestrator = SynonymOrchestrator(registry, gpt4_suggester)

        print("✅ Orchestrator created successfully")
        print(f"   Config policy: {orchestrator.config.policy.value}")
        print(f"   Cache TTL: {orchestrator.config.cache_ttl_seconds}s")
        print(f"   Cache max size: {orchestrator.config.cache_max_size}")
        print(
            f"   Min synonyms threshold: {orchestrator.config.min_synonyms_threshold}"
        )

        return orchestrator

    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return None


def test_basic_query(orchestrator: SynonymOrchestrator):
    """Test 2: Basic synonym query."""
    print_separator("TEST 2: Basic Query")

    try:
        # Query existing term (should exist from migration)
        term = "voorlopige hechtenis"
        synonyms = orchestrator.get_synonyms_for_lookup(
            term=term, max_results=5, min_weight=0.7
        )

        print(f"Query: '{term}'")
        print(f"Found: {len(synonyms)} synonyms")

        if synonyms:
            print("\nSynonyms:")
            for i, syn in enumerate(synonyms, 1):
                print(
                    f"  {i}. {syn.term} "
                    f"(weight: {syn.weight:.2f}, "
                    f"status: {syn.status}, "
                    f"preferred: {syn.is_preferred})"
                )
            print("✅ Query successful")
        else:
            print("⚠️  No synonyms found (registry might be empty)")

        # Check cache stats
        stats = orchestrator.get_cache_stats()
        print(
            f"\nCache stats: hits={stats['hits']}, misses={stats['misses']}, size={stats['size']}"
        )

    except Exception as e:
        print(f"❌ Query failed: {e}")


def test_cache_hit(orchestrator: SynonymOrchestrator):
    """Test 3: Cache hit behavior."""
    print_separator("TEST 3: Cache Hit")

    try:
        term = "voorlopige hechtenis"

        # First query (cache miss)
        print(f"First query: '{term}'")
        synonyms1 = orchestrator.get_synonyms_for_lookup(term, max_results=5)
        stats1 = orchestrator.get_cache_stats()
        print(f"  Result: {len(synonyms1)} synonyms")
        print(f"  Cache: hits={stats1['hits']}, misses={stats1['misses']}")

        # Second query (should be cache hit)
        print(f"\nSecond query: '{term}' (should be cache HIT)")
        synonyms2 = orchestrator.get_synonyms_for_lookup(term, max_results=5)
        stats2 = orchestrator.get_cache_stats()
        print(f"  Result: {len(synonyms2)} synonyms")
        print(f"  Cache: hits={stats2['hits']}, misses={stats2['misses']}")

        # Verify hit rate
        print(f"\nCache hit rate: {stats2['hit_rate']:.1%}")

        if stats2["hits"] > stats1["hits"]:
            print("✅ Cache hit detected")
        else:
            print("❌ Cache hit NOT detected")

    except Exception as e:
        print(f"❌ Cache test failed: {e}")


def test_cache_invalidation(orchestrator: SynonymOrchestrator):
    """Test 4: Cache invalidation."""
    print_separator("TEST 4: Cache Invalidation")

    try:
        term = "test_term"

        # Prime cache
        print(f"Prime cache for '{term}'")
        orchestrator.get_synonyms_for_lookup(term, max_results=5)
        stats1 = orchestrator.get_cache_stats()
        print(f"  Cache size: {stats1['size']}")

        # Invalidate specific term
        print(f"\nInvalidate cache for '{term}'")
        orchestrator.invalidate_cache(term)
        stats2 = orchestrator.get_cache_stats()
        print(f"  Cache size after invalidation: {stats2['size']}")

        # Query again (should be cache miss)
        print("\nQuery after invalidation (should be MISS)")
        orchestrator.get_synonyms_for_lookup(term, max_results=5)
        stats3 = orchestrator.get_cache_stats()
        print(f"  Cache: hits={stats3['hits']}, misses={stats3['misses']}")

        if stats3["misses"] > stats2["misses"]:
            print("✅ Cache invalidation working")
        else:
            print("❌ Cache invalidation NOT working")

    except Exception as e:
        print(f"❌ Invalidation test failed: {e}")


def test_governance_policy(orchestrator: SynonymOrchestrator):
    """Test 5: Governance policy enforcement."""
    print_separator("TEST 5: Governance Policy")

    try:
        print(f"Current policy: {orchestrator.config.policy.value}")

        # Test STRICT policy (only active)
        term = "voorlopige hechtenis"
        synonyms = orchestrator.get_synonyms_for_lookup(term, max_results=10)

        active_count = sum(1 for s in synonyms if s.status == "active")
        ai_pending_count = sum(1 for s in synonyms if s.status == "ai_pending")

        print(f"\nResults for '{term}':")
        print(f"  Active: {active_count}")
        print(f"  AI pending: {ai_pending_count}")

        if orchestrator.config.policy == SynonymPolicy.STRICT:
            if ai_pending_count == 0:
                print("✅ STRICT policy enforced (no ai_pending)")
            else:
                print("❌ STRICT policy NOT enforced (ai_pending found)")
        else:
            print("✅ PRAGMATIC policy allows ai_pending")

    except Exception as e:
        print(f"❌ Policy test failed: {e}")


async def test_enrichment(orchestrator: SynonymOrchestrator):
    """Test 6: GPT-4 enrichment flow (placeholder)."""
    print_separator("TEST 6: GPT-4 Enrichment (Placeholder)")

    try:
        term = "test_enrichment_term"

        print(f"Ensure synonyms for '{term}' (min_count=5)")
        print("Note: GPT-4 is placeholder, will return 0 AI suggestions")

        synonyms, ai_count = await orchestrator.ensure_synonyms(
            term=term,
            min_count=5,
            context={
                "definitie": "Test definitie",
                "tokens": ["test", "strafrecht"],
                "domain": "strafrecht",
            },
        )

        print("\nResult:")
        print(f"  Found: {len(synonyms)} synonyms")
        print(f"  AI suggestions: {ai_count}")

        if ai_count == 0:
            print("✅ Enrichment flow executed (placeholder returned 0 as expected)")
        else:
            print(f"⚠️  Unexpected AI count: {ai_count}")

    except Exception as e:
        print(f"❌ Enrichment test failed: {e}")


def test_health_check(orchestrator: SynonymOrchestrator):
    """Test 7: Health check."""
    print_separator("TEST 7: Health Check")

    try:
        health = orchestrator.get_health_check()

        print(f"Status: {health['status']}")
        print(f"Timestamp: {health['timestamp']}")

        if health.get("warnings"):
            print(f"Warnings: {health['warnings']}")

        print("\nCache Stats:")
        cache_stats = health["cache_stats"]
        for key, value in cache_stats.items():
            print(f"  {key}: {value}")

        print("\nRegistry Stats:")
        registry_stats = health["registry_stats"]
        for key, value in registry_stats.items():
            if key == "top_groups":
                continue  # Skip detailed list
            print(f"  {key}: {value}")

        print("✅ Health check successful")

    except Exception as e:
        print(f"❌ Health check failed: {e}")


def test_cache_eviction(orchestrator: SynonymOrchestrator):
    """Test 8: Cache size enforcement (LRU eviction)."""
    print_separator("TEST 8: Cache Eviction (LRU)")

    try:
        # Get current max size
        max_size = orchestrator.config.cache_max_size
        print(f"Cache max size: {max_size}")

        # Query many terms to trigger eviction
        print(f"\nQuerying {max_size + 5} terms to trigger eviction...")

        for i in range(max_size + 5):
            term = f"test_term_{i}"
            orchestrator.get_synonyms_for_lookup(term, max_results=1)

        stats = orchestrator.get_cache_stats()
        print(f"\nCache size after queries: {stats['size']}")
        print(f"Expected: <= {max_size}")

        if stats["size"] <= max_size:
            print("✅ Cache eviction working (size limited)")
        else:
            print(f"❌ Cache eviction NOT working (size: {stats['size']} > {max_size})")

    except Exception as e:
        print(f"❌ Eviction test failed: {e}")


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("  SynonymOrchestrator Manual Test Suite (PHASE 2.1)")
    print("=" * 60)

    # Test 1: Initialization
    orchestrator = test_initialization()
    if not orchestrator:
        print("\n❌ Cannot continue without orchestrator")
        return

    # Test 2: Basic query
    test_basic_query(orchestrator)

    # Test 3: Cache hit
    test_cache_hit(orchestrator)

    # Test 4: Cache invalidation
    test_cache_invalidation(orchestrator)

    # Test 5: Governance policy
    test_governance_policy(orchestrator)

    # Test 6: GPT-4 enrichment (async)
    await test_enrichment(orchestrator)

    # Test 7: Health check
    test_health_check(orchestrator)

    # Test 8: Cache eviction
    test_cache_eviction(orchestrator)

    # Final summary
    print_separator("SUMMARY")
    final_stats = orchestrator.get_cache_stats()
    print("Final cache stats:")
    print(f"  Size: {final_stats['size']}/{final_stats['max_size']}")
    print(f"  Hit rate: {final_stats['hit_rate']:.1%}")
    print(f"  Hits: {final_stats['hits']}, Misses: {final_stats['misses']}")

    print("\n✅ All tests completed")
    print("\nNext steps:")
    print("  1. Integrate into ServiceContainer")
    print("  2. Register cache invalidation callback")
    print("  3. Update definition generation flow")
    print("  4. Create unit tests")


if __name__ == "__main__":
    asyncio.run(main())
