"""DEF-620 (RAG fase 1): zoeken met relevantiepoort in de bronbibliotheek.

Een fragment dat het begrip (of een vervoegde vorm als heel woord) niet noemt,
mag nooit als bron worden geleverd; binnen de poort bepaalt de betekenis
(cosine) de volgorde. Zonder zoektermen blijft het oude gedrag. Het webfilter
houdt exact zijn oorspronkelijke semantiek.
"""

from __future__ import annotations

import re
import sqlite3
from unittest.mock import MagicMock

import numpy as np
import pytest

from services.rag.embedding_store import EmbeddingStore
from services.rag.rag_service import RAGService
from tests.unit.services.rag.test_rag_service import DIMS, SCHEMA_SQL
from utils.term_match import (
    _woordvormen_ing,
    noemt_term,
    normaliseer_zoektekst,
    tel_treffers_rag,
    zoekpatronen,
)

pytestmark = [pytest.mark.unit]


def _vec(*waarden: float) -> np.ndarray:
    v = np.zeros(DIMS, dtype=np.float32)
    v[: len(waarden)] = waarden
    return v


def _db(tmp_path) -> tuple[str, EmbeddingStore]:
    db = str(tmp_path / "rag.db")
    conn = sqlite3.connect(db)
    conn.executescript(SCHEMA_SQL)
    conn.close()
    return db, EmbeddingStore(db_path=db)


def _vul(db: str, store: EmbeddingStore, naam: str, rijen: list[tuple]) -> int:
    cid = store.create_collection(naam, dimensions=DIMS, model="test")
    conn = sqlite3.connect(db)
    conn.execute(
        "INSERT INTO rag_documents (collection_id, filename, chunk_count) VALUES (?, ?, ?)",
        (cid, f"{naam}.pdf", len(rijen)),
    )
    conn.commit()
    doc = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    store.store_batch(
        collection_id=cid,
        document_id=doc,
        chunks=[
            {"chunk_text": tekst, "chunk_index": i, **extra}
            for i, (tekst, _v, extra) in enumerate(rijen)
        ],
        embeddings=[v for _t, v, _e in rijen],
    )
    return cid


def _service(db, store, query_vec):
    embedder = MagicMock(spec=["embed", "embed_batch", "DIMENSIONS", "MODEL"])
    embedder.DIMENSIONS = DIMS
    embedder.MODEL = "test"
    embedder.embed.return_value = query_vec
    return RAGService(MagicMock(spec=["chunk_tekst"]), embedder, store, db), embedder


SV = [
    # hoge cosine, noemt het begrip NIET (het "Doortocht"-geval)
    (
        "Artikel 5.4.16 Doortocht van een persoon",
        _vec(1, 0),
        {"rechtsgebied": "strafrecht"},
    ),
    # lagere cosine, noemt een vervoegde vorm
    (
        "Artikel 68 zich aan de tenuitvoerlegging onttrekt",
        _vec(0.2, 1),
        {"rechtsgebied": "strafrecht", "wet_regeling": "Sv", "bron_type": "wetgeving"},
    ),
    (
        "Artikel 80 bij onttrekking aan de schorsing",
        _vec(0.6, 1),
        {"rechtsgebied": "strafrecht", "wet_regeling": "Sv", "bron_type": "wetgeving"},
    ),
    # noemt alleen het synoniem
    (
        "Artikel 99 over ongeoorloofde afwezigheid",
        _vec(0, 1),
        {"rechtsgebied": "strafrecht"},
    ),
    # verkeerde woordfamilie: mag niet door de poort (Codex-review 06-10)
    (
        "De gegevens zijn beschikbaar en staan in het handelsregister",
        _vec(1, 0.1),
        {"rechtsgebied": "strafrecht"},
    ),
]


@pytest.fixture
def sv(tmp_path):
    db, store = _db(tmp_path)
    cid = _vul(db, store, "sv", SV)
    svc, emb = _service(db, store, _vec(1, 0))  # ligt het dichtst bij "Doortocht"
    return svc, store, cid, emb


def _teksten(ctx) -> list[str]:
    return [c["chunk_text"] for c in ctx.chunks]


# --- poort en rangorde -------------------------------------------------------


def test_zonder_term_geen_bron_ook_bij_hoge_cosine(sv):
    svc, _store, cid, _emb = sv
    ctx = svc.retrieve_context("onttrekking", cid, top_k=5, zoektermen=["onttrekking"])
    assert all("Doortocht" not in t for t in _teksten(ctx))
    assert ctx.kandidaten == 2


def test_binnen_de_poort_volgorde_op_betekenis(sv):
    svc, _store, cid, _emb = sv
    ctx = svc.retrieve_context("onttrekking", cid, top_k=5, zoektermen=["onttrekking"])
    assert _teksten(ctx) == [
        "Artikel 80 bij onttrekking aan de schorsing",
        "Artikel 68 zich aan de tenuitvoerlegging onttrekt",
    ]
    assert [c["trefwoord_treffers"] for c in ctx.chunks] == [1, 1]


@pytest.mark.parametrize("begrip", ["beschikking", "handeling"])
def test_verkeerde_woordfamilie_komt_niet_door_de_poort(sv, begrip):
    svc, _store, cid, _emb = sv
    ctx = svc.retrieve_context(begrip, cid, top_k=5, zoektermen=[begrip])
    assert ctx.chunks == []
    assert ctx.kandidaten == 0


def test_geen_treffer_geeft_lege_context(sv):
    svc, _store, cid, _emb = sv
    ctx = svc.retrieve_context("zelfmelder", cid, top_k=5, zoektermen=["zelfmelder"])
    assert ctx.chunks == []
    assert ctx.formatted_context == ""
    assert ctx.kandidaten == 0


def test_lege_zoektermen_is_het_oude_pad(sv):
    svc, _store, cid, _emb = sv
    ctx = svc.retrieve_context("onttrekking", cid, top_k=1, zoektermen=[])
    assert _teksten(ctx) == ["Artikel 5.4.16 Doortocht van een persoon"]
    assert ctx.kandidaten is None


def test_lege_strings_in_zoektermen_worden_genegeerd(sv):
    svc, _store, cid, _emb = sv
    ctx = svc.retrieve_context(
        "onttrekking", cid, top_k=5, zoektermen=["", "  ", "onttrekking"]
    )
    assert ctx.kandidaten == 2


def test_synoniem_telt_mee_en_zit_in_de_embeddingvraag(sv):
    svc, _store, cid, emb = sv
    ctx = svc.retrieve_context(
        "onttrekking",
        cid,
        top_k=5,
        zoektermen=["onttrekking", "ongeoorloofde afwezigheid"],
    )
    assert "Artikel 99 over ongeoorloofde afwezigheid" in _teksten(ctx)
    emb.embed.assert_called_once_with("onttrekking; ongeoorloofde afwezigheid")


def test_zonder_zoektermen_oud_gedrag(sv):
    svc, _store, cid, _emb = sv
    ctx = svc.retrieve_context("onttrekking", cid, top_k=1)
    assert _teksten(ctx) == ["Artikel 5.4.16 Doortocht van een persoon"]
    assert ctx.kandidaten is None


# --- filters ------------------------------------------------------------------


def test_rechtsgebiedfilter_met_terugval_zonder_filter(sv):
    svc, _store, cid, _emb = sv
    ctx = svc.retrieve_context(
        "onttrekking",
        cid,
        top_k=5,
        rechtsgebied="bestuursrecht",
        zoektermen=["onttrekking"],
    )
    assert len(ctx.chunks) == 2  # nul treffers mét filter → één poging zonder
    ctx2 = svc.retrieve_context(
        "onttrekking",
        cid,
        top_k=5,
        rechtsgebied="strafrecht",
        zoektermen=["onttrekking"],
    )
    assert len(ctx2.chunks) == 2


def test_wet_regeling_en_bron_type_filters(sv):
    svc, store, cid, _emb = sv
    hits = store.search_keyword(
        _vec(1, 0), cid, ["onttrekking"], wet_regeling="Sv", bron_type="wetgeving"
    )
    assert len(hits) == 2
    assert (
        store.search_keyword(_vec(1, 0), cid, ["onttrekking"], wet_regeling="Sr") == []
    )


# --- meerdere collections -------------------------------------------------------


def test_twee_collections_globale_top_k_en_filter_per_collection(tmp_path):
    db, store = _db(tmp_path)
    c1 = _vul(db, store, "sv", SV)
    c2 = _vul(
        db,
        store,
        "bjj",
        [
            (
                "Artikel 1 Bjj onttrekking aan het toezicht",
                _vec(0.9, 1),
                {"rechtsgebied": "strafrecht"},
            ),
            (
                "Artikel 2 Bjj onttrekking bestuursrechtelijk",
                _vec(1, 0.05),
                {"rechtsgebied": "bestuursrecht"},
            ),
        ],
    )
    svc, _emb = _service(db, store, _vec(1, 0))
    ctx = svc.retrieve_context_multi(
        "onttrekking",
        collection_ids=[c1, c2],
        top_k=2,
        rechtsgebied="strafrecht",
        zoektermen=["onttrekking"],
    )
    # globaal op cosine over beide collections; bestuursrecht-chunk valt af
    assert _teksten(ctx) == [
        "Artikel 1 Bjj onttrekking aan het toezicht",
        "Artikel 80 bij onttrekking aan de schorsing",
    ]
    assert ctx.kandidaten == 3
    assert ctx.collection_id == 0  # meerdere collections


def test_search_keyword_score_is_cosine(sv):
    _svc, store, cid, _emb = sv
    hits = store.search_keyword(_vec(1, 0), cid, ["onttrekking"])
    assert [round(h["score"], 3) for h in hits] == [
        round(0.6 / np.sqrt(1.36), 3),
        round(0.2 / np.sqrt(1.04), 3),
    ]


# --- termherkenning bronbibliotheek ---------------------------------------------


@pytest.mark.parametrize(
    ("term", "tekst", "verwacht"),
    [
        ("onttrekking", "De verdachte onttrekt zich", 1),
        ("onttrekking", "zich onttrekken aan", 1),
        ("onttrekking", "onttrekking en nog eens onttrekking", 2),
        ("onttrekking", "onttrekking", 1),  # geen dubbeltelling van vormen
        ("beschikking", "De gegevens zijn beschikbaar", 0),
        ("handeling", "het handelsregister", 0),
        ("verklaring", "Hij verklaart dat", 1),
        ("veroordeling", "de rechter veroordeelt", 1),
        ("dagvaarding", "de verdachte wordt gedagvaard en dagvaardt", 1),
        ("onttrekking", "Een ont­trekking aan toezicht", 1),
        ("onttrekking", "Een ont-\ntrekking aan toezicht", 1),
        ("identificatie", "de identiﬁcatie", 1),
        ("coöperatie", "coöperatie", 1),
        ("in beslag", "in beslag", 1),
        ("verdachte", "de verdachten", 1),
        ("om", "omstandigheden", 0),
        ("onttrekking aan toezicht", "toezicht na onttrekking", 1),
        ("wet om", "Wet op het OM", 0),
        ("", "onttrekking", 0),
        ("onttrekking", None, 0),
    ],
)
def test_tel_treffers_rag(term, tekst, verwacht):
    assert tel_treffers_rag(tekst, zoekpatronen(term)) == verwacht


def test_normalisatie_voegt_geen_losse_woorden_samen():
    assert normaliseer_zoektekst("artikel\n12 en\nverder") == "artikel 12 en verder"
    assert normaliseer_zoektekst("ont-\ntrekking") == "onttrekking"
    assert normaliseer_zoektekst("Sv-\nArtikel") == "sv- artikel"  # hoofdletter erna


@pytest.mark.parametrize(
    ("woord", "bevat", "niet"),
    [
        ("onttrekking", {"onttrekt", "onttrekken"}, {"onttrek"}),
        ("beschikking", {"beschikt", "beschikken"}, {"beschik"}),
        ("verklaring", {"verklaart", "verklaren"}, set()),
        ("regeling", {"regelen"}, set()),
        ("toetsing", set(), set()),  # stam te kort
        ("verdachte", set(), set()),  # geen -ing
    ],
)
def test_woordvormen_ing(woord, bevat, niet):
    vormen = set(_woordvormen_ing(woord))
    assert bevat <= vormen
    assert not (niet & vormen)


# --- webfilter: exacte pariteit met het oorspronkelijke _noemt_begrip -----------


def _oud_noemt_begrip(tekst: str, term: str | None) -> bool:
    """Letterlijke kopie van de DEF-620-webimplementatie vóór deze wijziging."""
    begrip = (term or "").strip().lower()
    if not begrip:
        return False
    tekst = tekst.lower()
    if not tekst:
        return False

    def _staat_erin(woord: str) -> bool:
        einde = r"(?!\w)" if len(woord) < 5 else ""
        patroon = r"(?<!\w)" + re.escape(woord) + einde
        return re.search(patroon, tekst) is not None

    if _staat_erin(begrip):
        return True
    woorden = [w for w in begrip.split() if len(w) >= 4]
    return len(woorden) > 1 and all(_staat_erin(w) for w in woorden)


@pytest.mark.parametrize(
    ("tekst", "term"),
    [
        ("Verdachte", "verdachte"),
        ("Verdachten worden gehoord", "verdachte"),
        ("In bijzondere omstandigheden", "om"),
        ("Het OM vervolgt", "om"),
        ("onttrekking aan het toezicht", "Onttrekking"),
        ("toezicht na onttrekking", "onttrekking aan toezicht"),
        ("Wet op het OM", "wet om"),
        ("Waterschapsverordening", "onttrekking"),
        ("ın beslag", "in beslag"),
        ("IN beslag", "in   beslag"),
        ("De verdachte onttrekt zich", "onttrekking"),
        ("in beslag", "in beslag"),
        ("", "verdachte"),
        ("verdachte", None),
        ("İstanbul", "istanbul"),
    ],
)
def test_webfilter_gelijk_aan_oud(tekst, term):
    assert noemt_term(tekst, term) is _oud_noemt_begrip(tekst, term)
