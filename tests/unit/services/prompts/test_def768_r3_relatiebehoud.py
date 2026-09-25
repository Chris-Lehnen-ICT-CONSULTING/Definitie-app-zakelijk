"""DEF-768 ronde 3: G behoudt gedeelde betekenisbepalende relaties.

Bevinding R2 (uitkomst-en-vervolg-v2.md, R2G4-run1 actueel): de bron verbindt
ieder object aan precies één verzameling en al zijn onderdelen aan diezelfde
verzameling. De actuele definitie noemde alleen de relatie van de onderdelen
("… uit één …") en liet de relatie van het object zelf weg. Het onderscheid met
de buren bleef correct, maar er ging betekenis verloren.

Herleide oorzaak: de ESS-05-generatie-instructie stuurt volledig op
onderscheidende kenmerken en zegt nergens dat een relatie die het begrip met
zijn buren deelt, blijft staan. Daardoor kan een gedeelde relatie wegvallen of
verschuiven naar een onderdeel.

Regressiebewaking R2G2 (basis run 1): de bevestigingsrelatie verschoof van de
vastlegging naar wat is vastgelegd; de actuele variant was juist. Die
relatiebehoudregels blijven staan.

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
from tests.unit.services.prompts.test_def768_r2_g_betekenisbehoud import (
    BRON_OMVANG,
    BRON_RELATIE,
    ESS05_GEEN_UITSLUITING,
    ESS05_RELATIE,
    KOP_GEEN_UITSLUITING,
)
from toetsregels.rule_cache import get_rule_cache

pytestmark = [pytest.mark.unit]

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts" / "ess05"))

import proefinvoer as pi

R2_G_INVOER = (
    ROOT / "reports" / "DEF-768-AI-20260924-R2" / "onafhankelijke-g-invoer-v1.json"
)
R2_ACTUEEL_SHA = "de78720c2c6cf5d0f3af14419d0dd4a1d66f9250e19e1bf2e203dadedb1f8914"

GEDEELD_BEHOUD = (
    "Laat een kenmerk of relatie die de bron aan het begrip zelf toekent niet weg "
    "omdat de verwante begrippen haar delen: behoud gedeelde betekenisbepalende "
    "relaties naast de onderscheidende kenmerken, zonder ze als onderscheid op te "
    "voeren"
)
GEEN_VERSCHUIVING = (
    "verschuif een relatie niet naar een ander object, zoals van het begrip naar "
    "een onderdeel of inhoud ervan, of van een vastlegging naar wat is vastgelegd"
)
#: R2-verbeteringen die intact moeten blijven.
BLIJVEND = (
    ESS05_RELATIE,
    ESS05_GEEN_UITSLUITING,
    BRON_RELATIE,
    BRON_OMVANG,
    KOP_GEEN_UITSLUITING,
)
GEVALSWOORDEN = (
    "pakket",
    "routecode",
    "routedossier",
    "dossier",
    "paraaf",
    "controleur",
    "wisselbewijs",
    "inschrijving",
    "plaat",
    "archief",
    "kravel",
    "ispeld",
)


@pytest.fixture(autouse=True)
def _verse_regelcache():
    get_rule_cache().clear_cache()


def _instructie() -> str:
    return JSONBasedRulesModule("ESS", "r3", "r3", "", "", 1)._get_instruction_for_rule(
        "ESS-05"
    )


def test_ess05_instructie_draagt_relatiebehoud_een_keer():
    tekst = _instructie()
    assert tekst.count(GEDEELD_BEHOUD) == 1
    assert tekst.count(GEEN_VERSCHUIVING) == 1


def test_g_actueel_instructie_is_gewijzigd():
    """De G-actuele variant verandert bewust; R2-bindingen gelden niet meer."""
    sha = hashlib.sha256(pi.huidige_g_instructie().encode("utf-8")).hexdigest()
    assert sha != R2_ACTUEEL_SHA


def test_geen_gevalswoorden_in_de_nieuwe_zinnen():
    for zin in (GEDEELD_BEHOUD, GEEN_VERSCHUIVING):
        for woord in GEVALSWOORDEN:
            assert woord not in zin.lower(), woord


def test_onderscheid_blijft_de_opdracht():
    """Geen algemene verschuiving: het onderscheidende kenmerk blijft vereist."""
    tekst = _instructie()
    assert tekst.startswith("Kies een bovenbegrip en toespitsende kenmerken")
    assert "de kern drukt per verwant begrip een onderbouwd verschil" in tekst


@pytest.mark.skipif(
    not R2_G_INVOER.is_file(), reason="git-ignored R2-G-invoer ontbreekt"
)
@pytest.mark.parametrize("gid", ["R2G4", "R2G2"])
def test_r2_diagnose_g_prompt_draagt_relatiebehoud_en_r2_verbeteringen(gid):
    data = json.loads(R2_G_INVOER.read_text(encoding="utf-8"))
    invoer = next(i for i in data["invoeren"] if i["id"] == gid)
    prompt = asyncio.run(pi.bouw_g_prompt(invoer))
    for zin in (GEDEELD_BEHOUD, GEEN_VERSCHUIVING, *BLIJVEND):
        assert prompt.count(zin) == 1, zin
    pi.controleer_promptlengte(gid, "actueel", prompt)
