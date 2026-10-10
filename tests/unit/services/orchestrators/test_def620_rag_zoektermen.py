"""DEF-620 (RAG fase 1): de orchestrator zoekt in de bronbibliotheek met de
relevantiepoort op het begrip (zonder synoniemen uit het register), en de
cosine-drempel blijft daarbovenop gelden."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

import pytest

from models.synonym_models import WeightedSynonym
from services.interfaces import GenerationRequest

pytestmark = [pytest.mark.unit]


@dataclass
class _Ctx:
    chunks: list[dict]
    formatted_context: str = ""
    collection_id: int = 9
    query: str = ""
    kandidaten: int | None = None


@dataclass
class _CtxZonderKandidaten:
    """Context zoals een oudere/andere RAG-implementatie hem levert."""

    chunks: list[dict]
    formatted_context: str = ""
    collection_id: int = 9
    query: str = ""


@dataclass
class _Rag:
    antwoord: _Ctx | _CtxZonderKandidaten
    aanroepen: list[dict] = field(default_factory=list)

    def _ensure_collection(self, _naam):
        return 9

    def retrieve_context(self, **kwargs):
        self.aanroepen.append(kwargs)
        return self.antwoord

    def retrieve_context_multi(self, **kwargs):
        self.aanroepen.append(kwargs)
        return self.antwoord


class _Synoniemen:
    async def ensure_synonyms(self, term, min_count=5, context=None):
        return (
            [
                WeightedSynonym("zich onttrekken", 0.9, "active", False),
                WeightedSynonym("ontvluchting", 0.7, "ai_pending", False),
            ],
            1,
        )


def _orchestrator(tmp_path, monkeypatch, rag):
    from services.cleaning_service import CleaningConfig, CleaningService
    from services.definition_repository import DefinitionRepository
    from services.interfaces import OrchestratorConfig
    from services.null_repository import NullDefinitionRepository
    from services.orchestrators.definition_orchestrator_v2 import (
        DefinitionOrchestratorV2,
    )
    from services.orchestrators.validation_orchestrator_v2 import (
        ValidationOrchestratorV2,
    )
    from services.prompts.prompt_service_v2 import PromptServiceV2
    from services.validation.modular_validation_service import (
        ModularValidationService,
    )
    from tests.unit.services.orchestrators.test_def622_generatiegrens import (
        BevrorenProvider,
    )
    from toetsregels.manager import get_toetsregel_manager
    from voorbeelden import unified_voorbeelden

    async def _leeg(*_a, **_k):
        return {}

    monkeypatch.setattr(unified_voorbeelden, "genereer_alle_voorbeelden_async", _leeg)
    cleaning = CleaningService(CleaningConfig())
    return DefinitionOrchestratorV2(
        prompt_service=PromptServiceV2(),
        ai_service=BevrorenProvider(
            "Handeling waarbij een jeugdige zich zonder toestemming aan het toezicht onttrekt"
        ),
        validation_service=ValidationOrchestratorV2(
            ModularValidationService(
                toetsregel_manager=get_toetsregel_manager(),
                repository=NullDefinitionRepository(),
            ),
            cleaning_service=cleaning,
        ),
        cleaning_service=cleaning,
        repository=DefinitionRepository(str(tmp_path / "keten.db")),
        config=OrchestratorConfig(enable_feedback_loop=False, enable_enhancement=False),
        synonym_orchestrator=_Synoniemen(),
        rag_service=rag,
    )


def _verzoek():
    return GenerationRequest(
        id=str(uuid.uuid4()),
        begrip="onttrekking",
        ontologische_categorie="proces",
        organisatorische_context=["DJI"],
    )


@pytest.mark.asyncio
async def test_zoektermen_alleen_het_begrip_geen_synoniemen(tmp_path, monkeypatch):
    monkeypatch.setenv("RAG_MIN_SCORE", "0.3")
    rag = _Rag(_Ctx(chunks=[], kandidaten=0))
    antwoord = await _orchestrator(tmp_path, monkeypatch, rag).create_definition(
        _verzoek()
    )
    assert antwoord.success is True, antwoord.error
    assert rag.aanroepen[0]["zoektermen"] == ["onttrekking"]
    md = antwoord.definition.metadata
    assert md["rag_zoektermen"] == ["onttrekking"]
    assert md["rag_kandidaten"] == 0
    assert md["bronnen_in_prompt"] == 0


@pytest.mark.asyncio
async def test_drempel_filtert_gepoorte_fragmenten_met_lage_score(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("RAG_MIN_SCORE", "0.3")

    def _chunk(cid, tekst, score):
        return {
            "chunk_id": cid,
            "chunk_text": tekst,
            "score": score,
            "artikel_lid": str(cid),
            "wet_regeling": "Wetboek van Strafvordering",
            "metadata": {},
        }

    rag = _Rag(
        _Ctx(
            chunks=[
                _chunk(68, "Artikel 68 zich aan de hechtenis onttrekt", 0.45),
                # noemt het begrip (bv. homoniem), maar score onder de drempel
                _chunk(94, "onttrekking aan het verkeer van voorwerpen", 0.2),
            ],
            kandidaten=2,
        )
    )
    antwoord = await _orchestrator(tmp_path, monkeypatch, rag).create_definition(
        _verzoek()
    )
    assert antwoord.success is True, antwoord.error
    md = antwoord.definition.metadata
    assert md["rag_chunks_count"] == 1
    assert md["rag_kandidaten"] == 2
    assert md["bronnen_in_prompt"] == 1


@pytest.mark.asyncio
async def test_zonder_kandidatenveld_oud_gedrag(tmp_path, monkeypatch):
    monkeypatch.setenv("RAG_MIN_SCORE", "0.3")
    chunk = {"chunk_id": 1, "chunk_text": "x onttrekking", "score": 0.2, "metadata": {}}
    rag = _Rag(_CtxZonderKandidaten(chunks=[chunk]))
    antwoord = await _orchestrator(tmp_path, monkeypatch, rag).create_definition(
        _verzoek()
    )
    md = antwoord.definition.metadata
    assert md["rag_chunks_count"] == 0
    assert md["rag_kandidaten"] is None
