"""Tests voor V6 Migration: hybride schema (DEF-370)."""

from __future__ import annotations

import json
import sqlite3

import pytest

import database.migrations.v6_migration as v6
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
from database.sqlite_backup import create_verified_backup
from tests.fixtures.schema_profiles import (
    bouw_profiel,
    kolommen,
    lees_sentinels,
    schema_versies,
    zaai_sentinels,
)

pytestmark = [pytest.mark.unit]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def db_path(tmp_path):
    """Maak een temp database in het versie-1-profiel (v5-vorm, DEF-664).

    Het profiel bevat ook de kerntabellen: de migratie maakt sinds DEF-664
    eerst een geverifieerde backup, en de DEF-663-guard weigert een bron
    zonder kernschema.
    """
    (tmp_path / "data").mkdir()
    return bouw_profiel(tmp_path / "data" / "definities.db", 1)


def _backups(pad) -> list:
    map_ = pad.parent / "backups"
    return sorted(map_.glob("pre_v6_migration_*.db")) if map_.exists() else []


def _versies(pad) -> list[int]:
    return schema_versies(pad)


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
# DEF-664: fail-closed precondities, transactiegrens en backup/restore
# ---------------------------------------------------------------------------
class TestPrecondities:
    def test_zonder_versie_1_geen_succes_en_niets_geschreven(self, db_path):
        conn = sqlite3.connect(str(db_path))
        conn.execute("DELETE FROM schema_version")
        conn.commit()
        conn.close()

        assert run_migration(db_path) is False

        assert schema_versies(db_path) == []
        assert "bron_type" not in kolommen(db_path, "rag_chunks")
        assert _backups(db_path) == []

    def test_zonder_schema_version_tabel_geen_succes(self, tmp_path):
        pad = bouw_profiel(tmp_path / "definities.db", None)
        assert run_migration(pad) is False
        assert schema_versies(pad) == []

    def test_zonder_rag_chunks_geen_succes_en_geen_versie(self, db_path):
        conn = sqlite3.connect(str(db_path))
        conn.executescript("PRAGMA foreign_keys=OFF; DROP TABLE rag_chunks;")
        conn.close()

        assert run_migration(db_path) is False

        assert schema_versies(db_path) == [1]


class TestFoutpadIsAtomair:
    def test_falende_verificatie_rolt_alles_terug(self, db_with_data, monkeypatch):
        monkeypatch.setattr(v6, "verify_migration", lambda conn: False)

        assert run_migration(db_with_data) is False

        assert schema_versies(db_with_data) == [1]
        assert "bron_type" not in kolommen(db_with_data, "rag_chunks")

    def test_commitfout_rolt_alles_terug(self, db_with_data, monkeypatch):
        from database import schema_contract

        def _commit_faalt(conn):
            raise sqlite3.OperationalError("disk I/O error")

        monkeypatch.setattr(schema_contract, "_commit", _commit_faalt)
        conn = sqlite3.connect(str(db_with_data))
        voor = conn.execute(
            "SELECT id, chunk_text, artikel_lid FROM rag_chunks ORDER BY id"
        ).fetchall()
        conn.close()

        assert run_migration(db_with_data) is False

        assert schema_versies(db_with_data) == [1]
        assert "metadata" not in kolommen(db_with_data, "rag_chunks")
        conn = sqlite3.connect(str(db_with_data))
        assert (
            conn.execute(
                "SELECT id, chunk_text, artikel_lid FROM rag_chunks ORDER BY id"
            ).fetchall()
            == voor
        )
        conn.close()

    def test_fout_in_datamigratie_rolt_kolommen_en_versie_terug(
        self, db_with_data, monkeypatch
    ):
        def _klapt(conn):
            raise sqlite3.OperationalError("geinjecteerde fout in migrate_data")

        monkeypatch.setattr(v6, "migrate_data", _klapt)

        assert run_migration(db_with_data) is False

        assert schema_versies(db_with_data) == [1]
        assert "bron_type" not in kolommen(db_with_data, "rag_chunks")


class TestVolledigDoelcontract:
    """v6 moet het volledige versie-2-doelcontract binnen de transactie toetsen."""

    def test_ontbrekende_trigger_in_bron_geeft_geen_succes_en_rolt_terug(self, db_path):
        conn = sqlite3.connect(str(db_path))
        conn.execute("DROP TRIGGER log_definitie_changes")
        conn.close()

        assert run_migration(db_path) is False

        assert schema_versies(db_path) == [1]
        assert "bron_type" not in kolommen(db_path, "rag_chunks")

    def test_afwijkende_index_in_bron_geeft_geen_succes(self, db_path):
        conn = sqlite3.connect(str(db_path))
        conn.executescript(
            "DROP INDEX idx_definities_begrip_nocase_actief;"
            "CREATE INDEX idx_definities_begrip_nocase_actief ON definities(begrip);"
        )
        conn.close()

        assert run_migration(db_path) is False

        assert schema_versies(db_path) == [1]

    def test_geslaagde_migratie_haalt_het_versie_2_doelcontract(self, db_path):
        from database.schema_contract import (
            contract_problems,
            read_contract,
            target_contract,
        )

        assert run_migration(db_path) is True

        conn = sqlite3.connect(str(db_path))
        try:
            assert contract_problems(read_contract(conn), target_contract(2)) == []
        finally:
            conn.close()


class TestBronbehoud:
    def test_bronobjecten_die_verdwijnen_geven_geen_succes(self, db_path, monkeypatch):
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE VIEW gebruikers_extra AS SELECT id FROM definities")
        conn.close()
        origineel = v6.create_indexes

        def _sloopt_te_veel(conn):
            origineel(conn)
            conn.execute("DROP VIEW gebruikers_extra")

        monkeypatch.setattr(v6, "create_indexes", _sloopt_te_veel)

        assert run_migration(db_path) is False

        assert schema_versies(db_path) == [1]
        conn = sqlite3.connect(str(db_path))
        try:
            assert conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='view' AND name='gebruikers_extra'"
            ).fetchone()
        finally:
            conn.close()


class TestBackupEnRestore:
    def test_backup_gaat_vooraf_en_is_werkelijk_herstelbaar(self, db_path, tmp_path):
        zaai_sentinels(db_path)
        voor = lees_sentinels(db_path)

        assert run_migration(db_path) is True

        backups = _backups(db_path)
        assert len(backups) == 1
        hersteld = tmp_path / "hersteld" / "definities.db"
        hersteld.parent.mkdir()
        manifest = create_verified_backup(backups[0], hersteld)

        assert manifest.schema_version == 1
        assert "bron_type" not in kolommen(hersteld, "rag_chunks")
        assert lees_sentinels(hersteld) == voor
        assert lees_sentinels(db_path) == voor


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
