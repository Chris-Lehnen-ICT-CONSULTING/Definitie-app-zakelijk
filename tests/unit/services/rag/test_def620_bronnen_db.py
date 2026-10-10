"""DEF-620 (RAG fase 3): de bronbibliotheek in een eigen bestand data/bronnen.db."""

from __future__ import annotations

import logging
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from database.sqlite_backup import (
    BackupError,
    create_verified_backup,
)
from services.container import ServiceContainer, _afgeleid_bronnenpad
from services.rag.bronnen_schema import (
    BRONNEN_SCHEMA_VERSIE,
    RAG_TABELLEN,
    aantal_rag_chunks,
    zorg_voor_bronnen_schema,
)

pytestmark = [pytest.mark.unit]

SRC = Path(__file__).resolve().parents[4] / "src"


def _tabellen(pad: Path) -> set[str]:
    conn = sqlite3.connect(pad)
    try:
        return {
            r[0]
            for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    finally:
        conn.close()


# --- schema -------------------------------------------------------------------


def test_schema_in_leeg_bestand_en_idempotent(tmp_path):
    pad = tmp_path / "sub" / "bronnen.db"  # map bestaat nog niet
    zorg_voor_bronnen_schema(pad)
    zorg_voor_bronnen_schema(pad)
    assert set(RAG_TABELLEN) <= _tabellen(pad)
    conn = sqlite3.connect(pad)
    indexen = {
        r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
    }
    versie = conn.execute("PRAGMA user_version").fetchone()[0]
    conn.close()
    assert {"idx_chunks_collection", "idx_chunks_bron_type"} <= indexen
    assert versie == BRONNEN_SCHEMA_VERSIE
    assert aantal_rag_chunks(pad) == 0


def test_definitiedatabase_wordt_niet_aangepast(tmp_path, caplog):
    pad = tmp_path / "definities.db"
    conn = sqlite3.connect(pad)
    conn.execute("CREATE TABLE definities (id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()
    with caplog.at_level(logging.WARNING):
        zorg_voor_bronnen_schema(pad)
    assert _tabellen(pad) == {"definities"}
    assert "definitiedatabase" in caplog.text


def test_aantal_rag_chunks_zonder_bestand_of_tabel(tmp_path):
    assert aantal_rag_chunks(tmp_path / "bestaat-niet.db") == 0
    leeg = tmp_path / "leeg.db"
    sqlite3.connect(leeg).close()
    assert aantal_rag_chunks(leeg) == 0


# --- container ----------------------------------------------------------------


def test_bronnenpad_naast_definitiedatabase():
    assert _afgeleid_bronnenpad("data/definities.db") == str(Path("data/bronnen.db"))
    assert _afgeleid_bronnenpad("/x/y/test.db") == str(Path("/x/y/bronnen.db"))
    assert _afgeleid_bronnenpad(":memory:") == ":memory:"


def test_container_gebruikt_bronnenbestand_voor_rag(tmp_path):
    definities = tmp_path / "definities.db"
    container = ServiceContainer({"db_path": str(definities)})
    assert container.bronnen_db_path == str(tmp_path / "bronnen.db")
    beheer = container.rag_management_service
    cid = beheer.create_collection("proef", collection_type="wetgeving")
    assert cid > 0
    assert set(RAG_TABELLEN) <= _tabellen(tmp_path / "bronnen.db")
    assert not definities.exists()  # de RAG raakt de definitiedatabase niet
    assert container.rag_service._db_path == str(tmp_path / "bronnen.db")


def test_container_bronnenpad_instelbaar(tmp_path):
    eigen = tmp_path / "elders" / "mijn-bronnen.db"
    container = ServiceContainer(
        {"db_path": str(tmp_path / "definities.db"), "bronnen_db_path": str(eigen)}
    )
    _ = container.embedding_store  # lazy-load maakt het schema aan
    assert set(RAG_TABELLEN) <= _tabellen(eigen)


def test_waarschuwing_als_bronnen_leeg_maar_definities_nog_rag_heeft(tmp_path, caplog):
    definities = tmp_path / "definities.db"
    zorg_voor_bronnen_schema(tmp_path / "oud.db")
    (tmp_path / "oud.db").rename(definities)  # RAG-tabellen, nog zonder definities
    conn = sqlite3.connect(definities)
    conn.execute("INSERT INTO rag_collections (id, collection_name) VALUES (1, 'a')")
    conn.execute(
        "INSERT INTO rag_chunks (collection_id, chunk_text) VALUES (1, 'tekst')"
    )
    conn.commit()
    conn.close()
    container = ServiceContainer({"db_path": str(definities)})
    with caplog.at_level(logging.WARNING, logger="services.container"):
        _ = container.embedding_store
    assert "rag_verhuis_naar_bronnen" in caplog.text


# --- backup met eigen kernmanifest ---------------------------------------------


def _bronnen_met_rij(pad: Path) -> Path:
    zorg_voor_bronnen_schema(pad)
    conn = sqlite3.connect(pad)
    conn.execute("INSERT INTO rag_collections (collection_name) VALUES ('a')")
    conn.commit()
    conn.close()
    return pad


def test_backup_bronnenbestand_met_bronnenkern(tmp_path):
    from services.rag.bronnen_schema import BRONNEN_KERN

    bron = _bronnen_met_rij(tmp_path / "bronnen.db")
    with pytest.raises(BackupError, match="core_schema_incomplete"):
        create_verified_backup(bron, tmp_path / "zonder-kern.db")
    assert not (tmp_path / "zonder-kern.db").exists()
    create_verified_backup(bron, tmp_path / "backup.db", kern=BRONNEN_KERN)
    conn = sqlite3.connect(tmp_path / "backup.db")
    assert conn.execute("SELECT collection_name FROM rag_collections").fetchall() == [
        ("a",)
    ]
    conn.close()


def test_backup_cli_kern_bronnen(tmp_path):
    bron = _bronnen_met_rij(tmp_path / "bronnen.db")
    doel = tmp_path / "backup.db"
    res = subprocess.run(
        [sys.executable, "-m", "database.sqlite_backup", "--kern", "bronnen",
         str(bron), str(doel)],
        env={"PYTHONPATH": str(SRC), "PATH": "/usr/bin:/bin"},
        capture_output=True, text=True, check=False,
    )  # fmt: skip
    assert res.returncode == 0, res.stderr
    assert doel.exists()
