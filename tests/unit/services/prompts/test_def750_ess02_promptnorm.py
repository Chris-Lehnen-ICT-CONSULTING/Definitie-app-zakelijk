"""ESS-02 (DEF-750): de werkelijke generatie-instructies; geen modelkwaliteitsclaim.

Bewijst dat regelkaart, categoriehints, taakblok, uitvoerformaat en de échte
samengestelde prompt dezelfde besluiten volgen: niveau en aard apart, vier
overlappende richtingen zonder woordplicht, geen aparte markerregel in een
uitvoer die alleen de definitiekern mag bevatten, RESULTAAT niet standaard
'Maatregel', en de ESS-01-/CON-02-instructies ongewijzigd. Een prompttest
bewijst de instructies, niet de kwaliteit van live modeluitvoer.
"""

from __future__ import annotations

import pytest

from opschoning.opschoning_enhanced import extract_definition_from_gpt_response
from services.definition_generator_config import UnifiedGeneratorConfig
from services.definition_generator_context import EnrichedContext
from services.interfaces import GenerationRequest
from services.prompts.modules.base_module import ModuleContext
from services.prompts.modules.definition_task_module import DefinitionTaskModule
from services.prompts.modules.json_based_rules_module import JSONBasedRulesModule
from services.prompts.modules.output_specification_module import (
    OutputSpecificationModule,
)
from services.prompts.modules.semantic_categorisation_module import (
    SemanticCategorisationModule,
)
from services.prompts.modules.template_module import TemplateModule
from services.prompts.prompt_service_v2 import PromptServiceV2
from toetsregels.rule_cache import get_rule_cache

pytestmark = [pytest.mark.unit]


@pytest.fixture(autouse=True)
def _verse_regelcache():
    # De promptmodules lezen via de gecachete manager (schijfcache, TTL 1 uur);
    # de regelkaart moet het actuele ESS-02.json tonen, niet een oudere lading.
    get_rule_cache().clear_cache()


VIER = ["type", "proces", "resultaat", "exemplaar"]

#: Oude formuleringen die een markerplicht, exclusieve vierdeling of
#: onvoorwaardelijk woordverbod uitdrukten.
VERBODEN_OUD = (
    "Ontologische marker",
    "lever als eerste regel",
    "soort | exemplaar | proces | resultaat",
    "kies duidelijk tussen",
    "Je **moet**",
    "Start NOOIT met meta-woorden",
    "begin niet met 'soort'",
    "begin niet met 'type'",
    "(kies één)",
    "niet de ontologische marker",
)

#: De gedeelde ESS-02-aanwijzing die op elke promptplaats terug moet komen.
GEDEELDE_AANWIJZING = "geen verplicht woordenlijstje"


def context(begrip: str = "toezicht", **metadata) -> ModuleContext:
    return ModuleContext(
        begrip=begrip,
        enriched_context=EnrichedContext(
            base_context={},
            sources=[],
            expanded_terms={},
            confidence_scores={},
            metadata=metadata,
        ),
        config=UnifiedGeneratorConfig(),
        shared_state={},
    )


def test_ess02_regelkaart_met_generiek_voorbeeldpaar_en_ess01_ongewijzigd():
    module = JSONBasedRulesModule("ESS-", "ess_rules", "ESS", "⚖", "ESS", 65)
    output = module.execute(context())
    assert output.success
    ess01, rest = output.content.split("🔹 **ESS-02")
    ess02 = rest.split("🔹 **ESS-03")[0]
    # ESS-01 (DEF-746) blijft exact overeind.
    assert "behoefte of eis van een belanghebbende" in ess01
    assert "geen automatische wijziging of regeneratie" in ess01
    # ESS-02: niveau en aard, richtingen als hulp, generieke voorbeelden.
    assert "algemeen begrip" in ess02
    assert "één bepaald ding" in ess02
    assert "markerwoorden zijn niet vereist" in ess02
    assert "✅ document dat informatie over één behandeld onderwerp vastlegt" in ess02
    assert (
        "❌ activiteit of uitkomst van het vastleggen van meetwaarden in een register"
        in ess02
    )
    assert GEDEELDE_AANWIJZING in ess02
    for oud in VERBODEN_OUD:
        assert oud not in ess02, oud


@pytest.mark.parametrize("category", [*VIER, None])
def test_categoriehints_zijn_overlappende_richtingen_zonder_woordplicht(category):
    output = SemanticCategorisationModule().execute(
        context(ontologische_categorie=category)
    )
    assert output.success
    tekst = output.content
    assert "ESS-02" in tekst
    assert GEDEELDE_AANWIJZING in tekst
    for oud in VERBODEN_OUD:
        assert oud not in tekst, oud
    # Alle vier richtingen blijven zichtbaar als hulp, ook zonder categorie.
    for richting in ("TYPE", "PROCES", "RESULTAAT", "EXEMPLAAR"):
        assert richting in tekst
    if category == "type":
        assert "passend genus" in tekst
        # DEF-746: de ESS-01-grensgevallen blijven staan.
        assert "Grensgevallen: maatregel en interventie" in tekst
        assert "Zonder grond geen voorbeeld als algemeen correct presenteren" in tekst
    elif category == "proces":
        assert "activiteit als kern" in tekst
        assert "één bepaald voorval" in tekst
    elif category == "resultaat":
        assert "uitkomst als kern" in tekst
        assert (
            "een doel of functie alleen met begripsbepalende grond volgens ESS-01"
            in tekst
        )
        assert "niet noodzakelijk een maatregel" in tekst
    elif category == "exemplaar":
        assert "één bepaald ding" in tekst
        assert "identificatie" in tekst


def test_soort_en_type_zijn_geen_verboden_woorden():
    output = SemanticCategorisationModule().execute(
        context(ontologische_categorie="type")
    )
    tekst = output.content.lower()
    assert "verboden" not in tekst
    assert "nooit" not in tekst.replace("nooit met 'is een'", "")
    # Het genus 'soort' blijft toegestaan waar soorten zelf bedoeld zijn.
    assert "soort" in tekst


def test_taakblok_zonder_markerregel_en_met_niveau_hint():
    ctx = context()
    ctx.set_shared("ontological_category", "type")
    output = DefinitionTaskModule().execute(ctx)
    assert output.success
    for oud in VERBODEN_OUD:
        assert oud not in output.content, oud
    assert "CONSTRUCTIE GUIDE" in output.content
    assert "soort/categorie" not in output.content
    assert "algemeen begrip" in output.content
    # DEF-746: de ESS-01-kwaliteitscontrole blijft.
    assert "volgens ESS-01" in output.content
    assert "metadata" in output.content.lower()


def test_uitvoerformaat_telt_alleen_de_definitiekern():
    output = OutputSpecificationModule().execute(
        context(min_karakters=40, max_karakters=200)
    )
    assert output.success
    assert output.metadata["has_limit_warning"] is True
    assert "één enkele zin" in output.content
    assert "niet de ontologische marker" not in output.content
    assert "Tel alleen de definitie" in output.content


def test_resultaat_krijgt_een_uitkomsttemplate_geen_maatregel():
    output = TemplateModule().execute(context(semantic_category="Resultaat"))
    assert output.success
    assert "Template voor Resultaat" in output.content
    assert "niet noodzakelijk een maatregel" in output.content
    assert "[Uitkomst" in output.content
    assert "Maatregel" not in output.content.split("Aanbevolen definitiepatronen")[0]


@pytest.mark.parametrize("category", VIER)
async def test_echte_samengestelde_prompt_volgt_de_besluiten(category):
    request = GenerationRequest(
        id=f"def750-{category}",
        begrip="registratie",
        ontologische_categorie=category,
        organisatorische_context=["DJI"],
        actor="test_user",
    )
    result = await PromptServiceV2().build_generation_prompt(request)
    prompt = result.text
    assert result.metadata["ontologische_categorie"] == category
    for oud in VERBODEN_OUD:
        assert oud not in prompt, oud
    assert GEDEELDE_AANWIJZING in prompt
    assert "één enkele zin" in prompt
    # Regelkaart ESS-02 staat één keer; ESS-01 en CON-02 blijven staan.
    assert prompt.count("🔹 **ESS-02") == 1
    assert "behoefte of eis van een belanghebbende" in prompt
    assert "BRONNEN INSTRUCTIE (CON-02)" in prompt
    if category == "resultaat":
        assert "Template voor Resultaat" in prompt
        assert "Template voor Maatregel" not in prompt
    elif category == "type":
        assert "Template voor Object" in prompt


def test_parser_blijft_tolerant_voor_oude_markerregels():
    # Backcompat: een eventuele markerregel uit een ouder model of een
    # opgeslagen ruwe uitvoer wordt nog steeds gestript; zonder marker
    # verandert er niets.
    kern = "activiteit waarbij meetwaarden in een register worden vastgelegd"
    assert (
        extract_definition_from_gpt_response(f"Ontologische categorie: proces\n{kern}")
        == kern
    )
    assert extract_definition_from_gpt_response(kern) == kern
