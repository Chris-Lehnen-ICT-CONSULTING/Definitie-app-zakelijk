"""De drie AI-beoordelingen (CON-02, ESS-03, INT-03) lopen gelijktijdig.

`ValidationOrchestratorV2` verkrijgt per validatie drie onafhankelijke
AI-beoordelingen. Na elkaar ge-await telden hun looptijden op (gemeten:
CON-02 44 s + ESS-03 11 s + INT-03 >27 s) en overschreed één generatie het
budget van 120 s. Gelijktijdig is de duur het maximum, niet de som.

Alleen de gelijktijdigheid verandert. Deze tests leggen vast dat:

* de duur ≈ het maximum is en de drie beoordelingen werkelijk overlappen;
* de uitkomst (context naar de toetsing, violations, scores, teruggegeven
  beoordelingen) gelijk is aan de oude sequentiële route, die hier letterlijk
  als referentie is overgenomen;
* een fout of timeout binnen één beoordeling (door de methode zelf afgevangen)
  de andere niet raakt; een fout die de methode uitloopt geeft dezelfde
  degraded uitkomst als sequentieel — bij meerdere wint de eerste in de oude
  volgorde — en de nog lopende beoordelingen worden geannuleerd;
* annulering van de buitenste taak (budget op) alle drie annuleert zonder
  achterblijvende taken, en de generatiedeadline in elke beoordeling geldt.
"""

from __future__ import annotations

import asyncio
import time
from copy import deepcopy
from typing import Any

import pytest

from services.interfaces import Definition
from services.null_repository import NullDefinitionRepository
from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2
from services.validation.interfaces import CONTRACT_VERSION, ValidationContext
from services.validation.mappers import (
    create_degraded_result,
    ensure_schema_compliance,
)
from services.validation.modular_validation_service import ModularValidationService
from tests.fixtures.def743_fakes import (
    BEGRIP,
    BRONNEN,
    JUR,
    ORG,
    TEKST,
    WET,
    FakeBronbeoordeling,
)
from tests.fixtures.def766_fakes import FakeEss03Assessor
from tests.fixtures.def772_fakes import FakeInt03Assessor
from toetsregels.manager import get_toetsregel_manager
from utils.generatie_deadline import generatie_deadline, huidige_generatie_deadline

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]

CORRELATION_ID = "00000000-0000-4000-8000-000000000843"
METADATA = {
    "organisatorische_context": list(ORG),
    "juridische_context": list(JUR),
    "wettelijke_basis": list(WET),
    "provenance_sources": deepcopy(BRONNEN),
    "peildatum": "2026-09-15",
    "toelichting": "Synthetische toelichting.",
}


class Vertraagd:
    """Laat een fake-beoordelaar `vertraging` seconden duren en legt vast
    wanneer hij start, eindigt of wordt geannuleerd. Overige attributen
    (`binding`, `max_passage_chars`, `calls`) komen van de fake zelf."""

    def __init__(self, naam: str, fake: Any, vertraging: float) -> None:
        self._naam = naam
        self._fake = fake
        self._vertraging = vertraging
        self.start: float | None = None
        self.eind: float | None = None
        self.geannuleerd = False
        self.deadline: float | None = None

    def __getattr__(self, attribuut: str) -> Any:
        return getattr(self._fake, attribuut)

    async def assess(self, *args: Any, **kwargs: Any) -> Any:
        self.start = time.monotonic()
        self.deadline = huidige_generatie_deadline()
        try:
            await asyncio.sleep(self._vertraging)
        except asyncio.CancelledError:
            self.geannuleerd = True
            raise
        try:
            return await self._fake.assess(*args, **kwargs)
        finally:
            self.eind = time.monotonic()


class Opnemer:
    """Echte toetsing die de ontvangen context bewaart (diepe kopie)."""

    def __init__(self, dienst: Any) -> None:
        self._dienst = dienst
        self.ontvangen: dict[str, Any] | None = None

    def __getattr__(self, attribuut: str) -> Any:
        return getattr(self._dienst, attribuut)

    async def validate_definition(self, **kwargs: Any) -> Any:
        self.ontvangen = deepcopy(kwargs.get("context"))
        return await self._dienst.validate_definition(**kwargs)


class SnelleToetsing:
    """Toetsing zonder regelset: de duurmeting meet alleen de beoordelingen."""

    async def validate_definition(self, **_kwargs: Any) -> dict[str, Any]:
        return {"version": CONTRACT_VERSION, "system": {}}


def _toetsing() -> Opnemer:
    return Opnemer(
        ModularValidationService(
            get_toetsregel_manager(), repository=NullDefinitionRepository()
        )
    )


def _orchestrator(
    *,
    bron: Any,
    ess03: Any,
    int03: Any,
    toetsing: Any | None = None,
) -> ValidationOrchestratorV2:
    return ValidationOrchestratorV2(
        toetsing or _toetsing(),
        source_assessment_service=bron,
        ess03_assessment_service=ess03,
        int03_assessment_service=int03,
    )


def _definitie() -> Definition:
    return Definition(
        begrip=BEGRIP,
        definitie=TEKST,
        toelichting="Toelichting uit het record.",
        ontologische_categorie="type",
        organisatorische_context=list(ORG),
        juridische_context=list(JUR),
        wettelijke_basis=list(WET),
        metadata={
            "provenance_sources": deepcopy(BRONNEN),
            "peildatum": "2026-09-15",
        },
    )


def _context() -> ValidationContext:
    return ValidationContext(correlation_id=CORRELATION_ID, metadata=deepcopy(METADATA))


# --- de oude sequentiële route, letterlijk overgenomen als referentie ------------


async def _beoordeel_sequentieel(orch, begrip, tekst, context_dict, cid):
    assessment = await orch._beoordeel_bronnen(begrip, tekst, context_dict, cid)
    if assessment is not None:
        context_dict["source_assessment"] = assessment
    telbaarheid = await orch._beoordeel_telbaarheid(begrip, tekst, context_dict, cid)
    if telbaarheid is not None:
        context_dict["ess03_assessment"] = telbaarheid
    verwijzingen = await orch._beoordeel_verwijzingen(begrip, tekst, context_dict, cid)
    if verwijzingen is not None:
        context_dict["int03_assessment"] = verwijzingen
    await orch._beoordeel_int02(begrip, context_dict, cid)
    return assessment, telbaarheid


async def _referentie_definition(orch, definitie, context):
    cid = str(context.correlation_id)
    ctx = orch._enrich_context_with_definition_fields(
        orch._context_dict(context), definitie
    )
    assessment, telbaarheid = await _beoordeel_sequentieel(
        orch, definitie.begrip, ctx["record_text"], ctx, cid
    )
    result = await orch.validation_service.validate_definition(
        begrip=definitie.begrip,
        text=definitie.definitie,
        ontologische_categorie=definitie.ontologische_categorie,
        context=ctx,
    )
    return orch._met_beoordelingen(
        ensure_schema_compliance(result, cid), assessment, telbaarheid
    )


async def _referentie_text(orch, begrip, tekst, categorie, context):
    cid = str(context.correlation_id)
    ctx = dict(orch._context_dict(context) or {})
    ctx["record_text"] = tekst
    ctx["ontologische_categorie"] = categorie
    assessment, telbaarheid = await _beoordeel_sequentieel(
        orch, begrip, tekst, ctx, cid
    )
    result = await orch.validation_service.validate_definition(
        begrip=begrip, text=tekst, ontologische_categorie=categorie, context=ctx
    )
    return orch._met_beoordelingen(
        ensure_schema_compliance(result, cid), assessment, telbaarheid
    )


_VLUCHTIG = ("timestamp", "validated_at", "duration_ms", "processing_time_ms")


def _stabiel(waarde: Any) -> Any:
    """Uitkomst zonder tijdstempels/duur, zodat twee runs vergelijkbaar zijn."""
    if isinstance(waarde, dict):
        return {k: _stabiel(v) for k, v in waarde.items() if k not in _VLUCHTIG}
    if isinstance(waarde, list):
        return [_stabiel(v) for v in waarde]
    return waarde


def _fakes(scenario_bron="pass", scenario_ess="pass", scenario_int="pass", **fout):
    return {
        "bron": FakeBronbeoordeling(scenario=scenario_bron),
        "ess03": FakeEss03Assessor(scenario=scenario_ess, fout=fout.get("ess03")),
        "int03": FakeInt03Assessor(scenario=scenario_int, fout=fout.get("int03")),
    }


def _vertraagd(fakes, bron=0.3, ess03=0.2, int03=0.1):
    return {
        "bron": Vertraagd("CON-02", fakes["bron"], bron),
        "ess03": Vertraagd("ESS-03", fakes["ess03"], ess03),
        "int03": Vertraagd("INT-03", fakes["int03"], int03),
    }


def _geen_andere_taken() -> list[asyncio.Task]:
    huidige = asyncio.current_task()
    return [t for t in asyncio.all_tasks() if t is not huidige and not t.done()]


# --- 1. duur = maximum, niet de som ---------------------------------------------


@pytest.mark.parametrize("route", ["definition", "text"])
async def test_duur_is_het_maximum_en_de_beoordelingen_overlappen(route):
    diensten = _vertraagd(_fakes())
    orch = _orchestrator(**diensten, toetsing=SnelleToetsing())

    begin = time.monotonic()
    if route == "definition":
        await orch.validate_definition(_definitie(), context=_context())
    else:
        await orch.validate_text(BEGRIP, TEKST, "type", context=_context())
    duur = time.monotonic() - begin

    starts = [d.start for d in diensten.values()]
    eindes = [d.eind for d in diensten.values()]
    assert None not in starts and None not in eindes
    # Overlap, onafhankelijk van machinebelasting: alle drie zijn gestart
    # voordat de eerste klaar was.
    assert max(starts) < min(eindes)
    # Som = 0,6 s; maximum = 0,3 s.
    assert 0.3 <= duur < 0.55, duur


# --- 2. uitkomst identiek aan de sequentiële route ------------------------------


SCENARIO_S = [
    pytest.param(("pass", "pass", "pass"), id="alles-pass"),
    pytest.param(("authority_fail", "insufficient", "fail"), id="drie-afwijkingen"),
    pytest.param(("error", "error", "insufficient"), id="dienst-meldt-fout"),
]


@pytest.mark.parametrize("scenario", SCENARIO_S)
@pytest.mark.parametrize("route", ["definition", "text"])
async def test_uitkomst_gelijk_aan_sequentiele_route(route, scenario):
    referentie_orch = _orchestrator(**_fakes(*scenario))
    parallel_orch = _orchestrator(**_vertraagd(_fakes(*scenario)))

    if route == "definition":
        verwacht = await _referentie_definition(
            referentie_orch, _definitie(), _context()
        )
        uitkomst = await parallel_orch.validate_definition(
            _definitie(), context=_context()
        )
    else:
        verwacht = await _referentie_text(
            referentie_orch, BEGRIP, TEKST, "type", _context()
        )
        uitkomst = await parallel_orch.validate_text(
            BEGRIP, TEKST, "type", context=_context()
        )

    # Dezelfde context naar de toetsing (inhoud; de dict-volgorde is niet
    # betekenisdragend), dus dezelfde beoordelingen en bindingen.
    assert (
        parallel_orch.validation_service.ontvangen
        == referentie_orch.validation_service.ontvangen
    )
    # En dezelfde uitkomst: violations in dezelfde volgorde, scores,
    # teruggegeven beoordelingen.
    assert [v.get("rule_id") for v in uitkomst["violations"]] == [
        v.get("rule_id") for v in verwacht["violations"]
    ]
    assert _stabiel(uitkomst) == _stabiel(verwacht)


# --- 3. fouten en timeouts per beoordeling --------------------------------------


@pytest.mark.parametrize(
    "fout",
    [
        pytest.param({"ess03": RuntimeError("synthetische storing")}, id="ess03"),
        pytest.param({"int03": TimeoutError()}, id="int03-timeout"),
    ],
)
async def test_afgevangen_fout_in_een_beoordeling_raakt_de_andere_niet(fout):
    referentie_orch = _orchestrator(**_fakes(**fout))
    diensten = _vertraagd(_fakes(**fout))
    parallel_orch = _orchestrator(**diensten)

    verwacht = await _referentie_definition(referentie_orch, _definitie(), _context())
    uitkomst = await parallel_orch.validate_definition(_definitie(), context=_context())

    # De andere twee zijn volledig doorlopen, niemand is geannuleerd.
    assert all(d.eind is not None and not d.geannuleerd for d in diensten.values())
    assert _stabiel(uitkomst) == _stabiel(verwacht)
    status = {
        "ess03": uitkomst["ess03_assessment"]["status"],
        "int03": parallel_orch.validation_service.ontvangen["int03_assessment"][
            "status"
        ],
    }
    (welke,) = fout
    assert status[welke] == "error"


async def _ontsnapt(seconden: float, melding: str):
    await asyncio.sleep(seconden)
    raise RuntimeError(melding)


async def test_ontsnappende_fout_geeft_dezelfde_degraded_uitkomst_en_annuleert_rest(
    monkeypatch,
):
    """Een fout die de beoordelingsmethode zelf niet afvangt, liep sequentieel
    naar de buitenste `except` (degraded result). Dat blijft zo; de nog
    lopende beoordelingen worden geannuleerd en er blijft geen taak hangen."""

    async def kapot(self, *_a, **_k):
        return await _ontsnapt(0.05, "ESS-03 ontsnapt")

    # Sequentieel liep de fout uit de beoordelingen naar de buitenste
    # `except`, die er een degraded result van maakt.
    referentie_orch = _orchestrator(**_fakes())
    monkeypatch.setattr(
        referentie_orch, "_beoordeel_telbaarheid", kapot.__get__(referentie_orch)
    )
    with pytest.raises(RuntimeError, match="ESS-03 ontsnapt"):
        await _referentie_definition(referentie_orch, _definitie(), _context())
    verwacht = create_degraded_result(
        error="ESS-03 ontsnapt", correlation_id=CORRELATION_ID, begrip=BEGRIP
    )

    diensten = _vertraagd(_fakes(), bron=0.1, ess03=0.0, int03=1.0)
    parallel_orch = _orchestrator(**diensten)
    monkeypatch.setattr(
        parallel_orch, "_beoordeel_telbaarheid", kapot.__get__(parallel_orch)
    )
    uitkomst = await parallel_orch.validate_definition(_definitie(), context=_context())

    assert _stabiel(uitkomst) == _stabiel(verwacht)
    # CON-02 (eerder in de volgorde) liep volledig door, net als sequentieel;
    # INT-03 (later) is geannuleerd in plaats van door te lopen.
    assert diensten["bron"].eind is not None
    assert diensten["int03"].geannuleerd and diensten["int03"].eind is None
    assert _geen_andere_taken() == []


async def test_bij_meerdere_fouten_wint_de_eerste_in_de_oude_volgorde(monkeypatch):
    """Sequentieel bereikte een fout in CON-02 de aanroeper, ook als ESS-03
    óók zou falen. Gelijktijdig faalt ESS-03 eerder in de tijd; toch moet de
    CON-02-fout de uitkomst bepalen."""

    async def bron_kapot(self, *_a, **_k):
        return await _ontsnapt(0.1, "CON-02 ontsnapt")

    async def ess_kapot(self, *_a, **_k):
        return await _ontsnapt(0.0, "ESS-03 ontsnapt")

    orch = _orchestrator(**_vertraagd(_fakes()))
    monkeypatch.setattr(orch, "_beoordeel_bronnen", bron_kapot.__get__(orch))
    monkeypatch.setattr(orch, "_beoordeel_telbaarheid", ess_kapot.__get__(orch))

    uitkomst = await orch.validate_definition(_definitie(), context=_context())

    assert uitkomst["system"]["error"] == "CON-02 ontsnapt"
    assert _geen_andere_taken() == []


# --- 4. annulering van buitenaf (budget op) -------------------------------------


@pytest.mark.parametrize("route", ["definition", "text"])
async def test_budget_op_annuleert_alle_drie_zonder_hangende_taken(route):
    diensten = _vertraagd(_fakes(), bron=5.0, ess03=5.0, int03=5.0)
    orch = _orchestrator(**diensten)
    if route == "definition":
        aanroep = orch.validate_definition(_definitie(), context=_context())
    else:
        aanroep = orch.validate_text(BEGRIP, TEKST, "type", context=_context())

    with pytest.raises(TimeoutError):
        await asyncio.wait_for(aanroep, timeout=0.1)

    for naam, dienst in diensten.items():
        assert dienst.start is not None, naam
        assert dienst.geannuleerd, naam
        assert dienst.eind is None, naam
    assert _geen_andere_taken() == []


async def test_generatiedeadline_geldt_in_elke_beoordeling():
    diensten = _vertraagd(_fakes(), bron=0.0, ess03=0.0, int03=0.0)
    orch = _orchestrator(**diensten)

    with generatie_deadline(60) as deadline:
        await orch.validate_definition(_definitie(), context=_context())

    assert [d.deadline for d in diensten.values()] == [deadline] * 3
