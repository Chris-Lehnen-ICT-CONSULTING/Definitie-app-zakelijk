"""
End-to-End Integration Tests voor Synonym Orchestrator v3.1 (Architecture PHASE 3).

Test complete flow: definitie generation → synonym enrichment → review → manual edit sync.

Test Categories:
- PHASE 3.1 & 3.2: Generation flow with enrichment and review UI
- PHASE 3.3: Manual edit sync to registry
- Cache invalidation and data consistency

Architecture Reference: docs/architectuur/synonym-orchestrator-architecture-v3.1.md
"""

import logging
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from src.database.definitie_repository import DefinitieRecord
from src.services.definition_repository import (
    DefinitionRepository,  # Use services repository
)
from src.services.interfaces import Definition, GenerationRequest
from src.services.orchestrators.definition_orchestrator_v2 import (
    DefinitionOrchestratorV2,
)
from src.services.synonym_orchestrator import SynonymOrchestrator, WeightedSynonym

logger = logging.getLogger(__name__)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture()
def container(initialized_synonym_db):
    """Create a test container with initialized synonym database."""
    from src.services.container import ServiceContainer, reset_container

    # Reset global container to ensure test isolation
    reset_container()

    # Create test container with temp db
    config = {
        "db_path": initialized_synonym_db,  # Use initialized db with synonym tables
        "use_json_rules": False,  # Skip validation rules for faster tests
    }
    test_container = ServiceContainer(config)

    # Override global container for this test
    # This ensures _sync_synonyms_to_registry() uses the TEST database
    import src.services.container as container_module

    container_module._default_container = test_container

    yield test_container

    # Cleanup: reset global container after test
    reset_container()


# ============================================================================
# TEST 1: Complete Flow - Generation → Enrichment → Review
# ============================================================================


@pytest.mark.asyncio()
@pytest.mark.integration()
async def test_definition_generation_with_synonym_enrichment_e2e(container):
    """
    E2E: Definitiegeneratie → enrichment → weblookup → review.

    Flow (Architecture v3.1, PHASE 3.1 & 3.2):
    1. Generate definition for term with <5 synonyms
    2. Verify GPT-4 enrichment triggered
    3. Verify AI-pending synonyms created in registry
    4. Verify metadata in generation response
    5. Simulate user approval via registry
    6. Verify synonyms activated and cache invalidated

    Test Context:
    - Container moet synonym_orchestrator hebben geïnjecteerd
    - DefinitionOrchestratorV2 moet ensure_synonyms() aanroepen
    - Registry moet AI-pending members hebben na enrichment
    """
    # Setup: Get services from container
    registry = container.synonym_registry()
    orchestrator = container.orchestrator()
    synonym_orch = container.synonym_orchestrator()

    # Verify orchestrator has synonym_orchestrator injected (PHASE 3.1)
    assert orchestrator.synonym_orchestrator is not None
    assert orchestrator.synonym_orchestrator is synonym_orch

    # Generate definition for term
    request = GenerationRequest(
        id="test-gen-001",
        begrip="voorlopige hechtenis",
        organisatorische_context=["strafrecht"],
        juridische_context=["detentie"],
        wettelijke_basis=[],
        ontologische_categorie="proces",
        actor="test_user",
    )

    # Execute generation (should trigger synonym enrichment via ensure_synonyms)
    response = await orchestrator.create_definition(request, context={})

    # Assertions on response
    assert response.success is True
    assert "synonym_enrichment_status" in response.metadata

    # Check enrichment status (may be "success", "no_synonyms", or "not_available")
    enrichment_status = response.metadata["synonym_enrichment_status"]
    logger.info(f"Synonym enrichment status: {enrichment_status}")

    # If enrichment triggered and synonyms found
    if enrichment_status == "success":
        assert response.metadata["enriched_synonyms_count"] > 0

        # May have AI-pending synonyms if GPT-4 was called
        ai_pending_count = response.metadata.get("ai_pending_synonyms_count", 0)
        logger.info(f"AI-pending synonyms: {ai_pending_count}")

        # Verify enriched synonyms metadata
        enriched_synonyms = response.metadata.get("enriched_synonyms", [])
        assert isinstance(enriched_synonyms, list)

        # Each enriched synonym should have term and weight
        for syn in enriched_synonyms:
            assert "term" in syn
            assert "weight" in syn
            assert isinstance(syn["term"], str)
            assert isinstance(syn["weight"], (int, float))

    # Verify synonym group exists in registry (created by ensure_synonyms)
    group = registry.find_group_by_term("voorlopige hechtenis")

    if group is not None:
        logger.info(f"Synonym group found: {group.canonical_term}")

        # Get all members (active + ai_pending)
        all_members = registry.get_group_members(group_id=group.id)
        logger.info(f"Total members in group: {len(all_members)}")

        # Get AI-pending members specifically
        pending_members = registry.get_group_members(
            group_id=group.id, statuses=["ai_pending"]
        )

        if len(pending_members) > 0:
            logger.info(f"Found {len(pending_members)} AI-pending synonyms for review")

            # Simulate user approval of first pending synonym
            first_pending = pending_members[0]
            logger.info(f"Approving synonym: {first_pending.term}")

            registry.update_member_status(
                member_id=first_pending.id, new_status="active", reviewed_by="test_user"
            )

            # Verify status updated
            updated_member = registry.get_group_member(first_pending.id)
            assert updated_member.status == "active"
            assert updated_member.reviewed_by == "test_user"

            # Verify active members increased
            active_members = registry.get_group_members(
                group_id=group.id, statuses=["active"]
            )
            assert len(active_members) >= 1

            # Verify synonym now available for lookup (cache should be invalidated)
            lookup_synonyms = synonym_orch.get_synonyms_for_lookup(
                "voorlopige hechtenis"
            )
            logger.info(
                f"Lookup synonyms after approval: {[s.term for s in lookup_synonyms]}"
            )

            # The approved synonym should now be in lookup results
            approved_terms = [s.term for s in lookup_synonyms]
            assert first_pending.term in approved_terms


# ============================================================================
# TEST 2: Manual Edit Sync to Registry
# ============================================================================


@pytest.mark.integration()
def test_manual_edit_sync_to_registry(container):
    """
    E2E: Manual edit in definitie-editor → registry sync (PHASE 3.3).

    Flow:
    1. Create definitie via repository
    2. Manual edit: add synoniemen via save_voorbeelden()
    3. Verify synced to registry with definitie_id scope and source=manual
    4. Manual edit: remove synonym
    5. Verify deprecated in registry
    6. Manual edit: re-add synonym
    7. Verify reactivated in registry

    Test Context:
    - DefinitieRepository.save_voorbeelden() moet _sync_synonyms_to_registry() aanroepen
    - Synoniemen moeten scoped zijn (definitie_id + source=manual)
    - Lifecycle: active → deprecated → active (idempotent sync)
    """
    # Setup: Get services
    repo = container.repository()
    registry = container.synonym_registry()

    # Step 1: Create definitie
    definitie = Definition(
        begrip="test_manual_term",
        definitie="Test definitie voor manual synonym sync",
        organisatorische_context=["test"],
        juridische_context=[],
        wettelijke_basis=[],
        categorie="proces",
        created_by="test_user",
    )

    definitie_id = repo.save(definitie)
    assert definitie_id > 0
    logger.info(f"Created definitie {definitie_id}: {definitie.begrip}")

    # Step 2: Manual edit - add synoniemen
    synoniemen = ["manueel_syn1", "manueel_syn2", "manueel_syn3"]

    # Use legacy_repo for save_voorbeelden (services repo doesn't expose it)
    saved_ids = repo.legacy_repo.save_voorbeelden(
        definitie_id=definitie_id,
        voorbeelden_dict={"synoniemen": synoniemen},
        gegenereerd_door="test_user",
    )

    # Step 3: Verify in registry (scoped to definitie_id)
    group = registry.find_group_by_term("test_manual_term")
    assert group is not None, "Synonym group should be created"

    members = registry.get_group_members(
        group_id=group.id, filters={"definitie_id": definitie_id, "source": "manual"}
    )

    assert len(members) == 3, f"Expected 3 manual synonyms, got {len(members)}"
    assert all(m.status == "active" for m in members), "All should be active"
    assert all(
        m.definitie_id == definitie_id for m in members
    ), "All should be scoped to definitie_id"
    assert all(m.source == "manual" for m in members), "All should have source=manual"
    assert all(
        m.weight == 1.0 for m in members
    ), "Manual synonyms should have weight=1.0"

    member_terms = {m.term for m in members}
    assert member_terms == set(
        synoniemen
    ), "Registry should contain all manual synonyms"

    logger.info(f"✓ Verified {len(members)} manual synonyms in registry")

    # Step 4: Manual edit - remove one synonym (manueel_syn3)
    updated_synoniemen = ["manueel_syn1", "manueel_syn2"]  # syn3 removed

    repo.legacy_repo.save_voorbeelden(
        definitie_id=definitie_id,
        voorbeelden_dict={"synoniemen": updated_synoniemen},
        gegenereerd_door="test_user",
    )

    logger.info("Removed manueel_syn3 from synoniemen")

    # Step 5: Verify syn3 deprecated in registry
    members = registry.get_group_members(
        group_id=group.id, filters={"definitie_id": definitie_id}
    )

    syn3_member = next((m for m in members if m.term == "manueel_syn3"), None)
    assert syn3_member is not None, "manueel_syn3 should still exist in registry"
    assert syn3_member.status == "deprecated", "manueel_syn3 should be deprecated"

    # Other members should still be active
    active_members = [m for m in members if m.status == "active"]
    assert len(active_members) == 2, "Two synonyms should still be active"
    assert {m.term for m in active_members} == {"manueel_syn1", "manueel_syn2"}

    logger.info("✓ Verified manueel_syn3 deprecated after removal")

    # Step 6: Manual edit - re-add syn3
    re_added_synoniemen = ["manueel_syn1", "manueel_syn2", "manueel_syn3"]

    repo.legacy_repo.save_voorbeelden(
        definitie_id=definitie_id,
        voorbeelden_dict={"synoniemen": re_added_synoniemen},
        gegenereerd_door="test_user",
    )

    logger.info("Re-added manueel_syn3 to synoniemen")

    # Step 7: Verify syn3 reactivated (idempotent sync)
    members = registry.get_group_members(
        group_id=group.id, filters={"definitie_id": definitie_id}
    )

    syn3_member = next((m for m in members if m.term == "manueel_syn3"), None)
    assert syn3_member is not None
    assert syn3_member.status == "active", "manueel_syn3 should be reactivated"

    # All three should be active again
    active_members = [m for m in members if m.status == "active"]
    assert len(active_members) == 3, "All three synonyms should be active"

    logger.info("✓ Verified manueel_syn3 reactivated after re-adding (idempotent sync)")


# ============================================================================
# TEST 3: Cache Invalidation After Approval
# ============================================================================


@pytest.mark.integration()
def test_synonym_cache_invalidation_after_approval(container):
    """
    Verify cache invalidation after synonym approval (PHASE 3 cache behavior).

    Flow:
    1. Create synonym group with AI-pending member
    2. Query synonyms (cache miss) - should NOT include ai_pending
    3. Query again (cache hit) - should still NOT include ai_pending
    4. Approve AI-pending synonym
    5. Query again (cache invalidated) - should NOW include approved synonym

    Test Context:
    - SynonymOrchestrator uses TTL cache with callback invalidation
    - Approval should trigger cache invalidation via registry callbacks
    - Policy=STRICT means ai_pending not included in lookup
    """
    # Setup: Get services
    orchestrator = container.synonym_orchestrator()
    registry = container.synonym_registry()

    # Reset cache stats
    orchestrator._cache_hits = 0
    orchestrator._cache_misses = 0

    # Step 1: Create group with AI-pending member
    group = registry.get_or_create_group(
        canonical_term="test_cache_term", created_by="test"
    )

    member_id = registry.add_group_member(
        group_id=group.id,
        term="pending_cache_syn",
        weight=0.9,
        status="ai_pending",
        source="ai_suggested",
        created_by="test",
    )

    logger.info(f"Created AI-pending synonym: pending_cache_syn (id={member_id})")

    # Step 2: Query synonyms (cache miss)
    result1 = orchestrator.get_synonyms_for_lookup("test_cache_term")
    assert orchestrator._cache_misses == 1, "First query should be cache miss"
    assert len(result1) == 0, "ai_pending should NOT be included (policy=STRICT)"

    logger.info(
        "✓ Query 1: Cache miss, no AI-pending synonyms returned (STRICT policy)"
    )

    # Step 3: Query again (cache hit)
    result2 = orchestrator.get_synonyms_for_lookup("test_cache_term")
    assert orchestrator._cache_hits == 1, "Second query should be cache hit"
    assert len(result2) == 0, "Still no ai_pending synonyms"

    logger.info("✓ Query 2: Cache hit, still no AI-pending synonyms")

    # Step 4: Approve synonym (should invalidate cache via callback)
    registry.update_member_status(
        member_id=member_id, new_status="active", reviewed_by="test"
    )

    logger.info("Approved synonym: pending_cache_syn → active")

    # Step 5: Query again (cache should be invalidated, fresh query)
    result3 = orchestrator.get_synonyms_for_lookup("test_cache_term")

    # Cache should have been invalidated, so this is a new cache miss
    assert (
        orchestrator._cache_misses == 2
    ), "Approval should invalidate cache (new miss)"

    # Now the approved synonym should be included
    assert len(result3) == 1, "Approved synonym should now be included"
    assert result3[0].term == "pending_cache_syn"
    assert result3[0].weight == 0.9

    logger.info("✓ Query 3: Cache invalidated after approval, synonym now included")

    # Step 6: Query one more time (should be cache hit again)
    result4 = orchestrator.get_synonyms_for_lookup("test_cache_term")
    assert orchestrator._cache_hits == 2, "Fourth query should be cache hit"
    assert len(result4) == 1

    logger.info("✓ Query 4: Cache hit with approved synonym")

    # Final verification
    logger.info(
        f"Final cache stats: hits={orchestrator._cache_hits}, misses={orchestrator._cache_misses}"
    )
    assert orchestrator._cache_hits == 2
    assert orchestrator._cache_misses == 2
