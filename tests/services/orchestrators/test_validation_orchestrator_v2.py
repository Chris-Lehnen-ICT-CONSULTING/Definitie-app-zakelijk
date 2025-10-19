"""
Unit tests voor ValidationOrchestratorV2 - Story 2.2
"""

import uuid
from unittest.mock import AsyncMock, Mock

import pytest

from services.interfaces import Definition
from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2
from services.validation.interfaces import (
    CONTRACT_VERSION,
    ValidationContext,
    ValidationRequest,
    ValidationResult,
)


class TestValidationOrchestratorV2:
    """Test suite for ValidationOrchestratorV2."""

    @pytest.fixture()
    def mock_validation_service(self):
        """Create a mock validation service."""
        service = Mock()
        service.validate_definition = AsyncMock(
            return_value={
                "version": CONTRACT_VERSION,
                "overall_score": 0.95,
                "is_acceptable": True,
                "violations": [],
                "passed_rules": ["RULE-001", "RULE-002"],
                "detailed_scores": {
                    "taal": 1.0,
                    "juridisch": 0.9,
                    "structuur": 0.95,
                    "samenhang": 0.9,
                },
                "system": {
                    "correlation_id": str(uuid.uuid4()),
                    "engine_version": "2.0.0",
                    "timestamp": "2024-01-01T00:00:00Z",
                },
            }
        )
        return service

    @pytest.fixture()
    def mock_cleaning_service(self):
        """Create a mock cleaning service."""
        service = Mock()
        service.clean_text = AsyncMock(return_value=Mock(cleaned_text="cleaned text"))
        service.clean_definition = AsyncMock(
            return_value=Mock(cleaned_text="cleaned definition text")
        )
        return service

    @pytest.fixture()
    def orchestrator(self, mock_validation_service):
        """Create orchestrator with mock validation service."""
        return ValidationOrchestratorV2(validation_service=mock_validation_service)

    @pytest.fixture()
    def orchestrator_with_cleaning(
        self, mock_validation_service, mock_cleaning_service
    ):
        """Create orchestrator with both services."""
        return ValidationOrchestratorV2(
            validation_service=mock_validation_service,
            cleaning_service=mock_cleaning_service,
        )

    def test_init_requires_validation_service(self):
        """Test that validation service is required."""
        with pytest.raises(ValueError, match="validation_service is vereist"):
            ValidationOrchestratorV2(validation_service=None)

    @pytest.mark.asyncio()
    async def test_validate_text_basic(self, orchestrator, mock_validation_service):
        """Test basic text validation."""
        result = await orchestrator.validate_text(
            begrip="test_begrip",
            text="test text",
            ontologische_categorie="PROCES",
            context=ValidationContext(profile="standard"),
        )

        assert isinstance(result, dict)
        assert result["version"] == CONTRACT_VERSION
        assert result["overall_score"] == 0.95
        assert result["is_acceptable"] is True

        # Verify service was called with correct args
        mock_validation_service.validate_definition.assert_called_once_with(
            begrip="test_begrip",
            text="test text",
            ontologische_categorie="PROCES",
            context={"profile": "standard"},
        )

    @pytest.mark.asyncio()
    async def test_validate_text_without_context(
        self, orchestrator, mock_validation_service
    ):
        """Test text validation without context."""
        result = await orchestrator.validate_text(
            begrip="test_begrip", text="test text"
        )

        assert result["is_acceptable"] is True

        # Verify service was called with None context
        mock_validation_service.validate_definition.assert_called_once_with(
            begrip="test_begrip",
            text="test text",
            ontologische_categorie=None,
            context=None,
        )

    @pytest.mark.asyncio()
    async def test_validate_text_with_cleaning(
        self, orchestrator_with_cleaning, mock_validation_service, mock_cleaning_service
    ):
        """Test text validation with cleaning service."""
        await orchestrator_with_cleaning.validate_text(
            begrip="test_begrip", text="dirty text"
        )

        # Verify cleaning was called
        mock_cleaning_service.clean_text.assert_called_once_with(
            "dirty text", "test_begrip"
        )

        # Verify validation used cleaned text
        mock_validation_service.validate_definition.assert_called_once_with(
            begrip="test_begrip",
            text="cleaned text",
            ontologische_categorie=None,
            context=None,
        )

    @pytest.mark.asyncio()
    async def test_validate_definition(self, orchestrator, mock_validation_service):
        """Test definition validation."""
        definition = Definition(
            begrip="test_begrip",
            definitie="test definitie",
            ontologische_categorie="OBJECT",
        )

        context = ValidationContext(profile="advanced")

        result = await orchestrator.validate_definition(
            definition=definition, context=context
        )

        assert result["is_acceptable"] is True

        # Verify service was called correctly
        mock_validation_service.validate_definition.assert_called_once_with(
            begrip="test_begrip",
            text="test definitie",
            ontologische_categorie="OBJECT",
            context={"profile": "advanced"},
        )

    @pytest.mark.asyncio()
    async def test_validate_definition_with_cleaning(
        self, orchestrator_with_cleaning, mock_validation_service, mock_cleaning_service
    ):
        """Test definition validation with cleaning."""
        definition = Definition(begrip="test_begrip", definitie="dirty definitie")

        await orchestrator_with_cleaning.validate_definition(definition=definition)

        # Verify cleaning was called
        mock_cleaning_service.clean_definition.assert_called_once_with(definition)

        # Verify validation used cleaned text
        mock_validation_service.validate_definition.assert_called_once_with(
            begrip="test_begrip",
            text="cleaned definition text",
            ontologische_categorie=None,
            context=None,
        )

    @pytest.mark.asyncio()
    async def test_batch_validate_sequential(self, orchestrator):
        """Test batch validation processes sequentially."""
        requests = [
            ValidationRequest(
                begrip=f"begrip_{i}",
                text=f"text {i}",
                ontologische_categorie=None,
                context=None,
            )
            for i in range(3)
        ]

        results = await orchestrator.batch_validate(requests)

        assert len(results) == 3
        assert all(r["is_acceptable"] for r in results)

        # Verify each was processed
        assert orchestrator.validation_service.validate_definition.call_count == 3

    @pytest.mark.asyncio()
    async def test_batch_validate_preserves_order(
        self, orchestrator, mock_validation_service
    ):
        """Test batch validation preserves input order."""
        # Make service return different scores for each
        scores = [0.9, 0.8, 0.7]
        mock_validation_service.validate_definition.side_effect = [
            {
                "version": CONTRACT_VERSION,
                "overall_score": score,
                "is_acceptable": True,
                "violations": [],
                "passed_rules": [],
                "detailed_scores": {},
                "system": {"correlation_id": str(uuid.uuid4())},
            }
            for score in scores
        ]

        requests = [
            ValidationRequest(begrip=f"begrip_{i}", text=f"text {i}") for i in range(3)
        ]

        results = await orchestrator.batch_validate(requests)

        # Verify order is preserved
        assert results[0]["overall_score"] == 0.9
        assert results[1]["overall_score"] == 0.8
        assert results[2]["overall_score"] == 0.7

    @pytest.mark.asyncio()
    async def test_batch_validate_ignores_max_concurrency(self, orchestrator):
        """Test that max_concurrency is ignored in v2.2."""
        requests = [ValidationRequest(begrip="test", text="text") for _ in range(2)]

        # Should work the same regardless of max_concurrency
        results1 = await orchestrator.batch_validate(requests, max_concurrency=1)
        results2 = await orchestrator.batch_validate(requests, max_concurrency=10)

        assert len(results1) == len(results2) == 2
        # Both should have made sequential calls
        assert orchestrator.validation_service.validate_definition.call_count == 4

    @pytest.mark.asyncio()
    async def test_validate_text_handles_service_exception(
        self, mock_validation_service
    ):
        """Test that service exceptions result in degraded mode."""
        # Make service raise exception
        mock_validation_service.validate_definition.side_effect = Exception(
            "Service unavailable"
        )

        orchestrator = ValidationOrchestratorV2(
            validation_service=mock_validation_service
        )

        result = await orchestrator.validate_text(
            begrip="test_begrip", text="test text"
        )

        # Should return degraded result, not raise
        assert isinstance(result, dict)
        assert result["version"] == CONTRACT_VERSION
        assert result["overall_score"] == 0.0
        assert result["is_acceptable"] is False
        assert len(result["violations"]) == 1

        violation = result["violations"][0]
        assert violation["code"] == "SYS-SVC-001"
        assert violation["severity"] == "error"
        assert "Service unavailable" in violation["message"]

        assert "system" in result
        assert "correlation_id" in result["system"]
        assert result["system"]["error"] == "Service unavailable"

    @pytest.mark.asyncio()
    async def test_validate_definition_handles_cleaning_exception(
        self, mock_validation_service, mock_cleaning_service
    ):
        """Test that cleaning service exceptions are handled gracefully."""
        # Make cleaning service raise exception
        mock_cleaning_service.clean_definition.side_effect = Exception(
            "Cleaning failed"
        )

        orchestrator = ValidationOrchestratorV2(
            validation_service=mock_validation_service,
            cleaning_service=mock_cleaning_service,
        )

        definition = Definition(begrip="test_begrip", definitie="test definitie")

        result = await orchestrator.validate_definition(definition)

        # Should return degraded result
        assert result["is_acceptable"] is False
        assert result["overall_score"] == 0.0
        assert any("Cleaning failed" in v["message"] for v in result["violations"])

    @pytest.mark.asyncio()
    async def test_context_propagation_with_all_fields(
        self, orchestrator, mock_validation_service
    ):
        """Test that all context fields are properly propagated."""
        context = ValidationContext(
            correlation_id=uuid.uuid4(),
            profile="advanced",
            locale="nl-NL",
            feature_flags={"test_flag": True},
        )

        await orchestrator.validate_text(begrip="test", text="text", context=context)

        # Verify all fields were passed
        call_args = mock_validation_service.validate_definition.call_args
        context_dict = call_args.kwargs["context"]

        assert context_dict["profile"] == "advanced"
        assert context_dict["correlation_id"] == str(context.correlation_id)
        assert context_dict["locale"] == "nl-NL"
        assert context_dict["feature_flags"] == {"test_flag": True}
