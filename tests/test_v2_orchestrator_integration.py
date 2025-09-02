"""
Integration tests voor V2 orchestrator met alle service interfaces.

Deze tests verifiëren dat de V2 orchestrator correct werkt met
alle aangepaste service interfaces na de codex fixes.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, Mock
from datetime import datetime

import pytest

from src.services.orchestrators.definition_orchestrator_v2 import DefinitionOrchestratorV2
from src.services.interfaces import (
    AIGenerationResult,
    CleaningResult,
    Definition,
    DefinitionResponseV2,
    GenerationRequest,
    OrchestratorConfig,
    PromptResult,
    ValidationResult,
    ValidationViolation,
)


@pytest.fixture
def mock_services():
    """Create mock services voor V2 orchestrator testing."""
    # AI Service
    ai_service = AsyncMock()
    ai_service.generate_definition = AsyncMock(return_value=AIGenerationResult(
        text="Test definitie voor het begrip",
        model="gpt-4",
        tokens_used=100,
        generation_time=1.5,
        cached=False,
        retry_count=0,
        metadata={}
    ))

    # Prompt Service
    prompt_service = AsyncMock()
    prompt_service.build_generation_prompt = AsyncMock(return_value=PromptResult(
        text="Geoptimaliseerde prompt voor definitie",
        token_count=150,
        components_used=["base", "context", "feedback"],
        feedback_integrated=True,
        optimization_applied=True,
        metadata={}
    ))

    # Security Service
    security_service = AsyncMock()
    security_service.sanitize_request = AsyncMock(side_effect=lambda req: req)

    # Feedback Engine
    feedback_engine = AsyncMock()
    feedback_engine.get_feedback_for_request = AsyncMock(return_value=[
        {"type": "quality", "content": "Previous definition was too technical"}
    ])
    feedback_engine.process_validation_feedback = AsyncMock(return_value={
        "status": "processed",
        "feedback_id": "fb-123"
    })

    # Cleaning Service
    cleaning_service = AsyncMock()
    cleaning_service.clean_text = AsyncMock(return_value=CleaningResult(
        original_text="Test definitie voor het begrip",
        cleaned_text="Test definitie voor het begrip.",
        was_cleaned=True,
        applied_rules=["add_period"],
        improvements=["Added period at end"]
    ))
    # Add hasattr support for cleaning service
    cleaning_service.__class__.clean_text = property(lambda self: self.clean_text)

    # Validation Service
    validation_service = AsyncMock()
    validation_service.validate_definition = AsyncMock(return_value=ValidationResult(
        is_valid=True,
        definition_text="Test definitie voor het begrip.",
        errors=[],
        warnings=[],
        suggestions=[],
        score=0.95,
        violations=[]
    ))
    # Add hasattr support
    validation_service.__class__.validate_definition = property(lambda self: self.validate_definition)

    # Enhancement Service
    enhancement_service = AsyncMock()
    enhancement_service.enhance_definition = AsyncMock(return_value="Verbeterde definitie tekst")

    # Monitoring Service
    monitoring_service = AsyncMock()
    monitoring_service.start_generation = AsyncMock()
    monitoring_service.complete_generation = AsyncMock()
    monitoring_service.track_error = AsyncMock()
    monitoring_service.get_metrics_summary = Mock(return_value={
        "total_generations": 100,
        "success_rate": 0.95
    })

    # Repository
    repository = Mock()
    repository.save = Mock(return_value=123)

    return {
        "ai_service": ai_service,
        "prompt_service": prompt_service,
        "security_service": security_service,
        "feedback_engine": feedback_engine,
        "cleaning_service": cleaning_service,
        "validation_service": validation_service,
        "enhancement_service": enhancement_service,
        "monitoring_service": monitoring_service,
        "repository": repository
    }


@pytest.fixture
def v2_orchestrator(mock_services):
    """Create V2 orchestrator met mock services."""
    config = OrchestratorConfig(
        enable_feedback_loop=True,
        enable_enhancement=True,
        enable_caching=True
    )

    orchestrator = DefinitionOrchestratorV2(
        config=config,
        ai_service=mock_services["ai_service"],
        prompt_service=mock_services["prompt_service"],
        cleaning_service=mock_services["cleaning_service"],
        validation_service=mock_services["validation_service"],
        repository=mock_services["repository"],
        security_service=mock_services["security_service"],
        monitoring_service=mock_services["monitoring_service"],
        feedback_engine=mock_services["feedback_engine"],
        enhancement_service=mock_services["enhancement_service"]
    )

    return orchestrator, mock_services


class TestV2OrchestratorIntegration:
    """Test suite voor V2 orchestrator met alle service interfaces."""

    @pytest.mark.asyncio
    async def test_complete_flow_with_all_services(self, v2_orchestrator):
        """Test complete V2 flow met alle services."""
        orchestrator, services = v2_orchestrator

        request = GenerationRequest(
            id="test-123",
            begrip="testbegrip",
            context="juridische context",
            ontologische_categorie="proces",
            options={"temperature": 0.7, "max_tokens": 500}
        )

        # Execute orchestration
        response = await orchestrator.create_definition(request, context={"session": "test"})

        # Verify response
        assert isinstance(response, DefinitionResponseV2)
        assert response.success is True
        assert response.definition is not None
        assert response.definition.begrip == "testbegrip"
        assert response.definition.definitie == "Test definitie voor het begrip."

        # Verify service calls in correct order
        # 1. Security sanitization
        services["security_service"].sanitize_request.assert_called_once_with(request)

        # 2. Feedback retrieval
        services["feedback_engine"].get_feedback_for_request.assert_called_once_with(
            "testbegrip", "proces"
        )

        # 3. Prompt building
        services["prompt_service"].build_generation_prompt.assert_called_once()
        call_args = services["prompt_service"].build_generation_prompt.call_args
        assert call_args[0][0] == request  # First positional arg
        assert "feedback_history" in call_args[1]  # Keyword args
        assert "context" in call_args[1]

        # 4. AI generation
        services["ai_service"].generate_definition.assert_called_once()

        # 5. Text cleaning (WITH await!)
        services["cleaning_service"].clean_text.assert_called_once_with(
            "Test definitie voor het begrip",
            "testbegrip"
        )

        # 6. Validation
        services["validation_service"].validate_definition.assert_called_once_with(
            "testbegrip",
            "Test definitie voor het begrip.",
            ontologische_categorie="proces"
        )

        # 7. Repository save
        services["repository"].save.assert_called_once()

        # 8. Monitoring calls
        services["monitoring_service"].start_generation.assert_called()
        services["monitoring_service"].complete_generation.assert_called()

    @pytest.mark.asyncio
    async def test_enhancement_flow_on_validation_failure(self, v2_orchestrator):
        """Test enhancement flow wanneer validatie faalt."""
        orchestrator, services = v2_orchestrator

        # Setup validation failure
        services["validation_service"].validate_definition.return_value = ValidationResult(
            is_valid=False,
            definition_text="Test definitie.",
            errors=["Definitie te kort"],
            violations=[ValidationViolation(
                rule_id="MIN_LENGTH",
                severity="high",
                description="Definitie moet minimaal 20 woorden bevatten"
            )]
        )

        request = GenerationRequest(
            id="test-456",
            begrip="complexbegrip",
            ontologische_categorie="object"
        )

        # Execute orchestration
        response = await orchestrator.create_definition(request)

        # Verify enhancement was called with correct signature
        services["enhancement_service"].enhance_definition.assert_called_once()
        call_args = services["enhancement_service"].enhance_definition.call_args
        assert isinstance(call_args[0][0], str)  # text
        assert isinstance(call_args[0][1], list)  # violations
        assert call_args[1]["context"] == request  # context kwarg

    @pytest.mark.asyncio
    async def test_error_handling_and_monitoring(self, v2_orchestrator):
        """Test error handling en monitoring integratie."""
        orchestrator, services = v2_orchestrator

        # Setup AI service failure
        services["ai_service"].generate_definition.side_effect = Exception("AI Service Error")

        request = GenerationRequest(id="test-789", begrip="errorbegrip")

        # Execute and expect failure
        response = await orchestrator.create_definition(request)

        assert response.success is False
        assert response.error is not None
        assert "AI Service Error" in response.error

        # Verify monitoring tracked the error
        services["monitoring_service"].track_error.assert_called()
        error_call = services["monitoring_service"].track_error.call_args
        assert "test-789" in str(error_call[0][0])  # generation_id
        assert isinstance(error_call[0][1], Exception)  # error

    @pytest.mark.asyncio
    async def test_feedback_integration(self, v2_orchestrator):
        """Test feedback engine integration in V2 flow."""
        orchestrator, services = v2_orchestrator

        # Setup mock feedback
        services["feedback_engine"].get_feedback_for_request.return_value = [
            {"type": "quality", "content": "Avoid technical jargon"},
            {"type": "accuracy", "content": "Include practical examples"}
        ]

        request = GenerationRequest(
            id="test-feedback",
            begrip="feedbackbegrip",
            ontologische_categorie="handeling"
        )

        response = await orchestrator.create_definition(request)

        # Verify feedback was retrieved
        services["feedback_engine"].get_feedback_for_request.assert_called_with(
            "feedbackbegrip", "handeling"
        )

        # Verify feedback was passed to prompt service
        prompt_call = services["prompt_service"].build_generation_prompt.call_args
        feedback_history = prompt_call[1]["feedback_history"]
        assert len(feedback_history) == 2
        assert feedback_history[0]["type"] == "quality"

    @pytest.mark.asyncio
    async def test_cleaning_service_async_await(self, v2_orchestrator):
        """Specifieke test voor async/await van cleaning service."""
        orchestrator, services = v2_orchestrator

        # Track dat clean_text een coroutine retourneert
        async def mock_clean_text(text, term):
            await asyncio.sleep(0.01)  # Simuleer async werk
            return CleaningResult(
                original_text=text,
                cleaned_text=f"{text} (cleaned)",
                was_cleaned=True
            )

        services["cleaning_service"].clean_text = mock_clean_text

        request = GenerationRequest(id="test-clean", begrip="cleantest")

        # Dit zou NIET moeten falen met "coroutine was never awaited"
        response = await orchestrator.create_definition(request)

        assert response.success is True
        assert "(cleaned)" in response.definition.definitie


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
