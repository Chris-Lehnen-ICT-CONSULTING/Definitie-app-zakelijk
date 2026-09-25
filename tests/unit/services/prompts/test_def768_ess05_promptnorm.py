"""ESS-05 (DEF-768): de werkelijke generatie-instructie; geen modelkwaliteitsclaim.

Bewijst dat de ESS-05-regelkaart en de échte samengestelde prompt de G-tekst
(synthese ESS-05, §6.5 v2) dragen: kies bovenbegrip en toespitsende kenmerken
die het begrip in de context onderscheiden van de aangeleverde verwante
begrippen, zodat de kern per verwant begrip een onderbouwd verschil in
kenmerken uitdrukt (kenmerkvraag, K-3b; geen extensietoets: overlap van
gevallen zoals lener én werknemer is geen gebrek, ESS05-E05), verzin geen
verwant begrip, kenmerk of bron, en laat 'uniek', 'specifiek' of
'onderscheidend kenmerk' geen concreet kenmerk vervangen — als deel van een
naam, vaste term of noodzakelijke inhoud blijven ze staan (review 24-09,
correctie 1). Een ander woord alleen is nog geen afgrenzing: het kenmerk
grenst gevallen van het verwante begrip af die volgens bron of bedoelde
betekenis niet onder dit begrip vallen; gedeelde gevallen mogen (correctie 4,
binnen K-3b/K-5, zonder nieuw schema of verplichte invoer). De oude
trefwoordgerichte instructie ("Maak expliciet duidelijk waarin het begrip
zich onderscheidt") en de 'wat maakt dit uniek'-aanwijzing zijn vervallen; het
voorbeeldpaar is het ASTRA-paar. Een prompttest bewijst de instructies, niet
de kwaliteit van live modeluitvoer.
"""

from __future__ import annotations

import pytest

from services.interfaces import GenerationRequest
from services.prompts.modules.json_based_rules_module import JSONBasedRulesModule
from services.prompts.prompt_service_v2 import PromptServiceV2
from tests.unit.services.prompts.test_def766_ess03_promptnorm import (
    G_KERN as ESS03_G_KERN,
    context,
)
from toetsregels.rule_cache import get_rule_cache

pytestmark = [pytest.mark.unit]


@pytest.fixture(autouse=True)
def _verse_regelcache():
    get_rule_cache().clear_cache()


#: Kernzinnen van de G-instructie die op de ESS-05-regelkaart moeten staan.
G_KERN = (
    (
        "Kies een bovenbegrip en toespitsende kenmerken die het begrip binnen de "
        "gegeven context onderscheiden van de aangeleverde verwante begrippen"
    ),
    (
        "de kern drukt per verwant begrip een onderbouwd verschil in kenmerken uit "
        "ten opzichte van de beschrijving van dat begrip"
    ),
    (
        "Overlap van gevallen is geen gebrek: een persoon of object dat beide "
        "rollen vervult, maakt de definitie niet onvoldoende onderscheidend"
    ),
    "verzin geen verwant begrip, kenmerk of bron",
    "vernauw de betekenis niet verder dan de bron draagt",
    "geen niet-begripsbepalend doel of gebruik zijn (ESS-01)",
    "hoort niet in de kern",
    # Review 24-09, correctie 4 (RE5-01 binnen K-3b/K-5): een ander woord is
    # nog geen afgrenzing; gedeelde gevallen mogen; niets verzinnen.
    "Een ander woord of een ander kenmerk alleen is nog geen afgrenzing",
    (
        "gevallen van het verwante begrip afgrenzen die volgens bron of bedoelde "
        "betekenis niet onder dit begrip vallen; gedeelde gevallen mogen"
    ),
    "verzin geen tegenvoorbeeld of betekenis om een afgrenzing te maken",
    # Review 24-09, correctie 1: geen trefwoordverbod.
    (
        "zijn op zichzelf geen kenmerk en vervangen geen concreet kenmerk; als "
        "deel van een door de bron gedragen naam, vaste term of noodzakelijke "
        "inhoud blijven ze staan"
    ),
    "de vergelijking blijft bij de ESS-05-beoordeling open",
)

#: Een trefwoordverbod (review 24-09, correctie 1): de woorden mogen als deel
#: van een naam, vaste term of noodzakelijke inhoud blijven staan.
VERBODEN_TREFWOORDVERBOD = (
    "zijn geen kenmerk en horen niet in de kern",
    "‘uniek’ of ‘specifiek’ is geen kenmerk)",
)

#: Oude formuleringen die een trefwoord of vergelijkingsfrase uitlokten.
VERBODEN_OUD = (
    "Maak expliciet duidelijk waarin het begrip zich onderscheidt",
    "wat maakt dit uniek",
    "VERSCHIL met verwante begrippen (hoe te onderscheiden)",
    "Reclasseringstoezicht: toezicht gericht op gedragsverandering",
)

#: Extensietoets (afgewezen door K-3b, ESS05-E05): mag in geen enkele module
#: van de generatieprompt staan. Eén persoon kan lener én werknemer zijn.
VERBODEN_EXTENSIETOETS = (
    "geen geval van zo'n begrip",
    "aan alle kenmerken van de definitie kunnen voldoen",
    "mag aan alle kenmerken",
)


def _ess05_kaart(content: str) -> str:
    _, rest = content.split("🔹 **ESS-05")
    return rest.split("🔹 **")[0]


def test_ess05_regelkaart_draagt_de_g_instructie_en_het_astra_paar():
    module = JSONBasedRulesModule("ESS-", "ess_rules", "ESS", "⚖", "ESS", 65)
    output = module.execute(context())
    assert output.success
    kaart = _ess05_kaart(output.content)
    for kern in G_KERN:
        assert kern in kaart, kern
    assert "✅ Incident waarbij een jeugdige zonder toestemming één van de" in kaart
    assert (
        "❌ Incident waarbij een jeugdige zonder toestemming de justitiële "
        "jeugdinrichting verlaat." in kaart
    )
    for oud in VERBODEN_OUD:
        assert oud not in kaart, oud
    for extensie in VERBODEN_EXTENSIETOETS:
        assert extensie not in kaart, extensie
    for verbod in VERBODEN_TREFWOORDVERBOD:
        assert verbod not in kaart, verbod


@pytest.mark.parametrize(
    "begrip",
    ["bijzondere bijstand", "specifieke uitkering", "unieke identificatiecode"],
)
async def test_noodzakelijke_naam_met_trefwoord_wordt_niet_verboden(begrip):
    """Een vaste term met 'bijzonder', 'specifiek' of 'uniek' krijgt geen verbod.

    De prompt noemt de woorden alleen als niet-vervanging van een concreet
    kenmerk en behoudt ze uitdrukkelijk als deel van een naam of vaste term.
    """
    request = GenerationRequest(
        id=f"def768-naam-{begrip}",
        begrip=begrip,
        ontologische_categorie="type",
        organisatorische_context=["DJI"],
        actor="test_user",
    )
    prompt = (await PromptServiceV2().build_generation_prompt(request)).text
    assert begrip in prompt
    assert "als deel van een door de bron gedragen naam, vaste term" in prompt
    for verbod in VERBODEN_TREFWOORDVERBOD:
        assert verbod not in prompt, verbod
    assert "‘uniek’ of ‘specifiek’ is op zichzelf geen kenmerk" in prompt


@pytest.mark.parametrize("category", ["type", "proces", "resultaat", "exemplaar", None])
async def test_echte_samengestelde_prompt_volgt_de_ess05_norm(category):
    request = GenerationRequest(
        id=f"def768-{category}",
        begrip="lener",
        ontologische_categorie=category,
        organisatorische_context=["DJI"],
        actor="test_user",
    )
    prompt = (await PromptServiceV2().build_generation_prompt(request)).text
    assert prompt.count("🔹 **ESS-05") == 1
    for kern in G_KERN:
        assert prompt.count(kern) == 1, kern
    for oud in VERBODEN_OUD:
        assert oud not in prompt, oud
    for extensie in VERBODEN_EXTENSIETOETS:
        assert extensie not in prompt, extensie
    for verbod in VERBODEN_TREFWOORDVERBOD:
        assert verbod not in prompt, verbod
    # De ESS-03-kernzinnen blijven elk precies één keer staan: ESS-05 gebruikt
    # voor de CON-01-scheiding een eigen formulering.
    for kern in ESS03_G_KERN:
        assert prompt.count(kern) == 1, kern
