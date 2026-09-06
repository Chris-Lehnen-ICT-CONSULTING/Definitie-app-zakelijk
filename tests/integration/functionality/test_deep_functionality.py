#!/usr/bin/env python3
"""Diepe functionaliteitstoets voor DefinitieAgent (DEF-519).

Toetst de vijf onderdelen waarvoor dit bestand oorspronkelijk geschreven is:

1. synoniemen/antoniemen-generatie (vijf items);
2. bulkgeneratie van alle voorbeeldsoorten;
3. endpoint-specifieke rate limiting;
4. de V2-orchestrator;
5. performance-monitoring.

De oude opzet laadde `.env`, sloeg zichzelf over zonder API-key en drukte zijn
oordeel af in plaats van het te asserteren. Alles draait nu achter de bevroren
providergrens uit `conftest.py`; onderdeel 3 en 5 hebben helemaal geen provider
nodig en gebruiken verse, geïsoleerde toestand zodat de uitkomst niet van de
testvolgorde afhangt.
"""

import asyncio
import uuid

import pytest

from domain.ontological_categories import OntologischeCategorie
from services.interfaces import GenerationRequest
from tests.integration.functionality.conftest import (
    lees_opgeslagen_definitie,
    verwacht_resultaat,
)
from utils.performance_monitor import (
    get_performance_monitor,
    start_timing,
    stop_timing,
)
from utils.smart_rate_limiter import RateLimitConfig, get_smart_limiter
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

#: Endpoints uit `config/rate_limit_config.py` die dit bestand oorspronkelijk
#: naast elkaar zette.
PRODUCTIE_ENDPOINTS = (
    "examples_generation_sentence",
    "examples_generation_synonyms",
    "examples_generation_antonyms",
)


async def test_synoniemen_antoniemen(bevroren_omgeving):
    """Synoniemen en antoniemen leveren vijf termen én een gemeten duur op."""
    client = bevroren_omgeving.client

    start_timing("synoniemen_generatie")
    synoniemen = genereer_synoniemen(BEGRIP, DEFINITIE, CONTEXT)
    duur_synoniemen = stop_timing("synoniemen_generatie")

    start_timing("antoniemen_generatie")
    antoniemen = genereer_antoniemen(BEGRIP, DEFINITIE, CONTEXT)
    duur_antoniemen = stop_timing("antoniemen_generatie")

    assert synoniemen == verwacht_resultaat("synoniemen", 5)
    assert antoniemen == verwacht_resultaat("antoniemen", 5)
    assert len(client.oproepen_van("synoniemen")) == 1
    assert len(client.oproepen_van("antoniemen")) == 1

    # De monitor heeft beide operaties echt geregistreerd. De duur meet lokale
    # code achter een bevroren antwoord — géén API-latency.
    assert isinstance(duur_synoniemen, float) and duur_synoniemen >= 0.0
    assert isinstance(duur_antoniemen, float) and duur_antoniemen >= 0.0
    metrics = get_performance_monitor().metrics
    assert metrics["synoniemen_generatie"] == [duur_synoniemen]
    assert metrics["antoniemen_generatie"] == [duur_antoniemen]

    # Discriminatie: zonder bruikbare respons blijft er niets over.
    bevroren_omgeving.zet_modus("leeg")
    assert genereer_synoniemen(BEGRIP, DEFINITIE, CONTEXT) == []
    assert genereer_antoniemen(BEGRIP, DEFINITIE, CONTEXT) == []


async def test_bulk_generation(bevroren_omgeving):
    """Bulkgeneratie levert elke soort met het aantal uit de centrale config."""
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

    assert set(voorbeelden) == {soort.value for soort in ExampleType}
    assert DEFAULT_EXAMPLE_COUNTS == {
        "voorbeeldzinnen": 3,
        "praktijkvoorbeelden": 3,
        "tegenvoorbeelden": 3,
        "synoniemen": 5,
        "antoniemen": 5,
        "toelichting": 1,
    }
    for soort in ExampleType:
        sleutel = soort.value
        if sleutel == "toelichting":
            assert isinstance(voorbeelden[sleutel], str)
            assert voorbeelden[sleutel] == verwacht_resultaat(sleutel, 1)[0]
            continue
        aantal = DEFAULT_EXAMPLE_COUNTS[sleutel]
        assert voorbeelden[sleutel] == verwacht_resultaat(sleutel, aantal)

    assert len(client.oproepen) == len(ExampleType)

    bevroren_omgeving.zet_modus("leeg")
    leeg = genereer_alle_voorbeelden(
        begrip, definitie, context, GenerationMode.RESILIENT
    )
    assert leeg["toelichting"] == ""
    assert all(
        leeg[soort.value] == [] for soort in ExampleType if soort.value != "toelichting"
    )


async def test_rate_limiting(bevroren_omgeving):
    """Rate limiting is echt per endpoint gescheiden en put echt tokens uit."""
    from config.rate_limit_config import get_rate_limit_config

    # 1) Productiebedrading: elke endpoint krijgt zijn eigen limiter met de
    #    configuratie uit config/rate_limit_config.py.
    productie_limiters = {}
    for naam in PRODUCTIE_ENDPOINTS:
        limiter = await get_smart_limiter(naam)
        verwacht = get_rate_limit_config(naam)
        assert limiter.config.tokens_per_second == verwacht.tokens_per_second
        assert limiter.config.bucket_capacity == verwacht.bucket_capacity
        assert limiter.token_bucket.capacity == verwacht.bucket_capacity
        productie_limiters[naam] = limiter

    assert len({id(limiter) for limiter in productie_limiters.values()}) == len(
        PRODUCTIE_ENDPOINTS
    ), "endpoints moeten aparte limiters krijgen"
    assert len(
        {id(limiter.token_bucket) for limiter in productie_limiters.values()}
    ) == len(PRODUCTIE_ENDPOINTS), "endpoints moeten aparte token buckets krijgen"

    # 2) Echt gedrag op verse, geïsoleerde endpoints. De refill staat bewust op
    #    0.1 token/s en de capaciteit op 5: het uitputten is dan een
    #    deterministisch feit en geen wedloop met de klok.
    capaciteit = 5
    probe_endpoints = [f"def519_probe_{letter}" for letter in ("a", "b", "c")]
    probe_config = RateLimitConfig(
        tokens_per_second=0.1, bucket_capacity=capaciteit, burst_capacity=1
    )
    probe_limiters = {}
    try:
        for naam in probe_endpoints:
            probe_limiters[naam] = await get_smart_limiter(naam, probe_config)
            assert probe_limiters[naam].token_bucket.tokens == float(capaciteit)

        async def doe_verzoek(endpoint: str, index: int):
            limiter = probe_limiters[endpoint]
            verkregen = await limiter.token_bucket.acquire(1)
            return endpoint, index, verkregen

        taken = [
            doe_verzoek(endpoint, index)
            for endpoint in probe_endpoints
            for index in range(capaciteit)
        ]
        resultaten = await asyncio.gather(*taken)

        assert len(resultaten) == len(probe_endpoints) * capaciteit
        assert all(verkregen for _, _, verkregen in resultaten)
        for endpoint in probe_endpoints:
            per_endpoint = [r for r in resultaten if r[0] == endpoint]
            assert len(per_endpoint) == capaciteit
            assert sorted(index for _, index, _ in per_endpoint) == list(
                range(capaciteit)
            )

        # Uitgeput: een extra token komt er binnen de korte timeout niet meer
        # uit (refill 0.1/s). Zou de bucket niets aftrekken, dan slaagt dit.
        assert (
            await probe_limiters[probe_endpoints[0]].token_bucket.acquire(
                1, timeout=0.05
            )
            is False
        )

        # ... terwijl een nog niet gebruikt endpoint gewoon doorloopt: het
        # verbruik lekt niet tussen endpoints.
        vers = await get_smart_limiter("def519_probe_vers", probe_config)
        probe_limiters["def519_probe_vers"] = vers
        assert await vers.token_bucket.acquire(1, timeout=0.05) is True
    finally:
        for limiter in probe_limiters.values():
            await limiter.stop()


async def test_orchestrator_v2(bevroren_omgeving):
    """De V2-orchestrator levert definitie én voorbeelden in de metadata."""
    client = bevroren_omgeving.client
    orchestrator = bevroren_omgeving.container.orchestrator()

    request = GenerationRequest(
        id=str(uuid.uuid4()),
        begrip="hoger beroep",
        context="Gerechtshof",
        # Canonieke, kleine waarde: `service_factory` geeft `.value` door en de
        # CHECK-constraint op definities.categorie kent alleen deze vorm.
        ontologische_categorie=OntologischeCategorie.PROCES.value,
    )

    resultaat = await orchestrator.create_definition(request)

    assert resultaat.success, f"generatie mislukt: {resultaat.error}"
    assert resultaat.definition is not None
    assert resultaat.definition.begrip == "hoger beroep"
    assert "bevoegde instantie binnen het strafprocesrecht" in (
        resultaat.definition.definitie
    )

    # Opslagbewijs: lees de rij terug via een nieuwe, echte SQLite-verbinding.
    definitie_id = resultaat.definition.id
    assert isinstance(definitie_id, int) and definitie_id > 0
    rij = lees_opgeslagen_definitie(bevroren_omgeving.db_path, definitie_id)
    assert rij is not None, "generatie meldde succes maar sloeg geen rij op"
    assert rij["begrip"] == "hoger beroep"
    assert rij["definitie"] == resultaat.definition.definitie
    assert rij["categorie"] == OntologischeCategorie.PROCES.value
    assert rij["status"] == "draft"
    assert rij["version_number"] == 1
    # Discriminator: een niet-opgeslagen id levert niets op.
    assert (
        lees_opgeslagen_definitie(bevroren_omgeving.db_path, definitie_id + 10_000)
        is None
    )

    # Voorbeelden komen mee in de metadata (niet in Definition.voorbeelden,
    # dat veld blijft leeg — de oude test las daar en zag daarom altijd 0).
    metadata = resultaat.definition.metadata or {}
    voorbeelden = metadata.get("voorbeelden") or {}
    assert set(voorbeelden) == {soort.value for soort in ExampleType}
    for soort in ExampleType:
        sleutel = soort.value
        if sleutel == "toelichting":
            assert voorbeelden[sleutel] == verwacht_resultaat(sleutel, 1)[0]
            continue
        aantal = DEFAULT_EXAMPLE_COUNTS[sleutel]
        assert voorbeelden[sleutel] == verwacht_resultaat(sleutel, aantal)

    # De providergrens is voor zowel de definitie als de voorbeelden gebruikt.
    assert client.oproepen_van(None), "definitieprompt moet de provider bereiken"
    assert {oproep.soort for oproep in client.oproepen} >= {
        soort.value for soort in ExampleType
    }


async def test_performance_summary(bevroren_omgeving):
    """De performance-summary vat echte metingen samen en blijft leeg zonder."""
    monitor = get_performance_monitor()

    # Verse monitor (de fixture isoleert hem): een lege samenvatting mag niet
    # als "geslaagd" tellen, dus dit is het startpunt en geen einddoel.
    assert monitor.get_summary() == {}

    operatie = f"def519_meting_{uuid.uuid4().hex[:8]}"
    for _ in range(2):
        start_timing(operatie)
        await asyncio.sleep(0)
        stop_timing(operatie)

    samenvatting = monitor.get_summary()
    assert set(samenvatting) == {operatie}

    stats = samenvatting[operatie]
    assert set(stats) == {"count", "total", "average", "min", "max"}
    assert stats["count"] == 2
    metingen = monitor.metrics[operatie]
    assert len(metingen) == 2
    assert stats["total"] == pytest.approx(sum(metingen))
    assert stats["average"] == pytest.approx(sum(metingen) / 2)
    assert stats["min"] == pytest.approx(min(metingen))
    assert stats["max"] == pytest.approx(max(metingen))
    assert stats["min"] <= stats["average"] <= stats["max"]

    # Een timer die nooit gestart is levert 0.0 op en vervuilt de samenvatting
    # niet — de samenvatting telt dus alleen echte metingen.
    assert stop_timing("def519_nooit_gestart") == 0.0
    assert set(monitor.get_summary()) == {operatie}
