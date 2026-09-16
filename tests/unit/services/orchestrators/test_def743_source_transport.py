"""Real generation orchestration; offline boundaries, no persistence claim (DEF-743).

Drives ``DefinitionOrchestratorV2.create_definition`` with mocked AI, cleaning,
validation and repository services and inspects two transport surfaces:

* the ``context`` the orchestrator hands to ``build_generation_prompt``;
* ``definition.metadata["sources"]`` on the returned definition.

Sources are candidate evidence for the prompt. Nothing here asserts authority,
scoring quality or persistence beyond the mocked ``repository.save`` call.
"""

from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from services.interfaces import (
    AIGenerationResult,
    CleaningResult,
    GenerationRequest,
    OrchestratorConfig,
    PromptResult,
)
from services.orchestrators.definition_orchestrator_v2 import DefinitionOrchestratorV2
from services.prompts.prompt_service_v2 import PromptServiceV2
from ui.handlers.definition_generation_handler import DefinitionGenerationHandler

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]

PASSAGE = "Een archiefkaart beschrijft één verzameling documenten."
DOCUMENT = {
    "doc_id": "upload-01",
    "filename": "register.txt",
    "citation_label": "§ 2",
    "snippet": PASSAGE,
    "score": 1.0,
    "selection_basis": "term_match",
}
CHUNK = {
    "chunk_id": 501,
    "document_id": 81,
    "chunk_index": 0,
    "created_at": "2026-09-14T10:00:00Z",
    "filename": "register.txt",
    "bron_type": "beleid",
    "rechtsgebied": "Bestuursrecht",
    "wet_regeling": "Synthetisch testregister",
    "artikel_lid": "2",
    "metadata": {"pagina_nummer": 2, "locator": {"section": "Kaarten"}},
    "chunk_text": PASSAGE,
    "score": 0.91,
}
# Identity and locator fields a RAG source must carry unchanged when present.
RAG_FIELDS = tuple(key for key in CHUNK if key not in ("chunk_text", "score"))
SPARSE_CHUNK = {"chunk_text": "Sparse", "score": 0.8}
EXCLUDED_CHUNK = {"chunk_id": 999, "chunk_text": "Excluded", "score": 0.1}
DOCUMENTS_CONTEXT = {
    "snippets": [DOCUMENT],
    "summary": "Gekozen register",
    "selected_ids": ["upload-01"],
    "custom_context": {"purpose": "test"},
}


def rag_sources(response):
    return [
        s for s in response.definition.metadata["sources"] if s["provider"] == "rag"
    ]


@pytest.fixture
def generate(monkeypatch):
    """Run one real ``create_definition`` with offline service doubles.

    ``documents`` replaces the ``context["documents"]`` block; ``chunks`` replaces
    the RAG retrieval result (default: one rich, one sparse and one chunk below
    ``RAG_MIN_SCORE``). Returns the response plus the prompt-side context.
    """
    from voorbeelden import unified_voorbeelden

    monkeypatch.setattr(
        unified_voorbeelden,
        "genereer_alle_voorbeelden_async",
        AsyncMock(return_value={}),
    )
    monkeypatch.setenv("RAG_MIN_SCORE", "0.3")

    async def run(documents=None, chunks=None):
        context = {
            "documents": deepcopy(DOCUMENTS_CONTEXT if documents is None else documents)
        }
        chunks = deepcopy(
            [CHUNK, SPARSE_CHUNK, EXCLUDED_CHUNK] if chunks is None else chunks
        )
        prompt = AsyncMock()
        prompt.build_generation_prompt.return_value = PromptResult(
            text="Offline",
            token_count=1,
            components_used=(),
            feedback_integrated=False,
            optimization_applied=False,
            metadata={},
        )
        ai = AsyncMock()
        ai.generate_definition.return_value = AIGenerationResult(
            text=PASSAGE, model="offline", tokens_used=1, generation_time=0.0
        )
        cleaning = AsyncMock()
        cleaning.clean_text.return_value = CleaningResult(
            original_text=PASSAGE, cleaned_text=PASSAGE, was_cleaned=False
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
        rag = MagicMock()
        rag.retrieve_context.return_value = SimpleNamespace(
            chunks=chunks, collection_id=7
        )
        orch = DefinitionOrchestratorV2(
            prompt_service=prompt,
            ai_service=ai,
            validation_service=validation,
            cleaning_service=cleaning,
            repository=repo,
            rag_service=rag,
            config=OrchestratorConfig(
                enable_feedback_loop=False, enable_enhancement=False
            ),
        )
        response = await orch.create_definition(
            GenerationRequest(
                id="con02-offline",
                begrip="archiefkaart",
                ontologische_categorie="type",
                organisatorische_context=["Testregistratie"],
                rag_collection_id=7,
            ),
            context=deepcopy(context),
        )
        assert response.success, response.error
        repo.save.assert_called_once()
        ai.generate_definition.assert_awaited_once()
        return SimpleNamespace(
            response=response,
            context=prompt.build_generation_prompt.call_args.kwargs["context"],
            original=context,
            chunks=chunks,
        )

    return run


async def test_upload_coordinates_and_document_context_survive_generation(generate):
    result = await generate()
    sources = result.response.definition.metadata["sources"]
    assert [s["provider"] for s in sources] == ["documents", "rag", "rag"]
    doc = sources[0]
    for key, value in DOCUMENT.items():
        assert doc[key] == value
        assert result.context["documents"]["snippets"][0][key] == value
    assert doc["title"] == "register.txt"
    assert doc["source_label"] == "Geüpload document"
    for key in ("summary", "selected_ids", "custom_context"):
        assert result.context["documents"][key] == result.original["documents"][key]


async def test_sparse_upload_snippet_does_not_invent_locators(generate):
    result = await generate({"snippets": [{"title": "los.txt", "snippet": "Alleen."}]})
    doc = result.response.definition.metadata["sources"][0]
    assert doc["provider"] == "documents"
    assert doc["title"] == "los.txt"
    assert doc["snippet"] == "Alleen."
    assert doc["doc_id"] is None
    for key in ("filename", "citation_label", "selection_basis"):
        assert key not in doc
    assert set(result.context["documents"]) == {"snippets"}


async def test_mixed_snippets_keep_basis_and_skip_malformed_entry(generate):
    whole = {
        "doc_id": "upload-02",
        "filename": "awb.txt",
        "citation_label": "volledig document",
        "snippet": "Kort.",
        "score": 0.0,
        "selection_basis": "selected_short_document",
    }
    broken = {"doc_id": "upload-03", "snippet": "Kapot", "score": "n/a"}
    result = await generate({"snippets": [DOCUMENT, whole, broken]})
    docs = [
        s
        for s in result.response.definition.metadata["sources"]
        if s["provider"] == "documents"
    ]
    assert [(d["doc_id"], d["selection_basis"], d["score"]) for d in docs] == [
        ("upload-01", "term_match", 1.0),
        ("upload-02", "selected_short_document", 0.0),
    ]
    assert docs[1]["citation_label"] == "volledig document"
    assert [s["doc_id"] for s in result.context["documents"]["snippets"]] == [
        "upload-01",
        "upload-02",
    ]


async def test_rag_coordinates_survive_without_inventing_missing_evidence(generate):
    result = await generate()
    sources = rag_sources(result.response)
    assert len(sources) == 2
    rich, sparse = sources
    for key in RAG_FIELDS:
        assert rich[key] == CHUNK[key]
        assert key not in sparse
    assert result.context["rag_chunks"][0] == CHUNK
    assert rich["snippet"] == PASSAGE
    assert rich["score"] == 0.91
    assert rich["is_authoritative"] is False
    assert rich["url"] is None
    assert rich["legal"] == {
        "citation_text": "Bestuursrecht · Synthetisch testregister · 2"
    }
    for key in ("source_version", "effective_date", "review_status"):
        assert key not in rich
    assert sparse["title"] == "RAG document"
    assert sparse["legal"] is None
    assert "Excluded" not in {s["snippet"] for s in sources}


async def test_rag_locator_metadata_is_an_independent_deep_copy(generate):
    result = await generate()
    rich = rag_sources(result.response)[0]
    assert rich["metadata"] == CHUNK["metadata"]
    assert rich["metadata"] is not result.chunks[0]["metadata"]

    rich["metadata"]["locator"]["section"] = "Mutated"
    assert result.chunks[0]["metadata"]["locator"]["section"] == "Kaarten"
    assert result.context["rag_chunks"][0]["metadata"]["locator"]["section"] == (
        "Kaarten"
    )

    result.chunks[0]["metadata"]["pagina_nummer"] = 99
    assert rich["metadata"]["pagina_nummer"] == 2


@pytest.mark.parametrize("bad_metadata", ["p. 2", None, ["Kaarten"], 7])
async def test_malformed_rag_metadata_and_null_identity_stay_unknown(
    generate, bad_metadata
):
    chunk = {
        "chunk_id": None,
        "document_id": 0,  # Zero is a real identifier, not a missing one.
        "metadata": bad_metadata,
        "chunk_text": "Onvolledig",
        "score": 0.5,
    }
    result = await generate(chunks=[chunk])
    (source,) = rag_sources(result.response)
    assert source["snippet"] == "Onvolledig"
    assert source["document_id"] == 0
    assert "chunk_id" not in source
    assert "metadata" not in source
    assert result.context["rag_chunks"] == [chunk]


async def test_selected_short_source_reaches_existing_prompt_collector(
    generate, monkeypatch
):
    doc = SimpleNamespace(
        id="short",
        filename="register.txt",
        extracted_text=PASSAGE,
        mime_type="text/plain",
    )
    monkeypatch.setattr(
        "ui.handlers.definition_generation_handler.get_document_processor",
        lambda: SimpleNamespace(get_document_by_id=lambda _: doc),
    )
    snippets = DefinitionGenerationHandler(None, None, None)._build_document_snippets(
        "registratiehulpmiddel", [doc.id]
    )
    result = await generate({"snippets": snippets, "selected_ids": [doc.id]})

    # Invoke the actual collector: XML contents, not an AI judgment or full prompt.
    xml = PromptServiceV2()._collect_document_brons(
        SimpleNamespace(metadata=result.context), 0
    )
    assert len(xml) == 1
    assert 'type="document"' in xml[0]
    assert PASSAGE in xml[0]
    assert 'titel="register.txt"' in xml[0]
    assert 'citatie="volledig document"' in xml[0]

    source = result.response.definition.metadata["sources"][0]
    assert source["doc_id"] == doc.id
    assert source["filename"] == "register.txt"
    assert source["citation_label"] == "volledig document"
    assert source["selection_basis"] == "selected_short_document"
    assert source["score"] == 0.0
    assert result.context["documents"]["selected_ids"] == [doc.id]
