"""DEF-768 R4-OC-01 (/10): samengestelde procesoverlap versus gedeelde gebeurtenis.

Reviewbevinding R4-OC-01 (logs/def768/r4-ontwikkelcorrectie-review-result-v1.md):
de /9-zin stelde absoluut dat een situatie, handeling of gebeurtenis waarin
exemplaren van beide begrippen voorkomen "zelf geen geval van die begrippen" is.
Dat sluit een omvattende handeling uit die volgens de bron zelf van beide
soorten is, terwijl de zin ervoor zo'n handeling juist als gedeeld geval noemt.

Twee synthetische flows op de echte keten modelprojectie → bouw_t_prompt:

- PROCES: een omvattende handeling is volgens de bron zelf van beide soorten,
  en binnen haar vinden afzonderlijke handelingen van beide soorten plaats.
  De instructie mag haar niet uitsluiten en moet haar via eigen kenmerken of
  bron als gedeeld geval toelaten.
- OBJECT: twee objectsoorten ondergaan dezelfde handeling (R308-klasse). Dat
  samen voorkomen mag op zichzelf geen gedeeld geval of overlap opleveren.

Constructiebewijs op de echte prompt: de instructie bevat voor beide flows de
juiste, niet-tegenstrijdige route. Geen claim over modeluitkomsten.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

from services.validation.ess05_assessment_service import laad_ess05_norm
from tests.unit.validation.test_def768_r4c_gevalsbegrip import ABSOLUUT_R4C, GEVAL

pytestmark = [pytest.mark.unit]

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts" / "ess05"))

import proefinvoer as pi

_CONTEXT = {
    "organisatorische_context": ["Synthetische werkplaats Ovrand"],
    "juridische_context": [],
    "wettelijke_basis": [],
}
PROCES_BRON = (
    "Ovrand kent keurslagen en boekslagen. Een keurslag is een handeling die "
    "informatie toetst; een boekslag is een handeling die informatie vastlegt. "
    "Een dubbelslag toetst informatie en legt die vast, en is daarmee zowel een "
    "keurslag als een boekslag. Binnen een dubbelslag vinden ook een afzonderlijke "
    "toetsing en een afzonderlijke vastlegging plaats."
)
PROCES = {
    "id": "R4D-proces",
    "begrip": "keurslag",
    "tekst": "handeling die informatie toetst",
    "toelichting": None,
    "categorie": None,
    "context": _CONTEXT,
    "bronnen": [
        {
            "provider": "documents",
            "doc_id": "synthetisch-r4d-proces",
            "title": "Synthetische afspraak Ovrand",
            "snippet": PROCES_BRON,
        }
    ],
    "buren": [
        {
            "term": "boekslag",
            "definitie": "handeling die informatie vastlegt",
            "herkomst": "gebruiker",
            "bevestigd": True,
        }
    ],
    "verwacht": "review_required",
}
OBJECT_BRON = (
    "Ovrand kent precies twee soorten kommen: schaalkommen en schenkkommen. Een "
    "schaalkom heeft een vlakke bodem; een schenkkom heeft een tuit. Beide soorten "
    "ondergaan dezelfde spoelbeurt. Andere kommen komen hier niet voor."
)
OBJECT = {
    **PROCES,
    "id": "R4D-object",
    "begrip": "schaalkom",
    "tekst": "kom met een vlakke bodem",
    "bronnen": [
        {
            "provider": "documents",
            "doc_id": "synthetisch-r4d-object",
            "title": "Synthetische afspraak Ovrand",
            "snippet": OBJECT_BRON,
        }
    ],
    "buren": [
        {
            "term": "schenkkom",
            "definitie": "kom met een tuit",
            "herkomst": "gebruiker",
            "bevestigd": True,
        }
    ],
}
#: De voorwaardelijke route voor een omvattende handeling (R4-OC-01).
OMVATTEND_TOEGELATEN = (
    "zo'n omvattende situatie, handeling of gebeurtenis is alleen zelf een gedeeld "
    "geval als haar eigen kenmerken of de bron haar als exemplaar van beide "
    "begrippen dragen"
)
#: De R308-grens: samen voorkomen of dezelfde handeling ondergaan bewijst niets.
SAMEN_GEEN_OVERLAP = (
    "dat exemplaren van beide begrippen in dezelfde situatie, handeling of "
    "gebeurtenis voorkomen of dezelfde handeling ondergaan, maakt op zichzelf geen "
    "gedeeld geval en geen overlap"
)


def _teksten(geval: dict) -> tuple[str, str]:
    norm = laad_ess05_norm()
    prompt = pi.bouw_t_prompt(pi.modelprojectie(geval), norm)
    pi.controleer_afscherming(geval, prompt.teksten, norm)
    return prompt.teksten


def _instructie(systeem: str) -> str:
    begin = systeem.index("Toetsinstructie:")
    return systeem[begin : systeem.index("Uitkomst per verwant begrip", begin)]


def _zinnen(tekst: str) -> list[str]:
    return [z for z in re.split(r"(?<=[.])\s+", tekst) if z.strip()]


@pytest.mark.parametrize("geval", [PROCES, OBJECT], ids=["proces", "object"])
def test_bron_bereikt_de_prompt_onveranderd(geval):
    _, user = _teksten(geval)
    assert geval["bronnen"][0]["snippet"] in user


@pytest.mark.parametrize("geval", [PROCES, OBJECT], ids=["proces", "object"])
def test_geen_instructiezin_sluit_een_omvattende_handeling_absoluut_uit(geval):
    """Onder /9 faalt dit: de absolute uitsluiting zou de dubbelslag, die volgens
    de bron zelf van beide soorten is, als geval verbieden."""
    instructie = _instructie(_teksten(geval)[0])
    assert ABSOLUUT_R4C not in instructie
    for zin in _zinnen(instructie):
        if "gedeeld geval" in zin and "handeling" in zin:
            assert not re.search(r"\bis zelf geen geval\b", zin), zin


def test_proces_omvattende_handeling_kan_gedeeld_geval_zijn():
    systeem, user = _teksten(PROCES)
    instructie = _instructie(systeem)
    # De bron draagt de omvattende handeling expliciet als beide soorten ...
    assert "zowel een keurslag als een boekslag" in user
    # ... en de instructie laat haar via eigen kenmerken of bron toe.
    assert instructie.count(OMVATTEND_TOEGELATEN) == 1
    assert "bij begrippen voor handelingen, één handeling die aan beide" in instructie


def test_object_samen_dezelfde_handeling_ondergaan_is_geen_overlap():
    systeem, user = _teksten(OBJECT)
    instructie = _instructie(systeem)
    assert "ondergaan dezelfde spoelbeurt" in user
    assert instructie.count(SAMEN_GEEN_OVERLAP) == 1
    # De toelating vraagt eigen kenmerken of bronclassificatie van beide soorten,
    # niet alleen samen voorkomen: de grens en de toelating staan in één zin.
    zin = next(z for z in _zinnen(instructie) if SAMEN_GEEN_OVERLAP in z)
    assert OMVATTEND_TOEGELATEN in zin
    assert zin.index(SAMEN_GEEN_OVERLAP) < zin.index(OMVATTEND_TOEGELATEN)


def test_beide_flows_krijgen_dezelfde_ene_gevalsomschrijving():
    for geval in (PROCES, OBJECT):
        instructie = _instructie(_teksten(geval)[0])
        assert instructie.count(GEVAL) == 1
        assert instructie.count("Een geval is") == 1
