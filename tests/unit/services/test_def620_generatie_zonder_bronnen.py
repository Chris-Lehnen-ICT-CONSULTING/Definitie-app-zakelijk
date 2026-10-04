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
from services.modern_web_lookup_service import _noemt_begrip
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


def test_waarschuwing_noemt_gevonden_maar_niet_gebruikt():
    tekst = waarschuwing_zonder_bronnen(
        {
            "bronnen_in_prompt": 0,
            "web_lookup_status": "success",
            "rag_status": "success",
            "bronkanalen": {
                "web": {"aangeleverd": 3, "gebruikt": 0},
                "rag": {"aangeleverd": 0, "gebruikt": 0},
            },
        }
    )
    assert "3 gevonden, 0 in prompt" in tekst
    assert "0 bruikbaar" in tekst
    assert "gelukt" not in tekst


@pytest.mark.parametrize(
    ("titel", "snippet", "begrip", "verwacht"),
    [
        ("Verdachte", "", "verdachte", True),
        ("", "Verdachten worden gehoord", "verdachte", True),
        ("", "In bijzondere omstandigheden", "om", False),
        ("", "Het OM vervolgt", "om", True),
        ("", "onttrekking aan het toezicht", "Onttrekking", True),
        ("", "toezicht na onttrekking", "onttrekking aan toezicht", True),
        ("", "Wet op het OM", "wet om", False),
        ("Waterschapsverordening", "", "onttrekking", False),
        (None, None, "verdachte", False),
    ],
)
def test_noemt_begrip(titel, snippet, begrip, verwacht):
    assert _noemt_begrip({"title": titel, "snippet": snippet}, begrip) is verwacht


def test_handler_toont_waarschuwing_alleen_bij_geslaagde_generatie_zonder_bronnen():
    from unittest.mock import MagicMock

    from tests.unit.ui.handlers.test_def751_betekenisconflict_handler import (
        FakeService,
        FakeSM,
        _handler,
        _run,
        succes_ui,
    )

    def _met(md):
        ui = succes_ui()
        ui["metadata"] = md
        return ui

    zonder = {
        "bronnen_in_prompt": 0,
        "web_lookup_status": "no_results",
        "rag_status": "error",
    }
    met = {
        "bronnen_in_prompt": 2,
        "web_lookup_status": "success",
        "rag_status": "success",
    }

    for md, verwacht in ((zonder, True), (met, False)):
        handler, _repo = _handler(FakeService(_met(md)))
        st = MagicMock()
        _run(handler, FakeSM(determined_category="proces", category_reasoning="r"), st)
        meldingen = " ".join(str(a) for c in st.warning.call_args_list for a in c.args)
        assert ("zonder bronnen" in meldingen) is verwacht
        assert st.success.called


@pytest.mark.asyncio
async def test_orchestrator_telt_een_webbron_in_de_prompt(tmp_path, monkeypatch):
    from services.cleaning_service import CleaningConfig, CleaningService
    from services.definition_repository import DefinitionRepository
    from services.interfaces import LookupResult, OrchestratorConfig, WebSource
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

    class _Web:
        _last_debug = None

        async def lookup(self, request):
            return [
                LookupResult(
                    term="keurmerk",
                    source=WebSource(
                        name="Wikipedia",
                        url="https://nl.wikipedia.org/wiki/Keurmerk",
                        confidence=0.9,
                        is_juridical=False,
                    ),
                    definition="Een keurmerk is een merkteken dat kwaliteit aangeeft.",
                    success=True,
                )
            ]

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
        web_lookup_service=_Web(),
    )
    request = GenerationRequest(
        id=str(uuid.uuid4()),
        begrip="keurmerk",
        ontologische_categorie="type",
        organisatorische_context=["Stichting Zilver"],
    )

    antwoord = await orch.create_definition(request)

    assert antwoord.success is True, antwoord.error
    md = antwoord.definition.metadata
    assert md["bronnen_in_prompt"] == 1
    assert md["bronkanalen"]["web"] == {"aangeleverd": 1, "gebruikt": 1}
