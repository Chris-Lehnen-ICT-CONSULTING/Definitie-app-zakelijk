"""DEF-766: de actieve async wrappers verkrijgen de ESS-03-beoordeling standaard.

`ValidationOrchestratorV2.validate_text` en `validate_definition` moeten zélf
een verse telbaarheidsbeoordeling verkrijgen via de geïnjecteerde
`Ess03AssessmentService`, haar aan de evaluator meegeven én volledig
teruggeven (`result["ess03_assessment"]`, contract 2.1.0). Een door de
aanroeper meegegeven `ess03_assessment` is nooit een kortere weg naar een
positief oordeel. Zonder term of tekst wordt er geen model aangeroepen; zonder
dienst is de beoordeling expliciet `unavailable`; een dienstfout is een
technische fout — nooit stil een pass. Ook de DI-keten (DefinitionOrchestratorV2,
ServiceContainer) injecteert de dienst werkelijk.
"""

from __future__ import annotations

from copy import deepcopy
from unittest.mock import AsyncMock

import pytest

from domain.ess03.contract import CONTRACTVERSIE, Intentie, bereken_ess03_vingerafdruk
from services.interfaces import Definition
from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2
from services.validation.interfaces import CONTRACT_VERSION, ValidationContext
from tests.fixtures.def766_fakes import FakeEss03Assessor

pytestmark = [pytest.mark.unit]

BEGRIP = "eiland"
TEKST = (
    "Afzonderlijk aaneengesloten landoppervlak dat op het afgesproken peilmoment "
    "volledig door water is omgeven."
)
CONTEXT = {
    "organisatorische_context": ["Synthetisch Waterschap"],
    "juridische_context": [],
    "wettelijke_basis": [],
}
BRON = {
    "provider": "documents",
    "doc_id": "conv-1",
    "snippet": "Elk gescheiden aaneengesloten vlak telt op peil P als één.",
}


def _service():
    """Validatiedubbel dat de ontvangen context bewaart en een dict teruggeeft."""
    service = AsyncMock()

    async def _bewaar(*_a, **kwargs):
        service.received = deepcopy(kwargs.get("context") or {})
        return {"version": CONTRACT_VERSION, "system": {}}

    service.validate_definition.side_effect = _bewaar
    return service


async def test_validate_text_verkrijgt_verse_beoordeling_en_geeft_haar_terug():
    service, assessor = _service(), FakeEss03Assessor(scenario="pass")
    orch = ValidationOrchestratorV2(service, ess03_assessment_service=assessor)
    metadata = {
        **CONTEXT,
        "provenance_sources": [BRON],
        "toelichting": "Synthetische conventie.",
        "ontologische_categorie": "type",
        "ess03_verduidelijking": "Peil P is het zomerpeil.",
        # Een meegegeven beoordeling is nooit de bron van waarheid.
        "ess03_assessment": {"status": "assessed", "judgment": {"verdict": "pass"}},
    }
    before = deepcopy(metadata)

    result = await orch.validate_text(
        BEGRIP, TEKST, context=ValidationContext(metadata=metadata)
    )

    assert metadata == before
    (call,) = assessor.calls
    assert call["begrip"] == BEGRIP
    assert call["tekst"] == TEKST
    assert call["bronnen"] == [BRON]
    assert call["intentie"] == Intentie(
        toelichting="Synthetische conventie.",
        categorie="type",
        verduidelijking="Peil P is het zomerpeil.",
    )
    doorgegeven = service.received["ess03_assessment"]
    assert doorgegeven["status"] == "assessed"
    assert doorgegeven["contract_version"] == CONTRACTVERSIE
    assert doorgegeven["fingerprint"] == bereken_ess03_vingerafdruk(
        BEGRIP, TEKST, CONTEXT, [BRON], intentie=call["intentie"]
    )
    assert doorgegeven["attribution"]["model"] == "fake-ess03-model"
    assert result["ess03_assessment"] == doorgegeven
    # DEF-771: 2.2.0 (additief: not_evaluated als deeluitkomst).
    assert result["version"] == CONTRACT_VERSION == "2.2.0"


async def test_validate_definition_gebruikt_recordtekst_en_toelichting():
    service, assessor = _service(), FakeEss03Assessor(scenario="pass")
    orch = ValidationOrchestratorV2(service, ess03_assessment_service=assessor)
    definitie = Definition(
        begrip=BEGRIP,
        definitie=TEKST,
        toelichting="Synthetische conventie uit het record.",
        organisatorische_context=list(CONTEXT["organisatorische_context"]),
        ontologische_categorie="type",
        metadata={"provenance_sources": [BRON], "version_number": 3},
    )
    result = await orch.validate_definition(definitie)
    (call,) = assessor.calls
    assert call["tekst"] == TEKST
    assert call["bronnen"] == [BRON]
    assert call["intentie"].toelichting == "Synthetische conventie uit het record."
    assert call["intentie"].categorie == "type"
    assert result["ess03_assessment"]["status"] == "assessed"
    assert service.received["ess03_assessment"] == result["ess03_assessment"]


async def test_zonder_term_of_tekst_geen_modelaanroep():
    service, assessor = _service(), FakeEss03Assessor()
    orch = ValidationOrchestratorV2(service, ess03_assessment_service=assessor)
    leeg = await orch.validate_text(
        BEGRIP, "   ", context=ValidationContext(metadata={})
    )
    zonder_term = await orch.validate_text(
        "", TEKST, context=ValidationContext(metadata={})
    )
    assert assessor.calls == []
    assert leeg["ess03_assessment"] is None
    assert zonder_term["ess03_assessment"] is None
    assert "ess03_assessment" not in service.received


async def test_zonder_dienst_is_de_beoordeling_expliciet_niet_beschikbaar():
    service = _service()
    orch = ValidationOrchestratorV2(service)
    result = await orch.validate_text(
        BEGRIP, TEKST, context=ValidationContext(metadata={})
    )
    doc = result["ess03_assessment"]
    assert doc["status"] == "unavailable"
    assert "geen" in doc["reason"].lower()
    assert service.received["ess03_assessment"] == doc


async def test_dienstfout_is_technische_fout_nooit_pass():
    service = _service()
    assessor = FakeEss03Assessor(fout=RuntimeError("synthetische storing"))
    orch = ValidationOrchestratorV2(service, ess03_assessment_service=assessor)
    result = await orch.validate_text(
        BEGRIP, TEKST, context=ValidationContext(metadata={})
    )
    doc = result["ess03_assessment"]
    assert doc["status"] == "error"
    assert doc["error"]["type"] == "unknown"
    assert "synthetische storing" in doc["error"]["message"]
    assert doc["fingerprint"] == bereken_ess03_vingerafdruk(
        BEGRIP, TEKST, {}, [], intentie=Intentie()
    )


async def test_dienst_die_geen_document_geeft_is_technische_fout():
    service = _service()

    class Kapot:
        async def assess(self, *a, **k):
            return "geen document"

    orch = ValidationOrchestratorV2(service, ess03_assessment_service=Kapot())
    result = await orch.validate_text(
        BEGRIP, TEKST, context=ValidationContext(metadata={})
    )
    assert result["ess03_assessment"]["status"] == "error"


def test_definition_orchestrator_injecteert_de_dienst_in_de_wrapper():
    from services.orchestrators.definition_orchestrator_v2 import (
        DefinitionOrchestratorV2,
    )

    class _Repo:
        pass

    assessor = FakeEss03Assessor()
    orch = DefinitionOrchestratorV2(
        ai_service=object(),
        cleaning_service=object(),
        repository=_Repo(),
        ess03_assessment_service=assessor,
    )
    assert orch.ess03_assessment_service is assessor


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
    dienst = orch.ess03_assessment_service
    from services.validation.ess03_assessment_service import Ess03AssessmentService

    assert isinstance(dienst, Ess03AssessmentService)
    assert dienst._ai_service is ai
    assert orch.ess03_assessment_service is dienst  # singleton per orchestrator


def test_container_levert_een_gedeelde_dienst(monkeypatch):
    from services.container import ServiceContainer

    container = ServiceContainer.__new__(ServiceContainer)
    container._instances = {}
    monkeypatch.setattr(container, "ai_service", lambda: object(), raising=False)
    monkeypatch.setattr(container, "model_router", lambda: None, raising=False)
    from services.validation.ess03_assessment_service import Ess03AssessmentService

    dienst = container.ess03_assessment_service()
    assert isinstance(dienst, Ess03AssessmentService)
    assert container.ess03_assessment_service() is dienst
