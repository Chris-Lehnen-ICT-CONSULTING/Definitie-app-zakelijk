"""DEF-768 R7 (/13): betekenisbehoud voor elk genoemd ontbrekend of afgrenzend kenmerk.

Bevinding R6-eindproef (reports/DEF-768-AI-20260925-R6/uitkomst-en-vervolg-v1.md,
R6-E01): in één herhaling noemde de per-buurreden naast het juiste ontbrekende
kenmerk een alternatief kenmerk als mogelijke afgrenzing dat een door de bron
onder het doelbegrip geplaatst (gedeeld) geval zou uitsluiten. De bestaande
eis "blijft binnen wat bron of bedoelde betekenis dragen en maakt de betekenis
niet nauwer" gold alleen voor missing_feature.

Herstel (kleinste generieke tekstcorrectie in de bestaande reasoncontrole): de
eis geldt voor elk kenmerk dat het antwoord als ontbrekend of als mogelijke
afgrenzing noemt, in missing_feature of in een reason, ook als voorbeeld of
alternatief; zo'n kenmerk sluit geen geval uit dat volgens het materiaal onder
dit begrip valt, ook geen gedeeld geval. Geen nieuwe norm, geen plicht alle
kenmerken te noemen of te citeren, geen automatische vernauwing. De oorzaak is
een hypothese; alleen de echte modelproef kan een effect tonen.

Constructiebewijs op de echte prompt; geen claim over modeluitkomsten.
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

pytestmark = [pytest.mark.unit]

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts" / "ess05"))

import proefinvoer as pi

R7_SELECTIE = ROOT / "reports" / "DEF-768-AI-20260925-R7" / "ontwikkelselectie-v1.json"
NORM_SHA = "af550b2cc5868a6dad6ed951d4fc867a86f1b16fa283181941ac355833ac93e4"

#: Het ongewijzigde begin van de reasoncontrole (R4c, R6-E02).
REASONCONTROLE_BEGIN = (
    "Controleer vóór je antwoordt ook je volledige reason tegen het materiaal: "
    "wat je als gedeeld geval of overlap opvoert, moet een gedeeld geval zijn zoals "
    "hierboven omschreven, en wat je als niet beschreven, niet vastgelegd of open "
    "opvoert, mag niet uit een bron of beschrijving blijken, ook niet uit twee "
    "uitspraken samen; een kenmerk van de kern dat je voor een verwant begrip niet "
    "onderscheidend noemt, mag volgens bron of beschrijving geen gevallen van dat "
    "begrip afgrenzen, maar je hoeft niet elk afgrenzend kenmerk te noemen of te "
    "citeren; je reason mag zichzelf en de uitkomst die je per verwant begrip "
    "geeft niet tegenspreken, "
)
#: R7: de betekenisbehoudseis geldt voor elk genoemd ontbrekend of afgrenzend kenmerk.
BETEKENISBEHOUD = (
    "en elk kenmerk dat je in missing_feature of in een reason als ontbrekend of "
    "als mogelijke afgrenzing noemt, ook als voorbeeld of alternatief, blijft "
    "binnen wat bron of bedoelde betekenis dragen en maakt de betekenis niet "
    "nauwer: het sluit geen geval uit dat volgens het materiaal onder dit begrip "
    "valt, ook geen gedeeld geval; "
)
REASONCONTROLE_SLOT = (
    "dat je het kenmerk niet nauwer kunt benoemen, maakt de uitkomst niet unclear; "
    "klopt dat niet, pas dan reason, missing_feature en uitkomst aan."
)
REASONCONTROLE = REASONCONTROLE_BEGIN + BETEKENISBEHOUD + REASONCONTROLE_SLOT
LACKS_CONTROLE = (
    "Controleer vóór je antwoordt of lacks_differentia overeenkomt met je eigen "
    "reason"
)
#: Vervangen /12-formulering (gold alleen voor missing_feature).
OUD_R7 = (
    (
        "en wat je in missing_feature als ontbrekend kenmerk noemt, blijft binnen wat "
        "bron of bedoelde betekenis dragen"
    ),
)
#: Casuswoorden uit de R6-bevinding: mogen nergens in de nieuwe tekst staan.
GEVALSWOORDEN = (
    "puls",
    "ontvang",
    "toevoer",
    "vulgang",
    "vloeistof",
    "stroom",
    "vat",
    "twee",
    "precies",
    "gelijkmatig",
)


def _systeem(geval: dict) -> str:
    norm = laad_ess05_norm()
    prompt = pi.bouw_t_prompt(pi.modelprojectie(geval), norm)
    pi.controleer_afscherming(geval, prompt.teksten, norm)
    return prompt.teksten[0]


def _instructie(systeem: str) -> str:
    begin = systeem.index("Toetsinstructie:")
    return systeem[begin : systeem.index("Uitkomst per verwant begrip", begin)]


def _r7_gevallen() -> list[dict]:
    return json.loads(R7_SELECTIE.read_text(encoding="utf-8"))["gevallen"]


def test_versie_is_verhoogd():
    # /13 (R7): R6-E01 als verbreding van een bestaande zin.
    # /14 (ADR-003): alleen het uitvoertemplate naar het gesloten concept
    # (`ess05-concept/1`); de toetsinstructie (T/13) blijft bytegelijk.
    # /15 (R8-offsetherstel): antwoord zonder posities; T/13 ongewijzigd.
    assert Ess05AssessmentService.PROMPT_VERSION == "ess05-assess/15"


def test_norm_blijft_ongewijzigd():
    assert normhash(laad_ess05_norm()) == NORM_SHA


def test_reasoncontrole_precies_eenmaal_en_oude_grens_weg():
    systeem = _systeem(ZUSTER)
    assert systeem.count(REASONCONTROLE) == 1
    for oud in OUD_R7:
        assert oud not in systeem, oud


def test_reasoncontrole_direct_voor_de_indicatorcontrole():
    instructie = _instructie(_systeem(ZUSTER))
    assert instructie.index(REASONCONTROLE) + len(REASONCONTROLE) + 1 == (
        instructie.index(LACKS_CONTROLE)
    )
    assert instructie.count("Controleer vóór je antwoordt") == 2


def test_eis_geldt_voor_elk_genoemd_kenmerk_in_alle_redenen():
    """Reikwijdte: missing_feature én reasons (algemeen en per buur), ook
    voorbeelden en alternatieven; geen uitsluiting van doelgevallen, ook niet
    van gedeelde gevallen."""
    for deel in (
        "elk kenmerk",
        "in missing_feature of in een reason",
        "als ontbrekend of als mogelijke afgrenzing",
        "ook als voorbeeld of alternatief",
        "maakt de betekenis niet nauwer",
        "het sluit geen geval uit dat volgens het materiaal onder dit begrip valt",
        "ook geen gedeeld geval",
    ):
        assert deel in BETEKENISBEHOUD, deel


def test_geen_nieuwe_plicht_en_geen_automatische_vernauwing():
    """Geen opsom- of citeerplicht, geen vernauwing van de kern, geen nieuwe
    uitkomstroute; de bestaande ontheffingen blijven letterlijk staan."""
    assert "je hoeft niet elk afgrenzend kenmerk te noemen of te citeren" in (
        REASONCONTROLE
    )
    assert "dat je het kenmerk niet nauwer kunt benoemen, maakt de uitkomst niet " in (
        REASONCONTROLE
    )
    for verboden in (
        "noem alle",
        "noem elk",
        "citeer elk",
        "citeer alle",
        "alle kenmerken",
        "maak de kern",
        "vernauw",
        "unclear",
        "not_distinguished",
        "distinguished",
    ):
        assert verboden not in BETEKENISBEHOUD.lower(), verboden


def test_bestaande_e01_e02_en_behoud_blijven():
    """De R6-zinnen (E01, kern-bronbescherming) en alle R6-behoudszinnen blijven."""
    from tests.unit.validation import test_def768_r6_herstel as r6

    systeem = _systeem(ZUSTER)
    for zin in (r6.GEEN_LEEMTE, r6.KERN, *r6.BLIJVEND):
        assert systeem.count(zin) >= 1, zin
    assert systeem.count(r6.GEEN_LEEMTE) == 1
    assert systeem.count(r6.KERN) == 1


def test_nieuwe_tekst_zonder_gevalswoorden():
    for woord in GEVALSWOORDEN:
        assert not re.search(rf"\b{woord}", BETEKENISBEHOUD.lower()), woord


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


@pytest.mark.skipif(not R7_SELECTIE.is_file(), reason="R7-ontwikkelselectie ontbreekt")
def test_geen_termen_uit_de_r7_ontwikkelinvoer_in_de_nieuwe_tekst():
    termen = set()
    for geval in _r7_gevallen():
        termen.add(geval["begrip"].lower())
        termen.update(b["term"].lower() for b in geval.get("buren") or [])
    for term in termen:
        assert not re.search(rf"\b{re.escape(term)}\b", BETEKENISBEHOUD.lower()), term


@pytest.mark.skipif(not R7_SELECTIE.is_file(), reason="R7-ontwikkelselectie ontbreekt")
def test_r7_ontwikkelgevallen_krijgen_de_zin_zonder_labellek():
    gevallen = _r7_gevallen()
    assert len(gevallen) == 9
    for geval in gevallen:
        systeem = _systeem(geval)  # controleer_afscherming: geen labels in prompt
        assert systeem.count(REASONCONTROLE) == 1, geval["id"]


@pytest.mark.skipif(not R7_SELECTIE.is_file(), reason="R7-ontwikkelselectie ontbreekt")
def test_beide_r614_pogingen_krijgen_een_bytegelijke_modelinvoer():
    """Alleen de technische pogingidentiteit verschilt; de modelinvoer niet."""
    per_id = {g["id"]: g for g in _r7_gevallen()}
    norm = laad_ess05_norm()
    prompts = [
        pi.bouw_t_prompt(pi.modelprojectie(per_id[i]), norm)
        for i in ("R614", "R614-D2")
    ]
    assert prompts[0].teksten == prompts[1].teksten
    assert prompts[0].sha256 == prompts[1].sha256
    assert {k: v for k, v in per_id["R614"].items() if k != "id"} == {
        k: v for k, v in per_id["R614-D2"].items() if k != "id"
    }
