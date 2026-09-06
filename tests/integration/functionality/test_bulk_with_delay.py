#!/usr/bin/env python3
"""Bulkgeneratie met pacing tussen de voorbeeldsoorten (DEF-519).

Het oorspronkelijke script liep de zes `ExampleType`-waarden één voor één af met
een wachttijd ervoor, om de live API niet in een rate limit te duwen. Die
wachttijden zeggen offline niets over het product; ze staan hier nog wel, maar
verkort tot een symbolische waarde. Wat écht getoetst wordt is het gedrag van
`generate_examples`: per verzoek het gevraagde aantal, de juiste responsevorm en
één providercall per soort — achter de bevroren grens uit `conftest.py`.
"""

import asyncio
import time

import pytest

from tests.integration.functionality.conftest import verwacht_resultaat
from voorbeelden.unified_voorbeelden import (
    ExampleRequest,
    ExampleResponse,
    ExampleType,
    GenerationMode,
    get_examples_generator,
)

pytestmark = [pytest.mark.integration, pytest.mark.slow]

BEGRIP = "hoger beroep"
DEFINITIE = (
    "Het rechtsmiddel waarbij een partij die het niet eens is met een uitspraak "
    "van de rechter in eerste aanleg, de zaak aan een hogere rechter kan "
    "voorleggen."
)
CONTEXT = {
    "organisatorisch": ["Gerechtshof"],
    "juridisch": ["Strafprocesrecht"],
    "wettelijk": ["Wetboek van Strafvordering"],
}

#: (soort, gevraagd aantal, pacing vóór het verzoek in seconden). De pacing was
#: oorspronkelijk 2-3 seconden tegen live rate limits; offline is elke waarde
#: boven nul pure wachttijd, dus staat hier het symbolische minimum.
PACING = 0.01
GENERATIEPLAN: tuple[tuple[ExampleType, int, float], ...] = (
    (ExampleType.VOORBEELDZINNEN, 3, 0.0),
    (ExampleType.PRAKTIJKVOORBEELDEN, 3, 0.0),
    (ExampleType.TEGENVOORBEELDEN, 3, 0.0),
    (ExampleType.TOELICHTING, 1, PACING),
    (ExampleType.SYNONIEMEN, 5, PACING),
    (ExampleType.ANTONIEMEN, 5, PACING),
)


def _verzoek(soort: ExampleType, aantal: int) -> ExampleRequest:
    return ExampleRequest(
        begrip=BEGRIP,
        definitie=DEFINITIE,
        context_dict=CONTEXT,
        example_type=soort,
        generation_mode=GenerationMode.RESILIENT,
        max_examples=aantal,
    )


async def test_bulk_generation_with_delay(bevroren_omgeving):
    """Elke soort levert het gevraagde aantal, ook met pacing ertussen."""
    generator = get_examples_generator()
    client = bevroren_omgeving.client

    resultaten: dict[str, list[str]] = {}
    begin = time.monotonic()

    for soort, aantal, pauze in GENERATIEPLAN:
        if pauze:
            await asyncio.sleep(pauze)

        respons = generator.generate_examples(_verzoek(soort, aantal))

        assert isinstance(respons, ExampleResponse)
        assert respons.success, f"{soort.value} faalde: {respons.error_message}"
        assert respons.error_message is None
        assert isinstance(respons.generation_time, float)
        assert respons.generation_time >= 0.0
        resultaten[soort.value] = respons.examples

    verstreken = time.monotonic() - begin
    # `asyncio.sleep` garandeert een ondergrens; de pacing is dus echt gelopen.
    assert verstreken >= sum(pauze for _, _, pauze in GENERATIEPLAN)

    # Elke soort precies het gevraagde aantal, met de verwachte inhoud.
    assert set(resultaten) == {soort.value for soort in ExampleType}
    for soort, aantal, _ in GENERATIEPLAN:
        gevonden = resultaten[soort.value]
        assert isinstance(gevonden, list)
        assert len(gevonden) == aantal, f"{soort.value}: {len(gevonden)} van {aantal}"
        assert gevonden == verwacht_resultaat(soort.value, aantal)

    # Eén providercall per soort, met het aantal dat het verzoek vroeg.
    assert len(client.oproepen) == len(GENERATIEPLAN)
    for soort, aantal, _ in GENERATIEPLAN:
        oproepen = client.oproepen_van(soort.value)
        assert len(oproepen) == 1
        if soort is not ExampleType.TOELICHTING:
            assert oproepen[0].gevraagd_aantal == aantal

    # Herhaling van hetzelfde verzoek belast de provider niet opnieuw: de
    # AIServiceV2-cache vangt de identieke prompt op.
    herhaling = generator.generate_examples(_verzoek(ExampleType.SYNONIEMEN, 5))
    assert herhaling.success
    assert herhaling.examples == resultaten[ExampleType.SYNONIEMEN.value]
    assert len(client.oproepen_van(ExampleType.SYNONIEMEN.value)) == 1

    # Discriminatie: met een lege respons loopt élke soort leeg, dus de
    # gelijkheden hierboven kunnen niet toevallig slagen.
    bevroren_omgeving.zet_modus("leeg")
    for soort, aantal, _ in GENERATIEPLAN:
        leeg = generator.generate_examples(_verzoek(soort, aantal))
        assert leeg.examples == [], f"{soort.value} zou leeg moeten zijn"

    # Discriminatie op het aantal: één item minder komt ook echt als minder
    # terug in plaats van te worden aangevuld.
    bevroren_omgeving.zet_modus("tekort")
    tekort = generator.generate_examples(_verzoek(ExampleType.ANTONIEMEN, 5))
    assert len(tekort.examples) == 4
