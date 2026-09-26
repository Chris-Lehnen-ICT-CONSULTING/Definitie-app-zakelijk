"""DEF-772 WP3: de actieve async wrappers verkrijgen de INT-03-beoordeling standaard.

`ValidationOrchestratorV2.validate_text` en `validate_definition` moeten zélf
een verse verwijzingsbeoordeling verkrijgen via de geïnjecteerde
`Int03AssessmentService`, haar mét de actuele binding aan de evaluator
meegeven (`int03_assessment`, `int03_binding` in de servicecontext). Een door
de aanroeper meegegeven `int03_assessment` is nooit een kortere weg naar een
positief oordeel. Zonder tekst wordt er geen model aangeroepen (een lege term
is geen belemmering: de term is ondersteunend); zonder dienst is de
beoordeling expliciet `unavailable`; een dienstfout is een technische fout —
nooit stil een pass. Ook de DI-keten (DefinitionOrchestratorV2,
ServiceContainer) injecteert de dienst werkelijk. Het resultaatcontract
(2.2.0) krijgt geen nieuw top-level veld: de payload reist in `rule_results`.

Reviewcorrecties (review-codex-wp3-v1, dispositie v3): op de recordroute is
de actuele recordtoelichting gezaghebbend — ook leeggemaakt — boven
verouderde aanroepermetadata, zodat een oude beoordeling/cache niet blijft
gelden (R1); afgewezen modelcitaten en uitzonderingsteksten bereiken op de
volledige route geen log of foutmelding (R2).
"""

from __future__ import annotations

import logging
from copy import deepcopy
from unittest.mock import AsyncMock

import pytest

from domain.int03.contract import CONTRACTVERSIE, bereken_int03_vingerafdruk
from services.interfaces import Definition
from services.null_repository import NullDefinitionRepository
from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2
from services.validation.int03_assessment_service import Int03AssessmentService
from services.validation.interfaces import CONTRACT_VERSION, ValidationContext
from services.validation.modular_validation_service import ModularValidationService
from tests.fixtures.def772_fakes import (
    BINDING,
    FakeInt03Assessor,
    FakeModelgrens,
    FakeRouter,
    bouw_ruwe_modeluitvoer,
)
from toetsregels.manager import get_toetsregel_manager

pytestmark = [pytest.mark.unit]

BEGRIP = "proefbegrip"
TEKST = "persoon die wordt verdacht van een strafbaar feit"
CONTEXT = {
    "organisatorische_context": ["Synthetische Organisatie"],
    "juridische_context": [],
    "wettelijke_basis": [],
}
#: Synthetische gevoelige inhoud die een model zou kunnen terugkaatsen (R2).
GEVOELIG = "Testpersoon Voorbeeldnaam heeft diagnose Voorbeeldziekte"
GEVOELIGE_MARKERS = ("Voorbeeldnaam", "Voorbeeldziekte")


def _service():
    """Validatiedubbel dat de ontvangen context bewaart en een dict teruggeeft."""
    service = AsyncMock()

    async def _bewaar(*_a, **kwargs):
        service.received = deepcopy(kwargs.get("context") or {})
        return {"version": CONTRACT_VERSION, "system": {}}

    service.validate_definition.side_effect = _bewaar
    return service


async def test_validate_text_verkrijgt_verse_beoordeling_met_binding():
    service, assessor = _service(), FakeInt03Assessor(scenario="pass")
    orch = ValidationOrchestratorV2(service, int03_assessment_service=assessor)
    metadata = {
        **CONTEXT,
        "toelichting": "Synthetische toelichting.",
        # Een meegegeven beoordeling is nooit de bron van waarheid.
        "int03_assessment": {"status": "assessed", "judgment": {"verdict": "pass"}},
    }
    before = deepcopy(metadata)

    result = await orch.validate_text(
        BEGRIP, TEKST, context=ValidationContext(metadata=metadata)
    )

    assert metadata == before
    (call,) = assessor.calls
    assert call["begrip"] == BEGRIP
    assert call["tekst"] == TEKST
    assert call["toelichting"] == "Synthetische toelichting."
    assert call["contexten"]["organisatorische_context"] == ["Synthetische Organisatie"]
    doorgegeven = service.received["int03_assessment"]
    assert doorgegeven["status"] == "assessed"
    assert doorgegeven["contract_version"] == CONTRACTVERSIE
    assert doorgegeven["fingerprint"] == bereken_int03_vingerafdruk(
        BEGRIP, TEKST, CONTEXT, "Synthetische toelichting."
    )
    assert doorgegeven["attribution"]["model"] == "fake-int03-model"
    assert service.received["int03_binding"] == BINDING.als_dict()
    # Geen nieuw top-level veld: de actuele contractversie is 2.2.0 (DEF-771);
    # die beschrijft ook assessment/signals in rule_results['INT-03'].
    assert result["version"] == CONTRACT_VERSION == "2.2.0"
    assert "int03_assessment" not in result


async def test_validate_definition_gebruikt_recordtekst_en_recordtoelichting():
    # Zelfde leesvolgorde als ESS-03 (`intentie_uit_context`): zonder
    # aanroeperwaarde komt de toelichting uit het record (`definition`).
    service, assessor = _service(), FakeInt03Assessor(scenario="pass")
    orch = ValidationOrchestratorV2(service, int03_assessment_service=assessor)
    definitie = Definition(
        begrip=BEGRIP,
        definitie=TEKST,
        toelichting="Toelichting uit het record.",
        organisatorische_context=list(CONTEXT["organisatorische_context"]),
        metadata={"version_number": 3},
    )
    await orch.validate_definition(definitie)
    (call,) = assessor.calls
    assert call["tekst"] == TEKST
    assert call["toelichting"] == "Toelichting uit het record."
    assert service.received["int03_assessment"]["fingerprint"] == (
        bereken_int03_vingerafdruk(
            BEGRIP, TEKST, CONTEXT, "Toelichting uit het record."
        )
    )


# --- R1: de actuele recordtoelichting is gezaghebbend op de recordroute --------


def _record(toelichting: str | None) -> Definition:
    return Definition(
        begrip=BEGRIP,
        definitie=TEKST,
        toelichting=toelichting,
        organisatorische_context=list(CONTEXT["organisatorische_context"]),
        metadata={"version_number": 4},
    )


#: Verouderde aanroepermetadata: dezelfde oude toelichting op beide vindplaatsen.
VEROUDERDE_METADATA = {
    "toelichting": "OUDE BETEKENIS",
    "definition": {"toelichting": "OUDE BETEKENIS"},
}


async def test_recordroute_recordtoelichting_wint_van_verouderde_metadata():
    service, assessor = _service(), FakeInt03Assessor(scenario="pass")
    orch = ValidationOrchestratorV2(service, int03_assessment_service=assessor)

    await orch.validate_definition(
        _record("NIEUWE BETEKENIS"),
        ValidationContext(metadata=deepcopy(VEROUDERDE_METADATA)),
    )

    (call,) = assessor.calls
    assert call["toelichting"] == "NIEUWE BETEKENIS"
    assert service.received["toelichting"] == "NIEUWE BETEKENIS"
    assert service.received["definition"]["toelichting"] == "NIEUWE BETEKENIS"
    assert service.received["int03_assessment"]["fingerprint"] == (
        bereken_int03_vingerafdruk(BEGRIP, TEKST, CONTEXT, "NIEUWE BETEKENIS")
    )


@pytest.mark.parametrize("leeg", [None, "", "   "], ids=["none", "leeg", "spaties"])
async def test_recordroute_leeggemaakte_recordtoelichting_wint_van_verouderde_metadata(
    leeg,
):
    # Leegmaken is een echte wijziging: de oude bedoeling keert niet terug via
    # aanroepermetadata, op geen van beide vindplaatsen.
    service, assessor = _service(), FakeInt03Assessor(scenario="pass")
    orch = ValidationOrchestratorV2(service, int03_assessment_service=assessor)

    await orch.validate_definition(
        _record(leeg), ValidationContext(metadata=deepcopy(VEROUDERDE_METADATA))
    )

    (call,) = assessor.calls
    assert call["toelichting"] is None
    assert "toelichting" not in service.received
    assert "toelichting" not in service.received.get("definition", {})
    assert service.received["int03_assessment"]["fingerprint"] == (
        bereken_int03_vingerafdruk(BEGRIP, TEKST, CONTEXT, None)
    )


async def test_gewijzigde_recordtoelichting_omzeilt_de_cache_van_de_echte_dienst():
    """Reproductie van reviewbevinding R1 met de echte dienst: toets met
    toelichting OUD, wijzig het record naar NIEUW en behoud de oude
    contextmetadata. De tweede toetsing moet opnieuw naar het model."""
    service, ai = _service(), FakeModelgrens(definitie=TEKST, scenario="pass")
    dienst = Int03AssessmentService(ai, model_router=FakeRouter())
    orch = ValidationOrchestratorV2(service, int03_assessment_service=dienst)

    await orch.validate_definition(
        _record("OUDE BETEKENIS"), ValidationContext(metadata={})
    )
    eerste = service.received["int03_assessment"]
    await orch.validate_definition(
        _record("NIEUWE BETEKENIS"),
        ValidationContext(metadata=deepcopy(VEROUDERDE_METADATA)),
    )
    tweede = service.received["int03_assessment"]

    assert len(ai.int03_calls) == 2
    assert "NIEUWE BETEKENIS" in ai.int03_calls[1]["prompt"]
    assert "OUDE BETEKENIS" not in ai.int03_calls[1]["prompt"]
    assert eerste["status"] == tweede["status"] == "assessed"
    assert tweede["attribution"]["cached"] is False
    assert tweede["fingerprint"] != eerste["fingerprint"]
    assert tweede["fingerprint"] == bereken_int03_vingerafdruk(
        BEGRIP, TEKST, CONTEXT, "NIEUWE BETEKENIS"
    )


async def test_zonder_tekst_geen_modelaanroep_zonder_term_wel():
    service, assessor = _service(), FakeInt03Assessor()
    orch = ValidationOrchestratorV2(service, int03_assessment_service=assessor)
    await orch.validate_text(BEGRIP, "   ", context=ValidationContext(metadata={}))
    assert assessor.calls == []
    assert "int03_assessment" not in service.received
    # De term is ondersteunend: zonder term wordt de definitie wél beoordeeld.
    await orch.validate_text("", TEKST, context=ValidationContext(metadata={}))
    assert len(assessor.calls) == 1
    assert service.received["int03_assessment"]["status"] == "assessed"


async def test_zonder_dienst_is_de_beoordeling_expliciet_niet_beschikbaar():
    service = _service()
    orch = ValidationOrchestratorV2(service)
    await orch.validate_text(BEGRIP, TEKST, context=ValidationContext(metadata={}))
    doc = service.received["int03_assessment"]
    assert doc["status"] == "unavailable"
    assert "geen" in doc["reason"].lower()
    assert doc["fingerprint"] == bereken_int03_vingerafdruk(BEGRIP, TEKST, {}, None)


async def test_dienstfout_is_technische_fout_nooit_pass(caplog):
    service = _service()
    assessor = FakeInt03Assessor(fout=RuntimeError(f"storing: {GEVOELIG}"))
    orch = ValidationOrchestratorV2(service, int03_assessment_service=assessor)
    with caplog.at_level(logging.DEBUG):
        await orch.validate_text(BEGRIP, TEKST, context=ValidationContext(metadata={}))
    doc = service.received["int03_assessment"]
    assert doc["status"] == "error"
    assert doc["error"]["type"] == "unknown"
    # R2: alleen het uitzonderingstype is technische metadata; de
    # uitzonderingstekst is onbetrouwbaar en blijft buiten melding en log.
    assert "RuntimeError" in doc["error"]["message"]
    for marker in GEVOELIGE_MARKERS:
        assert marker not in doc["error"]["message"]
        assert marker not in caplog.text
    assert any("DEF-772" in r.getMessage() for r in caplog.records)
    assert doc["fingerprint"] == bereken_int03_vingerafdruk(BEGRIP, TEKST, {}, None)


class _BindingKapot(FakeInt03Assessor):
    """Dienst waarvan de bindingsbepaling zelf faalt (reviewbevinding R2, v2)."""

    def binding(self):
        msg = f"binding: {GEVOELIG}"
        raise RuntimeError(msg)


async def test_bindingsfout_is_technische_fout_zonder_uitzonderingstekst(caplog):
    service, assessor = _service(), _BindingKapot(scenario="pass")
    orch = ValidationOrchestratorV2(service, int03_assessment_service=assessor)
    with caplog.at_level(logging.DEBUG):
        await orch.validate_text(BEGRIP, TEKST, context=ValidationContext(metadata={}))
    doc = service.received["int03_assessment"]
    # Zonder actuele binding kan geen beoordeling als actueel gelden: een
    # technische fout, zonder modelaanroep (kosten) en zonder binding in de
    # context; alleen het uitzonderingstype reist mee.
    assert doc["status"] == "error"
    assert doc["error"]["type"] == "unknown"
    assert "RuntimeError" in doc["error"]["message"]
    assert "binding" in doc["error"]["message"].lower()
    for marker in GEVOELIGE_MARKERS:
        assert marker not in doc["error"]["message"]
        assert marker not in caplog.text
    assert any("DEF-772" in r.getMessage() for r in caplog.records)
    assert assessor.calls == []
    assert "int03_binding" not in service.received


async def test_bindingsfout_bereikt_geen_log_op_de_volledige_route(caplog):
    orch = ValidationOrchestratorV2(
        ModularValidationService(
            get_toetsregel_manager(), repository=NullDefinitionRepository()
        ),
        int03_assessment_service=_BindingKapot(scenario="pass"),
    )
    with caplog.at_level(logging.DEBUG):
        result = await orch.validate_text(
            BEGRIP, TEKST, context=ValidationContext(metadata=dict(CONTEXT))
        )
    assert result["rule_statuses"]["INT-03"] == "error"
    detail = result["rule_results"]["INT-03"]
    for marker in GEVOELIGE_MARKERS:
        assert marker not in caplog.text
        assert marker not in detail["parts"][0]["reason"]
        assert marker not in detail["assessment"]["error"]["message"]
    assert any("INT-03" in r.getMessage() for r in caplog.records)


async def test_dienst_die_geen_document_geeft_is_technische_fout():
    service = _service()

    class Kapot:
        async def assess(self, *a, **k):
            return "geen document"

    orch = ValidationOrchestratorV2(service, int03_assessment_service=Kapot())
    await orch.validate_text(BEGRIP, TEKST, context=ValidationContext(metadata={}))
    doc = service.received["int03_assessment"]
    assert doc["status"] == "error"
    assert "str" in doc["error"]["message"]


# --- R2: geen modelcitaat of uitzonderingstekst in logs op de volledige route --


def _echte_wrapper(ai: FakeModelgrens) -> ValidationOrchestratorV2:
    """Echte ModularValidationService (echte regelset) + echte
    Int03AssessmentService; alleen de modelgrens is een fake."""
    return ValidationOrchestratorV2(
        ModularValidationService(
            get_toetsregel_manager(), repository=NullDefinitionRepository()
        ),
        int03_assessment_service=Int03AssessmentService(ai, model_router=FakeRouter()),
    )


def _verzonnen_passage_met_gevoelige_inhoud() -> dict:
    return bouw_ruwe_modeluitvoer(
        TEKST,
        "pass",
        verwijzingen=[
            {
                "word": "die",
                "passage": GEVOELIG,
                "status": "clear",
                "reading": "verzonnen",
                "candidates": [{"quote": "persoon", "reason": "synthetisch"}],
            }
        ],
    )


@pytest.mark.parametrize(
    ("ai", "foutsoort"),
    [
        (
            FakeModelgrens(
                definitie=TEKST, uitkomsten=[_verzonnen_passage_met_gevoelige_inhoud()]
            ),
            "unverifiable_evidence",
        ),
        (
            FakeModelgrens(
                definitie=TEKST,
                uitkomsten=[
                    {**_verzonnen_passage_met_gevoelige_inhoud(), "verdict": GEVOELIG}
                ],
            ),
            "malformed_response",
        ),
        (FakeModelgrens(definitie=TEKST, fout=RuntimeError(GEVOELIG)), "unknown"),
    ],
    ids=["afgewezen-citaat", "structuurfout-met-modeltekst", "uitzonderingstekst"],
)
async def test_gevoelige_modelinhoud_bereikt_geen_log_op_de_volledige_route(
    ai, foutsoort, caplog
):
    orch = _echte_wrapper(ai)
    with caplog.at_level(logging.DEBUG):
        result = await orch.validate_text(
            BEGRIP, TEKST, context=ValidationContext(metadata=dict(CONTEXT))
        )

    assert result["rule_statuses"]["INT-03"] == "error"
    detail = result["rule_results"]["INT-03"]
    document = detail["assessment"]
    assert document["error"]["type"] == foutsoort
    for marker in GEVOELIGE_MARKERS:
        assert marker not in caplog.text
        assert marker not in document["error"]["message"]
        assert marker not in detail["parts"][0]["reason"]
    # De log is werkelijk gevuld (de technische melding staat erin) — anders
    # bewijst de afwezigheid niets.
    assert any("INT-03" in r.getMessage() for r in caplog.records)
    if foutsoort == "unverifiable_evidence":
        # Het bewijs zelf blijft in het document (voor UI/diagnose), niet in
        # meldingen of logs.
        assert GEVOELIG in document["rejected"][0]["detail"]


async def test_ess03_en_int03_beoordelingen_reizen_naast_elkaar():
    from tests.fixtures.def766_fakes import FakeEss03Assessor

    service = _service()
    orch = ValidationOrchestratorV2(
        service,
        ess03_assessment_service=FakeEss03Assessor(scenario="pass"),
        int03_assessment_service=FakeInt03Assessor(scenario="pass"),
    )
    result = await orch.validate_text(
        BEGRIP, TEKST, context=ValidationContext(metadata={})
    )
    assert service.received["ess03_assessment"]["status"] == "assessed"
    assert service.received["int03_assessment"]["status"] == "assessed"
    assert result["ess03_assessment"]["status"] == "assessed"


def test_definition_orchestrator_injecteert_de_dienst_in_de_wrapper():
    from services.orchestrators.definition_orchestrator_v2 import (
        DefinitionOrchestratorV2,
    )

    class _Repo:
        pass

    assessor = FakeInt03Assessor()
    orch = DefinitionOrchestratorV2(
        ai_service=object(),
        cleaning_service=object(),
        repository=_Repo(),
        int03_assessment_service=assessor,
    )
    assert orch.int03_assessment_service is assessor


def test_definition_orchestrator_bouwt_de_dienst_lazy_op_de_ai_service(monkeypatch):
    from services.orchestrators import definition_orchestrator_v2 as module

    class FakeRouter:
        @classmethod
        def from_config(cls):
            return cls()

        def get_model(self, task_type):
            return "fake", "fake-model"

    monkeypatch.setattr("services.ai.model_router.ModelRouter", FakeRouter)

    class _Repo:
        pass

    ai = object()
    orch = module.DefinitionOrchestratorV2(
        ai_service=ai, cleaning_service=object(), repository=_Repo()
    )
    dienst = orch.int03_assessment_service
    from services.validation.int03_assessment_service import Int03AssessmentService

    assert isinstance(dienst, Int03AssessmentService)
    assert dienst._ai_service is ai
    assert orch.int03_assessment_service is dienst  # singleton per orchestrator


def test_definition_orchestrator_geeft_de_dienst_aan_de_validatiewrapper(
    monkeypatch,
):
    from services.orchestrators import definition_orchestrator_v2 as module

    class _Repo:
        pass

    assessor = FakeInt03Assessor()
    orch = module.DefinitionOrchestratorV2(
        ai_service=object(),
        cleaning_service=object(),
        repository=_Repo(),
        int03_assessment_service=assessor,
    )
    wrapper = orch.validation_service
    assert isinstance(wrapper, ValidationOrchestratorV2)
    assert wrapper.int03_assessment_service is assessor


def test_container_levert_een_gedeelde_dienst(monkeypatch):
    from services.container import ServiceContainer

    container = ServiceContainer.__new__(ServiceContainer)
    container._instances = {}
    monkeypatch.setattr(container, "ai_service", lambda: object(), raising=False)
    monkeypatch.setattr(container, "model_router", lambda: None, raising=False)
    from services.validation.int03_assessment_service import Int03AssessmentService

    dienst = container.int03_assessment_service()
    assert isinstance(dienst, Int03AssessmentService)
    assert container.int03_assessment_service() is dienst
