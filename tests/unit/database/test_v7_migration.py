"""Tests voor V7 Migration: fail-closed, transactioneel, met backup (DEF-664).

Gemeten vóór deze reparatie: v7 meldde succes op een database zónder
``rag_collections`` en schreef schema_version 3 weg, omdat de kolomcheck een
lege ``PRAGMA table_info`` las als "kolom al verwijderd". De commit stond
bovendien vóór de verificatie en er werd geen backup gemaakt.
"""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

import database.migrations.v7_migration as v7
from database.sqlite_backup import create_verified_backup
from tests.fixtures.schema_profiles import (
    REPO_ROOT,
    bouw_profiel,
    kolommen,
    lees_sentinels,
    schema_versies,
    zaai_sentinels,
)

pytestmark = [pytest.mark.unit]


def _backups(pad: Path) -> list[Path]:
    map_ = pad.parent / "backups"
    return sorted(map_.glob("pre_v7_migration_*.db")) if map_.exists() else []


def _views(pad: Path) -> set[str]:
    conn = sqlite3.connect(str(pad))
    try:
        return {
            r[0]
            for r in conn.execute("SELECT name FROM sqlite_master WHERE type='view'")
        }
    finally:
        conn.close()


@pytest.fixture
def v2_db(tmp_path: Path) -> Path:
    (tmp_path / "data").mkdir()
    pad = bouw_profiel(tmp_path / "data" / "definities.db", 2)
    zaai_sentinels(pad)
    return pad


class TestGeslaagdeMigratie:
    def test_v2_naar_v3_met_databehoud(self, v2_db: Path):
        voor = lees_sentinels(v2_db)
        assert "document_count" in kolommen(v2_db, "rag_collections")

        assert v7.run_migration(v2_db) is True

        assert schema_versies(v2_db) == [1, 2, 3]
        assert not {"document_count", "chunk_count"} & set(
            kolommen(v2_db, "rag_collections")
        )
        assert lees_sentinels(v2_db) == voor

    def test_stale_views_worden_verwijderd(self, v2_db: Path):
        # De historische vorm: de views verwijzen naar een tabel die niet meer
        # bestaat (generation_logs_old is destijds verwijderd).
        conn = sqlite3.connect(str(v2_db))
        conn.executescript(
            "CREATE TABLE generation_logs_old (id INTEGER);"
            "CREATE VIEW failed_generations AS SELECT * FROM generation_logs_old;"
            "CREATE VIEW definities_with_generation AS SELECT * FROM generation_logs_old;"
            "DROP TABLE generation_logs_old;"
        )
        conn.close()

        assert v7.run_migration(v2_db) is True

        assert not {"failed_generations", "definities_with_generation"} & _views(v2_db)

    def test_bruikbare_views_op_bestaande_generation_logs_old_blijven_staan(
        self, v2_db: Path
    ):
        # Bestaat de tabel wél, dan zijn de views bruikbaar en dus bronobjecten.
        conn = sqlite3.connect(str(v2_db))
        conn.executescript(
            "CREATE TABLE generation_logs_old (id INTEGER);"
            "CREATE VIEW failed_generations AS SELECT * FROM generation_logs_old;"
        )
        conn.close()

        assert v7.run_migration(v2_db) is True

        assert "failed_generations" in _views(v2_db)

    def test_geldige_gebruikersviews_met_bekende_naam_blijven_staan(self, v2_db: Path):
        # Codex-interimreview P1: v7 verwijderde élke view met een van de twee
        # historische namen, ook een geldige die alleen `definities` leest.
        conn = sqlite3.connect(str(v2_db))
        conn.executescript(
            "CREATE VIEW failed_generations AS "
            "SELECT id, begrip FROM definities WHERE status = 'draft';"
            "CREATE VIEW definities_with_generation AS "
            "SELECT id, begrip, generation_prompt_data FROM definities;"
            "CREATE VIEW gebruikers_extra AS SELECT id FROM definities;"
        )
        conn.close()

        assert v7.run_migration(v2_db) is True

        assert {
            "failed_generations",
            "definities_with_generation",
            "gebruikers_extra",
        } <= _views(v2_db)
        conn = sqlite3.connect(str(v2_db))
        try:
            assert conn.execute("SELECT COUNT(*) FROM failed_generations").fetchone()
        finally:
            conn.close()

    def test_geldige_view_met_literal_generation_logs_old_blijft_staan(
        self, v2_db: Path
    ):
        # Rootprobe (probe-valid-stale-name-view): substringclassificatie van
        # de SQL is geen bewijs van een echte tabelverwijzing.
        conn = sqlite3.connect(str(v2_db))
        conn.executescript(
            "CREATE VIEW failed_generations AS "
            "SELECT id, 'generation_logs_old' AS note FROM definities;"
            "CREATE VIEW definities_with_generation AS "
            "SELECT d.id AS generation_logs_old FROM definities d -- generation_logs_old\n;"
        )
        conn.close()

        assert v7.run_migration(v2_db) is True

        assert {"failed_generations", "definities_with_generation"} <= _views(v2_db)
        conn = sqlite3.connect(str(v2_db))
        try:
            # De view leest echt uit definities: evenveel rijen als de tabel.
            assert (
                conn.execute("SELECT COUNT(*) FROM failed_generations").fetchone()[0]
                == conn.execute("SELECT COUNT(*) FROM definities").fetchone()[0]
                > 0
            )
        finally:
            conn.close()

    def test_view_met_bekende_naam_maar_andere_defecte_verwijzing_faalt_veilig(
        self, v2_db: Path
    ):
        # Twijfelgeval: onbruikbaar, maar niet de bekende historische vorm.
        # Dan liever niets wijzigen dan een onbekende view weggooien.
        conn = sqlite3.connect(str(v2_db))
        conn.executescript(
            "CREATE TABLE tijdelijk (id INTEGER);"
            "CREATE VIEW failed_generations AS SELECT * FROM tijdelijk;"
            "DROP TABLE tijdelijk;"
        )
        conn.close()

        assert v7.run_migration(v2_db) is False

        assert "failed_generations" in _views(v2_db)
        assert schema_versies(v2_db) == [1, 2]
        assert "document_count" in kolommen(v2_db, "rag_collections")

    def test_bronobjecten_die_verdwijnen_geven_geen_succes(
        self, v2_db: Path, monkeypatch
    ):
        # Bronbehoud is een afzonderlijke controle tegen het pre-migratie-
        # manifest: een stap die stil een bestaand object sloopt mag niet
        # committen, ook als het doelcontract (dat extra's toestaat) slaagt.
        conn = sqlite3.connect(str(v2_db))
        conn.execute("CREATE VIEW gebruikers_extra AS SELECT id FROM definities")
        conn.close()
        origineel = v7.drop_stale_views

        def _sloopt_te_veel(conn):
            origineel(conn)
            conn.execute("DROP VIEW gebruikers_extra")

        monkeypatch.setattr(v7, "drop_stale_views", _sloopt_te_veel)

        assert v7.run_migration(v2_db) is False

        assert "gebruikers_extra" in _views(v2_db)
        assert schema_versies(v2_db) == [1, 2]

    def test_idempotent(self, v2_db: Path):
        assert v7.run_migration(v2_db) is True
        assert v7.run_migration(v2_db) is True
        assert schema_versies(v2_db) == [1, 2, 3]

    def test_backup_gaat_vooraf_en_is_werkelijk_herstelbaar(
        self, v2_db: Path, tmp_path: Path
    ):
        voor = lees_sentinels(v2_db)
        assert v7.run_migration(v2_db) is True

        backups = _backups(v2_db)
        assert len(backups) == 1
        hersteld = tmp_path / "hersteld" / "definities.db"
        hersteld.parent.mkdir()
        manifest = create_verified_backup(backups[0], hersteld)

        # De backup is de toestand van vóór de migratie: tellers nog aanwezig,
        # versie 3 nog niet, alle sentinels exact terug te lezen.
        assert manifest.schema_version == 2
        assert "document_count" in kolommen(hersteld, "rag_collections")
        assert lees_sentinels(hersteld) == voor


class TestPrecondities:
    def test_zonder_rag_collections_geen_succes_en_geen_versie(self, tmp_path: Path):
        pad = bouw_profiel(tmp_path / "definities.db", 2)
        conn = sqlite3.connect(str(pad))
        conn.executescript(
            "PRAGMA foreign_keys=OFF; DROP TABLE rag_chunks; DROP TABLE rag_documents;"
            "DROP TABLE rag_collections;"
        )
        conn.close()

        assert v7.run_migration(pad) is False

        assert schema_versies(pad) == [1, 2]
        assert _backups(pad) == []

    def test_zonder_schema_version_tabel_geen_succes(self, tmp_path: Path):
        pad = bouw_profiel(tmp_path / "definities.db", None)
        voor = kolommen(pad, "definities")

        assert v7.run_migration(pad) is False

        assert schema_versies(pad) == []
        assert kolommen(pad, "definities") == voor

    def test_zonder_versie_2_geen_succes_en_niets_geschreven(self, tmp_path: Path):
        pad = bouw_profiel(tmp_path / "definities.db", 1)

        assert v7.run_migration(pad) is False

        assert schema_versies(pad) == [1]
        assert "document_count" in kolommen(pad, "rag_collections")

    def test_onbestaande_database_geen_succes(self, tmp_path: Path):
        assert v7.run_migration(tmp_path / "bestaat-niet.db") is False


class TestFoutpadIsAtomair:
    def test_falende_verificatie_rolt_alles_terug(self, v2_db: Path, monkeypatch):
        monkeypatch.setattr(v7, "verify_migration", lambda conn: False)

        assert v7.run_migration(v2_db) is False

        assert schema_versies(v2_db) == [1, 2]
        assert "document_count" in kolommen(v2_db, "rag_collections")

    def test_commitfout_rolt_alles_terug(self, v2_db: Path, monkeypatch):
        from database import schema_contract

        def _commit_faalt(conn):
            raise sqlite3.OperationalError("disk I/O error")

        monkeypatch.setattr(schema_contract, "_commit", _commit_faalt)
        voor = lees_sentinels(v2_db)

        assert v7.run_migration(v2_db) is False

        assert schema_versies(v2_db) == [1, 2]
        assert "document_count" in kolommen(v2_db, "rag_collections")
        assert lees_sentinels(v2_db) == voor

    def test_ddl_fout_rolt_versie_terug(self, v2_db: Path, monkeypatch):
        def _klapt(conn):
            raise sqlite3.OperationalError("geinjecteerde DDL-fout")

        monkeypatch.setattr(v7, "drop_stale_columns", _klapt)

        assert v7.run_migration(v2_db) is False

        assert schema_versies(v2_db) == [1, 2]


class TestVolledigDoelcontract:
    """Rootprobe (probe-migration-atomicity): v7 meldde succes op een v2-bron
    zónder de verplichte trigger, waarna startup de database weigerde. De
    migratie moet het volledige versie-3-doelcontract binnen de transactie
    toetsen, niet alleen haar eigen mutaties."""

    def test_ontbrekende_trigger_in_bron_geeft_geen_succes_en_rolt_terug(
        self, v2_db: Path
    ):
        conn = sqlite3.connect(str(v2_db))
        conn.execute("DROP TRIGGER log_definitie_changes")
        conn.close()
        voor = lees_sentinels(v2_db)

        assert v7.run_migration(v2_db) is False

        assert schema_versies(v2_db) == [1, 2]
        assert "document_count" in kolommen(v2_db, "rag_collections")
        assert lees_sentinels(v2_db) == voor

    def test_afwijkende_view_in_bron_geeft_geen_succes(self, v2_db: Path):
        conn = sqlite3.connect(str(v2_db))
        conn.executescript(
            "DROP VIEW actieve_definities;"
            "CREATE VIEW actieve_definities AS SELECT * FROM definities;"
        )
        conn.close()

        assert v7.run_migration(v2_db) is False

        assert schema_versies(v2_db) == [1, 2]

    def test_geslaagde_migratie_haalt_het_startupcontract(self, v2_db: Path):
        from database.schema_contract import assert_startup_contract

        assert v7.run_migration(v2_db) is True

        conn = sqlite3.connect(str(v2_db))
        try:
            assert_startup_contract(conn)
        finally:
            conn.close()


class TestCliExitcode:
    def _run(self, cwd: Path) -> subprocess.CompletedProcess[str]:
        env = {
            **os.environ,
            "PYTHONPATH": str(REPO_ROOT / "src"),
            "DEFINITIE_DISABLE_DOTENV": "1",
        }
        return subprocess.run(
            [sys.executable, "-m", "database.migrations.v7_migration"],
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )

    def test_exit_1_zonder_database(self, tmp_path: Path):
        assert self._run(tmp_path).returncode == 1

    def test_exit_1_bij_geweigerde_preconditie(self, tmp_path: Path):
        (tmp_path / "data").mkdir()
        bouw_profiel(tmp_path / "data" / "definities.db", 1)
        assert self._run(tmp_path).returncode == 1

    def test_exit_0_bij_geslaagde_migratie(self, v2_db: Path):
        assert self._run(v2_db.parents[1]).returncode == 0
        assert schema_versies(v2_db) == [1, 2, 3]
