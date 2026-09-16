"""DEF-743: kwitantie v2 door de echte keten prompt → orchestrator → kwitantieconsument.

Echte `PromptServiceV2` (pakket E, met stub-promptbouwer en bekende budgetten),
echte `DefinitionOrchestratorV2` (gemockte AI/cleaning/repository) en echte
`ValidationOrchestratorV2` → `ModularValidationService` met een fake
bronbeoordelingsdienst. Bewijst dat de koppeling `(source_type, input_index)` +
`original_content_hash` de aangeleverde bronnen correct terugvindt bij dubbele
doc_id's/URL's, ontbrekende id's, sortering en budget — en dat een niet te
koppelen record een zichtbare technische fout is, geen positioneel gegokte
herkomst. Geen echt model, geen productiedatabase.
"""

import hashlib
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

import services.prompts.prompt_service_v2 as psv2
from domain.sources.contract import (
    CONTRACTVERSIE,
    ONDERDEEL_GEZAG,
    ONDERDEEL_STEUN,
    ONDERDEEL_VERWIJZING,
    bereken_bronvingerafdruk,
)
from domain.sources.normalisatie import canoniseer_bronnen
from services.interfaces import (
    AIGenerationResult,
    CleaningResult,
    GenerationRequest,
    LookupResult,
    OrchestratorConfig,
    WebSource,
)
from services.null_repository import NullDefinitionRepository
from services.orchestrators.definition_orchestrator_v2 import DefinitionOrchestratorV2
from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2
from services.prompts.prompt_service_v2 import PromptServiceV2
from services.validation.modular_validation_service import ModularValidationService
from services.validation.source_assessment_service import (
    SourceAssessment,
    SourceAssessmentService,
)
from toetsregels.manager import get_toetsregel_manager

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]

BEGRIP = "archiefkaart"
DEFINITIE = "Beschrijving van één verzameling documenten van een archiefvormer."
DOC_A = {
    "doc_id": "doc1",
    "filename": "register.txt",
    "citation_label": "§ 1",
    "snippet": "Eerste passage doc1: een archiefkaart beschrijft één verzameling.",
    "score": 1.0,
}
DOC_B = {
    "doc_id": "doc1",
    "filename": "register.txt",
    "citation_label": "§ 2",
    "snippet": "Tweede passage doc1: de kaart noemt de archiefvormer.",
    "score": 0.9,
}
CHUNK_X = {
    "document_id": 81,
    "chunk_text": "Gedeelde prefix alfa uit chunk X.",
    "score": 0.9,
}
CHUNK_Y = {
    "document_id": 81,
    "chunk_text": "Gedeelde prefix beta uit chunk Y.",
    "score": 0.8,
}


def _sha(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


class _StubBuilder:
    def build_prompt(self, begrip, context):
        return "PROMPT_BODY"


class FakeAssessor:
    """Registreert de bronnen die de wrapper aanlevert; gegrond oordeel op de eerste gebruikte bron."""

    def __init__(self):
        self.calls = []

    async def assess(
        self,
        begrip,
        tekst,
        contexten,
        bronnen_ruw,
        *,
        peildatum=None,
        correlation_id=None,
        receipt=None,
    ):
        self.calls.append(
            {"bronnen": deepcopy(bronnen_ruw), "receipt": deepcopy(receipt)}
        )
        # De echte service beslist over kwitantie-/koppelfouten; daarna een synthetisch oordeel.
        fout = SourceAssessmentService._kwitantiefout(
            receipt
        ) or SourceAssessmentService._koppelfout(receipt, bronnen_ruw)
        canoniek = canoniseer_bronnen(bronnen_ruw)
        fingerprint = bereken_bronvingerafdruk(
            begrip, tekst, contexten, canoniek, peildatum=peildatum
        )
        if fout is not None:
            from domain.sources.contract import beoordeling_technische_fout

            soort = (
                "receipt_error"
                if SourceAssessmentService._kwitantiefout(receipt)
                else "receipt_mismatch"
            )
            return SourceAssessment(
                beoordeling_technische_fout(fingerprint, soort, fout, sources=canoniek)
            )
        gebruikt = next((b for b in canoniek if b.used_in_prompt), None)
        bewijs = (
            [
                {
                    "source_id": gebruikt.source_id,
                    "quote": gebruikt.passage[:30],
                    "locator": gebruikt.locator,
                }
            ]
            if gebruikt
            else []
        )
        deel = {
            "status": "pass" if bewijs else "review_required",
            "reason": "synthetisch",
            "uncertainty": None,
            "evidence": bewijs,
        }
        return SourceAssessment(
            {
                "contract_version": CONTRACTVERSIE,
                "prompt_version": "con02-assess/1",
                "fingerprint": fingerprint,
                "status": "assessed",
                "error": None,
                "assessed_at": "2026-09-15T12:00:00+00:00",
                "attribution": {
                    "provider": "fake",
                    "model": "fake-model",
                    "task_type": "validation",
                    "cached": False,
                    "tokens_used": 1,
                },
                "peildatum": peildatum,
                "sources": [b.als_dict() for b in canoniek],
                "parts": {
                    ONDERDEEL_GEZAG: {
                        **deel,
                        "sources": [
                            {
                                "source_id": b["source_id"],
                                "profile": "vakpublicatie",
                                "applicable": True,
                                "reason": "synthetisch",
                            }
                            for b in bewijs
                        ],
                    },
                    ONDERDEEL_STEUN: {
                        **deel,
                        "claims": [
                            {
                                "aspect": "kenmerk",
                                "text": "archiefkaart",
                                "supported": True,
                                "source_id": b["source_id"],
                            }
                            for b in bewijs
                        ],
                    },
                    ONDERDEEL_VERWIJZING: {
                        **deel,
                        "sources": [
                            {
                                "source_id": b["source_id"],
                                "locatable": True,
                                "reason": "synthetisch",
                            }
                            for b in bewijs
                        ],
                    },
                },
                "rejected": [],
                "raw_response_sha256": None,
            }
        )


@pytest.fixture
def prompt_service(monkeypatch):
    def _cfg():
        return {
            "web_lookup": {
                "prompt_augmentation": {
                    "enabled": True,
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
    monkeypatch.setenv("DOCUMENT_SNIPPETS_ENABLED", "true")
    monkeypatch.setenv("DOCUMENT_SNIPPETS_MAX", "16")
    monkeypatch.setenv("DOCUMENT_SNIPPETS_MAX_CHARS", "800")
    svc = PromptServiceV2()
    svc.prompt_generator = _StubBuilder()
    return svc


@pytest.fixture
def generate(monkeypatch, prompt_service):
    from voorbeelden import unified_voorbeelden

    monkeypatch.setattr(
        unified_voorbeelden,
        "genereer_alle_voorbeelden_async",
        AsyncMock(return_value={}),
    )
    monkeypatch.setenv("RAG_MIN_SCORE", "0.3")

    async def run(*, documents=None, chunks=None, web=None, tamper=None):
        assessor = FakeAssessor()
        prompt = prompt_service
        if tamper is not None:
            origineel = prompt.build_generation_prompt

            async def _getamperd(*a, **kw):
                result = await origineel(*a, **kw)
                tamper(result.metadata["source_receipt"])
                return result

            prompt = SimpleNamespace(build_generation_prompt=_getamperd)
        ai = AsyncMock()
        ai.generate_definition.return_value = AIGenerationResult(
            text=DEFINITIE, model="offline", tokens_used=1, generation_time=0.0
        )
        cleaning = AsyncMock()
        cleaning.clean_text.return_value = CleaningResult(
            original_text=DEFINITIE, cleaned_text=DEFINITIE, was_cleaned=False
        )
        validation = ValidationOrchestratorV2(
            ModularValidationService(
                get_toetsregel_manager(), repository=NullDefinitionRepository()
            ),
            source_assessment_service=assessor,
        )
        repo = MagicMock()
        repo.save.return_value = 42
        rag = None
        if chunks is not None:
            rag = MagicMock()
            rag.retrieve_context.return_value = SimpleNamespace(
                chunks=deepcopy(chunks), collection_id=7
            )
        web_service = None
        if web is not None:
            web_service = SimpleNamespace(
                lookup=AsyncMock(
                    return_value=[
                        LookupResult(
                            term=BEGRIP,
                            source=WebSource(
                                name=w["provider"], url=w["url"], confidence=w["score"]
                            ),
                            definition=w["snippet"],
                            metadata={"dc_title": w["title"]},
                        )
                        for w in web
                    ]
                )
            )
        orch = DefinitionOrchestratorV2(
            prompt_service=prompt,
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
        context = (
            {"documents": {"snippets": deepcopy(documents)}}
            if documents is not None
            else None
        )
        response = await orch.create_definition(
            GenerationRequest(
                id="con02-keten",
                begrip=BEGRIP,
                ontologische_categorie="type",
                organisatorische_context=["Testregistratie"],
                rag_collection_id=7 if chunks is not None else None,
            ),
            context=context,
        )
        assert response.success, response.error
        return SimpleNamespace(
            response=response,
            assessor=assessor,
            definition=repo.save.call_args.args[0],
            prompt=prompt_service,
        )

    return run


def _per_locator(bronnen):
    return {
        b.get("citation_label") or b.get("chunk_text") or b.get("snippet"): b
        for b in bronnen
    }


async def test_dubbel_doc_id_wordt_ondubbelzinnig_gekoppeld_na_max_count(
    generate, monkeypatch
):
    monkeypatch.setenv("DOCUMENT_SNIPPETS_MAX", "1")
    result = await generate(documents=[DOC_A, DOC_B])
    md = result.definition.metadata
    receipt = md["source_receipt"]
    assert receipt["version"] == "2"
    assert [r["input_index"] for r in receipt["sources"]] == [0]
    assert [(r["input_index"], r["reason"]) for r in receipt["omitted"]] == [
        (1, "max_count")
    ]

    per = _per_locator(md["provenance_sources"])
    a, b = per["§ 1"], per["§ 2"]
    assert a["used_in_prompt"] is True and a["receipt_correlation"] == "verified"
    assert a["prompt_content"] == receipt["sources"][0]["content"]
    assert a["original_content_hash"] == _sha(DOC_A["snippet"])
    assert b["used_in_prompt"] is False and b["omitted_reason"] == "max_count"
    assert b["receipt_correlation"] == "verified"
    assert "prompt_content" not in b
    assert md["source_receipt_correlation"] == {
        "verified": 2,
        "not_in_receipt": 0,
        "unmatched": 0,
        "ambiguous": 0,
    }
    assert md["source_assessment"]["status"] == "assessed"
    # Wat de beoordeling kreeg is exact de gekoppelde lijst.
    assert result.assessor.calls[0]["bronnen"] == md["provenance_sources"]
    assert result.response.validation_result["rule_statuses"]["CON-02"] == "pass"


async def test_rag_chunks_zonder_chunk_id_worden_per_positie_en_hash_gekoppeld(
    generate,
):
    result = await generate(chunks=[CHUNK_X, CHUNK_Y])
    md = result.definition.metadata
    receipt = md["source_receipt"]
    assert [r["source_id"] for r in receipt["sources"]] == [None, None]
    per = _per_locator(md["provenance_sources"])
    x = next(
        b for b in md["provenance_sources"] if b["snippet"] == CHUNK_X["chunk_text"]
    )
    y = next(
        b for b in md["provenance_sources"] if b["snippet"] == CHUNK_Y["chunk_text"]
    )
    assert (x["receipt_nr"], y["receipt_nr"]) == (1, 2)
    assert (
        x["prompt_content"] == CHUNK_X["chunk_text"]
        and y["prompt_content"] == CHUNK_Y["chunk_text"]
    )
    assert x["input_index"] == 0 and y["input_index"] == 1
    assert md["source_receipt_correlation"]["verified"] == 2
    assert md["source_receipt_correlation"]["unmatched"] == 0
    assert per  # geen leeg resultaat


async def test_dubbele_url_na_sortering_en_geen_rag_alias_in_het_webkanaal(generate):
    web = [
        {
            "provider": "wikipedia",
            "url": "https://w/x",
            "title": "Laag",
            "snippet": "Webpassage laag: archiefkaart.",
            "score": 0.4,
        },
        {
            "provider": "wikipedia",
            "url": "https://w/x",
            "title": "Hoog",
            "snippet": "Webpassage hoog: archiefkaart.",
            "score": 0.9,
        },
    ]
    result = await generate(web=web, chunks=[CHUNK_X])
    md = result.definition.metadata
    receipt = md["source_receipt"]
    # Het webkanaal telt precies de twee webbronnen — de RAG-bron is er geen alias van.
    assert receipt["channels"]["web"]["supplied"] == 2
    assert receipt["channels"]["rag"]["supplied"] == 1
    webbronnen = [
        b for b in md["provenance_sources"] if b.get("provider") == "wikipedia"
    ]
    assert {b["title"]: b["receipt_correlation"] for b in webbronnen} == {
        "Laag": "verified",
        "Hoog": "verified",
    }
    for b in webbronnen:
        assert b["used_in_prompt"] is True
        assert b["prompt_content"].startswith("Webpassage " + b["title"].lower())
    assert md["source_receipt_correlation"]["unmatched"] == 0


async def test_gemanipuleerde_kwitantie_is_zichtbare_technische_fout_zonder_bewijs(
    generate,
):
    def _tamper(receipt):
        receipt["sources"][0]["original_content_hash"] = _sha(
            "andere oorspronkelijke tekst"
        )

    result = await generate(documents=[DOC_A], tamper=_tamper)
    md = result.definition.metadata
    assert md["source_receipt_correlation"] == {
        "verified": 0,
        "not_in_receipt": 1,
        "unmatched": 1,
        "ambiguous": 0,
    }
    per_status = {b["receipt_correlation"]: b for b in md["provenance_sources"]}
    assert per_status["not_in_receipt"]["used_in_prompt"] is False
    assert "prompt_content" not in per_status["not_in_receipt"]
    assert per_status["unmatched"]["doc_id"] == "doc1"
    assert md["source_assessment"]["status"] == "error"
    assert md["source_assessment"]["error"]["type"] == "receipt_mismatch"
    raw = result.response.validation_result
    assert raw["rule_statuses"]["CON-02"] == "error"
    assert "CON-02" not in raw["passed_rules"]
    assert raw["is_acceptable"] is False
