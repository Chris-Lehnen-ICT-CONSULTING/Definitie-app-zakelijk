"""DEF-835 WP5a: de container bouwt INT-02 (O2) alleen op expliciet verzoek (eerst rood).

`ServiceContainer.int02_assessment_service` construeert de WP2-dienst
uitsluitend met een expliciet `Modelprofiel` en een expliciet `Budget`: geen
default, geen singleton, geen profiel of budget van een andere regel
(INT-03/ESS-03/bronnen) en geen modelaanroep bij constructie. De normale
`orchestrator()` blijft O1: zij bouwt of injecteert geen INT-02-dienst, ook
niet nadat de factory is gebruikt. Een expliciet gebouwde dienst bereikt via
de bestaande DI (`DefinitionOrchestratorV2`) wél de validatiewrapper.
"""

from __future__ import annotations

import inspect

import pytest

from services.container import ServiceContainer
from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2
from services.validation import int02_assessment_service as int02_module
from services.validation.int02_assessment_service import (
    Budget,
    Int02AssessmentService,
    Int02ServiceConfigError,
    Modelprofiel,
)
from services.validation.modular_validation_service import ModularValidationService
from toetsregels.manager import ToetsregelManager
from toetsregels.runtime_contract import EvaluatorType

pytestmark = [pytest.mark.unit]

PROFIEL = Modelprofiel(
    profiel_id="wp5a-container-fixture",
    provider="fakeprovider",
    model="fake-int02-model",
    kwalificatie="testfixture; geen kwaliteitsclaim",
)
BUDGET = Budget(
    max_uitvoertokens=800,
    deadline_seconden=5.0,
    max_invoertekens_veld=2000,
    max_invoertekens_totaal=6000,
    max_antwoordtekens=20000,
)


class _TellendeAI:
    """AI-grens die elke aanroep telt; een aanroep is hier altijd fout."""

    def __init__(self):
        self.calls = 0

    async def generate_definition(self, *args, **kwargs):  # pragma: no cover
        self.calls += 1
        raise AssertionError("geen modelaanroep verwacht")


class _Router:
    def get_model(self, task_type):  # pragma: no cover - niet aangeroepen
        raise AssertionError("geen routering bij constructie verwacht")


class _Repo:
    pass


@pytest.fixture
def container(monkeypatch):
    """Container zonder echte AI-client, database of webdiensten."""
    c = ServiceContainer.__new__(ServiceContainer)
    c._instances = {}
    c._lazy_instances = {}
    c.use_json_rules = True
    ai, router = _TellendeAI(), _Router()
    monkeypatch.setattr(c, "ai_service", lambda: ai, raising=False)
    monkeypatch.setattr(c, "model_router", lambda: router, raising=False)
    monkeypatch.setattr(c, "cleaning_service", lambda: object(), raising=False)
    monkeypatch.setattr(c, "repository", lambda: _Repo(), raising=False)
    monkeypatch.setattr(c, "web_lookup", lambda: None, raising=False)
    monkeypatch.setattr(c, "synonym_orchestrator", lambda: None, raising=False)
    monkeypatch.setattr(ServiceContainer, "rag_service", property(lambda _s: None))
    for naam in (
        "source_assessment_service",
        "ess03_assessment_service",
        "int03_assessment_service",
    ):
        monkeypatch.setattr(c, naam, lambda: object(), raising=False)
    c.fake_ai, c.fake_router = ai, router
    return c


@pytest.fixture
def constructies(monkeypatch):
    """Telt elke constructie van de INT-02-dienst in dit proces."""
    teller: list[dict] = []
    origineel = Int02AssessmentService.__init__

    def _init(self, *args, **kwargs):
        teller.append(kwargs)
        origineel(self, *args, **kwargs)

    monkeypatch.setattr(Int02AssessmentService, "__init__", _init)
    return teller


def test_factory_vereist_expliciet_profiel_en_budget_zonder_default(container):
    handtekening = inspect.signature(container.int02_assessment_service)
    for naam in ("profiel", "budget"):
        parameter = handtekening.parameters[naam]
        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
        assert parameter.default is inspect.Parameter.empty

    with pytest.raises(TypeError):
        container.int02_assessment_service()
    with pytest.raises(Int02ServiceConfigError):
        container.int02_assessment_service(profiel=None, budget=BUDGET)
    with pytest.raises(Int02ServiceConfigError):
        container.int02_assessment_service(profiel=PROFIEL, budget=None)


def test_factory_bouwt_op_expliciet_verzoek_zonder_modelaanroep(
    container, constructies
):
    dienst = container.int02_assessment_service(profiel=PROFIEL, budget=BUDGET)

    assert isinstance(dienst, Int02AssessmentService)
    assert dienst._ai_service is container.fake_ai
    assert dienst._model_router is container.fake_router
    assert dienst._profiel is PROFIEL
    assert dienst._budget is BUDGET
    assert len(constructies) == 1
    assert container.fake_ai.calls == 0
    # Geen singleton en geen registratie voor de orchestrator.
    assert dienst not in container._instances.values()
    tweede = container.int02_assessment_service(profiel=PROFIEL, budget=BUDGET)
    assert tweede is not dienst


def test_normale_orchestrator_blijft_o1_zonder_int02_dienst(container, constructies):
    # Ook nadat de factory is gebruikt, bedraadt orchestrator() niets.
    container.int02_assessment_service(profiel=PROFIEL, budget=BUDGET)
    constructies.clear()

    orchestrator = container.orchestrator()
    wrapper = orchestrator.validation_service

    assert isinstance(wrapper, ValidationOrchestratorV2)
    assert orchestrator.int02_assessment_service is None
    assert wrapper.int02_assessment_service is None
    assert constructies == []
    assert container.fake_ai.calls == 0


def test_expliciet_gebouwde_dienst_bereikt_de_validatiewrapper(container):
    from services.orchestrators.definition_orchestrator_v2 import (
        DefinitionOrchestratorV2,
    )

    dienst = container.int02_assessment_service(profiel=PROFIEL, budget=BUDGET)
    orchestrator = DefinitionOrchestratorV2(
        ai_service=container.ai_service(),
        cleaning_service=object(),
        repository=_Repo(),
        int02_assessment_service=dienst,
    )
    assert orchestrator.validation_service.int02_assessment_service is dienst


def test_actieve_ssot_houdt_int02_op_o1():
    service = ModularValidationService(toetsregel_manager=ToetsregelManager())
    assert service.evaluator_voor("INT-02") is EvaluatorType.JUDGMENT_REVIEW


def test_wp2_dienst_kent_geen_default_profiel_of_budget():
    # Geen profielbudget van een andere regel als O2-kwalificatie: de module
    # definieert zelf geen profiel- of budgetinstantie om op terug te vallen.
    for waarde in vars(int02_module).values():
        assert not isinstance(waarde, Modelprofiel | Budget)
