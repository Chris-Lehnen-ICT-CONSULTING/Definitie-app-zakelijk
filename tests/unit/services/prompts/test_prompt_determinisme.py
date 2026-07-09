"""De gegenereerde prompt moet deterministisch zijn (DEF-581, DEF-582).

Twee onafhankelijke bronnen van niet-determinisme, allebei gedicht:

1. **Wall-clock** (DEF-581). `definition_task_module._build_metadata()` zette
   `datetime.now(UTC)` in de prompt. Dezelfde invoer leverde elke seconde een
   andere prompt op — de bron van een flaky required check.

2. **Data-race op `word_type`** (DEF-582). `ExpertiseModule` schrijft het
   woordsoort in `shared_state`; `GrammarModule` en `TemplateModule` lazen het
   met een default terwijl ze geen dependency declareerden. Ze draaiden dus in
   dezelfde parallelle batch en wonnen soms van de schrijver, waarna het
   woordsoort-specifieke blok uit de prompt viel.

De begrippen hieronder zijn bewust gekozen: `_bepaal_woordsoort("test")` geeft
de default `"overig"`, waardoor de race voor dát begrip onzichtbaar is. Alleen
met een werkwoord (`controleren`) of een deverbaal (`detentie`) wordt hij
zichtbaar. Elke test die alleen `"test"` gebruikt, geeft valse zekerheid.
"""

import re

import pytest
from freezegun import freeze_time

pytestmark = pytest.mark.unit

from services.definition_generator_config import UnifiedGeneratorConfig
from services.definition_generator_context import EnrichedContext
from services.prompts.modular_prompt_builder import ModularPromptBuilder

# Datum- of tijdachtige patronen die niet in een prompt thuishoren.
# Bewust ook een datum ZONDER tijd: die zou de kloksprong-test hieronder
# ontglippen (verandert pas om middernacht).
_TIJD_PATROON = re.compile(r"\d{4}-\d{2}-\d{2}|\d{2}:\d{2}:\d{2}")

# `test` = woordsoort "overig" (de default waarop de race terugviel),
# `detentie` = deverbaal, `controleren` = werkwoord.
_BEGRIPPEN = ("test", "detentie", "controleren")


def _context(category: str = "proces") -> EnrichedContext:
    return EnrichedContext(
        base_context={"organisatorisch": ["DJI"], "domein": ["Rechtspraak"]},
        sources=[],
        expanded_terms={},
        confidence_scores={},
        metadata={"ontologische_categorie": category},
    )


@pytest.mark.parametrize("begrip", _BEGRIPPEN)
def test_prompt_bevat_geen_wisselende_tijdstempel(begrip):
    builder = ModularPromptBuilder()
    prompt = builder.build_prompt(begrip, _context(), UnifiedGeneratorConfig())
    gevonden = _TIJD_PATROON.search(prompt)
    assert gevonden is None, (
        f"prompt bevat een tijdstempel ({gevonden.group(0)}); dezelfde invoer "
        "levert dan elke seconde een andere prompt op"
    )


@pytest.mark.parametrize("begrip", _BEGRIPPEN)
def test_zelfde_invoer_geeft_zelfde_prompt_over_de_tijd(begrip):
    """Twee builds met een kloksprong ertussen — de kern van DEF-581.

    `freeze_time` patcht `datetime` zelf, dus dit werkt waar `patch("time.time")`
    faalt (`datetime.now()` leest de C-level klok). Een sprong van maanden vangt
    ook een datum-only timestamp, die één seconde slaap zou missen.
    """
    builder = ModularPromptBuilder()
    with freeze_time("2026-07-09 12:00:00"):
        eerste = builder.build_prompt(begrip, _context(), UnifiedGeneratorConfig())
    with freeze_time("2027-01-01 03:04:05"):
        tweede = builder.build_prompt(begrip, _context(), UnifiedGeneratorConfig())
    assert eerste == tweede, "prompt hangt af van het moment van bouwen"


@pytest.mark.parametrize("begrip", _BEGRIPPEN)
def test_zelfde_invoer_geeft_zelfde_prompt_bij_herhaling(begrip):
    """DEF-582: de data-race op `word_type` maakte de prompt niet-deterministisch
    zónder dat de klok een rol speelde.

    Genoeg herhalingen om de race te betrappen: ongefixt week `controleren` in
    ~11% van de builds af (13/120 gemeten, zonder CPU-druk).
    """
    builder = ModularPromptBuilder()
    eerste = builder.build_prompt(begrip, _context(), UnifiedGeneratorConfig())
    for _ in range(60):
        volgende = builder.build_prompt(begrip, _context(), UnifiedGeneratorConfig())
        assert volgende == eerste, (
            f"prompt voor '{begrip}' varieert tussen builds met identieke invoer "
            "(data-race op shared_state?)"
        )


def test_woordsoort_specifiek_blok_staat_altijd_in_de_prompt():
    """Het concrete symptoom van DEF-582: het werkwoord-blok viel willekeurig weg.

    Zonder de dependency-declaratie las `GrammarModule` het woordsoort voordat
    `ExpertiseModule` het geschreven had, viel terug op "overig", en liet de
    woordsoort-specifieke regels weg — het model kreeg dan andere instructies.
    """
    builder = ModularPromptBuilder()
    for _ in range(30):
        prompt = builder.build_prompt(
            "controleren", _context(), UnifiedGeneratorConfig()
        )
        assert "Werkwoord-specifieke regels" in prompt


@pytest.mark.parametrize("begrip", _BEGRIPPEN)
def test_casing_van_categorie_maakt_geen_verschil(begrip):
    """De assertie die `test_mixed_case_categories` bedoelde te doen — nu zonder
    tijdstempel-ruis en over meerdere woordsoorten."""
    builder = ModularPromptBuilder()
    prompts = [
        builder.build_prompt(begrip, _context(cat), UnifiedGeneratorConfig())
        for cat in ("PROCES", "Proces", "pRoCeS", "proces")
    ]
    assert all(p == prompts[0] for p in prompts)
