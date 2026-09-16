"""Werkelijke ESS-instructie-uitvoer; geen claim over modelkwaliteit."""

import pytest

from services.definition_generator_config import UnifiedGeneratorConfig
from services.definition_generator_context import EnrichedContext
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

pytestmark = [pytest.mark.unit]


def context(**metadata):
    return ModuleContext(
        begrip="toezicht",
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


def test_ess_regeluitvoer_met_primaire_voorbeelden_en_een_generatieinstructie():
    module = JSONBasedRulesModule("ESS-", "ess_rules", "ESS", "⚖", "ESS", 65)
    output = module.execute(context())
    assert output.success
    ess01 = output.content.split("🔹 **ESS-02")[0]
    assert "behoefte of eis van een belanghebbende" in ess01
    assert "meldpunt:" not in ess01
    assert "woordkeuze of zinsvorm beslist" in ess01.lower()
    assert "expliciet bevestigde domeinafbakening" in ess01
    assert "defect of ongebruikt exemplaar" in ess01
    assert "geen automatische wijziging of regeneratie" in ess01
    assert "niet WAARVOOR" not in ess01


@pytest.mark.parametrize("module", [OutputSpecificationModule, DefinitionTaskModule])
def test_overige_instructies_verwijzen_naar_functiegrens(module):
    output = module().execute(context())
    assert output.success
    assert "ESS-01" in output.content
    assert "niet het doel" not in output.content


@pytest.mark.parametrize(
    "category", ["Proces", "Object", "Maatregel", "Informatie", "algemeen"]
)
def test_templates_maken_geen_onvoorwaardelijk_doelvoorbeeld(category):
    output = TemplateModule().execute(context(semantic_category=category))
    assert output.success
    assert "[doel/functie]" not in output.content
    assert "[met welk doel/resultaat]" not in output.content
    assert "[doel/gebruik]" not in output.content
    for term in ("toezicht", "systeem", "interventie", "register"):
        assert f"✅ {term}:" not in output.content
    if category == "Proces":
        assert (
            "systematisch volgen van handelingen om naleving van regels te waarborgen"
            in output.content
        )
        assert "grensgeval" in output.content.lower()
        assert "begripsbepalend" in output.content


@pytest.mark.parametrize("category", ["type", "proces", "resultaat", "exemplaar"])
def test_categorie_is_geen_functiegrond(category):
    output = SemanticCategorisationModule().execute(
        context(ontologische_categorie=category)
    )
    assert output.success
    assert '✅ "maatregel die recidive moet voorkomen"' not in output.content
    assert '✅ "interventie gericht op gedragsverandering"' not in output.content
    assert "WAT het betekent/bewerkstelligt (doel/functie)" not in output.content
