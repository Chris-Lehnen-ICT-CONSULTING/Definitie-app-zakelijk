"""DEF-772 WP1: de INT-03-norm (G) in de feitelijke generatieprompt, contextvrij.

Besluit K3(b) (besluiten-chris-v1.md): alleen INT-03 wordt, naast INT-01
(DEF-770) en CON-02 (DEF-743), in élke generatieprompt getoond — ook zonder
juridische of wettelijke context. De overige INT-regels en SAM behouden hun
DEF-123-toepasselijkheid. De instructie is de ene G-tekst uit synthese-v2 §3.

Bewijsgrens: de echte `JSONBasedRulesModule`, de echte `PromptServiceV2` en de
echte generatie-orchestrator tot aan een bevroren providergrens. Geen
modelaanroep en geen claim over generatiekwaliteit (dat vraagt de
effectevaluatie van WP6).
"""

from __future__ import annotations

import uuid

import pytest

from services.definition_generator_config import UnifiedGeneratorConfig
from services.definition_generator_context import EnrichedContext
from services.interfaces import GenerationRequest
from services.prompts.modular_prompt_builder import PromptComponentConfig
from services.prompts.modules.base_module import ModuleContext
from services.prompts.modules.json_based_rules_module import JSONBasedRulesModule
from services.prompts.prompt_service_v2 import PromptServiceV2

pytestmark = [pytest.mark.unit]

INT03_KAART = "🔹 **INT-03"
#: Exacte G-instructie (synthese-v2 §3; besluit "G-instructietekst").
G_INSTRUCTIE = (
    "Maak iedere verwijzing in de definitiekern eenduidig, ook bij 'het', 'dat' "
    "en bezit ('zijn', 'haar', 'hun'). Duidelijke die/dat-bijzinnen en duidelijke "
    "vooruitverwijzingen zijn toegestaan; niet-verwijzend gebruik (lidwoord, loos "
    "'het') vraagt geen antecedent. Herhaal bij dubbelzinnigheid het bedoelde "
    "zelfstandig naamwoord of herformuleer, zonder het begrip zelf in te voegen "
    "en met behoud van actor, rol, bezit, bereik en tijdsrelaties. Vul "
    "ontbrekende bedoeling niet zelf in: verzin geen referent en zet geen vraag "
    "in de definitie; laat de onduidelijkheid zichtbaar, zodat de toets haar met "
    "één vraag meldt. Losse context, bron, lemma of toelichting vervangt geen "
    "ontbrekende verwijzing in de kern."
)
INSTRUCTIEREGEL = f"- **Instructie:** {G_INSTRUCTIE}"
#: De vervangen instructie (DEF-126) mag nergens meer in de prompt staan.
OUDE_INSTRUCTIE = (
    "Zorg dat voornaamwoorden ('deze', 'dit', 'die') direct verwijzen naar een "
    "duidelijk antecedent in dezelfde zin"
)
#: Uitvoercontract dat ná de regelkaarten komt; aanwezig = staart niet afgekapt.
EEN_ZIN = "in één enkele zin, zonder toelichting"

ORG = ["Synthetische Proefdienst"]
CONTEXTEN = [
    ({}, False),
    ({"org": ORG}, False),
    ({"jur": ["bestuursrecht"]}, True),
    ({"wet": ["Synthetische Proefwet"]}, True),
]
CONTEXT_IDS = ["geen", "alleen-organisatorisch", "alleen-juridisch", "alleen-wettelijk"]


def _request(**context) -> GenerationRequest:
    return GenerationRequest(
        id=str(uuid.uuid4()),
        begrip="proefvergunning",
        ontologische_categorie="type",
        organisatorische_context=context.get("org"),
        juridische_context=context.get("jur"),
        wettelijke_basis=context.get("wet"),
    )


def _enriched(**base) -> EnrichedContext:
    return EnrichedContext(
        base_context={"organisatorisch": [], "juridisch": [], "wettelijk": [], **base},
        sources=[],
        expanded_terms={},
        confidence_scores={},
        metadata={},
    )


def _int_module() -> JSONBasedRulesModule:
    # Zelfde constructie als in modular_prompt_adapter.py.
    module = JSONBasedRulesModule(
        rule_prefix="INT",
        module_id="integrity_rules",
        module_name="Integrity Validation Rules (INT)",
        header_emoji="🔒",
        header_text="Integriteit Regels (INT)",
        priority=70,
    )
    module.initialize({"include_examples": True})
    return module


def _ctx(enriched: EnrichedContext) -> ModuleContext:
    return ModuleContext(
        begrip="proefvergunning",
        enriched_context=enriched,
        config=UnifiedGeneratorConfig(),
        shared_state={},
    )


def _rule_ids(content: str) -> list[str]:
    """De gerenderde regel-ID's, in volgorde (kop: `🔹 **ID - Naam**`)."""
    return [
        regel[len("🔹 **") :].split(" - ", 1)[0]
        for regel in content.splitlines()
        if regel.startswith("🔹 **")
    ]


def _kaart(tekst: str, kop: str) -> list[str]:
    """De regels van één regelkaart: vanaf de kop tot de volgende kop/sectie."""
    regels = tekst.split(kop, 1)[1].split("\n")
    kaart = [kop + regels[0]]
    for regel in regels[1:]:
        if regel.startswith(("🔹", "###")) or regel.strip() == "":
            break
        kaart.append(regel)
    return kaart


# ---------------------------------------------------------------------------
# Module: selectie en instructietekst
# ---------------------------------------------------------------------------


def test_int_module_toont_int03_naast_int01_zonder_juridische_context():
    module = _int_module()
    for enriched in (_enriched(), _enriched(organisatorisch=ORG)):
        zonder = module.execute(_ctx(enriched))
        assert zonder.success is True
        # Smal: precies INT-01 en INT-03; geen andere INT-regel.
        assert _rule_ids(zonder.content) == ["INT-01", "INT-03"]
        assert zonder.metadata["rules_count"] == 2
        assert "INT-03" not in zonder.metadata["rules_skipped"]
        assert {"INT-02", "INT-04"} <= set(zonder.metadata["rules_skipped"])


def test_int_module_met_juridische_context_toont_de_ongewijzigde_volledige_set():
    module = _int_module()
    zonder = module.execute(_ctx(_enriched()))
    met = module.execute(_ctx(_enriched(wettelijk=["Synthetische Proefwet"])))
    assert met.metadata["rules_skipped"] == []
    assert "INT-03" in _rule_ids(met.content)
    assert sorted(_rule_ids(met.content)) == sorted(
        ["INT-01", "INT-03", *zonder.metadata["rules_skipped"]]
    )


def test_int03_kaart_draagt_de_volledige_g_instructie_en_het_astra_paar():
    content = _int_module().execute(_ctx(_enriched())).content
    assert INT03_KAART in content
    kaart = _kaart(content, INT03_KAART)
    assert kaart[0] == "🔹 **INT-03 - Voornaamwoord-verwijzing duidelijk**"
    assert INSTRUCTIEREGEL in kaart
    assert OUDE_INSTRUCTIE not in content
    # Het ASTRA-voorbeeldpaar uit INT-03.json blijft de getoonde onderbouwing.
    assert any(r.strip().startswith("✅") for r in kaart)
    assert any(r.strip().startswith("❌") for r in kaart)


# ---------------------------------------------------------------------------
# De feitelijk gebouwde prompt (PromptServiceV2 → adapter → orchestrator)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(("context", "juridisch"), CONTEXTEN, ids=CONTEXT_IDS)
async def test_int03_met_g_instructie_in_echte_prompt_bij_elke_context(
    context, juridisch
):
    prompt = (await PromptServiceV2().build_generation_prompt(_request(**context))).text

    # Eén INT-03-kaart, met de volledige G-instructie als eigen regel.
    assert prompt.count(INT03_KAART) == 1
    assert INSTRUCTIEREGEL in _kaart(prompt, INT03_KAART)
    assert OUDE_INSTRUCTIE not in prompt
    # Binnen de harde kap en niet afgekapt: de staart met het uitvoercontract
    # staat ná de INT-03-kaart.
    assert len(prompt) <= PromptComponentConfig().max_prompt_length
    assert prompt.index(G_INSTRUCTIE) < prompt.rindex(EEN_ZIN)

    ids = _rule_ids(prompt)
    int_ids = [i for i in ids if i.startswith("INT")]
    sam_ids = [i for i in ids if i.startswith("SAM")]
    con_ids = [i for i in ids if i.startswith("CON")]
    assert "CON-02" in con_ids
    if juridisch:
        # Bestaande toepasselijkheid: volledige INT- en SAM-set.
        assert {"INT-01", "INT-02", "INT-03"} <= set(int_ids)
        assert sam_ids
    else:
        # Smal: alleen INT-01 en INT-03; overige INT en SAM ongewijzigd afwezig.
        assert int_ids == ["INT-01", "INT-03"]
        assert not sam_ids
    if not context:
        # DEF-743 ongewijzigd: zonder context uitsluitend de bronbasisregel.
        assert con_ids == ["CON-02"]


@pytest.mark.asyncio
async def test_provider_ontvangt_int03_bij_alleen_organisatorische_context(
    tmp_path, monkeypatch
):
    """Ketenbewijs tot de providergrens via de echte generatie-orchestrator;
    alleen de netwerkgrens (provider) is bevroren."""
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

    antwoord = await orch.create_definition(_request(org=ORG))

    assert antwoord.success is True, antwoord.error
    [ontvangen] = provider.oproepen
    assert ontvangen.count(INT03_KAART) == 1
    assert INSTRUCTIEREGEL in _kaart(ontvangen, INT03_KAART)
    assert OUDE_INSTRUCTIE not in ontvangen
    assert "🔹 **INT-01" in ontvangen
    assert "🔹 **INT-02" not in ontvangen
    assert antwoord.definition.metadata["prompt_text"] == ontvangen
