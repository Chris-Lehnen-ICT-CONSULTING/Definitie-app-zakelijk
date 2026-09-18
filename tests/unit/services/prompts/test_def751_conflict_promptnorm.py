"""DEF-751 stap 2 — de echte eindprompt: conflictcontract en verduidelijking.

Bewijst de instructies, niet de modelkwaliteit:

* het conflictcontract staat precies één keer in de samengestelde prompt,
  als uitzondering op de definitie-only-uitvoer, met de uitsluitingen
  (overlap tussen richtingen, eigen onzekerheid, ontbrekend label ≠ conflict);
* een gebruikersverduidelijking reist als DATA binnen het bestaande
  `context`-datablok (gesaniteerd, één keer, geen nieuwe bron), en ontbreekt
  volledig wanneer er geen verduidelijking is;
* de verduidelijking wordt als gebruikersbedoeling geframed — een keuze van
  de betekenislaag, geen bewezen bronfeit en geen ESS-02-oordeel — en een
  nieuwe tegenspraak wordt opnieuw gemeld;
* de DEF-750-tellingen en de ESS-01-/CON-02-instructies blijven intact.
"""

from __future__ import annotations

import re

import pytest

from services.interfaces import GenerationRequest
from services.modelantwoord import CONFLICT_SENTINEL
from services.prompts.modules.context_awareness_module import VERDUIDELIJKING_KOP
from services.prompts.modules.ess02_aanwijzing import GEDEELDE_ESS02_AANWIJZING
from services.prompts.prompt_service_v2 import PromptServiceV2
from toetsregels.rule_cache import get_rule_cache

pytestmark = [pytest.mark.unit]

VERDUIDELIJKING = "Bedoeld is de handeling van het vastleggen, leeftijd < 18 jaar"


@pytest.fixture(autouse=True)
def _verse_regelcache():
    get_rule_cache().clear_cache()


def _request(**extra) -> GenerationRequest:
    return GenerationRequest(
        id="def751-stap2",
        begrip="registratie",
        ontologische_categorie=extra.pop("categorie", "proces"),
        organisatorische_context=["DJI"],
        actor="test_user",
        **extra,
    )


async def _prompt(**extra) -> str:
    return (await PromptServiceV2().build_generation_prompt(_request(**extra))).text


def _contextblok(prompt: str) -> str:
    blokken = re.findall(r"<context>(.*?)</context>", prompt, flags=re.DOTALL)
    assert len(blokken) == 1, "precies één context-datablok"
    return blokken[0]


@pytest.mark.parametrize(
    "categorie", ["type", "proces", "resultaat", "exemplaar", None]
)
async def test_conflictcontract_staat_een_keer_als_uitzondering_op_definitie_only(
    categorie,
):
    prompt = await _prompt(categorie=categorie)
    # Het definitie-only-contract blijft.
    assert "één enkele zin, zonder toelichting" in prompt
    assert "Lever uitsluitend de definitiekern" in prompt
    # Het conflictcontract: sentinel, JSON-vorm, minstens twee lezingen met grond.
    assert prompt.count(CONFLICT_SENTINEL) == 1
    assert '"vraag"' in prompt and '"lezingen"' in prompt
    assert '"bron"' in prompt and '"grond"' in prompt
    assert "minstens twee" in prompt
    assert "bron NUMMER" in prompt and "context: CONTEXTWAARDE" in prompt
    # Geen nieuwe angle-bracket-tags in de instructies (DEF-590: de echte
    # datablok-tags zijn de enige).
    assert "<nr>" not in prompt and "<lezing>" not in prompt
    assert "Nooit een definitie én deze melding samen" in prompt
    assert "verzin geen bron" in prompt.lower()
    # Uitsluitingen: overlap, onzekerheid en ontbrekend label zijn geen conflict.
    assert "type/proces" in prompt
    assert "eigen onzekerheid" in prompt
    assert "ontbrekende categorie" in prompt
    assert "is géén conflict" in prompt
    # DEF-750-tellingen ongewijzigd (regelkaart + betekenislaagsectie).
    assert prompt.count("kies niet stil") == 2
    assert prompt.count("eerst worden verduidelijkt") == 2
    assert prompt.count("geldt niet als bevestiging") == 2
    assert prompt.count("zonder werkelijke tegenspraak") == 2
    assert prompt.count("Bij werkelijke tegenspraak") == 2
    assert len(prompt.split("geef één voorlopige kandidaat")) == 3
    # ESS-01 en CON-02 ongewijzigd.
    assert "hoogstens een herkenbaar voorlopig voorstel" in prompt
    assert "BRONNEN INSTRUCTIE (CON-02)" in prompt


async def test_zonder_verduidelijking_geen_verduidelijkingsdata_in_de_prompt():
    prompt = await _prompt()
    # De instructie noemt het kopje; de DATA-regel (kopje + dubbele punt +
    # tekst) ontbreekt volledig zonder verduidelijking.
    assert f"{VERDUIDELIJKING_KOP}:" not in prompt
    assert f"{VERDUIDELIJKING_KOP}:" not in _contextblok(prompt)
    assert VERDUIDELIJKING not in prompt
    assert "DJI" in _contextblok(prompt)


async def test_verduidelijking_staat_als_data_in_het_bestaande_contextblok():
    prompt = await _prompt(betekenisverduidelijking=VERDUIDELIJKING)
    blok = _contextblok(prompt)
    # Binnen het datablok, gesaniteerd (angle-bracket geëscaped), één keer.
    assert f"{VERDUIDELIJKING_KOP}: Bedoeld is de handeling" in blok
    assert "leeftijd &lt; 18 jaar" in blok
    assert "leeftijd < 18 jaar" not in prompt
    assert prompt.count(f"{VERDUIDELIJKING_KOP}:") == 1
    # Geen nieuwe bron: geen bronnenblok (de legenda in de CON-02-instructie
    # is geen blok) en geen 'ADDITIONELE BRON'.
    assert '<bron nr="1"' not in prompt
    assert "ADDITIONELE BRONNEN" not in prompt
    # De oorspronkelijke context blijft.
    assert "DJI" in blok
    # Buiten het datablok staat de verduidelijking nergens.
    buiten = prompt.replace(blok, "")
    assert "leeftijd &lt; 18" not in buiten


async def test_verduidelijking_is_gebruikersbedoeling_geen_bronfeit_of_oordeel():
    prompt = await _prompt(betekenisverduidelijking=VERDUIDELIJKING)
    # Framing in de instructies (niet in het datablok).
    assert "keuze van de bedoelde betekenislaag door de gebruiker" in prompt
    assert "herschrijf de bronnen niet" in prompt
    assert "meld die opnieuw" in prompt
    assert "geen bronfeit en geen ESS-02-oordeel" in prompt
    # Nooit als vastgesteld feit of als ESS-02-oordeel geformuleerd.
    for verboden in (
        "beslist altijd",
        "is de waarheid",
        "geldt als bronfeit",
        "ESS-02 is daarmee voldaan",
        "geldt als beoordeling",
    ):
        assert verboden not in prompt, verboden


def test_gedeelde_aanwijzing_verwijst_naar_de_verduidelijkingsroute_zonder_de_besluiten_te_verliezen():
    tekst = GEDEELDE_ESS02_AANWIJZING
    assert "kies niet stil" in tekst
    assert "geldt niet als bevestiging" in tekst
    assert "verduidelijking van de gebruiker" in tekst
    assert "bedoeling" in tekst
    assert "geen bronfeit" in tekst
