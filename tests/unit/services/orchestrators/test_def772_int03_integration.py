"""DEF-772 WP3: de INT-03-beoordeling door de hele generatieketen (offline, echte validatie).

`DefinitionOrchestratorV2.create_definition` met gemockte AI/prompt/cleaning/
repository, maar met de echte `ValidationOrchestratorV2` →
`ModularValidationService` (echte regelset) en een deterministische fake
`Int03AssessmentService`. Bewijst dat de gegenereerde kandidaat de
verwijzingsbeoordeling bereikt, dat de gestructureerde payload (inclusief het
volledige, aan de eindtekst gebonden document) in `rule_results["INT-03"]`
van het validatieresultaat staat, en dat een negatieve INT-03-uitkomst geen
herstelroute activeert en de generatie niet laat falen. Geen echt model, geen
productiedatabase. Duurzame opslag, UI en export zijn WP4.

Tweede deel (reviewcorrecties, dispositie v3/v4): de échte productieroute.
Geen geïnjecteerde prompt-, validatie- of beoordelingsdienst en geen
vervangen ModelRouter: `DefinitionOrchestratorV2` bouwt de echte
`PromptServiceV2`, de wrapper en de echte `Int03AssessmentService` lazy op de
gedeelde AI-service (zoals de container), met de echte `CleaningService`,
`SecurityService`, `ModelRouter.from_config()` en voorbeeldengenerator, met
uitsluitend de modelgrens gestubd en opslag in een tijdelijke
SQLite-database. Plus de containerbedrading zelf: één gedeelde dienst voor
orchestrator en validatiewrapper.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from domain.int03.contract import (
    BEVINDING_GEEN_VERWIJZEND_WOORD,
    MOTIVERING_GEEN_VERWIJZEND_WOORD,
    bereken_int03_vingerafdruk,
)
from services.definition_repository import DefinitionRepository
from services.interfaces import (
    AIGenerationResult,
    CleaningResult,
    GenerationRequest,
    OrchestratorConfig,
    PromptResult,
)
from services.null_repository import NullDefinitionRepository
from services.orchestrators.definition_orchestrator_v2 import DefinitionOrchestratorV2
from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2
from services.validation.int03_assessment_service import (
    Int03AssessmentService,
    laad_int03_norm,
)
from services.validation.modular_validation_service import ModularValidationService
from tests.fixtures.def772_fakes import FakeInt03Assessor, FakeModelgrens, FakeRouter
from toetsregels.manager import get_toetsregel_manager

pytestmark = [pytest.mark.unit]

BEGRIP = "archiefkaart"
DEFINITIE_MET_DIE = (
    "Beschrijving van een verzameling documenten die bij een zaak horen."
)
DEFINITIE_ZONDER = "Beschrijving van een verzameling documenten van een archiefvormer."


@pytest.fixture
def generate(monkeypatch):
    from voorbeelden import unified_voorbeelden

    monkeypatch.setattr(
        unified_voorbeelden,
        "genereer_alle_voorbeelden_async",
        AsyncMock(return_value={}),
    )

    async def run(*, scenario="pass", definitie=DEFINITIE_MET_DIE, enhancement=None):
        assessor = FakeInt03Assessor(scenario=scenario)
        prompt = AsyncMock()
        prompt.build_generation_prompt.return_value = PromptResult(
            text="Offline",
            token_count=1,
            components_used=(),
            feedback_integrated=False,
            optimization_applied=False,
            metadata={},
        )
        ai = AsyncMock()
        ai.generate_definition.return_value = AIGenerationResult(
            text=definitie, model="offline", tokens_used=1, generation_time=0.0
        )
        cleaning = AsyncMock()
        cleaning.clean_text.return_value = CleaningResult(
            original_text=definitie, cleaned_text=definitie, was_cleaned=False
        )
        validation = ValidationOrchestratorV2(
            ModularValidationService(
                get_toetsregel_manager(), repository=NullDefinitionRepository()
            ),
            int03_assessment_service=assessor,
        )
        repo = MagicMock()
        repo.save.return_value = 42
        orch = DefinitionOrchestratorV2(
            prompt_service=prompt,
            ai_service=ai,
            validation_service=validation,
            cleaning_service=cleaning,
            repository=repo,
            enhancement_service=enhancement,
            config=OrchestratorConfig(
                enable_feedback_loop=False, enable_enhancement=enhancement is not None
            ),
        )
        response = await orch.create_definition(
            GenerationRequest(
                id="int03-offline",
                begrip=BEGRIP,
                ontologische_categorie="type",
                organisatorische_context=["Testregistratie"],
            ),
            context={},
        )
        assert response.success, response.error
        return SimpleNamespace(response=response, assessor=assessor, repo=repo)

    return run


async def test_generatie_bereikt_de_beoordeling_en_levert_de_payload(generate):
    result = await generate()
    (call,) = result.assessor.calls
    assert call["begrip"] == BEGRIP
    assert call["tekst"] == DEFINITIE_MET_DIE
    raw = result.response.validation_result
    assert raw["rule_statuses"]["INT-03"] == "pass"
    detail = raw["rule_results"]["INT-03"]
    assert detail["status"] == "pass"
    assert detail["score"] is None
    document = detail["assessment"]
    assert document["status"] == "assessed"
    assert document["fingerprint"] == detail["fingerprint"]
    assert document["fingerprint"] == bereken_int03_vingerafdruk(
        BEGRIP,
        DEFINITIE_MET_DIE,
        {"organisatorische_context": ["Testregistratie"]},
        None,
    )
    assert document["judgment"]["references"][0]["word"] == "die"


async def test_negatieve_int03_laat_generatie_slagen_zonder_herstel(generate):
    enhancement = AsyncMock()
    enhancement.enhance_definition.return_value = "HERSCHREVEN"
    result = await generate(scenario="fail", enhancement=enhancement)
    raw = result.response.validation_result
    assert raw["rule_statuses"]["INT-03"] == "fail"
    [violation] = [v for v in raw["violations"] if v.get("code") == "INT-03"]
    assert violation["severity"] == "warning"
    assert violation["metadata"]["advisory"] is True
    # De INT-03-violation bereikt de hersteldienst niet: geen automatische
    # tekstwijziging op een verwijzingsoordeel (K5: herstel alleen op verzoek).
    for call in enhancement.enhance_definition.await_args_list:
        assert all(v.get("code") != "INT-03" for v in call.args[1])
    assert raw["rule_results"]["INT-03"]["assessment"]["judgment"]["verdict"] == "fail"


async def test_geen_verwijzend_woord_is_pass_met_motivering_in_de_keten(generate):
    result = await generate(scenario="no_word", definitie=DEFINITIE_ZONDER)
    raw = result.response.validation_result
    assert raw["rule_statuses"]["INT-03"] == "pass"
    detail = raw["rule_results"]["INT-03"]
    assert detail["parts"][0]["reason"] == MOTIVERING_GEEN_VERWIJZEND_WOORD
    assert detail["review"]["assessment"]["finding"] == (
        BEVINDING_GEEN_VERWIJZEND_WOORD
    )


async def test_technische_fout_reist_mee_als_error_niet_als_oordeel(generate):
    result = await generate(scenario="error")
    raw = result.response.validation_result
    assert raw["rule_statuses"]["INT-03"] == "error"
    detail = raw["rule_results"]["INT-03"]
    assert detail["assessment"]["status"] == "error"
    assert detail["assessment"]["judgment"] is None


# --- Echte productieroute: uitsluitend de modelgrens gestubd ---------------------


@pytest.fixture
def genereer_productieroute(tmp_path):
    """`DefinitionOrchestratorV2` zoals de container hem bouwt, met de
    productieservices intact: echte `PromptServiceV2` (lazy), echte
    `CleaningService` met de standaard `CleaningConfig`, echte
    `SecurityService`, echte `ModelRouter.from_config()` op `config.yaml`,
    echte lazy `ValidationOrchestratorV2` → `ModularValidationService`
    (cached manager) → echte `Int03AssessmentService` (en de ESS-03-/CON-02-
    diensten) op de gedeelde AI-service, echte voorbeeldengenerator, opslag in
    een tijdelijke SQLite-database. Enige stub: de modelgrens
    (`FakeModelgrens.generate_definition`), gedeeld door generatie,
    beoordelingen en voorbeelden. Niet geïnjecteerd (None, zoals de container
    bij een uitgevallen dienst): web lookup, synoniemen, RAG, feedbackengine,
    monitoring; verrijking en feedbackloop staan via `OrchestratorConfig` uit.
    Netwerk is door `tests/conftest.py` geblokkeerd."""
    from services.ai.model_router import ModelRouter
    from services.cleaning_service import CleaningConfig, CleaningService
    from services.security_service import SecurityService
    from toetsregels.rule_cache import get_rule_cache
    from voorbeelden.unified_voorbeelden import (
        get_examples_generator,
        reset_examples_generator,
    )

    # Het productielaadpad (cached manager) mag geen oud INT-03-record uit de
    # schijfcache serveren (DEF-750).
    get_rule_cache().clear_cache()
    provider, model = ModelRouter.from_config().get_model("validation")
    runs: list[Any] = []

    async def run(*, scenario="pass", definitie=DEFINITIE_MET_DIE):
        ai = FakeModelgrens(
            definitie=definitie, scenario=scenario, beoordelingsmodel=model
        )
        # De voorbeeldengenerator haalt zijn AI-service anders uit de globale
        # container (productie-DB); hier dezelfde modelgrens via de daarvoor
        # bestemde override, zodat de echte generator werkelijk draait.
        reset_examples_generator()
        get_examples_generator().ai_service = ai
        db = str(tmp_path / f"int03-productieroute-{len(runs)}.db")
        orch = DefinitionOrchestratorV2(
            ai_service=ai,
            cleaning_service=CleaningService(CleaningConfig()),
            repository=DefinitionRepository(db),
            security_service=SecurityService(),
            config=OrchestratorConfig(
                enable_feedback_loop=False, enable_enhancement=False
            ),
        )
        response = await orch.create_definition(
            GenerationRequest(
                id="int03-productieroute",
                begrip=BEGRIP,
                ontologische_categorie="type",
                organisatorische_context=["Testregistratie"],
            ),
            context={},
        )
        assert response.success, response.error
        record = DefinitionRepository(db).get(response.definition.id)
        uit = SimpleNamespace(
            response=response,
            ai=ai,
            orch=orch,
            record=record,
            provider=provider,
            model=model,
        )
        runs.append(uit)
        return uit

    yield run
    reset_examples_generator()


async def test_productieroute_bouwt_de_echte_dienst_op_de_gedeelde_ai_service(
    genereer_productieroute,
):
    from services.ai.model_router import ModelRouter
    from services.cleaning_service import CleaningService
    from services.prompts.prompt_service_v2 import PromptServiceV2

    uit = await genereer_productieroute()

    # De productieservices zijn echt; alleen de AI-service is de fake.
    assert isinstance(uit.orch.prompt_service, PromptServiceV2)
    assert isinstance(uit.orch.cleaning_service, CleaningService)
    wrapper = uit.orch.validation_service
    assert isinstance(wrapper, ValidationOrchestratorV2)
    assert isinstance(wrapper.validation_service, ModularValidationService)
    dienst = uit.orch.int03_assessment_service
    assert isinstance(dienst, Int03AssessmentService)
    assert dienst._ai_service is uit.ai
    assert isinstance(dienst._model_router, ModelRouter)
    assert wrapper.int03_assessment_service is dienst

    # Eén gedeelde modelgrens: generatie (zonder taaktype), voorbeelden (eigen
    # taaktypes) en beoordeling (`validation`) lopen over dezelfde AI-service.
    generatie = [c for c in uit.ai.calls if c.get("task_type") is None]
    voorbeelden = [
        c for c in uit.ai.calls if c.get("task_type") not in (None, "validation")
    ]
    assert len(generatie) == 1
    assert BEGRIP in generatie[0]["prompt"]
    assert voorbeelden, "de echte voorbeeldengenerator bereikte de modelgrens niet"

    # Precies één INT-03-modelaanroep, met de afgesproken opt-ins, de norm uit
    # het regelrecord en de werkelijk gevalideerde (opgeschoonde) kandidaat.
    (call,) = uit.ai.int03_calls
    assert call["task_type"] == "validation"
    assert call["use_cache"] is False
    assert call["max_attempts"] == 1
    assert call["max_retries"] == 0
    # Outputtokenlimiet (Chris, 26-09-2026: max 5000, vervangt max 2500): de
    # echte productieconstructie (orchestrator → dienst zonder expliciet budget)
    # stuurt 5000 naar de AI-laag; geen verborgen oud budget op deze route.
    assert call["max_tokens"] == 5000
    assert uit.record.definitie in call["prompt"]
    assert laad_int03_norm()["uitleg"] in call["system_prompt"]

    raw = uit.response.validation_result
    assert raw["rule_statuses"]["INT-03"] == "pass"
    document = raw["rule_results"]["INT-03"]["assessment"]
    assert document["status"] == "assessed"
    assert document["prompt_version"] == Int03AssessmentService.PROMPT_VERSION
    assert document["norm_sha256"] == dienst.norm_sha256
    # Provider en model komen uit de echte ModelRouter/configuratie.
    assert document["attribution"]["provider"] == uit.provider
    assert document["attribution"]["model"] == uit.model
    assert document["attribution"]["cached"] is False
    assert document["fingerprint"] == bereken_int03_vingerafdruk(
        BEGRIP,
        uit.record.definitie,
        {"organisatorische_context": ["Testregistratie"]},
        None,
    )
    assert document["judgment"]["references"][0]["word"] == "die"
    # De keten liep door tot opslag; de kandidaat komt van de modelgrens.
    assert uit.record is not None
    assert "die" in uit.record.definitie.split()


async def test_productieroute_negatieve_uitkomst_via_de_echte_dienst_is_advisory(
    genereer_productieroute,
):
    uit = await genereer_productieroute(scenario="fail")
    raw = uit.response.validation_result
    assert raw["rule_statuses"]["INT-03"] == "fail"
    [violation] = [v for v in raw["violations"] if v.get("code") == "INT-03"]
    assert violation["severity"] == "warning"
    assert violation["metadata"]["advisory"] is True
    assert raw["rule_results"]["INT-03"]["assessment"]["judgment"]["verdict"] == "fail"
    assert uit.record is not None


def test_container_deelt_een_dienst_met_orchestrator_en_validatiewrapper(
    monkeypatch,
):
    from services.container import ServiceContainer
    from toetsregels.rule_cache import get_rule_cache

    get_rule_cache().clear_cache()
    container = ServiceContainer.__new__(ServiceContainer)
    container._instances = {}
    container.use_json_rules = True
    monkeypatch.setattr(ServiceContainer, "rag_service", property(lambda self: None))
    ai = FakeModelgrens(definitie=DEFINITIE_MET_DIE)
    monkeypatch.setattr(container, "ai_service", lambda: ai, raising=False)
    monkeypatch.setattr(container, "model_router", FakeRouter, raising=False)
    monkeypatch.setattr(container, "cleaning_service", AsyncMock, raising=False)
    monkeypatch.setattr(
        container, "repository", NullDefinitionRepository, raising=False
    )
    monkeypatch.setattr(container, "web_lookup", lambda: None, raising=False)
    monkeypatch.setattr(container, "synonym_orchestrator", lambda: None, raising=False)

    dienst = container.int03_assessment_service()
    assert isinstance(dienst, Int03AssessmentService)
    assert dienst._ai_service is ai
    orch = container.orchestrator()
    assert orch.int03_assessment_service is dienst
    assert container.validation_orchestrator().int03_assessment_service is dienst


async def test_container_dienst_stuurt_outputbudget_5000_naar_de_ai_laag(
    monkeypatch,
):
    """De tweede productieconstructie (`ServiceContainer.int03_assessment_service`,
    zonder expliciet budget) geeft bij een echte beoordeling exact 5000
    outputtokens aan de gedeelde AI-service door (Chris, 26-09-2026: max 5000
    vervangt max 2500)."""
    from services.container import ServiceContainer
    from toetsregels.rule_cache import get_rule_cache

    get_rule_cache().clear_cache()
    container = ServiceContainer.__new__(ServiceContainer)
    container._instances = {}
    container.use_json_rules = True
    ai = FakeModelgrens(definitie=DEFINITIE_MET_DIE)
    monkeypatch.setattr(container, "ai_service", lambda: ai, raising=False)
    monkeypatch.setattr(container, "model_router", FakeRouter, raising=False)

    dienst = container.int03_assessment_service()
    beoordeling = await dienst.assess(
        BEGRIP, DEFINITIE_MET_DIE, {"organisatorische_context": ["Testregistratie"]}
    )
    (call,) = ai.int03_calls
    assert call["max_tokens"] == 5000
    assert call["task_type"] == "validation"
    assert beoordeling.status == "assessed"
