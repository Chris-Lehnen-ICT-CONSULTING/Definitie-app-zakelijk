"""DEF-622 reviewbevinding 1 — koppelteken in een samenstelling is geen label.

Het termprefix-patroon van de cleaner (`^<begrip>\\b\\s*[:\\-]\\s*`) verwijdert het
begrip als het door een dubbelepunt of streepje wordt gevolgd: "Controle: …",
"controle - …". Dat is vormnormalisatie van een label. Maar een koppelteken
dat direct aan het begrip vastzit is een samenstelling of samentrekking
("Controle-handeling", "Controle- en toezichtshandeling") en draagt betekenis;
het wegsnijden ervan levert een beschadigde definitie op die de echte
generatieroute vervolgens toetst en opslaat (reviewrapport, bevinding 1).

Onderscheid: een labelscheider is een dubbelepunt, of een streepje met
witruimte ervóór ("controle - …"); een koppelteken zonder witruimte vóór het
streepje hoort bij het woord en blijft staan — ook bij een samentrekking met
spatie erna ("Controle- en …").
"""

from __future__ import annotations

import pytest

from opschoning.opschoning import opschonen
from opschoning.opschoning_enhanced import opschonen_enhanced

pytestmark = [pytest.mark.unit]

SAMENSTELLING = "Controle-handeling die een bevoegd ambtenaar verricht"
SAMENTREKKING = "Controle- en toezichtshandeling die een bevoegd ambtenaar verricht"


@pytest.mark.parametrize(
    ("invoer", "verwacht"),
    [
        (SAMENSTELLING, SAMENSTELLING + "."),
        (SAMENTREKKING, SAMENTREKKING + "."),
        # Kleine letter: de hoofdletterherstelling raakt alleen de eerste letter.
        (
            "controle-handeling die een bevoegd ambtenaar verricht",
            SAMENSTELLING + ".",
        ),
        # Een samenstelling na een verwijderd koppelwerkwoord blijft heel.
        (
            "is een controle-handeling die een bevoegd ambtenaar verricht",
            SAMENSTELLING + ".",
        ),
    ],
    ids=["samenstelling", "samentrekking", "kleine-letter", "na-koppelwerkwoord"],
)
def test_koppelteken_binnen_samenstelling_blijft_staan(invoer, verwacht):
    assert opschonen(invoer, "controle") == verwacht
    assert opschonen_enhanced(invoer, "controle", handle_gpt_format=False) == verwacht


REST = "handeling die een bevoegd ambtenaar verricht"


@pytest.mark.parametrize(
    "invoer",
    [
        f"Controle: {REST}",
        f"Controle : {REST}",
        f"controle - {REST}",
        f"Controle: een {REST}",
    ],
    ids=[
        "dubbelepunt",
        "dubbelepunt-met-spatie",
        "streepje-met-spaties",
        "dubbelepunt-en-lidwoord",
    ],
)
def test_labelscheider_wordt_nog_steeds_genormaliseerd(invoer):
    verwacht = "Handeling die een bevoegd ambtenaar verricht."
    assert opschonen(invoer, "controle") == verwacht
    assert opschonen_enhanced(invoer, "controle", handle_gpt_format=False) == verwacht
