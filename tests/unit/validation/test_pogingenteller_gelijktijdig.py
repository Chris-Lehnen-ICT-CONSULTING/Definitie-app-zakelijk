"""De pogingenteller van ESS-03/INT-03 blijft juist als de beoordelingen gelijktijdig lopen.

`_Pogingenteller` telt herhaalde transportpogingen via de logs van de
onderliggende lagen en zet die loggers tijdens de aanroep tijdelijk op INFO.
Sinds CON-02, ESS-03 en INT-03 gelijktijdig lopen (validatiebudget) zijn er
meerdere tellers tegelijk actief op dezelfde loggers. Vastgelegd:

* elke teller telt alleen de herhalingsmeldingen van zijn eigen aanroep —
  niet die van de andere beoordeling en niet die van CON-02;
* na afloop staan de loggers exact op hun oorspronkelijke niveau, ongeacht
  welke beoordeling het eerst klaar is, en hangt er geen teller meer aan.

Echte `Ess03AssessmentService` en `Int03AssessmentService` onder de echte
`ValidationOrchestratorV2`; alleen de AI-grens en CON-02 zijn fakes.
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from copy import deepcopy
from typing import Any

import pytest

from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2
from services.validation.ess03_assessment_service import (
    _RETRY_LOGGERS,
    Ess03AssessmentService,
    _Pogingenteller,
)
from services.validation.int03_assessment_service import Int03AssessmentService
from services.validation.interfaces import CONTRACT_VERSION, ValidationContext
from tests.fixtures.def743_fakes import (
    BEGRIP,
    BRONNEN,
    JUR,
    ORG,
    TEKST,
    WET,
    FakeBronbeoordeling,
)
from tests.fixtures.def772_fakes import INT03_PROMPTMARKER, FakeModelgrens, FakeRouter
from ui.helpers.async_bridge import run_async

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]

HERHAALMELDING = "Retrying request to /v1/messages in 0.5 seconds"
SDK_LOGGER = "anthropic._base_client"


def _meld_herhaling() -> None:
    logging.getLogger(SDK_LOGGER).info(HERHAALMELDING)


class Grens(FakeModelgrens):
    """Gedeelde AI-grens: ESS-03 meldt één herhaling, INT-03 twee; elk duurt
    zo lang als opgegeven, zodat de volgorde van afronden te kiezen is."""

    def __init__(self, *, ess03_duur: float, int03_duur: float) -> None:
        super().__init__(definitie=TEKST, scenario="pass")
        self.ess03_duur = ess03_duur
        self.int03_duur = int03_duur
        self.klaar: list[str] = []

    async def generate_definition(self, prompt: str, **kwargs: Any):
        if INT03_PROMPTMARKER in str(prompt):
            _meld_herhaling()
            await asyncio.sleep(self.int03_duur / 2)
            _meld_herhaling()
            await asyncio.sleep(self.int03_duur / 2)
            self.klaar.append("INT-03")
        else:
            _meld_herhaling()
            await asyncio.sleep(self.ess03_duur)
            self.klaar.append("ESS-03")
        return await super().generate_definition(prompt, **kwargs)


class LuidruchtigeBron(FakeBronbeoordeling):
    """CON-02 die tijdens de andere beoordelingen drie herhalingen meldt."""

    async def assess(self, *args: Any, **kwargs: Any):
        for _ in range(3):
            await asyncio.sleep(0.02)
            _meld_herhaling()
        return await super().assess(*args, **kwargs)


class Opnemer:
    async def validate_definition(self, **kwargs: Any) -> dict[str, Any]:
        self.ontvangen = deepcopy(kwargs.get("context"))
        return {"version": CONTRACT_VERSION, "system": {}}


@pytest.fixture
def oorspronkelijke_niveaus():
    """Vaste beginniveaus (hoger dan INFO of NOTSET), na de test hersteld."""
    loggers = {naam: logging.getLogger(naam) for naam in _RETRY_LOGGERS}
    vooraf = {naam: log.level for naam, log in loggers.items()}
    loggers["anthropic._base_client"].setLevel(logging.WARNING)
    loggers["openai._base_client"].setLevel(logging.ERROR)
    loggers["utils.async_api"].setLevel(logging.NOTSET)
    try:
        yield {naam: log.level for naam, log in loggers.items()}
    finally:
        for naam, log in loggers.items():
            log.setLevel(vooraf[naam])


@pytest.mark.parametrize(
    ("ess03_duur", "int03_duur", "volgorde"),
    [
        pytest.param(0.05, 0.2, ["ESS-03", "INT-03"], id="ess03-eerst-klaar"),
        pytest.param(0.2, 0.05, ["INT-03", "ESS-03"], id="int03-eerst-klaar"),
    ],
)
async def test_gelijktijdige_tellers_tellen_eigen_herhalingen_en_herstellen_niveaus(
    oorspronkelijke_niveaus, ess03_duur, int03_duur, volgorde
):
    grens = Grens(ess03_duur=ess03_duur, int03_duur=int03_duur)
    toetsing = Opnemer()
    orch = ValidationOrchestratorV2(
        toetsing,
        source_assessment_service=LuidruchtigeBron(),
        ess03_assessment_service=Ess03AssessmentService(
            grens, model_router=FakeRouter()
        ),
        int03_assessment_service=Int03AssessmentService(
            grens, model_router=FakeRouter()
        ),
    )
    context = ValidationContext(
        metadata={
            "organisatorische_context": list(ORG),
            "juridische_context": list(JUR),
            "wettelijke_basis": list(WET),
            "provenance_sources": deepcopy(BRONNEN),
        }
    )

    begin = time.monotonic()
    result = await orch.validate_text(BEGRIP, TEKST, context=context)
    duur = time.monotonic() - begin

    # Werkelijk gelijktijdig, in de gekozen volgorde klaar.
    assert grens.klaar == volgorde
    assert duur < ess03_duur + int03_duur
    # Loggers exact terug op hun oorspronkelijke niveau, zonder achtergebleven
    # teller.
    for naam, niveau in oorspronkelijke_niveaus.items():
        log = logging.getLogger(naam)
        assert log.level == niveau, naam
        assert not [f for f in log.filters if isinstance(f, _Pogingenteller)], naam
    # Per dienst alleen de eigen herhalingen: ESS-03 één, INT-03 twee;
    # die van CON-02 en van de andere beoordeling tellen niet mee.
    ess03 = result["ess03_assessment"]["attribution"]
    int03 = toetsing.ontvangen["int03_assessment"]["attribution"]
    assert (ess03["retries_observed"], ess03["attempts_observed"]) == (1, 2)
    assert (int03["retries_observed"], int03["attempts_observed"]) == (2, 3)


async def test_losse_teller_telt_alleen_binnen_zijn_eigen_taak(
    oorspronkelijke_niveaus,
):
    """Een melding uit een andere, eerder gestarte taak (zoals CON-02) telt
    niet; een melding uit een werkthread van de eigen aanroep
    (`asyncio.to_thread`, zoals de nabewerking van de AI-laag) wel."""

    async def _andere_taak() -> None:
        await asyncio.sleep(0.01)
        _meld_herhaling()

    andere = asyncio.create_task(_andere_taak())
    teller = _Pogingenteller()
    with teller:
        _meld_herhaling()
        await asyncio.to_thread(_meld_herhaling)
        await andere

    assert teller.attributie() == {"attempts_observed": 3, "retries_observed": 2}
    for naam, niveau in oorspronkelijke_niveaus.items():
        assert logging.getLogger(naam).level == niveau, naam


async def test_tweede_module_exemplaar_hergebruikt_het_pogingenfilter(
    oorspronkelijke_niveaus, monkeypatch
):
    """Herladen of een tweede exemplaar van de module hangt geen tweede
    filter aan de loggers en telt via hetzelfde filter."""
    import importlib.util
    import sys

    from services.validation import ess03_assessment_service as origineel

    naam = "ess03_assessment_service_tweede_exemplaar"
    spec = importlib.util.spec_from_file_location(naam, origineel.__file__)
    assert spec is not None and spec.loader is not None
    tweede = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, naam, tweede)
    spec.loader.exec_module(tweede)

    assert tweede._DISPATCHER is origineel._DISPATCHER
    for lognaam in _RETRY_LOGGERS:
        filters = logging.getLogger(lognaam).filters
        assert [type(f).__name__ for f in filters].count("_Pogingendispatcher") == 1

    teller = tweede._Pogingenteller()
    with teller:
        _meld_herhaling()
    assert teller.attributie() == {"attempts_observed": 2, "retries_observed": 1}


async def test_afsluitende_teller_in_andere_thread_laat_geen_melding_vallen(
    oorspronkelijke_niveaus,
):
    """Twee validaties in twee `run_async`-werkthreads (de UI-brug).

    Gecontroleerde interleaving: B logt een eigen herhaling en staat met dat
    record midden in de filterketen van de logger precies op het moment dat
    A zijn teller afsluit. Een filterlijst die tijdens die iteratie krimpt,
    laat B's telling overslaan; die melding hoort toch bij B te tellen. B
    logt daarna nog één herhaling via `asyncio.to_thread`: ook binnen de
    werkthread van `run_async` reist de actieve teller mee naar de eigen
    nabewerking. A ziet geen van beide.
    """
    sdk = logging.getLogger(SDK_LOGGER)
    a_actief = threading.Event()
    b_in_filterketen = threading.Event()
    a_afgesloten = threading.Event()

    class Sluis(logging.Filter):
        """Houdt B's eerste record in de filterketen vast tot A is afgesloten."""

        def filter(self, record: logging.LogRecord) -> bool:
            if "[B]" in record.getMessage() and not b_in_filterketen.is_set():
                b_in_filterketen.set()
                a_afgesloten.wait(5)
            return True

    sluis = Sluis()

    async def aanroep_a() -> dict[str, int]:
        teller = _Pogingenteller()
        with teller:
            # De sluis komt ná wat A registreerde en vóór wat B registreert.
            sdk.addFilter(sluis)
            a_actief.set()
            assert b_in_filterketen.wait(5)
        a_afgesloten.set()
        return teller.attributie()

    async def aanroep_b() -> dict[str, int]:
        assert a_actief.wait(5)
        teller = _Pogingenteller()
        with teller:
            sdk.info(f"{HERHAALMELDING} [B]")
            await asyncio.to_thread(_meld_herhaling)
        return teller.attributie()

    uitkomsten: dict[str, Any] = {}

    def draai(naam: str, aanroep: Any) -> None:
        try:
            uitkomsten[naam] = run_async(aanroep(), timeout=10)
        except BaseException as exc:  # zichtbaar maken in de assert hieronder
            uitkomsten[naam] = exc

    def beide() -> None:
        threads = [
            threading.Thread(target=draai, args=("A", aanroep_a)),
            threading.Thread(target=draai, args=("B", aanroep_b)),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(15)

    try:
        await asyncio.to_thread(beide)
    finally:
        sdk.removeFilter(sluis)

    assert b_in_filterketen.is_set() and a_afgesloten.is_set()
    assert uitkomsten == {
        "A": {"attempts_observed": 1, "retries_observed": 0},
        "B": {"attempts_observed": 3, "retries_observed": 2},
    }
    for naam, niveau in oorspronkelijke_niveaus.items():
        log = logging.getLogger(naam)
        assert log.level == niveau, naam
        # Eén blijvend pogingenfilter per logger, geen per-aanroepfilters.
        assert [type(f).__name__ for f in log.filters].count(
            "_Pogingendispatcher"
        ) == 1, naam
        assert not [f for f in log.filters if isinstance(f, _Pogingenteller)], naam
