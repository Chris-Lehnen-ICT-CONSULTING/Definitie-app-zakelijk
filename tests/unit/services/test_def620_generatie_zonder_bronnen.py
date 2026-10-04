"""DEF-620 — een generatie zonder bronnen wordt zichtbaar.

De orchestrator legt vast hoeveel bronnen werkelijk in de prompt stonden
(`bronnen_in_prompt`, uit de kwitantie); de servicelaag geeft dat met de
RAG-status door aan de UI; de handler toont dan een waarschuwing.
"""

from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest

from services.interfaces import GenerationRequest
from ui.handlers.definition_generation_handler import waarschuwing_zonder_bronnen

pytestmark = [pytest.mark.unit]


def test_waarschuwing_bij_nul_bronnen_noemt_de_statussen():
    tekst = waarschuwing_zonder_bronnen(
        {
            "bronnen_in_prompt": 0,
            "web_lookup_status": "no_results",
            "rag_status": "error",
        }
    )
    assert tekst is not None
    assert "zonder bronnen" in tekst
    assert "geen resultaten" in tekst
    assert "fout" in tekst


@pytest.mark.parametrize(
    "metadata",
    [
        {"bronnen_in_prompt": 1, "web_lookup_status": "success", "rag_status": "error"},
        {"bronnen_in_prompt": None},
        {},
        None,
        {"bronnen_in_prompt": False},
    ],
)
def test_geen_waarschuwing_bij_bronnen_of_onbekend(metadata):
    assert waarschuwing_zonder_bronnen(metadata) is None


def test_servicelaag_geeft_bronnen_in_prompt_en_rag_status_door():
    from services.service_factory import ServiceAdapter

    md = {
        "bronnen_in_prompt": 0,
        "rag_status": "error",
        "web_lookup_status": "no_results",
    }
    response = SimpleNamespace(definition=SimpleNamespace(metadata=md))
    ui_md = ServiceAdapter._build_ui_metadata(object.__new__(ServiceAdapter), response)

    assert ui_md["bronnen_in_prompt"] == 0
    assert ui_md["rag_status"] == "error"
    assert ui_md["web_lookup_status"] == "no_results"


@pytest.mark.asyncio
async def test_orchestrator_legt_bronnen_in_prompt_vast(tmp_path, monkeypatch):
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
    provider = BevrorenProvider(
        "Kwaliteitskeurmerk dat door een keurmerkhouder wordt verleend"
    )
    cleaning = CleaningService(CleaningConfig())
    orch = DefinitionOrchestratorV2(
        prompt_service=PromptServiceV2(),
        ai_service=provider,
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
    )
    request = GenerationRequest(
        id=str(uuid.uuid4()),
        begrip="keurmerk",
        ontologische_categorie="type",
        organisatorische_context=["Stichting Zilver"],
    )

    antwoord = await orch.create_definition(request)

    assert antwoord.success is True, antwoord.error
    assert antwoord.definition.metadata["bronnen_in_prompt"] == 0
