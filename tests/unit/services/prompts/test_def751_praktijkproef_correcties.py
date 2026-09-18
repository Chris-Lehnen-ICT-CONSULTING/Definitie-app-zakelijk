"""DEF-751 praktijkproef (live-run-1, 17-09-2026): twee gerichte promptcorrecties.

1. De grammatica-instructie voor een deverbaal begrip schreef een betekenislaag
   voor op grond van de woordvorm ("Focus op het resultaat of de staat",
   "Vermijd procesbeschrijvingen"). Dat strijdt met ESS-02: de bedoelde
   betekenislaag volgt uit context, bronnen, categorie en verduidelijking,
   niet uit de vorm van het woord. Voor `registratie` (deverbaal) met
   categorie proces stond de prompt zichzelf tegen te spreken.
2. Na een expliciete verduidelijking van de gebruiker stelde het model bij de
   echte conflictbronnen dezelfde vraag opnieuw en voerde het de
   verduidelijking als `context: …`-bron van een lezing op (parser: grond
   niet aangeleverd). Het contract zegt nu expliciet dat de daarmee besliste
   tegenspraak niet opnieuw wordt gemeld en dat de verduidelijking nooit een
   bron of contextwaarde van een lezing is.

Echte modules, echte samengestelde prompt; geen modelaanroep. Deze tests
bewijzen de instructie, niet het modelgedrag.
"""

from __future__ import annotations

import pytest

from services.definition_generator_config import UnifiedGeneratorConfig
from services.definition_generator_context import EnrichedContext
from services.interfaces import GenerationRequest
from services.prompts.modules.base_module import ModuleContext
from services.prompts.modules.ess02_aanwijzing import GEDEELDE_ESS02_AANWIJZING
from services.prompts.modules.grammar_module import GrammarModule
from services.prompts.prompt_service_v2 import PromptServiceV2
from toetsregels.rule_cache import get_rule_cache

pytestmark = [pytest.mark.unit]

#: Vormgedreven betekenisvoorschriften die niet meer in de prompt mogen staan.
VORMGEDREVEN_OUD = (
    "Focus op het resultaat of de staat",
    "Vermijd procesbeschrijvingen",
    "het proces van registreren",
)


@pytest.fixture(autouse=True)
def _verse_regelcache():
    get_rule_cache().clear_cache()


def _grammatica(word_type: str) -> str:
    ctx = ModuleContext(
        begrip="registratie",
        enriched_context=EnrichedContext(
            base_context={},
            sources=[],
            expanded_terms={},
            confidence_scores={},
            metadata={},
        ),
        config=UnifiedGeneratorConfig(),
        shared_state={"word_type": word_type},
    )
    module = GrammarModule()
    module.initialize({"include_examples": True})
    out = module.execute(ctx)
    assert out.success
    return out.content


def test_deverbaal_regel_laat_de_betekenislaag_aan_bedoeling_en_context():
    tekst = _grammatica("deverbaal")
    for oud in VORMGEDREVEN_OUD:
        assert oud not in tekst, oud
    assert "Deverbaal-specifieke regels" in tekst
    assert "woordvorm bepaalt dat niet" in tekst
    assert "ESS-02" in tekst
    # Beide lagen zijn als voorbeeld toegestaan; alleen vermenging is fout.
    assert "activiteit bedoeld" in tekst and "uitkomst bedoeld" in tekst
    assert "lagen vermengd" in tekst


def test_werkwoord_en_overig_ongewijzigd():
    assert "Werkwoord-specifieke regels" in _grammatica("werkwoord")
    assert "specifieke regels" not in _grammatica("overig")


@pytest.mark.parametrize("category", ["proces", "resultaat", None])
async def test_echte_prompt_voor_deverbaal_kent_geen_vormgedreven_laag(category):
    request = GenerationRequest(
        id=f"def751-proef-{category}",
        begrip="registratie",
        ontologische_categorie=category,
        organisatorische_context=["Meetdienst"],
        actor="test_user",
    )
    prompt = (await PromptServiceV2().build_generation_prompt(request)).text
    assert "Termtype: deverbaal" in prompt
    for oud in VORMGEDREVEN_OUD:
        assert oud not in prompt, oud
    assert "woordvorm bepaalt dat niet" in prompt
    # ESS-01/ESS-02/CON-02 en het conflictcontract blijven staan.
    assert "hoogstens een herkenbaar voorlopig voorstel" in prompt
    assert prompt.count("kies niet stil") == 2
    assert "BRONNEN INSTRUCTIE (CON-02)" in prompt


async def test_contract_sluit_besliste_tegenspraak_en_verduidelijking_als_bron_uit():
    request = GenerationRequest(
        id="def751-proef-verduidelijkt",
        begrip="registratie",
        ontologische_categorie=None,
        organisatorische_context=["Meetdienst"],
        actor="test_user",
        betekenisverduidelijking="Bedoeld wordt de activiteit van het vastleggen.",
    )
    prompt = (await PromptServiceV2().build_generation_prompt(request)).text
    contract = prompt.split("Betekenisconflict (ESS-02)", 1)[1]
    assert "meld haar niet opnieuw" in contract
    assert "nooit op als bron of contextwaarde" in contract
    assert "ándere tegenspraak" in contract and "meld die opnieuw" in contract
    # De gedeelde aanwijzing draagt dezelfde grens (regelkaart én
    # betekenislaagsectie), zonder de bestaande tellingen te verstoren.
    assert "niet opnieuw gemeld" in GEDEELDE_ESS02_AANWIJZING
    assert prompt.count("niet opnieuw gemeld") == 2
    assert prompt.count("kies niet stil") == 2
    assert prompt.count("geldt niet als bevestiging") == 2
    assert prompt.count("eerst worden verduidelijkt") == 2
