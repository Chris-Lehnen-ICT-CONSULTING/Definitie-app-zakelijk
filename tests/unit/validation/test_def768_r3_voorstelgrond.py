"""DEF-768 ronde 3: een buurvoorstel moet door het materiaal zelf gedragen worden.

Bevindingen R2 (reports/DEF-768-AI-20260924-R2/uitkomst-en-vervolg-v2.md en
inhoudelijke-beoordeling-addendum-voorstellen-v1.md):

- R215: uit "een passage is vastgelegd" werd een voorgestelde zelfstandige
  soort naast de kern gemaakt, met aangenomen verwarring;
- R220: uit geregistreerde begin- en eindpunten werd een voorgestelde
  recordsoort gemaakt, met source_id en een letterlijk citaat dat alleen het
  registratiefeit draagt, niet het voorgestelde begrip.

Herleide oorzaak in de T-instructie:
- de voorstelregel liet "kan in deze context verward worden" als eigen
  aanname toe, zonder eis dat verwarring of overlap uit het materiaal blijkt;
- bronherkomst hing aan "staat het voorstel in een bron", niet aan een citaat
  dat het voorgestelde begrip zelf noemt;
- de gebruikersprompt zonder buren vroeg "stel eventueel verwante begrippen
  voor".

Constructiebewijs op de echte prompt; geen claim over modeluitkomsten.
Geldige voorstellen (zusters die de bron zelf noemt) blijven toegestaan en
de strikte parser blijft ongewijzigd.
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
from tests.unit.validation.test_def768_ess05_assessment_service import (
    CONTEXT,
    _service,
)

pytestmark = [pytest.mark.unit]

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts" / "ess05"))

import proefinvoer as pi

R2_EINDSET = (
    ROOT / "reports" / "DEF-768-AI-20260924-R2" / "onafhankelijke-eindset-v1.json"
)

#: /8 (ronde 4, R312) preciseert de R3-kandidaatzinnen en de herkomstregel:
#: dezelfde plek, de bronpassage moet het begrip als kandidaat dragen.
KANDIDAAT = (
    "Een kandidaat is een zelfstandig begrip dat het materiaal zelf opvoert als "
    "soort naast dit begrip onder hetzelfde bovenbegrip"
)
GEEN_SOORT_UIT_GEGEVEN = (
    "Een gegeven, onderdeel, handeling of gebeurtenis die het materiaal alleen "
    "noemt, telt of als deel van dit begrip beschrijft (zoals dat iets is "
    "vastgelegd of geregistreerd), is daarmee nog geen kandidaat"
)
VERWARRING_UIT_MATERIAAL = (
    "Verwarring of gedeelde gevallen moeten uit het materiaal blijken; dat beide "
    "hetzelfde object, dezelfde handeling of dezelfde vastlegging betreffen, toont "
    "dat niet aan"
)
BRONHERKOMST = (
    "Geef source_id en quote alleen als die bronpassage het voorgestelde begrip als "
    "zo'n kandidaat draagt en het citaat het begrip zelf noemt; een bronpassage of "
    "citaat die alleen de naam of een verwant gegeven bevat, draagt het voorstel "
    "niet"
)
BRON_NULL = "Noemt geen aangeleverde bron het voorgestelde begrip, dan zijn source_id en quote beide null"
GEEN_GROND = (
    "Is er onvoldoende grond, doe dan geen voorstel en stel zo nodig in question "
    "één vraag naar de relevante verwante begrippen"
)
NIEUW = (
    KANDIDAAT,
    GEEN_SOORT_UIT_GEGEVEN,
    VERWARRING_UIT_MATERIAAL,
    BRONHERKOMST,
    BRON_NULL,
    GEEN_GROND,
)
OUDE_HERKOMSTREGEL = "Staat het voorstel in een aangeleverde bron, geef dan source_id"
OUDE_UITNODIGING = "stel eventueel verwante begrippen voor"
GEEN_BUREN_NIEUW = (
    "stel alleen een verwant begrip voor als het materiaal het draagt, anders geen "
    "voorstel"
)
#: Bestaande toestemming en grenzen blijven (K-1, R2).
BLIJVEND = (
    "Je mag in proposed_neighbours verwante begrippen voorstellen",
    "begrippen met hetzelfde bovenbegrip",
    "Geen voorstel is beter dan een ongegrond voorstel",
    "blijven een onbevestigd voorstel",
    "niet een ander ding waarmee het begrip in een relatie staat",
)
GEVALSWOORDEN = (
    "passage",
    "cirkelpas",
    "lijnrecord",
    "puntrecord",
    "beginpunt",
    "eindpunt",
    "routepunt",
    "trekbeweging",
    "ronde",
    "talpen",
    "ulder",
    "zeefkaart",
    "tolkaart",
)

#: Synthetisch geval van de R215/R220-klasse (geen R2-eindgeval).
REGISTRATIEFEIT = {
    "id": "R3-T-registratiefeit",
    "begrip": "zeefkaart",
    "tekst": "kaart",
    "toelichting": None,
    "categorie": None,
    "context": {
        "organisatorische_context": ["Synthetische zeefplaats Orrin"],
        "juridische_context": [],
        "wettelijke_basis": [],
    },
    "bronnen": [
        {
            "provider": "documents",
            "doc_id": "synthetisch-r3-registratiefeit",
            "title": "Synthetische afspraak Orrin",
            "snippet": (
                "Een zeefkaart wordt pas gemaakt nadat voor elke zeef een "
                "doorloop is vastgelegd."
            ),
        }
    ],
    "buren": [],
    "verwacht": "fail",
    "verwacht_per_buur": [],
    "grond": "Synthetisch constructiegeval; geen modeluitkomst geclaimd.",
}
#: Synthetisch positief geval: de bron noemt zelf een zelfstandige zuster.
ZUSTER = {
    **REGISTRATIEFEIT,
    "id": "R3-T-zuster",
    "begrip": "tolkaart",
    "tekst": "kaart die toegang geeft tot één tolbrug gedurende één dag",
    "bronnen": [
        {
            "provider": "documents",
            "doc_id": "synthetisch-r3-zuster",
            "title": "Synthetische afspraak Orrin",
            "snippet": (
                "Orrin kent twee soorten kaarten: een tolkaart geeft toegang tot "
                "één tolbrug gedurende één dag; een weekkaart geeft toegang tot "
                "één tolbrug gedurende zeven dagen."
            ),
        }
    ],
    "verwacht": "review_required",
}


def _teksten(geval: dict) -> tuple[str, str]:
    norm = laad_ess05_norm()
    prompt = pi.bouw_t_prompt(pi.modelprojectie(geval), norm)
    pi.controleer_afscherming(geval, prompt.teksten, norm)
    return prompt.teksten


def _instructieblok(systeem: str) -> str:
    begin = systeem.index("- Je mag in proposed_neighbours")
    return systeem[begin : systeem.index(GEEN_GROND) + len(GEEN_GROND)]


def test_versie_is_verhoogd():
    # /14 (ADR-003): alleen het uitvoertemplate naar het gesloten concept
    # (`ess05-concept/1`); de toetsinstructie (T/13) blijft bytegelijk.
    # /15 (R8-offsetherstel): antwoord zonder posities; T/13 ongewijzigd.
    # assess/16 + verify/3 (R9-bewijsherstel): deelzin per bewijsroute; T/13 gelijk.
    # assess/17 + verify/4 (R10-C3): gesloten bewijsroute per claim; T/13 gelijk.
    # assess/18 (answer/2): genest, citaat-eerst antwoord; T/13 gelijk.
    assert Ess05AssessmentService.PROMPT_VERSION == "ess05-assess/19"


def test_voorstelregel_eist_door_het_materiaal_gedragen_kandidaat():
    systeem, _ = _teksten(REGISTRATIEFEIT)
    for zin in NIEUW:
        assert systeem.count(zin) == 1, zin
    assert OUDE_HERKOMSTREGEL not in systeem


def test_geldige_voorstellen_blijven_toegestaan():
    """Geen algemene uitschakeling: de toestemming en haar grenzen blijven."""
    systeem, _ = _teksten(ZUSTER)
    for zin in BLIJVEND:
        assert zin in systeem, zin
    for verbod in (
        "stel geen verwante begrippen voor",
        "proposed_neighbours is altijd leeg",
        "doe nooit een voorstel",
    ):
        assert verbod not in systeem.lower()


def test_gebruikersprompt_zonder_buren_nodigt_niet_meer_ongericht_uit():
    _, gebruiker = _teksten(REGISTRATIEFEIT)
    assert OUDE_UITNODIGING not in gebruiker
    assert gebruiker.count(GEEN_BUREN_NIEUW) == 1


def test_instructie_zonder_gevalswoorden():
    """Hele woorden: 'bronpassage' is een bestaande promptterm, geen gevalswoord."""
    blok = _instructieblok(_teksten(REGISTRATIEFEIT)[0]).lower()
    for woord in GEVALSWOORDEN:
        assert not re.search(rf"\b{woord}\b", blok), woord


@pytest.mark.asyncio
async def test_parser_blijft_een_gedragen_brongebonden_voorstel_aanvaarden():
    """Een zuster die de bron noemt, met exact citaat, blijft een geldig voorstel.

    Gemigreerd (ADR-003, `/1` → `/2`): de specificatie gaat nu via de fake
    als gesloten conceptoordeel met bewijsplaats in `source:` plus volledige
    verificatie door de keten; de toetsing van het brongebonden voorstel is
    gelijk gebleven."""
    bron = {
        "source_id": "doc:synthetisch-r3-zuster",
        "content": ZUSTER["bronnen"][0]["snippet"],
    }
    antwoord = {
        "lacks_differentia": False,
        "reason": "De kern noemt toegang tot één tolbrug gedurende één dag.",
        "neighbours": [],
        "proposed_neighbours": [
            {
                "term": "weekkaart",
                "source_id": "doc:synthetisch-r3-zuster",
                "quote": "een weekkaart geeft toegang tot één tolbrug gedurende "
                "zeven dagen",
                "reason": "De bron noemt de weekkaart als tweede soort kaart.",
            }
        ],
        "question": "Hoort de weekkaart in de vergelijkingsruimte van tolkaart?",
    }
    ai, svc = _service(antwoord)
    doc = (
        await svc.assess("tolkaart", ZUSTER["tekst"], CONTEXT, [bron], buren=[])
    ).als_dict()
    assert doc["status"] == "assessed"
    assert doc["rejected"] in (None, [], {})
    voorstellen = doc["judgment"]["proposed_neighbours"]
    assert [v["term"] for v in voorstellen] == ["weekkaart"]
    assert voorstellen[0]["source_id"] == "doc:synthetisch-r3-zuster"
    assert [c["task_type"] for c in ai.calls] == ["validation", "ess05_verification"]


@pytest.mark.skipif(not R2_EINDSET.is_file(), reason="git-ignored R2-eindset ontbreekt")
@pytest.mark.parametrize("gid", ["R215", "R220"])
def test_r2_diagnosegevallen_krijgen_de_nieuwe_voorstelregel(gid):
    gevallen = json.loads(R2_EINDSET.read_text(encoding="utf-8"))["gevallen"]
    systeem, gebruiker = _teksten(next(g for g in gevallen if g["id"] == gid))
    for zin in NIEUW:
        assert zin in systeem, zin
    assert OUDE_UITNODIGING not in gebruiker
