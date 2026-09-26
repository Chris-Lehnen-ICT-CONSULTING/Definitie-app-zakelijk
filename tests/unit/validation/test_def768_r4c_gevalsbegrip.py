"""DEF-768 R4-ontwikkelcorrectie (/9): gevalsbegrip en zelfcontrole van de reason.

Bevindingen R4-ontwikkeling (coördinator, na technische review akkoord):

1. R308 — de reason noemt een gedeelde situatie (twee objectsoorten die
   dezelfde handeling kunnen ondergaan) nog steeds toegestane overlap.
   Oorzaak: het /8-voorbeeld "een handeling die aan beide beschrijvingen
   voldoet" maakte een handeling tot geval, ook als de begrippen geen
   handelingen aanduiden; de latere zinnen gebruiken "gevallen" en "overlap"
   zonder die grens. Herstel: "geval" één keer omschrijven als exemplaar van
   wat de begrippen aanduiden, bij de bestaande definitiezin.
2. R313 (eerste poging) — de reason ontkent een expliciet bronfeit: dat het
   materiaal geen gevallen van de buur beschrijft die onder de kern maar niet
   onder dit begrip vallen, terwijl de bron zulke gevallen via een combinatie
   van uitspraken vastlegt. Herstel: de bestaande "geen leemte"-zin preciseert
   wat "beschrijft" omvat, en de bestaande zelfcontrole toetst de volledige
   reason tegen het materiaal.

R313-D2/D3 en R302 (echte rol-overlap) waren goed en blijven beschermd.
Constructiebewijs op de echte prompt; geen claim over modeluitkomsten.
Norm, beslisvolgorde, parser en schema blijven ongewijzigd.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

from services.validation.ai_beoordeling_transport import normhash
from services.validation.ess05_assessment_service import (
    Ess05AssessmentService,
    laad_ess05_norm,
)
from tests.unit.validation.test_def768_r3_voorstelgrond import ZUSTER
from tests.unit.validation.test_def768_r6_herstel import GEEN_LEEMTE, REASONCONTROLE

pytestmark = [pytest.mark.unit]

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts" / "ess05"))

import proefinvoer as pi

R4_SELECTIE = ROOT / "reports" / "DEF-768-AI-20260924-R4" / "ontwikkelselectie-v1.json"

# --- 1. geval en gedeeld geval ---------------------------------------------------
GEVAL = (
    "Een geval is één exemplaar van wat de begrippen aanduiden, en een gedeeld "
    "geval is één zo'n exemplaar dat onder beide begrippen valt, zoals een persoon "
    "met beide rollen of, bij begrippen voor handelingen, één handeling die aan "
    "beide beschrijvingen voldoet; dat exemplaren van beide begrippen in dezelfde "
    "situatie, handeling of gebeurtenis voorkomen of dezelfde handeling ondergaan, "
    "maakt op zichzelf geen gedeeld geval en geen overlap: zo'n omvattende "
    "situatie, handeling of gebeurtenis is alleen zelf een gedeeld geval als haar "
    "eigen kenmerken of de bron haar als exemplaar van beide begrippen dragen."
)
#: /9-formulering die elke omvattende handeling uitsloot (R4-OC-01).
ABSOLUUT_R4C = "is zelf geen geval van die begrippen"
OVERLAP_CRITERIA = "dat één geval beide criteria kan hebben, is overlap."
# --- 2. beschreven gevallen en zelfcontrole ---------------------------------------
#: GEEN_LEEMTE en REASONCONTROLE: R6 (/12, R5-E01 en R5-E02) verlengt beide
#: zinnen; het R4c-begin blijft letterlijk staan. De volledige zinnen komen uit
#: tests/unit/validation/test_def768_r6_herstel.py (één bron, zie de import).
LACKS_CONTROLE = (
    "Controleer vóór je antwoordt of lacks_differentia overeenkomt met je eigen "
    "reason"
)
NIEUW = (GEVAL, OVERLAP_CRITERIA, GEEN_LEEMTE, REASONCONTROLE)
#: Vervangen /8-formuleringen.
OUD_R4 = (
    "Een gedeeld geval is één exemplaar dat onder beide begrippen valt",
    "maakt nog geen gedeeld geval",
    "dat gevallen beide kunnen hebben is overlap",
    "Gevallen die het materiaal wel zo beschrijft, zijn geen leemte",
    ABSOLUUT_R4C,
)
#: Bestaande norm en gedrag blijven (rol-/fase-overlap, leemte, voorstellen).
BLIJVEND = (
    "gedeelde gevallen mogen",
    "Overlap van gevallen tussen rollen of fasen",
    "Een persoon of object dat beide rollen vervult bewijst op zichzelf geen gebrek",
    "verzin geen tegenvoorbeeld of betekenis",
    (
        "je hoeft niet aan te tonen dat gevallen van het verwante begrip het kenmerk "
        "van de kern missen"
    ),
    (
        "en beschrijft het materiaal geen gevallen van dat begrip die onder de kern "
        "maar niet onder dit begrip vallen, vul die leemte dan niet aan"
    ),
    (
        "vul die leemte dan niet aan met aangenomen gevallen van dat begrip, met of "
        "zonder het kenmerk: de uitkomst is dan unclear"
    ),
    (
        "Dat gedeelde gevallen mogen, rechtvaardigt geen aangenomen gevallen van het "
        "verwante begrip"
    ),
    "Verwarring of gedeelde gevallen moeten uit het materiaal blijken",
    "Geen voorstel is beter dan een ongegrond voorstel",
    LACKS_CONTROLE,
)
GEVALSWOORDEN = (
    "koppeling",
    "losmak",
    "toevoer",
    "pakket",
    "tril",
    "vloeistof",
    "nat",
    "droog",
    "verzegel",
    "klank",
    "toon",
    "deelnemer",
    "istravel",
    "tervulo",
    "velmora",
)
NORM_SHA = "af550b2cc5868a6dad6ed951d4fc867a86f1b16fa283181941ac355833ac93e4"


def _systeem(geval: dict) -> str:
    norm = laad_ess05_norm()
    prompt = pi.bouw_t_prompt(pi.modelprojectie(geval), norm)
    pi.controleer_afscherming(geval, prompt.teksten, norm)
    return prompt.teksten[0]


def _instructie(systeem: str) -> str:
    begin = systeem.index("Toetsinstructie:")
    return systeem[begin : systeem.index("Uitkomst per verwant begrip", begin)]


def test_versie_is_verhoogd():
    # /10 (R4-OC-01) maakt de uitsluiting uit /9 voorwaardelijk; /11 (R5) laat
    # het gevalsbegrip intact.
    # /14 (ADR-003): alleen het uitvoertemplate naar het gesloten concept
    # (`ess05-concept/1`); de toetsinstructie (T/13) blijft bytegelijk.
    # /15 (R8-offsetherstel): antwoord zonder posities; T/13 ongewijzigd.
    # assess/16 + verify/3 (R9-bewijsherstel): deelzin per bewijsroute; T/13 gelijk.
    # assess/17 + verify/4 (R10-C3): gesloten bewijsroute per claim; T/13 gelijk.
    # assess/18 (answer/2): genest, citaat-eerst antwoord; T/13 gelijk.
    assert Ess05AssessmentService.PROMPT_VERSION == "ess05-assess/18"


def test_norm_blijft_ongewijzigd():
    assert normhash(laad_ess05_norm()) == NORM_SHA


def test_nieuwe_zinnen_elk_precies_eenmaal():
    systeem = _systeem(ZUSTER)
    for zin in NIEUW:
        assert systeem.count(zin) == 1, zin


def test_vervangen_formuleringen_zijn_weg():
    systeem = _systeem(ZUSTER)
    for oud in OUD_R4:
        assert oud not in systeem, oud


def test_bestaande_norm_en_gedrag_blijven():
    systeem = _systeem(ZUSTER)
    for zin in BLIJVEND:
        assert zin in systeem, zin


def test_geval_omschreven_voor_elk_later_gebruik_van_gevallen_en_overlap():
    """Eén omschrijving, direct bij de eerste vermelding; alle latere zinnen
    over gevallen en overlap lezen haar dus mee (geen tweede definitie)."""
    instructie = _instructie(_systeem(ZUSTER))
    eerste = instructie.index("gedeelde gevallen mogen")
    assert instructie.index(GEVAL) == eerste + len("gedeelde gevallen mogen. ")
    na = instructie[instructie.index(GEVAL) + len(GEVAL) :]
    assert "Een geval is" not in na
    assert "gedeeld geval is" not in na
    for gebruik in ("overlap", "gevallen"):
        assert instructie.index(gebruik, eerste + 1) > instructie.index(GEVAL) or (
            instructie.index(gebruik) < eerste
        )


def test_samen_voorkomen_bewijst_geen_overlap_maar_sluit_niets_uit():
    """R308 blijft: samen voorkomen of dezelfde handeling ondergaan bewijst op
    zichzelf geen overlap. R4-OC-01: een omvattende handeling is niet absoluut
    uitgesloten; ze is een gedeeld geval als haar eigen kenmerken of de bron dat
    dragen."""
    assert "bij begrippen voor handelingen, één handeling" in GEVAL
    assert "maakt op zichzelf geen gedeeld geval en geen overlap" in GEVAL
    assert "alleen zelf een gedeeld geval als haar eigen kenmerken of de bron" in GEVAL
    assert ABSOLUUT_R4C not in GEVAL
    # Echte rol-overlap blijft het eerste voorbeeld.
    assert GEVAL.index("een persoon met beide rollen") < GEVAL.index("handeling")


def test_reasoncontrole_direct_voor_de_bestaande_controle():
    instructie = _instructie(_systeem(ZUSTER))
    assert instructie.index(REASONCONTROLE) + len(REASONCONTROLE) + 1 == (
        instructie.index(LACKS_CONTROLE)
    )
    assert instructie.count("Controleer vóór je antwoordt") == 2


def test_leemteclausule_blijft_een_zin_en_gaat_voor_de_geen_leemtezin():
    systeem = _systeem(ZUSTER)
    begin = systeem.index("Laat het materiaal echter open")
    eind = systeem.index("de uitkomst is dan unclear.", begin)
    assert "." not in systeem[begin:eind]
    assert systeem.index(GEEN_LEEMTE) == eind + len("de uitkomst is dan unclear. ")


def test_instructie_zonder_gevalswoorden():
    for zin in NIEUW:
        for woord in GEVALSWOORDEN:
            assert not re.search(rf"\b{woord}", zin.lower()), (woord, zin)


def test_geen_verzachting_of_nieuwe_uitkomstroute():
    instructie = _instructie(_systeem(ZUSTER)).lower()
    for verzachting in (
        "bij twijfel distinguished",
        "bij twijfel not_distinguished",
        "altijd unclear",
        "nooit unclear",
    ):
        assert verzachting not in instructie


@pytest.mark.skipif(not R4_SELECTIE.is_file(), reason="R4-ontwikkelselectie ontbreekt")
@pytest.mark.parametrize("gid", ["R308", "R313", "R313-D2", "R313-D3", "R302"])
def test_r4_ontwikkelgevallen_krijgen_de_preciseringen(gid):
    gevallen = json.loads(R4_SELECTIE.read_text(encoding="utf-8"))["gevallen"]
    systeem = _systeem(next(g for g in gevallen if g["id"] == gid))
    for zin in NIEUW:
        assert zin in systeem, zin
