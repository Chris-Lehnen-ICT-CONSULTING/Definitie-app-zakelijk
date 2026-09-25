"""DEF-768: de actieve async wrappers verkrijgen de ESS-05-beoordeling standaard.

`ValidationOrchestratorV2.validate_text` en `validate_definition` stellen de
actieve burenlijst samen (opgeslagen besluiten, gebruikersinvoer uit
`gerelateerde_begrippen`, verse repository-buren in dezelfde context), vragen
één verse onderscheidsbeoordeling aan de geïnjecteerde `Ess05AssessmentService`,
geven haar aan de evaluator mee én volledig terug (`result["ess05_assessment"]`).
Een meegegeven `ess05_assessment`, `ess05_binding` of `ess05_actieve_buren` van
de aanroeper telt nooit. Zonder term, tekst of context geen modelaanroep; bij
een geldige deskundige bevestiging van een lege vergelijkingsruimte evenmin.
Zonder dienst `unavailable`; een dienst-, burenlijst- of repositoryfout is een
technische fout — nooit stil een pass.
"""

from __future__ import annotations

from copy import deepcopy
from unittest.mock import AsyncMock

import pytest

from domain.ess05.contract import (
    CONTRACTVERSIE,
    bereken_ess05_vingerafdruk,
    normaliseer_buren,
)
from services.interfaces import Definition
from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2
from services.validation.interfaces import CONTRACT_VERSION, ValidationContext
from tests.fixtures.def768_fakes import BINDING, FakeEss05Assessor

pytestmark = [pytest.mark.unit]

BEGRIP = "lener"
TEKST = "Persoon met een actuele lening bij de instelling."
WERKNEMER = "Persoon met een arbeidsovereenkomst met de instelling."
CONTEXT = {
    "organisatorische_context": ["Synthetische Uitleendienst"],
    "juridische_context": [],
    "wettelijke_basis": [],
}
GEBRUIKERSBUUR = {
    "term": "werknemer",
    "definitie": WERKNEMER,
    "herkomst": "gebruiker",
    "bevestigd": True,
}


def _service():
    """Validatiedubbel dat de ontvangen context bewaart en een dict teruggeeft."""
    service = AsyncMock()

    async def _bewaar(*_a, **kwargs):
        service.received = deepcopy(kwargs.get("context") or {})
        return {"version": CONTRACT_VERSION, "system": {}}

    service.validate_definition.side_effect = _bewaar
    return service


class FakeBurenbron:
    """De repositorygrens: verse buren in dezelfde context."""

    def __init__(self, rijen=(), fout: Exception | None = None):
        self.rijen = list(rijen)
        self.fout = fout
        self.calls: list[tuple] = []

    def zoek_ess05_buren(self, begrip, contexten, eigen_id):
        self.calls.append((begrip, deepcopy(dict(contexten)), eigen_id))
        if self.fout is not None:
            raise self.fout
        return deepcopy(self.rijen)


def _orch(service, assessor=None, burenbron=None):
    return ValidationOrchestratorV2(
        service, ess05_assessment_service=assessor, ess05_burenbron=burenbron
    )


async def test_ess05_velden_zijn_schemaconform():
    """Contract 2.2.0: beoordeling en burenlijst passen in hun eigen subschema."""
    import json
    from pathlib import Path

    from jsonschema import validate

    schema = json.loads(
        (
            Path(__file__).resolve().parents[4]
            / "docs/architectuur/contracts/schemas/validation_result.schema.json"
        ).read_text(encoding="utf-8")
    )
    result = await _orch(
        _service(),
        FakeEss05Assessor(scenario="pass"),
        FakeBurenbron([{"id": 9, "begrip": "klant", "definitie": "Persoon."}]),
    ).validate_text(
        begrip=BEGRIP,
        text=TEKST,
        ontologische_categorie="type",
        context=ValidationContext(metadata=dict(CONTEXT)),
    )
    assert result["version"] == "2.2.0"
    for veld in ("ess05_assessment", "ess05_actieve_buren"):
        assert result[veld] is not None
        validate(instance=result[veld], schema=schema["properties"][veld])


async def test_validate_text_verkrijgt_verse_beoordeling_en_geeft_haar_terug():
    service, assessor = _service(), FakeEss05Assessor(scenario="pass")
    metadata = {
        **CONTEXT,
        "ess05_buren": [GEBRUIKERSBUUR],
        # Nooit de bron van waarheid: de wrapper gooit dit weg.
        "ess05_assessment": {"status": "assessed", "judgment": {}},
        "ess05_binding": {"model": "vervalst"},
        "ess05_actieve_buren": [],
    }
    before = deepcopy(metadata)

    result = await _orch(service, assessor).validate_text(
        BEGRIP, TEKST, context=ValidationContext(metadata=metadata)
    )

    assert metadata == before
    (call,) = assessor.calls
    assert (call["begrip"], call["tekst"]) == (BEGRIP, TEKST)
    buren = normaliseer_buren([GEBRUIKERSBUUR])
    assert call["buren"] == buren
    doorgegeven = service.received["ess05_assessment"]
    assert doorgegeven["status"] == "assessed"
    assert doorgegeven["contract_version"] == CONTRACTVERSIE
    assert doorgegeven["fingerprint"] == bereken_ess05_vingerafdruk(
        BEGRIP, TEKST, CONTEXT, [], intentie=call["intentie"], buren=buren
    )
    assert service.received["ess05_binding"] == BINDING.als_dict()
    assert service.received["ess05_actieve_buren"] == [b.als_dict() for b in buren]
    assert result["ess05_assessment"] == doorgegeven


async def test_validate_definition_neemt_record_en_repositoryburen_mee():
    service, assessor = _service(), FakeEss05Assessor(scenario="pass")
    bron = FakeBurenbron(
        [
            {"id": 9, "begrip": "klant", "definitie": "Persoon die iets afneemt."},
            {"id": 7, "begrip": "borg", "definitie": "Persoon die instaat."},
        ]
    )
    definitie = Definition(
        id=3,
        begrip=BEGRIP,
        definitie=TEKST,
        organisatorische_context=list(CONTEXT["organisatorische_context"]),
        gerelateerde_begrippen=["werknemer", "  "],
        metadata={
            "ess05_buren": [
                {
                    "id": "repository:7",
                    "term": "borg",
                    "definitie": "oud",
                    "herkomst": "repository",
                    "bevestigd": False,
                    "afgewezen": True,
                }
            ]
        },
    )
    result = await _orch(service, assessor, bron).validate_definition(definitie)

    ((begrip, contexten, eigen_id),) = bron.calls
    assert (begrip, eigen_id) == (BEGRIP, 3)
    assert contexten["organisatorische_context"] == ["Synthetische Uitleendienst"]
    (call,) = assessor.calls
    termen = {b.term: b for b in call["buren"]}
    assert set(termen) == {"werknemer", "klant"}
    assert termen["werknemer"].herkomst == "gebruiker"
    assert termen["werknemer"].bevestigd is True
    assert termen["werknemer"].definitie is None
    assert termen["klant"].id == "repository:9"
    assert termen["klant"].bevestigd is False
    assert call["uitgesloten_termen"] == ("borg",)
    assert service.received["ess05_uitgesloten_termen"] == ["borg"]
    assert result["ess05_assessment"]["status"] == "assessed"


async def test_gebruikersterm_die_al_als_buur_bestaat_wordt_niet_verdubbeld():
    service, assessor = _service(), FakeEss05Assessor()
    definitie = Definition(
        begrip=BEGRIP,
        definitie=TEKST,
        organisatorische_context=list(CONTEXT["organisatorische_context"]),
        gerelateerde_begrippen=["Werknemer"],
        metadata={"ess05_buren": [GEBRUIKERSBUUR]},
    )
    await _orch(service, assessor).validate_definition(definitie)
    (call,) = assessor.calls
    assert [b.term for b in call["buren"]] == ["werknemer"]
    assert call["buren"][0].definitie == WERKNEMER


@pytest.mark.parametrize(
    ("begrip", "tekst", "metadata"),
    [
        (BEGRIP, "   ", CONTEXT),
        ("", TEKST, CONTEXT),
        (BEGRIP, TEKST, {"organisatorische_context": [], "juridische_context": []}),
    ],
    ids=["zonder-tekst", "zonder-term", "zonder-context"],
)
async def test_zonder_term_tekst_of_context_geen_modelaanroep(begrip, tekst, metadata):
    service, assessor = _service(), FakeEss05Assessor()
    bron = FakeBurenbron()
    result = await _orch(service, assessor, bron).validate_text(
        begrip, tekst, context=ValidationContext(metadata=dict(metadata))
    )
    assert assessor.calls == []
    assert bron.calls == []
    assert result["ess05_assessment"] is None
    assert "ess05_assessment" not in service.received


async def test_zonder_dienst_is_de_beoordeling_expliciet_niet_beschikbaar():
    service = _service()
    result = await _orch(service).validate_text(
        BEGRIP, TEKST, context=ValidationContext(metadata=dict(CONTEXT))
    )
    doc = result["ess05_assessment"]
    assert doc["status"] == "unavailable"
    assert "geen" in doc["reason"].lower()
    assert service.received["ess05_assessment"] == doc


async def test_dienstfout_is_technische_fout_nooit_pass():
    service = _service()
    assessor = FakeEss05Assessor(fout=RuntimeError("synthetische storing"))
    result = await _orch(service, assessor).validate_text(
        BEGRIP, TEKST, context=ValidationContext(metadata=dict(CONTEXT))
    )
    doc = result["ess05_assessment"]
    assert doc["status"] == "error"
    assert doc["error"]["type"] == "unknown"
    assert "synthetische storing" in doc["error"]["message"]


async def test_repositoryfout_is_technische_fout_zonder_modelaanroep():
    service, assessor = _service(), FakeEss05Assessor()
    bron = FakeBurenbron(fout=RuntimeError("db weg"))
    result = await _orch(service, assessor, bron).validate_text(
        BEGRIP, TEKST, context=ValidationContext(metadata=dict(CONTEXT))
    )
    assert assessor.calls == []
    doc = result["ess05_assessment"]
    assert doc["status"] == "error"
    assert doc["error"]["type"] == "neighbour_lookup"


async def test_ongeldige_burenlijst_is_technische_fout_zonder_modelaanroep():
    service, assessor = _service(), FakeEss05Assessor()
    metadata = {**CONTEXT, "ess05_buren": [{"term": "x", "herkomst": "onbekend"}]}
    result = await _orch(service, assessor).validate_text(
        BEGRIP, TEKST, context=ValidationContext(metadata=metadata)
    )
    assert assessor.calls == []
    doc = result["ess05_assessment"]
    assert doc["status"] == "error"
    assert doc["error"]["type"] == "invalid_neighbours"


async def test_geldige_lege_ruimte_vraagt_geen_modelaanroep():
    service, assessor = _service(), FakeEss05Assessor()
    vingerafdruk = bereken_ess05_vingerafdruk(BEGRIP, TEKST, CONTEXT, [], buren=())
    lege_ruimte = {
        "fingerprint": vingerafdruk,
        "contract_version": CONTRACTVERSIE,
        "grond": "Synthetisch: enig begrip in dit register.",
        "actor": "deskundige",
        "at": "2026-09-23T10:00:00+00:00",
    }
    metadata = {**CONTEXT, "ess05_lege_ruimte": lege_ruimte}
    result = await _orch(service, assessor, FakeBurenbron()).validate_text(
        BEGRIP, TEKST, context=ValidationContext(metadata=metadata)
    )
    assert assessor.calls == []
    assert result["ess05_assessment"] is None
    assert service.received["ess05_lege_ruimte"] == lege_ruimte
    assert service.received["ess05_actieve_buren"] == []


async def test_verouderde_lege_ruimte_leidt_wel_tot_een_aanroep():
    service, assessor = _service(), FakeEss05Assessor()
    metadata = {
        **CONTEXT,
        "ess05_lege_ruimte": {
            "fingerprint": "0" * 64,
            "contract_version": CONTRACTVERSIE,
            "grond": "g",
            "actor": "a",
        },
    }
    await _orch(service, assessor).validate_text(
        BEGRIP, TEKST, context=ValidationContext(metadata=metadata)
    )
    assert len(assessor.calls) == 1


def test_definition_orchestrator_injecteert_dienst_en_burenbron():
    from services.interfaces import OrchestratorConfig
    from services.orchestrators.definition_orchestrator_v2 import (
        DefinitionOrchestratorV2,
    )

    class _Repo:
        def zoek_ess05_buren(self, begrip, contexten, eigen_id):
            return []

    assessor, repo = FakeEss05Assessor(), _Repo()
    orch = DefinitionOrchestratorV2(
        ai_service=object(),
        cleaning_service=object(),
        repository=repo,
        config=OrchestratorConfig(use_json_rules=False),
        source_assessment_service=object(),
        ess03_assessment_service=object(),
        ess05_assessment_service=assessor,
    )
    assert orch.ess05_assessment_service is assessor
    wrapper = orch.validation_service
    assert wrapper.ess05_assessment_service is assessor
    assert wrapper.ess05_burenbron is repo


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
    from services.validation.ess05_assessment_service import Ess05AssessmentService

    dienst = orch.ess05_assessment_service
    assert isinstance(dienst, Ess05AssessmentService)
    assert dienst._ai_service is ai
    assert orch.ess05_assessment_service is dienst


def test_container_levert_een_gedeelde_dienst(monkeypatch):
    from services.container import ServiceContainer
    from services.validation.ess05_assessment_service import Ess05AssessmentService

    container = ServiceContainer.__new__(ServiceContainer)
    container._instances = {}
    monkeypatch.setattr(container, "ai_service", lambda: object(), raising=False)
    monkeypatch.setattr(container, "model_router", lambda: None, raising=False)
    dienst = container.ess05_assessment_service()
    assert isinstance(dienst, Ess05AssessmentService)
    assert container.ess05_assessment_service() is dienst
