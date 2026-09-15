"""DEF-622: de gedeelde lezer van opgeslagen contextvelden.

Reviewbevinding op de duplicaatlookup: `lees_contextwaarden` maakte van een
JSON-`null` de tekst "None", waardoor `contextsleutel(['A', None])` en de
sleutel via de lezer uiteenliepen en een bestaand record niet werd gevonden.
De lezer volgt dezelfde normalisatie als `canoniseer_contextlijst`: lege en
ontbrekende waarden tellen niet mee.
"""

from __future__ import annotations

import pytest

from domain.context.normalisatie import contextsleutel, lees_contextwaarden

pytestmark = [pytest.mark.unit]


@pytest.mark.parametrize(
    ("opgeslagen", "verwacht"),
    [
        ('["A", null]', ["A"]),
        ("[null]", []),
        ("null", []),
        ('["A", "", " "]', ["A", "", " "]),  # leeg filtert de canonisering
        (["A", None], ["A"]),
        ('"vrije tekst"', ["vrije tekst"]),
        ("vrije tekst", ["vrije tekst"]),
        (None, []),
        ("", []),
    ],
)
def test_lezer_laat_null_weg(opgeslagen, verwacht):
    assert lees_contextwaarden(opgeslagen) == verwacht


def test_sleutel_via_lezer_is_gelijk_aan_sleutel_van_lijst_met_none():
    assert contextsleutel(lees_contextwaarden('["A", null]')) == contextsleutel(
        ["A", None]
    )
    assert contextsleutel(lees_contextwaarden('["A", null]')) == ("a",)
