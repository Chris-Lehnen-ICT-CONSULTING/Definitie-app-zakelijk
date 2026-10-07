"""DEF-844: bronrangorde door de echte keten orchestrator → promptservice.

Echte `DefinitionOrchestratorV2` en echte `PromptServiceV2` (stub-promptbouwer,
bekende budgetten); AI, cleaning, validatie en repository zijn offline doubles.
Uitgangspunt (Codex-review, besluit Cowork): de rangorde verandert alleen de
**volgorde**, nooit de **selectie** van wat in de prompt komt. Bewijst:

* GAT-scenario (DEF-837 hertest 3, "verdachte"): wetsartikelen vóór
  Wikipedia, in weergave/opslag én prompt;
* de selectie (top-K-markering, `include_all_hits`, budgetten) is gelijk aan
  die zonder rangorde — in beide standen van `include_all_hits`;
* prompt en weergave hebben dezelfde volgorde, ook bij gemengde brontypen;
* een upload via de uploadroute telt nooit als wettelijk, ook niet met het
  label "wetgeving" (echte RAGService, tijdelijke database).

Geen echt model, geen netwerk, geen productiedatabase.
"""

import sqlite3
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest

import services.orchestrators.definition_orchestrator_v2 as orch_mod
import services.prompts.prompt_service_v2 as psv2
from domain.sources.rangorde import RANG_EIGEN, UPLOAD_COLLECTIE, bronrang
from services.interfaces import (
    AIGenerationResult,
    CleaningResult,
    GenerationRequest,
    LookupResult,
    OrchestratorConfig,
    WebSource,
)
from services.orchestrators.definition_orchestrator_v2 import DefinitionOrchestratorV2
from services.prompts.prompt_service_v2 import PromptServiceV2
from services.rag.embedding_service import EmbeddingService
from services.rag.embedding_store import EmbeddingStore
from services.rag.models import ChunkingResult, ChunkMetadata, DocumentChunk
from services.rag.rag_service import RAGService
from tests.unit.services.rag.test_rag_service import SCHEMA_SQL

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]

BEGRIP = "verdachte"
DEFINITIE = "Persoon te wiens aanzien een redelijk vermoeden van schuld bestaat."
BIBLIOTHEEK = "Wetboek van Strafvordering"
WIKIPEDIA = {
    "provider": "Wikipedia",
    "url": "https://nl.wikipedia.org/wiki/Verdachte",
    "title": "Wikipedia",
    "snippet": "Een verdachte is iemand die verdacht wordt van een strafbaar feit.",
    "score": 1.0,
}
WIKTIONARY = {
    "provider": "Wiktionary",
    "url": "https://nl.wiktionary.org/wiki/verdachte",
    "title": "verdachte (wiktionary)",
    "snippet": "verdachte: iemand die van iets verdacht wordt.",
    "score": 0.95,
}
BRAVE = {
    "provider": "Brave Search",
    "url": "https://example.org/verdachte",
    "title": "Zoekresultaat verdachte",
    "snippet": "Algemene uitleg over de verdachte in het strafproces.",
    "score": 0.9,
}
WETTEN = {
    "provider": "Wetgeving.nl",
    "url": "https://wetten.overheid.nl/BWBR0001903/2026-07-01#Artikel27",
    "title": "Wetboek van Strafvordering art. 27",
    "snippet": "Als verdachte wordt aangemerkt degene te wiens aanzien ...",
    "score": 0.6,
}
KAMERSTUK = {
    "provider": "Overheid.nl",
    "url": "https://zoek.officielebekendmakingen.nl/kst-36000-1.html",
    "title": "Kamerstuk 36000, nr. 1",
    "snippet": "Memorie van toelichting over de positie van de verdachte.",
    "score": 0.5,
    "document_type": "Kamerstuk",
}


def _chunk(
    chunk_id: int,
    artikel: str,
    score: float,
    *,
    bron_type: str = "wetgeving",
    collectie: str = BIBLIOTHEEK,
) -> dict:
    return {
        "chunk_id": chunk_id,
        "document_id": 900,
        "bron_type": bron_type,
        "collection_name": collectie,
        "rechtsgebied": "Strafrecht",
        "wet_regeling": "Wetboek van Strafvordering",
        "artikel_lid": artikel,
        "chunk_text": f"Artikel {artikel}: de verdachte (fragment {chunk_id}).",
        "score": score,
    }


GAT_CHUNKS = [
    _chunk(1, "1.4.1", 0.47),
    _chunk(2, "27", 0.46),
    _chunk(3, "1.4.2", 0.41),
    _chunk(4, "27d", 0.41),
    _chunk(5, "2.5.4", 0.40),
]


class _StubBuilder:
    def build_prompt(self, begrip, context):
        return "PROMPT_BODY"


@pytest.fixture
def generate(monkeypatch):
    from voorbeelden import unified_voorbeelden

    monkeypatch.setattr(
        unified_voorbeelden,
        "genereer_alle_voorbeelden_async",
        AsyncMock(return_value={}),
    )
    monkeypatch.setenv("RAG_MIN_SCORE", "0.3")
    monkeypatch.setenv("DOCUMENT_SNIPPETS_ENABLED", "true")

    async def run(
        *,
        web=(),
        chunks=None,
        rag_service=None,
        docs=None,
        include_all_hits=True,  # productiestandaard (web_lookup_defaults.yaml)
    ):
        def _cfg():
            return {
                "web_lookup": {
                    "prompt_augmentation": {
                        "enabled": True,
                        "include_all_hits": include_all_hits,
                        "max_snippets": 5,
                        "max_tokens_per_snippet": 300,
                        "total_token_budget": 1500,
                        "prioritize_juridical": True,
                    },
                    "rag_injection": {
                        "max_tokens_per_chunk": 600,
                        "total_token_budget": 2500,
                        "max_chunks": 5,
                    },
                }
            }

        monkeypatch.setattr(psv2, "load_web_lookup_config", _cfg)
        prompt = PromptServiceV2()
        prompt.prompt_generator = _StubBuilder()
        spy = AsyncMock(wraps=prompt.build_generation_prompt)
        ai = AsyncMock()
        ai.generate_definition.return_value = AIGenerationResult(
            text=DEFINITIE, model="offline", tokens_used=1, generation_time=0.0
        )
        cleaning = AsyncMock()
        cleaning.clean_text.return_value = CleaningResult(
            original_text=DEFINITIE, cleaned_text=DEFINITIE, was_cleaned=False
        )
        validation = AsyncMock()
        validation.validate_definition.return_value = {
            "version": "1.0.0",
            "overall_score": 0.85,
            "is_acceptable": True,
            "violations": [],
            "passed_rules": [],
            "detailed_scores": {},
            "system": {},
        }
        repo = MagicMock()
        repo.save.return_value = 42
        rag = rag_service
        if chunks is not None:
            rag = MagicMock()
            rag.retrieve_context.return_value = SimpleNamespace(
                chunks=deepcopy(chunks), collection_id=7
            )
        web_service = SimpleNamespace(
            lookup=AsyncMock(
                return_value=[
                    LookupResult(
                        term=BEGRIP,
                        source=WebSource(
                            name=w["provider"], url=w["url"], confidence=w["score"]
                        ),
                        definition=w["snippet"],
                        metadata={
                            "dc_title": w["title"],
                            **(
                                {"dc_type": w["document_type"]}
                                if "document_type" in w
                                else {}
                            ),
                        },
                    )
                    for w in web
                ]
            )
        )
        orch = DefinitionOrchestratorV2(
            prompt_service=SimpleNamespace(build_generation_prompt=spy),
            ai_service=ai,
            validation_service=validation,
            cleaning_service=cleaning,
            repository=repo,
            web_lookup_service=web_service,
            rag_service=rag,
            config=OrchestratorConfig(
                enable_feedback_loop=False, enable_enhancement=False
            ),
        )
        response = await orch.create_definition(
            GenerationRequest(
                id="def844",
                begrip=BEGRIP,
                ontologische_categorie="type",
                organisatorische_context=["OM"],
                rag_collection_id=7 if chunks is not None else None,
            ),
            context=(
                {"documents": {"snippets": deepcopy(docs)}}
                if docs is not None
                else None
            ),
        )
        assert response.success, response.error
        return SimpleNamespace(
            md=repo.save.call_args.args[0].metadata,
            context=spy.call_args.kwargs["context"],
            prompt_text=ai.generate_definition.call_args.kwargs["prompt"],
        )

    return run


def _labels(bronnen):
    return [b.get("artikel_lid") or b.get("title") for b in bronnen]


def _in_prompt(bronnen):
    return [b for b in bronnen if b.get("used_in_prompt")]


def _selectie(receipt):
    """Wat er in de prompt kwam en wat niet (met reden) — zonder volgorde."""
    gebruikt = {(r["source_type"], r["input_index"]) for r in receipt["sources"]}
    weggelaten = {
        (r["source_type"], r["input_index"], r["reason"]) for r in receipt["omitted"]
    }
    return gebruikt, weggelaten


def _neutraliseer_rangorde(monkeypatch):
    """De keten zonder DEF-844: geen herordening in orchestrator of prompt."""
    monkeypatch.setattr(orch_mod, "rangschik_bronnen", list)
    monkeypatch.setattr(psv2, "sorteersleutel", lambda _bron: (0, 0, 0.0))


def _assert_prompt_volgt_weergave(result):
    """Prompt- en weergavevolgorde zijn gelijk: de in de prompt opgenomen
    bronnen staan in de weergave in kwitantievolgorde, en hun passages staan
    in de prompttekst in diezelfde volgorde."""
    gebruikt = _in_prompt(result.md["sources"])
    assert [b["receipt_nr"] for b in gebruikt] == list(range(1, len(gebruikt) + 1))
    receipt = result.md["source_receipt"]["sources"]
    posities = [result.prompt_text.index(r["xml"]) for r in receipt]
    assert posities == sorted(posities)


# --- GAT-scenario ------------------------------------------------------------


async def test_gat_scenario_weergave_wetsartikelen_boven_wikipedia(generate):
    result = await generate(web=[WIKIPEDIA], chunks=GAT_CHUNKS)
    assert _labels(result.md["sources"]) == [
        "1.4.1",
        "27",
        "1.4.2",
        "27d",
        "2.5.4",
        "Wikipedia",
    ]
    # Opslag en weergave delen dezelfde volgorde.
    assert _labels(result.md["provenance_sources"]) == _labels(result.md["sources"])


async def test_gat_scenario_prompt_wetsartikelen_boven_wikipedia(generate):
    result = await generate(web=[WIKIPEDIA], chunks=GAT_CHUNKS)
    receipt = result.md["source_receipt"]
    assert [(r["nr"], r["source_type"]) for r in receipt["sources"]] == [
        (1, "rag"),
        (2, "rag"),
        (3, "rag"),
        (4, "rag"),
        (5, "rag"),
        (6, "web"),
    ]
    tekst = result.prompt_text
    assert tekst.index("Artikel 1.4.1: de verdachte") < tekst.index(
        WIKIPEDIA["snippet"]
    )
    # De kwitantie koppelt na het herordenen nog steeds elke bron.
    assert result.md["source_receipt_correlation"]["verified"] == 6
    assert result.md["source_receipt_correlation"]["unmatched"] == 0
    nrs = {
        b.get("artikel_lid") or b["title"]: b["receipt_nr"]
        for b in result.md["sources"]
    }
    assert nrs["1.4.1"] == 1 and nrs["Wikipedia"] == 6
    _assert_prompt_volgt_weergave(result)


# --- Punt 4/5: alleen volgorde, nooit selectie; beide include_all_hits ------


@pytest.mark.parametrize("include_all_hits", [True, False])
async def test_rangorde_verandert_de_selectie_niet(
    generate, monkeypatch, include_all_hits
):
    web = [WIKIPEDIA, WIKTIONARY, BRAVE, WETTEN]
    met = await generate(web=web, chunks=GAT_CHUNKS, include_all_hits=include_all_hits)
    _neutraliseer_rangorde(monkeypatch)
    zonder = await generate(
        web=web, chunks=GAT_CHUNKS, include_all_hits=include_all_hits
    )

    assert _selectie(met.md["source_receipt"]) == _selectie(zonder.md["source_receipt"])
    # Webkanaal en top-K-markering exact als vóór DEF-844: op webscore.
    for result in (met, zonder):
        web_ctx = result.context["web_lookup"]["sources"]
        assert [s["url"] for s in web_ctx] == [w["url"] for w in web]
        assert [s["used_in_prompt"] for s in web_ctx] == [True, True, True, False]


async def test_include_all_hits_uit_wetsbron_buiten_top_k_blijft_buiten_prompt(
    generate,
):
    # Webscore van wetten.overheid.nl (0.6) is de laagste; top_k = 3. De
    # rangorde zet haar in de weergave bovenaan, maar haalt haar niet de
    # prompt in: selectie is geen taak van de rangorde.
    result = await generate(
        web=[WIKIPEDIA, WIKTIONARY, BRAVE, WETTEN], include_all_hits=False
    )
    bronnen = result.md["sources"]
    assert bronnen[0]["url"] == WETTEN["url"]
    assert bronnen[0]["used_in_prompt"] is False
    assert bronnen[0]["omitted_reason"] == "not_selected"
    assert WETTEN["snippet"][:30] not in result.prompt_text
    assert [b["url"] for b in _in_prompt(bronnen)] == [
        WIKIPEDIA["url"],
        WIKTIONARY["url"],
        BRAVE["url"],
    ]
    _assert_prompt_volgt_weergave(result)


async def test_include_all_hits_aan_alle_hits_in_prompt_wetsbron_eerst(generate):
    result = await generate(
        web=[WIKIPEDIA, WIKTIONARY, BRAVE, WETTEN], include_all_hits=True
    )
    bronnen = result.md["sources"]
    assert [b["url"] for b in _in_prompt(bronnen)] == [
        WETTEN["url"],
        WIKIPEDIA["url"],
        WIKTIONARY["url"],
        BRAVE["url"],
    ]
    tekst = result.prompt_text
    assert tekst.index(WETTEN["snippet"][:30]) < tekst.index(WIKIPEDIA["snippet"])
    _assert_prompt_volgt_weergave(result)


# --- Punt 3: één rangorde voor prompt en weergave, gemengde brontypen --------


async def test_gemengde_brontypen_prompt_en_weergave_zelfde_volgorde(generate):
    chunks = [
        # Eigen RAG met hoge cosine vs. wets-RAG met lage cosine.
        _chunk(11, "beleid-3", 0.8, bron_type="pdf", collectie="Beleid OM"),
        _chunk(12, "27", 0.4),
        # Upload met wetgevingslabel: eigen bron, op eigen score.
        _chunk(13, "upload-1", 0.7, collectie=UPLOAD_COLLECTIE),
    ]
    docs = [
        {
            "doc_id": "upload-01",
            "filename": "werkinstructie.txt",
            "title": "werkinstructie.txt",
            "snippet": "De verdachte wordt gehoord volgens de werkinstructie.",
            "score": 1.0,
            "selection_basis": "term_match",
        }
    ]
    result = await generate(
        web=[WIKIPEDIA, WETTEN, KAMERSTUK], chunks=chunks, docs=docs
    )
    assert _labels(result.md["sources"]) == [
        "27",  # wets-RAG (bronbibliotheek), cosine 0.4
        "Wetboek van Strafvordering art. 27",  # BWB-webbron
        "werkinstructie.txt",  # geüpload document
        "beleid-3",  # eigen RAG 0.8
        "upload-1",  # upload-RAG met wetgevingslabel 0.7
        "Wikipedia",  # overig web 1.0
        "Kamerstuk 36000, nr. 1",  # gemengd domein, geen regelgeving
    ]
    assert all(b["used_in_prompt"] for b in result.md["sources"])
    receipt = result.md["source_receipt"]["sources"]
    assert [(r["source_type"], r["input_index"]) for r in receipt] == [
        ("rag", 1),
        ("web", 1),
        ("document", 0),
        ("rag", 0),
        ("rag", 2),
        ("web", 0),
        ("web", 2),
    ]
    _assert_prompt_volgt_weergave(result)


async def test_bekendmaking_alleen_met_regelgevingstype_voor_wikipedia(generate):
    staatsblad = {
        "provider": "Overheid.nl",
        "url": "https://zoek.officielebekendmakingen.nl/stb-2026-1.html",
        "title": "Staatsblad 2026, 1",
        "snippet": "Wet van 1 januari 2026 tot wijziging van het Wetboek van "
        "Strafvordering.",
        "score": 0.4,
        "document_type": "Staatsblad",
    }
    result = await generate(web=[WIKIPEDIA, KAMERSTUK, staatsblad])
    assert [b["url"] for b in result.md["sources"]] == [
        staatsblad["url"],
        WIKIPEDIA["url"],
        KAMERSTUK["url"],
    ]
    assert result.md["sources"][0]["document_type"] == "Staatsblad"
    _assert_prompt_volgt_weergave(result)


async def test_zonder_rag_en_wetgeving_blijft_webvolgorde_ongewijzigd(generate):
    result = await generate(web=[WIKIPEDIA, WIKTIONARY, BRAVE])
    assert [b["url"] for b in result.md["sources"]] == [
        WIKIPEDIA["url"],
        WIKTIONARY["url"],
        BRAVE["url"],
    ]
    assert [b["used_in_prompt"] for b in result.md["sources"]] == [True] * 3
    _assert_prompt_volgt_weergave(result)


# --- Punt 1: uploadroute → nooit wettelijk -----------------------------------


def _vec(*waarden: float) -> np.ndarray:
    # `_ensure_collection` (uploadroute) gebruikt de productiedimensie.
    v = np.zeros(EmbeddingService.DIMENSIONS, dtype=np.float32)
    v[: len(waarden)] = waarden
    return v


@pytest.fixture
def upload_rag(tmp_path):
    """Echte RAGService; document ingest zoals de uploadroute het doet."""
    db = str(tmp_path / "bronnen.db")
    conn = sqlite3.connect(db)
    conn.executescript(SCHEMA_SQL)
    conn.close()
    chunker = MagicMock(spec=["chunk_tekst"])
    embedder = MagicMock(spec=["embed", "embed_batch", "DIMENSIONS", "MODEL"])
    embedder.DIMENSIONS = EmbeddingService.DIMENSIONS
    embedder.MODEL = "test"
    embedder.embed.return_value = _vec(1, 0)
    embedder.embed_batch.return_value = [_vec(1, 0.2)]
    tekst = "De verdachte wordt binnen zes uur gehoord (eigen werkinstructie)."
    chunker.chunk_tekst.return_value = ChunkingResult(
        chunks=(
            DocumentChunk(
                tekst=tekst,
                metadata=ChunkMetadata(
                    bronbestand="werkinstructie.pdf",
                    chunk_index=0,
                    rechtsgebied="strafrecht",
                    wet_regeling=None,
                    artikel_nummer=None,
                ),
                token_count=10,
            ),
        ),
        bronbestand="werkinstructie.pdf",
        bestandstype="application/pdf",
        totaal_tokens=10,
    )
    service = RAGService(chunker, embedder, EmbeddingStore(db_path=db), db)
    # document_upload_renderer: collectie "user_documents"; met gekozen
    # rechtsgebied zet de route bron_type "wetgeving".
    coll_id = service._ensure_collection("user_documents")
    service.ingest_document(
        tekst=tekst,
        collection_id=coll_id,
        filename="werkinstructie.pdf",
        file_type="application/pdf",
        rechtsgebied="strafrecht",
        bron_type="wetgeving",
    )
    return service


async def test_uploadroute_met_wetgevingslabel_is_geen_wettelijke_bron(
    generate, upload_rag
):
    result = await generate(web=[WIKIPEDIA, WETTEN], rag_service=upload_rag)
    bronnen = result.md["sources"]
    upload = next(b for b in bronnen if b["provider"] == "rag")
    assert upload["bron_type"] == "wetgeving"
    assert upload["collection_name"] == UPLOAD_COLLECTIE
    assert bronrang(upload) == RANG_EIGEN
    assert [b["provider"] for b in bronnen] == ["wetgeving.nl", "rag", "wikipedia"]
    _assert_prompt_volgt_weergave(result)
