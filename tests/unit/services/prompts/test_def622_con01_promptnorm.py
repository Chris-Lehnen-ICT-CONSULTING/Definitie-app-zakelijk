"""DEF-622 (B-02): de generatieprompts volgen de CON-01-norm.

De registratiecontext blijft buiten de definitiezin, maar een naam die
inhoudelijk noodzakelijk is om het begrip af te bakenen of te identificeren
mag erin staan. De oude instructie ("VERMIJD het expliciet noemen van
contextnamen") was een absoluut verbod en stuurde de generator weg van een
toegestane, soms noodzakelijke naam. De algemene passendheidstoets is
DEF-742 en hoort hier niet.
"""

from __future__ import annotations

import pytest

from services.definition_generator_config import UnifiedGeneratorConfig
from services.definition_generator_context import ContextSource, EnrichedContext
from services.prompts.modules.base_module import ModuleContext
from services.prompts.modules.context_awareness_module import ContextAwarenessModule

pytestmark = [pytest.mark.unit]

NOODZAKELIJK = "inhoudelijk noodzakelijk"
REGISTRATIE = "registratiecontext"
VERBODEN_OUD = (
    "VERMIJD het expliciet noemen van contextnamen",
    "zonder de context expliciet te benoemen",
    "zonder deze expliciet te benoemen",
)


def _ctx(base_items: int, sources: int, expanded: int) -> ModuleContext:
    enriched = EnrichedContext(
        base_context={
            "organisatorisch": [f"Stichting {i}" for i in range(base_items)],
            "juridisch": [],
            "wettelijk": [],
        },
        sources=[
            ContextSource(source_type="web_lookup", confidence=0.9, content="A")
            for _ in range(sources)
        ],
        expanded_terms={f"K{i}": f"V{i}" for i in range(expanded)},
        confidence_scores={"web_lookup": 0.9} if sources else {},
        metadata={},
    )
    return ModuleContext(
        begrip="keurmerk",
        enriched_context=enriched,
        config=UnifiedGeneratorConfig(),
        shared_state={},
    )


@pytest.mark.parametrize(
    ("base_items", "sources", "expanded", "niveau"),
    [
        (1, 0, 0, "minimal"),
        (2, 1, 0, "moderate"),
        (10, 2, 5, "rich"),
    ],
)
def test_contextinstructie_kent_de_noodzakelijke_naamuitzondering(
    base_items, sources, expanded, niveau
):
    mod = ContextAwarenessModule()
    mod.initialize({})
    out = mod.execute(_ctx(base_items, sources, expanded))
    assert out.success is True
    assert out.metadata.get("formatting_level") in {niveau, "rich", "moderate"}
    tekst = out.content
    assert REGISTRATIE in tekst, tekst
    assert NOODZAKELIJK in tekst, tekst
    for oud in VERBODEN_OUD:
        assert oud not in tekst, oud


def test_regelinstructie_con01_kent_de_uitzondering():
    from services.prompts.modules.json_based_rules_module import (
        JSONBasedRulesModule,
    )

    # Zelfde constructie als de CON-module in modular_prompt_adapter.py.
    module = JSONBasedRulesModule(
        rule_prefix="CON-",
        module_id="con_rules",
        module_name="Context Validation Rules (CON)",
        header_emoji="🌐",
        header_text="Context Regels (CON)",
        priority=70,
    )
    con01 = module._get_instruction_for_rule("CON-01") or ""
    assert REGISTRATIE in con01
    assert NOODZAKELIJK in con01
    assert "zonder expliciete benoeming van contextnamen" not in con01


@pytest.mark.parametrize("categorie", [None, "type", "proces"])
def test_afsluitende_checklist_spreekt_de_uitzondering_niet_tegen(categorie):
    """K6: de actieve DefinitionTaskModule-checklist stond nog op een
    ongeclausuleerd verbod ("Context verwerkt zonder expliciete benoeming")
    naast de gewijzigde CON-01-instructie."""
    from services.prompts.modules.definition_task_module import DefinitionTaskModule

    checklist = DefinitionTaskModule()._build_checklist(categorie)
    assert "zonder expliciete benoeming" not in checklist
    assert NOODZAKELIJK in checklist
    assert REGISTRATIE in checklist
