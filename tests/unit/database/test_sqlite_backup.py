"""Regressietests voor de gedeelde WAL-veilige SQLite-backuphelper (DEF-663).

Dekt de acceptatiecriteria van de story en de Codex-bevindingen op de helper:
één consistente read-snapshot, begrensde contention, padweigering inclusief
symlinks in bovenliggende mappen, het publicatiecommitpunt versus
stagingcleanup, een manifest met bijzondere identifiers en het sluiten van
alle verbindingen op foutpaden. Alles draait op synthetische databases in
``tmp_path``; de echte ``data/definities.db`` wordt nooit aangeraakt.
"""

from __future__ import annotations

import logging
import os
import sqlite3
import threading
import time
from pathlib import Path

import pytest

from database import sqlite_backup
from database.sqlite_backup import (
    BackupError,
    SchemaManifest,
    create_verified_backup,
    read_manifest,
)

pytestmark = [pytest.mark.unit]

# Minimale kernschema-bron: alle tabellen/kolommen uit CORE_TABLE_COLUMNS,
# met AUTOINCREMENT zodat ook het interne sqlite_sequence-object ontstaat.
CORE_SCHEMA_SQL = """
CREATE TABLE definities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    begrip TEXT NOT NULL,
    definitie TEXT NOT NULL
);
CREATE TABLE definitie_geschiedenis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    definitie_id INTEGER NOT NULL REFERENCES definities(id),
    wijziging_type TEXT NOT NULL
);
CREATE TABLE definitie_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    definitie_id INTEGER NOT NULL REFERENCES definities(id),
    tag_naam TEXT NOT NULL
);
CREATE TABLE definitie_voorbeelden (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    definitie_id INTEGER NOT NULL REFERENCES definities(id),
    voorbeeld_tekst TEXT NOT NULL
);
CREATE TABLE synonym_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_term TEXT NOT NULL UNIQUE
);
CREATE TABLE synonym_group_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL REFERENCES synonym_groups(id),
    term TEXT NOT NULL
);
CREATE TABLE import_export_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operatie_type TEXT NOT NULL
);
"""

SAMPLE_ROWS_SQL = """
INSERT INTO definities (begrip, definitie) VALUES ('verificatie', 'controleren');
INSERT INTO definities (begrip, definitie) VALUES ('registratie', 'vastleggen');
INSERT INTO definitie_geschiedenis (definitie_id, wijziging_type) VALUES (1, 'created');
INSERT INTO definitie_tags (definitie_id, tag_naam) VALUES (1, 'prioriteit');
INSERT INTO definitie_voorbeelden (definitie_id, voorbeeld_tekst) VALUES (2, 'vb');
INSERT INTO synonym_groups (canonical_term) VALUES ('verificatie');
INSERT INTO synonym_group_members (group_id, term) VALUES (1, 'controle');
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _build_source(path: Path, *, schema: str = CORE_SCHEMA_SQL, rows: bool = True):
    conn = sqlite3.connect(str(path))
    try:
        conn.executescript(schema)
        if rows:
            conn.executescript(SAMPLE_ROWS_SQL)
    finally:
        conn.close()


def _query(path: Path, sql: str) -> list[tuple]:
    conn = sqlite3.connect(str(path))
    try:
        return conn.execute(sql).fetchall()
    finally:
        conn.close()


def _staging_artefacts(directory: Path) -> list[str]:
    return sorted(
        p.name for p in directory.iterdir() if sqlite_backup.STAGING_MARKER in p.name
    )


def _corrupt_second_page(path: Path) -> None:
    """Overschrijf pagina 2 zodat integrity_check niet langer exact 'ok' geeft."""
    header = path.read_bytes()[:100]
    page_size = int.from_bytes(header[16:18], "big") or 4096
    with path.open("r+b") as handle:
        handle.seek(page_size)
        handle.write(b"\xff" * page_size)


def _wal_writer(path: Path) -> sqlite3.Connection:
    """Schrijver in WAL-modus zonder automatische checkpoints."""
    writer = sqlite3.connect(str(path))
    writer.execute("PRAGMA journal_mode=WAL")
    writer.execute("PRAGMA wal_autocheckpoint=0")
    return writer


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def source(tmp_path: Path) -> Path:
    source_dir = tmp_path / "bron"
    source_dir.mkdir()
    path = source_dir / "definities.db"
    _build_source(path)
    return path


@pytest.fixture
def backups_dir(tmp_path: Path) -> Path:
    path = tmp_path / "backups"
    path.mkdir()
    return path


@pytest.fixture
def destination(backups_dir: Path) -> Path:
    return backups_dir / "backup.db"


# ===========================================================================
# 1. Succes en snapshotconsistentie
# ===========================================================================
class TestGeverifieerdePublicatie:
    def test_publiceert_alleen_het_doelbestand(
        self, source: Path, destination: Path, backups_dir: Path
    ):
        manifest = create_verified_backup(source, destination)

        assert isinstance(manifest, SchemaManifest)
        assert dict(manifest.row_counts)["definities"] == 2
        assert _query(destination, "SELECT begrip FROM definities ORDER BY id") == [
            ("verificatie",),
            ("registratie",),
        ]
        assert _query(destination, "PRAGMA integrity_check") == [("ok",)]
        # Geen staging-, wal- of shm-bijbestanden naast de gepubliceerde backup.
        assert sorted(p.name for p in backups_dir.iterdir()) == ["backup.db"]

    def test_backup_bevat_ongecheckpointte_wal_commit(
        self, source: Path, destination: Path
    ):
        writer = _wal_writer(source)
        try:
            writer.execute(
                "INSERT INTO definities (begrip, definitie) "
                "VALUES ('wal-alleen', 'staat alleen in de WAL')"
            )
            writer.commit()
            assert (source.parent / f"{source.name}-wal").stat().st_size > 0

            create_verified_backup(source, destination)
        finally:
            writer.close()

        assert _query(
            destination, "SELECT definitie FROM definities WHERE begrip='wal-alleen'"
        ) == [("staat alleen in de WAL",)]

    def test_backup_zonder_wal_bijbestanden(self, source: Path, destination: Path):
        """De backup is één zelfstandig bestand, ook als de bron in WAL-modus staat."""
        writer = _wal_writer(source)
        try:
            writer.execute(
                "INSERT INTO definities (begrip, definitie) VALUES ('a','b')"
            )
            writer.commit()
            create_verified_backup(source, destination)
        finally:
            writer.close()

        assert _query(destination, "PRAGMA journal_mode") != [("wal",)]
        assert sorted(p.name for p in destination.parent.iterdir()) == ["backup.db"]

    def test_manifest_en_backup_komen_uit_dezelfde_snapshot(
        self, source: Path, destination: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """Een commit tijdens het kopiëren zit noch in het manifest noch in de backup."""
        writer = _wal_writer(source)
        writer.close()
        original_copy = sqlite_backup._copy_snapshot

        def commit_then_copy(source_conn, staging, *args, **kwargs):
            late = sqlite3.connect(str(source))
            try:
                late.execute(
                    "INSERT INTO definities (begrip, definitie) VALUES ('laat', 'x')"
                )
                late.commit()
            finally:
                late.close()
            return original_copy(source_conn, staging, *args, **kwargs)

        monkeypatch.setattr(sqlite_backup, "_copy_snapshot", commit_then_copy)

        manifest = create_verified_backup(source, destination)

        assert dict(manifest.row_counts)["definities"] == 2
        assert _query(destination, "SELECT COUNT(*) FROM definities") == [(2,)]
        assert _query(source, "SELECT COUNT(*) FROM definities") == [(3,)]

    def test_bron_snapshot_weigert_schrijven(self, source: Path):
        conn = sqlite_backup.open_readonly_snapshot(source)
        try:
            with pytest.raises(sqlite3.OperationalError, match="readonly"):
                conn.execute(
                    "INSERT INTO definities (begrip, definitie) VALUES ('w','x')"
                )
        finally:
            conn.close()
        assert _query(source, "SELECT COUNT(*) FROM definities") == [(2,)]

    def test_laat_vreemd_stagingartefact_van_eerdere_onderbreking_staan(
        self, source: Path, destination: Path, backups_dir: Path
    ):
        stale = backups_dir / f"backup.db{sqlite_backup.STAGING_MARKER}oud"
        stale.write_bytes(b"onderbroken")

        create_verified_backup(source, destination)

        assert destination.exists()
        assert stale.read_bytes() == b"onderbroken"


# ===========================================================================
# 2. Padweigering
# ===========================================================================
class TestPadweigering:
    @staticmethod
    def _assert_geweigerd(source: Path, destination: Path, reason: str) -> None:
        with pytest.raises(BackupError) as excinfo:
            create_verified_backup(source, destination)
        assert excinfo.value.reason == reason
        assert not destination.exists()
        assert not destination.is_symlink()
        if destination.parent.is_dir():
            assert _staging_artefacts(destination.parent) == []

    def test_bron_ontbreekt(self, tmp_path: Path, destination: Path):
        self._assert_geweigerd(tmp_path / "geen.db", destination, "source_missing")

    def test_bron_is_directory(self, tmp_path: Path, destination: Path):
        self._assert_geweigerd(tmp_path, destination, "source_not_a_file")

    def test_bron_is_symlink(self, source: Path, destination: Path):
        alias = source.parent / "alias.db"
        alias.symlink_to(source)
        self._assert_geweigerd(alias, destination, "source_symlink")

    def test_bron_via_symlink_in_bovenliggende_map(
        self, tmp_path: Path, source: Path, destination: Path
    ):
        alias_dir = tmp_path / "alias-bron"
        alias_dir.symlink_to(source.parent, target_is_directory=True)
        self._assert_geweigerd(alias_dir / source.name, destination, "source_symlink")

    def test_doel_bestaat_al(self, source: Path, destination: Path):
        destination.write_bytes(b"bestaande backup")
        with pytest.raises(BackupError) as excinfo:
            create_verified_backup(source, destination)
        assert excinfo.value.reason == "destination_exists"
        assert destination.read_bytes() == b"bestaande backup"
        assert _staging_artefacts(destination.parent) == []

    def test_doel_is_symlink(self, source: Path, destination: Path):
        destination.symlink_to(source.parent / "elders.db")
        with pytest.raises(BackupError) as excinfo:
            create_verified_backup(source, destination)
        assert excinfo.value.reason == "destination_symlink"
        assert not (source.parent / "elders.db").exists()

    def test_doel_via_symlink_in_bovenliggende_map(
        self, tmp_path: Path, source: Path, backups_dir: Path
    ):
        alias_dir = tmp_path / "alias-backups"
        alias_dir.symlink_to(backups_dir, target_is_directory=True)
        self._assert_geweigerd(source, alias_dir / "backup.db", "destination_symlink")
        assert list(backups_dir.iterdir()) == []

    def test_doel_is_bestaande_directory(self, source: Path, backups_dir: Path):
        with pytest.raises(BackupError) as excinfo:
            create_verified_backup(source, backups_dir)
        assert excinfo.value.reason == "destination_exists"
        assert backups_dir.is_dir()
        assert list(backups_dir.iterdir()) == []

    def test_doelmap_ontbreekt(self, source: Path, tmp_path: Path):
        self._assert_geweigerd(
            source, tmp_path / "nergens" / "backup.db", "destination_dir_missing"
        )

    def test_bron_is_doel(self, source: Path):
        with pytest.raises(BackupError) as excinfo:
            create_verified_backup(source, source)
        assert excinfo.value.reason == "source_is_destination"
        assert _query(source, "SELECT COUNT(*) FROM definities") == [(2,)]
        assert _staging_artefacts(source.parent) == []

    @pytest.mark.parametrize(
        ("onveilige_bron", "onveilig_doel"),
        [
            (Path("data/*.db"), Path("backups/*.db")),
            (Path("data/definities?.db"), Path("backups/backup?.db")),
            (Path("file:definities.db"), Path("file:backup.db")),
        ],
        ids=["glob-ster", "glob-vraagteken", "uri-schema"],
    )
    def test_onveilige_padtekst(
        self,
        source: Path,
        destination: Path,
        onveilige_bron: Path,
        onveilig_doel: Path,
    ):
        self._assert_geweigerd(source, onveilig_doel, "unsafe_path")
        self._assert_geweigerd(onveilige_bron, destination, "unsafe_path")


# ===========================================================================
# 3. Schema en manifest
# ===========================================================================
class TestSchemaEnManifest:
    def test_kernschema_incompleet_wordt_geweigerd(
        self, tmp_path: Path, destination: Path
    ):
        onvolledig = tmp_path / "onvolledig.db"
        schema = CORE_SCHEMA_SQL.replace(
            "CREATE TABLE definitie_voorbeelden", "CREATE TABLE vb_zonder_kern"
        )
        _build_source(onvolledig, schema=schema, rows=False)

        with pytest.raises(BackupError) as excinfo:
            create_verified_backup(onvolledig, destination)
        assert excinfo.value.reason == "core_schema_incomplete"
        assert not destination.exists()
        assert _staging_artefacts(destination.parent) == []

    def test_kernkolom_ontbreekt_wordt_geweigerd(
        self, tmp_path: Path, destination: Path
    ):
        zonder_kolom = tmp_path / "zonder_kolom.db"
        schema = CORE_SCHEMA_SQL.replace("canonical_term TEXT", "andere_term TEXT")
        _build_source(zonder_kolom, schema=schema, rows=False)

        with pytest.raises(BackupError) as excinfo:
            create_verified_backup(zonder_kolom, destination)
        assert excinfo.value.reason == "core_schema_incomplete"
        assert not destination.exists()

    def test_manifest_dekt_tabel_met_sqlite_prefix_zonder_underscore(
        self, source: Path, destination: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """'sqliteXextra' is een geldige gebruikerstabel; LIKE 'sqlite_%' laat hem weg."""
        conn = sqlite3.connect(str(source))
        try:
            conn.execute("CREATE TABLE sqliteXextra (id INTEGER PRIMARY KEY)")
            conn.execute("INSERT INTO sqliteXextra (id) VALUES (7)")
            conn.commit()
        finally:
            conn.close()
        original_copy = sqlite_backup._copy_snapshot

        def copy_then_drop(source_conn, staging, *args, **kwargs):
            original_copy(source_conn, staging, *args, **kwargs)
            staged = sqlite3.connect(str(staging))
            try:
                staged.execute("DROP TABLE sqliteXextra")
                staged.commit()
            finally:
                staged.close()

        monkeypatch.setattr(sqlite_backup, "_copy_snapshot", copy_then_drop)

        with pytest.raises(BackupError) as excinfo:
            create_verified_backup(source, destination)
        assert excinfo.value.reason == "manifest_mismatch"
        assert not destination.exists()
        assert _staging_artefacts(destination.parent) == []

    def test_gequote_identifier_en_alle_objecttypen_in_manifest(
        self, source: Path, destination: Path
    ):
        conn = sqlite3.connect(str(source))
        try:
            conn.executescript("""
                CREATE TABLE "extra""naam" (id INTEGER PRIMARY KEY, waarde TEXT);
                INSERT INTO "extra""naam" (waarde) VALUES ('q');
                CREATE TABLE sqliteXextra (id INTEGER PRIMARY KEY);
                CREATE INDEX idx_definities_begrip ON definities(begrip);
                CREATE VIEW actieve_definities AS SELECT begrip FROM definities;
                CREATE TRIGGER trg_geschiedenis AFTER INSERT ON definities
                BEGIN
                    INSERT INTO definitie_geschiedenis (definitie_id, wijziging_type)
                    VALUES (NEW.id, 'created');
                END;
                """)
        finally:
            conn.close()

        manifest = create_verified_backup(source, destination)

        namen = {(kind, name) for kind, name, _tbl, _sql in manifest.objects}
        assert ("table", 'extra"naam') in namen
        assert ("table", "sqliteXextra") in namen
        assert ("index", "idx_definities_begrip") in namen
        assert ("view", "actieve_definities") in namen
        assert ("trigger", "trg_geschiedenis") in namen
        assert manifest.tables()['extra"naam'] == ("id", "waarde")
        assert dict(manifest.row_counts)['extra"naam'] == 1
        assert _query(destination, 'SELECT waarde FROM "extra""naam"') == [("q",)]

    def test_manifest_sluit_interne_sqlite_objecten_uit(self, source: Path):
        conn = sqlite_backup.open_readonly_snapshot(source)
        try:
            manifest = read_manifest(conn)
        finally:
            conn.close()
        assert all(
            not name.lower().startswith("sqlite_")
            for _k, name, _t, _s in manifest.objects
        )
        assert manifest.schema_version is None

    def test_schema_version_wordt_meegenomen_als_aanwezig(
        self, source: Path, destination: Path
    ):
        conn = sqlite3.connect(str(source))
        try:
            conn.executescript(
                "CREATE TABLE schema_version (id INTEGER PRIMARY KEY, version INTEGER);"
                "INSERT INTO schema_version (version) VALUES (1);"
                "INSERT INTO schema_version (version) VALUES (3);"
            )
        finally:
            conn.close()
        manifest = create_verified_backup(source, destination)
        assert manifest.schema_version == 3
        assert _query(destination, "SELECT MAX(version) FROM schema_version") == [(3,)]


# ===========================================================================
# 4. Verificatie vóór publicatie en de gedeelde verifier
# ===========================================================================
class TestVerificatieVoorPublicatie:
    def test_corruptie_voor_publicatie_laat_geen_eindbestand_achter(
        self, source: Path, destination: Path, monkeypatch: pytest.MonkeyPatch
    ):
        original_copy = sqlite_backup._copy_snapshot

        def copy_then_corrupt(source_conn, staging, *args, **kwargs):
            original_copy(source_conn, staging, *args, **kwargs)
            _corrupt_second_page(Path(staging))

        monkeypatch.setattr(sqlite_backup, "_copy_snapshot", copy_then_corrupt)

        with pytest.raises(BackupError) as excinfo:
            create_verified_backup(source, destination)
        assert excinfo.value.reason == "integrity_check_failed"
        assert not destination.exists()
        assert _staging_artefacts(destination.parent) == []

    def test_verify_backup_file_geeft_manifest_van_geldige_backup(
        self, source: Path, destination: Path
    ):
        manifest = create_verified_backup(source, destination)
        assert sqlite_backup.verify_backup_file(destination) == manifest
        assert sqlite_backup.verify_backup_file(destination, manifest) == manifest

    def test_verify_backup_file_weigert_niet_sqlite_bestand(self, tmp_path: Path):
        rommel = tmp_path / "rommel.db"
        rommel.write_text("geen database")
        with pytest.raises(BackupError) as excinfo:
            sqlite_backup.verify_backup_file(rommel)
        assert excinfo.value.reason == "integrity_check_failed"

    def test_verify_backup_file_weigert_ontbrekend_bestand(self, tmp_path: Path):
        with pytest.raises(BackupError) as excinfo:
            sqlite_backup.verify_backup_file(tmp_path / "weg.db")
        assert excinfo.value.reason == "backup_unreadable"

    def test_verify_backup_file_weigert_onvolledig_kernschema(self, tmp_path: Path):
        db = tmp_path / "unrelated.db"
        _build_source(db, schema="CREATE TABLE unrelated (id INTEGER);", rows=False)
        with pytest.raises(BackupError) as excinfo:
            sqlite_backup.verify_backup_file(db)
        assert excinfo.value.reason == "core_schema_incomplete"

    def test_verify_backup_file_weigert_afwijkend_manifest(
        self, source: Path, destination: Path
    ):
        manifest = create_verified_backup(source, destination)
        conn = sqlite3.connect(str(source))
        try:
            conn.execute("INSERT INTO definities (begrip, definitie) VALUES ('x','y')")
            conn.commit()
        finally:
            conn.close()
        bron_conn = sqlite_backup.open_readonly_snapshot(source)
        try:
            gewijzigd = read_manifest(bron_conn)
        finally:
            bron_conn.close()
        assert gewijzigd != manifest
        with pytest.raises(BackupError) as excinfo:
            sqlite_backup.verify_backup_file(destination, gewijzigd)
        assert excinfo.value.reason == "manifest_mismatch"


# ===========================================================================
# 5. Begrensde contention
# ===========================================================================
class TestBegrensdeContention:
    def test_vergrendelde_staging_eindigt_binnen_deadline(
        self, source: Path, destination: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """Een exclusieve lock op het stagingbestand mag de backup niet laten hangen."""
        lockers: list[sqlite3.Connection] = []
        original_make_staging = sqlite_backup.make_staging

        def locked_staging(dest: Path) -> Path:
            staging = original_make_staging(dest)
            locker = sqlite3.connect(
                str(staging), isolation_level=None, check_same_thread=False
            )
            locker.execute("BEGIN EXCLUSIVE")
            lockers.append(locker)
            return staging

        monkeypatch.setattr(sqlite_backup, "make_staging", locked_staging)
        monkeypatch.setattr(
            sqlite_backup, "DEFAULT_DEADLINE_SECONDS", 0.5, raising=False
        )
        outcome: dict[str, object] = {}

        def run() -> None:
            try:
                outcome["result"] = create_verified_backup(source, destination)
            except BaseException as exc:  # uitkomst wordt hieronder getoetst
                outcome["error"] = exc

        worker = threading.Thread(target=run, daemon=True)
        started = time.monotonic()
        worker.start()
        worker.join(timeout=5.0)
        ended_in_time = not worker.is_alive()
        elapsed = time.monotonic() - started
        for locker in lockers:
            locker.close()
        worker.join(timeout=30.0)

        assert ended_in_time, f"backup hing nog na {elapsed:.1f}s ondanks contention"
        error = outcome.get("error")
        assert isinstance(error, BackupError), outcome
        assert error.reason == "backup_timeout"
        assert not destination.exists()
        assert _staging_artefacts(destination.parent) == []

    def test_vergrendelde_bron_faalt_begrensd(
        self, source: Path, destination: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """Rollback-journal-bron onder exclusieve lock: begrensd falen, geen doel.

        De lockwachttijd is begrensd op het totale budget; als de bron het hele
        budget vergrendeld blijft, is het verlopen budget de classificatie.
        """
        monkeypatch.setattr(
            sqlite_backup, "DEFAULT_DEADLINE_SECONDS", 0.5, raising=False
        )
        locker = sqlite3.connect(str(source), isolation_level=None)
        locker.execute("BEGIN EXCLUSIVE")
        try:
            started = time.monotonic()
            with pytest.raises(BackupError) as excinfo:
                create_verified_backup(source, destination)
            elapsed = time.monotonic() - started
        finally:
            locker.close()

        assert excinfo.value.reason == "backup_timeout"
        assert elapsed < 4.0
        assert not destination.exists()
        assert _staging_artefacts(destination.parent) == []


# ===========================================================================
# 6. Publicatiecommitpunt versus stagingcleanup
# ===========================================================================
def _unlink_dat_staging_weigert(monkeypatch: pytest.MonkeyPatch) -> None:
    real_unlink = os.unlink

    def failing_unlink(path, *args, **kwargs):
        if sqlite_backup.STAGING_MARKER in os.fspath(path):
            raise PermissionError(1, "cleanup geweigerd")
        return real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(os, "unlink", failing_unlink)


class TestPublicatieCommitpunt:
    def test_cleanupfout_na_publicatie_is_eerlijk_succes(
        self,
        source: Path,
        destination: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ):
        _unlink_dat_staging_weigert(monkeypatch)
        caplog.set_level(logging.WARNING, logger="database.sqlite_backup")

        manifest = create_verified_backup(source, destination)

        assert destination.exists()
        assert sqlite_backup.verify_backup_file(destination, manifest) == manifest
        assert _staging_artefacts(destination.parent) != []
        warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert warnings, "cleanupfout moet als waarschuwing gelogd worden"
        assert any("staging_cleanup_failed" in r.getMessage() for r in warnings)
        assert all(
            str(destination.parent) not in r.getMessage() for r in caplog.records
        )
        assert not any(r.levelno >= logging.ERROR for r in caplog.records)

    def test_cleanupfout_maskeert_oorspronkelijke_fout_niet(
        self, source: Path, destination: Path, monkeypatch: pytest.MonkeyPatch
    ):
        original_copy = sqlite_backup._copy_snapshot

        def copy_then_corrupt(source_conn, staging, *args, **kwargs):
            original_copy(source_conn, staging, *args, **kwargs)
            _corrupt_second_page(Path(staging))

        monkeypatch.setattr(sqlite_backup, "_copy_snapshot", copy_then_corrupt)
        _unlink_dat_staging_weigert(monkeypatch)

        with pytest.raises(BackupError) as excinfo:
            create_verified_backup(source, destination)

        assert excinfo.value.reason == "integrity_check_failed"
        assert not destination.exists()

    def test_publicatie_weigert_doel_dat_intussen_verscheen(
        self, source: Path, destination: Path, monkeypatch: pytest.MonkeyPatch
    ):
        original_copy = sqlite_backup._copy_snapshot

        def copy_then_claim_destination(source_conn, staging, *args, **kwargs):
            original_copy(source_conn, staging, *args, **kwargs)
            destination.write_bytes(b"race")

        monkeypatch.setattr(
            sqlite_backup, "_copy_snapshot", copy_then_claim_destination
        )

        with pytest.raises(BackupError) as excinfo:
            create_verified_backup(source, destination)
        assert excinfo.value.reason == "destination_exists"
        assert destination.read_bytes() == b"race"
        assert _staging_artefacts(destination.parent) == []


# ===========================================================================
# 7. Verbindingen en logging
# ===========================================================================
class TestVerbindingenEnLogging:
    @staticmethod
    def _assert_alle_gesloten(connections: list[sqlite3.Connection]) -> None:
        assert connections, "er zijn geen verbindingen geregistreerd"
        for conn in connections:
            with pytest.raises(sqlite3.ProgrammingError):
                conn.execute("SELECT 1")

    def test_alle_verbindingen_gesloten_bij_fout(
        self, source: Path, destination: Path, monkeypatch: pytest.MonkeyPatch
    ):
        original_copy = sqlite_backup._copy_snapshot

        def copy_then_corrupt(source_conn, staging, *args, **kwargs):
            original_copy(source_conn, staging, *args, **kwargs)
            _corrupt_second_page(Path(staging))

        monkeypatch.setattr(sqlite_backup, "_copy_snapshot", copy_then_corrupt)
        real_connect = sqlite3.connect
        opened: list[sqlite3.Connection] = []

        def recording_connect(*args, **kwargs):
            conn = real_connect(*args, **kwargs)
            opened.append(conn)
            return conn

        with monkeypatch.context() as patch:
            patch.setattr(sqlite_backup.sqlite3, "connect", recording_connect)
            with pytest.raises(BackupError):
                create_verified_backup(source, destination)

        assert len(opened) >= 3  # bron, stagingdoel, verificatie
        self._assert_alle_gesloten(opened)

    def test_alle_verbindingen_gesloten_bij_succes(
        self, source: Path, destination: Path, monkeypatch: pytest.MonkeyPatch
    ):
        real_connect = sqlite3.connect
        opened: list[sqlite3.Connection] = []

        def recording_connect(*args, **kwargs):
            conn = real_connect(*args, **kwargs)
            opened.append(conn)
            return conn

        with monkeypatch.context() as patch:
            patch.setattr(sqlite_backup.sqlite3, "connect", recording_connect)
            create_verified_backup(source, destination)

        self._assert_alle_gesloten(opened)

    def test_kopieerfout_sluit_bron_en_laat_niets_achter(
        self, source: Path, destination: Path, monkeypatch: pytest.MonkeyPatch
    ):
        def kapotte_kopie(*_args, **_kwargs):
            raise sqlite3.OperationalError("disk I/O error")

        monkeypatch.setattr(sqlite_backup, "_copy_snapshot", kapotte_kopie)
        real_connect = sqlite3.connect
        opened: list[sqlite3.Connection] = []

        def recording_connect(*args, **kwargs):
            conn = real_connect(*args, **kwargs)
            opened.append(conn)
            return conn

        with monkeypatch.context() as patch:
            patch.setattr(sqlite_backup.sqlite3, "connect", recording_connect)
            with pytest.raises(BackupError) as excinfo:
                create_verified_backup(source, destination)

        assert excinfo.value.reason == "copy_failed"
        assert not destination.exists()
        assert _staging_artefacts(destination.parent) == []
        self._assert_alle_gesloten(opened)

    def test_foutlog_bevat_alleen_de_classificatie(
        self, source: Path, destination: Path, caplog: pytest.LogCaptureFixture
    ):
        destination.write_bytes(b"x")
        caplog.set_level(logging.ERROR, logger="database.sqlite_backup")
        with pytest.raises(BackupError):
            create_verified_backup(source, destination)
        berichten = [r.getMessage() for r in caplog.records]
        assert any("destination_exists" in m for m in berichten)
        assert all(str(destination.parent) not in m for m in berichten)


# ===========================================================================
# 8. CLI
# ===========================================================================
class TestCli:
    def test_succes_geeft_exit_0(self, source: Path, destination: Path):
        assert sqlite_backup.main([str(source), str(destination)]) == 0
        assert _query(destination, "SELECT COUNT(*) FROM definities") == [(2,)]

    def test_weigering_geeft_exit_1_met_alleen_reden(
        self, source: Path, destination: Path, capsys: pytest.CaptureFixture[str]
    ):
        destination.write_bytes(b"bestaand")
        with pytest.raises(SystemExit) as excinfo:
            sqlite_backup.main([str(source), str(destination)])
        assert excinfo.value.code == 1
        err = capsys.readouterr().err
        assert "sqlite_backup: destination_exists" in err
        assert str(destination.parent) not in err
        assert destination.read_bytes() == b"bestaand"


# ===========================================================================
# 9. Totale deadline: manifest, verificatie en geen late publicatie
#    (deterministisch via een geïnjecteerde monotone klok, geen wallclock)
# ===========================================================================
class _Klok:
    def __init__(self, start: float = 1000.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now


class TestTotaleDeadline:
    def test_verlopen_deadline_na_manifestlezen_maakt_geen_staging(
        self, source: Path, destination: Path, monkeypatch: pytest.MonkeyPatch
    ):
        klok = _Klok()
        monkeypatch.setattr(sqlite_backup, "_monotonic", klok)
        original_read_manifest = sqlite_backup.read_manifest

        def trage_manifestlezer(conn):
            manifest = original_read_manifest(conn)
            klok.now += 10_000  # de manifestqueries duurden langer dan het budget
            return manifest

        monkeypatch.setattr(sqlite_backup, "read_manifest", trage_manifestlezer)
        staging_aangemaakt: list[Path] = []
        original_make_staging = sqlite_backup.make_staging

        def registrerende_staging(dest: Path) -> Path:
            staging = original_make_staging(dest)
            staging_aangemaakt.append(staging)
            return staging

        monkeypatch.setattr(sqlite_backup, "make_staging", registrerende_staging)

        with pytest.raises(BackupError) as excinfo:
            create_verified_backup(source, destination, deadline_seconds=5.0)

        assert excinfo.value.reason == "backup_timeout"
        assert staging_aangemaakt == []
        assert not destination.exists()

    def test_progress_handler_breekt_lopende_query_af_na_deadline(
        self, source: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """Een lange query op een bewapende verbinding stopt zodra de klok verloopt."""
        klok = _Klok()
        monkeypatch.setattr(sqlite_backup, "_monotonic", klok)
        conn = sqlite_backup.open_readonly_snapshot(source)
        try:
            sqlite_backup._arm_deadline(conn, deadline=klok.now + 1.0)
            assert conn.execute("SELECT COUNT(*) FROM definities").fetchone() == (2,)
            klok.now += 5.0
            with pytest.raises(sqlite3.OperationalError, match="interrupted"):
                conn.execute(
                    "WITH RECURSIVE c(x) AS (SELECT 1 UNION ALL SELECT x + 1 FROM c "
                    "WHERE x < 200000) SELECT COUNT(*) FROM c"
                ).fetchone()
        finally:
            conn.close()

    def test_verify_backup_file_respecteert_deadline(
        self, source: Path, destination: Path, monkeypatch: pytest.MonkeyPatch
    ):
        manifest = create_verified_backup(source, destination)
        klok = _Klok()
        monkeypatch.setattr(sqlite_backup, "_monotonic", klok)

        geldig = sqlite_backup.verify_backup_file(
            destination, manifest, deadline=klok.now + 60.0
        )
        assert geldig == manifest
        with pytest.raises(BackupError) as excinfo:
            sqlite_backup.verify_backup_file(
                destination, manifest, deadline=klok.now - 1.0
            )
        assert excinfo.value.reason == "backup_timeout"

    def test_verifier_lockwacht_is_begrensd_op_resterend_budget(
        self, source: Path, destination: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """Een exclusief vergrendelde backup mag de verifier niet 5s laten wachten.

        Budget 0,2s; bovengrens 2s ligt ruim onder de oude busy-timeout van 5s.
        """
        create_verified_backup(source, destination)
        locker = sqlite3.connect(str(destination), isolation_level=None)
        locker.execute("BEGIN EXCLUSIVE")
        real_connect = sqlite3.connect
        opened: list[sqlite3.Connection] = []

        def recording_connect(*args, **kwargs):
            conn = real_connect(*args, **kwargs)
            opened.append(conn)
            return conn

        try:
            started = time.monotonic()
            with monkeypatch.context() as patch:
                patch.setattr(sqlite_backup.sqlite3, "connect", recording_connect)
                with pytest.raises(BackupError) as excinfo:
                    sqlite_backup.verify_backup_file(
                        destination, deadline=sqlite_backup._monotonic() + 0.2
                    )
            elapsed = time.monotonic() - started
        finally:
            locker.close()

        assert excinfo.value.reason == "backup_timeout"
        assert elapsed < 2.0, f"verifier wachtte {elapsed:.2f}s op de lock"
        assert opened, "de verifier moet een verbinding geopend hebben"
        for conn in opened:
            with pytest.raises(sqlite3.ProgrammingError):
                conn.execute("SELECT 1")

    def test_bronlockwacht_gebruikt_resterend_budget_niet_volledig_budget(
        self, source: Path, destination: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """Budget 5s, waarvan 4,95s al verbruikt vóór het openen van de bron.

        De busy-timeout van de bron moet dan hoogstens de resterende 0,05s zijn,
        niet opnieuw min(5s, 5s). Verbruikte tijd wordt met een verschoven klok
        gesimuleerd; de echte lockwacht blijft daardoor ver onder 2s.
        """
        offset = [0.0]
        monkeypatch.setattr(
            sqlite_backup, "_monotonic", lambda: time.monotonic() + offset[0]
        )
        original_validate = sqlite_backup._validate_paths

        def trage_validatie(src: Path, dst: Path) -> None:
            original_validate(src, dst)
            offset[0] += 4.95  # het budget is bijna op vóór het openen van de bron

        monkeypatch.setattr(sqlite_backup, "_validate_paths", trage_validatie)
        locker = sqlite3.connect(str(source), isolation_level=None)
        locker.execute("BEGIN EXCLUSIVE")
        try:
            started = time.monotonic()
            with pytest.raises(BackupError) as excinfo:
                create_verified_backup(source, destination, deadline_seconds=5.0)
            elapsed = time.monotonic() - started
        finally:
            locker.close()

        assert excinfo.value.reason == "backup_timeout"
        assert elapsed < 2.0, f"bronlockwacht duurde {elapsed:.2f}s"
        assert not destination.exists()
        assert _staging_artefacts(destination.parent) == []

    def test_gedeelde_deadline_utilities_volgen_de_geinjecteerde_klok(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        klok = _Klok(start=100.0)
        monkeypatch.setattr(sqlite_backup, "_monotonic", klok)
        deadline = sqlite_backup.monotonic_now() + 5.0

        assert sqlite_backup.remaining_budget(deadline) == pytest.approx(5.0)
        sqlite_backup.ensure_within_deadline(deadline)
        klok.now += 3.0
        assert sqlite_backup.remaining_budget(deadline) == pytest.approx(2.0)
        klok.now += 3.0
        assert sqlite_backup.remaining_budget(deadline) == 0.0
        with pytest.raises(BackupError) as excinfo:
            sqlite_backup.ensure_within_deadline(deadline)
        assert excinfo.value.reason == "backup_timeout"
        sqlite_backup.ensure_within_deadline(None)  # zonder deadline geen grens

    def test_geen_publicatie_na_verlopen_budget(
        self, source: Path, destination: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """Verificatie slaagt, maar het budget is op: het doel mag niet verschijnen."""
        klok = _Klok()
        monkeypatch.setattr(sqlite_backup, "_monotonic", klok)
        original_verify = sqlite_backup.verify_backup_file

        def trage_verifier(*args, **kwargs):
            manifest = original_verify(*args, **kwargs)
            klok.now += 10_000
            return manifest

        monkeypatch.setattr(sqlite_backup, "verify_backup_file", trage_verifier)

        with pytest.raises(BackupError) as excinfo:
            create_verified_backup(source, destination, deadline_seconds=5.0)

        assert excinfo.value.reason == "backup_timeout"
        assert not destination.exists()
        assert _staging_artefacts(destination.parent) == []
