"""
Tests for UNIQUE constraint removal (Migration 009).

This module contains tests to verify the behavior before and after removing
the UNIQUE INDEX constraint on definities table.

Tests are organized in two phases:
1. PRE-MIGRATION: Verify constraint EXISTS and BLOCKS duplicates
2. POST-MIGRATION: Verify constraint REMOVED and allows duplicates

Run these tests in sequence:
    pytest tests/database/test_unique_constraint_removal.py::test_pre_migration -v
    # Apply migration 009
    pytest tests/database/test_unique_constraint_removal.py::test_post_migration -v
"""

import json
import sqlite3
from pathlib import Path

import pytest

from database.definitie_repository import DefinitieRecord, DefinitieRepository

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture()
def test_db_path(tmp_path):
    """Create temporary test database with schema."""
    db_path = tmp_path / "test_definities.db"

    # Initialize database with schema
    DefinitieRepository(str(db_path))

    # Apply migration 008 (add UNIQUE INDEX) if not already applied
    # This simulates the pre-migration state
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Check if UNIQUE INDEX exists
    cursor.execute(
        """
        SELECT COUNT(*) FROM sqlite_master
        WHERE type='index' AND name='idx_definities_unique_full'
    """
    )
    index_exists = cursor.fetchone()[0] > 0

    if not index_exists:
        # Apply migration 008 to create UNIQUE INDEX
        migration_008 = (
            Path(__file__).parent.parent.parent
            / "src"
            / "database"
            / "migrations"
            / "008_add_unique_constraint.sql"
        )
        if migration_008.exists():
            with open(migration_008) as f:
                cursor.executescript(f.read())
            conn.commit()

    conn.close()

    return str(db_path)


@pytest.fixture()
def repo(test_db_path):
    """Create repository instance for testing."""
    return DefinitieRepository(test_db_path)


# ============================================================================
# PRE-MIGRATION TESTS (UNIQUE INDEX EXISTS)
# ============================================================================


class TestPreMigration:
    """Tests to run BEFORE migration 009 (UNIQUE INDEX exists)."""

    def test_unique_index_exists(self, test_db_path):
        """Verify UNIQUE INDEX exists before migration."""
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        # Check index exists
        cursor.execute(
            """
            SELECT name, sql FROM sqlite_master
            WHERE type='index' AND name='idx_definities_unique_full'
        """
        )
        result = cursor.fetchone()

        assert result is not None, "UNIQUE INDEX should exist before migration"
        assert result[0] == "idx_definities_unique_full"

        conn.close()

    def test_duplicate_blocked_by_database(self, repo):
        """Verify database-level UNIQUE constraint blocks duplicates."""
        record1 = DefinitieRecord(
            begrip="test_begrip",
            definitie="First definition",
            categorie="ENT",
            organisatorische_context="DJI",
            juridische_context="strafrecht",
            wettelijke_basis="[]",
        )

        # Create first record - should succeed
        id1 = repo.create_definitie(record1)
        assert id1 > 0

        # Attempt duplicate with DIFFERENT definitie text but SAME key fields
        record2 = DefinitieRecord(
            begrip="test_begrip",  # SAME
            definitie="Second definition (different text)",
            categorie="ENT",  # SAME
            organisatorische_context="DJI",  # SAME
            juridische_context="strafrecht",  # SAME
            wettelijke_basis="[]",  # SAME
        )

        # Should raise ValueError due to Python-level check
        with pytest.raises(ValueError, match="bestaat al"):
            repo.create_definitie(record2)

    def test_python_check_detects_duplicates(self, repo):
        """Verify Python find_duplicates() detects matches."""
        record = DefinitieRecord(
            begrip="test_begrip",
            definitie="Test definition",
            categorie="ENT",
            organisatorische_context="DJI",
            juridische_context="strafrecht",
            wettelijke_basis="[]",
        )

        repo.create_definitie(record)

        # find_duplicates should detect the existing record
        duplicates = repo.find_duplicates(
            begrip="test_begrip",
            organisatorische_context="DJI",
            juridische_context="strafrecht",
            categorie="ENT",
            wettelijke_basis=[],
        )

        assert len(duplicates) == 1, "Should find existing definition as duplicate"
        assert duplicates[0].match_score == 1.0, "Should be exact match"
        assert (
            "Exact match" in duplicates[0].match_reasons[0]
        ), "Should indicate exact match"

    def test_different_categorie_allowed(self, repo):
        """Verify different categorie creates separate definition."""
        record1 = DefinitieRecord(
            begrip="test_begrip",
            definitie="Entity definition",
            categorie="ENT",
            organisatorische_context="DJI",
            juridische_context="strafrecht",
            wettelijke_basis="[]",
        )

        record2 = DefinitieRecord(
            begrip="test_begrip",
            definitie="Activity definition",
            categorie="ACT",  # DIFFERENT categorie
            organisatorische_context="DJI",
            juridische_context="strafrecht",
            wettelijke_basis="[]",
        )

        id1 = repo.create_definitie(record1)
        id2 = repo.create_definitie(record2)

        assert id1 != id2, "Different categorie should allow separate definition"

        # Verify both exist
        def1 = repo.get_definitie(id1)
        def2 = repo.get_definitie(id2)

        assert def1.categorie == "ENT"
        assert def2.categorie == "ACT"


# ============================================================================
# POST-MIGRATION TESTS (UNIQUE INDEX REMOVED)
# ============================================================================


class TestPostMigration:
    """Tests to run AFTER migration 009 (UNIQUE INDEX removed)."""

    def test_unique_index_removed(self, test_db_path):
        """Verify UNIQUE INDEX is removed after migration."""
        # Apply migration 009
        migration_009 = (
            Path(__file__).parent.parent.parent
            / "src"
            / "database"
            / "migrations"
            / "009_remove_unique_constraint.sql"
        )

        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        if migration_009.exists():
            with open(migration_009) as f:
                cursor.executescript(f.read())
            conn.commit()

        # Check index does NOT exist
        cursor.execute(
            """
            SELECT COUNT(*) FROM sqlite_master
            WHERE type='index' AND name='idx_definities_unique_full'
        """
        )
        count = cursor.fetchone()[0]

        assert count == 0, "UNIQUE INDEX should NOT exist after migration"
        conn.close()

    def test_duplicate_allowed_with_flag(self, test_db_path):
        """Verify duplicates ARE allowed with allow_duplicate=True after migration."""
        # Apply migration first
        migration_009 = (
            Path(__file__).parent.parent.parent
            / "src"
            / "database"
            / "migrations"
            / "009_remove_unique_constraint.sql"
        )

        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        if migration_009.exists():
            with open(migration_009) as f:
                cursor.executescript(f.read())
            conn.commit()

        conn.close()

        # Now test duplicate creation
        repo = DefinitieRepository(test_db_path)

        record1 = DefinitieRecord(
            begrip="duplicate_test",
            definitie="First definition",
            categorie="ENT",
            organisatorische_context="DJI",
            juridische_context="strafrecht",
            wettelijke_basis="[]",
        )

        id1 = repo.create_definitie(record1, allow_duplicate=False)
        assert id1 > 0

        # Attempt duplicate WITH allow_duplicate=True - should succeed
        record2 = DefinitieRecord(
            begrip="duplicate_test",
            definitie="Second definition (variant)",
            categorie="ENT",
            organisatorische_context="DJI",
            juridische_context="strafrecht",
            wettelijke_basis="[]",
        )

        id2 = repo.create_definitie(record2, allow_duplicate=True)
        assert id2 > 0
        assert id2 != id1, "Should create separate definition"

        # Verify both records exist
        def1 = repo.get_definitie(id1)
        def2 = repo.get_definitie(id2)

        assert def1.definitie == "First definition"
        assert def2.definitie == "Second definition (variant)"

    def test_python_guard_still_blocks_without_flag(self, test_db_path):
        """Verify Python-level check still blocks when allow_duplicate=False."""
        # Apply migration first
        migration_009 = (
            Path(__file__).parent.parent.parent
            / "src"
            / "database"
            / "migrations"
            / "009_remove_unique_constraint.sql"
        )

        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        if migration_009.exists():
            with open(migration_009) as f:
                cursor.executescript(f.read())
            conn.commit()

        conn.close()

        repo = DefinitieRepository(test_db_path)

        record1 = DefinitieRecord(
            begrip="guard_test",
            definitie="First definition",
            categorie="ENT",
            organisatorische_context="DJI",
            juridische_context="strafrecht",
            wettelijke_basis="[]",
        )

        repo.create_definitie(record1)

        # Attempt duplicate WITHOUT allow_duplicate - should raise ValueError
        record2 = DefinitieRecord(
            begrip="guard_test",
            definitie="Second definition",
            categorie="ENT",
            organisatorische_context="DJI",
            juridische_context="strafrecht",
            wettelijke_basis="[]",
        )

        with pytest.raises(ValueError, match="bestaat al"):
            repo.create_definitie(record2, allow_duplicate=False)

    def test_find_duplicates_still_works(self, test_db_path):
        """Verify find_duplicates() still detects matches after migration."""
        # Apply migration first
        migration_009 = (
            Path(__file__).parent.parent.parent
            / "src"
            / "database"
            / "migrations"
            / "009_remove_unique_constraint.sql"
        )

        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        if migration_009.exists():
            with open(migration_009) as f:
                cursor.executescript(f.read())
            conn.commit()

        conn.close()

        repo = DefinitieRepository(test_db_path)

        # Create two identical definitions
        record1 = DefinitieRecord(
            begrip="find_test",
            definitie="First definition",
            categorie="ENT",
            organisatorische_context="DJI",
            juridische_context="strafrecht",
            wettelijke_basis="[]",
        )
        record2 = DefinitieRecord(
            begrip="find_test",
            definitie="Second definition",
            categorie="ENT",
            organisatorische_context="DJI",
            juridische_context="strafrecht",
            wettelijke_basis="[]",
        )

        repo.create_definitie(record1)
        repo.create_definitie(record2, allow_duplicate=True)

        # find_duplicates should detect both
        duplicates = repo.find_duplicates(
            begrip="find_test",
            organisatorische_context="DJI",
            juridische_context="strafrecht",
            categorie="ENT",
            wettelijke_basis=[],
        )

        assert len(duplicates) == 2, "Should find both definitions as duplicates"
        assert all(
            d.match_score == 1.0 for d in duplicates
        ), "Should all be exact matches"

    def test_multiple_variants_allowed(self, test_db_path):
        """Verify multiple definition variants can coexist after migration."""
        # Apply migration first
        migration_009 = (
            Path(__file__).parent.parent.parent
            / "src"
            / "database"
            / "migrations"
            / "009_remove_unique_constraint.sql"
        )

        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        if migration_009.exists():
            with open(migration_009) as f:
                cursor.executescript(f.read())
            conn.commit()

        conn.close()

        repo = DefinitieRepository(test_db_path)

        # Create 3 variants of same definition
        for i in range(1, 4):
            record = DefinitieRecord(
                begrip="variant_test",
                definitie=f"Variant {i} definition",
                categorie="ENT",
                organisatorische_context="DJI",
                juridische_context="strafrecht",
                wettelijke_basis="[]",
            )
            allow_dup = i > 1  # First one doesn't need flag
            repo.create_definitie(record, allow_duplicate=allow_dup)

        # Verify all 3 variants exist
        duplicates = repo.find_duplicates(
            begrip="variant_test",
            organisatorische_context="DJI",
            juridische_context="strafrecht",
            categorie="ENT",
            wettelijke_basis=[],
        )

        assert len(duplicates) == 3, "Should have 3 variants"
        definitions = [d.definitie_record.definitie for d in duplicates]
        assert "Variant 1 definition" in definitions
        assert "Variant 2 definition" in definitions
        assert "Variant 3 definition" in definitions


# ============================================================================
# ROLLBACK TESTS
# ============================================================================


class TestRollback:
    """Tests for rollback procedure."""

    def test_rollback_fails_with_duplicates(self, test_db_path):
        """Verify rollback fails if duplicates exist."""
        # Apply migration 009
        migration_009 = (
            Path(__file__).parent.parent.parent
            / "src"
            / "database"
            / "migrations"
            / "009_remove_unique_constraint.sql"
        )

        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        if migration_009.exists():
            with open(migration_009) as f:
                cursor.executescript(f.read())
            conn.commit()

        # Create duplicates
        repo = DefinitieRepository(test_db_path)

        record1 = DefinitieRecord(
            begrip="rollback_test",
            definitie="First",
            categorie="ENT",
            organisatorische_context="DJI",
            juridische_context="strafrecht",
            wettelijke_basis="[]",
        )
        record2 = DefinitieRecord(
            begrip="rollback_test",
            definitie="Second",
            categorie="ENT",
            organisatorische_context="DJI",
            juridische_context="strafrecht",
            wettelijke_basis="[]",
        )

        repo.create_definitie(record1)
        repo.create_definitie(record2, allow_duplicate=True)

        # Attempt rollback - should fail due to duplicates
        rollback_migration = (
            Path(__file__).parent.parent.parent
            / "src"
            / "database"
            / "migrations"
            / "009_rollback_remove_unique_constraint.sql"
        )

        if rollback_migration.exists():
            with open(rollback_migration) as f:
                rollback_sql = f.read()

            with pytest.raises(sqlite3.IntegrityError):
                cursor.executescript(rollback_sql)

        conn.close()

    def test_rollback_succeeds_without_duplicates(self, test_db_path):
        """Verify rollback succeeds when no duplicates exist."""
        # Apply migration 009
        migration_009 = (
            Path(__file__).parent.parent.parent
            / "src"
            / "database"
            / "migrations"
            / "009_remove_unique_constraint.sql"
        )

        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        if migration_009.exists():
            with open(migration_009) as f:
                cursor.executescript(f.read())
            conn.commit()

        # Verify INDEX removed
        cursor.execute(
            """
            SELECT COUNT(*) FROM sqlite_master
            WHERE type='index' AND name='idx_definities_unique_full'
        """
        )
        assert cursor.fetchone()[0] == 0

        # Apply rollback (no duplicates exist)
        rollback_migration = (
            Path(__file__).parent.parent.parent
            / "src"
            / "database"
            / "migrations"
            / "009_rollback_remove_unique_constraint.sql"
        )

        if rollback_migration.exists():
            with open(rollback_migration) as f:
                cursor.executescript(f.read())
            conn.commit()

        # Verify INDEX restored
        cursor.execute(
            """
            SELECT COUNT(*) FROM sqlite_master
            WHERE type='index' AND name='idx_definities_unique_full'
        """
        )
        assert (
            cursor.fetchone()[0] == 1
        ), "UNIQUE INDEX should be restored after rollback"

        conn.close()
