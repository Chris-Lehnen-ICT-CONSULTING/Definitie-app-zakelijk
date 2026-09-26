"""DEF-768 R2-ontwikkelcorrectie: lacks_differentia consistent met de eigen reden.

Ontwikkelronde R2 (reports/DEF-768-AI-20260924-R2/ontwikkeling-inhoud-v1.md,
E10): de reden stelde dat naast het bovenbegrip alleen waarderende woorden
staan, maar lacks_differentia was false ("maar dat zijn wel woorden"). Binnen de
bestaande norm: de aanwezigheid van woorden is geen inhoudelijk kenmerk, en
boolean en eigen reden mogen elkaar niet tegenspreken. Een echt maar gedeeld
kenmerk houdt de indicator false (geen nieuwe eis).

Constructiebewijs op de echte prompt (proefprojectie, geen modelantwoord); of
het model de indicator nu goed zet, bewijst dit niet. Geen parser- of
validatorwijziging: de consistentie wordt niet in code geraden.
"""

from __future__ import annotations

import json
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

SELECTIE = ROOT / "reports" / "DEF-768-AI-20260924-R2" / "ontwikkelselectie-v1.json"

WOORDEN_GEEN_KENMERK = (
    "Dat er naast het bovenbegrip woorden staan, maakt die woorden nog geen "
    "inhoudelijk kenmerk"
)
ZELFCONTROLE = (
    "Controleer vóór je antwoordt of lacks_differentia overeenkomt met je eigen "
    "reason"
)
#: R5 (/11, R4-E02): de takken dekken ook een verwijzing naar niet genoemde
#: eigenschappen (true) en een onjuist kenmerk (false); de consistentie blijft.
TRUE_TAK = (
    "stelt je reason dat de kern naast het bovenbegrip geen inhoudelijk kenmerk "
    "noemt, ook als er woorden of een verwijzing naar niet genoemde eigenschappen "
    "staan, dan is lacks_differentia true"
)
FALSE_TAK = (
    "noemt de kern een inhoudelijk kenmerk, ook een onjuist of gedeeld kenmerk dat "
    "niets afgrenst, dan is het false"
)
#: Bestaande definitie blijft (geen nieuwe eis voor gedeelde kenmerken).
BESTAAND = (
    "lacks_differentia gaat over de kern als geheel",
    (
        "false zodra de kern een inhoudelijk kenmerk noemt, ook als dat kenmerk "
        "onjuist is, met een verwant begrip gedeeld wordt of niets afgrenst"
    ),
    "dat tekort meld je per verwant begrip als not_distinguished",
)
#: R2-01 blijft intact.
R2_01 = (
    (
        "je hoeft niet aan te tonen dat gevallen van het verwante begrip het kenmerk "
        "van de kern missen"
    ),
    "vul die leemte dan niet aan met aangenomen gevallen van dat begrip",
)

#: Synthetisch geval van de E10-klasse (geen R1/R2-eindgeval, geen heldout).
WAARDEREND = {
    "id": "R2-OC-waarderend",
    "begrip": "hoofdmonster",
    "tekst": "monster met een eigen, duidelijk en passend karakter.",
    "toelichting": None,
    "categorie": None,
    "context": {
        "organisatorische_context": ["Synthetisch laboratorium Brem"],
        "juridische_context": [],
        "wettelijke_basis": [],
    },
    "bronnen": [],
    "buren": [
        {
            "term": "reservemonster",
            "definitie": "monster dat apart wordt bewaard voor herhaling.",
            "herkomst": "gebruiker",
            "bevestigd": True,
        }
    ],
    "verwacht": "fail",
    "verwacht_per_buur": {"reservemonster": "not_distinguished"},
    "grond": "Synthetisch constructiegeval; geen modeluitkomst geclaimd.",
}


def _systeem(geval: dict) -> str:
    norm = laad_ess05_norm()
    prompt = pi.bouw_t_prompt(pi.modelprojectie(geval), norm)
    pi.controleer_afscherming(geval, prompt.teksten, norm)
    return prompt.teksten[0]


def test_versie_is_verhoogd():
    # /6 bracht de indicatorconsistentie; /7 t/m /10 laten die intact; /11
    # verbreedt de takken (R4-E02).
    # /14 (ADR-003): alleen het uitvoertemplate naar het gesloten concept
    # (`ess05-concept/1`); de toetsinstructie (T/13) blijft bytegelijk.
    # /15 (R8-offsetherstel): antwoord zonder posities; T/13 ongewijzigd.
    # assess/16 + verify/3 (R9-bewijsherstel): deelzin per bewijsroute; T/13 gelijk.
    # assess/17 + verify/4 (R10-C3): gesloten bewijsroute per claim; T/13 gelijk.
    # assess/18 (answer/2): genest, citaat-eerst antwoord; T/13 gelijk.
    assert Ess05AssessmentService.PROMPT_VERSION == "ess05-assess/18"


def test_echte_prompt_draagt_indicatorconsistentie():
    systeem = _systeem(WAARDEREND)
    for zin in (WOORDEN_GEEN_KENMERK, ZELFCONTROLE, TRUE_TAK, FALSE_TAK):
        assert systeem.count(zin) == 1, zin


def test_bestaande_definitie_en_r2_01_blijven():
    systeem = _systeem(WAARDEREND)
    for zin in (*BESTAAND, *R2_01):
        assert zin in systeem, zin
    # De zelfcontrole staat ná de definitie van de indicator.
    assert systeem.index(BESTAAND[0]) < systeem.index(ZELFCONTROLE)


def test_geen_gevalswoorden():
    systeem = _systeem(WAARDEREND).lower()
    blok = systeem[systeem.index(WOORDEN_GEEN_KENMERK.lower()) :]
    blok = blok[: blok.index(FALSE_TAK.lower()) + len(FALSE_TAK)]
    for woord in (
        "dubbelbewijs",
        "enkelbewijs",
        "bewijsstuk",
        "controlestation",
        "wel woorden",
        "hoofdmonster",
    ):
        assert woord not in blok, woord


@pytest.mark.skipif(not SELECTIE.is_file(), reason="git-ignored R2-selectie ontbreekt")
def test_selectie_e10_krijgt_de_zelfcontrole():
    gevallen = json.loads(SELECTIE.read_text(encoding="utf-8"))["gevallen"]
    systeem = _systeem(next(g for g in gevallen if g["id"] == "E10"))
    assert ZELFCONTROLE in systeem
    assert TRUE_TAK in systeem
