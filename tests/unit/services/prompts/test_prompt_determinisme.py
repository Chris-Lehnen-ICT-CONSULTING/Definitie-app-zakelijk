"""De gegenereerde prompt moet deterministisch zijn (DEF-581).

`definition_task_module._build_metadata()` zette `datetime.now(UTC)` in de
prompt. Dezelfde invoer leverde daardoor elke seconde een andere prompt op:
niet reproduceerbaar, en de bron van een flaky required check
(`test_mixed_case_categories` vergelijkt vier prompts; onder CI-load rolde de
seconde om tussen twee builds).

Traceerbaarheid hoort in de logging, niet in de prompt naar het model.
"""

import re
import time

import pytest

pytestmark = pytest.mark.unit

from services.definition_generator_config import UnifiedGeneratorConfig
from services.definition_generator_context import EnrichedContext
from services.prompts.modular_prompt_builder import ModularPromptBuilder

# Datum- of tijdachtige patronen die niet in een prompt thuishoren.
# Bewust ook een datum ZONDER tijd: die zou de sleep-test hieronder ontglippen
# (verandert pas om middernacht) en zo een zeldzamere flakiness-klasse
# introduceren.
_TIJD_PATROON = re.compile(r"\d{4}-\d{2}-\d{2}|\d{2}:\d{2}:\d{2}")


def _context(category: str = "proces") -> EnrichedContext:
    return EnrichedContext(
        base_context={"organisatorisch": ["DJI"], "domein": ["Rechtspraak"]},
        sources=[],
        expanded_terms={},
        confidence_scores={},
        metadata={"ontologische_categorie": category},
    )


def test_prompt_bevat_geen_wisselende_tijdstempel():
    builder = ModularPromptBuilder()
    prompt = builder.build_prompt("test", _context(), UnifiedGeneratorConfig())
    gevonden = _TIJD_PATROON.search(prompt)
    assert gevonden is None, (
        f"prompt bevat een tijdstempel ({gevonden.group(0)}); dezelfde invoer "
        "levert dan elke seconde een andere prompt op"
    )


def test_zelfde_invoer_geeft_zelfde_prompt_over_de_tijd():
    """Twee builds met een echte secondewissel ertussen — de kern van DEF-581.

    Bewust een black-box-test met een echte `sleep`: de fix verwijdert de
    `datetime`-import uit de module, dus er valt niets meer te patchen. Een
    patch op `time.time` zou sowieso niets doen (`datetime.now()` leest de
    C-level klok) en de test vals-groen maken.

    Complementair aan de regex-test hierboven: die vangt één formaat, deze vangt
    élke per-build-variatie (epoch-int, uuid, sub-seconde). Ruim één seconde,
    zodat "%H:%M:%S" gegarandeerd omrolt — precies wat onder CI-load spontaan
    gebeurde.
    """
    builder = ModularPromptBuilder()
    eerste = builder.build_prompt("test", _context(), UnifiedGeneratorConfig())
    time.sleep(1.05)
    tweede = builder.build_prompt("test", _context(), UnifiedGeneratorConfig())
    assert eerste == tweede, "prompt hangt af van het moment van bouwen"


def test_casing_van_categorie_maakt_geen_verschil():
    """De assertie die `test_mixed_case_categories` bedoelde te doen — nu
    zonder tijdstempel-ruis, dus niet langer afhankelijk van machinesnelheid."""
    builder = ModularPromptBuilder()
    prompts = [
        builder.build_prompt("test", _context(cat), UnifiedGeneratorConfig())
        for cat in ("PROCES", "Proces", "pRoCeS", "proces")
    ]
    assert all(p == prompts[0] for p in prompts)
