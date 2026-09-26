"""DEF-768 ronde 4: drie T-redeneringsfouten uit de R3-eindproef, gericht hersteld.

Bevindingen R3 (reports/DEF-768-AI-20260924-R3/uitkomst-en-vervolg-v1.md,
inhoudelijke-beoordeling-onafhankelijk-v1.md):

1. R308 — een gedeelde gebruikssituatie van twee objectsoorten werd als
   overlap van gevallen opgevoerd. Oorzaak: "gedeelde gevallen" had geen
   drager; de instructie zei niet dat een gedeeld geval één exemplaar onder
   beide begrippen is. Herstel: die term één keer omschrijven, bij haar eerste
   vermelding. Echte rol-, fase- en handelingsoverlap blijft toegestaan.
2. R312 — een binnen het begrip getelde deelhandeling werd als zelfstandige
   buur met bronclaim voorgesteld. Oorzaak: de R3-kandidaatzin en de
   herkomstregel waren al vervuld zodra de naam in de bron stond. Herstel:
   dezelfde zinnen vervangen; bronpassage moet het begrip als kandidaat dragen.
   Geen absoluut verbod op onderdelen; zustervoorstellen blijven.
3. R313-H1 — expliciet beschreven tegengevallen werden als leemte behandeld
   (unclear in plaats van not_distinguished). Oorzaak: de leemteclausule
   legde niet vast dat beschreven gevallen geen leemte zijn. Herstel: de
   voorwaarde in dezelfde clausule preciseren.

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
from tests.unit.validation.test_def768_r3_voorstelgrond import (
    REGISTRATIEFEIT,
    ZUSTER,
)
from tests.unit.validation.test_def768_r4c_gevalsbegrip import GEEN_LEEMTE, GEVAL

pytestmark = [pytest.mark.unit]

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts" / "ess05"))

import proefinvoer as pi

R3_EINDSET = (
    ROOT / "reports" / "DEF-768-AI-20260924-R3" / "onafhankelijke-eindset-v1.json"
)

# --- 1. drager van overlap ------------------------------------------------------------
#: /9 (R4-ontwikkelcorrectie) preciseert deze /8-zin; de positie-eis blijft.
GEDEELD_GEVAL = GEVAL
# --- 2. voorstelgrond --------------------------------------------------------------------
KANDIDAAT = (
    "Een kandidaat is een zelfstandig begrip dat het materiaal zelf opvoert als "
    "soort naast dit begrip onder hetzelfde bovenbegrip, of waarvan het materiaal "
    "zelf vastlegt dat het met dit begrip verward wordt of er gevallen mee deelt."
)
GEEN_KANDIDAAT = (
    "Een gegeven, onderdeel, handeling of gebeurtenis die het materiaal alleen "
    "noemt, telt of als deel van dit begrip beschrijft (zoals dat iets is "
    "vastgelegd of geregistreerd), is daarmee nog geen kandidaat: maak er geen "
    "soort van en bedenk er geen naam, classificatie of verwarring bij."
)
BRONHERKOMST = (
    "Geef source_id en quote alleen als die bronpassage het voorgestelde begrip als "
    "zo'n kandidaat draagt en het citaat het begrip zelf noemt; een bronpassage of "
    "citaat die alleen de naam of een verwant gegeven bevat, draagt het voorstel "
    "niet."
)
#: Vervangen R3-formuleringen (/7).
OUD_R3 = (
    (
        "Een kandidaat is een zelfstandige soort die het materiaal zelf noemt of "
        "beschrijft"
    ),
    "geen eigen soort, ook niet door er een naam voor te bedenken",
    (
        "Geef source_id en quote alleen als het citaat het voorgestelde begrip zelf "
        "noemt"
    ),
)
# --- 3. unclear alleen bij werkelijke leemte ---------------------------------------------
LEEMTE_VOORWAARDE = (
    "en beschrijft het materiaal geen gevallen van dat begrip die onder de kern "
    "maar niet onder dit begrip vallen, vul die leemte dan niet aan"
)
#: GEEN_LEEMTE: /9 preciseert wat "beschrijft" omvat (geïmporteerd hierboven).
NIEUW = (GEDEELD_GEVAL, KANDIDAAT, GEEN_KANDIDAAT, BRONHERKOMST, GEEN_LEEMTE)
#: Bestaande norm en gedrag blijven (R2-01, K-3b, rol-/fase-overlap, R3).
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
        "omdat het aangeeft dat over dat begrip op dat punt niets of alleen een beperkt "
        "gegeven is vastgelegd"
    ),
    (
        "vul die leemte dan niet aan met aangenomen gevallen van dat begrip, met of "
        "zonder het kenmerk: de uitkomst is dan unclear"
    ),
    "Verwarring of gedeelde gevallen moeten uit het materiaal blijken",
    "Je mag in proposed_neighbours verwante begrippen voorstellen",
    "begrippen met hetzelfde bovenbegrip",
    "Geen voorstel is beter dan een ongegrond voorstel",
    (
        "Noemt geen aangeleverde bron het voorgestelde begrip, dan zijn source_id en "
        "quote beide null"
    ),
    "Is er onvoldoende grond, doe dan geen voorstel",
    (
        "Controleer vóór je antwoordt of lacks_differentia overeenkomt met je eigen "
        "reason"
    ),
)
GEVALSWOORDEN = (
    "koppeling",
    "losmak",
    "toevoer",
    "nevel",
    "puls",
    "proefvlak",
    "pakket",
    "tril",
    "vloeistof",
    "verzegel",
    "trommel",
    "istravel",
    "solnemi",
    "tervulo",
)
NORM_SHA = "af550b2cc5868a6dad6ed951d4fc867a86f1b16fa283181941ac355833ac93e4"


def _teksten(geval: dict) -> tuple[str, str]:
    norm = laad_ess05_norm()
    prompt = pi.bouw_t_prompt(pi.modelprojectie(geval), norm)
    pi.controleer_afscherming(geval, prompt.teksten, norm)
    return prompt.teksten


def test_versie_is_verhoogd():
    # /9 (R4-ontwikkelcorrectie) laat de /8-preciseringen intact.
    # /14 (ADR-003): alleen het uitvoertemplate naar het gesloten concept
    # (`ess05-concept/1`); de toetsinstructie (T/13) blijft bytegelijk.
    # /15 (R8-offsetherstel): antwoord zonder posities; T/13 ongewijzigd.
    # assess/16 + verify/3 (R9-bewijsherstel): deelzin per bewijsroute; T/13 gelijk.
    # assess/17 + verify/4 (R10-C3): gesloten bewijsroute per claim; T/13 gelijk.
    assert Ess05AssessmentService.PROMPT_VERSION == "ess05-assess/17"


def test_norm_blijft_ongewijzigd():
    assert normhash(laad_ess05_norm()) == NORM_SHA


def test_nieuwe_zinnen_elk_precies_eenmaal():
    systeem, _ = _teksten(ZUSTER)
    for zin in NIEUW:
        assert systeem.count(zin) == 1, zin
    assert systeem.count(LEEMTE_VOORWAARDE) == 1


def test_vervangen_r3_formuleringen_zijn_weg():
    systeem, _ = _teksten(REGISTRATIEFEIT)
    for oud in OUD_R3:
        assert oud not in systeem, oud


def test_bestaande_norm_en_gedrag_blijven():
    systeem, _ = _teksten(ZUSTER)
    for zin in BLIJVEND:
        assert zin in systeem, zin


def _instructie_start(systeem: str) -> int:
    """De normtekst (toetsvraag) noemt 'gedeelde gevallen mogen' ook; na die."""
    return systeem.index("Toetsinstructie:")


def test_drager_staat_direct_bij_de_eerste_vermelding():
    systeem, _ = _teksten(ZUSTER)
    eerste = systeem.index("gedeelde gevallen mogen", _instructie_start(systeem))
    assert systeem.index(GEDEELD_GEVAL) == eerste + len("gedeelde gevallen mogen. ")


def test_leemteclausule_draagt_de_voorwaarde_in_dezelfde_zin():
    systeem, _ = _teksten(ZUSTER)
    begin = systeem.index("Laat het materiaal echter open")
    eind = systeem.index("de uitkomst is dan unclear.", begin)
    zin = systeem[begin:eind]
    assert LEEMTE_VOORWAARDE in zin
    assert "." not in zin  # één zin: de voorwaarde, geen losse uitzondering
    assert systeem.index(GEEN_LEEMTE) > eind


def test_geen_absoluut_verbod_op_onderdelen_of_voorstellen():
    systeem, _ = _teksten(ZUSTER)
    laag = systeem.lower()
    for verbod in (
        "een onderdeel is nooit",
        "onderdelen zijn nooit",
        "stel geen verwante begrippen voor",
        "doe nooit een voorstel",
    ):
        assert verbod not in laag
    # De grond "gedeelde gevallen" blijft een route naar een kandidaat.
    assert "er gevallen mee deelt" in KANDIDAAT


def test_instructie_zonder_gevalswoorden():
    systeem, _ = _teksten(REGISTRATIEFEIT)
    blokken = [
        systeem[
            systeem.index(GEDEELD_GEVAL) : systeem.index(GEDEELD_GEVAL)
            + len(GEDEELD_GEVAL)
        ],
        systeem[
            systeem.index("Laat het materiaal echter open") : systeem.index(GEEN_LEEMTE)
            + len(GEEN_LEEMTE)
        ],
        systeem[
            systeem.index(KANDIDAAT) : systeem.index(BRONHERKOMST) + len(BRONHERKOMST)
        ],
    ]
    for blok in blokken:
        for woord in GEVALSWOORDEN:
            assert not re.search(rf"\b{woord}", blok.lower()), woord


@pytest.mark.skipif(not R3_EINDSET.is_file(), reason="git-ignored R3-eindset ontbreekt")
@pytest.mark.parametrize("gid", ["R308", "R312", "R313", "R302", "R320"])
def test_r3_diagnosegevallen_krijgen_de_preciseringen(gid):
    gevallen = json.loads(R3_EINDSET.read_text(encoding="utf-8"))["gevallen"]
    systeem, _ = _teksten(next(g for g in gevallen if g["id"] == gid))
    for zin in NIEUW:
        assert zin in systeem, zin
