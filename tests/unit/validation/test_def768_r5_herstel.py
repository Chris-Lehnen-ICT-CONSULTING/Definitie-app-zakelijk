"""DEF-768 R5 (/11): te toetsen kern, inhoudsindicator en samenhang van de reason.

Bevindingen R4-eindproef (reports/DEF-768-AI-20260924-R4/uitkomst-en-vervolg-v1.md):

- R4-E01: een kern die een bevestigde buur parafraseert, werd als onbeslisbare
  broncontradictie open gelaten. Herstel: de tegenstrijdigheidszin gaat over
  bronnen, buurbeschrijvingen en bedoelde betekenis onderling; de kern is wat
  je beoordeelt. Bewust smal: een afwijking tussen kern en bron maakt de kern
  op zichzelf niet onvoldoende onderscheidend (een bronfout kan buiten ESS-05
  liggen). Echte broncontradicties blijven unclear, zonder herkomstvoorrang.
- R4-E02: een verwijzing naar eigenschappen die de kern niet noemt, gold als
  inhoudelijk kenmerk. Herstel binnen de bestaande definitie en zelfcontrole;
  een echt, ook onjuist of gedeeld, kenmerk houdt de indicator false.
- R4-E03: een reason die zichzelf en de uitkomst tegensprak, en een voorgesteld
  ontbrekend kenmerk dat de betekenis ongegrond vernauwde. Herstel in de
  bestaande reasoncontrole; het ontbrekende kenmerk blijft benoemd en een niet
  onderscheiden buur wordt daardoor niet unclear.

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
from tests.unit.validation.test_def768_r6_herstel import KERN, REASONCONTROLE

pytestmark = [pytest.mark.unit]

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts" / "ess05"))

import proefinvoer as pi

R5_SELECTIE = ROOT / "reports" / "DEF-768-AI-20260925-R5" / "ontwikkelselectie-v1.json"
NORM_SHA = "af550b2cc5868a6dad6ed951d4fc867a86f1b16fa283181941ac355833ac93e4"

# --- E01 --------------------------------------------------------------------------
TEGENSTRIJDIG = (
    "Spreken bronnen, beschrijvingen van verwante begrippen of de bedoelde "
    "betekenis zichzelf of elkaar tegen op een punt dat de afgrenzing van een "
    "verwant begrip bepaalt, en blijkt uit het materiaal niet welke lezing geldt, "
    "dan is de uitkomst voor dat verwante begrip unclear: kies geen kant op grond "
    "van herkomst of soort bron, benoem de tegenstrijdigheid in uncertainty en "
    "stel er één vraag over; wat niet betwist is beoordeel je gewoon."
)
#: KERN en REASONCONTROLE: R6 (/12, R5-E01 en R5-E02) verlengt beide zinnen;
#: de volledige zinnen komen uit test_def768_r6_herstel.py (één bron).
# --- E02 --------------------------------------------------------------------------
INDICATOR = (
    "lacks_differentia gaat over de kern als geheel: true als de kern naast het "
    "bovenbegrip geen inhoudelijk kenmerk noemt, ook als er alleen waarderende of "
    "inhoudsloze woorden staan of een verwijzing naar eigenschappen die de kern "
    "niet noemt, zodat de kern geen enkel verwant begrip kan uitsluiten; false "
    "zodra de kern een inhoudelijk kenmerk noemt, ook als dat kenmerk onjuist is, "
    "met een verwant begrip gedeeld wordt of niets afgrenst;"
)
TRUE_TAK = (
    "stelt je reason dat de kern naast het bovenbegrip geen inhoudelijk kenmerk "
    "noemt, ook als er woorden of een verwijzing naar niet genoemde eigenschappen "
    "staan, dan is lacks_differentia true"
)
FALSE_TAK = (
    "noemt de kern een inhoudelijk kenmerk, ook een onjuist of gedeeld kenmerk dat "
    "niets afgrenst, dan is het false."
)
# --- E03: REASONCONTROLE, zie de import uit test_def768_r6_herstel.py ---------------
LACKS_CONTROLE = (
    "Controleer vóór je antwoordt of lacks_differentia overeenkomt met je eigen "
    "reason"
)
NIEUW = (TEGENSTRIJDIG, KERN, INDICATOR, TRUE_TAK, FALSE_TAK, REASONCONTROLE)
#: Vervangen /10-formuleringen.
OUD_R5 = (
    "Spreekt het aangeleverde materiaal zichzelf tegen",
    (
        "stelt je reason dat de kern naast het bovenbegrip alleen waarderende of "
        "inhoudsloze woorden noemt"
    ),
    "ook een gedeeld kenmerk dat niets afgrenst, dan is het false",
    "ook als dat kenmerk met een verwant begrip gedeeld wordt of niets afgrenst",
    "klopt dat niet, pas dan reason en uitkomst aan.",
)
#: Wat niet mag verschuiven: echte tegenstrijdigheid/leemte blijft unclear,
#: geen herkomstvoorrang, ontbrekend kenmerk benoemen, rol-overlap blijft.
BLIJVEND = (
    "kies geen kant op grond van herkomst of soort bron",
    (
        "vul die leemte dan niet aan met aangenomen gevallen van dat begrip, met of "
        "zonder het kenmerk: de uitkomst is dan unclear"
    ),
    "Zijn de gronden daarvoor onvoldoende, dan is de uitkomst unclear",
    (
        "not_distinguished: geen onderbouwd verschil; benoem in missing_feature het "
        "ontbrekende of te ruime kenmerk"
    ),
    (
        "Dat er naast het bovenbegrip woorden staan, maakt die woorden nog geen "
        "inhoudelijk kenmerk"
    ),
    "dat tekort meld je per verwant begrip als not_distinguished",
    "Overlap van gevallen tussen rollen of fasen",
    "Een persoon of object dat beide rollen vervult bewijst op zichzelf geen gebrek",
    "Een kenmerk dat ook het verwante begrip draagt",
    LACKS_CONTROLE,
)
#: Casuswoorden uit de R4-bevindingen; de R5-invoer levert de rest (data).
GEVALSWOORDEN = (
    "container",
    "specifiek",
    "zeef",
    "opening",
    "richting",
    "verplaats",
    "kist",
    "verzend",
    "deelnemer",
    "ritvolger",
    "ring",
    "trommel",
)


def _systeem(geval: dict) -> str:
    norm = laad_ess05_norm()
    prompt = pi.bouw_t_prompt(pi.modelprojectie(geval), norm)
    pi.controleer_afscherming(geval, prompt.teksten, norm)
    return prompt.teksten[0]


def _instructie(systeem: str) -> str:
    begin = systeem.index("Toetsinstructie:")
    return systeem[begin : systeem.index("Uitkomst per verwant begrip", begin)]


def _r5_gevallen() -> list[dict]:
    return json.loads(R5_SELECTIE.read_text(encoding="utf-8"))["gevallen"]


def test_versie_is_verhoogd():
    # /11 (R5): E01–E03 als gerichte vervanging van bestaande zinnen.
    # /14 (ADR-003): alleen het uitvoertemplate naar het gesloten concept
    # (`ess05-concept/1`); de toetsinstructie (T/13) blijft bytegelijk.
    # /15 (R8-offsetherstel): antwoord zonder posities; T/13 ongewijzigd.
    assert Ess05AssessmentService.PROMPT_VERSION == "ess05-assess/15"


def test_norm_blijft_ongewijzigd():
    assert normhash(laad_ess05_norm()) == NORM_SHA


def test_nieuwe_zinnen_elk_precies_eenmaal():
    systeem = _systeem(ZUSTER)
    for zin in NIEUW:
        assert systeem.count(zin) == 1, zin


def test_vervangen_formuleringen_zijn_weg():
    systeem = _systeem(ZUSTER)
    for oud in OUD_R5:
        assert oud not in systeem, oud


def test_bestaande_norm_en_gedrag_blijven():
    systeem = _systeem(ZUSTER)
    for zin in BLIJVEND:
        assert zin in systeem, zin


def test_e01_kern_volgt_direct_op_de_tegenstrijdigheidszin():
    instructie = _instructie(_systeem(ZUSTER))
    assert instructie.index(TEGENSTRIJDIG) + len(TEGENSTRIJDIG) + 1 == (
        instructie.index(KERN)
    )
    assert instructie.index(KERN) + len(KERN) + 1 == instructie.index(INDICATOR)


def test_e01_is_smal_geen_afwijking_bewijst_zelf_onvoldoende_onderscheid():
    """Niet elke afwijking tussen kern en bron is not_distinguished; alleen een
    vastgestelde parafrase van een bevestigde buur of aantoonbaar ontbrekende
    afgrenzing. De tegenstrijdigheid betreft het materiaal onderling, niet de kern."""
    assert "maakt de kern op zichzelf niet onvoldoende onderscheidend" in KERN
    assert "stelt je reason vast" in KERN
    assert "bevestigd verwant begrip" in KERN
    assert "aantoonbaar geen kenmerk" in KERN
    assert "kern" not in TEGENSTRIJDIG
    for te_breed in ("elke afwijking", "iedere afwijking", "wijkt de kern af"):
        assert te_breed not in KERN.lower()


def test_e02_verwijzing_zonder_kenmerk_is_true_en_echt_kenmerk_false():
    assert "een verwijzing naar eigenschappen die de kern niet noemt" in INDICATOR
    assert "ook als dat kenmerk onjuist is" in INDICATOR
    assert "met een verwant begrip gedeeld wordt" in INDICATOR
    systeem = _systeem(ZUSTER)
    # Beide takken van de zelfcontrole staan in één zin, na de definitie.
    assert systeem.index(INDICATOR) < systeem.index(LACKS_CONTROLE)
    assert systeem.index(LACKS_CONTROLE) < systeem.index(TRUE_TAK)
    assert systeem.index(TRUE_TAK) < systeem.index(FALSE_TAK)


def test_e03_reasoncontrole_direct_voor_de_indicatorcontrole():
    instructie = _instructie(_systeem(ZUSTER))
    assert instructie.index(REASONCONTROLE) + len(REASONCONTROLE) + 1 == (
        instructie.index(LACKS_CONTROLE)
    )
    assert instructie.count("Controleer vóór je antwoordt") == 2


def test_e03_ontbrekend_kenmerk_blijft_benoemd_en_fail_gaat_niet_open():
    assert "maakt de uitkomst niet unclear" in REASONCONTROLE
    assert "blijft binnen wat bron of bedoelde betekenis dragen" in REASONCONTROLE
    systeem = _systeem(ZUSTER)
    assert "benoem in missing_feature het ontbrekende of te ruime kenmerk" in systeem


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
        "altijd not_distinguished",
    ):
        assert verzachting not in instructie


@pytest.mark.skipif(not R5_SELECTIE.is_file(), reason="R5-ontwikkelselectie ontbreekt")
def test_geen_termen_uit_de_r5_ontwikkelinvoer_in_de_nieuwe_zinnen():
    termen = set()
    for geval in _r5_gevallen():
        termen.add(geval["begrip"].lower())
        termen.update(b["term"].lower() for b in geval.get("buren") or [])
    for zin in NIEUW:
        for term in termen:
            assert not re.search(rf"\b{re.escape(term)}\b", zin.lower()), (term, zin)


@pytest.mark.skipif(not R5_SELECTIE.is_file(), reason="R5-ontwikkelselectie ontbreekt")
def test_r5_ontwikkelgevallen_krijgen_de_herstelzinnen():
    gevallen = _r5_gevallen()
    assert len(gevallen) == 9
    for geval in gevallen:
        systeem = _systeem(geval)
        for zin in NIEUW:
            assert systeem.count(zin) == 1, (geval["id"], zin)
