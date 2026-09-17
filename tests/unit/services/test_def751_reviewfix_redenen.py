"""DEF-751 stap 2, reviewcorrectie 3 (Codex, head db027b894): geen modeltekst in redenen.

Een afgewezen conflictmelding krijgt uitsluitend een vaste foutcode en een
vaste technische omschrijving. Vrije modelstrings — onbekende JSON-sleutels,
ongeldige bronverwijzingen, wat dan ook uit de payload — bereiken nooit
`reden`, de responsemetadata of het log. Bewezen met een synthetische
privémarker op beide routes (onbekende sleutel én ongeldige bron), negatief
geasserteerd op parser, response én caplog.
"""

from __future__ import annotations

import json

import pytest

from services.modelantwoord import (
    CONFLICT_SENTINEL,
    FOUTCODES,
    SOORT_ONGELDIG,
    lees_modelantwoord,
    verifieer_gronden,
)
from tests.unit.services.orchestrators.test_def751_betekenisconflict_keten import (
    LEZINGEN,
    VRAAG,
    Keten,
)

pytestmark = [pytest.mark.unit]

PRIVE = "PRIVE_MARKER_Jan_Jansen_BSN123456789"


def _melding(payload: dict) -> str:
    return f"{CONFLICT_SENTINEL} " + json.dumps(payload, ensure_ascii=False)


ONBEKENDE_SLEUTEL = _melding({"vraag": VRAAG, "lezingen": LEZINGEN, PRIVE: "x"})
ONBEKENDE_LEZINGSSLEUTEL = _melding(
    {"vraag": VRAAG, "lezingen": [LEZINGEN[0], {**LEZINGEN[1], PRIVE: "x"}]}
)
ONGELDIGE_BRON = _melding(
    {"vraag": VRAAG, "lezingen": [LEZINGEN[0], {**LEZINGEN[1], "bron": PRIVE}]}
)


@pytest.mark.parametrize(
    ("raw", "code"),
    [
        (ONBEKENDE_SLEUTEL, "onbekende_sleutel"),
        (ONBEKENDE_LEZINGSSLEUTEL, "lezing_onbekende_sleutel"),
    ],
)
def test_parserreden_is_vaste_code_zonder_modeltekst(raw, code):
    antwoord = lees_modelantwoord(raw)
    assert antwoord.soort == SOORT_ONGELDIG
    assert antwoord.code == code
    assert antwoord.reden == FOUTCODES[code]
    assert PRIVE not in antwoord.reden and PRIVE not in antwoord.code


def test_grondreden_is_vaste_code_zonder_bronwaarde():
    conflict = lees_modelantwoord(ONGELDIGE_BRON).conflict
    assert conflict is not None
    uitkomst = verifieer_gronden(conflict, bron_nrs={1}, contextwaarden={"DJI"})
    assert uitkomst is not None
    code, reden = uitkomst
    assert code == "grond_niet_aangeleverd"
    assert reden == FOUTCODES[code]
    assert PRIVE not in reden


def test_alle_foutcodes_zijn_vaste_teksten_zonder_placeholders():
    for code, tekst in FOUTCODES.items():
        assert "{" not in tekst and "}" not in tekst, code
        assert tekst.strip() == tekst and tekst


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("modeltekst", "code"),
    [
        (ONBEKENDE_SLEUTEL, "onbekende_sleutel"),
        (ONBEKENDE_LEZINGSSLEUTEL, "lezing_onbekende_sleutel"),
        (ONGELDIGE_BRON, "grond_niet_aangeleverd"),
    ],
)
async def test_response_en_log_dragen_alleen_vaste_code_en_omschrijving(
    monkeypatch, caplog, modeltekst, code
):
    keten = Keten(monkeypatch, modeltekst)
    with caplog.at_level("DEBUG"):
        response = await keten.run()

    assert response.success is False
    md = response.metadata
    assert md["error_type"] == "modelantwoord_ongeldig"
    assert md["code"] == code
    assert md["reden"] == FOUTCODES[code]
    serialisatie = json.dumps(md, ensure_ascii=False) + (response.error or "")
    assert PRIVE not in serialisatie
    assert VRAAG not in serialisatie
    assert PRIVE not in caplog.text
    assert VRAAG not in caplog.text
    keten.geen_downstream()
