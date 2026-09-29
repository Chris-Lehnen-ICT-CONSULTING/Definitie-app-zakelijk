"""DEF-770 herstel na G24: INT-01 bereikt de echte generatieprompt in elke context.

G24 toonde dat de hele INT-sectie ontbrak zonder juridische of wettelijke
context (G01/G04/G05: prompts oud/nieuw byte-identiek). Oorzaak:
`PromptOrchestrator._get_active_modules` activeerde `integrity_rules` alleen
bij juridische/wettelijke context (DEF-123). INT-01 geldt voor iedere
definitie (`geldigheid: alle`) en wordt altijd getoetst; de overige INT-regels
en SAM behouden hun bestaande contexttoepasselijkheid.

Bewijsgrens: de echte `PromptServiceV2` (en de echte generatie-orchestrator
tot aan een bevroren providergrens); geen modelaanroep, geen claim over
generatiekwaliteit.
"""

from __future__ import annotations

import uuid

import pytest

from services.definition_generator_config import UnifiedGeneratorConfig
from services.definition_generator_context import EnrichedContext
from services.interfaces import GenerationRequest
from services.prompts.modules.base_module import ModuleContext
from services.prompts.modules.json_based_rules_module import JSONBasedRulesModule
from services.prompts.modules.prompt_orchestrator import PromptOrchestrator
from services.prompts.prompt_service_v2 import PromptServiceV2

pytestmark = [pytest.mark.unit]

INT01_KAART = "🔹 **INT-01"
#: Betekenisbehoud bij herformuleren (G24: modaliteit, exclusiviteit,
#: voorwaarden, verwijzing, brongebonden beperking) — wel, en begrensd.
BETEKENISBEHOUD = (
    "maak van een mogelijkheid geen feit",
    "‘uitsluitend’",
    "toepassings- of eindvoorwaarde",
    "antecedent",
    "brongebonden beperking",
    "Neem bronbijzaken die het begrip niet afbakenen niet op",
)
#: Wat de INT-01-instructie al droeg en moet blijven dragen.
BESTAAND = (
    "één compacte zin in de geldende substitutiestijl",
    "zelfstandige hoofdzin is niet vereist",
    "behoud negaties en de bronbetekenis",
    "registratiecontext is geen doelgroep",
)

CONTEXTEN = [
    ({}, False),
    ({"org": ["Synthetische Proefdienst"]}, False),
    ({"jur": ["bestuursrecht"]}, True),
    ({"wet": ["Synthetische Proefwet"]}, True),
    ({"org": ["Synthetische Proefdienst"], "jur": ["bestuursrecht"]}, True),
]
CONTEXT_IDS = [
    "geen",
    "alleen-organisatorisch",
    "alleen-juridisch",
    "alleen-wettelijk",
    "org+jur",
]
ORG = ["Synthetische Proefdienst"]


def _request(**context) -> GenerationRequest:
    return GenerationRequest(
        id=str(uuid.uuid4()),
        begrip="proefvergunning",
        ontologische_categorie="type",
        organisatorische_context=context.get("org"),
        juridische_context=context.get("jur"),
        wettelijke_basis=context.get("wet"),
    )


def _rule_ids(content: str) -> list[str]:
    return [
        regel[len("🔹 **") :].split(" - ", 1)[0]
        for regel in content.splitlines()
        if regel.startswith("🔹 **")
    ]


def _int01_kaart(prompt: str) -> str:
    kaart = prompt.split(INT01_KAART, 1)[1]
    return kaart.split("🔹 **", 1)[0].split("###", 1)[0]


@pytest.mark.asyncio
@pytest.mark.parametrize(("context", "juridisch"), CONTEXTEN, ids=CONTEXT_IDS)
async def test_int01_in_echte_prompt_bij_elke_context(context, juridisch):
    prompt = (await PromptServiceV2().build_generation_prompt(_request(**context))).text
    assert prompt.count(INT01_KAART) == 1
    assert "### 🔒 Integriteit Regels (INT):" in prompt
    kaart = _int01_kaart(prompt)
    for zinsdeel in BESTAAND + BETEKENISBEHOUD:
        assert zinsdeel in kaart, zinsdeel
    ids = _rule_ids(prompt)
    int_ids = [i for i in ids if i.startswith("INT")]
    sam_ids = [i for i in ids if i.startswith("SAM")]
    if juridisch:
        # Bestaande toepasselijkheid: volledige INT- en SAM-set.
        assert len(int_ids) > 1 and "INT-02" in int_ids
        assert sam_ids
    else:
        # Smal: alleen INT-01 en INT-03 (DEF-772 K3(b)); overige INT en SAM
        # ongewijzigd afwezig.
        assert int_ids == ["INT-01", "INT-03"]
        assert not sam_ids


@pytest.mark.asyncio
async def test_int01_en_volledige_bron_bij_alleen_organisatorische_context():
    """G24-vorm: alleen organisatorische context plus een bronpassage."""
    passage = (
        "Een proefvergunning wordt verleend voor ten hoogste twaalf maanden en "
        "zegt op zichzelf niets over de uitkomst van een latere aanvraag."
    )
    context = {
        "documents": {
            "snippets": [
                {
                    "provider": "documents",
                    "title": "synthetisch proefdocument",
                    "filename": "synthetisch proefdocument",
                    "doc_id": "B01",
                    "snippet": passage,
                    "score": 0.0,
                    "selection_basis": "selected_short_document",
                    "used_in_prompt": True,
                    "citation_label": "volledig document",
                }
            ]
        }
    }
    result = await PromptServiceV2().build_generation_prompt(
        _request(org=["Synthetische Proefdienst"]), context=context
    )
    assert result.text.count(INT01_KAART) == 1
    receipt = result.metadata["source_receipt"]
    assert receipt["status"] == "used"
    [bron] = [s for s in receipt["sources"] if s["source_type"] == "document"]
    assert bron["content"] == passage
    assert bron["truncated"] is False
    assert bron["xml"] in result.text
    assert receipt["omitted"] == []


def _enriched(**base) -> EnrichedContext:
    return EnrichedContext(
        base_context={"organisatorisch": [], "juridisch": [], "wettelijk": [], **base},
        sources=[],
        expanded_terms={},
        confidence_scores={},
        metadata={},
    )


def test_orchestrator_activeert_integrity_altijd_en_sam_ongewijzigd():
    orch = PromptOrchestrator()

    class _Mod:
        def __init__(self, module_id):
            self.module_id = module_id
            self.module_name = module_id
            self.priority = 50

        def get_dependencies(self):
            return []

        def initialize(self, _cfg):
            pass

    for module_id in ("integrity_rules", "sam_rules"):
        orch.register_module(_Mod(module_id))
    for enriched in (_enriched(), _enriched(organisatorisch=ORG)):
        actief = orch._get_active_modules(enriched, UnifiedGeneratorConfig())
        assert "integrity_rules" in actief
        assert "sam_rules" not in actief
    actief = orch._get_active_modules(
        _enriched(juridisch=["bestuursrecht"]), UnifiedGeneratorConfig()
    )
    assert {"integrity_rules", "sam_rules"} <= actief


def test_int_module_toont_zonder_juridische_context_alleen_int01_en_int03():
    """DEF-772 K3(b): naast INT-01 is ook INT-03 contextvrij; de rest niet."""
    module = JSONBasedRulesModule("INT", "integrity_rules", "INT", "🔒", "INT", 70)
    module.initialize({"include_examples": True})

    def _ctx(enriched):
        return ModuleContext(
            begrip="proefvergunning",
            enriched_context=enriched,
            config=UnifiedGeneratorConfig(),
            shared_state={},
        )

    zonder = module.execute(_ctx(_enriched(organisatorisch=ORG)))
    assert _rule_ids(zonder.content) == ["INT-01", "INT-03"]
    assert zonder.metadata["rules_count"] == 2
    assert "INT-02" in zonder.metadata["rules_skipped"]
    met = module.execute(_ctx(_enriched(wettelijk=["Synthetische Proefwet"])))
    assert "INT-01" in _rule_ids(met.content) and "INT-02" in _rule_ids(met.content)
    assert met.metadata["rules_skipped"] == []
    assert sorted(_rule_ids(met.content)) == sorted(
        ["INT-01", "INT-03", *zonder.metadata["rules_skipped"]]
    )


@pytest.mark.asyncio
async def test_provider_ontvangt_int01_bij_alleen_organisatorische_context(
    tmp_path, monkeypatch
):
    """Ketenbewijs tot de providergrens via de echte generatie-orchestrator."""
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
    provider = BevrorenProvider("vergunning die tijdelijk toegang geeft tot een proef")
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

    antwoord = await orch.create_definition(_request(org=["Synthetische Proefdienst"]))

    assert antwoord.success is True, antwoord.error
    [ontvangen] = provider.oproepen
    assert ontvangen.count(INT01_KAART) == 1
    kaart = _int01_kaart(ontvangen)
    for zinsdeel in BETEKENISBEHOUD:
        assert zinsdeel in kaart, zinsdeel
    assert "🔹 **INT-02" not in ontvangen
