"""DEF-821 — de aparte uitkomst 'ontbrekende noodzakelijke betekenisgrond'.

Het modelantwoordcontract (DEF-751) kent naast de definitie en het
ESS-02-betekenisconflict een tweede, strikt herkenbare niet-succesuitkomst:
sentinel `BETEKENISGROND ONTBREEKT:` op de eerste regel plus precies één
JSON-object met `ontbrekende_grond` en `vraag`. Er zijn géén lezingen of
bronverwijzingen nodig (geen verzonnen conflict). Alles wat afwijkt —
gemengd met een definitie of met een conflictmelding, onbekende of lege
velden, markup rond de payload — is veilig ongeldig. Modeltekst in de velden
blijft letterlijk tekst (geen interpretatie van HTML/Markdown hier).
"""

from __future__ import annotations

import json

import pytest

from services.modelantwoord import (
    CONFLICT_SENTINEL,
    FOUTCODES,
    ONTBREKENDE_GROND_SENTINEL,
    SOORT_CONFLICT,
    SOORT_DEFINITIE,
    SOORT_ONGELDIG,
    SOORT_ONTBREKENDE_GROND,
    lees_modelantwoord,
)

pytestmark = [pytest.mark.unit]

GROND = "waarvan het percentage wordt berekend en aan welk criterium wordt voldaan"
VRAAG = "Op welke verzameling en welk criterium slaat de grens van 80% (ten minste)?"
DEFINITIE = "Partij waarvan ten minste 80% van de voorwerpen blauw is"
LEZINGEN = [
    {"lezing": "a", "bron": "bron 1", "grond": "x"},
    {"lezing": "b", "bron": "bron 2", "grond": "y"},
]
CONFLICTPAYLOAD = {"vraag": "v", "lezingen": LEZINGEN}
GRONDPAYLOAD = {"ontbrekende_grond": GROND, "vraag": VRAAG}


def melding(payload: dict | None = None, sentinel: str = ONTBREKENDE_GROND_SENTINEL):
    data = GRONDPAYLOAD if payload is None else payload
    return f"{sentinel} " + json.dumps(data, ensure_ascii=False)


def test_sentinels_zijn_verschillend_en_geen_deelstring_van_elkaar():
    assert ONTBREKENDE_GROND_SENTINEL != CONFLICT_SENTINEL
    assert ONTBREKENDE_GROND_SENTINEL.lower() not in CONFLICT_SENTINEL.lower()
    assert CONFLICT_SENTINEL.lower() not in ONTBREKENDE_GROND_SENTINEL.lower()


def test_geldige_melding_ontbrekende_grond_zonder_lezingen():
    antwoord = lees_modelantwoord(melding())
    assert antwoord.soort == SOORT_ONTBREKENDE_GROND
    assert antwoord.conflict is None
    assert antwoord.code is None and antwoord.reden is None
    assert antwoord.ontbrekende_grond is not None
    assert antwoord.ontbrekende_grond.ontbrekende_grond == GROND
    assert antwoord.ontbrekende_grond.vraag == VRAAG
    assert antwoord.ontbrekende_grond.to_dict() == GRONDPAYLOAD


@pytest.mark.parametrize(
    "raw",
    [
        # Kastongevoelig, op een eigen regel, met fence en met opsommingsteken.
        melding().replace(ONTBREKENDE_GROND_SENTINEL, "betekenisgrond ontbreekt:"),
        f"{ONTBREKENDE_GROND_SENTINEL}\n" + json.dumps(GRONDPAYLOAD),
        f"\n\n{ONTBREKENDE_GROND_SENTINEL}\n```json\n"
        + json.dumps(GRONDPAYLOAD)
        + "\n```",
        "- " + melding(),
    ],
)
def test_toegestane_vormvarianten(raw):
    assert lees_modelantwoord(raw).soort == SOORT_ONTBREKENDE_GROND


def test_witruimte_in_velden_wordt_samengevoegd():
    antwoord = lees_modelantwoord(
        melding({"ontbrekende_grond": "  a \n b ", "vraag": "c\t d?"})
    )
    assert antwoord.ontbrekende_grond.ontbrekende_grond == "a b"
    assert antwoord.ontbrekende_grond.vraag == "c d?"


@pytest.mark.parametrize(
    ("raw", "code"),
    [
        # Gemengd met een definitie, vóór of ná de melding.
        (DEFINITIE + "\n" + melding(), "sentinel_niet_eerst"),
        (melding() + "\n" + DEFINITIE, "tekst_na_payload"),
        # Gemengd met een conflictmelding (in beide volgordes) of dubbel.
        (
            melding() + "\n" + melding(CONFLICTPAYLOAD, CONFLICT_SENTINEL),
            "gemengde_melding",
        ),
        (
            melding(CONFLICTPAYLOAD, CONFLICT_SENTINEL) + "\n" + melding(),
            "gemengde_melding",
        ),
        (melding() + "\n" + melding(), "dubbele_melding"),
        # Misvormd.
        (f"{ONTBREKENDE_GROND_SENTINEL}", "payload_ontbreekt"),
        (f"{ONTBREKENDE_GROND_SENTINEL} de noemer ontbreekt", "payload_geen_json"),
        (f"{ONTBREKENDE_GROND_SENTINEL} [1, 2]", "payload_geen_object"),
        (f'{ONTBREKENDE_GROND_SENTINEL} {{"vraag": "{VRAAG}"', "payload_geen_json"),
        (melding({"vraag": VRAAG}), "grond_ontbreekt"),
        (melding({"ontbrekende_grond": "  ", "vraag": VRAAG}), "grond_ontbreekt"),
        (melding({"ontbrekende_grond": ["a"], "vraag": VRAAG}), "grond_ontbreekt"),
        (melding({"ontbrekende_grond": GROND}), "vraag_ontbreekt"),
        (melding({"ontbrekende_grond": GROND, "vraag": 3}), "vraag_ontbreekt"),
        # Geen fictieve lezingen, geen extra velden (ook geen definitie-veld).
        (melding({**GRONDPAYLOAD, "lezingen": LEZINGEN}), "onbekende_sleutel"),
        (melding({**GRONDPAYLOAD, "definitie": DEFINITIE}), "onbekende_sleutel"),
        # Markup rond sentinel of payload: niet herkenbaar → veilig ongeldig.
        (
            f"**{ONTBREKENDE_GROND_SENTINEL}** " + json.dumps(GRONDPAYLOAD),
            "payload_geen_json",
        ),
        ("```\n" + melding() + "\n```", "sentinel_niet_eerst"),
        (
            f"<p>{ONTBREKENDE_GROND_SENTINEL} " + json.dumps(GRONDPAYLOAD) + "</p>",
            "sentinel_niet_eerst",
        ),
    ],
)
def test_gemengd_of_misvormd_faalt_veilig_met_vaste_reden(raw, code):
    antwoord = lees_modelantwoord(raw)
    assert antwoord.soort == SOORT_ONGELDIG
    assert antwoord.ontbrekende_grond is None and antwoord.conflict is None
    assert antwoord.code == code
    assert antwoord.reden == FOUTCODES[code]
    # De reden bevat nooit modeltekst.
    for fragment in (GROND, VRAAG, DEFINITIE):
        assert fragment not in antwoord.reden


def test_markup_in_velden_blijft_letterlijke_tekst():
    """Het contract leest structuur; weergave als platte tekst is aan de UI."""
    html = '<img src=x onerror="alert(1)"> [klik](javascript:alert(1)) **vet**'
    antwoord = lees_modelantwoord(melding({"ontbrekende_grond": html, "vraag": html}))
    assert antwoord.soort == SOORT_ONTBREKENDE_GROND
    assert antwoord.ontbrekende_grond.ontbrekende_grond == html
    assert antwoord.ontbrekende_grond.vraag == html


def test_bestaand_conflict_en_definitiepad_blijven_ongewijzigd():
    conflict = lees_modelantwoord(melding(CONFLICTPAYLOAD, CONFLICT_SENTINEL))
    assert conflict.soort == SOORT_CONFLICT
    assert conflict.ontbrekende_grond is None
    raw = "Ontologische categorie: proces\n" + DEFINITIE
    definitie = lees_modelantwoord(raw)
    assert definitie.soort == SOORT_DEFINITIE
    assert definitie.tekst is raw


def test_conflictpayload_met_ontbrekende_grondvelden_blijft_ongeldig():
    """Geen vermenging van de twee contracten binnen één payload."""
    antwoord = lees_modelantwoord(
        melding({**CONFLICTPAYLOAD, "ontbrekende_grond": GROND}, CONFLICT_SENTINEL)
    )
    assert antwoord.soort == SOORT_ONGELDIG
    assert antwoord.code == "onbekende_sleutel"
