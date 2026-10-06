"""DEF-620 (RAG fase 3): BWB- en EU-parser en de relevantiepoort zonder kopregel."""

from __future__ import annotations

import sqlite3

import numpy as np
import pytest

from services.rag.bwb_parser import parse_bwb_toestand
from services.rag.embedding_store import EmbeddingStore
from services.rag.eu_parser import parse_eu_xhtml
from services.rag.metadata_schemas import valideer_chunk_metadata
from tests.unit.services.rag.test_rag_service import DIMS, SCHEMA_SQL

pytestmark = [pytest.mark.unit]

BWB_XML = """<?xml version="1.0" encoding="UTF-8"?>
<toestand bwb-id="BWBR0009999" bwb-ng-vast-deel="http://wetten.overheid.nl/id/BWBR0009999/2026-01-01/0">
  <wetgeving soort="wet"><wet-besluit><wettekst>
    <hoofdstuk>
      <kop><label>Hoofdstuk</label><nr>I</nr><titel>BEGRIPSBEPALINGEN</titel></kop>
      <artikel status="goed">
        <kop><label>Artikel</label><nr>1</nr><titel>Definities</titel></kop>
        <al>Voor de toepassing van deze wet wordt verstaan onder: </al>
        <lijst>
          <li><li.nr>a.</li.nr><al>inrichting: een penitentiaire inrichting;</al>
            <meta-data><jcis><jci verwijzing="x"/></jcis></meta-data></li>
          <li><li.nr>b.</li.nr><al>gedetineerde: degene die in een inrichting verblijft;</al></li>
        </lijst>
        <meta-data><brondata><publicatiejaar>2025</publicatiejaar></brondata></meta-data>
      </artikel>
      <artikel status="vervallen"><kop><label>Artikel</label><nr>2</nr></kop><al>Oude tekst.</al></artikel>
      <artikel status="nogniet"><kop><label>Artikel</label><nr>3</nr></kop><al>Toekomstige tekst.</al></artikel>
      <artikel status="goed"><kop><label>Artikel</label><nr>4</nr></kop><redactie>Vervallen.</redactie></artikel>
      <paragraaf>
        <kop><label>§</label><nr>2</nr><titel>Toezicht</titel></kop>
        <artikel status="goed"><kop><label>Artikel</label><nr>5</nr></kop>
          <lid><lidnr>1</lidnr><al>De directeur houdt <nadruk>toezicht</nadruk>.</al></lid>
          <lid status="vervallen"><lidnr>2</lidnr><al>Vervallen lid.</al></lid>
          <lid status="nogniet"><lidnr>3</lidnr><al>Toekomstig lid.</al></lid></artikel>
      </paragraaf>
      <afdeling status="nogniet">
        <kop><label>Afdeling</label><nr>3</nr><titel>Toekomst</titel></kop>
        <artikel status="goed"><kop><label>Artikel</label><nr>6</nr></kop>
          <al>Geldt nog niet.</al></artikel>
      </afdeling>
    </hoofdstuk>
  </wettekst></wet-besluit></wetgeving>
</toestand>
"""

EU_OJ = """<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><body><div class="eli-container">
<div id="rct_1"><p class="oj-normal">(1) Overweging die niet meegaat.</p></div>
<div id="enc_1" class="eli-subdivision">
 <div id="cpt_I">
  <p class="oj-ti-section-1">HOOFDSTUK I</p>
  <div class="eli-title" id="cpt_I.tit_1"><p class="oj-ti-section-2">Algemene bepalingen</p></div>
  <div class="eli-subdivision" id="art_4">
   <p class="oj-ti-art">Artikel 4</p>
   <div class="eli-title" id="art_4.tit_1"><p class="oj-sti-art">Definities</p></div>
   <p class="oj-normal">Voor de toepassing van deze verordening wordt verstaan onder:</p>
   <p class="oj-normal">1) <span class="oj-bold">„persoonsgegevens”</span>: alle informatie over een persoon;</p>
   <p class="oj-normal">11) <span class="oj-bold">„toestemming”</span> van de betrokkene: elke vrije wilsuiting;</p>
   <p class="oj-normal">Zie<span class="oj-note-tag">1</span> ook hieronder over de hand<span class="oj-italic">tekening</span>.</p>
  </div>
 </div>
</div>
<div id="anx_I"><div class="eli-subdivision" id="art_99"><p class="oj-ti-art">Artikel 99</p><p class="oj-normal">Bijlagetekst.</p></div></div>
</div></body></html>
"""

EU_CONSOLIDATIE = """<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><body>
<div id="cpt_II">
 <p class="title-division-1">HOOFDSTUK II</p>
 <p class="title-division-2">ELEKTRONISCHE IDENTIFICATIE</p>
 <div id="cpt_II.sct_1">
  <p class="title-division-1">AFDELING 1</p>
  <p class="title-division-2">Europese portemonnee</p>
  <div class="eli-subdivision" id="art_5a">
   <p class="title-article-norm">Artikel 5 bis</p>
   <div class="eli-title"><p class="stitle-article-norm">Europese portemonnees</p></div>
   <p class="modref"><a>▼M2</a></p>
   <div class="norm"><span class="no-parag">1.  </span><div class="norm inline-element">Elke lidstaat verstrekt een portemonnee.</div></div>
  </div>
 </div>
</div>
</body></html>
"""


@pytest.fixture
def bwb(tmp_path):
    pad = tmp_path / "BWBR0009999_2026-01-01_0.xml"
    pad.write_text(BWB_XML, encoding="utf-8")
    return parse_bwb_toestand(pad, "Testwet (versie 1-1-2026)", "penitentiair_recht")


def test_bwb_alleen_geldende_artikelen_met_inhoud(bwb):
    artikelen = [
        c.metadata.artikel_nummer
        for c in bwb.chunks
        if c.metadata.structuur_type == "artikel"
    ]
    assert artikelen == ["1", "5"]  # 2 vervallen, 3 nog niet, 4 alleen noot


def test_bwb_kopregel_titel_en_geen_metagegevens(bwb):
    eerste = bwb.chunks[0]
    kop, tekst = eerste.tekst.split("\n", 1)
    assert kop == (
        "Testwet (versie 1-1-2026) — Hoofdstuk I Begripsbepalingen › Artikel 1 Definities"
    )
    assert "2025" not in tekst and "jci" not in tekst
    assert tekst.startswith("Voor de toepassing van deze wet wordt verstaan onder:")
    vijf = next(c for c in bwb.chunks if c.metadata.artikel_nummer == "5")
    assert vijf.metadata.sectie == "Hoofdstuk I Begripsbepalingen › § 2 Toezicht"
    assert vijf.tekst.endswith("1 De directeur houdt toezicht.")


def test_bwb_begripsbepalingen(bwb):
    defs = [c.tekst for c in bwb.chunks if c.metadata.structuur_type == "definitie"]
    assert defs == [
        (
            "Testwet (versie 1-1-2026) — definitie (artikel 1, onder a)\n"
            "inrichting: een penitentiaire inrichting;"
        ),
        (
            "Testwet (versie 1-1-2026) — definitie (artikel 1, onder b)\n"
            "gedetineerde: degene die in een inrichting verblijft;"
        ),
    ]


def test_bwb_metadata_voldoet_aan_schema(bwb):
    for c in bwb.chunks:
        assert c.metadata.rechtsgebied == "penitentiair_recht"
        valideer_chunk_metadata(
            "wetgeving",
            {
                "artikel_nummer": c.metadata.artikel_nummer,
                "structuur_type": c.metadata.structuur_type,
                "bronbestand": c.metadata.bronbestand,
                "sectie": c.metadata.sectie,
            },
        )


def test_bwb_verkeerde_of_kapotte_xml(tmp_path):
    kapot = tmp_path / "kapot.xml"
    kapot.write_text("<toestand>", encoding="utf-8")
    assert parse_bwb_toestand(kapot, "X").fout_melding.startswith("XML onleesbaar")
    ander = tmp_path / "ander.xml"
    ander.write_text("<officiele-publicatie/>", encoding="utf-8")
    assert "geen BWB-toestand" in parse_bwb_toestand(ander, "X").fout_melding


def test_eu_oorspronkelijk_publicatieblad(tmp_path):
    pad = tmp_path / "EU_test.xhtml"
    pad.write_text(EU_OJ, encoding="utf-8")
    res = parse_eu_xhtml(pad, "AVG", "europees_recht")
    assert res.fout_melding is None
    artikel = res.chunks[0]
    kop, tekst = artikel.tekst.split("\n", 1)
    assert kop == "AVG — Hoofdstuk I Algemene bepalingen › Artikel 4 Definities"
    assert "Overweging" not in artikel.tekst and "Bijlagetekst" not in artikel.tekst
    assert "Zie ook hieronder over de handtekening." in tekst  # inline aaneen
    defs = [
        c.tekst.split("\n")[1]
        for c in res.chunks
        if c.metadata.structuur_type == "definitie"
    ]
    assert defs == [
        "persoonsgegevens: alle informatie over een persoon;",
        (
            "toestemming van de betrokkene: elke vrije wilsuiting; "
            "Zie ook hieronder over de handtekening."
        ),
    ]
    assert [c.metadata.artikel_nummer for c in res.chunks] == ["4", "4", "4"]


def test_eu_consolidatie_met_afdeling_en_bis_artikel(tmp_path):
    pad = tmp_path / "EU_cons.xhtml"
    pad.write_text(EU_CONSOLIDATIE, encoding="utf-8")
    (chunk,) = parse_eu_xhtml(pad, "eIDAS").chunks
    assert chunk.metadata.artikel_nummer == "5 bis"
    assert chunk.tekst == (
        "eIDAS — Hoofdstuk II Elektronische identificatie › Afdeling 1 Europese "
        "portemonnee › Artikel 5 bis Europese portemonnees\n"
        "1. Elke lidstaat verstrekt een portemonnee."
    )


def test_eu_onleesbaar(tmp_path):
    pad = tmp_path / "kapot.xhtml"
    pad.write_text("<html><body>", encoding="utf-8")
    assert parse_eu_xhtml(pad, "X").fout_melding.startswith("XHTML onleesbaar")


# --- relevantiepoort zonder kopregel ------------------------------------------------


def test_poort_negeert_wetnaam_in_kopregel(tmp_path):
    db = str(tmp_path / "rag.db")
    conn = sqlite3.connect(db)
    conn.executescript(SCHEMA_SQL)
    conn.close()
    store = EmbeddingStore(db_path=db)
    cid = store.create_collection("wpg", dimensions=DIMS, model="test")
    vec = np.ones(DIMS, dtype=np.float32)
    wet = "Wet politiegegevens (versie 1-9-2026)"
    store.store_batch(
        collection_id=cid,
        document_id=None,
        chunks=[
            {"chunk_text": f"{wet} — Hoofdstuk 1 › Artikel 2\nDe korpschef beslist.",
             "chunk_index": 0, "wet_regeling": wet, "artikel_lid": "2"},
            {"chunk_text": f"{wet} — Hoofdstuk 1 › Artikel 8\nPolitiegegevens worden verwerkt.",
             "chunk_index": 1, "wet_regeling": wet, "artikel_lid": "8"},
            {"chunk_text": "Politiegegevens in een pdf\nzonder wetkopregel.",
             "chunk_index": 2, "wet_regeling": "pdf", "artikel_lid": None},
            {"chunk_text": f"{wet}\nInleiding over de korpschef.",
             "chunk_index": 3, "wet_regeling": wet, "artikel_lid": "pdf-titel"},
            {"chunk_text": f"{wet} — definitie (artikel 1, onder a)\nkorpschef: de chef.",
             "chunk_index": 4, "wet_regeling": wet, "artikel_lid": "1"},
        ],
        embeddings=[vec] * 5,
    )  # fmt: skip
    treffers = store.search_keyword(vec, cid, ["politiegegevens"])
    # wetchunks zonder het begrip in de tekst vallen af (artikel 2, definitie);
    # een pdf-chunk die met de wetnaam begint, houdt zijn eerste regel
    assert sorted(t["artikel_lid"] or "pdf" for t in treffers) == [
        "8", "pdf", "pdf-titel",
    ]  # fmt: skip


def test_bwb_niet_geldende_leden_en_onderdelen(bwb):
    vijf = next(c for c in bwb.chunks if c.metadata.artikel_nummer == "5")
    assert "Vervallen lid" not in vijf.tekst and "Toekomstig lid" not in vijf.tekst
    assert "6" not in {
        c.metadata.artikel_nummer for c in bwb.chunks
    }  # afdeling nogniet


def test_rechtsgebiedfilter_verruimt_pas_als_geen_enkele_collectie_treft(tmp_path):
    """Met één collectie per wet: treffers binnen het rechtsgebied gaan voor;
    andere wetten vallen niet per collectie terug op 'zonder filter'."""
    from unittest.mock import MagicMock

    from services.rag.rag_service import RAGService

    db = str(tmp_path / "rag.db")
    conn = sqlite3.connect(db)
    conn.executescript(SCHEMA_SQL)
    conn.close()
    store = EmbeddingStore(db_path=db)
    vec = np.ones(DIMS, dtype=np.float32)
    ids = {}
    for naam, rg in (("Wpg", "strafrecht"), ("AVG", "europees_recht")):
        cid = store.create_collection(naam, dimensions=DIMS, model="test")
        ids[naam] = cid
        store.store_batch(
            collection_id=cid,
            document_id=None,
            chunks=[{"chunk_text": f"{naam}: persoonsgegevens worden verwerkt.",
                     "chunk_index": 0, "rechtsgebied": rg, "wet_regeling": naam}],
            embeddings=[vec],
        )  # fmt: skip
    embedder = MagicMock(spec=["embed", "embed_batch", "DIMENSIONS", "MODEL"])
    embedder.embed.return_value = vec
    svc = RAGService(MagicMock(), embedder, store, db)
    alle = list(ids.values())

    ctx = svc.retrieve_context_multi(
        "persoonsgegevens",
        alle,
        rechtsgebied="strafrecht",
        zoektermen=["persoonsgegevens"],
    )
    assert [c["wet_regeling"] for c in ctx.chunks] == ["Wpg"]

    ctx = svc.retrieve_context_multi(
        "persoonsgegevens",
        alle,
        rechtsgebied="bestuursrecht",
        zoektermen=["persoonsgegevens"],
    )
    assert sorted(c["wet_regeling"] for c in ctx.chunks) == ["AVG", "Wpg"]
