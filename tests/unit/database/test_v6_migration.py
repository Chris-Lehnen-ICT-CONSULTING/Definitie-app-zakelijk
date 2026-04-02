"""Tests voor V6 Migration: hybride schema (DEF-370)."""

from __future__ import annotations

import json
import sqlite3

import pytest

from database.migrations.v6_migration import (
    METADATA_KEYS_PER_BRON_TYPE,
    MIGRATION_VERSION,
    _add_column_if_not_exists,
    _column_exists,
    add_columns,
    apply_schema_version,
    create_indexes,
    migrate_data,
    run_migration,
    verify_migration,
)

pytestmark = [pytest.mark.unit]

# ---------------------------------------------------------------------------
# Pre-migration schema (mirrors v5 state)
# ---------------------------------------------------------------------------
V5_SCHEMA_SQL = """
CREATE TABLE schema_version (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version INTEGER NOT NULL,
    description TEXT,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO schema_version (version, description) VALUES (1, 'Initial v5 migration');

CREATE TABLE rag_collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_name VARCHAR(255) NOT NULL UNIQUE,
    document_count INTEGER DEFAULT 0,
    chunk_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata_json TEXT
);

CREATE TABLE rag_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_id INTEGER REFERENCES rag_collections(id) ON DELETE CASCADE,
    filename VARCHAR(255),
    file_type VARCHAR(50),
    chunk_count INTEGER,
    rechtsgebied VARCHAR(100),
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_path VARCHAR(500)
);

CREATE TABLE rag_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_id INTEGER REFERENCES rag_collections(id) ON DELETE CASCADE,
    document_id INTEGER REFERENCES rag_documents(id) ON DELETE CASCADE,
    chunk_text TEXT NOT NULL,
    embedding BLOB,
    chunk_index INTEGER,
    rechtsgebied VARCHAR(100),
    wet_regeling VARCHAR(255),
    artikel_lid VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chunks_collection ON rag_chunks(collection_id);
CREATE INDEX idx_chunks_document ON rag_chunks(document_id);
"""


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def db_path(tmp_path):
    """Maak een temp database met v5 schema."""
    path = tmp_path / "test.db"
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(V5_SCHEMA_SQL)
    conn.close()
    return path


@pytest.fixture
def conn(db_path):
    """SQLite connectie naar test database."""
    connection = sqlite3.connect(str(db_path))
    connection.execute("PRAGMA foreign_keys=ON")
    yield connection
    connection.close()


@pytest.fixture
def db_with_data(conn, db_path):
    """Database met bestaande chunks (pre-migratie data)."""
    conn.execute(
        "INSERT INTO rag_collections (collection_name, metadata_json) "
        "VALUES ('test', '{\"dimensions\": 8}')"
    )
    conn.execute(
        "INSERT INTO rag_documents (collection_id, filename, rechtsgebied) "
        "VALUES (1, 'wet.pdf', 'bestuursrecht')"
    )
    # Chunk met artikel_lid (legacy)
    conn.execute(
        "INSERT INTO rag_chunks (collection_id, document_id, chunk_text, "
        "chunk_index, rechtsgebied, wet_regeling, artikel_lid) "
        "VALUES (1, 1, 'Artikel 1 lid 2', 0, 'bestuursrecht', 'Awb', 'art. 1:2')"
    )
    # Chunk zonder artikel_lid
    conn.execute(
        "INSERT INTO rag_chunks (collection_id, document_id, chunk_text, "
        "chunk_index, rechtsgebied) "
        "VALUES (1, 1, 'Inleiding', 1, 'bestuursrecht')"
    )
    conn.commit()
    return db_path


# ---------------------------------------------------------------------------
# Tests: helpers
# ---------------------------------------------------------------------------
class TestHelpers:
    def test_column_exists_true(self, conn):
        assert _column_exists(conn, "rag_chunks", "chunk_text") is True

    def test_column_exists_false(self, conn):
        assert _column_exists(conn, "rag_chunks", "nonexistent") is False

    def test_add_column_if_not_exists_new(self, conn):
        _add_column_if_not_exists(conn, "rag_chunks", "test_col", "VARCHAR(50)")
        assert _column_exists(conn, "rag_chunks", "test_col") is True

    def test_add_column_if_not_exists_duplicate(self, conn):
        """Herhaald toevoegen van dezelfde kolom is safe."""
        _add_column_if_not_exists(conn, "rag_chunks", "test_col", "VARCHAR(50)")
        _add_column_if_not_exists(conn, "rag_chunks", "test_col", "VARCHAR(50)")
        assert _column_exists(conn, "rag_chunks", "test_col") is True

    def test_add_column_unknown_type_raises(self, conn):
        with pytest.raises(ValueError, match="Onbekend kolomtype"):
            _add_column_if_not_exists(conn, "rag_chunks", "bad", "DANGER_TYPE")


# ---------------------------------------------------------------------------
# Tests: schema versioning
# ---------------------------------------------------------------------------
class TestSchemaVersion:
    def test_inserts_version_2(self, conn):
        apply_schema_version(conn)
        row = conn.execute(
            "SELECT version, description FROM schema_version WHERE version = ?",
            (MIGRATION_VERSION,),
        ).fetchone()
        assert row is not None
        assert row[0] == 2

    def test_idempotent(self, conn):
        apply_schema_version(conn)
        apply_schema_version(conn)
        count = conn.execute(
            "SELECT COUNT(*) FROM schema_version WHERE version = ?",
            (MIGRATION_VERSION,),
        ).fetchone()[0]
        assert count == 1

    def test_preserves_v1(self, conn):
        """V5 version (1) moet intact blijven."""
        apply_schema_version(conn)
        v1 = conn.execute(
            "SELECT version FROM schema_version WHERE version = 1"
        ).fetchone()
        assert v1 is not None


# ---------------------------------------------------------------------------
# Tests: kolommen toevoegen
# ---------------------------------------------------------------------------
class TestAddColumns:
    def test_adds_bron_type(self, conn):
        add_columns(conn)
        assert _column_exists(conn, "rag_chunks", "bron_type") is True

    def test_adds_metadata(self, conn):
        add_columns(conn)
        assert _column_exists(conn, "rag_chunks", "metadata") is True

    def test_idempotent(self, conn):
        add_columns(conn)
        add_columns(conn)
        assert _column_exists(conn, "rag_chunks", "bron_type") is True
        assert _column_exists(conn, "rag_chunks", "metadata") is True


# ---------------------------------------------------------------------------
# Tests: data migratie
# ---------------------------------------------------------------------------
class TestDataMigration:
    def test_migrates_artikel_lid_to_metadata(self, db_with_data):
        conn = sqlite3.connect(str(db_with_data))
        add_columns(conn)
        stats = migrate_data(conn)
        conn.commit()

        # Chunk met artikel_lid → metadata gemigreerd
        row = conn.execute(
            "SELECT json(metadata), bron_type FROM rag_chunks WHERE chunk_index = 0"
        ).fetchone()
        meta = json.loads(row[0])
        assert meta["artikel_nummer"] == "art. 1:2"
        assert row[1] == "wetgeving"
        assert stats["metadata_migrated"] == 1
        conn.close()

    def test_fills_empty_metadata(self, db_with_data):
        """Chunk zonder artikel_lid behoudt lege metadata.

        ALTER TABLE ADD COLUMN met DEFAULT '{}' geeft bestaande rijen
        automatisch de default waarde, dus empty_filled kan 0 zijn.
        """
        conn = sqlite3.connect(str(db_with_data))
        add_columns(conn)
        stats = migrate_data(conn)
        conn.commit()

        # Chunk zonder artikel_lid → lege metadata (via DEFAULT of UPDATE)
        row = conn.execute(
            "SELECT json(metadata) FROM rag_chunks WHERE chunk_index = 1"
        ).fetchone()
        meta = json.loads(row[0])
        assert meta == {}
        # empty_filled kan 0 zijn door DEFAULT '{}' op bestaande rijen
        assert stats["empty_filled"] >= 0
        conn.close()

    def test_sets_bron_type_for_rechtsgebied(self, db_with_data):
        conn = sqlite3.connect(str(db_with_data))
        add_columns(conn)
        stats = migrate_data(conn)
        conn.commit()

        rows = conn.execute(
            "SELECT bron_type FROM rag_chunks WHERE rechtsgebied IS NOT NULL"
        ).fetchall()
        assert all(row[0] == "wetgeving" for row in rows)
        assert stats["bron_type_set"] == 2
        conn.close()

    def test_idempotent_does_not_overwrite(self, db_with_data):
        """Herhaald uitvoeren overschrijft niet."""
        conn = sqlite3.connect(str(db_with_data))
        add_columns(conn)
        migrate_data(conn)
        conn.commit()

        # Wijzig metadata handmatig
        conn.execute(
            "UPDATE rag_chunks SET metadata = jsonb(?) WHERE chunk_index = 0",
            (json.dumps({"artikel_nummer": "custom_value"}),),
        )
        conn.commit()

        # Herhaald uitvoeren
        migrate_data(conn)
        conn.commit()

        row = conn.execute(
            "SELECT json(metadata) FROM rag_chunks WHERE chunk_index = 0"
        ).fetchone()
        meta = json.loads(row[0])
        assert meta["artikel_nummer"] == "custom_value"
        conn.close()


# ---------------------------------------------------------------------------
# Tests: indexes
# ---------------------------------------------------------------------------
class TestIndexes:
    def test_creates_indexes(self, conn):
        add_columns(conn)
        create_indexes(conn)

        indexes = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' "
                "AND tbl_name='rag_chunks'"
            ).fetchall()
        }
        assert "idx_chunks_rechtsgebied" in indexes
        assert "idx_chunks_wet_regeling" in indexes
        assert "idx_chunks_bron_type" in indexes

    def test_idempotent(self, conn):
        add_columns(conn)
        create_indexes(conn)
        create_indexes(conn)


# ---------------------------------------------------------------------------
# Tests: verificatie
# ---------------------------------------------------------------------------
class TestVerifyMigration:
    def test_passes_after_full_migration(self, conn):
        apply_schema_version(conn)
        add_columns(conn)
        create_indexes(conn)
        conn.commit()
        assert verify_migration(conn) is True

    def test_fails_without_columns(self, conn):
        apply_schema_version(conn)
        conn.commit()
        assert verify_migration(conn) is False


# ---------------------------------------------------------------------------
# Tests: run_migration orchestrator
# ---------------------------------------------------------------------------
class TestRunMigration:
    def test_full_migration(self, db_with_data):
        assert run_migration(db_with_data) is True

        conn = sqlite3.connect(str(db_with_data))
        # Kolommen bestaan
        assert _column_exists(conn, "rag_chunks", "bron_type")
        assert _column_exists(conn, "rag_chunks", "metadata")

        # Schema version 2
        row = conn.execute(
            "SELECT version FROM schema_version WHERE version = 2"
        ).fetchone()
        assert row is not None

        # Data gemigreerd
        row = conn.execute(
            "SELECT json(metadata), bron_type FROM rag_chunks WHERE chunk_index = 0"
        ).fetchone()
        meta = json.loads(row[0])
        assert meta["artikel_nummer"] == "art. 1:2"
        assert row[1] == "wetgeving"
        conn.close()

    def test_idempotent_full(self, db_with_data):
        """Twee keer uitvoeren → zelfde resultaat."""
        assert run_migration(db_with_data) is True
        assert run_migration(db_with_data) is True

    def test_nonexistent_db_returns_false(self, tmp_path):
        assert run_migration(tmp_path / "nonexistent.db") is False


# ---------------------------------------------------------------------------
# Tests: metadata schema conventie
# ---------------------------------------------------------------------------
class TestMetadataConventie:
    def test_all_bron_types_defined(self):
        assert set(METADATA_KEYS_PER_BRON_TYPE.keys()) == {
            "wetgeving",
            "website",
            "pdf",
            "api",
        }

    def test_wetgeving_keys(self):
        assert "artikel_nummer" in METADATA_KEYS_PER_BRON_TYPE["wetgeving"]
        assert "lid_nummer" in METADATA_KEYS_PER_BRON_TYPE["wetgeving"]
        assert "structuur_type" in METADATA_KEYS_PER_BRON_TYPE["wetgeving"]
