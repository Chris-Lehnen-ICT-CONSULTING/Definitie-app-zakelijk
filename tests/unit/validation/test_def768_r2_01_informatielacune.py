"""DEF-768 R2-01: ontbrekende informatie is geen ontkenning én geen bewijseis.

Review ronde 2 (logs/def768/ronde2-review-result-v1.md, R2-01): de /4-zin
"Een kenmerk grenst alleen af als bron of beschrijving aangeeft dat gevallen
van het verwante begrip het niet hebben" maakte bewijs van afwezigheid algemeen
verplicht. Dat botst met K-3b en het vastgelegde ESS05-E05 (lener/werknemer:
verschillende gedragen rolcriteria, geen informatie over werknemers zonder
lening nodig). De R1-les (E14-klasse) blijft: een leemte in het materiaal over
de buur vul je niet aan met aangenomen gevallen.

Constructiebewijs op de echte prompt (via de proefprojectie, zonder
modelantwoord): de conflicterende eis staat er niet meer in, de leemteclausule
wel, en de instructie noemt geen gevalswoorden. Of het model E05 en de
E14-klasse nu goed beoordeelt, bewijst dit niet; dat blijft de geautoriseerde
ontwikkelronde.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

from services.validation.ess05_assessment_service import (
    Ess05AssessmentService,
    laad_ess05_norm,
)

pytestmark = [pytest.mark.unit]

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts" / "ess05"))

import proefinvoer as pi

ONTWIKKEL = ROOT / "tests" / "fixtures" / "ess05" / "ontwikkelgevallen_v1.json"
SELECTIE = ROOT / "reports" / "DEF-768-AI-20260924-R2" / "ontwikkelselectie-v1.json"

#: De gewraakte /4-eis (algemeen afwezigheidsbewijs).
OUDE_EIS = (
    "Een kenmerk grenst alleen af als bron of beschrijving aangeeft dat gevallen "
    "van het verwante begrip het niet hebben"
)
GEEN_ONTKENNING = "Ontbrekende informatie over een verwant begrip is geen ontkenning"
GEEN_BEWIJSEIS = (
    "je hoeft niet aan te tonen dat gevallen van het verwante begrip het kenmerk "
    "van de kern missen"
)
CRITERIA = (
    "Berust dat begrip volgens beschrijving of bron op een eigen, onderbouwd "
    "criterium en de kern op een ander onderbouwd criterium, dan beoordeel je het "
    "verschil tussen die criteria"
)
LEEMTE = (
    "vul die leemte dan niet aan met aangenomen gevallen van dat begrip, met of "
    "zonder het kenmerk: de uitkomst is dan unclear"
)
LEEMTE_AANLEIDING = (
    "omdat het aangeeft dat over dat begrip op dat punt niets of alleen een beperkt "
    "gegeven is vastgelegd"
)
GEEN_AANNAME = "rechtvaardigt geen aangenomen gevallen van het verwante begrip"
#: Bestaande normzinnen die blijven (K-3b; geen automatische pass).
BLIJVEND = (
    "Een ander woord of een ander kenmerk alleen bewijst nog geen afgrenzing",
    "gedeelde gevallen mogen",
    "Een persoon of object dat beide rollen vervult bewijst op zichzelf geen gebrek",
)

#: Een synthetisch geval van de E14-klasse: de bron legt van de buur uitdrukkelijk
#: alleen een ander gegeven vast (geen R1-eindgeval, geen heldout).
E14_KLASSE = {
    "id": "R2-01-leemte",
    "begrip": "herstelkrat",
    "tekst": "krat voor beschadigde stukken.",
    "toelichting": "Het krat bevat beschadigde stukken die terugkomen.",
    "categorie": None,
    "context": {
        "organisatorische_context": ["Synthetische magazijnafspraak Tolm"],
        "juridische_context": [],
        "wettelijke_basis": [],
    },
    "bronnen": [
        {
            "provider": "documents",
            "doc_id": "synthetisch-r201",
            "title": "Synthetische afspraak Tolm-kratten",
            "snippet": (
                "Tolm gebruikt een herstelkrat voor beschadigde stukken. Voor het "
                "doorgeefkrat is in deze afspraak uitsluitend de bestemming "
                "vastgelegd: de laadperron."
            ),
        }
    ],
    "buren": [
        {
            "term": "doorgeefkrat",
            "definitie": "krat voor stukken die naar de laadperron gaan.",
            "herkomst": "gebruiker",
            "bevestigd": True,
        }
    ],
    "verwacht": "open",
    "verwacht_per_buur": {"doorgeefkrat": "unclear"},
    "grond": "Synthetisch R2-01-constructiegeval; geen modeluitkomst geclaimd.",
}


def _prompt(geval: dict) -> tuple[str, str]:
    norm = laad_ess05_norm()
    prompt = pi.bouw_t_prompt(pi.modelprojectie(geval), norm)
    pi.controleer_afscherming(geval, prompt.teksten, norm)
    return prompt.teksten


def _e05() -> dict:
    gevallen = json.loads(ONTWIKKEL.read_text(encoding="utf-8"))["gevallen"]
    return next(g for g in gevallen if g["id"] == "ESS05-E05")


def test_versie_is_verhoogd_na_r2_01():
    # /5 was R2-01; /6 t/m /8 laten de R2-01-tekst intact.
    # /14 (ADR-003): alleen het uitvoertemplate naar het gesloten concept
    # (`ess05-concept/1`); de toetsinstructie (T/13) blijft bytegelijk.
    # /15 (R8-offsetherstel): antwoord zonder posities; T/13 ongewijzigd.
    # assess/16 + verify/3 (R9-bewijsherstel): deelzin per bewijsroute; T/13 gelijk.
    # assess/17 + verify/4 (R10-C3): gesloten bewijsroute per claim; T/13 gelijk.
    assert Ess05AssessmentService.PROMPT_VERSION == "ess05-assess/17"


def test_echte_e05_prompt_eist_geen_afwezigheidsbewijs():
    systeem, gebruiker = _prompt(_e05())
    assert OUDE_EIS not in systeem
    assert not re.search(r"grenst alleen af als", systeem)
    for zin in (GEEN_ONTKENNING, GEEN_BEWIJSEIS, CRITERIA, *BLIJVEND):
        assert zin in systeem, zin
    # Het materiaal draagt beide criteria; niets over werknemers zonder lening.
    assert "Persoon met een arbeidsovereenkomst met de instelling." in gebruiker
    assert "Persoon met een actuele lening bij de instelling." in gebruiker
    assert "zonder lening" not in gebruiker


def test_echte_prompt_van_de_e14_klasse_draagt_de_leemteclausule():
    systeem, gebruiker = _prompt(E14_KLASSE)
    for zin in (GEEN_ONTKENNING, LEEMTE_AANLEIDING, LEEMTE, GEEN_AANNAME):
        assert zin in systeem, zin
    assert "uitsluitend de bestemming vastgelegd" in gebruiker
    assert OUDE_EIS not in systeem


def test_instructie_zonder_gevalswoorden():
    systeem, _ = _prompt(_e05())
    instructie = systeem[: systeem.index(GEEN_AANNAME) + len(GEEN_AANNAME)].lower()
    instructie = instructie[instructie.index(GEEN_ONTKENNING.lower()) :]
    for woord in (
        "lener",
        "lening",
        "werknemer",
        "arbeidsovereenkomst",
        "wisselbak",
        "keuring",
        "afgekeurd",
        "verzending",
        "koppelstation",
        "retourbak",
        "herstelkrat",
        "doorgeefkrat",
    ):
        assert woord not in instructie, woord


@pytest.mark.skipif(not SELECTIE.is_file(), reason="git-ignored R2-selectie ontbreekt")
def test_selectie_e05_krijgt_dezelfde_instructie():
    """Het oude eindgeval E05 uit de R2-selectie: zelfde instructie, geen oude eis."""
    gevallen = json.loads(SELECTIE.read_text(encoding="utf-8"))["gevallen"]
    systeem, _ = _prompt(next(g for g in gevallen if g["id"] == "E05"))
    assert OUDE_EIS not in systeem
    assert GEEN_BEWIJSEIS in systeem
