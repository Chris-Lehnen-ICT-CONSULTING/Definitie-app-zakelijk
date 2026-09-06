#!/usr/bin/env python3
"""Kritieke voorbeeldgeneratie, hermetisch getoetst (DEF-519).

Oorspronkelijke opzet: een script dat `.env` laadde, zichzelf oversloeg zonder
`OPENAI_API_KEY` en zijn oordeel als return-waarde en print-regels achterliet —
een test die nooit kon falen. Het gedrag dat het wilde bewijzen blijft hier
volledig staan, maar nu achter de bevroren providergrens uit `conftest.py` en
met assertions die omvallen zodra de productiecode iets anders doet.
"""

import pytest

from tests.integration.functionality.conftest import verwacht_resultaat
from voorbeelden.unified_voorbeelden import (
    DEFAULT_EXAMPLE_COUNTS,
    ExampleType,
    GenerationMode,
    genereer_alle_voorbeelden,
    genereer_antoniemen,
    genereer_synoniemen,
)

pytestmark = [pytest.mark.integration, pytest.mark.slow]

BEGRIP = "verdachte"
DEFINITIE = "Een persoon die wordt verdacht van het plegen van een strafbaar feit."
CONTEXT = {
    "organisatorisch": ["Openbaar Ministerie"],
    "juridisch": ["Strafrecht"],
    "wettelijk": ["Wetboek van Strafvordering"],
}


def test_synoniemen_antoniemen(bevroren_omgeving):
    """Synoniemen en antoniemen leveren beide exact vijf bruikbare termen."""
    client = bevroren_omgeving.client

    synoniemen = genereer_synoniemen(BEGRIP, DEFINITIE, CONTEXT)
    antoniemen = genereer_antoniemen(BEGRIP, DEFINITIE, CONTEXT)

    assert synoniemen == verwacht_resultaat("synoniemen", 5)
    assert antoniemen == verwacht_resultaat("antoniemen", 5)
    assert all(isinstance(item, str) and item.strip() for item in synoniemen)
    assert all(isinstance(item, str) and item.strip() for item in antoniemen)

    # Het aantal is geen toevalstreffer van het antwoordboek: de productiecode
    # heeft de provider aantoonbaar om precies vijf items gevraagd.
    assert DEFAULT_EXAMPLE_COUNTS["synoniemen"] == 5
    assert DEFAULT_EXAMPLE_COUNTS["antoniemen"] == 5
    syn_oproepen = client.oproepen_van("synoniemen")
    ant_oproepen = client.oproepen_van("antoniemen")
    assert len(syn_oproepen) == 1, "synoniemen moeten precies één providercall doen"
    assert len(ant_oproepen) == 1, "antoniemen moeten precies één providercall doen"
    assert syn_oproepen[0].gevraagd_aantal == 5
    assert ant_oproepen[0].gevraagd_aantal == 5
    assert BEGRIP in syn_oproepen[0].prompt
    assert "Openbaar Ministerie" in syn_oproepen[0].prompt

    # Discriminatie: met een lege respons mag hierboven niets meer slagen.
    bevroren_omgeving.zet_modus("leeg")
    assert genereer_synoniemen(BEGRIP, DEFINITIE, CONTEXT) == []
    assert genereer_antoniemen(BEGRIP, DEFINITIE, CONTEXT) == []

    # Discriminatie: één item te weinig komt ook echt als vier terug.
    bevroren_omgeving.zet_modus("tekort")
    assert len(genereer_synoniemen(BEGRIP, DEFINITIE, CONTEXT)) == 4


def test_bulk_generation(bevroren_omgeving):
    """Bulkgeneratie levert alle zes soorten met de juiste vorm en aantallen."""
    client = bevroren_omgeving.client
    begrip = "strafblad"
    definitie = (
        "Een officieel document waarin de strafrechtelijke veroordelingen van "
        "een persoon worden geregistreerd."
    )
    context = {
        "organisatorisch": ["Justitiële Informatiedienst"],
        "juridisch": ["Strafrecht"],
        "wettelijk": ["Wet justitiële en strafvorderlijke gegevens"],
    }

    voorbeelden = genereer_alle_voorbeelden(
        begrip, definitie, context, GenerationMode.RESILIENT
    )

    # De sleutels zijn de Nederlandse `ExampleType`-waarden — de oude Engelse
    # verwachtingen ("sentence", "synonyms", ...) bestonden nergens in de code.
    assert set(voorbeelden) == {soort.value for soort in ExampleType}

    for soort in ("voorbeeldzinnen", "praktijkvoorbeelden", "tegenvoorbeelden"):
        verwacht = DEFAULT_EXAMPLE_COUNTS[soort]
        assert verwacht == 3
        assert voorbeelden[soort] == verwacht_resultaat(soort, verwacht)

    for soort in ("synoniemen", "antoniemen"):
        verwacht = DEFAULT_EXAMPLE_COUNTS[soort]
        assert verwacht == 5
        assert voorbeelden[soort] == verwacht_resultaat(soort, verwacht)

    # Toelichting is contractueel één string, geen lijst.
    assert isinstance(voorbeelden["toelichting"], str)
    assert voorbeelden["toelichting"] == verwacht_resultaat("toelichting", 1)[0]

    # Zes soorten, zes providercalls: er is niets stilletjes overgeslagen of
    # uit een cache van een eerdere test gehaald.
    assert len(client.oproepen) == 6
    assert {oproep.soort for oproep in client.oproepen} == {
        soort.value for soort in ExampleType
    }

    # Discriminatie: een lege provider laat alle lijsten leeglopen en de
    # toelichting leeg achter — de assertions hierboven zijn dus scherp.
    bevroren_omgeving.zet_modus("leeg")
    leeg = genereer_alle_voorbeelden(
        begrip, definitie, context, GenerationMode.RESILIENT
    )
    assert all(
        leeg[soort.value] == [] for soort in ExampleType if soort.value != "toelichting"
    )
    assert leeg["toelichting"] == ""
