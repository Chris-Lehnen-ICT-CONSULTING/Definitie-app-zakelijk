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
from services.prompts.modules.definition_task_module import DefinitionTaskModule
from services.prompts.modules.expertise_module import ExpertiseModule
from services.prompts.modules.grammar_module import GrammarModule
from services.prompts.modules.prompt_orchestrator import PromptOrchestrator
from services.prompts.modules.template_module import TemplateModule

# Datum- of tijdachtige patronen die niet in een prompt thuishoren.
# Bewust ook een datum ZONDER tijd: die zou de kloksprong-test hieronder
# ontglippen (verandert pas om middernacht).
_TIJD_PATROON = re.compile(r"\d{4}-\d{2}-\d{2}|\d{2}:\d{2}:\d{2}")

# `test` = woordsoort "overig" (de default waarop de race terugviel),
# `detentie` = deverbaal, `controleren` = werkwoord.
_BEGRIPPEN = ("test", "detentie", "controleren")


def _context(category: str = "proces") -> EnrichedContext:
    """Context met béíde categorie-sleutels.

    `semantic_category` is wezenlijk: zonder die sleutel slaat
    `TemplateModule.validate_input` de module over, en dan blijft de
    template-helft van de DEF-582-race volledig ongedekt. In productie zet
    `prompt_service_v2.py:158` die key wél.
    """
    return EnrichedContext(
        base_context={"organisatorisch": ["DJI"], "domein": ["Rechtspraak"]},
        sources=[],
        expanded_terms={},
        confidence_scores={},
        metadata={
            "ontologische_categorie": category,
            "semantic_category": "Proces",
        },
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


def test_template_module_draait_en_krijgt_het_juiste_woordsoort():
    """De template-helft van DEF-582.

    `TemplateModule` leest hetzelfde `word_type` en werd door dezelfde race
    getroffen. Zonder `semantic_category` in de context slaat de module zichzelf
    over en dekt geen enkele test die helft.
    """
    builder = ModularPromptBuilder()
    for _ in range(30):
        prompt = builder.build_prompt(
            "controleren", _context(), UnifiedGeneratorConfig()
        )
        assert "Definitie Templates" in prompt, "template-module draait niet"
        assert "handeling waarbij [wie/wat]" in prompt, "werkwoord-patroon ontbreekt"


# --- Deterministische guards op de dependency-graaf --------------------------
#
# De herhalingstests hierboven zijn zwakke regressiedetectoren: de uitkomst ligt
# per PROCES vast (de batch-volgorde volgt uit set-iteratie, dus uit
# PYTHONHASHSEED), niet per build. Meer herhalingen binnen één proces helpen
# nauwelijks — een heringevoerde regressie glipt in ~43% van de CI-runs door.
# Onderstaande asserties zijn 100% rood zodra de declaratie verdwijnt.


@pytest.mark.parametrize(
    ("module_klasse", "verwacht"),
    [
        (GrammarModule, "expertise"),
        (TemplateModule, "expertise"),
        (DefinitionTaskModule, "expertise"),
    ],
)
def test_lezers_van_word_type_declareren_expertise(module_klasse, verwacht):
    """Wie `word_type` uit shared state leest, moet zijn schrijver declareren."""
    assert verwacht in module_klasse().get_dependencies()


def test_expertise_draait_in_een_eerdere_batch_dan_zijn_lezers():
    """De structurele garantie: geen enkele lezer zit in dezelfde batch."""
    builder = ModularPromptBuilder()
    orchestrator = next(
        v for v in vars(builder).values() if isinstance(v, PromptOrchestrator)
    )
    batches = orchestrator.resolve_execution_order()
    batch_van = {mid: i for i, batch in enumerate(batches) for mid in batch}

    for lezer in ("grammar", "template", "definition_task"):
        assert batch_van[lezer] > batch_van["expertise"], (
            f"'{lezer}' draait in dezelfde of een eerdere batch dan 'expertise' "
            "— de data-race op word_type is terug (DEF-582)"
        )


def test_deelregistratie_houdt_expertise_voor_zijn_lezers():
    """Ook met een deelverzameling modules blijft de volgorde gegarandeerd.

    Vóór de fix leverde precies dit `[['expertise', 'definition_task']]` op:
    één batch, dus dezelfde race.
    """
    orchestrator = PromptOrchestrator()
    orchestrator.register_module(ExpertiseModule())
    orchestrator.register_module(DefinitionTaskModule())
    batches = orchestrator.resolve_execution_order()

    assert batches[0] == ["expertise"]
    assert "definition_task" in batches[1]


@pytest.mark.parametrize("begrip", _BEGRIPPEN)
def test_casing_van_ontologische_categorie_wordt_genormaliseerd(begrip):
    """De casing van `ontologische_categorie` mag de prompt niet veranderen.

    Dit toetst de normalisatie in `DefinitionTaskModule._build_checklist`
    (`ontological_category.lower()`, DEF-447). Haal die `.lower()` weg en de
    focus-regel wordt `**PROCES**` in plaats van `**proces**` — dan falen deze
    asserties.

    Let op de scope: `semantic_category` wordt NIET genormaliseerd (TemplateModule
    neemt de casing letterlijk over in `_get_category_template` en in de header).
    Die inconsistentie is een aparte kwestie, zie DEF-584.
    """
    builder = ModularPromptBuilder()
    prompts = [
        builder.build_prompt(begrip, _context(cat), UnifiedGeneratorConfig())
        for cat in ("PROCES", "Proces", "pRoCeS", "proces")
    ]
    assert all(p == prompts[0] for p in prompts)
    # Expliciet: de genormaliseerde vorm staat in de prompt, de ruwe niet.
    assert "**proces**" in prompts[0]
    assert "**PROCES**" not in prompts[0]
