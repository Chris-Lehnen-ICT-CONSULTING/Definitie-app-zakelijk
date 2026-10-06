"""DEF-620 (RAG fase 2): importscript en vervangscript van de bronbibliotheek."""

from __future__ import annotations

import importlib.util
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pytest

from services.rag.embedding_store import EmbeddingStore
from tests.unit.services.rag.test_def620_officiele_publicatie import LABEL, OP_XML
from tests.unit.services.rag.test_rag_service import DIMS, SCHEMA_SQL

pytestmark = [pytest.mark.unit]

SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"

# Kerntabellen die de backuphelper (DEF-663) in elke bron verwacht.
KERN_SQL = """
CREATE TABLE definities (id INTEGER PRIMARY KEY, begrip TEXT, definitie TEXT);
CREATE TABLE definitie_geschiedenis (id INTEGER PRIMARY KEY, definitie_id INTEGER);
CREATE TABLE definitie_tags (id INTEGER PRIMARY KEY, definitie_id INTEGER);
CREATE TABLE definitie_voorbeelden (id INTEGER PRIMARY KEY, definitie_id INTEGER);
CREATE TABLE synonym_groups (id INTEGER PRIMARY KEY, canonical_term TEXT);
CREATE TABLE synonym_group_members (id INTEGER PRIMARY KEY, group_id INTEGER, term TEXT);
CREATE TABLE import_export_logs (id INTEGER PRIMARY KEY);
CREATE TABLE projects (
    id INTEGER PRIMARY KEY, project_name TEXT,
    rag_collection_id INTEGER REFERENCES rag_collections(id)
);
"""


def _laad(naam: str, monkeypatch):
    # Het importscript leest .env bij het laden; in tests nooit.
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **k: False)
    monkeypatch.setattr(sys, "dont_write_bytecode", True)
    spec = importlib.util.spec_from_file_location(naam, SCRIPTS / f"{naam}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, naam, module)  # nodig voor @dataclass
    spec.loader.exec_module(module)
    return module


def _maak_db(pad: Path) -> Path:
    pad.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(pad)
    conn.executescript(SCHEMA_SQL + KERN_SQL)
    conn.close()
    return pad


class _NepEmbedder:
    DIMENSIONS = DIMS
    MODEL = "test"

    def __init__(self, *_a, **_k) -> None:
        self.aanroepen = 0

    def embed_batch(self, teksten):
        self.aanroepen += 1
        return [np.ones(DIMS, dtype=np.float32) for _ in teksten]


# --- importscript -------------------------------------------------------------------


@pytest.fixture
def importeer(tmp_path, monkeypatch):
    mod = _laad("rag_importeer_officiele_publicatie", monkeypatch)
    monkeypatch.setattr(mod, "EmbeddingService", _NepEmbedder)
    db = _maak_db(tmp_path / "rag.db")
    # Testdimensie; het script hergebruikt een bestaande collectie.
    EmbeddingStore(str(db)).create_collection("sv-nieuw", dimensions=DIMS, model="test")
    xml = tmp_path / "stb-test.xml"
    xml.write_text(OP_XML, encoding="utf-8")
    argv = [
        "--db", str(db), "--collectie", "sv-nieuw", "--wet-regeling", LABEL,
        "--bestanden", str(xml),
    ]  # fmt: skip
    return mod, db, argv


def _documenten(db: Path) -> list[tuple]:
    conn = sqlite3.connect(db)
    try:
        return conn.execute(
            "SELECT d.filename, d.chunk_count, "
            "(SELECT COUNT(*) FROM rag_chunks c WHERE c.document_id = d.id) "
            "FROM rag_documents d"
        ).fetchall()
    finally:
        conn.close()


def test_import_daarna_compleet_document_overgeslagen(importeer):
    mod, db, argv = importeer
    assert mod.main(argv) == 0
    assert _documenten(db) == [("stb-test.xml", 4, 4)]
    assert mod.main(argv) == 0  # tweede keer: compleet, dus overgeslagen
    assert _documenten(db) == [("stb-test.xml", 4, 4)]


def test_incompleet_document_geeft_exit_2_en_verwijdert_niets(importeer):
    mod, db, argv = importeer
    assert mod.main(argv) == 0
    conn = sqlite3.connect(db)
    conn.execute("DELETE FROM rag_chunks WHERE chunk_index = 3")
    conn.commit()
    conn.close()
    assert mod.main(argv) == 2
    assert _documenten(db) == [("stb-test.xml", 4, 3)]


def test_onbekend_rechtsgebied_exit_1_zonder_schrijven(importeer):
    mod, db, argv = importeer
    assert mod.main([*argv, "--rechtsgebied", "sterrenkunde"]) == 1
    assert _documenten(db) == []


def test_droog_schrijft_niets(importeer):
    mod, db, argv = importeer
    assert mod.main([*argv, "--droog"]) == 0
    assert _documenten(db) == []


# --- vervangscript ------------------------------------------------------------------

UPLOAD = "data/uploads/oud-sv.pdf"


@pytest.fixture
def vervang(tmp_path, monkeypatch):
    """Projectmap <basis>/data/definities.db met een oude en een nieuwe collectie."""
    mod = _laad("rag_vervang_collectie", monkeypatch)
    basis = tmp_path / "project"
    db = _maak_db(basis / "data" / "definities.db")
    store = EmbeddingStore(str(db))
    oud = store.create_collection("oud", dimensions=DIMS, model="test")
    nieuw = store.create_collection("nieuw", dimensions=DIMS, model="test")
    conn = sqlite3.connect(db)
    for cid, n, pad in ((oud, 3, UPLOAD), (nieuw, 2, None)):
        doc = conn.execute(
            "INSERT INTO rag_documents (collection_id, filename, chunk_count, file_path)"
            " VALUES (?, ?, ?, ?)",
            (cid, f"doc-{cid}", n, pad),
        ).lastrowid
        for i in range(n):
            vec = np.zeros(DIMS, dtype=np.float32)
            vec[i] = 1.0
            conn.execute(
                "INSERT INTO rag_chunks (collection_id, document_id, chunk_text,"
                " embedding, chunk_index) VALUES (?, ?, ?, ?, ?)",
                (cid, doc, f"tekst {i}", vec.tobytes(), i),
            )
    conn.commit()
    conn.close()
    (basis / "data" / "uploads").mkdir()
    (basis / UPLOAD).write_bytes(b"%PDF oud")
    # Werkmap bewust ergens anders: het script mag daar niets van afhangen.
    elders = tmp_path / "elders"
    (elders / "data" / "uploads").mkdir(parents=True)
    (elders / UPLOAD).write_bytes(b"niet aankomen")
    monkeypatch.chdir(elders)
    argv = [
        "--db", str(db), "--oud-id", str(oud), "--oud-naam", "oud",
        "--oud-chunks", "3", "--nieuw-naam", "nieuw", "--nieuw-chunks", "2",
    ]  # fmt: skip
    return mod, basis, db, oud, nieuw, argv, elders


def _collecties(db: Path) -> list[tuple]:
    conn = sqlite3.connect(db)
    try:
        return conn.execute(
            "SELECT c.collection_name, (SELECT COUNT(*) FROM rag_chunks k"
            " WHERE k.collection_id = c.id) FROM rag_collections c ORDER BY c.id"
        ).fetchall()
    finally:
        conn.close()


def test_droge_run_wijzigt_niets(vervang):
    mod, basis, db, *_rest, argv, _elders = vervang
    assert mod.main(argv) == 0
    assert _collecties(db) == [("oud", 3), ("nieuw", 2)]
    assert (basis / UPLOAD).exists()
    assert not (basis / "data" / "backups").exists()


@pytest.mark.parametrize(
    ("vervanging", "fout"),
    [
        (("--oud-chunks", "3", "--oud-chunks", "4"), "oude collectie heeft 3"),
        (("--nieuw-chunks", "2", "--nieuw-chunks", "5"), "nieuwe collectie heeft 2"),
        (("--oud-naam", "oud", "--oud-naam", "nieuw"), "niet gevonden"),
    ],
)
def test_afwijkende_identiteit_weigert(vervang, capsys, vervanging, fout):
    mod, _basis, db, *_rest, argv, _elders = vervang
    i = argv.index(vervanging[0])
    aangepast = [*argv[:i], vervanging[2], vervanging[3], *argv[i + 2 :]]
    assert mod.main([*aangepast, "--bevestig"]) == 2
    assert fout in capsys.readouterr().out
    assert _collecties(db) == [("oud", 3), ("nieuw", 2)]


def test_incompleet_nieuw_document_weigert(vervang):
    mod, _basis, db, _oud, nieuw, argv, _elders = vervang
    conn = sqlite3.connect(db)
    conn.execute(
        "UPDATE rag_documents SET chunk_count = 9 WHERE collection_id = ?", (nieuw,)
    )
    conn.commit()
    conn.close()
    assert mod.main([*argv, "--bevestig"]) == 2
    assert _collecties(db) == [("oud", 3), ("nieuw", 2)]


def test_ontbrekende_embedding_weigert(vervang):
    mod, _basis, db, _oud, nieuw, argv, _elders = vervang
    conn = sqlite3.connect(db)
    conn.execute(
        "UPDATE rag_chunks SET embedding = NULL WHERE collection_id = ? "
        "AND chunk_index = 1",
        (nieuw,),
    )
    conn.commit()
    conn.close()
    assert mod.main([*argv, "--bevestig"]) == 2
    assert _collecties(db) == [("oud", 3), ("nieuw", 2)]


def test_projectverwijzing_weigert(vervang):
    mod, _basis, db, oud, _nieuw, argv, _elders = vervang
    conn = sqlite3.connect(db)
    conn.execute(
        "INSERT INTO projects (project_name, rag_collection_id) VALUES ('p', ?)", (oud,)
    )
    conn.commit()
    conn.close()
    assert mod.main([*argv, "--bevestig"]) == 2
    assert _collecties(db) == [("oud", 3), ("nieuw", 2)]


def test_uploadpad_buiten_projectmap_weigert(vervang):
    mod, _basis, db, oud, _nieuw, argv, _elders = vervang
    conn = sqlite3.connect(db)
    conn.execute(
        "UPDATE rag_documents SET file_path = '../../buiten.pdf' WHERE collection_id = ?",
        (oud,),
    )
    conn.commit()
    conn.close()
    assert mod.main([*argv, "--bevestig"]) == 2
    assert _collecties(db) == [("oud", 3), ("nieuw", 2)]


def test_bevestig_maakt_backup_bewaart_upload_en_verwijdert_oud(vervang):
    mod, basis, db, *_rest, argv, elders = vervang
    assert mod.main([*argv, "--bevestig"]) == 0
    assert _collecties(db) == [("nieuw", 2)]

    backups = basis / "data" / "backups"
    (backup,) = backups.glob("definities_backup_voor_vervang_*.db")
    conn = sqlite3.connect(backup)
    assert conn.execute("SELECT COUNT(*) FROM rag_chunks").fetchone()[0] == 5
    conn.close()
    (kopie,) = backups.glob("uploads_voor_vervang_*/oud-sv.pdf")
    assert kopie.read_bytes() == b"%PDF oud"

    assert not (basis / UPLOAD).exists()  # opgeruimd in de projectmap …
    assert (elders / UPLOAD).read_bytes() == b"niet aankomen"  # … niet in de werkmap
    assert Path.cwd() == elders
