"""Tests for V5 database migration (DEF-303).

Covers: backup, schema versioning, new table creation, idempotency,
and full migration run — all using tmp_path (never production data).
"""

import sqlite3
from datetime import datetime
from pathlib import Path

import pytest

import database.migrations.v5_migration as v5_module
from database.migrations.v5_migration import (
    EXPECTED_EXISTING_TABLES,
    MIGRATION_VERSION,
    NEW_TABLES,
    apply_schema_version,
    create_backup,
    create_new_tables,
    run_migration,
    verify_backup,
    verify_migration,
)

pytestmark = [pytest.mark.unit]


# ---------------------------------------------------------------------------
# Helpers: create a realistic test database with the 13 existing tables
# ---------------------------------------------------------------------------
def _create_existing_tables(conn: sqlite3.Connection) -> None:
    """Create minimal versions of all 13 existing production tables."""
    conn.executescript("""\
        CREATE TABLE IF NOT EXISTS definities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            begrip VARCHAR(255) NOT NULL,
            definitie TEXT NOT NULL,
            categorie VARCHAR(50) NOT NULL,
            organisatorische_context TEXT NOT NULL DEFAULT '[]',
            juridische_context TEXT NOT NULL DEFAULT '[]',
            status VARCHAR(50) NOT NULL DEFAULT 'draft',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS definitie_geschiedenis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            definitie_id INTEGER NOT NULL REFERENCES definities(id),
            begrip VARCHAR(255) NOT NULL,
            wijziging_type VARCHAR(50) NOT NULL,
            gewijzigd_op TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS definitie_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            definitie_id INTEGER NOT NULL REFERENCES definities(id),
            tag_naam VARCHAR(100) NOT NULL,
            toegevoegd_op TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(definitie_id, tag_naam)
        );

        CREATE TABLE IF NOT EXISTS definitie_voorbeelden (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            definitie_id INTEGER NOT NULL REFERENCES definities(id),
            voorbeeld_type VARCHAR(50) NOT NULL,
            voorbeeld_tekst TEXT NOT NULL,
            voorbeeld_volgorde INTEGER DEFAULT 1,
            aangemaakt_op TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(definitie_id, voorbeeld_type, voorbeeld_volgorde)
        );

        CREATE TABLE IF NOT EXISTS definitie_drafts (
            definitie_id INTEGER PRIMARY KEY REFERENCES definities(id),
            draft_content TEXT NOT NULL,
            saved_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS synonym_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            canonical_term TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS synonym_group_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL REFERENCES synonym_groups(id),
            term TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            source TEXT NOT NULL DEFAULT 'manual',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(group_id, term)
        );

        CREATE TABLE IF NOT EXISTS synonym_suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hoofdterm TEXT NOT NULL,
            synoniem TEXT NOT NULL,
            confidence DECIMAL(3,2) NOT NULL,
            rationale TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS import_export_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operatie_type VARCHAR(50) NOT NULL,
            bron_bestemming VARCHAR(255) NOT NULL,
            aantal_verwerkt INTEGER NOT NULL DEFAULT 0,
            gestart_op TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(50) NOT NULL DEFAULT 'running'
        );

        CREATE TABLE IF NOT EXISTS generation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            definitie_id INTEGER UNIQUE,
            prompt_full_text TEXT NOT NULL,
            model_name VARCHAR(100) NOT NULL,
            generation_status VARCHAR(20) NOT NULL DEFAULT 'pending',
            logged_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(definitie_id) REFERENCES definities(id)
        );

        CREATE TABLE IF NOT EXISTS performance_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_name TEXT NOT NULL,
            value REAL NOT NULL,
            timestamp REAL NOT NULL,
            metadata TEXT
        );

        CREATE TABLE IF NOT EXISTS performance_baselines (
            metric_name TEXT PRIMARY KEY,
            baseline_value REAL NOT NULL,
            confidence REAL NOT NULL,
            sample_count INTEGER NOT NULL,
            last_updated REAL NOT NULL
        );
        """)


def _insert_sample_data(conn: sqlite3.Connection) -> None:
    """Insert sample rows into key tables."""
    conn.execute(
        "INSERT INTO definities (begrip, definitie, categorie) "
        "VALUES ('verificatie', 'Het controleren van gegevens', 'ENT')"
    )
    conn.execute(
        "INSERT INTO definities (begrip, definitie, categorie) "
        "VALUES ('registratie', 'Het vastleggen van gegevens', 'ENT')"
    )
    conn.execute(
        "INSERT INTO definitie_tags (definitie_id, tag_naam) VALUES (1, 'prioriteit')"
    )
    conn.execute("INSERT INTO synonym_groups (canonical_term) VALUES ('verificatie')")
    conn.execute(
        "INSERT INTO synonym_group_members (group_id, term, source) "
        "VALUES (1, 'controle', 'manual')"
    )
    conn.commit()


def _get_table_names(db_path: Path) -> set[str]:
    """Return set of user table names (excluding sqlite_sequence)."""
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name != 'sqlite_sequence'"
        )
        return {row[0] for row in cursor.fetchall()}
    finally:
        conn.close()


def _get_index_names(db_path: Path) -> set[str]:
    """Return set of user-created index names."""
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='index' AND name NOT LIKE 'sqlite_%'"
        )
        return {row[0] for row in cursor.fetchall()}
    finally:
        conn.close()


def _get_column_names(db_path: Path, table: str) -> list[str]:
    """Return column names for a given table."""
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.execute(f"PRAGMA table_info({table})")
        return [row[1] for row in cursor.fetchall()]
    finally:
        conn.close()


def _count_rows(db_path: Path, table: str) -> int:
    """Return row count for a table."""
    conn = sqlite3.connect(str(db_path))
    try:
        return conn.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def test_db(tmp_path: Path) -> Path:
    """Create a test database with 13 existing tables and sample data."""
    db_path = tmp_path / "test_definities.db"
    conn = sqlite3.connect(str(db_path))
    try:
        _create_existing_tables(conn)
        _insert_sample_data(conn)
    finally:
        conn.close()
    return db_path


@pytest.fixture
def empty_test_db(tmp_path: Path) -> Path:
    """Create a test database with 13 existing tables but no data."""
    db_path = tmp_path / "test_definities_empty.db"
    conn = sqlite3.connect(str(db_path))
    try:
        _create_existing_tables(conn)
    finally:
        conn.close()
    return db_path


# =========================================================================
# 1. BACKUP TESTS
# =========================================================================
class TestCreateBackup:
    """Tests for backup creation and verification."""

    def test_creates_file(self, test_db: Path):
        """Backup creates a file in the backups directory."""
        backup_path = create_backup(test_db)
        assert backup_path.exists()
        assert backup_path.stat().st_size > 0

    def test_preserves_all_tables(self, test_db: Path):
        """Backup contains all tables from the original."""
        backup_path = create_backup(test_db)
        original_tables = _get_table_names(test_db)
        backup_tables = _get_table_names(backup_path)
        assert original_tables == backup_tables

    def test_preserves_data(self, test_db: Path):
        """Backup preserves row counts."""
        backup_path = create_backup(test_db)
        for table in ["definities", "definitie_tags", "synonym_groups"]:
            assert _count_rows(test_db, table) == _count_rows(backup_path, table)

    def test_raises_if_db_missing(self, tmp_path: Path):
        """Raises FileNotFoundError if source db doesn't exist."""
        with pytest.raises(FileNotFoundError):
            create_backup(tmp_path / "does_not_exist.db")

    def test_backup_path_in_backups_dir(self, test_db: Path):
        """Backup file is placed in a 'backups' subdirectory."""
        backup_path = create_backup(test_db)
        assert backup_path.parent.name == "backups"


class TestCreateBackupTijdstempel:
    """PR425 M5: de microseconden in de backupnaam zijn een bewaakt contract."""

    def test_zelfde_seconde_verschillende_microseconden_geeft_twee_backups(
        self, test_db: Path, monkeypatch: pytest.MonkeyPatch
    ):
        momenten = iter(
            [
                datetime(2026, 9, 5, 12, 0, 0, 111111),
                datetime(2026, 9, 5, 12, 0, 0, 222222),
            ]
        )

        class VasteKlok:
            @classmethod
            def now(cls) -> datetime:
                return next(momenten)

        monkeypatch.setattr(v5_module, "datetime", VasteKlok)

        eerste = create_backup(test_db)
        tweede = create_backup(test_db)

        # Zonder %f zouden beide runs dezelfde naam krijgen en zou de helper de
        # tweede met destination_exists weigeren.
        assert eerste.name == "pre_v5_migration_20260905_120000_111111.db"
        assert tweede.name == "pre_v5_migration_20260905_120000_222222.db"
        assert eerste != tweede
        assert verify_backup(eerste, test_db) is True
        assert verify_backup(tweede, test_db) is True


class TestCreateBackupWal:
    """DEF-663: de backup moet een gecommitte maar niet-gecheckpointte WAL-rij bevatten.

    Scenario: een schrijver houdt de bron open in WAL-modus met automatische
    checkpoints uit (``wal_autocheckpoint=0``) en commit een rij. Die rij staat
    dan uitsluitend in ``*.db-wal``; een bestandskopie van alleen ``*.db``
    verliest hem stil.
    """

    def test_backup_bevat_ongecheckpointte_wal_commit(self, test_db: Path):
        writer = sqlite3.connect(str(test_db))
        try:
            writer.execute("PRAGMA journal_mode=WAL")
            writer.execute("PRAGMA wal_autocheckpoint=0")
            writer.execute(
                "INSERT INTO definities (begrip, definitie, categorie) "
                "VALUES ('wal-alleen', 'staat alleen in de WAL', 'proces')"
            )
            writer.commit()
            assert (test_db.parent / f"{test_db.name}-wal").stat().st_size > 0

            backup_path = create_backup(test_db)

            reader = sqlite3.connect(str(backup_path))
            try:
                rows = reader.execute(
                    "SELECT definitie FROM definities WHERE begrip = 'wal-alleen'"
                ).fetchall()
            finally:
                reader.close()
            assert rows == [("staat alleen in de WAL",)]
        finally:
            writer.close()


class TestVerifyBackup:
    """Tests for backup verification."""

    def test_valid_backup(self, test_db: Path):
        """verify_backup returns True for valid backup."""
        backup_path = create_backup(test_db)
        assert verify_backup(backup_path, test_db) is True

    def test_corrupt_file(self, tmp_path: Path, test_db: Path):
        """verify_backup returns False for corrupt/non-SQLite file."""
        corrupt = tmp_path / "corrupt.db"
        corrupt.write_text("not a database")
        assert verify_backup(corrupt, test_db) is False

    def test_kernschema_ontbreekt_in_beide(self, tmp_path: Path):
        """DEF-663: twee gelijk onvolledige databases vormen geen geldige backup.

        Integriteit en manifest komen overeen, maar geen enkele kerntabel
        (definities, geschiedenis, voorbeelden, synoniemen) is aanwezig.
        """
        for name in ("origineel.db", "backup.db"):
            conn = sqlite3.connect(str(tmp_path / name))
            try:
                conn.execute("CREATE TABLE unrelated (id INTEGER)")
                conn.commit()
            finally:
                conn.close()

        assert verify_backup(tmp_path / "backup.db", tmp_path / "origineel.db") is False

    def test_backup_zonder_kerntabel_is_ongeldig(self, tmp_path: Path, test_db: Path):
        """Een backup waaruit een kerntabel ontbreekt wordt afgekeurd."""
        backup_path = create_backup(test_db)
        conn = sqlite3.connect(str(backup_path))
        try:
            conn.execute("DROP TABLE definitie_voorbeelden")
            conn.commit()
        finally:
            conn.close()

        assert verify_backup(backup_path, test_db) is False


# =========================================================================
# 2. SCHEMA VERSIONING TESTS
# =========================================================================
class TestSchemaVersioning:
    """Tests for schema_version table."""

    def test_table_created(self, test_db: Path):
        """schema_version table is created."""
        conn = sqlite3.connect(str(test_db))
        try:
            apply_schema_version(conn)
            conn.commit()
        finally:
            conn.close()
        assert "schema_version" in _get_table_names(test_db)

    def test_records_version_1(self, test_db: Path):
        """Version 1 is recorded after applying."""
        conn = sqlite3.connect(str(test_db))
        try:
            apply_schema_version(conn)
            conn.commit()
            row = conn.execute(
                "SELECT version FROM schema_version WHERE version = ?",
                (MIGRATION_VERSION,),
            ).fetchone()
        finally:
            conn.close()
        assert row is not None
        assert row[0] == MIGRATION_VERSION

    def test_idempotent(self, test_db: Path):
        """Running twice doesn't duplicate version record."""
        conn = sqlite3.connect(str(test_db))
        try:
            apply_schema_version(conn)
            conn.commit()
            apply_schema_version(conn)
            conn.commit()
            count = conn.execute(
                "SELECT COUNT(*) FROM schema_version WHERE version = ?",
                (MIGRATION_VERSION,),
            ).fetchone()[0]
        finally:
            conn.close()
        assert count == 1

    def test_has_timestamp(self, test_db: Path):
        """schema_version record includes applied_at timestamp."""
        conn = sqlite3.connect(str(test_db))
        try:
            apply_schema_version(conn)
            conn.commit()
            row = conn.execute(
                "SELECT applied_at FROM schema_version WHERE version = ?",
                (MIGRATION_VERSION,),
            ).fetchone()
        finally:
            conn.close()
        assert row[0] is not None


# =========================================================================
# 3. NEW TABLE CREATION TESTS
# =========================================================================
class TestNewTableCreation:
    """Tests for the 8 new tables."""

    def test_all_new_tables_created(self, test_db: Path):
        """All 8 new tables exist after create_new_tables."""
        conn = sqlite3.connect(str(test_db))
        try:
            apply_schema_version(conn)
            create_new_tables(conn)
            conn.commit()
        finally:
            conn.close()

        tables = _get_table_names(test_db)
        for table in NEW_TABLES:
            assert table in tables, f"Missing table: {table}"

    def test_existing_tables_preserved(self, test_db: Path):
        """All 13 existing tables still exist."""
        conn = sqlite3.connect(str(test_db))
        try:
            apply_schema_version(conn)
            create_new_tables(conn)
            conn.commit()
        finally:
            conn.close()

        tables = _get_table_names(test_db)
        for table in EXPECTED_EXISTING_TABLES:
            assert table in tables, f"Existing table lost: {table}"

    def test_rag_chunks_has_embedding_blob(self, test_db: Path):
        """rag_chunks has an 'embedding' column of type BLOB."""
        conn = sqlite3.connect(str(test_db))
        try:
            create_new_tables(conn)
            conn.commit()
        finally:
            conn.close()
        columns = _get_column_names(test_db, "rag_chunks")
        assert "embedding" in columns

    def test_projects_has_phase_columns(self, test_db: Path):
        """projects table has all 4 phase status columns."""
        conn = sqlite3.connect(str(test_db))
        try:
            create_new_tables(conn)
            conn.commit()
        finally:
            conn.close()
        columns = _get_column_names(test_db, "projects")
        for col in [
            "phase_rag_status",
            "phase_ontology_status",
            "phase_definition_status",
            "phase_validation_status",
        ]:
            assert col in columns, f"Missing column: {col}"

    def test_ontology_terms_has_key_columns(self, test_db: Path):
        """ontology_terms has model_id, term_text, and ufo_categorie."""
        conn = sqlite3.connect(str(test_db))
        try:
            create_new_tables(conn)
            conn.commit()
        finally:
            conn.close()
        columns = _get_column_names(test_db, "ontology_terms")
        for col in ["model_id", "term_text", "ufo_categorie"]:
            assert col in columns

    def test_indexes_created(self, test_db: Path):
        """IF NOT EXISTS indexes are created on new tables."""
        conn = sqlite3.connect(str(test_db))
        try:
            create_new_tables(conn)
            conn.commit()
        finally:
            conn.close()

        indexes = _get_index_names(test_db)
        expected_indexes = [
            "idx_chunks_collection",
            "idx_chunks_document",
            "idx_ont_terms_model",
            "idx_ont_rels_model",
        ]
        for idx in expected_indexes:
            assert idx in indexes, f"Missing index: {idx}"


# =========================================================================
# 4. IDEMPOTENCY TESTS
# =========================================================================
class TestIdempotency:
    """Tests ensuring migration can be run multiple times safely."""

    def test_same_tables_after_two_runs(self, test_db: Path):
        """Running migration twice produces the same table set."""
        run_migration(test_db)
        tables_first = _get_table_names(test_db)

        run_migration(test_db)
        tables_second = _get_table_names(test_db)

        assert tables_first == tables_second

    def test_existing_data_preserved(self, test_db: Path):
        """Row counts in original tables unchanged after migration."""
        counts_before = {}
        for table in EXPECTED_EXISTING_TABLES:
            try:
                counts_before[table] = _count_rows(test_db, table)
            except sqlite3.OperationalError:
                counts_before[table] = 0

        run_migration(test_db)

        for table, before in counts_before.items():
            after = _count_rows(test_db, table)
            assert after == before, f"{table}: {before} -> {after}"

    def test_indexes_same_after_two_runs(self, test_db: Path):
        """Same indexes after running migration twice."""
        run_migration(test_db)
        idx_first = _get_index_names(test_db)

        run_migration(test_db)
        idx_second = _get_index_names(test_db)

        assert idx_first == idx_second

    def test_schema_version_not_duplicated(self, test_db: Path):
        """Version 1 appears exactly once after two runs."""
        run_migration(test_db)
        run_migration(test_db)

        conn = sqlite3.connect(str(test_db))
        try:
            count = conn.execute(
                "SELECT COUNT(*) FROM schema_version WHERE version = ?",
                (MIGRATION_VERSION,),
            ).fetchone()[0]
        finally:
            conn.close()
        assert count == 1


# =========================================================================
# 5. FULL RUN TESTS
# =========================================================================
class TestRunMigration:
    """Tests for the complete run_migration function."""

    def test_returns_true_on_success(self, test_db: Path):
        """run_migration returns True on success."""
        assert run_migration(test_db) is True

    def test_returns_true_on_empty_db(self, empty_test_db: Path):
        """run_migration succeeds on empty tables."""
        assert run_migration(empty_test_db) is True

    def test_creates_all_new_tables(self, test_db: Path):
        """After full migration, all 8 new tables exist."""
        run_migration(test_db)
        tables = _get_table_names(test_db)
        for table in NEW_TABLES:
            assert table in tables

    def test_preserves_existing_tables(self, test_db: Path):
        """After full migration, all existing tables still exist."""
        run_migration(test_db)
        tables = _get_table_names(test_db)
        for table in EXPECTED_EXISTING_TABLES:
            assert table in tables

    def test_preserves_row_data(self, test_db: Path):
        """Specific data rows survive migration."""
        run_migration(test_db)
        conn = sqlite3.connect(str(test_db))
        try:
            begrippen = [
                r[0]
                for r in conn.execute(
                    "SELECT begrip FROM definities ORDER BY begrip"
                ).fetchall()
            ]
            assert "verificatie" in begrippen
            assert "registratie" in begrippen
        finally:
            conn.close()

    def test_records_schema_version(self, test_db: Path):
        """After migration, schema_version has version 1."""
        run_migration(test_db)
        conn = sqlite3.connect(str(test_db))
        try:
            row = conn.execute(
                "SELECT version FROM schema_version WHERE version = ?",
                (MIGRATION_VERSION,),
            ).fetchone()
        finally:
            conn.close()
        assert row is not None
        assert row[0] == MIGRATION_VERSION

    def test_creates_backup(self, test_db: Path):
        """Migration creates a backup file."""
        run_migration(test_db)
        backup_dir = test_db.parent / "backups"
        assert backup_dir.exists()
        backups = list(backup_dir.glob("pre_v5_migration_*.db"))
        assert len(backups) >= 1


# =========================================================================
# 6. VERIFY MIGRATION TESTS
# =========================================================================
class TestVerifyMigration:
    """Tests for verify_migration."""

    def test_passes_after_run(self, test_db: Path):
        """verify_migration returns True after successful migration."""
        run_migration(test_db)
        conn = sqlite3.connect(str(test_db))
        try:
            result = verify_migration(conn)
        finally:
            conn.close()
        assert result is True

    def test_fails_before_run(self, test_db: Path):
        """verify_migration returns False before migration."""
        conn = sqlite3.connect(str(test_db))
        try:
            result = verify_migration(conn)
        finally:
            conn.close()
        assert result is False
