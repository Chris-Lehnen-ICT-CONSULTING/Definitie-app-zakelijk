"""
Tests for DefinitionOrchestratorV2.

This test suite ensures the V2 orchestrator works correctly with:
- All 11 phases of the orchestration flow
- Ontological category integration (fixes template selection bug)
- GVI Rode Kabel feedback integration
- DPIA/AVG compliance
- Error handling and monitoring
"""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.interfaces import (Definition, DefinitionResponseV2,
                                 GenerationRequest, OrchestratorConfig,
                                 PromptResult, ValidationResult,
                                 ValidationSeverity, ValidationViolation)
from services.orchestrators.definition_orchestrator_v2 import \
    DefinitionOrchestratorV2


class TestDefinitionOrchestratorV2:
    """Test suite for DefinitionOrchestratorV2."""

    @pytest.fixture()
    def mock_services(self):
        """Create mock services for testing."""
        return {
            "prompt_service": AsyncMock(),
            "ai_service": AsyncMock(),
            "validation_service": AsyncMock(),
            "enhancement_service": AsyncMock(),
            "security_service": AsyncMock(),
            "cleaning_service": AsyncMock(),
            "repository": MagicMock(),
            "monitoring": AsyncMock(),
            "feedback_engine": AsyncMock(),
        }

    @pytest.fixture()
    def orchestrator(self, mock_services):
        """Create orchestrator with mock services."""
        return DefinitionOrchestratorV2(
            prompt_service=mock_services["prompt_service"],
            ai_service=mock_services["ai_service"],
            validation_service=mock_services["validation_service"],
            enhancement_service=mock_services["enhancement_service"],
            security_service=mock_services["security_service"],
            cleaning_service=mock_services["cleaning_service"],
            repository=mock_services["repository"],
            monitoring=mock_services["monitoring"],
            feedback_engine=mock_services["feedback_engine"],
            config=OrchestratorConfig(),
        )

    @pytest.fixture()
    def sample_request(self):
        """Create sample generation request with ontological category."""
        return GenerationRequest(
            id="test-123",
            begrip="verificatie",
            context="DJI detentiesysteem",
            ontologische_categorie="proces",  # Critical: test ontological category
            actor="test_user",
            legal_basis="legitimate_interest",
        )

    @pytest.mark.asyncio()
    async def test_successful_generation_with_ontological_category(
        self, orchestrator, mock_services, sample_request
    ):
        """Test successful generation with proper ontological category handling."""
        # Setup mocks for successful flow
        mock_services["security_service"].sanitize_request.return_value = sample_request
        mock_services["feedback_engine"].get_feedback_for_request.return_value = []

        # Mock prompt service with ontological category support
        mock_services["prompt_service"].build_generation_prompt.return_value = (
            PromptResult(
                text="Test prompt with ontological category",
                token_count=50,
                components_used=["ontologie_proces"],  # Should use process template
                feedback_integrated=False,
                optimization_applied=False,
                metadata={"ontological_category": "proces"},
            )
        )

        # Mock AI generation result
        mock_ai_result = MagicMock()
        mock_ai_result.text = "Een proces waarbij identiteit wordt geverifieerd."
        mock_ai_result.model = "gpt-4"
        mock_ai_result.tokens_used = 25
        mock_services["ai_service"].generate_definition.return_value = mock_ai_result

        # Mock cleaning service (V2 interface)
        from services.interfaces import CleaningResult

        mock_cleaning_result = CleaningResult(
            original_text="Een proces waarbij identiteit wordt geverifieerd.",
            cleaned_text="Een proces waarbij identiteit wordt geverifieerd.",
            was_cleaned=False,
            applied_rules=[],
            improvements=[],
        )
        mock_services["cleaning_service"].clean_text.return_value = mock_cleaning_result

        # Mock validation as successful
        mock_services["validation_service"].validate_definition.return_value = (
            ValidationResult(
                is_valid=True,
                definition_text="Een proces waarbij identiteit wordt geverifieerd.",
            )
        )

        # Mock repository save
        mock_services["repository"].save.return_value = 42

        # Execute orchestration
        response = await orchestrator.create_definition(sample_request)

        # Verify successful response
        assert response.success is True
        assert response.definition is not None
        assert response.validation_result.is_valid is True
        assert response.metadata["ontological_category"] == "proces"
        assert response.metadata["orchestrator_version"] == "v2.0"
        assert response.metadata["phases_completed"] == 11

        # Verify ontological category was passed to prompt service
        mock_services["prompt_service"].build_generation_prompt.assert_called_once()
        call_args = mock_services["prompt_service"].build_generation_prompt.call_args
        assert call_args[0][0].ontologische_categorie == "proces"

        # Verify validation service received ontological category via Definition object
        mock_services["validation_service"].validate_definition.assert_called_once()
        call_args = mock_services["validation_service"].validate_definition.call_args
        assert "definition" in call_args.kwargs
        assert call_args.kwargs["definition"].ontologische_categorie == "proces"

        # Verify definition object has correct ontological category
        assert response.definition.ontologische_categorie == "proces"

    @pytest.mark.asyncio()
    async def test_feedback_integration(
        self, orchestrator, mock_services, sample_request
    ):
        """Test GVI Rode Kabel feedback integration."""
        # Setup mock feedback
        mock_feedback = [
            {
                "attempt_number": 1,
                "violations": ["CON-01", "STR-01"],
                "suggestions": ["Avoid circular reasoning", "Fix structure"],
                "focus_areas": ["Avoid circular reasoning", "Fix definition structure"],
            }
        ]
        mock_services["feedback_engine"].get_feedback_for_request.return_value = (
            mock_feedback
        )

        # Setup other mocks for basic flow
        mock_services["security_service"].sanitize_request.return_value = sample_request
        mock_services["prompt_service"].build_generation_prompt.return_value = (
            PromptResult(
                text="Feedback-enhanced prompt",
                token_count=75,
                components_used=["ontologie_proces", "feedback_integration"],
                feedback_integrated=True,
                optimization_applied=False,
                metadata={"feedback_entries": 1},
            )
        )

        # Mock validation failure to trigger feedback processing
        mock_services["validation_service"].validate_definition.return_value = (
            ValidationResult(
                is_valid=False,
                definition_text="Bad definition",
                violations=[
                    ValidationViolation(
                        "CON-01", ValidationSeverity.HIGH, "Circular reasoning"
                    )
                ],
            )
        )

        # Mock other required services
        mock_ai_result = MagicMock()
        mock_ai_result.text = "Generated definition"
        mock_services["ai_service"].generate_definition.return_value = mock_ai_result

        mock_cleaning_result = MagicMock()
        mock_cleaning_result.cleaned_text = "Cleaned definition"
        mock_services["cleaning_service"].clean_text.return_value = mock_cleaning_result

        # Execute orchestration
        response = await orchestrator.create_definition(sample_request)

        # Verify feedback was integrated
        mock_services[
            "feedback_engine"
        ].get_feedback_for_request.assert_called_once_with("verificatie", "proces")

        # Verify prompt service received feedback
        call_args = mock_services["prompt_service"].build_generation_prompt.call_args
        assert call_args[1]["feedback_history"] == mock_feedback

        # Verify feedback processing was called for failed validation
        mock_services[
            "feedback_engine"
        ].process_validation_feedback.assert_called_once()

        # Verify response metadata indicates feedback integration
        assert response.metadata["feedback_integrated"] is True

    @pytest.mark.asyncio()
    async def test_security_service_integration(
        self, orchestrator, mock_services, sample_request
    ):
        """Test DPIA/AVG compliance through security service."""
        # Mock security service sanitization
        sanitized_request = GenerationRequest(
            id=sample_request.id,
            begrip=sample_request.begrip,
            context="[PII-REDACTED] detentiesysteem",  # Sanitized context.domein,
            ontologische_categorie=sample_request.ontologische_categorie,
            actor=sample_request.actor,
            legal_basis=sample_request.legal_basis,
        )
        mock_services["security_service"].sanitize_request.return_value = (
            sanitized_request
        )

        # Setup other mocks for minimal flow
        mock_services["feedback_engine"].get_feedback_for_request.return_value = []
        mock_services["prompt_service"].build_generation_prompt.return_value = (
            PromptResult(
                text="Sanitized prompt",
                token_count=40,
                components_used=[],
                feedback_integrated=False,
                optimization_applied=False,
                metadata={},
            )
        )

        mock_ai_result = MagicMock()
        mock_ai_result.text = "Generated definition"
        mock_services["ai_service"].generate_definition.return_value = mock_ai_result

        mock_cleaning_result = MagicMock()
        mock_cleaning_result.cleaned_text = "Cleaned definition"
        mock_services["cleaning_service"].clean_text.return_value = mock_cleaning_result

        mock_services["validation_service"].validate_definition.return_value = (
            ValidationResult(is_valid=True, definition_text="Valid definition")
        )

        # Execute orchestration
        response = await orchestrator.create_definition(sample_request)

        # Verify security service was called
        mock_services["security_service"].sanitize_request.assert_called_once_with(
            sample_request
        )

        # Verify sanitized request was used in subsequent calls
        prompt_call_args = mock_services[
            "prompt_service"
        ].build_generation_prompt.call_args
        used_request = prompt_call_args[0][0]
        assert used_request.context == "[PII-REDACTED] detentiesysteem"

    @pytest.mark.asyncio()
    async def test_validation_failure_and_enhancement(
        self, orchestrator, mock_services, sample_request
    ):
        """Test enhancement flow when validation fails."""
        # Setup mocks for enhancement flow
        mock_services["security_service"].sanitize_request.return_value = sample_request
        mock_services["feedback_engine"].get_feedback_for_request.return_value = []
        mock_services["prompt_service"].build_generation_prompt.return_value = (
            PromptResult(
                text="Test prompt",
                token_count=40,
                components_used=[],
                feedback_integrated=False,
                optimization_applied=False,
                metadata={},
            )
        )

        mock_ai_result = MagicMock()
        mock_ai_result.text = "Poor quality definition"
        mock_services["ai_service"].generate_definition.return_value = mock_ai_result

        from services.interfaces import CleaningResult

        mock_cleaning_result = CleaningResult(
            original_text="Poor quality definition",
            cleaned_text="Poor quality definition",
            was_cleaned=False,
            applied_rules=[],
            improvements=[],
        )
        mock_services["cleaning_service"].clean_text.return_value = mock_cleaning_result

        # First validation fails
        initial_validation = ValidationResult(
            is_valid=False,
            definition_text="Poor quality definition",
            violations=[
                ValidationViolation("STR-01", ValidationSeverity.HIGH, "Bad structure")
            ],
        )

        # Enhanced validation succeeds
        enhanced_validation = ValidationResult(
            is_valid=True, definition_text="Enhanced quality definition"
        )

        # Mock validation service to return different results on consecutive calls
        mock_services["validation_service"].validate_definition.side_effect = [
            initial_validation,
            enhanced_validation,
        ]

        # Mock enhancement service
        mock_services["enhancement_service"].enhance_definition.return_value = (
            "Enhanced quality definition"
        )

        # Execute orchestration
        response = await orchestrator.create_definition(sample_request)

        # Verify enhancement was called
        mock_services["enhancement_service"].enhance_definition.assert_called_once_with(
            "Poor quality definition",
            initial_validation.violations,
            context=sample_request,
        )

        # Verify validation was called twice (before and after enhancement)
        assert mock_services["validation_service"].validate_definition.call_count == 2

        # Verify final response uses enhanced definition
        assert response.definition.definitie == "Enhanced quality definition"
        assert response.validation_result.is_valid is True
        assert response.metadata.get("enhanced") is True

    @pytest.mark.asyncio()
    async def test_error_handling(self, orchestrator, mock_services, sample_request):
        """Test comprehensive error handling."""
        # Mock security service to raise exception
        mock_services["security_service"].sanitize_request.side_effect = Exception(
            "Security failure"
        )

        # Execute orchestration
        response = await orchestrator.create_definition(sample_request)

        # Verify error response
        assert response.success is False
        assert "Generation failed: Security failure" in response.error
        assert response.metadata["error_type"] == "Exception"
        assert response.metadata["orchestrator_version"] == "v2.0"

        # Verify monitoring was called for error tracking
        if mock_services["monitoring"]:
            mock_services["monitoring"].track_error.assert_called_once()

    @pytest.mark.asyncio()
    async def test_monitoring_integration(
        self, orchestrator, mock_services, sample_request
    ):
        """Test comprehensive monitoring integration."""
        # Setup successful flow
        mock_services["security_service"].sanitize_request.return_value = sample_request
        mock_services["feedback_engine"].get_feedback_for_request.return_value = []
        mock_services["prompt_service"].build_generation_prompt.return_value = (
            PromptResult(
                text="Test prompt",
                token_count=50,
                components_used=["test"],
                feedback_integrated=False,
                optimization_applied=False,
                metadata={},
            )
        )

        mock_ai_result = MagicMock()
        mock_ai_result.text = "Generated definition"
        mock_ai_result.tokens_used = 30
        mock_services["ai_service"].generate_definition.return_value = mock_ai_result

        mock_cleaning_result = MagicMock()
        mock_cleaning_result.cleaned_text = "Cleaned definition"
        mock_services["cleaning_service"].clean_text.return_value = mock_cleaning_result

        mock_services["validation_service"].validate_definition.return_value = (
            ValidationResult(is_valid=True, definition_text="Valid definition")
        )

        # Execute orchestration
        response = await orchestrator.create_definition(sample_request)

        # Verify monitoring calls
        mock_services["monitoring"].start_generation.assert_called_once_with("test-123")
        mock_services["monitoring"].complete_generation.assert_called_once()

        # Verify monitoring received correct data
        complete_call = mock_services["monitoring"].complete_generation.call_args
        assert complete_call[1]["success"] is True
        assert complete_call[1]["token_count"] == 30
        assert "test" in complete_call[1]["components_used"]


# Integration test with real service container
class TestDefinitionOrchestratorV2Integration:
    """Integration tests for DefinitionOrchestratorV2 with real services."""

    @pytest.mark.integration()
    @pytest.mark.asyncio()
    async def test_integration_with_existing_services(self):
        """Test integration with existing service infrastructure."""
        # This test would use real service container
        # Placeholder for future integration testing

    @pytest.mark.performance()
    @pytest.mark.asyncio()
    async def test_performance_benchmarks(self):
        """Test that orchestrator meets performance targets (<5s response time)."""
        # This test would measure actual performance
        # Target: <5s response time (60% improvement over legacy)

    @pytest.mark.ontological_category()
    @pytest.mark.asyncio()
    async def test_ontological_category_end_to_end(self):
        """Test complete ontological category flow with real template selection."""
        # This test would verify the ontological category bug is fixed
        # Should use real prompt service with template selection
