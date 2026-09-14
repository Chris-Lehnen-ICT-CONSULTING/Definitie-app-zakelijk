"""DEF-622 vervolgcriteria — de feitelijk verzonden generatieprompt (CW-GEN-04).

Niet de losse modules, maar de eindprompt zoals `PromptServiceV2` hem voor de
generatie-orchestrator bouwt, op alle contextvarianten (alleen
organisatorisch, alleen juridisch, alleen wettelijk, alle drie). Alle actieve
bronnen — ContextAwareness, de JSON-regelmodule (CON-01) en de afsluitende
definition_task-checklist — volgen dezelfde noodzakelijke-naamuitzondering
(B-02), en het absolute verbod uit de oude norm komt nergens meer voor. De
niet-actieve ErrorPrevention-helper mag zijn oude verbod niet in de
eindprompt brengen; zijn tekst hoort dan ook afwezig te zijn.
"""

from __future__ import annotations

import uuid

import pytest

from services.interfaces import GenerationRequest
from services.prompts.prompt_service_v2 import PromptServiceV2

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]

NOODZAKELIJK = "inhoudelijk noodzakelijk"
REGISTRATIE = "registratiecontext"
VERBODEN_OUD = (
    "VERMIJD het expliciet noemen van contextnamen",
    "zonder de context expliciet te benoemen",
    "zonder deze expliciet te benoemen",
    "zonder expliciete benoeming van contextnamen",
    "Context verwerkt zonder expliciete benoeming",
    "Vermijd expliciete vermelding van juridisch context",
    "Vermijd expliciete vermelding van wetboek",
)


def _request(**context) -> GenerationRequest:
    return GenerationRequest(
        id=str(uuid.uuid4()),
        begrip="keurmerk",
        ontologische_categorie="type",
        organisatorische_context=context.get("org"),
        juridische_context=context.get("jur"),
        wettelijke_basis=context.get("wet"),
    )


@pytest.mark.parametrize(
    "context",
    [
        {"org": ["Stichting Zilver"]},
        {"jur": ["privaatrecht"]},
        {"wet": ["Regeling Z"]},
        {"org": ["DJI"], "jur": ["strafrecht"], "wet": ["Wetboek van Strafvordering"]},
    ],
    ids=["alleen-organisatorisch", "alleen-juridisch", "alleen-wettelijk", "alle-drie"],
)
async def test_eindprompt_volgt_de_naamuitzondering_in_alle_actieve_bronnen(context):
    prompt = (await PromptServiceV2().build_generation_prompt(_request(**context))).text

    # Alle drie actieve bronnen dragen de uitzondering (elk met een eigen
    # herkenbare formulering), dus minstens drie keer.
    assert prompt.count(NOODZAKELIJK) >= 3, prompt
    assert REGISTRATIE in prompt
    # ContextAwareness
    assert "hoort bij het record, niet in de definitiezin" in prompt
    # JSON-regelmodule CON-01
    assert "vermeld de registratiecontext niet in de definitiezin" in prompt
    # Afsluitende checklist (definition_task)
    assert "Context impliciet verwerkt: de registratiecontext niet in de zin" in prompt
    for oud in VERBODEN_OUD:
        assert oud not in prompt, oud
    # De opgegeven contextwaarden zelf staan in de prompt (transport).
    for waarden in context.values():
        for waarde in waarden:
            assert waarde in prompt


@pytest.mark.parametrize(
    "context",
    [
        {"org": ["Stichting Zilver"]},
        {"jur": ["privaatrecht"]},
        {"wet": ["Regeling Z"]},
        {"org": ["DJI"], "jur": ["strafrecht"], "wet": ["Wetboek van Strafvordering"]},
    ],
    ids=["alleen-organisatorisch", "alleen-juridisch", "alleen-wettelijk", "alle-drie"],
)
async def test_provider_ontvangt_de_eindprompt_met_de_naamuitzondering(
    tmp_path, monkeypatch, context
):
    """Ketenbewijs: niet alleen de promptbouw, maar wat de providergrens
    werkelijk ontvangt via de echte generatie-orchestrator met de echte
    `PromptServiceV2`, op alle vier contextvarianten (CW-GEN-04)."""
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
        "Kwaliteitskeurmerk dat uitsluitend door Stichting Zilver wordt verleend"
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

    antwoord = await orch.create_definition(
        GenerationRequest(
            id=str(uuid.uuid4()),
            begrip="Zilverkeurmerk",
            ontologische_categorie="type",
            organisatorische_context=context.get("org"),
            juridische_context=context.get("jur"),
            wettelijke_basis=context.get("wet"),
        )
    )

    assert antwoord.success is True, antwoord.error
    assert len(provider.oproepen) == 1
    ontvangen = provider.oproepen[0]
    assert "vermeld de registratiecontext niet in de definitiezin" in ontvangen
    assert "hoort bij het record, niet in de definitiezin" in ontvangen
    assert (
        "Context impliciet verwerkt: de registratiecontext niet in de zin" in ontvangen
    )
    for oud in VERBODEN_OUD:
        assert oud not in ontvangen, oud
    for waarden in context.values():
        for waarde in waarden:
            assert waarde in ontvangen
    # En de bewaarde prompt bij het record is dezelfde als wat verzonden is.
    assert antwoord.definition.metadata["prompt_text"] == ontvangen


async def test_eindprompt_bevat_geen_aanwijzing_om_context_te_raden():
    """Het oude 'rechtsgebied raden'-mechanisme stuurde de generator naar
    versmalde vocabulaire in plaats van de gegeven context; de eindprompt
    vraagt daar niet meer om."""
    prompt = (
        await PromptServiceV2().build_generation_prompt(
            _request(org=["Stichting Zilver"])
        )
    ).text
    assert "raden" not in prompt.lower()
