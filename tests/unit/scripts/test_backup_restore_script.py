"""Tests voor de backupcreatie van ``scripts/backup_restore.py`` (DEF-663).

Alleen ``DatabaseBackupManager.create_backup`` en de verificatie ervan vallen
onder deze story: de backup loopt via de gedeelde WAL-veilige helper, weigert
een bron zonder kernschema en laat bij een fout geen bestand achter. Restore en
retentie blijven buiten scope (DEF-666).

Het script configureert bij import een logbestand onder ``logs/`` relatief aan
de werkmap; de fixture wisselt daarom eerst naar ``tmp_path``.
"""

from __future__ import annotations

import gzip
import importlib.util
import logging
import os
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path
from types import ModuleType

import pytest

pytestmark = [pytest.mark.unit]

STAGING_MARKER = ".staging-"


class _VasteDatetime:
    """Bevroren ``datetime.now()`` zodat twee backups dezelfde bestandsnaam krijgen."""

    @classmethod
    def now(cls) -> datetime:
        return datetime(2026, 9, 5, 12, 0, 0)  # naïef, zoals het script zelf


def _bevries_tijd(monkeypatch: pytest.MonkeyPatch, module: ModuleType) -> None:
    monkeypatch.setattr(module, "datetime", _VasteDatetime)


_SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "backup_restore.py"

CORE_SCHEMA_SQL = """
CREATE TABLE definities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    begrip TEXT NOT NULL,
    definitie TEXT NOT NULL
);
CREATE TABLE definitie_geschiedenis (
    id INTEGER PRIMARY KEY AUTOINCREMENT, definitie_id INTEGER NOT NULL
);
CREATE TABLE definitie_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT, definitie_id INTEGER NOT NULL
);
CREATE TABLE definitie_voorbeelden (
    id INTEGER PRIMARY KEY AUTOINCREMENT, definitie_id INTEGER NOT NULL
);
CREATE TABLE synonym_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT, canonical_term TEXT NOT NULL
);
CREATE TABLE synonym_group_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT, group_id INTEGER NOT NULL, term TEXT NOT NULL
);
CREATE TABLE import_export_logs (id INTEGER PRIMARY KEY AUTOINCREMENT);
INSERT INTO definities (begrip, definitie) VALUES ('verificatie', 'controleren');
"""


@pytest.fixture
def backup_restore(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "logs").mkdir()

    # Het script opent bij import een FileHandler op logs/backup_restore.log;
    # registreer die zodat de fixture hem netjes sluit (geen ResourceWarning).
    handlers: list[logging.FileHandler] = []
    real_file_handler = logging.FileHandler

    class TrackingFileHandler(real_file_handler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            handlers.append(self)

    monkeypatch.setattr(logging, "FileHandler", TrackingFileHandler)
    spec = importlib.util.spec_from_file_location("backup_restore_def663", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module: ModuleType = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        yield module
    finally:
        for handler in handlers:
            logging.getLogger().removeHandler(handler)
            handler.close()


def _maak_db(path: Path, schema: str = CORE_SCHEMA_SQL) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    try:
        conn.executescript(schema)
    finally:
        conn.close()
    return path


def _query(path: Path, sql: str) -> list[tuple]:
    conn = sqlite3.connect(str(path))
    try:
        return conn.execute(sql).fetchall()
    finally:
        conn.close()


def _wal_writer_met_extra_rij(path: Path) -> sqlite3.Connection:
    writer = sqlite3.connect(str(path))
    writer.execute("PRAGMA journal_mode=WAL")
    writer.execute("PRAGMA wal_autocheckpoint=0")
    writer.execute(
        "INSERT INTO definities (begrip, definitie) "
        "VALUES ('wal-alleen', 'staat alleen in de WAL')"
    )
    writer.commit()
    assert (path.parent / f"{path.name}-wal").stat().st_size > 0
    return writer


class TestCreateBackup:
    def test_ongecomprimeerd_behoudt_wal_commit(
        self, tmp_path: Path, backup_restore: ModuleType
    ):
        db = _maak_db(tmp_path / "data" / "definities.db")
        backup_dir = tmp_path / "backups"
        manager = backup_restore.DatabaseBackupManager(
            db_path=str(db), backup_dir=str(backup_dir), compress=False
        )
        writer = _wal_writer_met_extra_rij(db)
        try:
            backup_path = manager.create_backup(description="voor test")
        finally:
            writer.close()

        assert backup_path.parent == backup_dir
        assert backup_path.suffix == ".db"
        assert _query(
            backup_path, "SELECT definitie FROM definities WHERE begrip = 'wal-alleen'"
        ) == [("staat alleen in de WAL",)]
        assert sorted(p.name for p in backup_dir.iterdir()) == [backup_path.name]

    def test_gecomprimeerd_verifieert_en_laat_alleen_gz_achter(
        self, tmp_path: Path, backup_restore: ModuleType
    ):
        db = _maak_db(tmp_path / "data" / "definities.db")
        backup_dir = tmp_path / "backups"
        manager = backup_restore.DatabaseBackupManager(
            db_path=str(db), backup_dir=str(backup_dir), compress=True
        )
        writer = _wal_writer_met_extra_rij(db)
        try:
            backup_path = manager.create_backup()
        finally:
            writer.close()

        assert backup_path.name.endswith(".db.gz")
        assert sorted(p.name for p in backup_dir.iterdir()) == [backup_path.name]
        assert manager.verify_backup(backup_path) is True
        assert sorted(p.name for p in backup_dir.iterdir()) == [backup_path.name]

        uitgepakt = tmp_path / "uitgepakt.db"
        uitgepakt.write_bytes(gzip.decompress(backup_path.read_bytes()))
        assert _query(uitgepakt, "SELECT COUNT(*) FROM definities") == [(2,)]

    def test_bron_zonder_kernschema_wordt_geweigerd_zonder_bestand(
        self, tmp_path: Path, backup_restore: ModuleType
    ):
        schema = CORE_SCHEMA_SQL.replace(
            "CREATE TABLE definitie_voorbeelden", "CREATE TABLE geen_kern"
        )
        db = _maak_db(tmp_path / "data" / "definities.db", schema=schema)
        backup_dir = tmp_path / "backups"
        manager = backup_restore.DatabaseBackupManager(
            db_path=str(db), backup_dir=str(backup_dir), compress=False
        )

        with pytest.raises(RuntimeError, match="core_schema_incomplete"):
            manager.create_backup()

        assert list(backup_dir.iterdir()) == []

    def test_verify_backup_weigert_backup_zonder_kernschema(
        self, tmp_path: Path, backup_restore: ModuleType
    ):
        db = _maak_db(tmp_path / "data" / "definities.db")
        manager = backup_restore.DatabaseBackupManager(
            db_path=str(db), backup_dir=str(tmp_path / "backups"), compress=False
        )
        onvolledig = _maak_db(
            tmp_path / "onvolledig.db", schema="CREATE TABLE unrelated (id INTEGER);"
        )

        assert manager.verify_backup(onvolledig) is False


# ---------------------------------------------------------------------------
# Gecomprimeerde route: no-clobber publicatie en veilige verificatie
# (Codex-herreview bevindingen 1 en 2)
# ---------------------------------------------------------------------------
def _gz_manager(tmp_path: Path, module: ModuleType, *, compress: bool = True):
    db = _maak_db(tmp_path / "data" / "definities.db")
    backup_dir = tmp_path / "backups"
    manager = module.DatabaseBackupManager(
        db_path=str(db), backup_dir=str(backup_dir), compress=compress
    )
    return db, backup_dir, manager


def _inhoud(directory: Path) -> list[str]:
    return sorted(p.name for p in directory.iterdir())


class _Klok:
    """Injecteerbare monotone klok; de helper en het script delen dezelfde klok."""

    def __init__(self, start: float = 1000.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now


class TestGecomprimeerdTijdsbudget:
    """Eén absolute deadline vanaf ``create_backup``-ingang, geen nieuw budget per stap."""

    @staticmethod
    def _klok(monkeypatch: pytest.MonkeyPatch) -> _Klok:
        from database import sqlite_backup

        klok = _Klok()
        monkeypatch.setattr(sqlite_backup, "_monotonic", klok)
        return klok

    def test_budget_verlopen_na_sqlite_backup_publiceert_geen_gz(
        self,
        tmp_path: Path,
        backup_restore: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
    ):
        klok = self._klok(monkeypatch)
        _db, backup_dir, manager = _gz_manager(tmp_path, backup_restore)
        real_create = backup_restore.create_verified_backup

        def trage_sqlite_backup(*args, **kwargs):
            manifest = real_create(*args, **kwargs)
            klok.now += 10_000  # budget verloopt direct ná de SQLite-backup
            return manifest

        monkeypatch.setattr(
            backup_restore, "create_verified_backup", trage_sqlite_backup
        )

        with pytest.raises(RuntimeError, match="backup_timeout"):
            manager.create_backup()

        assert _inhoud(backup_dir) == []

    def test_budget_verlopen_tijdens_compressie_publiceert_geen_gz(
        self,
        tmp_path: Path,
        backup_restore: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
    ):
        klok = self._klok(monkeypatch)
        _db, backup_dir, manager = _gz_manager(tmp_path, backup_restore)
        real_gzip_open = backup_restore.gzip.open

        def gzip_open_dat_tijd_kost(path, mode="rb", *args, **kwargs):
            handle = real_gzip_open(path, mode, *args, **kwargs)
            if mode.startswith("w"):
                klok.now += 10_000  # compressie duurt langer dan het budget
            return handle

        monkeypatch.setattr(backup_restore.gzip, "open", gzip_open_dat_tijd_kost)

        with pytest.raises(RuntimeError, match="backup_timeout"):
            manager.create_backup()

        assert _inhoud(backup_dir) == []

    def test_budget_verlopen_tijdens_decompressie_publiceert_geen_gz(
        self,
        tmp_path: Path,
        backup_restore: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
    ):
        klok = self._klok(monkeypatch)
        _db, backup_dir, manager = _gz_manager(tmp_path, backup_restore)
        real_gzip_open = backup_restore.gzip.open

        def gzip_open_dat_tijd_kost(path, mode="rb", *args, **kwargs):
            handle = real_gzip_open(path, mode, *args, **kwargs)
            if mode.startswith("r"):
                klok.now += 10_000  # terug-decompressie duurt langer dan het budget
            return handle

        monkeypatch.setattr(backup_restore.gzip, "open", gzip_open_dat_tijd_kost)

        with pytest.raises(RuntimeError, match="backup_timeout"):
            manager.create_backup()

        assert _inhoud(backup_dir) == []

    def test_budget_verlopen_na_gedeelde_verificatie_publiceert_geen_gz(
        self,
        tmp_path: Path,
        backup_restore: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
    ):
        klok = self._klok(monkeypatch)
        _db, backup_dir, manager = _gz_manager(tmp_path, backup_restore)
        real_verify = backup_restore.verify_backup_file

        def trage_verifier(*args, **kwargs):
            manifest = real_verify(*args, **kwargs)
            klok.now += 10_000  # verificatie slaagde, maar het budget is op
            return manifest

        monkeypatch.setattr(backup_restore, "verify_backup_file", trage_verifier)

        with pytest.raises(RuntimeError, match="backup_timeout"):
            manager.create_backup()

        assert _inhoud(backup_dir) == []

    def test_sqlite_backup_krijgt_resterend_budget_geen_nieuw_volledig_budget(
        self,
        tmp_path: Path,
        backup_restore: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
    ):
        klok = self._klok(monkeypatch)
        _db, _backup_dir, manager = _gz_manager(tmp_path, backup_restore)
        real_validate = backup_restore.validate_new_destination

        def validatie_die_tijd_kost(path):
            real_validate(path)
            klok.now += 3.0  # 3 s van het budget van 5 s is al verbruikt

        monkeypatch.setattr(
            backup_restore, "validate_new_destination", validatie_die_tijd_kost
        )
        real_create = backup_restore.create_verified_backup
        ontvangen: list[float | None] = []

        def registrerende_create(*args, **kwargs):
            ontvangen.append(kwargs.get("deadline_seconds"))
            return real_create(*args, **kwargs)

        monkeypatch.setattr(
            backup_restore, "create_verified_backup", registrerende_create
        )

        gz = manager.create_backup(deadline_seconds=5.0)

        assert gz.exists()
        assert ontvangen == [pytest.approx(2.0)]

    def test_standaard_budget_zonder_keyword_blijft_werken(
        self, tmp_path: Path, backup_restore: ModuleType
    ):
        _db, backup_dir, manager = _gz_manager(tmp_path, backup_restore)
        gz = manager.create_backup()
        assert _inhoud(backup_dir) == [gz.name]
        assert manager.verify_backup(gz) is True


class TestGecomprimeerdeNoClobber:
    def test_herhaalde_timestamp_overschrijft_bestaande_gz_niet(
        self,
        tmp_path: Path,
        backup_restore: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
    ):
        _bevries_tijd(monkeypatch, backup_restore)
        db, backup_dir, manager = _gz_manager(tmp_path, backup_restore)
        eerste = manager.create_backup()
        origineel = eerste.read_bytes()

        conn = sqlite3.connect(str(db))
        try:
            conn.execute("UPDATE definities SET definitie = 'gewijzigd'")
            conn.commit()
        finally:
            conn.close()

        with pytest.raises(RuntimeError, match="destination_exists"):
            manager.create_backup()

        assert eerste.read_bytes() == origineel
        assert _inhoud(backup_dir) == [eerste.name]

    def test_gz_doel_dat_symlink_is_wordt_geweigerd(
        self,
        tmp_path: Path,
        backup_restore: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
    ):
        _bevries_tijd(monkeypatch, backup_restore)
        _db, backup_dir, manager = _gz_manager(tmp_path, backup_restore)
        doelwit = tmp_path / "elders.db.gz"
        alias = backup_dir / "definities_backup_20260905_120000.db.gz"
        alias.symlink_to(doelwit)

        with pytest.raises(RuntimeError, match="destination_symlink"):
            manager.create_backup()

        assert alias.is_symlink()
        assert not doelwit.exists()
        assert _inhoud(backup_dir) == [alias.name]

    def test_compressiefout_publiceert_niets(
        self,
        tmp_path: Path,
        backup_restore: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
    ):
        _db, backup_dir, manager = _gz_manager(tmp_path, backup_restore)

        def kapotte_gzip_open(*_args, **_kwargs):
            raise OSError(28, "schijf vol")

        monkeypatch.setattr(backup_restore.gzip, "open", kapotte_gzip_open)

        with pytest.raises(RuntimeError, match="compress_failed"):
            manager.create_backup()

        assert _inhoud(backup_dir) == []

    def test_onderbreking_tijdens_compressie_publiceert_niets(
        self,
        tmp_path: Path,
        backup_restore: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
    ):
        _db, backup_dir, manager = _gz_manager(tmp_path, backup_restore)

        def onderbroken_gzip_open(*_args, **_kwargs):
            raise KeyboardInterrupt

        monkeypatch.setattr(backup_restore.gzip, "open", onderbroken_gzip_open)

        with pytest.raises(KeyboardInterrupt):
            manager.create_backup()

        assert _inhoud(backup_dir) == []

    def test_afgekapte_compressie_wordt_voor_publicatie_afgekeurd(
        self,
        tmp_path: Path,
        backup_restore: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Een gzip die maar de helft van de database bevat mag nooit gepubliceerd worden."""
        _db, backup_dir, manager = _gz_manager(tmp_path, backup_restore)
        real_copy = backup_restore._copy_within_deadline

        def halve_kopie(f_in, f_out, *args, **kwargs):
            if isinstance(f_out, gzip.GzipFile):
                data = f_in.read()
                f_out.write(data[: len(data) // 2])
                return None
            return real_copy(f_in, f_out, *args, **kwargs)

        monkeypatch.setattr(backup_restore, "_copy_within_deadline", halve_kopie)

        with pytest.raises(RuntimeError, match="Backup failed"):
            manager.create_backup()

        assert _inhoud(backup_dir) == []

    def test_publicatiefout_wordt_als_publish_failed_geclassificeerd(
        self,
        tmp_path: Path,
        backup_restore: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """PR425 M1: een OSError bij de hardlink-publicatie (bv. exFAT/SMB) is geen
        compressiefout; er verschijnt geen eindbestand en alles wordt opgeruimd."""
        _db, backup_dir, manager = _gz_manager(tmp_path, backup_restore)

        def link_die_faalt(staging: Path, destination: Path) -> None:
            raise OSError(1, "hardlinks niet ondersteund", str(destination))

        monkeypatch.setattr(backup_restore, "publish_staged_file", link_die_faalt)

        with pytest.raises(RuntimeError, match="publish_failed"):
            manager.create_backup()

        assert _inhoud(backup_dir) == []

    def test_cleanupfout_na_gz_publicatie_is_eerlijk_succes(
        self,
        tmp_path: Path,
        backup_restore: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ):
        _db, backup_dir, manager = _gz_manager(tmp_path, backup_restore)
        real_unlink = os.unlink

        def weigerende_unlink(path, *args, **kwargs):
            naam = os.fspath(path)
            if naam.endswith(".db") or STAGING_MARKER in naam:
                raise PermissionError(1, "cleanup geweigerd")
            return real_unlink(path, *args, **kwargs)

        monkeypatch.setattr(os, "unlink", weigerende_unlink)
        caplog.set_level(logging.WARNING)

        gepubliceerd = manager.create_backup()

        assert gepubliceerd.name.endswith(".db.gz")
        assert gepubliceerd.exists()
        assert manager.verify_backup(gepubliceerd) is True
        assert any("cleanup" in r.getMessage() for r in caplog.records)


class TestGecomprimeerdeVerificatie:
    def test_gz_verificatie_behoudt_bestaand_naastliggend_db_bestand(
        self, tmp_path: Path, backup_restore: ModuleType
    ):
        _db, backup_dir, manager = _gz_manager(tmp_path, backup_restore)
        gz = manager.create_backup()
        buur = gz.with_suffix("")  # definities_backup_<ts>.db naast de .gz
        buur.write_bytes(b"bestaand bestand moet verificatie overleven")

        assert manager.verify_backup(gz) is True

        assert buur.read_bytes() == b"bestaand bestand moet verificatie overleven"
        assert _inhoud(backup_dir) == sorted([gz.name, buur.name])

    @pytest.mark.parametrize("variant", ["afgekapt", "rommel"])
    def test_gz_verificatie_weigert_corrupte_gzip_zonder_restanten(
        self, tmp_path: Path, backup_restore: ModuleType, variant: str
    ):
        _db, backup_dir, manager = _gz_manager(tmp_path, backup_restore)
        gz = manager.create_backup()
        data = gz.read_bytes()
        kapot = backup_dir / "definities_backup_kapot.db.gz"
        kapot.write_bytes(
            data[: len(data) // 2] if variant == "afgekapt" else b"x" * 64
        )

        assert manager.verify_backup(kapot) is False
        assert _inhoud(backup_dir) == sorted([gz.name, kapot.name])

    def test_gz_verificatie_gebruikt_eigen_tempresource_en_sluit_die(
        self,
        tmp_path: Path,
        backup_restore: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
    ):
        _db, backup_dir, manager = _gz_manager(tmp_path, backup_restore)
        gz = manager.create_backup()
        real_mkstemp = tempfile.mkstemp
        aangemaakt: list[tuple[int, str]] = []

        def registrerende_mkstemp(*args, **kwargs):
            fd, naam = real_mkstemp(*args, **kwargs)
            aangemaakt.append((fd, naam))
            return fd, naam

        with monkeypatch.context() as patch:
            patch.setattr(tempfile, "mkstemp", registrerende_mkstemp)
            assert manager.verify_backup(gz) is True

        assert aangemaakt, "verificatie moet een eigen unieke tempresource gebruiken"
        for fd, naam in aangemaakt:
            assert not Path(naam).exists()
            assert Path(naam) != gz.with_suffix("")
            with pytest.raises(OSError, match="Bad file descriptor"):
                os.fstat(fd)

    def test_creatie_decomprimeert_in_de_backupdoelmap(
        self,
        tmp_path: Path,
        backup_restore: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """PR425 I1: tijdens creatie hoort de terug-decompressie in de doelmap,
        zodat een kleine systeem-temp-partitie de route niet breekt."""
        _db, backup_dir, manager = _gz_manager(tmp_path, backup_restore)
        real_mkstemp = tempfile.mkstemp
        aangemaakt: list[Path] = []

        def registrerende_mkstemp(*args, **kwargs):
            fd, naam = real_mkstemp(*args, **kwargs)
            aangemaakt.append(Path(naam))
            return fd, naam

        with monkeypatch.context() as patch:
            patch.setattr(tempfile, "mkstemp", registrerende_mkstemp)
            gz = manager.create_backup()

        assert len(aangemaakt) >= 3  # .db-staging, .gz-staging, verificatietemp
        assert all(p.parent == backup_dir for p in aangemaakt), aangemaakt
        assert all(not p.exists() for p in aangemaakt)
        assert _inhoud(backup_dir) == [gz.name]

    def test_standalone_verify_werkt_op_alleen_leesbare_archiefmap(
        self,
        tmp_path: Path,
        backup_restore: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """PR425 I1-correctie: standalone verify van een bestaand archief mag geen
        schrijfpermissie op de archiefmap vereisen en laat buurbestanden staan."""
        _db, backup_dir, manager = _gz_manager(tmp_path, backup_restore)
        gz = manager.create_backup()
        buur = gz.with_suffix("")
        buur.write_bytes(b"buur blijft")
        real_mkstemp = tempfile.mkstemp
        aangemaakt: list[Path] = []

        def registrerende_mkstemp(*args, **kwargs):
            fd, naam = real_mkstemp(*args, **kwargs)
            aangemaakt.append(Path(naam))
            return fd, naam

        oorspronkelijke_mode = backup_dir.stat().st_mode
        os.chmod(backup_dir, 0o555)
        try:
            with monkeypatch.context() as patch:
                patch.setattr(tempfile, "mkstemp", registrerende_mkstemp)
                assert manager.verify_backup(gz) is True
        finally:
            os.chmod(backup_dir, oorspronkelijke_mode)

        assert aangemaakt
        assert all(p.parent != backup_dir for p in aangemaakt), aangemaakt
        assert all(not p.exists() for p in aangemaakt)
        assert buur.read_bytes() == b"buur blijft"
        assert _inhoud(backup_dir) == sorted([gz.name, buur.name])

    def test_mkstemp_fout_in_gz_verificatie_geeft_false(
        self,
        tmp_path: Path,
        backup_restore: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ):
        """PR425 T1: een volle/onbeschrijfbare tempmap wordt een veilige reason en
        False, geen rauwe OSError uit een bool-functie."""
        _db, backup_dir, manager = _gz_manager(tmp_path, backup_restore)
        gz = manager.create_backup()

        def volle_temp(*_args, **_kwargs):
            raise OSError(28, "geen ruimte", str(tmp_path / "temp"))

        caplog.set_level(logging.ERROR)
        with monkeypatch.context() as patch:
            patch.setattr(tempfile, "mkstemp", volle_temp)
            assert manager.verify_backup(gz) is False

        berichten = [r.getMessage() for r in caplog.records]
        assert any("temp_unavailable" in m for m in berichten)
        assert all(str(tmp_path) not in m for m in berichten)
        assert _inhoud(backup_dir) == [gz.name]

    def test_standalone_verify_timeout_geeft_false_en_ruimt_eigen_temp_op(
        self,
        tmp_path: Path,
        backup_restore: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ):
        """Verlopen budget tijdens decompressie: False via de bestaande route, geen restanten."""
        from database import sqlite_backup

        _db, backup_dir, manager = _gz_manager(tmp_path, backup_restore)
        gz = manager.create_backup()
        klok = _Klok()
        monkeypatch.setattr(sqlite_backup, "_monotonic", klok)
        real_gzip_open = backup_restore.gzip.open

        def gzip_open_dat_tijd_kost(path, mode="rb", *args, **kwargs):
            handle = real_gzip_open(path, mode, *args, **kwargs)
            if mode.startswith("r"):
                klok.now += 10_000  # de decompressie duurt langer dan het budget
            return handle

        monkeypatch.setattr(backup_restore.gzip, "open", gzip_open_dat_tijd_kost)
        real_mkstemp = tempfile.mkstemp
        aangemaakt: list[tuple[int, str]] = []

        def registrerende_mkstemp(*args, **kwargs):
            fd, naam = real_mkstemp(*args, **kwargs)
            aangemaakt.append((fd, naam))
            return fd, naam

        caplog.set_level(logging.ERROR)
        with monkeypatch.context() as patch:
            patch.setattr(tempfile, "mkstemp", registrerende_mkstemp)
            assert manager.verify_backup(gz, deadline_seconds=5.0) is False

        assert any("backup_timeout" in r.getMessage() for r in caplog.records)
        assert aangemaakt
        for fd, naam in aangemaakt:
            assert not Path(naam).exists()
            with pytest.raises(OSError, match="Bad file descriptor"):
                os.fstat(fd)
        assert _inhoud(backup_dir) == [gz.name]

    def test_gecomprimeerde_backup_behoudt_wal_commit_en_is_herstelbaar(
        self, tmp_path: Path, backup_restore: ModuleType
    ):
        db, _backup_dir, manager = _gz_manager(tmp_path, backup_restore)
        writer = _wal_writer_met_extra_rij(db)
        try:
            gz = manager.create_backup()
            hersteld = tmp_path / "hersteld.db"
            hersteld.write_bytes(gzip.decompress(gz.read_bytes()))
        finally:
            writer.close()

        assert _query(
            hersteld, "SELECT definitie FROM definities WHERE begrip = 'wal-alleen'"
        ) == [("staat alleen in de WAL",)]
        assert _query(hersteld, "PRAGMA integrity_check") == [("ok",)]
