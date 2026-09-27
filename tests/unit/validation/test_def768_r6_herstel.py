"""DEF-768 R6 (/12): beschreven buurgeval onder de kern, en ontkende kenmerken.

Bevindingen R5-eindproef (reports/DEF-768-AI-20260925-R5/uitkomst-en-vervolg-v1.md):

- R5-E01: de kern sloot één beschreven buurvariant uit, maar omvatte een andere
  die volgens de bron buiten het doelbegrip valt; het antwoord noemde dat een
  "afwijking tussen kern en bron" en keurde goed. Herstel: zo'n door het
  materiaal beschreven buurgeval onder de kern bewijst ontbrekende afgrenzing,
  ook als andere gevallen van die buur wel worden uitgesloten; de
  kern-bronbescherming wordt daartoe beperkt. Gedeelde gevallen (die ook onder
  dit begrip vallen), leemtes en broncontradicties blijven zoals ze waren;
  geen aangenomen tegengevallen, geen universele uitsluiting.
- R5-E02: de reason ontkende dat een werkelijk afgrenzend kenmerk van de kern
  onderscheidt. Herstel in de bestaande reasoncontrole; geen eis alle
  kenmerken te noemen of te citeren. De oorzaak is niet aangetoond.

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
from tests.unit.validation.test_def768_r7_herstel import REASONCONTROLE

pytestmark = [pytest.mark.unit]

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts" / "ess05"))

import proefinvoer as pi

R6_SELECTIE = ROOT / "reports" / "DEF-768-AI-20260925-R6" / "ontwikkelselectie-v1.json"
NORM_SHA = "af550b2cc5868a6dad6ed951d4fc867a86f1b16fa283181941ac355833ac93e4"

# --- E01 --------------------------------------------------------------------------
#: De bestaande "geen leemte"-zin (R4c) blijft; R6 verlengt haar met de gevolgtrekking.
GEEN_LEEMTE_BEGIN = (
    "Gevallen die het materiaal wel zo beschrijft, ook door vast te leggen dat er "
    "gevallen van dat begrip zijn die tegelijk onder een ander begrip vallen dat "
    "volgens het materiaal buiten dit begrip valt, zijn geen leemte en geen "
    "aangenomen gevallen: beoordeel ze, ook als het materiaal daarnaast overlap "
    "noemt of het verwante begrip onbevestigd is"
)
BESCHREVEN_GEVAL = (
    "; valt zo'n door het materiaal beschreven geval van het verwante begrip "
    "buiten dit begrip maar wel onder de kern, dan grenst de kern dat verwante "
    "begrip niet af, ook als zij andere gevallen ervan wel uitsluit, en benoem je "
    "in missing_feature het kenmerk dat bron of bedoelde betekenis daarvoor "
    "dragen; gevallen die ook onder dit begrip vallen, blijven toegestane overlap."
)
GEEN_LEEMTE = GEEN_LEEMTE_BEGIN + BESCHREVEN_GEVAL
KERN = (
    "Een afwijking tussen de te toetsen kern en een bron, een beschrijving of de "
    "bedoelde betekenis is geen tegenstrijdigheid in het materiaal: de kern is wat "
    "je beoordeelt, geen lezing waartussen je kiest; zo'n afwijking maakt de kern "
    "op zichzelf niet onvoldoende onderscheidend, maar omvat de kern daardoor een "
    "door het materiaal beschreven geval van een verwant begrip dat buiten dit "
    "begrip valt, stelt je reason vast dat de kern hetzelfde uitdrukt als de "
    "beschrijving van een bevestigd verwant begrip, of heeft de kern aantoonbaar "
    "geen kenmerk dat gevallen van dat begrip afgrenst, dan is de uitkomst voor "
    "dat begrip not_distinguished."
)
# --- E02 --------------------------------------------------------------------------
#: REASONCONTROLE: R7 (/13, R6-E01) verbreedt het betekenisbehoud in deze zin; de
#: volledige zin komt uit test_def768_r7_herstel.py (één bron, zie de import). De
#: E02-delen blijven hieronder letterlijk getoetst.
LACKS_CONTROLE = (
    "Controleer vóór je antwoordt of lacks_differentia overeenkomt met je eigen "
    "reason"
)
NIEUW = (GEEN_LEEMTE, KERN, REASONCONTROLE)
#: Vervangen /11-formuleringen.
OUD_R6 = (
    "noemt of het verwante begrip onbevestigd is. Dat gedeelde gevallen",
    "op zichzelf niet onvoldoende onderscheidend, maar stelt je reason vast",
    "ook niet uit twee uitspraken samen; je reason mag zichzelf",
)
#: Behoud: echte overlap, leemte, broncontradictie, kernparafrase, echte
#: gedeelde kenmerken, ontbrekend kenmerk zonder vernauwing.
BLIJVEND = (
    "gedeelde gevallen mogen",
    "Een geval is één exemplaar van wat de begrippen aanduiden",
    "maakt op zichzelf geen gedeeld geval en geen overlap",
    "Overlap van gevallen tussen rollen of fasen",
    "Een persoon of object dat beide rollen vervult bewijst op zichzelf geen gebrek",
    "verzin geen tegenvoorbeeld of betekenis",
    (
        "je hoeft niet aan te tonen dat gevallen van het verwante begrip het kenmerk "
        "van de kern missen"
    ),
    (
        "vul die leemte dan niet aan met aangenomen gevallen van dat begrip, met of "
        "zonder het kenmerk: de uitkomst is dan unclear"
    ),
    (
        "Dat gedeelde gevallen mogen, rechtvaardigt geen aangenomen gevallen van het "
        "verwante begrip"
    ),
    "kies geen kant op grond van herkomst of soort bron",
    (
        "Spreken bronnen, beschrijvingen van verwante begrippen of de bedoelde "
        "betekenis zichzelf of elkaar tegen"
    ),
    (
        "stelt je reason vast dat de kern hetzelfde uitdrukt als de beschrijving van "
        "een bevestigd verwant begrip"
    ),
    "Een kenmerk dat ook het verwante begrip draagt",
    (
        "ook als dat kenmerk onjuist is, met een verwant begrip gedeeld wordt of "
        "niets afgrenst"
    ),
    (
        "noemt de kern een inhoudelijk kenmerk, ook een onjuist of gedeeld kenmerk dat "
        "niets afgrenst, dan is het false."
    ),
    (
        "not_distinguished: geen onderbouwd verschil; benoem in missing_feature het "
        "ontbrekende of te ruime kenmerk"
    ),
    LACKS_CONTROLE,
)
GEVALSWOORDEN = (
    "pekel",
    "helderwater",
    "spoel",
    "tel",
    "vat",
    "kaart",
    "middelpunt",
    "omtrek",
    "duur",
    "zes",
    "twee tellen",
)


def _systeem(geval: dict) -> str:
    norm = laad_ess05_norm()
    prompt = pi.bouw_t_prompt(pi.modelprojectie(geval), norm)
    pi.controleer_afscherming(geval, prompt.teksten, norm)
    return prompt.teksten[0]


def _instructie(systeem: str) -> str:
    begin = systeem.index("Toetsinstructie:")
    return systeem[begin : systeem.index("Uitkomst per verwant begrip", begin)]


def _r6_gevallen() -> list[dict]:
    return json.loads(R6_SELECTIE.read_text(encoding="utf-8"))["gevallen"]


def test_versie_is_verhoogd():
    # /12 (R6): R5-E01 en R5-E02 als gerichte vervanging van bestaande zinnen.
    # /14 (ADR-003): alleen het uitvoertemplate naar het gesloten concept
    # (`ess05-concept/1`); de toetsinstructie (T/13) blijft bytegelijk.
    # /15 (R8-offsetherstel): antwoord zonder posities; T/13 ongewijzigd.
    # assess/16 + verify/3 (R9-bewijsherstel): deelzin per bewijsroute; T/13 gelijk.
    # assess/17 + verify/4 (R10-C3): gesloten bewijsroute per claim; T/13 gelijk.
    # assess/18 (answer/2): genest, citaat-eerst antwoord; T/13 gelijk.
    assert Ess05AssessmentService.PROMPT_VERSION == "ess05-assess/19"


def test_norm_blijft_ongewijzigd():
    assert normhash(laad_ess05_norm()) == NORM_SHA


def test_nieuwe_zinnen_elk_precies_eenmaal():
    systeem = _systeem(ZUSTER)
    for zin in NIEUW:
        assert systeem.count(zin) == 1, zin


def test_vervangen_formuleringen_zijn_weg():
    systeem = _systeem(ZUSTER)
    for oud in OUD_R6:
        assert oud not in systeem, oud


def test_bestaande_norm_en_gedrag_blijven():
    systeem = _systeem(ZUSTER)
    for zin in BLIJVEND:
        assert zin in systeem, zin


def test_e01_alleen_beschreven_gevallen_buiten_dit_begrip():
    """Smal: het materiaal moet het buurgeval beschrijven, het valt buiten dit
    begrip én onder de kern; gedeelde gevallen blijven overlap. Geen universele
    uitsluiting en geen aangenomen gevallen."""
    for tekst in (BESCHREVEN_GEVAL, KERN):
        assert "door het materiaal beschreven geval" in tekst
        assert "buiten dit begrip" in tekst
    assert "maar wel onder de kern" in BESCHREVEN_GEVAL
    assert "ook als zij andere gevallen ervan wel uitsluit" in BESCHREVEN_GEVAL
    assert "gevallen die ook onder dit begrip vallen, blijven toegestane overlap" in (
        BESCHREVEN_GEVAL
    )
    for te_breed in (
        "elke afwijking",
        "iedere afwijking",
        "alle gevallen",
        "elk geval",
        "altijd not_distinguished",
        "denkbaar",
    ):
        for tekst in (BESCHREVEN_GEVAL, KERN):
            assert te_breed not in tekst.lower(), te_breed
    # De kern-bronbescherming blijft voor afwijkingen zonder zo'n geval.
    assert "maakt de kern op zichzelf niet onvoldoende onderscheidend" in KERN


def test_e01_volgt_direct_op_de_leemteclausule():
    systeem = _systeem(ZUSTER)
    begin = systeem.index("Laat het materiaal echter open")
    eind = systeem.index("de uitkomst is dan unclear.", begin)
    assert systeem.index(GEEN_LEEMTE) == eind + len("de uitkomst is dan unclear. ")


def test_e02_geen_ontkenning_zonder_citeereis():
    assert "niet onderscheidend noemt" in REASONCONTROLE
    assert "je hoeft niet elk afgrenzend kenmerk te noemen of te citeren" in (
        REASONCONTROLE
    )
    instructie = _instructie(_systeem(ZUSTER))
    assert instructie.index(REASONCONTROLE) + len(REASONCONTROLE) + 1 == (
        instructie.index(LACKS_CONTROLE)
    )
    assert instructie.count("Controleer vóór je antwoordt") == 2


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


@pytest.mark.skipif(not R6_SELECTIE.is_file(), reason="R6-ontwikkelselectie ontbreekt")
def test_geen_termen_uit_de_r6_ontwikkelinvoer_in_de_nieuwe_zinnen():
    termen = set()
    for geval in _r6_gevallen():
        termen.add(geval["begrip"].lower())
        termen.update(b["term"].lower() for b in geval.get("buren") or [])
    for zin in NIEUW:
        for term in termen:
            assert not re.search(rf"\b{re.escape(term)}\b", zin.lower()), (term, zin)


@pytest.mark.skipif(not R6_SELECTIE.is_file(), reason="R6-ontwikkelselectie ontbreekt")
def test_r6_ontwikkelgevallen_krijgen_de_herstelzinnen_zonder_labellek():
    gevallen = _r6_gevallen()
    assert len(gevallen) == 9
    for geval in gevallen:
        systeem = _systeem(geval)  # controleer_afscherming: geen labels in prompt
        for zin in NIEUW:
            assert systeem.count(zin) == 1, (geval["id"], zin)
