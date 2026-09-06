#!/usr/bin/env python3
"""Voorbeeldgeneratie en complete definitiegeneratie, hermetisch (DEF-519).

De oorspronkelijke opzet laadde `.env`, sloeg zichzelf over zonder API-key en
rapporteerde met prints en return-waarden. Hetzelfde gedrag wordt hier getoetst
met echte assertions, achter de bevroren providergrens uit `conftest.py`.
Duurmetingen zijn bewust verdwenen: bevroren antwoorden bewijzen gedrag, geen
API-latency.
"""

import uuid

import pytest

from domain.ontological_categories import OntologischeCategorie
from services.interfaces import GenerationRequest
from tests.integration.functionality.conftest import (
    DEFINITIE_TEKST,
    lees_opgeslagen_definitie,
    verwacht_resultaat,
)
from voorbeelden.unified_voorbeelden import (
    DEFAULT_EXAMPLE_COUNTS,
    ExampleType,
    GenerationMode,
    genereer_alle_voorbeelden,
    genereer_antoniemen,
    genereer_praktijkvoorbeelden,
    genereer_synoniemen,
    genereer_tegenvoorbeelden,
    genereer_toelichting,
    genereer_voorbeeld_zinnen,
)

pytestmark = [pytest.mark.integration, pytest.mark.slow]

BEGRIP = "dwangmiddel"
DEFINITIE = (
    "Een bevoegdheid die de overheid kan inzetten om het strafprocesrecht te "
    "handhaven, ook tegen de wil van de betrokkene."
)
CONTEXT = {
    "organisatorisch": ["Politie", "Openbaar Ministerie"],
    "juridisch": ["Strafprocesrecht"],
    "wettelijk": ["Wetboek van Strafvordering"],
}


def test_individual_generation(bevroren_omgeving):
    """Elke losse generatiefunctie levert het aantal en type dat zij belooft."""
    client = bevroren_omgeving.client

    gevallen = [
        ("voorbeeldzinnen", genereer_voorbeeld_zinnen, 3),
        ("praktijkvoorbeelden", genereer_praktijkvoorbeelden, 3),
        ("tegenvoorbeelden", genereer_tegenvoorbeelden, 3),
        ("synoniemen", genereer_synoniemen, 5),
        ("antoniemen", genereer_antoniemen, 5),
    ]

    for soort, functie, verwacht_aantal in gevallen:
        assert DEFAULT_EXAMPLE_COUNTS[soort] == verwacht_aantal
        resultaat = functie(BEGRIP, DEFINITIE, CONTEXT)

        assert isinstance(resultaat, list), f"{soort} moet een lijst opleveren"
        assert resultaat == verwacht_resultaat(soort, verwacht_aantal)

        oproepen = client.oproepen_van(soort)
        assert len(oproepen) == 1, f"{soort} moet precies één providercall doen"
        assert oproepen[0].gevraagd_aantal == verwacht_aantal
        assert BEGRIP in oproepen[0].prompt
        assert "Politie" in oproepen[0].prompt

    # Toelichting is contractueel één string, geen lijst.
    toelichting = genereer_toelichting(BEGRIP, DEFINITIE, CONTEXT)
    assert isinstance(toelichting, str)
    assert toelichting == verwacht_resultaat("toelichting", 1)[0]
    assert len(client.oproepen_van("toelichting")) == 1

    # Discriminatie: zonder bruikbare respons levert elke functie het lege
    # equivalent van haar type — de gelijkheden hierboven zijn dus scherp.
    bevroren_omgeving.zet_modus("leeg")
    for soort, functie, _ in gevallen:
        assert functie(BEGRIP, DEFINITIE, CONTEXT) == [], f"{soort} moet leeglopen"
    assert genereer_toelichting(BEGRIP, DEFINITIE, CONTEXT) == ""


def test_bulk_generation_sequential(bevroren_omgeving):
    """Sequentiële bulkgeneratie dekt alle zes soorten met de juiste vorm."""
    client = bevroren_omgeving.client
    begrip = "voorlopige hechtenis"
    definitie = (
        "De vrijheidsbeneming van een verdachte tijdens het vooronderzoek, "
        "voordat er een onherroepelijk vonnis is."
    )
    context = {
        "organisatorisch": ["Rechter-commissaris", "Raadkamer"],
        "juridisch": ["Strafprocesrecht"],
        "wettelijk": ["Wetboek van Strafvordering art. 63-88"],
    }

    voorbeelden = genereer_alle_voorbeelden(
        begrip, definitie, context, GenerationMode.RESILIENT
    )

    assert set(voorbeelden) == {soort.value for soort in ExampleType}
    for soort in ExampleType:
        sleutel = soort.value
        verwacht_aantal = DEFAULT_EXAMPLE_COUNTS[sleutel]
        if sleutel == "toelichting":
            assert isinstance(voorbeelden[sleutel], str)
            assert voorbeelden[sleutel] == verwacht_resultaat(sleutel, 1)[0]
            continue
        assert isinstance(voorbeelden[sleutel], list)
        assert len(voorbeelden[sleutel]) == verwacht_aantal
        assert voorbeelden[sleutel] == verwacht_resultaat(sleutel, verwacht_aantal)

    # Sequentieel betekent: elke soort precies één keer, geen dubbele calls.
    assert len(client.oproepen) == len(ExampleType)
    assert sorted(oproep.soort or "" for oproep in client.oproepen) == sorted(
        soort.value for soort in ExampleType
    )

    # Discriminatie: een lege provider laat alles leeglopen.
    bevroren_omgeving.zet_modus("leeg")
    leeg = genereer_alle_voorbeelden(
        begrip, definitie, context, GenerationMode.RESILIENT
    )
    assert leeg["toelichting"] == ""
    assert all(
        leeg[soort.value] == [] for soort in ExampleType if soort.value != "toelichting"
    )


async def test_definition_generation(bevroren_omgeving):
    """De echte V2-orchestrator levert een complete definitie op."""
    client = bevroren_omgeving.client
    orchestrator = bevroren_omgeving.container.orchestrator()

    # De oude opzet gaf hier de letterlijke string "PROCES" mee. Dat is geen
    # waarde die de applicatie ooit produceert: `service_factory` zet de enum om
    # via `.value` en de CHECK-constraint op `definities.categorie` kent alleen
    # de kleine variant. Met "PROCES" liep de opslagfase vast op
    # DatabaseConstraintError. Hier staat daarom de canonieke waarde.
    assert OntologischeCategorie.PROCES.value == "proces"

    request = GenerationRequest(
        id=str(uuid.uuid4()),
        begrip="recidive",
        context="Reclassering Nederland",
        ontologische_categorie=OntologischeCategorie.PROCES.value,
    )

    resultaat = await orchestrator.create_definition(request)

    assert resultaat.success, f"generatie mislukt: {resultaat.error}"
    assert resultaat.error is None
    assert resultaat.definition is not None
    assert resultaat.definition.begrip == "recidive"
    assert isinstance(resultaat.definition.definitie, str)
    assert resultaat.definition.definitie.strip()

    # De definitietekst komt aantoonbaar van de bevroren grens (de opschoning
    # mag hem normaliseren, maar niet vervangen).
    kern = "bevoegde instantie binnen het strafprocesrecht"
    assert kern in resultaat.definition.definitie, resultaat.definition.definitie

    # Opslagbewijs: een geslaagd responseobject zegt niets over de database.
    # Lees de rij terug via een nieuwe, echte SQLite-verbinding naar db_path.
    definitie_id = resultaat.definition.id
    assert isinstance(definitie_id, int) and definitie_id > 0
    rij = lees_opgeslagen_definitie(bevroren_omgeving.db_path, definitie_id)
    assert rij is not None, "generatie meldde succes maar sloeg geen rij op"
    assert rij["begrip"] == "recidive"
    assert rij["definitie"] == resultaat.definition.definitie
    assert kern in rij["definitie"]
    assert rij["categorie"] == OntologischeCategorie.PROCES.value
    assert rij["status"] == "draft"
    assert rij["version_number"] == 1

    # Discriminator: dezelfde leesroute vindt niets voor een id dat niet is
    # opgeslagen. De controle hierboven kan dus niet altijd slagen.
    assert (
        lees_opgeslagen_definitie(bevroren_omgeving.db_path, definitie_id + 10_000)
        is None
    )

    # De provider is echt aangeroepen voor de definitie zelf.
    definitie_oproepen = client.oproepen_van(None)
    assert definitie_oproepen, "orchestrator moet de providergrens aanroepen"
    assert "recidive" in definitie_oproepen[0].prompt
    assert DEFINITIE_TEKST.startswith("Een bevroren proefdefinitie")

    # Validatie heeft daadwerkelijk gedraaid. Het contract is de TypedDict uit
    # services.validation.types (sleutel `overall_score`, 0.0-1.0); de oude
    # opzet las `validation_result.score` als attribuut, wat nooit bestond.
    validatie = resultaat.validation_result
    assert validatie is not None
    for sleutel in (
        "version",
        "overall_score",
        "is_acceptable",
        "violations",
        "passed_rules",
        "detailed_scores",
        "system",
    ):
        assert sleutel in validatie, f"validatiecontract mist {sleutel!r}"
    score = validatie["overall_score"]
    assert isinstance(score, (int, float)) and not isinstance(score, bool)
    assert 0.0 <= float(score) <= 1.0
    assert isinstance(validatie["is_acceptable"], bool)
    # Er zijn echt regels geëvalueerd: geslaagd of overtreden, niet allebei leeg.
    assert validatie["passed_rules"] or validatie["violations"]
