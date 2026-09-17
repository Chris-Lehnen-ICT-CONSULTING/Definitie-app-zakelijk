"""DEF-751 stap 2 — het additieve modelconflictcontract, structureel gelezen.

Het model mag bij een werkelijk betekenisconflict géén definitie leveren
maar één melding: eerste regel `VERDUIDELIJKING NODIG:` gevolgd door één
JSON-object met een gerichte vraag en minstens twee lezingen die elk naar
een aangeleverde bron of contextwaarde verwijzen. Alles wat daarvan afwijkt
(ontbrekende/lege velden, definitie én melding, tekst na de payload, dubbele
melding, onbekende sleutels) is veilig ongeldig: nooit een kandidaat.

Een gewoon definitieantwoord — ook met de oude markerregel — gaat byte-
identiek door naar het bestaande pad. Er is geen regex-semantiekdetector:
alleen de sentinel en de JSON-structuur worden gelezen; de gronden worden
technisch getoetst (verwijst de opgegeven bron/contextwaarde naar iets dat
werkelijk is aangeleverd), niet inhoudelijk.
"""

from __future__ import annotations

import json

import pytest

from services.interfaces import GenerationRequest
from services.modelantwoord import (
    CONFLICT_SENTINEL,
    SOORT_CONFLICT,
    SOORT_DEFINITIE,
    SOORT_ONGELDIG,
    bron_nrs_uit_kwitantie,
    contextwaarden_uit,
    lees_modelantwoord,
    verifieer_gronden,
)

pytestmark = [pytest.mark.unit]

LEZINGEN = [
    {
        "lezing": "de handeling van het vastleggen",
        "bron": "bron 1",
        "grond": "bron 1 beschrijft registratie als activiteit",
    },
    {
        "lezing": "het vastgelegde gegeven",
        "bron": "context: DJI",
        "grond": "de DJI-context gebruikt registratie voor het resultaat",
    },
]
PAYLOAD = {
    "vraag": "Is de handeling of het vastgelegde gegeven bedoeld?",
    "lezingen": LEZINGEN,
}


def melding(payload: dict | str = PAYLOAD, sentinel: str = CONFLICT_SENTINEL) -> str:
    body = (
        payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
    )
    return f"{sentinel} {body}"


# ------------------------------------------------------------ definitie-only


@pytest.mark.parametrize(
    "raw",
    [
        "Een keurmerk is een teken dat …",
        "Ontologische categorie: type\nEen keurmerk is een teken dat …",
        "  \nEen keurmerk is een teken\nmet een tweede regel\n",
        "",
    ],
)
def test_gewoon_antwoord_blijft_byte_identiek_definitiepad(raw):
    antwoord = lees_modelantwoord(raw)
    assert antwoord.soort == SOORT_DEFINITIE
    assert antwoord.tekst is raw
    assert antwoord.conflict is None and antwoord.reden is None


# ---------------------------------------------------------------- conflict


@pytest.mark.parametrize(
    "raw",
    [
        melding(),
        "- " + melding(),
        melding(sentinel="verduidelijking nodig:"),
        f"{CONFLICT_SENTINEL}\n```json\n{json.dumps(PAYLOAD)}\n```",
        f"\n\n{CONFLICT_SENTINEL}\n{json.dumps(PAYLOAD, indent=2)}\n",
    ],
)
def test_geldige_melding_wordt_conflict_met_vraag_en_lezingen(raw):
    antwoord = lees_modelantwoord(raw)
    assert antwoord.soort == SOORT_CONFLICT, antwoord.reden
    assert antwoord.conflict.vraag == PAYLOAD["vraag"]
    assert [lz.to_dict() for lz in antwoord.conflict.lezingen] == LEZINGEN
    assert antwoord.tekst is raw


# ---------------------------------------------------------------- ongeldig


def _zonder(sleutel: str, obj: dict) -> dict:
    kopie = dict(obj)
    kopie.pop(sleutel)
    return kopie


@pytest.mark.parametrize(
    ("raw", "reden_bevat"),
    [
        # Definitie gevolgd door een melding: vermengd.
        ("Een keurmerk is een teken\n" + melding(), "eerste regel"),
        # Melding gevolgd door een definitie: tekst na de payload.
        (melding() + "\nEen keurmerk is een teken", "na de"),
        # Twee meldingen.
        (melding() + "\n" + melding(), "dubbel"),
        # Lege payload.
        (CONFLICT_SENTINEL, "JSON"),
        (CONFLICT_SENTINEL + " ", "JSON"),
        # Vrije tekst i.p.v. JSON — de losse sentinel is te zwak.
        (melding("de bronnen spreken elkaar tegen, welke bedoel je?"), "JSON"),
        # Geen object.
        (melding("[1, 2]"), "object"),
        # Ontbrekende of lege velden.
        (melding(_zonder("vraag", PAYLOAD)), "vraag"),
        (melding({**PAYLOAD, "vraag": "  "}), "vraag"),
        (melding(_zonder("lezingen", PAYLOAD)), "lezingen"),
        (melding({**PAYLOAD, "lezingen": LEZINGEN[:1]}), "minstens twee"),
        (
            melding(
                {**PAYLOAD, "lezingen": [LEZINGEN[0], _zonder("bron", LEZINGEN[1])]}
            ),
            "bron",
        ),
        (
            melding(
                {**PAYLOAD, "lezingen": [LEZINGEN[0], {**LEZINGEN[1], "grond": ""}]}
            ),
            "grond",
        ),
        (
            melding(
                {**PAYLOAD, "lezingen": [LEZINGEN[0], _zonder("lezing", LEZINGEN[1])]}
            ),
            "lezing",
        ),
        # Onbekende sleutels: geen verborgen extra payload.
        (melding({**PAYLOAD, "definitie": "Een keurmerk is …"}), "onbekende"),
        (
            melding({**PAYLOAD, "lezingen": [LEZINGEN[0], {**LEZINGEN[1], "x": 1}]}),
            "onbekende",
        ),
        # Twee keer dezelfde lezing is geen tegenspraak.
        (
            melding(
                {
                    **PAYLOAD,
                    "lezingen": [LEZINGEN[0], {**LEZINGEN[0], "bron": "bron 2"}],
                }
            ),
            "verschillen",
        ),
        # Verkeerde typen.
        (melding({**PAYLOAD, "lezingen": "geen lijst"}), "lezingen"),
        (melding({"vraag": 3, "lezingen": LEZINGEN}), "vraag"),
    ],
)
def test_afwijkende_melding_is_veilig_ongeldig(raw, reden_bevat):
    antwoord = lees_modelantwoord(raw)
    assert antwoord.soort == SOORT_ONGELDIG, antwoord
    assert antwoord.conflict is None
    assert reden_bevat.lower() in (antwoord.reden or "").lower(), antwoord.reden
    # De ruwe tekst blijft beschikbaar voor de aanroeper, maar is geen kandidaat.
    assert antwoord.tekst is raw


# ------------------------------------------------------- gronden (technisch)


def _conflict(lezingen):
    return lees_modelantwoord(melding({**PAYLOAD, "lezingen": lezingen})).conflict


def test_gronden_verwijzen_naar_aangeleverde_bron_of_contextwaarde():
    conflict = _conflict(LEZINGEN)
    assert conflict is not None
    assert verifieer_gronden(conflict, bron_nrs={1, 2}, contextwaarden={"DJI"}) is None
    # Bronnummer en contextwaarde kastongevoelig en met rand-spaties.
    conflict2 = _conflict(
        [
            {**LEZINGEN[0], "bron": " Bron 2 "},
            {**LEZINGEN[1], "bron": "Context:  dji"},
        ]
    )
    assert verifieer_gronden(conflict2, bron_nrs={2}, contextwaarden={"DJI"}) is None


@pytest.mark.parametrize(
    ("bron", "bron_nrs", "contextwaarden"),
    [
        ("bron 3", {1, 2}, {"DJI"}),  # niet-aangeleverd bronnummer
        ("bron 1", set(), {"DJI"}),  # geen bronnen in de prompt
        ("context: OM", {1}, {"DJI"}),  # niet-opgegeven contextwaarde
        ("handboek.txt", {1}, {"DJI"}),  # vrije bronnaam: geen verwijzing
        ("bron één", {1}, {"DJI"}),
        ("", {1}, {"DJI"}),
    ],
)
def test_onverifieerbare_grond_is_een_reden_tot_ongeldigheid(
    bron, bron_nrs, contextwaarden
):
    conflict = _conflict([LEZINGEN[0], {**LEZINGEN[1], "bron": bron}])
    if conflict is None:  # lege bron valt al structureel af
        assert bron == ""
        return
    reden = verifieer_gronden(
        conflict, bron_nrs=bron_nrs, contextwaarden=contextwaarden
    )
    assert reden is not None and "aangeleverd" in reden


def test_bronnummers_uit_de_kwitantie_en_contextwaarden_uit_het_request():
    receipt = {
        "status": "used",
        "sources": [
            {"nr": 1, "source_type": "document"},
            {"nr": 2, "source_type": "rag"},
        ],
        "omitted": [{"nr": 9}],
    }
    assert bron_nrs_uit_kwitantie(receipt) == {1, 2}
    assert bron_nrs_uit_kwitantie(None) == set()
    assert bron_nrs_uit_kwitantie({"sources": "kapot"}) == set()
    request = GenerationRequest(
        id="r",
        begrip="registratie",
        organisatorische_context=["DJI", " "],
        juridische_context=["Strafrecht"],
        wettelijke_basis=["Pbw"],
        organisatie="OM",
    )
    assert contextwaarden_uit(request) == {"DJI", "Strafrecht", "Pbw", "OM"}
