"""DEF-620 (RAG fase 3): verhuizing van de bronbibliotheek naar data/bronnen.db."""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

import numpy as np
import pytest

from services.rag.bronnen_schema import zorg_voor_bronnen_schema
from services.rag.embedding_store import EmbeddingStore
from tests.unit.scripts.test_def620_rag_scripts import _laad, _maak_db
from tests.unit.services.rag.test_rag_service import DIMS

pytestmark = [pytest.mark.unit]


def _sha(pad: Path) -> str:
    return hashlib.sha256(pad.read_bytes()).hexdigest()


@pytest.fixture
def verhuis(tmp_path, monkeypatch):
    mod = _laad("rag_verhuis_naar_bronnen", monkeypatch)
    van = _maak_db(tmp_path / "data" / "definities.db")
    store = EmbeddingStore(str(van))
    a = store.create_collection("a", dimensions=DIMS, model="test")
    b = store.create_collection("b", dimensions=DIMS, model="test")
    conn = sqlite3.connect(van)
    for cid, n in ((a, 3), (b, 2)):
        doc = conn.execute(
            "INSERT INTO rag_documents (collection_id, filename, chunk_count)"
            " VALUES (?, ?, ?)",
            (cid, f"doc-{cid}", n),
        ).lastrowid
        for i in range(n):
            vec = np.full(DIMS, i + cid, dtype=np.float32)
            conn.execute(
                "INSERT INTO rag_chunks (collection_id, document_id, chunk_text,"
                " embedding, chunk_index, metadata) VALUES (?, ?, ?, ?, ?, ?)",
                (cid, doc, f"tekst {cid}.{i}", vec.tobytes(), i, '{"x": 1}'),
            )
    # een verwijderde rij laat de AUTOINCREMENT-teller hoger staan
    conn.execute("DELETE FROM rag_chunks WHERE chunk_text = 'tekst 2.1'")
    conn.execute("UPDATE rag_documents SET chunk_count = 1 WHERE collection_id = 2")
    conn.commit()
    conn.close()
    naar = tmp_path / "data" / "bronnen.db"
    monkeypatch.chdir(tmp_path)
    return mod, van, naar, tmp_path


def _inhoud(pad: Path) -> list[tuple]:
    conn = sqlite3.connect(pad)
    try:
        return conn.execute(
            "SELECT c.id, c.collection_id, c.document_id, c.chunk_text, c.embedding,"
            " c.metadata, d.filename, k.collection_name FROM rag_chunks c"
            " JOIN rag_documents d ON d.id = c.document_id"
            " JOIN rag_collections k ON k.id = c.collection_id ORDER BY c.id"
        ).fetchall()
    finally:
        conn.close()


def test_droge_run_schrijft_niets(verhuis, capsys):
    mod, van, naar, _tmp = verhuis
    voor = _sha(van)
    assert mod.main(["--van", str(van), "--naar", str(naar)]) == 0
    assert not naar.exists()
    assert _sha(van) == voor
    assert "collectie 1 'a': 1 documenten, 3 fragmenten" in capsys.readouterr().out


def test_verhuizing_kopieert_alles_en_laat_bron_ongewijzigd(verhuis):
    mod, van, naar, tmp = verhuis
    voor = _sha(van)
    assert mod.main(["--van", str(van), "--naar", str(naar), "--bevestig"]) == 0
    assert _sha(van) == voor
    assert _inhoud(naar) == _inhoud(van)
    conn = sqlite3.connect(naar)
    seq = dict(conn.execute("SELECT name, seq FROM sqlite_sequence").fetchall())
    versie = conn.execute("PRAGMA user_version").fetchone()[0]
    conn.close()
    assert seq["rag_chunks"] == 5  # teller van de bron, niet het hoogste id (4)
    assert versie == 1
    (backup,) = (tmp / "data" / "backups").glob(
        "definities_backup_voor_verhuizing_bronnen_*.db"
    )
    assert _inhoud(backup) == _inhoud(van)
    assert not list(naar.parent.glob(".bronnen.db.verhuizing-*"))


def test_leeg_doel_met_alleen_schema_wordt_geaccepteerd(verhuis):
    mod, van, naar, _tmp = verhuis
    zorg_voor_bronnen_schema(naar)  # zoals de app het vanzelf aanmaakt
    assert mod.main(["--van", str(van), "--naar", str(naar), "--bevestig"]) == 0
    assert _inhoud(naar) == _inhoud(van)


def test_gevuld_doel_wordt_geweigerd(verhuis, capsys):
    mod, van, naar, _tmp = verhuis
    zorg_voor_bronnen_schema(naar)
    conn = sqlite3.connect(naar)
    conn.execute("INSERT INTO rag_collections (collection_name) VALUES ('x')")
    conn.commit()
    conn.close()
    voor = _sha(naar)
    assert mod.main(["--van", str(van), "--naar", str(naar), "--bevestig"]) == 2
    assert "doel bevat al gegevens" in capsys.readouterr().out
    assert _sha(naar) == voor


@pytest.mark.parametrize("geval", ["zelfde", "definities"])
def test_doel_mag_geen_definitiedatabase_zijn(verhuis, tmp_path, geval):
    mod, van, _naar, _tmp = verhuis
    doel = van if geval == "zelfde" else _maak_db(tmp_path / "andere" / "def.db")
    assert mod.main(["--van", str(van), "--naar", str(doel), "--bevestig"]) == 2


def test_verweesde_rijen_in_bron_weigeren(verhuis, capsys):
    mod, van, naar, _tmp = verhuis
    conn = sqlite3.connect(van)
    conn.execute(
        "INSERT INTO rag_chunks (collection_id, document_id, chunk_text)"
        " VALUES (99, 99, 'wees')"
    )
    conn.commit()
    conn.close()
    assert mod.main(["--van", str(van), "--naar", str(naar), "--bevestig"]) == 2
    assert "verweesde" in capsys.readouterr().out
    assert not naar.exists()


def test_afwijkende_kopie_plaatst_niets(verhuis, monkeypatch, capsys):
    mod, van, naar, _tmp = verhuis
    echt = mod._overzicht
    teller = {"n": 0}

    def overzicht(conn):
        teller["n"] += 1
        uit = echt(conn)
        if teller["n"] == 2:  # 1 = controle vooraf, 2 = de kopie
            uit[1] = ("a", 1, 3, "anders")
        return uit

    monkeypatch.setattr(mod, "_overzicht", overzicht)
    assert mod.main(["--van", str(van), "--naar", str(naar), "--bevestig"]) == 3
    assert "wijkt af" in capsys.readouterr().out
    assert not naar.exists()
    assert not list(naar.parent.glob(".bronnen.db.verhuizing-*"))


# --- vervangscript op het bronnenbestand ----------------------------------------


def test_vervangscript_op_bronnenbestand_met_projectcontrole(tmp_path, monkeypatch):
    mod = _laad("rag_vervang_collectie", monkeypatch)
    basis = tmp_path / "project"
    bronnen = basis / "data" / "bronnen.db"
    zorg_voor_bronnen_schema(bronnen)
    store = EmbeddingStore(str(bronnen))
    oud = store.create_collection("oud", dimensions=DIMS, model="test")
    nieuw = store.create_collection("nieuw", dimensions=DIMS, model="test")
    conn = sqlite3.connect(bronnen)
    for cid, n in ((oud, 2), (nieuw, 2)):
        doc = conn.execute(
            "INSERT INTO rag_documents (collection_id, filename, chunk_count)"
            " VALUES (?, ?, ?)",
            (cid, f"d{cid}", n),
        ).lastrowid
        for i in range(n):
            vec = np.zeros(DIMS, dtype=np.float32)
            vec[i] = 1.0
            conn.execute(
                "INSERT INTO rag_chunks (collection_id, document_id, chunk_text,"
                " embedding, chunk_index) VALUES (?, ?, ?, ?, ?)",
                (cid, doc, f"t{i}", vec.tobytes(), i),
            )
    conn.commit()
    conn.close()
    definities = _maak_db(basis / "data" / "definities.db")
    argv = [
        "--db", str(bronnen), "--definities-db", str(definities),
        "--oud-id", str(oud), "--oud-naam", "oud", "--oud-chunks", "2",
        "--nieuw-naam", "nieuw", "--nieuw-chunks", "2", "--bevestig",
    ]  # fmt: skip
    conn = sqlite3.connect(definities)
    conn.execute(
        "INSERT INTO projects (project_name, rag_collection_id) VALUES ('p', ?)", (oud,)
    )
    conn.commit()
    conn.close()
    assert mod.main(argv) == 2  # project verwijst naar de oude collectie

    conn = sqlite3.connect(definities)
    conn.execute("DELETE FROM projects")
    conn.commit()
    conn.close()
    assert mod.main(argv) == 0  # backup met bronnenkern slaagt
    (backup,) = (basis / "data" / "backups").glob("definities_backup_voor_vervang_*")
    conn = sqlite3.connect(bronnen)
    namen = [r[0] for r in conn.execute("SELECT collection_name FROM rag_collections")]
    conn.close()
    assert namen == ["nieuw"]
    assert backup.exists()
