"""DEF-768 robuustheidsronde, punt 2 — definitieruis neutraliseren vóór ESS-05.

Besluit Chris 29-09: een categorie-voorregel aan het begin van een definitie en
bronlabels "[Bron n]" gaan vóór de ESS-05-beoordeling uit de definitietekst,
consequent in wat het model als definitie krijgt en in de dekkings- en
citaatcontrole. De opgeslagen data blijft ongewijzigd. Vaste, geteste patronen,
geïnventariseerd in de echte database (read-only, 29-09): `- Ontologische
categorie: soort/proces/resultaat` (19/3/1), `**Ontologische categorie:
proces**` (1), `**Exemplaar**` (1), `Soort  ` (3) en `[Bron n]` (2 records).
"""

from __future__ import annotations

import pytest

from domain.ess05 import bewijsregels as br, contract as ec
from domain.ess05.definitieruis import neutraliseer_definitieruis

pytestmark = [pytest.mark.unit]

KERN = "rechtsbijstandverlener die als advocaat optreedt voor een verdachte"


@pytest.mark.parametrize(
    "voorregel",
    [
        "- Ontologische categorie: soort\n",
        "- Ontologische categorie: proces\n",
        "- Ontologische categorie: resultaat\n",
        "**Ontologische categorie: proces**\n",
        "**Exemplaar**\n\n",
        "Soort  \n",
        "Proces\n",
    ],
)
def test_categorievoorregel_verdwijnt(voorregel):
    assert neutraliseer_definitieruis(voorregel + KERN + ".") == KERN + "."


def test_p1_278_voorregel_en_bronlabels():
    tekst = (
        "Soort  \nrechtsbijstandverlener die als advocaat optreedt voor een verdachte "
        "in een strafvorderlijke procedure op grond van een keuze door de verdachte of "
        "een aanwijzing door het bestuur van de raad voor rechtsbijstand [Bron 1] "
        "[Bron 2] [Bron 3]."
    )
    assert neutraliseer_definitieruis(tekst) == (
        "rechtsbijstandverlener die als advocaat optreedt voor een verdachte in een "
        "strafvorderlijke procedure op grond van een keuze door de verdachte of een "
        "aanwijzing door het bestuur van de raad voor rechtsbijstand."
    )


def test_bronlabels_midden_in_de_tekst():
    assert neutraliseer_definitieruis("Rechter [Bron 1] die oordeelt [Bron 12].") == (
        "Rechter die oordeelt."
    )


@pytest.mark.parametrize(
    "tekst",
    [
        "Proces waarin de identiteit wordt geverifieerd.",  # categorie in de zin
        "Soort rechtsbijstandverlener die optreedt.",  # geen eigen regel
        '"Typering van een grondslag"@nl\n\nToelichting: x.',  # geen categorie
        "Persoon met een lening [zie bijlage].",  # ander blokhaaklabel
        "Persoon\nmet een lening.",  # geen categoriewoord
        "Rechter die oordeelt.\n- Ontologische categorie: soort",  # niet aan het begin
    ],
)
def test_andere_tekst_blijft_ongewijzigd(tekst):
    assert neutraliseer_definitieruis(tekst) == tekst


def test_idempotent():
    tekst = "- Ontologische categorie: soort\nType beoordeling [Bron 1]."
    eenmaal = neutraliseer_definitieruis(tekst)
    assert neutraliseer_definitieruis(eenmaal) == eenmaal == "Type beoordeling."


def test_alleen_de_eerste_voorregel():
    tekst = "Soort\nProces\nrest."
    assert neutraliseer_definitieruis(tekst) == "Proces\nrest."


# --- consequent in het ESS-05-materiaal ---------------------------------------------


CONTEXT = {"organisatorische_context": ["OM"]}
BUUR = {
    "id": "repository:1",
    "term": "toets",
    "definitie": "- Ontologische categorie: soort\nType beoordeling [Bron 1].",
    "herkomst": "repository",
    "bevestigd": False,
}


def _materiaal(tekst: str) -> dict[str, str]:
    return ec.beoordelingsmateriaal(
        "raadsman", tekst, [], ec.normaliseer_buren([BUUR]), contexten=CONTEXT
    )


def test_materiaal_definitie_en_buurbeschrijving_zonder_ruis():
    materiaal = _materiaal("Soort  \n" + KERN + " [Bron 1].")
    assert materiaal["definition"] == KERN + "."
    assert materiaal["neighbour:repository:1"] == "Type beoordeling."


def test_vingerafdruk_blijft_op_de_opgeslagen_tekst():
    # De opgeslagen data verandert niet; een andere recordtekst blijft een andere
    # vingerafdruk (een eerdere beoordeling wordt dan historisch).
    met = ec.bereken_ess05_vingerafdruk(
        "raadsman", "Soort  \n" + KERN, CONTEXT, [], buren=[]
    )
    zonder = ec.bereken_ess05_vingerafdruk("raadsman", KERN, CONTEXT, [], buren=[])
    assert met != zonder


def test_kerndekking_op_de_geneutraliseerde_definitie():
    # 278-achtig: zonder filter zijn 'Soort' en 'Bron 1' ongedekte woorden.
    materiaal = _materiaal("Soort  \n" + KERN + " [Bron 1].")
    invoer = br.Vergelijkingsinvoer("raadsman", materiaal, (("repository:1", "toets"),))
    ruw = {
        "schema_version": br.INTERPRETATIESCHEMA,
        "kern": {
            "bovenbegrip": "rechtsbijstandverlener",
            "kenmerken": [
                {
                    "id": "K1",
                    "kenmerk": "optreden",
                    "waarde": "als advocaat voor een verdachte",
                    "citaat": "die als advocaat optreedt voor een verdachte",
                }
            ],
        },
        "buiten_kern": [],
        "buurgroepen": [],
        "buiten_bereik": [],
        "antwoorden": [
            {"kenmerk_id": "K1", "onderwerp": o, "toestand": "onbesproken",
             "voorwaarden": [], "context": "algemeen", "citaten": []}
            for o in ("doel", "repository:1")
        ],
    }  # fmt: skip
    interpretatie = br.valideer_interpretatie(ruw, invoer)
    assert interpretatie.bovenbegrip == "rechtsbijstandverlener"
