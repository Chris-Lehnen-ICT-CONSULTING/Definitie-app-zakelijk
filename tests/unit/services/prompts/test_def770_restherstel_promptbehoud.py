"""DEF-770 restherstel: bronafbakening bij generatie, zonder ESS-01-normwijziging.

Diagnose (logs/def770-restherstel/claude-resultaat-v2.md, astra-review-v1): in
G24 vielen in beide varianten afbakenende gevolgen weg (een gevolg dat aan één
alternatief van een voorwaarde vastzit, ontkende gevolgen), en kreeg een
eigenschap die volgens de bron mag wisselen een vaste plaats in de definitie.
De eindcontrole toetste handeling, relatie en modaliteit, maar niet de
koppeling voorwaarde–gevolg; en MECHANISME 2 ('Vernauw begrippen met
domein-qualifiers') gaf een algemene opdracht tot vernauwen, zonder grens bij
de bronafbakening.

Correctie: de eindcontrole krijgt het punt voorwaarde en gevolg (elk
alternatief met eigen gevolg, ontkende gevolgen, uitzonderingen) en vervangt de
weglaatzin door een criterium dat ook de wisselende eigenschap omvat;
MECHANISME 2 kiest het domeinwoord binnen de bronafbakening; de INT-01-kaart
sluit daarop aan. ESS-01 blijft ongewijzigd.

Bewijsgrens: deze tests tonen dat de tekst de echte prompt bereikt, op de
bedoelde plek, in elke contextvariant. Het zijn geen bewijzen dat het model
minder betekenisfouten maakt; dat vraagt een nieuwe onafhankelijke effectproef.
"""

from __future__ import annotations

import json
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
    SRC / "services/prompts/modules/context_awareness_module.py",
]

CONTEXTEN = [
    {},
    {"org": ["Synthetische Proefdienst"]},
    {"jur": ["bestuursrecht"]},
    {"org": ["Synthetische Proefdienst"], "wet": ["Synthetische Proefwet"]},
]
CONTEXT_IDS = ["geen", "organisatorisch", "juridisch", "org+wet"]

#: Het nieuwe controlepunt in de eindcontrole.
VOORWAARDE_GEVOLG = (
    "voorwaarde en gevolg",
    "het gevolg dat de bron eraan koppelt",
    "elk alternatief",
    "ontkend gevolg",
    "uitzondering",
    "geen doel of effect in de zin van ESS-01",
)
#: De vervangen weglaatzin: nu een criterium, inclusief wisselende eigenschap.
WEGLAATCRITERIUM = (
    "Laat weg wat de bron niet als afbakening draagt",
    (
        "een eigenschap die volgens de bron mag wisselen zonder dat het begrip "
        "verandert"
    ),
)
OUDE_WEGLAATZIN = (
    "Een werkafspraak of mogelijkheid die het begrip niet afbakent, laat je weg "
    "in plaats van haar als eis op te nemen."
)
OUDE_MECHANISME_2 = "Vernauw begrippen met domein-qualifiers."
NIEUW_MECHANISME_2 = (
    "Kies het domeinspecifieke woord binnen de afbakening die de bron geeft",
    "niet smaller dan de bron",
)
#: Termen uit de G24-dossiers of beoordelaarsvelden: nooit in productie.
LEKTERMEN = (
    "onvolledigheidsmarkering",
    "wachttijd",
    "sorteertafel",
    "cyclusnummer",
    "heropent",
    "tegenstrijdigheid",
    "fasebuffer",
    "wisselbak",
    "controletafel",
    "terugzetverzoek",
    "beschermde_kenmerken",
    "beschermde_negaties",
)


def _request(**context) -> GenerationRequest:
    return GenerationRequest(
        id=str(uuid.uuid4()),
        begrip="proefvergunning",
        ontologische_categorie="type",
        organisatorische_context=context.get("org"),
        juridische_context=context.get("jur"),
        wettelijke_basis=context.get("wet"),
    )


async def _prompt(context=None, **velden) -> str:
    resultaat = await PromptServiceV2().build_generation_prompt(
        _request(**velden), context=context
    )
    return resultaat.text


def _eindcontrole(prompt: str) -> str:
    return prompt.split("KWALITEITSCONTROLE", 1)[1].split("####", 1)[0]


def _kaart(prompt: str, regel: str) -> str:
    kaart = prompt.split(f"🔹 **{regel} - ", 1)[1]
    return kaart.split("🔹 **", 1)[0].split("###", 1)[0]


@pytest.mark.asyncio
@pytest.mark.parametrize("velden", CONTEXTEN, ids=CONTEXT_IDS)
async def test_eindcontrole_draagt_voorwaarde_gevolg_en_weglaatcriterium(velden):
    prompt = await _prompt(**velden)
    controle = _eindcontrole(prompt)
    for zinsdeel in VOORWAARDE_GEVOLG + WEGLAATCRITERIUM:
        assert zinsdeel in controle, zinsdeel
    assert "controleer vier punten" in controle
    # Vervangen, niet aangevuld: de oude weglaatzin is weg.
    assert OUDE_WEGLAATZIN not in prompt
    # Voorrang ongewijzigd: vóór stijlvoorkeuren en vóór de opdrachtafsluiting.
    assert "gaat vóór stijlvoorkeuren" in controle
    assert prompt.index("voorwaarde en gevolg") < prompt.index("Geef nu de definitie")


@pytest.mark.asyncio
@pytest.mark.parametrize("velden", CONTEXTEN, ids=CONTEXT_IDS)
async def test_mechanisme_2_begrensd_door_bronafbakening(velden):
    prompt = await _prompt(**velden)
    assert OUDE_MECHANISME_2 not in prompt
    if "MECHANISME 2" in prompt:
        blok = prompt.split("MECHANISME 2", 1)[1].split("MECHANISME 3", 1)[0]
        for zinsdeel in NIEUW_MECHANISME_2:
            assert zinsdeel in blok, zinsdeel


@pytest.mark.asyncio
async def test_mechanisme_2_verschijnt_bij_context():
    """Het begrensde mechanisme bereikt de prompt waar contextmechanismen
    getoond worden; anders zou de test hierboven niets bewijzen."""
    prompt = await _prompt(org=["Synthetische Proefdienst"])
    assert "MECHANISME 2" in prompt
    assert NIEUW_MECHANISME_2[0] in prompt


@pytest.mark.asyncio
@pytest.mark.parametrize("velden", CONTEXTEN, ids=CONTEXT_IDS)
async def test_int01_kaart_harmonieert_met_eindcontrole(velden):
    kaart = _kaart(await _prompt(**velden), "INT-01")
    assert "met het gevolg dat de bron eraan koppelt" in kaart
    assert "mag wisselen" in kaart
    # Bestaande betekenisbehoudnorm blijft.
    assert "Neem bronbijzaken die het begrip niet afbakenen niet op" in kaart
    assert "toepassings- of eindvoorwaarde" in kaart


@pytest.mark.asyncio
@pytest.mark.parametrize("velden", CONTEXTEN, ids=CONTEXT_IDS)
async def test_ess01_norm_ongewijzigd_in_prompt(velden):
    """Geen ESS-01-normwijziging: de kaart volgt het ongewijzigde regelrecord."""
    record = json.loads((SRC / "toetsregels/regels/ESS-01.json").read_text("utf-8"))
    kaart = _kaart(await _prompt(**velden), "ESS-01")
    assert record["uitleg"] in kaart
    assert "niet-begripsbepalend doel, gewenst effect" in kaart


@pytest.mark.asyncio
async def test_bron_volledig_en_eindcontrole_samen_in_prompt():
    passage = (
        "Een proefvergunning vervalt bij een vastgestelde overtreding; tot die "
        "vaststelling blijft zij gelden. Verlenging volgt niet automatisch. De "
        "kleur van het vergunningsformulier kan per jaar verschillen."
    )
    context = {
        "documents": {
            "snippets": [
                {
                    "provider": "documents",
                    "title": "synthetisch proefdocument",
                    "filename": "synthetisch proefdocument",
                    "doc_id": "B01",
                    "snippet": passage,
                    "score": 0.0,
                    "selection_basis": "selected_short_document",
                    "used_in_prompt": True,
                    "citation_label": "volledig document",
                }
            ]
        }
    }
    resultaat = await PromptServiceV2().build_generation_prompt(
        _request(org=["Synthetische Proefdienst"]), context=context
    )
    [bron] = [
        s
        for s in resultaat.metadata["source_receipt"]["sources"]
        if s["source_type"] == "document"
    ]
    assert bron["content"] == passage and bron["truncated"] is False
    assert passage in resultaat.text
    for zinsdeel in VOORWAARDE_GEVOLG:
        assert zinsdeel in _eindcontrole(resultaat.text), zinsdeel


@pytest.mark.asyncio
async def test_geen_proeftermen_in_prompt_of_modules():
    prompt = await _prompt(org=["Synthetische Proefdienst"])
    bronnen = [pad.read_text(encoding="utf-8") for pad in MODULES]
    for term in LEKTERMEN:
        assert term not in prompt, term
        for bron in bronnen:
            assert term not in bron, term
