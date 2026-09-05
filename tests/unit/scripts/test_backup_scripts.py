"""Contracttests voor de shell-backupentrypoints (DEF-663).

``scripts/auto_backup_database.sh`` en ``scripts/backup_database.sh`` moeten
de gedeelde WAL-veilige helper gebruiken: een gecommitte maar niet-
gecheckpointte WAL-rij komt in de backup terecht, een bron zonder kernschema
wordt geweigerd zonder eindbestand, en een ontbrekende database faalt.

De scripts draaien in een gekopieerde, synthetische projectstructuur in
``tmp_path`` (scripts/, src/database/, data/). De echte ``data/definities.db``
wordt nooit gelezen of geschreven.
"""

from __future__ import annotations

import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit]

_REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ("auto_backup_database.sh", "backup_database.sh")
BACKUP_DIR_PER_SCRIPT = {
    "auto_backup_database.sh": Path("data") / "backups" / "auto",
    "backup_database.sh": Path("data") / "backups",
}
STAGING_MARKER = ".staging-"

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


def _maak_fixture_project(tmp_path: Path, schema: str = CORE_SCHEMA_SQL) -> Path:
    root = tmp_path / "project"
    (root / "scripts").mkdir(parents=True)
    for name in SCRIPTS:
        shutil.copy2(_REPO_ROOT / "scripts" / name, root / "scripts" / name)
    package = root / "src" / "database"
    package.mkdir(parents=True)
    shutil.copy2(_REPO_ROOT / "src" / "database" / "sqlite_backup.py", package)
    (package / "__init__.py").write_text("")
    (root / "data").mkdir()
    conn = sqlite3.connect(str(root / "data" / "definities.db"))
    try:
        conn.executescript(schema)
    finally:
        conn.close()
    return root


@pytest.fixture
def fixture_project(tmp_path: Path) -> Path:
    return _maak_fixture_project(tmp_path)


def _run(root: Path, script: str) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PYTHON": sys.executable}
    return subprocess.run(
        ["bash", str(root / "scripts" / script)],
        cwd=str(root),
        capture_output=True,
        text=True,
        env=env,
        check=False,
        timeout=120,
    )


def _backups(root: Path, script: str) -> list[Path]:
    directory = root / BACKUP_DIR_PER_SCRIPT[script]
    if not directory.is_dir():
        return []
    return sorted(directory.glob("definities_backup_*.db"))


def _staging_artefacts(root: Path, script: str) -> list[Path]:
    directory = root / BACKUP_DIR_PER_SCRIPT[script]
    if not directory.is_dir():
        return []
    return sorted(p for p in directory.iterdir() if STAGING_MARKER in p.name)


def _query(path: Path, sql: str) -> list[tuple]:
    conn = sqlite3.connect(str(path))
    try:
        return conn.execute(sql).fetchall()
    finally:
        conn.close()


@pytest.mark.parametrize("script", SCRIPTS)
def test_script_syntax(script: str):
    result = subprocess.run(
        ["bash", "-n", str(_REPO_ROOT / "scripts" / script)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("script", SCRIPTS)
def test_script_behoudt_ongecheckpointte_wal_commit(fixture_project: Path, script: str):
    db = fixture_project / "data" / "definities.db"
    writer = sqlite3.connect(str(db))
    try:
        writer.execute("PRAGMA journal_mode=WAL")
        writer.execute("PRAGMA wal_autocheckpoint=0")
        writer.execute(
            "INSERT INTO definities (begrip, definitie) "
            "VALUES ('wal-alleen', 'staat alleen in de WAL')"
        )
        writer.commit()
        assert (db.parent / "definities.db-wal").stat().st_size > 0

        result = _run(fixture_project, script)
    finally:
        writer.close()

    assert result.returncode == 0, result.stdout + result.stderr
    backups = _backups(fixture_project, script)
    assert len(backups) == 1, result.stdout + result.stderr
    assert _query(
        backups[0], "SELECT definitie FROM definities WHERE begrip = 'wal-alleen'"
    ) == [("staat alleen in de WAL",)]
    assert _query(backups[0], "PRAGMA integrity_check") == [("ok",)]
    assert _staging_artefacts(fixture_project, script) == []


def test_backup_database_adviseert_geen_cp_restore_over_de_bron(
    fixture_project: Path,
):
    """De hersteltip mag nooit een rauwe cp over de live (WAL-)database zijn."""
    result = _run(fixture_project, "backup_database.sh")
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'cp "' not in result.stdout
    assert "database.sqlite_backup" in result.stdout
    assert "NIEUW" in result.stdout


def test_auto_backup_onderhoudt_latest_symlink(fixture_project: Path):
    result = _run(fixture_project, "auto_backup_database.sh")
    assert result.returncode == 0, result.stdout + result.stderr
    latest = fixture_project / "data" / "backups" / "auto" / "latest.db"
    assert latest.is_symlink()
    assert latest.resolve() == _backups(fixture_project, "auto_backup_database.sh")[0]


@pytest.mark.parametrize("script", SCRIPTS)
def test_script_weigert_bron_zonder_kernschema(tmp_path: Path, script: str):
    schema = CORE_SCHEMA_SQL.replace(
        "CREATE TABLE definitie_voorbeelden", "CREATE TABLE geen_kern"
    )
    root = _maak_fixture_project(tmp_path, schema=schema)

    result = _run(root, script)

    assert result.returncode != 0
    assert _backups(root, script) == []
    assert _staging_artefacts(root, script) == []
    # De reden komt uit de helper; het pad van de bron hoort niet in stderr.
    assert "core_schema_incomplete" in result.stdout + result.stderr


@pytest.mark.parametrize("script", SCRIPTS)
def test_script_faalt_zonder_database(fixture_project: Path, script: str):
    (fixture_project / "data" / "definities.db").unlink()

    result = _run(fixture_project, script)

    assert result.returncode == 1
    assert _backups(fixture_project, script) == []


@pytest.mark.parametrize("script", SCRIPTS)
def test_script_overschrijft_bestaande_backup_niet(fixture_project: Path, script: str):
    """Twee runs binnen dezelfde seconde botsen op de tijdstempelnaam: geen clobber."""
    first = _run(fixture_project, script)
    assert first.returncode == 0, first.stdout + first.stderr
    eerste = _backups(fixture_project, script)[0]
    inhoud = eerste.read_bytes()

    second = _run(fixture_project, script)

    backups = _backups(fixture_project, script)
    if len(backups) == 1:
        # Zelfde tijdstempel: de tweede run moet weigeren en niets aanraken.
        assert second.returncode != 0
        assert "destination_exists" in second.stdout + second.stderr
    else:
        assert second.returncode == 0
    assert eerste.read_bytes() == inhoud
    assert _staging_artefacts(fixture_project, script) == []
