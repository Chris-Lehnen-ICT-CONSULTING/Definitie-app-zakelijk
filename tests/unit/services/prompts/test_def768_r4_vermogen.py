"""DEF-768 ronde 4: G behoudt een door de bron toegekend vermogen bij het begrip.

Bevinding R3 (reports/DEF-768-AI-20260924-R3/uitkomst-en-vervolg-v1.md, R3G3):
de bron kent een ring het vermogen toe een afstand te veranderen; alle vier
antwoorden (basis en actueel) maakten er een feitelijke handeling van
("verandert"). Oorzaakshypothese (coordinator-bevindingen-v1.json, niet
geïsoleerd): ARAI-04/ARAI-04SUB1 verbieden 'kan'/'kunnen' en de R3-behoudzin
zei niet hoe een vermogen zonder modaal werkwoord behouden blijft.

Herstel: de bestaande R3-behoudzin preciseren. Een vermogen, bevoegdheid of taak
van het begrip blijft een kenmerk van het begrip zelf: geen uitgevoerde
handeling, niet toegeschreven aan het object waarop het werkt (ook niet als
passieve eigenschap daarvan), zonder modaal werkwoord geformuleerd. ARAI-norm
en -validatie blijven ongewijzigd; geen nieuw woordverbod.

Constructiebewijs op de echte G-prompt; geen claim over modeluitkomsten.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import sys
from pathlib import Path

import pytest

from services.prompts.modules.json_based_rules_module import JSONBasedRulesModule
from tests.unit.services.prompts.test_def768_r3_relatiebehoud import (
    GEDEELD_BEHOUD,
    GEEN_VERSCHUIVING,
)
from toetsregels.rule_cache import get_rule_cache

pytestmark = [pytest.mark.unit]

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts" / "ess05"))

import proefinvoer as pi

R3_G_INVOER = (
    ROOT / "reports" / "DEF-768-AI-20260924-R3" / "onafhankelijke-g-invoer-v1.json"
)
R3_ACTUEEL_SHA = "d8a0663cf5aca973be7c40dce3aeb1b99512495c50c19fe17a5fe227d0d3bca5"

#: R5 (R4-E04) vervangt deze zin gericht: het vermogen hoort bij de drager die
#: de bron aanwijst (zie test_def768_r5_drager.py). De R3G3-bescherming (geen
#: uitvoering, niet naar het object, zonder modaal werkwoord) blijft erin.
VERMOGEN = (
    "Ook een vermogen, bevoegdheid of taak die de bron toekent, blijft een kenmerk "
    "van de drager die de bron daarvoor aanwijst: maak er geen feitelijk "
    "uitgevoerde handeling van, schrijf het niet toe aan het object waarop het "
    "betrekking heeft, ook niet als eigenschap van dat object, en formuleer het "
    "zonder modaal werkwoord als eigenschap van die drager (zoals ‘met het vermogen "
    "om …’); is die drager een ander dan wat het gekozen bovenbegrip aanduidt, "
    "zoals de persoon die een rol vervult, schrijf het dan niet aan het "
    "bovenbegrip toe, maar verbind het via de relatie uit de bron, zoals een rol "
    "die die bevoegdheid inhoudt."
)
#: ARAI-04-instructies blijven byte-gelijk (norm/validatie niet gewijzigd door
#: DEF-768). Integratie met main: DEF-770 (INT-01 vervolg) gaf beide een
#: voorrangsregel voor bronmodaliteit; de pin volgt die geïntegreerde basis.
ARAI = {
    "ARAI-04": (
        "Vermijd modale hulpwerkwoorden zoals 'kan', 'moet', 'mag', 'zal'. "
        "Drukt de bron een mogelijkheid, toestemming of niet-verplichting "
        "uit, maak daar dan geen feit of eis van: laat haar weg als zij het "
        "begrip niet afbakent, en druk haar anders uit zonder modaal "
        "werkwoord ('-baar', 'al dan niet', 'ongeacht')"
    ),
    "ARAI-04SUB1": (
        "Vermijd modale werkwoorden die onduidelijkheid scheppen over de "
        "essentie van het begrip; een mogelijkheid, toestemming of "
        "niet-verplichting uit de bron wordt daardoor geen feit of eis "
        "(zie ARAI-04)"
    ),
}
GEVALSWOORDEN = (
    "ring",
    "trommel",
    "afstand",
    "basis",
    "baan",
    "proef",
    "verstelbaar",
    "kelmurin",
    "relsuva",
)


@pytest.fixture(autouse=True)
def _verse_regelcache():
    get_rule_cache().clear_cache()


def _module() -> JSONBasedRulesModule:
    return JSONBasedRulesModule("ESS", "r4", "r4", "", "", 1)


def test_vermogenszin_precies_eenmaal_direct_na_de_r3_behoudzin():
    tekst = _module()._get_instruction_for_rule("ESS-05")
    assert tekst.count(VERMOGEN) == 1
    for zin in (GEDEELD_BEHOUD, GEEN_VERSCHUIVING):
        assert tekst.count(zin) == 1, zin
    einde_r3 = tekst.index(GEEN_VERSCHUIVING) + len(GEEN_VERSCHUIVING)
    assert tekst[einde_r3:].startswith(". " + VERMOGEN)


def test_g_actueel_instructie_is_gewijzigd():
    sha = hashlib.sha256(pi.huidige_g_instructie().encode("utf-8")).hexdigest()
    assert sha != R3_ACTUEEL_SHA


def test_arai_instructies_ongewijzigd():
    module = _module()
    for regel, tekst in ARAI.items():
        assert module._get_instruction_for_rule(regel) == tekst


def test_geen_gevalswoorden_en_geen_nieuw_woordverbod():
    laag = VERMOGEN.lower()
    for woord in GEVALSWOORDEN:
        assert woord not in laag, woord
    for verbod in ("gebruik nooit", "vermijd het woord", "verboden"):
        assert verbod not in laag


@pytest.mark.skipif(
    not R3_G_INVOER.is_file(), reason="git-ignored R3-G-invoer ontbreekt"
)
@pytest.mark.parametrize("gid", ["R3G3", "R3G1"])
def test_r3_diagnose_g_prompt_draagt_vermogenszin_naast_arai(gid):
    data = json.loads(R3_G_INVOER.read_text(encoding="utf-8"))
    invoer = next(i for i in data["invoeren"] if i["id"] == gid)
    prompt = asyncio.run(pi.bouw_g_prompt(invoer))
    assert prompt.count(VERMOGEN) == 1
    # De stijlregel staat er nog; de precisering vervangt haar niet.
    assert "ARAI-04" in prompt
    pi.controleer_promptlengte(gid, "actueel", prompt)
