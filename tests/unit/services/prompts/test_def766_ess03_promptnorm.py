"""ESS-03 (DEF-766): de werkelijke generatie-instructie; geen modelkwaliteitsclaim.

Bewijst dat de ESS-03-regelkaart en de échte samengestelde prompt de G-tekst
uit tekstvoorstellen-v3 dragen: bepaal uit de bedoelde betekenis wat één
instantie is, maak een noodzakelijke eenheidsgrens duidelijk met bovenbegrip
en kenmerken, gebruik een identifier alleen met onderbouwde scope, verzin
geen nummer/bron/telconventie en maak een stof niet stil tot monster. De
nummergerichte instructie ("Noem criteria voor unieke identificatie … zoals
serienummer, kenteken, ID, registratienummer") is vervallen. ESS-01 en ESS-02
blijven ongewijzigd. Een prompttest bewijst de instructies, niet de
kwaliteit van live modeluitvoer.
"""

from __future__ import annotations

import pytest

from services.definition_generator_config import UnifiedGeneratorConfig
from services.definition_generator_context import EnrichedContext
from services.interfaces import GenerationRequest
from services.prompts.modules.base_module import ModuleContext
from services.prompts.modules.json_based_rules_module import JSONBasedRulesModule
from services.prompts.prompt_service_v2 import PromptServiceV2
from toetsregels.rule_cache import get_rule_cache

pytestmark = [pytest.mark.unit]


@pytest.fixture(autouse=True)
def _verse_regelcache():
    # De promptmodules lezen via de gecachete manager (schijfcache, TTL 1 uur);
    # de regelkaart moet het actuele ESS-03.json tonen, niet een oudere lading.
    get_rule_cache().clear_cache()


#: Oude formuleringen die een nummerplicht of identifierlijst uitdrukten.
VERBODEN_OUD = (
    "Noem criteria voor unieke identificatie",
    "zoals serienummer, kenteken, ID, registratienummer",
    "uniek chassisnummer (VIN) en kenteken",
    "unieke kenmerken of identificatoren",
    "in elke situatie",
)

#: Kernzinnen van de G-instructie die op de regelkaart moeten staan.
G_KERN = (
    "Bepaal uit de bedoelde betekenis en de beschikbare onderbouwing wat als één instantie geldt",
    "passend bovenbegrip en begripsbepalende kenmerken",
    "verzin geen nummer, bron of telconventie",
    "monsters, porties of registraties",
    "Een naam of het woord ‘uniek’ is geen bewijs",
    "Houd registratiecontext en bronadministratie buiten de kern",
    # De verduidelijkingsvraag loopt via de ESS-03-beoordeling, niet via een
    # tweede uitvoerregel (uitvoercontract: één zin, alleen de kern).
    "de gerichte verduidelijkingsvraag blijft bij de ESS-03-beoordeling",
)

#: Instructies die een aparte melding of tweede uitvoerregel zouden vragen en
#: daarmee botsen met "één enkele zin" / "uitsluitend de definitiekern"
#: (reviewcorrectie P2 bij DEF-750; hier vooraf dichtgezet).
STRIJDIG_MET_UITVOERCONTRACT = (
    "Vraag bij een noodzakelijke onbesliste grens",
    "om gerichte verduidelijking.",
    "meld de ontbrekende keuze",
)

#: ESS-02-specifieke C3-formuleringen waarvan DEF-750/DEF-751-tests het
#: aantal op precies twee pinnen. ESS-03 draagt dezelfde scheiding in eigen
#: woorden, zodat die pins ESS-02-scoped blijven.
ESS02_GEPINDE_FRASEN = (
    "kies niet stil",
    "zonder werkelijke tegenspraak",
    "geef één voorlopige kandidaat",
    "Bij werkelijke tegenspraak",
)


def context(begrip: str = "meetobject", **metadata) -> ModuleContext:
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


def _ess03_kaart(content: str) -> str:
    _, rest = content.split("🔹 **ESS-03")
    return rest.split("🔹 **ESS-04")[0]


def test_ess03_regelkaart_draagt_de_g_instructie_en_het_semantische_paar():
    module = JSONBasedRulesModule("ESS-", "ess_rules", "ESS", "⚖", "ESS", 65)
    output = module.execute(context())
    assert output.success
    kaart = _ess03_kaart(output.content)
    assert "Instanties uniek onderscheidbaar (telbaarheid)" in kaart
    assert "administratieve identifier is niet verplicht" in kaart
    for kern in G_KERN:
        assert kern in kaart, kern
    assert (
        "✅ Afzonderlijk aaneengesloten landoppervlak dat op het afgesproken "
        "peilmoment volledig door water is omgeven." in kaart
    )
    assert (
        "❌ Boekexemplaar dat uitsluitend door zijn ISBN van andere fysieke "
        "exemplaren wordt onderscheiden." in kaart
    )
    for oud in VERBODEN_OUD:
        assert oud not in kaart, oud
    for frase in ESS02_GEPINDE_FRASEN:
        assert frase not in kaart, frase


def test_ess03_kandidaat_alleen_zonder_werkelijke_tegenspraak():
    """C3-scheiding (DEF-750/751) geldt ook op de ESS-03-kaart.

    De voorlopige kandidaat wordt uitsluitend gevraagd voor een onbesliste
    grens waarover bronnen en context elkaar níet werkelijk tegenspreken; bij
    werkelijke tegenspraak over de teleenheid geen stille keuze en geen
    betwiste telconventie in de kern. Geen tweede uitvoerregel of melding:
    de vraag blijft bij de ESS-03-beoordeling.
    """
    module = JSONBasedRulesModule("ESS-", "ess_rules", "ESS", "⚖", "ESS", 65)
    kaart = _ess03_kaart(module.execute(context()).content)
    delen = kaart.split("lever één voorlopige kandidaat")
    assert len(delen) == 2
    assert "elkaar niet werkelijk tegenspreken" in delen[0][-200:]
    assert "zonder melding of toelichting in de zin" in delen[1]
    assert "maak dan geen stille keuze" in kaart
    assert "leg geen betwiste telconventie in de kern vast" in kaart


def test_ess01_en_ess02_kaarten_ongewijzigd_naast_ess03():
    module = JSONBasedRulesModule("ESS-", "ess_rules", "ESS", "⚖", "ESS", 65)
    output = module.execute(context())
    ess01, rest = output.content.split("🔹 **ESS-02")
    ess02 = rest.split("🔹 **ESS-03")[0]
    assert "behoefte of eis van een belanghebbende" in ess01
    assert "geen automatische wijziging of regeneratie" in ess01
    assert "markerwoorden zijn niet vereist" in ess02
    assert "geen verplicht woordenlijstje" in ess02


@pytest.mark.parametrize("category", ["type", "proces", "exemplaar", None])
async def test_echte_samengestelde_prompt_volgt_de_ess03_norm(category):
    request = GenerationRequest(
        id=f"def766-{category}",
        begrip="meetobject",
        ontologische_categorie=category,
        organisatorische_context=["DJI"],
        actor="test_user",
    )
    result = await PromptServiceV2().build_generation_prompt(request)
    prompt = result.text
    assert prompt.count("🔹 **ESS-03") == 1
    for kern in G_KERN:
        assert prompt.count(kern) == 1, kern
    for oud in VERBODEN_OUD:
        assert oud not in prompt, oud
    for strijdig in STRIJDIG_MET_UITVOERCONTRACT:
        assert strijdig not in prompt, strijdig
    # De ESS-02-conflictmelding blijft de enige uitzondering op de uitvoer en
    # is niet stil naar ESS-03 verbreed.
    assert prompt.count("enige uitzondering op de definitie-uitvoer") == 1
    assert "Betekenisconflict (ESS-02)" in prompt
    # De aangrenzende besluiten blijven staan (ESS-01/ESS-02/CON-02).
    assert "behoefte of eis van een belanghebbende" in prompt
    assert "geen verplicht woordenlijstje" in prompt
    assert "BRONNEN INSTRUCTIE (CON-02)" in prompt
    # Het uitvoercontract is ongewijzigd: de G-tekst vraagt om gerichte
    # verduidelijking bij een onbesliste grens, niet om een tweede uitvoerregel.
    assert "één enkele zin" in prompt
