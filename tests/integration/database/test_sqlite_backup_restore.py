"""Backup-en-restore-integratietest voor de WAL-veilige backup (DEF-663).

Bouwt een synthetische database uit het volledige ``src/database/schema.sql``
(tabellen, indexen, views én triggers), vult definities, geschiedenis,
voorbeelden, tags, synoniemen en ``schema_version``, laat een schrijver met
niet-gecheckpointte WAL-commits open staan, maakt de backup en herstelt die
naar een NIEUWE database in ``tmp_path``. Daarna wordt alles exact herlezen.

Herstel naar een nieuwe database is dezelfde geverifieerde kopieerroute als de
backup zelf: ``create_verified_backup(backup, nieuw_pad)``. Beschadigde en
onvolledige backups moeten daarbij falen zonder eindbestand.
"""

from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

import pytest

from database import sqlite_backup
from database.sqlite_backup import BackupError, create_verified_backup, read_manifest

pytestmark = [pytest.mark.integration]

_REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_SQL = (_REPO_ROOT / "src" / "database" / "schema.sql").read_text()

# (tabel, kolommen) die na restore exact vergeleken worden.
HERLEES_QUERIES: dict[str, str] = {
    "definities": (
        "SELECT id, begrip, definitie, categorie, status, version_number "
        "FROM definities ORDER BY id"
    ),
    "definitie_geschiedenis": (
        "SELECT id, definitie_id, begrip, wijziging_type, definitie_oude_waarde, "
        "definitie_nieuwe_waarde FROM definitie_geschiedenis ORDER BY id"
    ),
    "definitie_voorbeelden": (
        "SELECT id, definitie_id, voorbeeld_type, voorbeeld_tekst, voorbeeld_volgorde "
        "FROM definitie_voorbeelden ORDER BY id"
    ),
    "definitie_tags": "SELECT id, definitie_id, tag_naam FROM definitie_tags ORDER BY id",
    "synonym_groups": "SELECT id, canonical_term, domain FROM synonym_groups ORDER BY id",
    "synonym_group_members": (
        "SELECT id, group_id, term, source, status FROM synonym_group_members ORDER BY id"
    ),
    "schema_version": "SELECT version, description FROM schema_version ORDER BY version",
}


def _read_all(path: Path) -> dict[str, list[tuple]]:
    conn = sqlite3.connect(str(path))
    try:
        return {
            table: conn.execute(sql).fetchall()
            for table, sql in HERLEES_QUERIES.items()
        }
    finally:
        conn.close()


def _corrupt_second_page(path: Path) -> None:
    page_size = int.from_bytes(path.read_bytes()[16:18], "big") or 4096
    with path.open("r+b") as handle:
        handle.seek(page_size)
        handle.write(b"\xff" * page_size)


@pytest.fixture
def bron_met_open_writer(tmp_path: Path):
    """Volledige schema.sql-database; de laatste commits staan alleen in de WAL."""
    bron_dir = tmp_path / "bron"
    bron_dir.mkdir()
    path = bron_dir / "definities.db"
    writer = sqlite3.connect(str(path))
    # schema.sql bevat seed-data (definities 1-2 en vier tags); de synthetische
    # rijen hieronder krijgen daarom id 3 en 4.
    # DEF-664: schema.sql is de canonieke versie-3-vorm en zaait zelf de drie
    # schema_version-rijen; de fixture voegt er geen meer toe.
    writer.executescript(SCHEMA_SQL)
    writer.executescript("""
        INSERT INTO definities (begrip, definitie, categorie)
            VALUES ('toetsing', 'Het controleren van gegevens', 'ENT');
        INSERT INTO definities (begrip, definitie, categorie)
            VALUES ('vastlegging', 'Het vastleggen van gegevens', 'ACT');
        INSERT INTO definitie_geschiedenis (definitie_id, begrip, wijziging_type)
            VALUES (3, 'toetsing', 'created');
        INSERT INTO definitie_tags (definitie_id, tag_naam) VALUES (3, 'prioriteit');
        INSERT INTO synonym_groups (canonical_term, domain) VALUES ('toetsing', 'strafrecht');
        INSERT INTO synonym_group_members (group_id, term, source) VALUES (1, 'controle', 'manual');
        """)
    writer.commit()

    # Vanaf hier WAL zonder automatische checkpoints: deze commits staan
    # uitsluitend in definities.db-wal zolang de writer open blijft.
    writer.execute("PRAGMA journal_mode=WAL")
    writer.execute("PRAGMA wal_autocheckpoint=0")
    writer.executescript("""
        UPDATE definities SET definitie = 'Het toetsen van gegevens' WHERE id = 3;
        INSERT INTO definitie_voorbeelden (definitie_id, voorbeeld_type, voorbeeld_tekst)
            VALUES (3, 'sentence', 'De toetsing van het adres slaagde.');
        INSERT INTO definitie_voorbeelden (definitie_id, voorbeeld_type, voorbeeld_tekst, voorbeeld_volgorde)
            VALUES (4, 'practical', 'Vastlegging in het register.', 2);
        INSERT INTO synonym_group_members (group_id, term, source) VALUES (1, 'toetsing', 'ai_suggested');
        """)
    writer.commit()
    assert (bron_dir / "definities.db-wal").stat().st_size > 0

    try:
        yield path
    finally:
        writer.close()


class TestBackupEnRestore:
    def test_restore_naar_nieuwe_database_leest_alles_exact_terug(
        self, tmp_path: Path, bron_met_open_writer: Path
    ):
        verwacht = _read_all(bron_met_open_writer)
        # De triggers uit schema.sql maakten bij de UPDATE geschiedenisrijen aan:
        # log_definitie_changes vuurt op de UPDATE zelf én op de UPDATE die
        # update_definities_timestamp daarbinnen doet (bekende trigger-cascade).
        assert [r[3] for r in verwacht["definitie_geschiedenis"]] == [
            "created",
            "updated",
            "updated",
        ]
        assert len(verwacht["definitie_voorbeelden"]) == 2
        assert len(verwacht["synonym_group_members"]) == 2

        backup_dir = tmp_path / "backups"
        backup_dir.mkdir()
        backup = backup_dir / "definities_backup.db"
        manifest = create_verified_backup(bron_met_open_writer, backup)
        assert sorted(p.name for p in backup_dir.iterdir()) == [backup.name]

        restore_dir = tmp_path / "restore"
        restore_dir.mkdir()
        hersteld = restore_dir / "definities_hersteld.db"
        hersteld_manifest = create_verified_backup(backup, hersteld)

        assert hersteld_manifest == manifest
        assert _read_all(hersteld) == verwacht
        assert [v for v, _ in verwacht["schema_version"]] == [1, 2, 3]
        assert manifest.schema_version == 3

        conn = sqlite3.connect(str(hersteld))
        try:
            assert conn.execute("PRAGMA integrity_check").fetchall() == [("ok",)]
            assert read_manifest(conn) == manifest
            types = dict(
                conn.execute(
                    "SELECT type, COUNT(*) FROM sqlite_master "
                    "WHERE lower(substr(name, 1, 7)) <> 'sqlite_' GROUP BY type"
                ).fetchall()
            )
        finally:
            conn.close()
        assert types["view"] == 3
        assert types["trigger"] >= 4
        assert types["index"] >= 20
        # De bron is door backup en restore niet aangeraakt.
        assert _read_all(bron_met_open_writer) == verwacht

    def test_restore_weigert_beschadigde_backup(
        self, tmp_path: Path, bron_met_open_writer: Path
    ):
        backup = tmp_path / "backup.db"
        create_verified_backup(bron_met_open_writer, backup)
        beschadigd = tmp_path / "beschadigd.db"
        shutil.copyfile(backup, beschadigd)
        _corrupt_second_page(beschadigd)

        with pytest.raises(BackupError) as excinfo:
            sqlite_backup.verify_backup_file(beschadigd)
        assert excinfo.value.reason == "integrity_check_failed"

        hersteld = tmp_path / "hersteld.db"
        with pytest.raises(BackupError):
            create_verified_backup(beschadigd, hersteld)
        assert not hersteld.exists()
        assert not any(
            sqlite_backup.STAGING_MARKER in p.name for p in tmp_path.iterdir()
        )

    def test_restore_weigert_backup_met_onvolledig_kernschema(
        self, tmp_path: Path, bron_met_open_writer: Path
    ):
        backup = tmp_path / "backup.db"
        create_verified_backup(bron_met_open_writer, backup)
        onvolledig = tmp_path / "onvolledig.db"
        shutil.copyfile(backup, onvolledig)
        conn = sqlite3.connect(str(onvolledig))
        try:
            conn.execute("DROP TABLE definitie_voorbeelden")
            conn.commit()
        finally:
            conn.close()

        with pytest.raises(BackupError) as excinfo:
            sqlite_backup.verify_backup_file(onvolledig)
        assert excinfo.value.reason == "core_schema_incomplete"

        hersteld = tmp_path / "hersteld.db"
        with pytest.raises(BackupError) as excinfo:
            create_verified_backup(onvolledig, hersteld)
        assert excinfo.value.reason == "core_schema_incomplete"
        assert not hersteld.exists()

    def test_onderbreking_voor_publicatie_laat_geen_eindbestand_achter(
        self,
        tmp_path: Path,
        bron_met_open_writer: Path,
        monkeypatch: pytest.MonkeyPatch,
    ):
        backup_dir = tmp_path / "backups"
        backup_dir.mkdir()
        backup = backup_dir / "backup.db"
        original_copy = sqlite_backup._copy_snapshot

        def copy_then_interrupt(source_conn, staging, *args, **kwargs):
            original_copy(source_conn, staging, *args, **kwargs)
            raise KeyboardInterrupt

        monkeypatch.setattr(sqlite_backup, "_copy_snapshot", copy_then_interrupt)

        with pytest.raises(KeyboardInterrupt):
            create_verified_backup(bron_met_open_writer, backup)

        assert not backup.exists()
        assert list(backup_dir.iterdir()) == []
        # De bron blijft beschrijfbaar: geen achtergebleven leestransactie.
        writer = sqlite3.connect(str(bron_met_open_writer), timeout=1.0)
        try:
            writer.execute(
                "INSERT INTO definitie_tags (definitie_id, tag_naam) VALUES (2, 'na')"
            )
            writer.commit()
        finally:
            writer.close()
