"""Integratietests voor de V2-orchestrator tegen de actieve service-interfaces.

Deze suite toetst dat `DefinitionOrchestratorV2` samenwerkt met de interfaces
zoals ze nú zijn. Drie constructies uit de oude opzet zijn daarbij vervangen,
omdat ze de suite lieten hangen of niets bewezen:

* **Klassebrede propertytrucs.** De oude fixture zette
  ``validation_service.__class__.validate_definition = property(lambda self:
  self.validate_definition)``. Die getter roept zichzelf aan: elke aanroep gaf
  een ``RecursionError`` — de reden onder de oude DEF-447-xfail — én de mutatie
  landde op `AsyncMock` zelf, dus op elke andere mock in het proces. Weg.
* **Onbegrensde mocks.** De dubbels zijn nu aan hun interface gebonden
  (``MagicMock(spec=...)``) en geven concrete antwoorden voor elk pad dat de
  flow raakt.
* **De echte voorbeeldenfase.** ``create_definition`` roept
  ``voorbeelden.unified_voorbeelden.genereer_alle_voorbeelden_async`` aan; die
  functie bouwt haar eigen AI-client en negeert de geïnjecteerde ai_service —
  de andere oude DEF-447-xfail. Onder de offline-gate liep dat op zes
  voorbeeldsoorten × zes resiliencepogingen vast en overschreed de suite elk
  procesbudget. De fixture `voorbeeldengrens` geeft die ene aanroep een
  expliciet antwoord, zodat de fase wordt uitgevoerd in plaats van bevroren.

`DefinitionResponseV2.validation_result` draagt de TypedDict uit
``services.validation.interfaces``; de dubbels leveren die vorm en de
assertions lezen sleutels, geen dataclass-attributen.
"""

import uuid
from unittest.mock import MagicMock, Mock

import pytest

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
)
from services.orchestrators.definition_orchestrator_v2 import (
    DefinitionOrchestratorV2,
)
from services.validation.interfaces import (
    CONTRACT_VERSION,
    ValidationContext,
    ValidationOrchestratorInterface,
    ValidationResult,
)

pytestmark = [pytest.mark.integration]

#: Expliciet antwoord van de voorbeeldenfase; geen mockwaarde.
VOORBEELDEN: dict[str, list[str] | str] = {
    "voorbeeldzinnen": ["Voorbeeldzin een."],
    "praktijkvoorbeelden": ["Praktijkvoorbeeld een."],
    "tegenvoorbeelden": ["Tegenvoorbeeld een."],
    "synoniemen": ["verwante term"],
    "antoniemen": ["tegengestelde term"],
    "toelichting": "Bevroren toelichting.",
}

LENGTEVIOLATIE = {
    "code": "VAL-STR-002",
    "severity": "error",
    "message": "Definitie moet minimaal 20 woorden bevatten",
    "rule_id": "MIN_LENGTH",
    "category": "structuur",
}


def validatieresultaat(
    *,
    is_acceptable: bool,
    overall_score: float,
    violations: tuple[dict[str, str], ...] = (),
) -> ValidationResult:
    """Schema-conform resultaat volgens het actieve TypedDict-contract."""
    resultaat: ValidationResult = {
        "version": CONTRACT_VERSION,
        "overall_score": overall_score,
        "is_acceptable": is_acceptable,
        "violations": [dict(v) for v in violations],
        "passed_rules": ["STR-01"] if is_acceptable else [],
        "detailed_scores": {
            "taal": overall_score,
            "juridisch": overall_score,
            "structuur": overall_score,
            "samenhang": overall_score,
        },
        "system": {"correlation_id": str(uuid.uuid4())},
    }
    return resultaat


@pytest.fixture
def voorbeeldengrens(monkeypatch):
    """Geef fase 5 één expliciet antwoord en leg de doorgegeven invoer vast."""
    from voorbeelden import unified_voorbeelden

    oproepen: list[dict[str, object]] = []

    async def bevroren_voorbeelden(
        *, begrip: str, definitie: str, context_dict: dict[str, list[str]]
    ) -> dict[str, list[str] | str]:
        oproepen.append(
            {"begrip": begrip, "definitie": definitie, "context_dict": context_dict}
        )
        return dict(VOORBEELDEN)

    monkeypatch.setattr(
        unified_voorbeelden, "genereer_alle_voorbeelden_async", bevroren_voorbeelden
    )
    return oproepen


@pytest.fixture
def mock_services():
    """Servicedubbels voor de V2-orchestrator, aan hun interface gebonden."""
    ai_service = MagicMock(spec=AIServiceInterface)
    ai_service.generate_definition.return_value = AIGenerationResult(
        text="Test definitie voor het begrip",
        model="gpt-4",
        tokens_used=100,
        generation_time=1.5,
        cached=False,
        retry_count=0,
        metadata={},
    )

    prompt_service = MagicMock(spec=PromptServiceInterface)
    prompt_service.build_generation_prompt.return_value = PromptResult(
        text="Geoptimaliseerde prompt voor definitie",
        token_count=150,
        components_used=("base", "context", "feedback"),
        feedback_integrated=True,
        optimization_applied=True,
        metadata={},
    )

    security_service = MagicMock(spec=SecurityServiceInterface)
    security_service.sanitize_request.side_effect = lambda req: req

    feedback_engine = MagicMock(spec=FeedbackEngineInterface)
    feedback_engine.get_feedback_for_request.return_value = [
        {"type": "quality", "content": "Previous definition was too technical"}
    ]
    feedback_engine.process_validation_feedback.return_value = {
        "status": "processed",
        "feedback_id": "fb-123",
    }

    cleaning_service = MagicMock(spec=CleaningServiceInterface)
    cleaning_service.clean_text.return_value = CleaningResult(
        original_text="Test definitie voor het begrip",
        cleaned_text="Test definitie voor het begrip.",
        was_cleaned=True,
        applied_rules=("add_period",),
        improvements=("Added period at end",),
    )

    validation_service = MagicMock(spec=ValidationOrchestratorInterface)
    validation_service.validate_definition.return_value = validatieresultaat(
        is_acceptable=True, overall_score=0.95
    )

    enhancement_service = MagicMock(spec=EnhancementServiceInterface)
    enhancement_service.enhance_definition.return_value = "Verbeterde definitie tekst"

    monitoring_service = MagicMock(spec=MonitoringServiceInterface)
    monitoring_service.start_generation.return_value = None
    monitoring_service.complete_generation.return_value = None
    monitoring_service.track_error.return_value = None
    monitoring_service.get_metrics_summary = Mock(
        return_value={"total_generations": 100, "success_rate": 0.95}
    )

    repository = MagicMock(spec=DefinitionRepositoryInterface)
    repository.save.return_value = 123

    return {
        "ai_service": ai_service,
        "prompt_service": prompt_service,
        "security_service": security_service,
        "feedback_engine": feedback_engine,
        "cleaning_service": cleaning_service,
        "validation_service": validation_service,
        "enhancement_service": enhancement_service,
        "monitoring_service": monitoring_service,
        "repository": repository,
    }


@pytest.fixture
def v2_orchestrator(mock_services, voorbeeldengrens):
    """De echte V2-orchestrator met de begrensde dubbels erachter."""
    config = OrchestratorConfig(
        enable_feedback_loop=True, enable_enhancement=True, enable_caching=True
    )

    orchestrator = DefinitionOrchestratorV2(
        config=config,
        ai_service=mock_services["ai_service"],
        prompt_service=mock_services["prompt_service"],
        cleaning_service=mock_services["cleaning_service"],
        validation_service=mock_services["validation_service"],
        repository=mock_services["repository"],
        security_service=mock_services["security_service"],
        monitoring=mock_services["monitoring_service"],
        feedback_engine=mock_services["feedback_engine"],
        enhancement_service=mock_services["enhancement_service"],
    )

    return orchestrator, mock_services


class TestV2OrchestratorIntegration:
    """De V2-flow tegen alle service-interfaces."""

    @pytest.mark.asyncio
    async def test_complete_flow_with_all_services(
        self, v2_orchestrator, voorbeeldengrens
    ):
        """De complete V2-flow raakt elke dienst met de juiste gegevens."""
        orchestrator, services = v2_orchestrator

        request = GenerationRequest(
            id="test-123",
            begrip="testbegrip",
            context="juridische context",
            ontologische_categorie="proces",
            options={"temperature": 0.7, "max_tokens": 500},
        )

        response = await orchestrator.create_definition(
            request, context={"session": "test"}
        )

        assert isinstance(response, DefinitionResponseV2)
        assert response.success is True
        assert response.definition is not None
        assert response.definition.begrip == "testbegrip"
        assert response.definition.definitie == "Test definitie voor het begrip."

        # 1. Security-sanitisatie
        services["security_service"].sanitize_request.assert_awaited_once_with(request)

        # 2. Feedback ophalen
        services["feedback_engine"].get_feedback_for_request.assert_awaited_once_with(
            "testbegrip", "proces"
        )

        # 3. Promptopbouw met de request, de feedback en de meegegeven context
        services["prompt_service"].build_generation_prompt.assert_awaited_once()
        promptaanroep = services["prompt_service"].build_generation_prompt.await_args
        assert promptaanroep.args[0] is request
        assert promptaanroep.kwargs["feedback_history"] == [
            {"type": "quality", "content": "Previous definition was too technical"}
        ]
        assert promptaanroep.kwargs["context"] == {"session": "test"}

        # 4. AI-generatie krijgt de gebouwde prompt en de opgegeven opties
        services["ai_service"].generate_definition.assert_awaited_once()
        aianroep = services["ai_service"].generate_definition.await_args
        assert aianroep.kwargs["prompt"] == "Geoptimaliseerde prompt voor definitie"
        assert aianroep.kwargs["temperature"] == 0.7
        assert aianroep.kwargs["max_tokens"] == 500

        # 5. Voorbeeldenfase: uitgevoerd met de ruwe AI-tekst, resultaat in de
        # metadata van de definitie.
        assert len(voorbeeldengrens) == 1
        assert voorbeeldengrens[0]["begrip"] == "testbegrip"
        assert voorbeeldengrens[0]["definitie"] == "Test definitie voor het begrip"
        assert response.definition.metadata["voorbeelden"] == VOORBEELDEN

        # 6. Opschoning — met await; de opgeschoonde tekst is de definitie.
        services["cleaning_service"].clean_text.assert_awaited_once_with(
            "Test definitie voor het begrip", "testbegrip"
        )

        # 7. Validatie via de actuele signatuur: een Definition plus context.
        services["validation_service"].validate_definition.assert_awaited_once()
        validatieaanroep = services["validation_service"].validate_definition.await_args
        gevalideerd = validatieaanroep.kwargs["definition"]
        assert gevalideerd.begrip == "testbegrip"
        assert gevalideerd.definitie == "Test definitie voor het begrip."
        assert gevalideerd.ontologische_categorie == "proces"
        assert isinstance(validatieaanroep.kwargs["context"], ValidationContext)
        assert (
            validatieaanroep.kwargs["context"].metadata["generation_id"] == "test-123"
        )
        # Het resultaat in de response is de TypedDict van de dienst zelf.
        assert (
            response.validation_result
            == services["validation_service"].validate_definition.return_value
        )
        assert response.validation_result["is_acceptable"] is True

        # 8. Opslag van precies deze definitie, met het toegekende ID.
        services["repository"].save.assert_called_once_with(response.definition)
        assert response.definition.id == 123

        # 9. Monitoring rond de hele generatie.
        services["monitoring_service"].start_generation.assert_awaited_once_with(
            "test-123"
        )
        services["monitoring_service"].complete_generation.assert_awaited_once()
        afronding = services["monitoring_service"].complete_generation.await_args
        assert afronding.kwargs["success"] is True
        assert afronding.kwargs["token_count"] == 100
        services["monitoring_service"].track_error.assert_not_called()

    @pytest.mark.asyncio
    async def test_enhancement_flow_on_validation_failure(self, v2_orchestrator):
        """Mislukte validatie leidt tot verbetering met de juiste signatuur."""
        orchestrator, services = v2_orchestrator

        mislukt = validatieresultaat(
            is_acceptable=False, overall_score=0.2, violations=(LENGTEVIOLATIE,)
        )
        services["validation_service"].validate_definition.return_value = mislukt

        request = GenerationRequest(
            id="test-456", begrip="complexbegrip", ontologische_categorie="object"
        )

        response = await orchestrator.create_definition(request)

        services["enhancement_service"].enhance_definition.assert_awaited_once()
        aanroep = services["enhancement_service"].enhance_definition.await_args
        assert aanroep.args[0] == "Test definitie voor het begrip."
        assert aanroep.args[1] == [LENGTEVIOLATIE]
        assert aanroep.kwargs["context"] is request

        # Hervalidatie van de verbeterde tekst, en die tekst is de uitkomst.
        assert services["validation_service"].validate_definition.await_count == 2
        hervalidatie = services[
            "validation_service"
        ].validate_definition.await_args_list[1]
        assert (
            hervalidatie.kwargs["definition"].definitie == "Verbeterde definitie tekst"
        )
        assert response.definition.definitie == "Verbeterde definitie tekst"
        assert response.metadata["enhanced"] is True
        assert response.definition.valid is False
        assert response.definition.validation_violations == [LENGTEVIOLATIE]

    @pytest.mark.asyncio
    async def test_error_handling_and_monitoring(self, v2_orchestrator):
        """Een falende AI-dienst geeft een foutresponse en wordt gemonitord."""
        orchestrator, services = v2_orchestrator

        services["ai_service"].generate_definition.side_effect = Exception(
            "AI Service Error"
        )

        request = GenerationRequest(id="test-789", begrip="errorbegrip")

        response = await orchestrator.create_definition(request)

        assert response.success is False
        assert response.definition is None
        assert response.error is not None
        assert "AI Service Error" in response.error
        assert response.metadata["error_type"] == "Exception"

        services["monitoring_service"].track_error.assert_awaited_once()
        foutaanroep = services["monitoring_service"].track_error.await_args
        assert foutaanroep.args[0] == "test-789"
        assert isinstance(foutaanroep.args[1], Exception)
        assert str(foutaanroep.args[1]) == "AI Service Error"
        # De flow stopt: geen opslag en geen afronding meer.
        services["repository"].save.assert_not_called()
        services["monitoring_service"].complete_generation.assert_not_called()

    @pytest.mark.asyncio
    async def test_feedback_integration(self, v2_orchestrator):
        """De feedback-engine voedt de promptopbouw van deze generatie."""
        orchestrator, services = v2_orchestrator

        services["feedback_engine"].get_feedback_for_request.return_value = [
            {"type": "quality", "content": "Avoid technical jargon"},
            {"type": "accuracy", "content": "Include practical examples"},
        ]

        request = GenerationRequest(
            id="test-feedback",
            begrip="feedbackbegrip",
            ontologische_categorie="handeling",
        )

        response = await orchestrator.create_definition(request)

        services["feedback_engine"].get_feedback_for_request.assert_awaited_with(
            "feedbackbegrip", "handeling"
        )

        promptaanroep = services["prompt_service"].build_generation_prompt.await_args
        feedback_history = promptaanroep.kwargs["feedback_history"]
        assert len(feedback_history) == 2
        assert feedback_history[0]["type"] == "quality"
        assert feedback_history[1]["content"] == "Include practical examples"
        assert response.metadata["feedback_integrated"] is True

    @pytest.mark.asyncio
    async def test_cleaning_service_async_await(self, v2_orchestrator):
        """De opschoondienst wordt geawait, niet als coroutine doorgegeven."""
        orchestrator, services = v2_orchestrator

        geziene_aanroepen: list[tuple[str, str]] = []

        async def echte_async_clean_text(text: str, term: str) -> CleaningResult:
            # Een gewone coroutinefunctie zonder sleep: als de orchestrator haar
            # niet zou awaiten, is `cleaning_result` een coroutine en valt de
            # generatie om op `.cleaned_text`.
            geziene_aanroepen.append((text, term))
            return CleaningResult(
                original_text=text, cleaned_text=f"{text} (cleaned)", was_cleaned=True
            )

        services["cleaning_service"].clean_text = echte_async_clean_text

        request = GenerationRequest(id="test-clean", begrip="cleantest")

        response = await orchestrator.create_definition(request)

        assert response.success is True, f"generatie mislukt: {response.error}"
        assert geziene_aanroepen == [("Test definitie voor het begrip", "cleantest")]
        assert (
            response.definition.definitie == "Test definitie voor het begrip (cleaned)"
        )
