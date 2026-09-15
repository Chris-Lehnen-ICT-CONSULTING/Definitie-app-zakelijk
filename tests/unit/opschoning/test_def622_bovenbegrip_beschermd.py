"""DEF-622 vervolgcriteria — de cleaner beschermt het bovenbegrip (CW-GEN-03).

De basisopschoning verwijderde configureerbare 'verboden frasen' als
beginconstructie. Voor lidwoorden en koppelwerkwoorden ("de", "is een") is
dat vormnormalisatie; voor een frase die het bovenbegrip draagt ("Handeling
die …", "Proces waarbij …") is het betekenisverlies: wat overblijft is een
kernloos fragment ("Door een toezichthouder wordt verricht …") dat vervolgens
wordt getoetst en opgeslagen alsof het de definitie is (onderzoek P-08,
coördinatorbaseline `reports/def622/vervolg/coordinator-cleaner-baseline.json`).

Besluit: de cleaner normaliseert vorm en verwijdert nooit het bovenbegrip of
betekenisdragende woorden. Of zo'n bovenbegrip inhoudelijk passend is, blijft
een oordeel van de toetsregels (ARAI-02 containerbegrippen), niet van de
nabewerking. Een tekstvergelijking achteraf vervangt deze bescherming niet.
"""

from __future__ import annotations

import pytest

from opschoning.opschoning import opschonen
from opschoning.opschoning_enhanced import opschonen_enhanced

pytestmark = [pytest.mark.unit]


@pytest.mark.parametrize(
    ("invoer", "verwacht"),
    [
        (
            (
                "Handeling die door een toezichthouder wordt verricht om naleving "
                "vast te stellen"
            ),
            (
                "Handeling die door een toezichthouder wordt verricht om naleving "
                "vast te stellen."
            ),
        ),
        (
            "Proces waarbij de volledigheid van een dossier wordt gecontroleerd",
            "Proces waarbij de volledigheid van een dossier wordt gecontroleerd.",
        ),
        (
            "vorm van toezicht die op afstand wordt uitgeoefend",
            "Vorm van toezicht die op afstand wordt uitgeoefend.",
        ),
        (
            "Kwaliteitskeurmerk dat uitsluitend door Stichting Zilver wordt verleend",
            "Kwaliteitskeurmerk dat uitsluitend door Stichting Zilver wordt verleend.",
        ),
        # Alleen het lidwoord is vorm; het bijvoeglijk naamwoord blijft staan
        # (of het passend is, beoordeelt ARAI-03 — niet de nabewerking).
        ("een belangrijk proces", "Belangrijk proces."),
    ],
    ids=[
        "handeling-die",
        "proces-waarbij",
        "vorm-van",
        "noodzakelijke-naam",
        "lidwoord-plus-bijvoeglijk",
    ],
)
def test_bovenbegrip_en_betekenisdragende_woorden_blijven_staan(invoer, verwacht):
    assert opschonen(invoer, "controle") == verwacht
    assert opschonen_enhanced(invoer, "controle", handle_gpt_format=False) == verwacht


@pytest.mark.parametrize(
    ("invoer", "verwacht"),
    [
        ("is een uitspraak van de rechter", "Uitspraak van de rechter."),
        ("de rechterlijke beslissing", "Rechterlijke beslissing."),
        ("vonnis betekent een beslissing", "Beslissing."),
        ("Vonnis: een uitspraak", "Uitspraak."),
        (
            "Ontologische categorie: type\nis een document dat rechten vastlegt",
            "Document dat rechten vastlegt.",
        ),
    ],
    ids=["koppelwerkwoord", "lidwoord", "circulair", "term-dubbelepunt", "gpt-kop"],
)
def test_vormnormalisatie_blijft_werken(invoer, verwacht):
    assert opschonen_enhanced(invoer, "vonnis", handle_gpt_format=True) == verwacht


@pytest.mark.parametrize(
    ("invoer", "begrip", "verwacht"),
    [
        # Het begrip als voorvoegsel van een langer woord: geen termprefix.
        (
            "Controlehandeling die op afstand wordt uitgevoerd",
            "controle",
            "Controlehandeling die op afstand wordt uitgevoerd.",
        ),
        # Een echt bovenbegrip dat het begrip herhaalt (circulair volgens
        # SAM-05, een toetsoordeel) verdwijnt niet alleen om die herhaling.
        (
            "Controle die door een toezichthouder wordt verricht",
            "controle",
            "Controle die door een toezichthouder wordt verricht.",
        ),
        (
            "Handeling die een dossier opent",
            "handeling",
            "Handeling die een dossier opent.",
        ),
        # Ondubbelzinnige termprefix mét scheidingsteken blijft normalisatie.
        ("Vonnis: een uitspraak van de rechter", "vonnis", "Uitspraak van de rechter."),
        (
            "vonnis - een uitspraak van de rechter",
            "vonnis",
            "Uitspraak van de rechter.",
        ),
        ("vonnis betekent een beslissing", "vonnis", "Beslissing."),
    ],
    ids=[
        "begrip-als-woorddeel",
        "bovenbegrip-herhaalt-begrip",
        "bovenbegrip-is-begrip",
        "term-dubbelepunt",
        "term-streepje",
        "term-koppelwerkwoord",
    ],
)
def test_termprefix_alleen_met_woordgrens_en_scheidingsteken(invoer, begrip, verwacht):
    assert opschonen(invoer, begrip) == verwacht


def test_opschoning_is_idempotent_op_beschermde_kern():
    """Een tweede opschoning (de validatie schoont opnieuw) verandert niets
    meer — anders zou de getoetste tekst van de opgeslagen tekst afwijken."""
    tekst = (
        "Handeling die door een toezichthouder wordt verricht om naleving vast "
        "te stellen"
    )
    eerste = opschonen(tekst, "controle")
    assert opschonen(eerste, "controle") == eerste
