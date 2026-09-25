"""DEF-768 R5 (E04): G koppelt een toegekend vermogen aan de door de bron aangewezen drager.

Bevinding R4-eindproef (reports/DEF-768-AI-20260924-R4/uitkomst-en-vervolg-v1.md,
R4-E04): twee actuele antwoorden schreven een bevoegdheid toe aan een rol als
bovenbegrip, terwijl de bron haar legt bij wie de rol vervult; de basisvariant
beschreef een rol die de bevoegdheid inhoudt. Oorzaakshypothese: de R4-zin
legde elk vermogen vast als "kenmerk van het begrip zelf", met het voorbeeld
‘bevoegd om …’.

Herstel: dezelfde zin gericht vervangen. Het vermogen hoort bij de drager die de
bron aanwijst; is dat een ander dan wat het bovenbegrip aanduidt, dan via de
bronrelatie. Geen verbod op een rol als bovenbegrip, geen verplichte exacte
formulering, geen nieuw woordverbod; ARAI-04 blijft ongewijzigd. Behouden:
vermogen bij het begrip zelf zonder modaal werkwoord (R3G3), geen verschuiving
naar het object, gedeelde relaties.

Constructiebewijs op de echte G-prompt; geen claim over modeluitkomsten.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
import sys
from pathlib import Path

import pytest

from services.prompts.modules.json_based_rules_module import JSONBasedRulesModule
from tests.unit.services.prompts.test_def768_r3_relatiebehoud import (
    GEDEELD_BEHOUD,
    GEEN_VERSCHUIVING,
)
from tests.unit.services.prompts.test_def768_r4_vermogen import ARAI
from toetsregels.rule_cache import get_rule_cache

pytestmark = [pytest.mark.unit]

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts" / "ess05"))

import proefinvoer as pi

R5_G = ROOT / "reports" / "DEF-768-AI-20260925-R5" / "g-ontwikkelinvoer-v1.json"
R4_ACTUEEL_SHA = "199dcf1c9f7e5b6e7f14c650de7126d0e934b5640855db50b52bd828e43ddbed"

DRAGER = (
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
#: De R4-zin die elk vermogen aan het begrip zelf legde.
OUD_R4 = (
    "blijft een kenmerk van het begrip zelf",
    "‘bevoegd om …’",
    "die de bron aan het begrip toekent, blijft",
)
GEVALSWOORDEN = (
    "kistvoogd",
    "ritvolger",
    "verzend",
    "deelnemer",
    "kist",
    "ring",
    "trommel",
    "afstand",
)


@pytest.fixture(autouse=True)
def _verse_regelcache():
    get_rule_cache().clear_cache()


def _module() -> JSONBasedRulesModule:
    return JSONBasedRulesModule("ESS", "r5", "r5", "", "", 1)


def test_dragerzin_precies_eenmaal_op_de_plaats_van_de_r4_zin():
    tekst = _module()._get_instruction_for_rule("ESS-05")
    assert tekst.count(DRAGER) == 1
    for zin in (GEDEELD_BEHOUD, GEEN_VERSCHUIVING):
        assert tekst.count(zin) == 1, zin
    einde = tekst.index(GEEN_VERSCHUIVING) + len(GEEN_VERSCHUIVING)
    assert tekst[einde:].startswith(". " + DRAGER + " Een onderscheidend kenmerk")


def test_r4_zin_is_vervangen():
    tekst = _module()._get_instruction_for_rule("ESS-05")
    for oud in OUD_R4:
        assert oud not in tekst, oud


def test_vermogen_bij_het_begrip_zelf_blijft_mogelijk():
    """R3G3: een vermogen dat de bron aan het begrip zelf toekent, blijft daar,
    als eigenschap en zonder modaal werkwoord."""
    assert "‘met het vermogen om …’" in DRAGER
    assert "zonder modaal werkwoord" in DRAGER
    assert "geen feitelijk uitgevoerde handeling" in DRAGER
    assert "schrijf het niet toe aan het object waarop het betrekking heeft" in DRAGER


def test_geen_rolverbod_geen_formuleringseis_geen_woordverbod():
    laag = DRAGER.lower()
    for verbod in (
        "gebruik nooit",
        "vermijd het woord",
        "verboden",
        "geen rol als bovenbegrip",
        "kies geen rol",
        "gebruik de formulering",
        "altijd de formulering",
        "letterlijk",
    ):
        assert verbod not in laag, verbod
    # Voorbeelden, geen eis.
    assert laag.count("zoals") == 3


def test_g_actueel_instructie_is_gewijzigd():
    sha = hashlib.sha256(pi.huidige_g_instructie().encode("utf-8")).hexdigest()
    assert sha != R4_ACTUEEL_SHA


def test_arai_instructies_ongewijzigd():
    module = _module()
    for regel, tekst in ARAI.items():
        assert module._get_instruction_for_rule(regel) == tekst


def test_geen_gevalswoorden():
    laag = DRAGER.lower()
    for woord in GEVALSWOORDEN:
        assert not re.search(rf"\b{woord}", laag), woord


@pytest.mark.skipif(not R5_G.is_file(), reason="R5-G-ontwikkelinvoer ontbreekt")
def test_r5_g_prompts_dragen_dragerzin_naast_arai_en_binnen_de_grens():
    data = json.loads(R5_G.read_text(encoding="utf-8"))
    assert [i["id"] for i in data["invoeren"]] == ["R4G1", "R4G1-D2", "R3G3", "R2G4"]
    termen = set()
    for invoer in data["invoeren"]:
        prompt = asyncio.run(pi.bouw_g_prompt(invoer))
        assert prompt.count(DRAGER) == 1, invoer["id"]
        assert "ARAI-04" in prompt
        pi.controleer_promptlengte(invoer["id"], "actueel", prompt)
        basis, _ = pi.basisvariant(
            prompt, pi.huidige_g_instructie(), data["g_teksten"]["basis"]["tekst"]
        )
        assert DRAGER not in basis
        pi.controleer_promptlengte(invoer["id"], "basis", basis)
        termen.add(str(invoer.get("begrip", "")).lower())
    laag = DRAGER.lower()
    for term in termen - {""}:
        assert not re.search(rf"\b{re.escape(term)}\b", laag), term
