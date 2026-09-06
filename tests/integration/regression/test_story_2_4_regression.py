"""
Story 2.4 Regression Test Suite

Regressietests op de *actuele* V2-interfaces. De elf oorspronkelijke intenties
zijn behouden; alleen het contract waartegen zij toetsen is bijgewerkt.

DEF-519 — wat er is bijgesteld:

* acht nodes riepen het verwijderde ``container.get_orchestrator()`` aan; de
  huidige fabriek is ``container.orchestrator()``;
* de drie losse validatieproeven gaven hun dubbel een dict zonder ``version``/
  ``system``. ``ensure_schema_compliance`` degradeert zo'n resultaat, waardoor
  hun assertions op violations/score niets meer over de invoer zeiden. De
  dubbels leveren nu het schema-conforme TypedDict-contract;
* ``if response.definition`` / ``if response.validation_result`` maakten
  afwezig gedrag groen; er wordt nu op aanwezigheid én concrete waarden
  geasserteerd.

Synthetische grenzen (eerlijk benoemd, geen full-pipelineclaim):

* de servicegrenzen van de orchestrator (prompt/ai/cleaning/validation) zijn
  interfacegebonden dubbels met vastgelegde antwoorden;
* fase 5 (``genereer_alle_voorbeelden_async``) bouwt een eigen AI-client en
  wordt door één bevroren antwoord vervangen;
* de performancegrenzen 0,5s gemiddeld / 1s maximum zijn behouden en meten
  uitsluitend de orchestratie *tussen* die grenzen — geen providerlatency.

De volledige integratie wordt elders bewezen (kernjourney); die wordt hier niet
elf keer herbouwd.
"""

import asyncio
import uuid
from typing import Any
from unittest.mock import MagicMock

import pytest

from domain.ontological_categories import OntologischeCategorie
from services.container import ContainerConfigs, ServiceContainer
from services.interfaces import (
    AIGenerationResult,
    AIServiceInterface,
    CleaningResult,
    CleaningServiceInterface,
    DefinitionRepositoryInterface,
    DefinitionResponseV2,
    EnhancementServiceInterface,
    FeedbackEngineInterface,
    GenerationRequest,
    MonitoringServiceInterface,
    OrchestratorConfig,
    PromptResult,
    PromptServiceInterface,
    SecurityServiceInterface,
    ValidationServiceInterface,
)
from services.orchestrators.definition_orchestrator_v2 import DefinitionOrchestratorV2
from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2
from services.validation.interfaces import (
    CONTRACT_VERSION,
    ValidationOrchestratorInterface,
    ValidationResult,
)

pytestmark = [pytest.mark.regression]

DEFINITIETEKST = (
    "automatisering: het gebruik van technologie om processen uit te voeren."
)

VOORBEELDEN: dict[str, list[str] | str] = {
    "voorbeeldzinnen": ["Voorbeeldzin een."],
    "praktijkvoorbeelden": ["Praktijkvoorbeeld een."],
    "tegenvoorbeelden": ["Tegenvoorbeeld een."],
    "synoniemen": ["mechanisering"],
    "antoniemen": ["handwerk"],
    "toelichting": "Bevroren toelichting.",
}


def validatieresultaat(
    *,
    is_acceptable: bool,
    overall_score: float,
    violations: tuple[dict[str, str], ...] = (),
    passed_rules: tuple[str, ...] = ("VAL-EMP-001", "VAL-LEN-001"),
) -> ValidationResult:
    """Schema-conform resultaat volgens het actieve TypedDict-contract.

    Met ``version`` en ``system`` laat ``ensure_schema_compliance`` het object
    ongewijzigd door, dus toetsen de assertions de invoer en niet een degraded
    vervanging.
    """
    resultaat: ValidationResult = {
        "version": CONTRACT_VERSION,
        "overall_score": overall_score,
        "is_acceptable": is_acceptable,
        "violations": [dict(v) for v in violations],
        "passed_rules": list(passed_rules),
        "detailed_scores": {
            "taal": overall_score,
            "juridisch": overall_score,
            "structuur": overall_score,
            "samenhang": overall_score,
        },
        "system": {"correlation_id": str(uuid.uuid4())},
    }
    return resultaat


def _sluit_containerverbindingen(container: Any) -> None:
    """Sluit de SQLite-verbindingen die deze container zelf opende."""
    from database.db_connection import DatabaseConnection

    gezien: set[int] = set()
    for instantie in list(getattr(container, "_instances", {}).values()):
        for houder in (instantie, getattr(instantie, "legacy_repo", None)):
            db = getattr(houder, "_db", None)
            if not isinstance(db, DatabaseConnection) or id(db) in gezien:
                continue
            gezien.add(id(db))
            toestand = getattr(getattr(db, "_thread_local", None), "state", None)
            if toestand is not None:
                toestand.close()


class TestStory24RegressionSuite:
    """Regression tests for Story 2.4 interface migration."""

    @pytest.fixture
    def container(self, tmp_path):
        """Echte ServiceContainer op een eigen tijdelijke database."""
        container = ServiceContainer(
            {**ContainerConfigs.testing(), "db_path": str(tmp_path / "regressie.db")}
        )
        try:
            yield container
        finally:
            _sluit_containerverbindingen(container)

    @pytest.fixture
    def voorbeeldengrens(self, monkeypatch):
        """Bevries fase 5: die bouwt een eigen AI-client (offline-gate)."""
        from voorbeelden import unified_voorbeelden

        async def bevroren_voorbeelden(
            *, begrip: str, definitie: str, context_dict: dict[str, list[str]]
        ) -> dict[str, list[str] | str]:
            return dict(VOORBEELDEN)

        monkeypatch.setattr(
            unified_voorbeelden,
            "genereer_alle_voorbeelden_async",
            bevroren_voorbeelden,
        )

    @pytest.fixture
    def grenzen(self, baseline_generation_request):
        """Interfacegebonden dubbels met vastgelegde antwoorden.

        De servicevelden van `DefinitionOrchestratorV2` zijn read-only
        properties, dus de dubbels gaan via de constructor. Dat is dezelfde
        opzet als de gerepareerde orchestratorproeven.
        """
        prompt_service = MagicMock(spec=PromptServiceInterface)
        prompt_service.build_generation_prompt.return_value = PromptResult(
            text="Standard regression test prompt",
            token_count=100,
            components_used=("base",),
            feedback_integrated=False,
            optimization_applied=False,
            metadata={},
        )

        ai_service = MagicMock(spec=AIServiceInterface)
        ai_service.generate_definition.return_value = AIGenerationResult(
            text=DEFINITIETEKST,
            model="gpt-4",
            tokens_used=150,
            generation_time=0.1,
        )

        cleaning_service = MagicMock(spec=CleaningServiceInterface)
        cleaning_service.clean_text.return_value = CleaningResult(
            original_text=DEFINITIETEKST,
            cleaned_text=DEFINITIETEKST,
            was_cleaned=False,
        )

        validation_service = MagicMock(spec=ValidationOrchestratorInterface)
        validation_service.validate_definition.return_value = validatieresultaat(
            is_acceptable=True, overall_score=0.9
        )

        enhancement_service = MagicMock(spec=EnhancementServiceInterface)
        enhancement_service.enhance_definition.return_value = DEFINITIETEKST

        security_service = MagicMock(spec=SecurityServiceInterface)
        security_service.sanitize_request.return_value = baseline_generation_request

        feedback_engine = MagicMock(spec=FeedbackEngineInterface)
        feedback_engine.get_feedback_for_request.return_value = []
        feedback_engine.process_validation_feedback.return_value = {
            "status": "processed"
        }

        repository = MagicMock(spec=DefinitionRepositoryInterface)
        repository.save.return_value = 42

        monitoring = MagicMock(spec=MonitoringServiceInterface)
        monitoring.start_generation.return_value = None
        monitoring.complete_generation.return_value = None
        monitoring.track_error.return_value = None

        return {
            "prompt_service": prompt_service,
            "ai_service": ai_service,
            "validation_service": validation_service,
            "enhancement_service": enhancement_service,
            "security_service": security_service,
            "cleaning_service": cleaning_service,
            "repository": repository,
            "monitoring": monitoring,
            "feedback_engine": feedback_engine,
        }

    @pytest.fixture
    def orchestrator(self, grenzen, voorbeeldengrens):
        """De echte orchestrator achter de begrensde dubbels."""
        return DefinitionOrchestratorV2(**grenzen, config=OrchestratorConfig())

    @pytest.fixture
    def baseline_generation_request(self):
        """Standard generation request for consistent testing."""
        return GenerationRequest(
            id="test-id",
            begrip="automatisering",
            context="informatiesystemen",
            ontologische_categorie=OntologischeCategorie.PROCES.value,
            organisatorische_context=["DJI"],
            actor="regression-test",
        )

    @pytest.fixture
    def expected_validation_result_structure(self):
        """Expected validation result structure for regression testing."""
        return {
            "version": str,
            "overall_score": float,
            "is_acceptable": bool,
            "violations": list,
            "passed_rules": list,
            "detailed_scores": dict,
            "system": dict,
        }

    # ========================================
    # REGRESSION TEST 1: API RESPONSE FORMATS
    # ========================================

    @pytest.mark.regression
    @pytest.mark.asyncio
    async def test_definition_response_v2_format_preserved(
        self, orchestrator, baseline_generation_request
    ):
        """Regression test: DefinitionResponseV2 format must remain consistent."""
        response = await orchestrator.create_definition(baseline_generation_request)

        assert isinstance(response, DefinitionResponseV2)
        assert response.success is True, response.error

        # Kritieke velden waarop externe consumenten steunen.
        assert hasattr(response, "success")
        assert hasattr(response, "definition")
        assert hasattr(response, "validation_result")
        assert hasattr(response, "metadata")
        assert hasattr(response, "error")

        # Aanwezigheid én inhoud: geen `if response.definition`-ontsnapping.
        definition = response.definition
        assert definition is not None
        assert definition.begrip == baseline_generation_request.begrip
        assert definition.definitie == DEFINITIETEKST
        assert (
            definition.ontologische_categorie
            == baseline_generation_request.ontologische_categorie
        )
        assert definition.valid is True
        assert definition.validation_violations == []

    @pytest.mark.regression
    @pytest.mark.asyncio
    async def test_validation_result_format_preserved(
        self,
        orchestrator,
        baseline_generation_request,
        expected_validation_result_structure,
    ):
        """Regression test: ValidationResult format must remain consistent."""
        response = await orchestrator.create_definition(baseline_generation_request)

        validation_result = response.validation_result
        assert validation_result is not None

        for field, expected_type in expected_validation_result_structure.items():
            assert field in validation_result, f"Missing field: {field}"
            assert isinstance(
                validation_result[field], expected_type
            ), f"Field {field} has wrong type: {type(validation_result[field])}"

        assert validation_result["version"] == CONTRACT_VERSION
        assert 0.0 <= validation_result["overall_score"] <= 1.0
        assert validation_result["is_acceptable"] is True
        assert "correlation_id" in validation_result["system"]

    # ========================================
    # REGRESSION TEST 2: PERFORMANCE
    # ========================================

    @pytest.mark.regression
    @pytest.mark.asyncio
    async def test_no_performance_regression(
        self, orchestrator, baseline_generation_request
    ):
        """Regression test: Story 2.4 must not introduce significant degradation.

        Scope: de orchestratie tussen de synthetische servicegrenzen. Geen
        uitspraak over provider- of pipelinelatency.
        """
        import time

        execution_times = []
        for _ in range(5):
            start_time = time.perf_counter()
            response = await orchestrator.create_definition(baseline_generation_request)
            execution_times.append(time.perf_counter() - start_time)

            assert response.success, "Generation should succeed for performance test"

        avg_time = sum(execution_times) / len(execution_times)
        max_time = max(execution_times)

        MAX_ACCEPTABLE_AVG_TIME = 0.5  # 500ms average
        MAX_ACCEPTABLE_MAX_TIME = 1.0  # 1s maximum

        assert (
            avg_time < MAX_ACCEPTABLE_AVG_TIME
        ), f"Performance regression: average {avg_time:.3f}s > {MAX_ACCEPTABLE_AVG_TIME}s"
        assert (
            max_time < MAX_ACCEPTABLE_MAX_TIME
        ), f"Performance regression: max {max_time:.3f}s > {MAX_ACCEPTABLE_MAX_TIME}s"

    # ========================================
    # REGRESSION TEST 3: BUSINESS LOGIC CONSISTENCY
    # ========================================

    @pytest.mark.regression
    @pytest.mark.asyncio
    async def test_business_logic_consistency(
        self, orchestrator, grenzen, baseline_generation_request
    ):
        """Regression test: Business logic outcomes must remain consistent."""
        grenzen["validation_service"].validate_definition.return_value = (
            validatieresultaat(
                is_acceptable=True,
                overall_score=0.85,
                passed_rules=("VAL-EMP-001", "VAL-LEN-001", "ESS-CONT-001"),
            )
        )

        response = await orchestrator.create_definition(baseline_generation_request)

        assert response.success is True, response.error
        assert response.definition is not None
        assert response.definition.begrip == baseline_generation_request.begrip
        assert (
            response.definition.ontologische_categorie
            == baseline_generation_request.ontologische_categorie
        )

        assert response.validation_result is not None
        assert response.validation_result["overall_score"] == 0.85
        assert response.validation_result["is_acceptable"] is True

        assert response.metadata is not None
        assert response.metadata["orchestrator_version"] == "v2.0"
        assert response.metadata["generation_id"] == baseline_generation_request.id
        assert (
            response.metadata["ontological_category"]
            == baseline_generation_request.ontologische_categorie
        )

    @pytest.mark.regression
    @pytest.mark.asyncio
    async def test_validation_scores_consistency(self, orchestrator, grenzen):
        """Regression test: Validation scoring logic must remain consistent."""
        test_request = GenerationRequest(
            id="scores-id",
            begrip="regressietest",
            context="gestandaardiseerde testcontext",
            # 'object' bestaat niet in OntologischeCategorie; geldige invoer was
            # bedoeld, dus een actuele enumwaarde.
            ontologische_categorie=OntologischeCategorie.TYPE.value,
            organisatorische_context=["DJI"],
            actor="regression-test",
        )
        grenzen["security_service"].sanitize_request.return_value = test_request
        grenzen["validation_service"].validate_definition.return_value = (
            validatieresultaat(
                is_acceptable=True,
                overall_score=0.75,
                violations=(
                    {
                        "code": "STR-TERM-001",
                        "severity": "warning",
                        "message": "Terminology could be improved",
                        "rule_id": "STR-TERM-001",
                        "category": "structuur",
                    },
                ),
                passed_rules=("VAL-EMP-001", "CON-CIRC-001"),
            )
        )

        response = await orchestrator.create_definition(test_request)

        validation_result = response.validation_result
        assert validation_result is not None
        assert validation_result["overall_score"] == 0.75

        detailed_scores = validation_result["detailed_scores"]
        assert detailed_scores, "detailed_scores moet gevuld zijn"
        for category, score in detailed_scores.items():
            assert isinstance(score, int | float)
            assert 0.0 <= score <= 1.0, f"Score {score} for {category} out of range"

        assert any(
            v["code"] == "STR-TERM-001" for v in validation_result["violations"]
        ), validation_result["violations"]

    # ========================================
    # REGRESSION TEST 4: ERROR HANDLING
    # ========================================

    @pytest.mark.regression
    @pytest.mark.asyncio
    async def test_error_handling_regression(
        self, orchestrator, grenzen, baseline_generation_request
    ):
        """Regression test: Error handling behavior must remain consistent."""
        # Echte foutinjectie op de promptgrens.
        grenzen["prompt_service"].build_generation_prompt.side_effect = Exception(
            "Prompt service error"
        )

        response = await orchestrator.create_definition(baseline_generation_request)

        assert isinstance(response, DefinitionResponseV2)
        assert response.success is False
        assert response.error is not None
        assert "Prompt service error" in response.error
        assert response.definition is None

        assert response.metadata is not None
        assert response.metadata["generation_id"] == baseline_generation_request.id
        assert response.metadata["error_type"] == "Exception"

    # ========================================
    # REGRESSION TEST 5: INTERFACE COMPATIBILITY
    # ========================================

    @pytest.mark.regression
    def test_orchestrator_interface_compatibility(self, container):
        """Regression test: Orchestrator interface must remain compatible."""
        # Contractmapping: de oude fabriek bestaat niet meer.
        assert not hasattr(container, "get_orchestrator")

        orchestrator = container.orchestrator()

        required_methods = [
            "create_definition",
            "update_definition",
            "validate_and_save",
        ]
        for method_name in required_methods:
            assert hasattr(orchestrator, method_name), f"Missing method: {method_name}"

        assert isinstance(orchestrator, DefinitionOrchestratorV2)
        # Huidige DI: dezelfde fabriek levert dezelfde instantie.
        assert container.orchestrator() is orchestrator

    @pytest.mark.regression
    def test_validation_service_interface_change_handled(self, container):
        """Regression test: ValidationOrchestratorInterface integration handled."""
        validation_service = container.orchestrator().validation_service

        assert isinstance(validation_service, ValidationOrchestratorInterface)
        for method_name in ("validate_text", "validate_definition", "batch_validate"):
            assert hasattr(
                validation_service, method_name
            ), f"ValidationOrchestratorInterface missing method: {method_name}"


class TestStory24RegressionEdgeCases:
    """Edge case regression tests for Story 2.4."""

    @staticmethod
    def _validatiedienst(resultaat: ValidationResult) -> MagicMock:
        """Dubbel van de onderliggende validatiedienst, aan zijn interface gebonden."""
        dienst = MagicMock(spec=ValidationServiceInterface)
        dienst.validate_definition.return_value = resultaat
        return dienst

    @pytest.mark.regression
    @pytest.mark.asyncio
    async def test_empty_text_validation_regression(self):
        """Regression test: Empty text validation should still work."""
        leeg_resultaat = validatieresultaat(
            is_acceptable=False,
            overall_score=0.0,
            violations=({"code": "VAL-EMP-001", "message": "Empty definition"},),
            passed_rules=(),
        )
        dienst = self._validatiedienst(leeg_resultaat)
        orchestrator = ValidationOrchestratorV2(dienst)

        result = await orchestrator.validate_text("begrip", "")

        assert result["is_acceptable"] is False
        assert result["overall_score"] == 0.0
        assert any(v.get("code") == "VAL-EMP-001" for v in result["violations"])
        # De lege tekst is werkelijk doorgegeven, niet vervangen.
        assert dienst.validate_definition.call_args.kwargs["text"] == ""

    @pytest.mark.regression
    @pytest.mark.asyncio
    async def test_unicode_handling_regression(self):
        """Regression test: Unicode text handling should remain consistent."""
        dienst = self._validatiedienst(
            validatieresultaat(is_acceptable=True, overall_score=0.8)
        )
        orchestrator = ValidationOrchestratorV2(dienst)

        unicode_text = "begrip: een definîtie met specìale karakters en émoji 🚀"
        result = await orchestrator.validate_text("unicode-begrip", unicode_text)

        assert result["is_acceptable"] is True
        assert result["overall_score"] == 0.8

        call_kwargs = dienst.validate_definition.call_args.kwargs
        assert call_kwargs["text"] == unicode_text
        assert call_kwargs["begrip"] == "unicode-begrip"

    @pytest.mark.regression
    @pytest.mark.asyncio
    async def test_concurrent_validation_regression(self):
        """Regression test: Concurrent validation should still work properly."""
        dienst = self._validatiedienst(
            validatieresultaat(is_acceptable=True, overall_score=0.8)
        )
        orchestrator = ValidationOrchestratorV2(dienst)

        tasks = [
            orchestrator.validate_text(f"begrip{i}", f"definitie {i}") for i in range(5)
        ]
        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        assert all(result["is_acceptable"] for result in results)

        # Alle vijf verzoeken zijn werkelijk doorgegeven, elk met eigen invoer.
        doorgegeven = {
            aanroep.kwargs["begrip"]
            for aanroep in dienst.validate_definition.call_args_list
        }
        assert doorgegeven == {f"begrip{i}" for i in range(5)}
