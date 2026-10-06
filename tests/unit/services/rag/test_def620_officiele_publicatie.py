"""DEF-620 (RAG fase 2): wetteksten per artikel uit een officiële publicatie."""

from __future__ import annotations

import sqlite3
from unittest.mock import MagicMock

import numpy as np
import pytest

from services.rag.embedding_store import EmbeddingStore
from services.rag.metadata_schemas import valideer_chunk_metadata
from services.rag.officiele_publicatie_parser import parse_officiele_publicatie
from services.rag.rag_service import RAGService
from tests.unit.services.rag.test_rag_service import DIMS, SCHEMA_SQL

pytestmark = [pytest.mark.unit]

LABEL = "Wetboek van Strafvordering (nieuw, i.w.t. 1-4-2029)"

OP_XML = """<?xml version="1.0" encoding="utf-8"?>
<officiele-publicatie>
  <staatsblad><intitule>Wet van 25 februari 2026</intitule></staatsblad>
  <boek>
    <kop><label>BOEK</label><nr>1</nr><titel>STRAFVORDERING IN HET ALGEMEEN</titel></kop>
    <hoofdstuk>
      <kop><label>HOOFDSTUK</label><nr>4</nr><titel>De verdachte</titel></kop>
      <titeldeel>
        <kop><label>TITEL</label><nr>4.1</nr><titel>Algemene bepalingen</titel></kop>
        <artikel>
          <kop><label>Artikel</label><nr>1.4.1</nr></kop>
          <lid><lidnr>1.</lidnr><al>Als verdachte wordt aangemerkt degene te wiens aanzien:</al>
            <lijst><li><li.nr>a.</li.nr><al>een redelijk vermoeden bestaat;</al></li>
                   <li><li.nr>b.</li.nr><al>de vervolging is gericht.</al></li></lijst>
          </lid>
          <lid><lidnr>2.</lidnr><al>Hij die zich aan de tenuitvoerlegging <nadruk>onttrekt</nadruk>, blijft verdachte.</al></lid>
        </artikel>
      </titeldeel>
    </hoofdstuk>
    <hoofdstuk>
      <kop><label>HOOFDSTUK</label><nr>5</nr><titel>Slachtoffers</titel></kop>
      <artikel>
        <kop><label>Artikel</label><nr>1.5.1</nr></kop>
        <al>In dit wetboek wordt verstaan onder:</al>
        <definitielijst>
          <definitie-item><li.nr>a.</li.nr><term>slachtoffer:</term>
            <definitie><al>het directe en het indirecte slachtoffer;</al></definitie></definitie-item>
          <definitie-item><li.nr>–</li.nr><term>familielid:</term>
            <definitie><al>de echtgenoot;</al></definitie></definitie-item>
        </definitielijst>
      </artikel>
    </hoofdstuk>
  </boek>
  <artikel><kop><label>ARTIKEL</label><nr>IV</nr></kop><al>Deze wet treedt in werking bij koninklijk besluit.</al></artikel>
</officiele-publicatie>
"""


@pytest.fixture
def xml_bestand(tmp_path):
    pad = tmp_path / "stb-test.xml"
    pad.write_text(OP_XML, encoding="utf-8")
    return pad


def test_een_chunk_per_artikel_plus_definities_formeel_artikel_overgeslagen(
    xml_bestand,
):
    res = parse_officiele_publicatie(xml_bestand, LABEL, "strafrecht")
    assert res.fout_melding is None
    soorten = [
        (c.metadata.structuur_type, c.metadata.artikel_nummer) for c in res.chunks
    ]
    assert soorten == [
        ("artikel", "1.4.1"),
        ("artikel", "1.5.1"),
        ("definitie", "1.5.1"),
        ("definitie", "1.5.1"),
    ]
    assert all(c.metadata.artikel_nummer != "IV" for c in res.chunks)
    assert [c.metadata.chunk_index for c in res.chunks] == [0, 1, 2, 3]
    assert res.totaal_tokens == sum(c.token_count for c in res.chunks) > 0


def test_kopregel_met_plaats_en_tekst_met_leden_en_onderdelen(xml_bestand):
    eerste = parse_officiele_publicatie(xml_bestand, LABEL, "strafrecht").chunks[0]
    kop, tekst = eerste.tekst.split("\n", 1)
    assert kop == (
        f"{LABEL} — Boek 1 Strafvordering in het algemeen › Hoofdstuk 4 De verdachte"
        " › Titel 4.1 Algemene bepalingen › Artikel 1.4.1"
    )
    assert tekst.startswith(
        "1. Als verdachte wordt aangemerkt degene te wiens aanzien:"
    )
    assert "a. een redelijk vermoeden bestaat; b. de vervolging is gericht." in tekst
    assert (
        "2. Hij die zich aan de tenuitvoerlegging onttrekt, blijft verdachte." in tekst
    )
    assert "Artikel 1.4.1" not in tekst  # kop niet dubbel in de tekst
    assert eerste.metadata.sectie == (
        "Boek 1 Strafvordering in het algemeen › Hoofdstuk 4 De verdachte"
        " › Titel 4.1 Algemene bepalingen"
    )


def test_definitie_chunks(xml_bestand):
    defs = [
        c.tekst
        for c in parse_officiele_publicatie(xml_bestand, LABEL).chunks
        if c.metadata.structuur_type == "definitie"
    ]
    assert defs == [
        (
            f"{LABEL} — definitie (artikel 1.5.1, onder a)\n"
            "slachtoffer: het directe en het indirecte slachtoffer;"
        ),
        f"{LABEL} — definitie (artikel 1.5.1)\nfamilielid: de echtgenoot;",
    ]


def test_metadata_voldoet_aan_schema_wetgeving(xml_bestand):
    for c in parse_officiele_publicatie(xml_bestand, LABEL, "strafrecht").chunks:
        m = c.metadata
        assert m.wet_regeling == LABEL
        assert m.rechtsgebied == "strafrecht"
        assert m.bronbestand == "stb-test.xml"
        valideer_chunk_metadata(
            "wetgeving",
            {
                "artikel_nummer": m.artikel_nummer,
                "structuur_type": m.structuur_type,
                "bronbestand": m.bronbestand,
                "sectie": m.sectie,
            },
        )


def test_onleesbaar_bestand_geeft_foutmelding(tmp_path):
    pad = tmp_path / "kapot.xml"
    pad.write_text("<officiele-publicatie><artikel>", encoding="utf-8")
    res = parse_officiele_publicatie(pad, LABEL)
    assert res.chunks == ()
    assert res.fout_melding and res.fout_melding.startswith("XML onleesbaar")


# Nabootsing van Stb. 2026, 57: de wettekst staat genest in wijzig-artikelen; de
# boekcontext van hoofdstuk 10 staat alleen in <wat>.
OP_XML_57 = """<?xml version="1.0" encoding="utf-8"?>
<officiele-publicatie>
  <wijzig-artikel>
    <kop><label>ARTIKEL</label><nr>I</nr></kop>
    <wat>Boek 1, Hoofdstuk 10, van het Wetboek van Strafvordering komt te luiden:</wat>
    <wijziging><wijzig-divisie>
      <kop><label>HOOFDSTUK</label><nr>10</nr><titel>TENUITVOERLEGGING</titel></kop>
      <artikel><kop><label>Artikel</label><nr>1.10.1</nr></kop>
        <al>De tenuitvoerlegging wordt bevorderd door het openbaar ministerie.</al></artikel>
    </wijzig-divisie></wijziging>
  </wijzig-artikel>
  <wijzig-artikel>
    <kop><label>ARTIKEL</label><nr>II</nr></kop>
    <wat>Boek 7 van het Wetboek van Strafvordering komt te luiden:</wat>
    <wijziging><wijzig-divisie>
      <kop><label>BOEK</label><nr>7</nr><titel>INTERNATIONALE SAMENWERKING</titel></kop>
      <wijzig-divisie>
        <kop><label>HOOFDSTUK</label><nr>1</nr><titel>Algemene bepalingen</titel></kop>
        <artikel><kop><label>Artikel</label><nr>7.1.1</nr></kop>
          <al>Dit boek is van toepassing op samenwerking.</al></artikel>
      </wijzig-divisie>
    </wijzig-divisie></wijziging>
  </wijzig-artikel>
  <artikel><kop><label>ARTIKEL</label><nr>IIIA</nr></kop><al>Artikel 24c wordt gewijzigd.</al></artikel>
  <artikel><kop><label>ARTIKEL</label><nr>V</nr></kop><al>Deze wet wordt aangehaald als …</al></artikel>
</officiele-publicatie>
"""


def test_vaststellingswet_boek_uit_wat_en_geen_dubbel_boek(tmp_path):
    pad = tmp_path / "stb-57.xml"
    pad.write_text(OP_XML_57, encoding="utf-8")
    res = parse_officiele_publicatie(pad, LABEL, "strafrecht")
    assert [(c.metadata.artikel_nummer, c.metadata.sectie) for c in res.chunks] == [
        ("1.10.1", "Boek 1 › Hoofdstuk 10 Tenuitvoerlegging"),
        (
            "7.1.1",
            "Boek 7 Internationale samenwerking › Hoofdstuk 1 Algemene bepalingen",
        ),
    ]
    assert res.chunks[0].tekst.startswith(
        f"{LABEL} — Boek 1 › Hoofdstuk 10 Tenuitvoerlegging › Artikel 1.10.1\n"
    )


def test_formeel_artikel_met_lettersuffix_overgeslagen(tmp_path):
    pad = tmp_path / "stb-57.xml"
    pad.write_text(OP_XML_57, encoding="utf-8")
    nummers = {
        c.metadata.artikel_nummer for c in parse_officiele_publicatie(pad, LABEL).chunks
    }
    assert nummers.isdisjoint({"IIIA", "V"})


# --- opslag ------------------------------------------------------------------------


@pytest.fixture
def rag(tmp_path):
    db = str(tmp_path / "rag.db")
    conn = sqlite3.connect(db)
    conn.executescript(SCHEMA_SQL)
    conn.close()
    store = EmbeddingStore(db_path=db)
    cid = store.create_collection("sv-nieuw", dimensions=DIMS, model="test")
    embedder = MagicMock(spec=["embed", "embed_batch", "DIMENSIONS", "MODEL"])
    embedder.DIMENSIONS = DIMS
    embedder.MODEL = "test"
    embedder.embed_batch.side_effect = lambda teksten: [
        np.ones(DIMS, dtype=np.float32) for _ in teksten
    ]
    chunker = MagicMock(spec=["chunk_tekst"])
    return RAGService(chunker, embedder, store, db), db, cid, embedder, chunker


def test_ingest_chunks_slaat_artikelen_op_zonder_chunker(rag, xml_bestand):
    svc, db, cid, _emb, chunker = rag
    res = parse_officiele_publicatie(xml_bestand, LABEL, "strafrecht")
    doc_id = svc.ingest_chunks(
        res,
        collection_id=cid,
        filename="stb-test.xml",
        rechtsgebied="strafrecht",
        bron_type="wetgeving",
    )
    chunker.chunk_tekst.assert_not_called()
    conn = sqlite3.connect(db)
    rijen = conn.execute(
        "SELECT artikel_lid, wet_regeling, bron_type, rechtsgebied FROM rag_chunks "
        "WHERE document_id = ? ORDER BY chunk_index",
        (doc_id,),
    ).fetchall()
    aantal = conn.execute(
        "SELECT chunk_count, file_type FROM rag_documents WHERE id = ?", (doc_id,)
    ).fetchone()
    conn.close()
    assert [r[0] for r in rijen] == ["1.4.1", "1.5.1", "1.5.1", "1.5.1"]
    assert {r[1:] for r in rijen} == {(LABEL, "wetgeving", "strafrecht")}
    assert aantal == (4, "application/xml")


def test_ingest_chunks_rolt_terug_bij_fout(rag, xml_bestand):
    svc, db, cid, emb, _chunker = rag
    emb.embed_batch.side_effect = RuntimeError("API weg")
    res = parse_officiele_publicatie(xml_bestand, LABEL, "strafrecht")
    with pytest.raises(RuntimeError):
        svc.ingest_chunks(res, collection_id=cid, filename="stb-test.xml")
    conn = sqlite3.connect(db)
    assert conn.execute("SELECT COUNT(*) FROM rag_documents").fetchone()[0] == 0
    conn.close()


def test_ingest_document_zonder_tekst_blijft_fout_zonder_chunks(rag):
    svc, _db, cid, _emb, _chunker = rag
    with pytest.raises(ValueError, match="tekst mag niet leeg"):
        svc.ingest_document("", collection_id=cid, filename="leeg.txt")


def test_ingest_chunks_normaliseert_rechtsgebied_per_chunk(rag, xml_bestand):
    svc, db, cid, _emb, _chunker = rag
    res = parse_officiele_publicatie(xml_bestand, LABEL, "Strafrecht")
    doc_id = svc.ingest_chunks(res, collection_id=cid, filename="stb-test.xml")
    conn = sqlite3.connect(db)
    waarden = {
        r[0]
        for r in conn.execute(
            "SELECT rechtsgebied FROM rag_chunks WHERE document_id = ?", (doc_id,)
        )
    }
    conn.close()
    assert waarden == {"strafrecht"}


def test_ingest_chunks_weigert_onbekend_rechtsgebied_zonder_opslag(rag, xml_bestand):
    svc, db, cid, emb, _chunker = rag
    res = parse_officiele_publicatie(xml_bestand, LABEL, "sterrenkunde")
    with pytest.raises(ValueError, match="Onbekend rechtsgebied"):
        svc.ingest_chunks(res, collection_id=cid, filename="stb-test.xml")
    emb.embed_batch.assert_not_called()
    conn = sqlite3.connect(db)
    assert conn.execute("SELECT COUNT(*) FROM rag_documents").fetchone()[0] == 0
    conn.close()


def test_ingest_chunks_rolt_terug_bij_onderbreking(rag, xml_bestand):
    svc, db, cid, emb, _chunker = rag
    emb.embed_batch.side_effect = KeyboardInterrupt
    res = parse_officiele_publicatie(xml_bestand, LABEL, "strafrecht")
    with pytest.raises(KeyboardInterrupt):
        svc.ingest_chunks(res, collection_id=cid, filename="stb-test.xml")
    conn = sqlite3.connect(db)
    assert conn.execute("SELECT COUNT(*) FROM rag_documents").fetchone()[0] == 0
    conn.close()


def test_ingest_chunks_rolt_terug_bij_onderbreking_direct_na_registratie(
    rag, xml_bestand, monkeypatch
):
    svc, db, cid, emb, _chunker = rag
    from services.rag import rag_service

    echte_info = rag_service.logger.info

    def info(bericht, *args, **kwargs):
        if bericht.startswith("Document geregistreerd"):
            raise KeyboardInterrupt  # na de commit van de registratie
        return echte_info(bericht, *args, **kwargs)

    monkeypatch.setattr(rag_service.logger, "info", info)
    res = parse_officiele_publicatie(xml_bestand, LABEL, "strafrecht")
    with pytest.raises(KeyboardInterrupt):
        svc.ingest_chunks(res, collection_id=cid, filename="stb-test.xml")
    emb.embed_batch.assert_not_called()
    conn = sqlite3.connect(db)
    assert conn.execute("SELECT COUNT(*) FROM rag_documents").fetchone()[0] == 0
    conn.close()


def test_teruggedraaide_registratie_raakt_hergebruikt_id_niet(rag, xml_bestand):
    """Een niet-gecommitte registratie wordt teruggedraaid; als SQLite het id
    daarna aan een andere ingest geeft, mag de opruimstap dat document niet
    verwijderen."""
    svc, db, cid, _emb, _chunker = rag
    echte_connect = svc._connect
    eerste = {"klaar": False}

    class Verbinding:
        def __init__(self, conn):
            self._conn = conn

        def __getattr__(self, naam):
            return getattr(self._conn, naam)

        def commit(self):
            if not eerste["klaar"]:
                eerste["klaar"] = True
                raise KeyboardInterrupt  # vóór de commit van de registratie
            return self._conn.commit()

        def rollback(self):
            self._conn.rollback()
            ander = sqlite3.connect(db)  # andere ingest krijgt hetzelfde id
            ander.execute(
                "INSERT INTO rag_documents (collection_id, filename, chunk_count)"
                " VALUES (?, 'ander.xml', 0)",
                (cid,),
            )
            ander.commit()
            ander.close()

    svc._connect = lambda: Verbinding(echte_connect())
    res = parse_officiele_publicatie(xml_bestand, LABEL, "strafrecht")
    with pytest.raises(KeyboardInterrupt):
        svc.ingest_chunks(res, collection_id=cid, filename="stb-test.xml")
    conn = sqlite3.connect(db)
    namen = [r[0] for r in conn.execute("SELECT filename FROM rag_documents")]
    conn.close()
    assert namen == ["ander.xml"]
