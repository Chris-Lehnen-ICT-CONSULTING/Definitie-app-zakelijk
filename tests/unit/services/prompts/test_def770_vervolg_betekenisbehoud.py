"""DEF-770 vervolg: betekenisbehoud bij generatie operationeel in de echte prompt.

Diagnose: logs/def770-vervolg/generatie-diagnose-v1.md. In G24 verloren nieuwe
teksten een bronhandeling (vervangen door een eigenschapswoord), een
relatiewoord, of maakten ze van een niet-verplichting een eis. Oorzaak volgens
de diagnose: (a) ARAI-04 leert 'kan beperken' → 'beperkt' zonder voorrangsregel
voor bronmodaliteit, en (b) de eindcontrole noemt betekenisbehoud zonder
controlehandeling.

Correctie: een voorrangsregel in de ARAI-04/ARAI-04SUB1-instructie en een
gerichte eindcontrole (bronhandeling, relatie, modaliteit) vóór de definitieve
formulering. Geen extra modelcall, geen G24-termen in productie.

Bewijsgrens: deze tests tonen dat de tekst de echte prompt bereikt, op de
bedoelde plek en zonder conflict met het uitvoercontract. Het zijn geen
bewijzen dat het model minder betekenisfouten maakt; dat vraagt een nieuwe
onafhankelijke effectproef.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from services.interfaces import GenerationRequest
from services.prompts.prompt_service_v2 import PromptServiceV2

pytestmark = [pytest.mark.unit]

SRC = Path(__file__).resolve().parents[4] / "src"
MODULES = [
    SRC / "services/prompts/modules/definition_task_module.py",
    SRC / "services/prompts/modules/json_based_rules_module.py",
]

#: De drie controlehandelingen en de voorrang boven stijlvoorkeuren.
EINDCONTROLE = (
    "Leg vóór de definitieve zin de bepalende bronpassages naast je formulering",
    "bronhandeling",
    "relatiewoord",
    "modaliteit",
    "gaat vóór stijlvoorkeuren",
)
#: Voorrangsregel bij ARAI-04 en ARAI-04SUB1.
MODALITEIT = (
    "mogelijkheid, toestemming of niet-verplichting",
    "geen feit of eis",
)
#: Termen uit de G24-dossiers of beoordelaarsvelden: nooit in productie.
LEKTERMEN = (
    "nulpaar",
    "samen bewaard",
    "aansluiting op",
    "invoertijd",
    "spiegelinschrijving",
    "herstelgrond",
    "aansluitverzoek",
    "beschermde_kenmerken",
    "bedoelde_betekenis",
    "beschermde_negaties",
)

CONTEXTEN = [
    {},
    {"org": ["Synthetische Proefdienst"]},
    {"jur": ["bestuursrecht"]},
    {"org": ["Synthetische Proefdienst"], "wet": ["Synthetische Proefwet"]},
]
CONTEXT_IDS = ["geen", "organisatorisch", "juridisch", "org+wet"]


def _request(**context) -> GenerationRequest:
    return GenerationRequest(
        id=str(uuid.uuid4()),
        begrip="proefvergunning",
        ontologische_categorie="type",
        organisatorische_context=context.get("org"),
        juridische_context=context.get("jur"),
        wettelijke_basis=context.get("wet"),
    )


def _kaart(prompt: str, regel: str) -> str:
    kaart = prompt.split(f"🔹 **{regel} - ", 1)[1]
    return kaart.split("🔹 **", 1)[0].split("###", 1)[0]


async def _prompt(**context) -> str:
    return (await PromptServiceV2().build_generation_prompt(_request(**context))).text


@pytest.mark.asyncio
@pytest.mark.parametrize("context", CONTEXTEN, ids=CONTEXT_IDS)
async def test_eindcontrole_in_echte_prompt_een_keer_voor_de_opdrachtafsluiting(
    context,
):
    prompt = await _prompt(**context)
    controle = prompt.split("KWALITEITSCONTROLE", 1)[1].split("####", 1)[0]
    for zinsdeel in EINDCONTROLE:
        assert zinsdeel in controle, zinsdeel
    assert prompt.count(EINDCONTROLE[0]) == 1
    # Vóór de afsluitende opdracht, zodat de controle vóór de definitieve
    # formulering gelezen wordt.
    assert prompt.index(EINDCONTROLE[0]) < prompt.index("Geef nu de definitie")


@pytest.mark.asyncio
@pytest.mark.parametrize("context", CONTEXTEN, ids=CONTEXT_IDS)
async def test_arai04_kaarten_dragen_voorrangsregel_bij_bronmodaliteit(context):
    prompt = await _prompt(**context)
    for regel in ("ARAI-04", "ARAI-04SUB1"):
        kaart = _kaart(prompt, regel)
        # De regel zelf blijft: modale werkwoorden vermijden.
        assert "odale" in kaart
        for zinsdeel in MODALITEIT:
            assert zinsdeel in kaart, (regel, zinsdeel)


@pytest.mark.asyncio
async def test_uitvoercontract_blijft_een_zin_zonder_toelichting():
    prompt = await _prompt(org=["Synthetische Proefdienst"])
    assert "Definitie in één enkele zin" in prompt
    assert "in één enkele zin, zonder toelichting" in prompt
    controle = prompt.split("KWALITEITSCONTROLE", 1)[1].split("####", 1)[0]
    # De eindcontrole vraagt geen tweede uitvoer, verantwoording of lijst.
    assert "lever uitsluitend de definitiekern" in controle.lower()


@pytest.mark.asyncio
async def test_geen_g24_termen_of_beoordelaarsvelden_in_prompt_of_modules():
    prompt = await _prompt(org=["Synthetische Proefdienst"])
    bronnen = [pad.read_text(encoding="utf-8") for pad in MODULES]
    for term in LEKTERMEN:
        assert term not in prompt, term
        for bron in bronnen:
            assert term not in bron, term
