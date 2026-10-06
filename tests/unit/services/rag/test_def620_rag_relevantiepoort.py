"""DEF-620 (RAG fase 1): zoeken met relevantiepoort in de bronbibliotheek.

Een fragment dat het begrip (of een zoekterm) niet noemt, mag nooit als bron
worden geleverd; binnen de fragmenten die het begrip noemen bepaalt de
betekenis (cosine) de volgorde. Zonder zoektermen blijft het oude gedrag.
"""

from __future__ import annotations

import sqlite3
from unittest.mock import MagicMock

import numpy as np
import pytest

from services.rag.embedding_store import EmbeddingStore
from services.rag.rag_service import RAGService
from tests.unit.services.rag.test_rag_service import DIMS, SCHEMA_SQL
from utils.term_match import noemt_term, tel_treffers

pytestmark = [pytest.mark.unit]


def _vec(*waarden: float) -> np.ndarray:
    v = np.zeros(DIMS, dtype=np.float32)
    v[: len(waarden)] = waarden
    return v


@pytest.fixture
def opstelling(tmp_path):
    db = str(tmp_path / "rag.db")
    conn = sqlite3.connect(db)
    conn.executescript(SCHEMA_SQL)
    conn.close()
    store = EmbeddingStore(db_path=db)
    cid = store.create_collection("sv", dimensions=DIMS, model="test")
    conn = sqlite3.connect(db)
    conn.execute(
        "INSERT INTO rag_documents (collection_id, filename, chunk_count) "
        "VALUES (?, 'sv.pdf', 4)",
        (cid,),
    )
    conn.commit()
    doc = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    store.store_batch(
        collection_id=cid,
        document_id=doc,
        chunks=[
            # hoge cosine, noemt het begrip NIET (het "Doortocht"-geval)
            {
                "chunk_text": "Artikel 5.4.16 Doortocht van een persoon",
                "chunk_index": 0,
                "rechtsgebied": "strafrecht",
            },
            # lagere cosine, noemt het begrip wel
            {
                "chunk_text": "Artikel 68 zich aan de tenuitvoerlegging onttrekt",
                "chunk_index": 1,
                "rechtsgebied": "strafrecht",
            },
            {
                "chunk_text": "Artikel 80 bij onttrekking aan de schorsing",
                "chunk_index": 2,
                "rechtsgebied": "strafrecht",
            },
            # noemt alleen het synoniem
            {
                "chunk_text": "Artikel 99 over ongeoorloofde afwezigheid",
                "chunk_index": 3,
                "rechtsgebied": "strafrecht",
            },
        ],
        embeddings=[_vec(1, 0), _vec(0.2, 1), _vec(0.6, 1), _vec(0, 1)],
    )
    embedder = MagicMock(spec=["embed", "embed_batch", "DIMENSIONS", "MODEL"])
    embedder.DIMENSIONS = DIMS
    embedder.MODEL = "test"
    embedder.embed.return_value = _vec(1, 0)  # ligt het dichtst bij "Doortocht"
    svc = RAGService(MagicMock(spec=["chunk_tekst"]), embedder, store, db)
    return svc, store, cid, embedder


def _teksten(ctx) -> list[str]:
    return [c["chunk_text"] for c in ctx.chunks]


def test_zonder_term_geen_bron_ook_bij_hoge_cosine(opstelling):
    svc, _store, cid, _emb = opstelling
    ctx = svc.retrieve_context("onttrekking", cid, top_k=5, zoektermen=["onttrekking"])
    assert all("Doortocht" not in t for t in _teksten(ctx))
    assert ctx.kandidaten == 2


def test_binnen_de_poort_volgorde_op_betekenis(opstelling):
    svc, _store, cid, _emb = opstelling
    ctx = svc.retrieve_context("onttrekking", cid, top_k=5, zoektermen=["onttrekking"])
    assert _teksten(ctx) == [
        "Artikel 80 bij onttrekking aan de schorsing",
        "Artikel 68 zich aan de tenuitvoerlegging onttrekt",
    ]
    assert all(c["trefwoord_treffers"] >= 1 for c in ctx.chunks)


def test_geen_treffer_geeft_lege_context(opstelling):
    svc, _store, cid, _emb = opstelling
    ctx = svc.retrieve_context("zelfmelder", cid, top_k=5, zoektermen=["zelfmelder"])
    assert ctx.chunks == []
    assert ctx.formatted_context == ""
    assert ctx.kandidaten == 0


def test_synoniem_telt_mee_en_zit_in_de_embeddingvraag(opstelling):
    svc, _store, cid, emb = opstelling
    ctx = svc.retrieve_context(
        "onttrekking",
        cid,
        top_k=5,
        zoektermen=["onttrekking", "ongeoorloofde afwezigheid"],
    )
    assert "Artikel 99 over ongeoorloofde afwezigheid" in _teksten(ctx)
    emb.embed.assert_called_once_with("onttrekking; ongeoorloofde afwezigheid")


def test_multi_collection_zelfde_poort(opstelling):
    svc, _store, cid, _emb = opstelling
    ctx = svc.retrieve_context_multi(
        "onttrekking", collection_ids=[cid], top_k=1, zoektermen=["onttrekking"]
    )
    assert _teksten(ctx) == ["Artikel 80 bij onttrekking aan de schorsing"]
    assert ctx.kandidaten == 2


def test_rechtsgebiedfilter_met_terugval_zonder_filter(opstelling):
    svc, _store, cid, _emb = opstelling
    # geen enkel fragment heeft rechtsgebied 'bestuursrecht' → één poging zonder filter
    ctx = svc.retrieve_context(
        "onttrekking",
        cid,
        top_k=5,
        rechtsgebied="bestuursrecht",
        zoektermen=["onttrekking"],
    )
    assert len(ctx.chunks) == 2
    ctx2 = svc.retrieve_context(
        "onttrekking",
        cid,
        top_k=5,
        rechtsgebied="strafrecht",
        zoektermen=["onttrekking"],
    )
    assert len(ctx2.chunks) == 2


def test_zonder_zoektermen_oud_gedrag(opstelling):
    svc, _store, cid, _emb = opstelling
    ctx = svc.retrieve_context("onttrekking", cid, top_k=1)
    assert _teksten(ctx) == ["Artikel 5.4.16 Doortocht van een persoon"]
    assert ctx.kandidaten is None


def test_search_keyword_score_is_cosine(opstelling):
    _svc, store, cid, _emb = opstelling
    hits = store.search_keyword(_vec(1, 0), cid, ["onttrekking", "onttrek"])
    assert [round(h["score"], 3) for h in hits] == [
        round(0.6 / np.sqrt(1.36), 3),
        round(0.2 / np.sqrt(1.04), 3),
    ]


@pytest.mark.parametrize(
    ("tekst", "term", "verwacht"),
    [
        ("Verdachte", "verdachte", True),
        ("Verdachten worden gehoord", "verdachte", True),
        ("In bijzondere omstandigheden", "om", False),
        ("Het OM vervolgt", "om", True),
        ("onttrekking aan het toezicht", "Onttrekking", True),
        ("toezicht na onttrekking", "onttrekking aan toezicht", True),
        ("Wet op het OM", "wet om", False),
        ("Waterschapsverordening", "onttrekking", False),
        (None, "verdachte", False),
        ("verdachte", None, False),
    ],
)
def test_noemt_term(tekst, term, verwacht):
    assert noemt_term(tekst, term) is verwacht


def test_tel_treffers():
    assert tel_treffers("onttrekking en nog eens onttrekking", "onttrekking") == 2
    assert (
        tel_treffers(
            "toezicht ... onttrekking ... onttrekking", "onttrekking aan toezicht"
        )
        == 1
    )


@pytest.mark.parametrize(
    ("term", "verwacht"),
    [
        ("onttrekking", ["onttrekking", "onttrek"]),
        ("inbeslagneming", ["inbeslagneming", "inbeslagnem"]),
        ("dagvaarding", ["dagvaarding", "dagvaard"]),
        ("ongeoorloofde afwezigheid", ["ongeoorloofde afwezigheid"]),
        ("regeling", ["regeling"]),  # stam 'regel' te kort
        ("toetsing", ["toetsing"]),
        ("verdachte", ["verdachte"]),
        ("", []),
    ],
)
def test_zoekvormen(term, verwacht):
    from utils.term_match import zoekvormen

    assert zoekvormen(term) == verwacht
