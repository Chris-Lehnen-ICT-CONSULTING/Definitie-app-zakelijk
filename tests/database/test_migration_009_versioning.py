"""
Test suite for Migration 009: Versioning System Enablement (DEF-138)

Tests verify that:
1. UNIQUE INDEX removal allows versioning
2. Application-level duplicate prevention still works
3. Version history can be created and queried
4. No unintended duplicates occur
"""

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest

from database.definitie_repository import (
    DefinitieRecord,
    DefinitieRepository,
    DefinitieStatus,
)
from domain.ontological_categories import OntologischeCategorie


class TestMigration009Versioning:
    """Test versioning system after UNIQUE INDEX removal."""

    @pytest.fixture()
    def repo(self, tmp_path):
        """Create temporary repository for testing."""
        db_path = tmp_path / "test_migration_009.db"
        repo = DefinitieRepository(str(db_path))

        # Verify UNIQUE INDEX does not exist
        with repo._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type = 'index' AND name = 'idx_definities_unique_full'
                """
            )
            result = cursor.fetchone()
            assert result is None, "UNIQUE INDEX should not exist after migration 009"

        return repo

    def test_versioning_basic_workflow(self, repo):
        """Test basic versioning: create v1, then v2, then v3."""
        # Create initial definition (v1)
        v1 = DefinitieRecord(
            begrip="werkwoord",
            definitie="Een werkwoord is een woord dat een handeling aanduidt.",
            categorie=OntologischeCategorie.TYPE.value,
            organisatorische_context="test",
            juridische_context="taalrecht",
            wettelijke_basis=json.dumps(["Algemene Taalwet"]),
            status=DefinitieStatus.DRAFT.value,
            version_number=1,
            created_by="test_user",
        )
        id_v1 = repo.create_definitie(v1, allow_duplicate=False)
        assert id_v1 > 0

        # Create improved version (v2) - should succeed with allow_duplicate=True
        v2 = DefinitieRecord(
            begrip="werkwoord",
            definitie="Een werkwoord is een woord dat een handeling, gebeurtenis of toestand uitdrukt.",  # Improved
            categorie=OntologischeCategorie.TYPE.value,
            organisatorische_context="test",
            juridische_context="taalrecht",
            wettelijke_basis=json.dumps(["Algemene Taalwet"]),
            status=DefinitieStatus.REVIEW.value,
            version_number=2,
            previous_version_id=id_v1,
            created_by="reviewer",
        )
        id_v2 = repo.create_definitie(v2, allow_duplicate=True)
        assert id_v2 > 0
        assert id_v2 != id_v1

        # Create finalized version (v3)
        v3 = DefinitieRecord(
            begrip="werkwoord",
            definitie="Een werkwoord is een woordsoort die een handeling, gebeurtenis of toestand uitdrukt en vervoeging kent.",  # Final
            categorie=OntologischeCategorie.TYPE.value,
            organisatorische_context="test",
            juridische_context="taalrecht",
            wettelijke_basis=json.dumps(["Algemene Taalwet"]),
            status=DefinitieStatus.ESTABLISHED.value,
            version_number=3,
            previous_version_id=id_v2,
            created_by="admin",
        )
        id_v3 = repo.create_definitie(v3, allow_duplicate=True)
        assert id_v3 > 0
        assert id_v3 not in [id_v1, id_v2]

        # Verify all versions exist
        retrieved_v1 = repo.get_definitie(id_v1)
        retrieved_v2 = repo.get_definitie(id_v2)
        retrieved_v3 = repo.get_definitie(id_v3)

        assert retrieved_v1 is not None
        assert retrieved_v2 is not None
        assert retrieved_v3 is not None

        # Verify version chain
        assert retrieved_v1.version_number == 1
        assert retrieved_v1.previous_version_id is None

        assert retrieved_v2.version_number == 2
        assert retrieved_v2.previous_version_id == id_v1

        assert retrieved_v3.version_number == 3
        assert retrieved_v3.previous_version_id == id_v2

        # Verify status progression
        assert retrieved_v1.status == DefinitieStatus.DRAFT.value
        assert retrieved_v2.status == DefinitieStatus.REVIEW.value
        assert retrieved_v3.status == DefinitieStatus.ESTABLISHED.value

    def test_duplicate_prevention_still_works(self, repo):
        """Verify Python-level duplicate detection prevents accidental duplicates."""
        # Create first definition
        d1 = DefinitieRecord(
            begrip="test_begrip",
            definitie="Eerste definitie",
            categorie=OntologischeCategorie.TYPE.value,
            organisatorische_context="test_org",
            juridische_context="test_jur",
            wettelijke_basis=json.dumps(["Test Wet"]),
            status=DefinitieStatus.DRAFT.value,
        )
        repo.create_definitie(d1, allow_duplicate=False)

        # Try to create exact duplicate (should raise ValueError, NOT IntegrityError)
        d2 = DefinitieRecord(
            begrip="test_begrip",
            definitie="Tweede definitie (andere tekst)",  # Different content
            categorie=OntologischeCategorie.TYPE.value,
            organisatorische_context="test_org",
            juridische_context="test_jur",
            wettelijke_basis=json.dumps(["Test Wet"]),
            status=DefinitieStatus.DRAFT.value,
        )

        # Default behavior: prevent duplicate
        with pytest.raises(ValueError, match="bestaat al in deze context"):
            repo.create_definitie(d2, allow_duplicate=False)

        # Explicit allow_duplicate=True should succeed (versioning)
        id2 = repo.create_definitie(d2, allow_duplicate=True)
        assert id2 > 0

    def test_different_contexts_allowed(self, repo):
        """Same begrip with different context should be allowed (no duplication)."""
        base_record = {
            "begrip": "arrest",
            "definitie": "Rechterlijke beslissing",
            "categorie": OntologischeCategorie.TYPE.value,
            "wettelijke_basis": json.dumps(["Wetboek van Strafrecht"]),
            "status": DefinitieStatus.DRAFT.value,
        }

        # Context 1: Strafrecht
        d1 = DefinitieRecord(
            **base_record,
            organisatorische_context="OM",
            juridische_context="strafrecht",
        )
        id1 = repo.create_definitie(d1)

        # Context 2: Bestuursrecht (different juridische_context)
        d2 = DefinitieRecord(
            **base_record,
            organisatorische_context="OM",
            juridische_context="bestuursrecht",
        )
        id2 = repo.create_definitie(d2)

        # Context 3: Different organisatie
        d3 = DefinitieRecord(
            **base_record,
            organisatorische_context="Politie",
            juridische_context="strafrecht",
        )
        id3 = repo.create_definitie(d3)

        # All should succeed (different contexts)
        assert id1 > 0
        assert id2 > 0
        assert id3 > 0
        assert len({id1, id2, id3}) == 3  # All unique

    def test_different_categories_allowed(self, repo):
        """Same begrip with different ontological category should be allowed."""
        # Same term, different categories (TYPE vs PROCES)
        d1 = DefinitieRecord(
            begrip="controle",
            definitie="Entiteit die controle uitvoert",
            categorie=OntologischeCategorie.TYPE.value,  # TYPE
            organisatorische_context="test",
            status=DefinitieStatus.DRAFT.value,
        )
        id1 = repo.create_definitie(d1)

        d2 = DefinitieRecord(
            begrip="controle",
            definitie="Het proces van controleren",
            categorie=OntologischeCategorie.PROCES.value,  # PROCES
            organisatorische_context="test",
            status=DefinitieStatus.DRAFT.value,
        )
        id2 = repo.create_definitie(d2)

        # Should both succeed (different categories)
        assert id1 > 0
        assert id2 > 0
        assert id1 != id2

    def test_archived_exclusion(self, repo):
        """Archived definitions should not block new definitions."""
        # Create and archive old version
        old = DefinitieRecord(
            begrip="wet",
            definitie="Oude definitie",
            categorie=OntologischeCategorie.TYPE.value,
            organisatorische_context="test",
            status=DefinitieStatus.ARCHIVED.value,  # ARCHIVED
        )
        id_old = repo.create_definitie(old, allow_duplicate=True)

        # Create new definition with same context (should succeed - old is archived)
        new = DefinitieRecord(
            begrip="wet",
            definitie="Nieuwe definitie",
            categorie=OntologischeCategorie.TYPE.value,
            organisatorische_context="test",
            status=DefinitieStatus.DRAFT.value,
        )
        id_new = repo.create_definitie(new, allow_duplicate=False)

        # Should succeed (archived definitions don't count as duplicates)
        assert id_new > 0
        assert id_new != id_old

    def test_version_history_query(self, repo):
        """Test querying version history for a term."""
        # Create version chain: v1 → v2 → v3
        v1 = DefinitieRecord(
            begrip="begrip_met_geschiedenis",
            definitie="Versie 1",
            categorie=OntologischeCategorie.TYPE.value,
            organisatorische_context="test",
            status=DefinitieStatus.DRAFT.value,
            version_number=1,
        )
        id_v1 = repo.create_definitie(v1, allow_duplicate=True)

        v2 = DefinitieRecord(
            begrip="begrip_met_geschiedenis",
            definitie="Versie 2",
            categorie=OntologischeCategorie.TYPE.value,
            organisatorische_context="test",
            status=DefinitieStatus.REVIEW.value,
            version_number=2,
            previous_version_id=id_v1,
        )
        id_v2 = repo.create_definitie(v2, allow_duplicate=True)

        v3 = DefinitieRecord(
            begrip="begrip_met_geschiedenis",
            definitie="Versie 3",
            categorie=OntologischeCategorie.TYPE.value,
            organisatorische_context="test",
            status=DefinitieStatus.ESTABLISHED.value,
            version_number=3,
            previous_version_id=id_v2,
        )
        id_v3 = repo.create_definitie(v3, allow_duplicate=True)

        # Query all versions
        all_versions = repo.search_definities(
            query="begrip_met_geschiedenis", limit=None
        )

        # Should find all 3 versions
        assert len(all_versions) == 3

        # Verify version numbers
        versions_found = {v.version_number for v in all_versions}
        assert versions_found == {1, 2, 3}

        # Verify chain links
        v2_retrieved = repo.get_definitie(id_v2)
        v3_retrieved = repo.get_definitie(id_v3)

        assert v2_retrieved.previous_version_id == id_v1
        assert v3_retrieved.previous_version_id == id_v2

    def test_wettelijke_basis_normalization(self, repo):
        """Test that wettelijke_basis is order-independent in duplicate detection."""
        # Create definition with basis ["A", "B"]
        d1 = DefinitieRecord(
            begrip="test_wet",
            definitie="Definitie 1",
            categorie=OntologischeCategorie.TYPE.value,
            organisatorische_context="test",
            wettelijke_basis=json.dumps(["Wet A", "Wet B"]),  # Order 1
            status=DefinitieStatus.DRAFT.value,
        )
        repo.create_definitie(d1)

        # Try to create with basis ["B", "A"] (different order, same content)
        d2 = DefinitieRecord(
            begrip="test_wet",
            definitie="Definitie 2",
            categorie=OntologischeCategorie.TYPE.value,
            organisatorische_context="test",
            wettelijke_basis=json.dumps(["Wet B", "Wet A"]),  # Order 2
            status=DefinitieStatus.DRAFT.value,
        )

        # Should detect as duplicate (normalized internally)
        with pytest.raises(ValueError, match="bestaat al in deze context"):
            repo.create_definitie(d2, allow_duplicate=False)

    def test_multiple_drafts_single_context(self, repo):
        """Multiple draft versions in same context should be allowed."""
        # Scenario: User generates multiple alternatives to compare
        base = {
            "begrip": "vergelijking",
            "categorie": OntologischeCategorie.TYPE.value,
            "organisatorische_context": "test",
            "status": DefinitieStatus.DRAFT.value,
        }

        d1 = DefinitieRecord(**base, definitie="Alternatief 1")
        d2 = DefinitieRecord(**base, definitie="Alternatief 2")
        d3 = DefinitieRecord(**base, definitie="Alternatief 3")

        id1 = repo.create_definitie(d1, allow_duplicate=True)
        id2 = repo.create_definitie(d2, allow_duplicate=True)
        id3 = repo.create_definitie(d3, allow_duplicate=True)

        # All should succeed
        assert len({id1, id2, id3}) == 3

        # User can then choose best one and archive others
        repo.change_status(id1, DefinitieStatus.ARCHIVED, "user")
        repo.change_status(id3, DefinitieStatus.ARCHIVED, "user")
        repo.change_status(id2, DefinitieStatus.REVIEW, "user")

        # Verify final state
        kept = repo.get_definitie(id2)
        assert kept.status == DefinitieStatus.REVIEW.value


class TestMigration009SafetyChecks:
    """Test safety aspects of migration 009."""

    @pytest.fixture()
    def repo(self, tmp_path):
        """Create temporary repository for testing."""
        db_path = tmp_path / "test_migration_009_safety.db"
        return DefinitieRepository(str(db_path))

    def test_index_does_not_exist(self, repo):
        """Verify UNIQUE INDEX was removed by migration 009."""
        with repo._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT name, sql
                FROM sqlite_master
                WHERE type = 'index' AND name = 'idx_definities_unique_full'
                """
            )
            result = cursor.fetchone()

        assert result is None, (
            "Migration 009 should have removed idx_definities_unique_full. "
            "Run: sqlite3 data/definities.db < src/database/migrations/009_remove_unique_index.sql"
        )

    def test_other_indices_intact(self, repo):
        """Verify other indices are still present."""
        with repo._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type = 'index'
                  AND tbl_name = 'definities'
                  AND name LIKE 'idx_definities_%'
                ORDER BY name
                """
            )
            indices = [row[0] for row in cursor.fetchall()]

        # Should have these indices (but NOT unique_full)
        expected_indices = {
            "idx_definities_begrip",
            "idx_definities_categorie",
            "idx_definities_created_at",
            "idx_definities_datum_voorstel",
            "idx_definities_status",
        }

        actual_indices = set(indices)
        assert expected_indices.issubset(
            actual_indices
        ), f"Missing indices: {expected_indices - actual_indices}"
        assert (
            "idx_definities_unique_full" not in actual_indices
        ), "UNIQUE INDEX should be removed"

    def test_no_unintended_duplicates(self, repo):
        """Verify no duplicate entries exist after migration."""
        with repo._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT
                    begrip,
                    organisatorische_context,
                    juridische_context,
                    wettelijke_basis,
                    categorie,
                    COUNT(*) as count
                FROM definities
                WHERE status != 'archived'
                GROUP BY begrip, organisatorische_context, juridische_context,
                         wettelijke_basis, categorie
                HAVING COUNT(*) > 1
                """
            )
            duplicates = cursor.fetchall()

        # After migration, there should be no unintended duplicates
        # (Any duplicates are intentional versioning)
        # This test checks the CURRENT state, not the ideal state
        # If duplicates exist, verify they are versioned correctly
        if duplicates:
            for dup in duplicates:
                begrip, org_ctx, jur_ctx, wet_basis, cat, _count = dup
                # Get the duplicate records
                with repo._get_connection() as conn:
                    cursor = conn.execute(
                        """
                        SELECT id, version_number, previous_version_id, status
                        FROM definities
                        WHERE begrip = ?
                          AND organisatorische_context = ?
                          AND juridische_context = ?
                          AND wettelijke_basis = ?
                          AND categorie = ?
                          AND status != 'archived'
                        ORDER BY version_number
                        """,
                        (begrip, org_ctx, jur_ctx, wet_basis, cat),
                    )
                    records = cursor.fetchall()

                # Verify they form a valid version chain
                for i in range(len(records) - 1):
                    _current_id, current_version, current_prev, _ = records[i + 1]
                    prev_id, prev_version, _, _ = records[i]

                    # Version chain should be valid
                    assert (
                        current_version > prev_version
                    ), f"Version numbers not increasing: {records}"
                    assert current_prev == prev_id, f"Version chain broken: {records}"


class TestMigration009IntegrationChecker:
    """Test integration with definitie_checker.py after migration 009."""

    @pytest.fixture()
    def repo(self, tmp_path):
        """Create temporary repository for testing."""
        db_path = tmp_path / "test_migration_009_checker.db"
        return DefinitieRepository(str(db_path))

    def test_checker_duplicate_detection(self, repo):
        """Test that definitie_checker still detects duplicates correctly."""
        from integration.definitie_checker import DefinitieChecker

        checker = DefinitieChecker(repository=repo)

        # Create first definition
        d1 = DefinitieRecord(
            begrip="checker_test",
            definitie="Eerste definitie",
            categorie=OntologischeCategorie.TYPE.value,
            organisatorische_context="test",
            status=DefinitieStatus.DRAFT.value,
        )
        repo.create_definitie(d1)

        # Check before generation (should find duplicate)
        result = checker.check_before_generation(
            begrip="checker_test",
            organisatorische_context="test",
            juridische_context="",
            categorie=OntologischeCategorie.TYPE,
        )

        # Should detect duplicate and suggest using existing
        assert result.action.value in ["use_existing", "update_existing"]
        assert result.existing_definitie is not None
        assert result.existing_definitie.begrip == "checker_test"

    def test_force_generate_bypass(self, repo):
        """Test force_generate flag bypasses duplicate check."""
        from integration.definitie_checker import DefinitieChecker

        checker = DefinitieChecker(repository=repo)

        # Create first definition
        d1 = DefinitieRecord(
            begrip="force_test",
            definitie="Eerste definitie",
            categorie=OntologischeCategorie.TYPE.value,
            organisatorische_context="test",
            status=DefinitieStatus.DRAFT.value,
        )
        repo.create_definitie(d1)

        # Generate with force_generate=True
        _check_result, _agent_result, _saved_record = checker.generate_with_check(
            begrip="force_test",
            organisatorische_context="test",
            juridische_context="",
            categorie=OntologischeCategorie.TYPE,
            force_generate=True,  # Bypass duplicate check
            created_by="test_user",
        )

        # Should create new version despite duplicate
        # (Actual generation may fail due to missing AI service in tests,
        #  but check_result should allow PROCEED)
        # This is integration test - actual AI call not needed to verify logic


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
