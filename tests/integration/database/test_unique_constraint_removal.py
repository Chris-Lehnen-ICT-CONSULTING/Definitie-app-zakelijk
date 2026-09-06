"""
Tests for UNIQUE constraint removal (Migration 009).

This module contains tests to verify the behavior before and after removing
the UNIQUE INDEX constraint on definities table.

Tests are organized in two phases:
1. PRE-MIGRATION: Verify constraint EXISTS and BLOCKS duplicates
2. POST-MIGRATION: Verify constraint REMOVED and allows duplicates

NOTE (DEF-676, repaired under DEF-519): the fixture and the tests used to
resolve the migration SQL under `tests/src/database/migrations/`, a directory
that does not exist — the files live in `src/database/migrations/`. Because
every lookup was guarded by `if migration.exists()`, the migrations were
silently skipped: two index assertions failed and the rollback-with-duplicates
test asserted nothing at all. The lookup is now repo-root relative and a
missing migration raises instead of being skipped.

Run (integration marker, offline bootstrap active via tests/conftest.py):

    .venv/bin/python -m pytest \\
        tests/integration/database/test_unique_constraint_removal.py
"""

import json
import sqlite3
from pathlib import Path

import pytest

from database.definitie_repository import DefinitieRecord, DefinitieRepository

pytestmark = [pytest.mark.integration]

# ============================================================================
# MIGRATIE-INVOER
# ============================================================================

#: Migratiemap, repo-root-relatief. `resolve()` maakt de resolutie
#: onafhankelijk van de werkdirectory; `parents[3]` is de repository-root
#: (dit bestand ligt in tests/integration/database/).
MIGRATIONS_DIR = Path(__file__).resolve().parents[3] / "src" / "database" / "migrations"

MIGRATION_008 = "008_add_unique_constraint.sql"
MIGRATION_009 = "009_remove_unique_constraint.sql"
MIGRATION_009_ROLLBACK = "009_rollback_remove_unique_constraint.sql"

UNIQUE_INDEX = "idx_definities_unique_full"


def read_required_migration(name: str, *, directory: Path = MIGRATIONS_DIR) -> str:
    """Lees een verplichte migratie. Ontbreken is een fout, geen stille skip."""
    path = directory / name
    if not path.is_file():
        raise FileNotFoundError(
            f"Verplichte migratie ontbreekt: {path}. Deze suite toetst echte DDL; "
            "zonder dat bestand valt er niets te toetsen."
        )
    return path.read_text(encoding="utf-8")


def apply_migration(conn: sqlite3.Connection, name: str) -> None:
    """Voer een verplichte migratie uit op een open verbinding."""
    conn.executescript(read_required_migration(name))
    conn.commit()


def count_unique_index(conn: sqlite3.Connection) -> int:
    """Aantal sqlite_master-rijen voor de UNIQUE INDEX van migratie 008."""
    cursor = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name=?",
        (UNIQUE_INDEX,),
    )
    return cursor.fetchone()[0]


def insert_duplicate_bypassing_python_guard(
    db_path: str, definitie_id: int, nieuwe_tekst: str
) -> None:
    """Kopieer de sleutelvelden van een bestaande rij via ruwe SQL.

    Gaat bewust langs `DefinitieRepository` heen: alleen de SQL-laag mag over
    deze invoeging beslissen. Zonder deze route bewijst een `ValueError` uit
    de Python-guard niets over de UNIQUE INDEX zelf.
    """
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            INSERT INTO definities (
                begrip, definitie, categorie, organisatorische_context,
                juridische_context, wettelijke_basis, status
            )
            SELECT begrip, ?, categorie, organisatorische_context,
                   juridische_context, wettelijke_basis, status
            FROM definities WHERE id = ?
            """,
            (nieuwe_tekst, definitie_id),
        )
        conn.commit()
    finally:
        conn.close()


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def test_db_path(tmp_path):
    """Create temporary test database with schema."""
    db_path = tmp_path / "test_definities.db"

    # Initialize database with schema
    DefinitieRepository(str(db_path))

    # Apply migration 008 (add UNIQUE INDEX) to reach the pre-migration state.
    # De DDL is zelf idempotent (CREATE UNIQUE INDEX IF NOT EXISTS), dus een
    # voorafgaande bestaanscheck voegt niets toe en zou een ontbrekende index
    # opnieuw stil maken.
    conn = sqlite3.connect(str(db_path))
    try:
        apply_migration(conn, MIGRATION_008)
    finally:
        conn.close()

    return str(db_path)


@pytest.fixture
def repo(test_db_path):
    """Create repository instance for testing."""
    return DefinitieRepository(test_db_path)


# ============================================================================
# MIGRATIE-INVOER (verplicht, werkdirectory-onafhankelijk)
# ============================================================================


class TestMigrationInput:
    """De invoer van deze suite: de echte SQL-bestanden, hard vereist."""

    def test_missing_migration_raises(self, tmp_path):
        """Een ontbrekende migratie faalt hard i.p.v. stil overgeslagen te worden."""
        synthetic_dir = tmp_path / "map-die-niet-bestaat"
        assert not synthetic_dir.exists()

        with pytest.raises(FileNotFoundError, match="Verplichte migratie ontbreekt"):
            read_required_migration(MIGRATION_008, directory=synthetic_dir)

    def test_required_migrations_resolve_independent_of_cwd(
        self, tmp_path, monkeypatch
    ):
        """Alle drie de migraties laden ook vanuit een andere werkdirectory."""
        monkeypatch.chdir(tmp_path)

        for name in (MIGRATION_008, MIGRATION_009, MIGRATION_009_ROLLBACK):
            assert read_required_migration(name).strip(), f"{name} is leeg"

        assert f"CREATE UNIQUE INDEX IF NOT EXISTS {UNIQUE_INDEX}" in (
            read_required_migration(MIGRATION_008)
        )


# ============================================================================
# PRE-MIGRATION TESTS (UNIQUE INDEX EXISTS)
# ============================================================================


class TestPreMigration:
    """Tests to run BEFORE migration 009 (UNIQUE INDEX exists)."""

    def test_unique_index_exists(self, test_db_path):
        """Verify UNIQUE INDEX exists before migration."""
        conn = sqlite3.connect(test_db_path)
        try:
            cursor = conn.cursor()

            # Check index exists
            cursor.execute("""
                SELECT name, sql FROM sqlite_master
                WHERE type='index' AND name='idx_definities_unique_full'
            """)
            result = cursor.fetchone()

            assert result is not None, "UNIQUE INDEX should exist before migration"
            assert result[0] == "idx_definities_unique_full"
        finally:
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

    def test_duplicate_blocked_at_sql_layer(self, repo, test_db_path):
        """De UNIQUE INDEX zelf blokkeert, niet alleen de Python-guard.

        `test_duplicate_blocked_by_database` toont een `ValueError` uit de
        Python-guard; die zou ook slagen zonder index. Hier wordt de guard
        omzeild, zodat alleen SQLite nog kan tegenhouden.
        """
        record = DefinitieRecord(
            begrip="sql_layer_pre",
            definitie="First definition",
            categorie="ENT",
            organisatorische_context="DJI",
            juridische_context="strafrecht",
            wettelijke_basis="[]",
        )
        record_id = repo.create_definitie(record)

        with pytest.raises(sqlite3.IntegrityError, match="UNIQUE constraint failed"):
            insert_duplicate_bypassing_python_guard(
                test_db_path, record_id, "Bypass definition"
            )

        conn = sqlite3.connect(test_db_path)
        try:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM definities WHERE begrip = ?", ("sql_layer_pre",)
            )
            assert cursor.fetchone()[0] == 1, "Geweigerde rij mag niet zijn opgeslagen"
        finally:
            conn.close()

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
        conn = sqlite3.connect(test_db_path)
        try:
            # Uitgangspunt: de fixture heeft 008 echt toegepast
            assert count_unique_index(conn) == 1, "UNIQUE INDEX should exist before 009"

            # Apply migration 009
            apply_migration(conn, MIGRATION_009)

            # Check index does NOT exist
            count = count_unique_index(conn)

            assert count == 0, "UNIQUE INDEX should NOT exist after migration"
        finally:
            conn.close()

    def test_duplicate_accepted_at_sql_layer(self, test_db_path):
        """Na 009 laat de SQL-laag het duplicaat door, ook zonder Python-guard."""
        # Apply migration first
        conn = sqlite3.connect(test_db_path)
        try:
            apply_migration(conn, MIGRATION_009)
        finally:
            conn.close()

        repo = DefinitieRepository(test_db_path)
        record = DefinitieRecord(
            begrip="sql_layer_post",
            definitie="First definition",
            categorie="ENT",
            organisatorische_context="DJI",
            juridische_context="strafrecht",
            wettelijke_basis="[]",
        )
        record_id = repo.create_definitie(record)

        insert_duplicate_bypassing_python_guard(
            test_db_path, record_id, "Bypass definition"
        )

        conn = sqlite3.connect(test_db_path)
        try:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM definities WHERE begrip = ?", ("sql_layer_post",)
            )
            assert cursor.fetchone()[0] == 2, "SQL-laag hoort na 009 niet te blokkeren"
        finally:
            conn.close()

    def test_duplicate_allowed_with_flag(self, test_db_path):
        """Verify duplicates ARE allowed with allow_duplicate=True after migration."""
        # Apply migration first
        conn = sqlite3.connect(test_db_path)
        try:
            apply_migration(conn, MIGRATION_009)
        finally:
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
        conn = sqlite3.connect(test_db_path)
        try:
            apply_migration(conn, MIGRATION_009)
        finally:
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
        conn = sqlite3.connect(test_db_path)
        try:
            apply_migration(conn, MIGRATION_009)
        finally:
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
        conn = sqlite3.connect(test_db_path)
        try:
            apply_migration(conn, MIGRATION_009)
        finally:
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
        conn = sqlite3.connect(test_db_path)
        try:
            cursor = conn.cursor()
            apply_migration(conn, MIGRATION_009)

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
            rollback_sql = read_required_migration(MIGRATION_009_ROLLBACK)

            with pytest.raises(sqlite3.IntegrityError):
                cursor.executescript(rollback_sql)

            assert (
                count_unique_index(conn) == 0
            ), "Mislukte rollback mag geen index achterlaten"
        finally:
            conn.close()

    def test_rollback_succeeds_without_duplicates(self, test_db_path):
        """Verify rollback succeeds when no duplicates exist."""
        # Apply migration 009
        conn = sqlite3.connect(test_db_path)
        try:
            apply_migration(conn, MIGRATION_009)

            # Verify INDEX removed
            assert count_unique_index(conn) == 0

            # Apply rollback (no duplicates exist)
            apply_migration(conn, MIGRATION_009_ROLLBACK)

            # Verify INDEX restored
            assert (
                count_unique_index(conn) == 1
            ), "UNIQUE INDEX should be restored after rollback"
        finally:
            conn.close()

        # Een herstelde index moet ook echt afdwingen; het bestaan van de rij in
        # sqlite_master zegt op zichzelf niets over handhaving.
        repo = DefinitieRepository(test_db_path)
        record = DefinitieRecord(
            begrip="rollback_enforced",
            definitie="First",
            categorie="ENT",
            organisatorische_context="DJI",
            juridische_context="strafrecht",
            wettelijke_basis="[]",
        )
        record_id = repo.create_definitie(record)

        with pytest.raises(sqlite3.IntegrityError, match="UNIQUE constraint failed"):
            insert_duplicate_bypassing_python_guard(
                test_db_path, record_id, "Bypass definition"
            )
