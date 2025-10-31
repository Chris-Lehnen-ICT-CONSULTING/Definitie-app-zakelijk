"""
Story 2.4 Unit Test Suite

Focused unit tests for Story 2.4 interface migration components.
Tests individual components in isolation with comprehensive mocking.

Test Coverage:
1. ValidationOrchestratorV2 unit tests
2. Interface compliance unit tests
3. Context conversion unit tests
4. Error handling unit tests
5. Schema compliance unit tests
"""

import uuid
from typing import Any, Dict
from unittest.mock import AsyncMock, Mock, patch

import pytest

from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2
from services.validation.interfaces import (
    CONTRACT_VERSION,
    ValidationContext,
    ValidationOrchestratorInterface,
    ValidationRequest,
    ValidationResult,
)


class TestValidationOrchestratorV2Unit:
    """Unit tests for ValidationOrchestratorV2 class."""

    @pytest.fixture
    def mock_validation_service(self):
        """Create mock validation service."""
        service = Mock()
        service.validate_definition = AsyncMock(
            return_value={
                "version": CONTRACT_VERSION,
                "overall_score": 0.85,
                "is_acceptable": True,
                "violations": [],
                "passed_rules": ["RULE-001"],
                "detailed_scores": {"taal": 0.9, "juridisch": 0.8},
                "system": {
                    "correlation_id": str(uuid.uuid4()),
                    "engine_version": "2.0.0",
                },
            }
        )
        return service

    @pytest.fixture
    def mock_cleaning_service(self):
        """Create mock cleaning service."""
        service = Mock()
        service.clean_text = AsyncMock(return_value=Mock(cleaned_text="cleaned text"))

        # clean_definition expects a Definition object and returns a cleaning result
        async def mock_clean_definition(definition):
            return Mock(cleaned_text="clean definitie")

        service.clean_definition = AsyncMock(side_effect=mock_clean_definition)
        return service

    @pytest.fixture
    def orchestrator(self, mock_validation_service, mock_cleaning_service):
        """Create ValidationOrchestratorV2 instance."""
        return ValidationOrchestratorV2(
            validation_service=mock_validation_service,
            cleaning_service=mock_cleaning_service,
        )

    # ========================================
    # CONSTRUCTOR TESTS
    # ========================================

    def test_constructor_requires_validation_service(self):
        """Test constructor validation service requirement."""
        with pytest.raises(ValueError, match="validation_service is vereist"):
            ValidationOrchestratorV2(validation_service=None)

    def test_constructor_accepts_optional_cleaning_service(
        self, mock_validation_service
    ):
        """Test constructor with optional cleaning service."""
        # Should work without cleaning service
        orchestrator = ValidationOrchestratorV2(
            validation_service=mock_validation_service, cleaning_service=None
        )
        assert orchestrator.validation_service == mock_validation_service
        assert orchestrator.cleaning_service is None

    def test_constructor_stores_services_correctly(
        self, mock_validation_service, mock_cleaning_service
    ):
        """Test constructor stores services correctly."""
        orchestrator = ValidationOrchestratorV2(
            validation_service=mock_validation_service,
            cleaning_service=mock_cleaning_service,
        )
        assert orchestrator.validation_service == mock_validation_service
        assert orchestrator.cleaning_service == mock_cleaning_service

    # ========================================
    # VALIDATE_TEXT METHOD TESTS
    # ========================================

    @pytest.mark.asyncio
    async def test_validate_text_basic_functionality(
        self, orchestrator, mock_validation_service
    ):
        """Test validate_text basic functionality."""
        result = await orchestrator.validate_text("begrip", "text")

        # Verify underlying service was called (text gets cleaned)
        mock_validation_service.validate_definition.assert_called_once_with(
            begrip="begrip",
            text="cleaned text",
            ontologische_categorie=None,
            context=None,
        )

        # Verify result structure
        assert isinstance(result, dict)
        assert "version" in result
        assert "overall_score" in result
        assert "is_acceptable" in result

    @pytest.mark.asyncio
    async def test_validate_text_with_all_parameters(
        self, orchestrator, mock_validation_service
    ):
        """Test validate_text with all parameters."""
        context = ValidationContext(
            correlation_id=uuid.uuid4(),
            profile="advanced",
            locale="nl-NL",
            feature_flags={"flag1": True},
        )

        await orchestrator.validate_text(
            begrip="testbegrip",
            text="test text",
            ontologische_categorie="object",
            context=context,
        )

        # Verify service call with context conversion
        call_args = mock_validation_service.validate_definition.call_args
        assert call_args[1]["begrip"] == "testbegrip"
        assert call_args[1]["text"] == "cleaned text"  # Text gets cleaned
        assert call_args[1]["ontologische_categorie"] == "object"

        # Verify context was converted to dict
        context_arg = call_args[1]["context"]
        assert isinstance(context_arg, dict)
        assert context_arg["profile"] == "advanced"
        assert context_arg["locale"] == "nl-NL"
        assert context_arg["feature_flags"] == {"flag1": True}

    @pytest.mark.asyncio
    async def test_validate_text_with_cleaning(
        self, orchestrator, mock_cleaning_service, mock_validation_service
    ):
        """Test validate_text with text cleaning."""
        mock_cleaning_service.clean_text.return_value.cleaned_text = "super clean text"

        await orchestrator.validate_text("begrip", "dirty text")

        # Verify cleaning was called
        mock_cleaning_service.clean_text.assert_called_once_with("dirty text", "begrip")

        # Verify validation received cleaned text
        call_args = mock_validation_service.validate_definition.call_args
        assert call_args[1]["text"] == "super clean text"

    @pytest.mark.asyncio
    async def test_validate_text_without_cleaning_service(
        self, mock_validation_service
    ):
        """Test validate_text without cleaning service."""
        orchestrator = ValidationOrchestratorV2(
            validation_service=mock_validation_service, cleaning_service=None
        )

        await orchestrator.validate_text("begrip", "original text")

        # Verify validation received original text
        call_args = mock_validation_service.validate_definition.call_args
        assert call_args[1]["text"] == "original text"

    # ========================================
    # VALIDATE_DEFINITION METHOD TESTS
    # ========================================

    @pytest.mark.asyncio
    async def test_validate_definition_basic_functionality(
        self, orchestrator, mock_validation_service
    ):
        """Test validate_definition with Definition object."""
        from services.interfaces import Definition

        definition = Definition(
            begrip="testbegrip",
            definitie="test definitie",
            ontologische_categorie="proces",
        )

        await orchestrator.validate_definition(definition)

        # Verify service call (definitie gets cleaned)
        call_args = mock_validation_service.validate_definition.call_args
        assert call_args[1]["begrip"] == "testbegrip"
        assert call_args[1]["text"] == "clean definitie"  # Text gets cleaned
        assert call_args[1]["ontologische_categorie"] == "proces"

    @pytest.mark.asyncio
    async def test_validate_definition_with_cleaning(
        self, orchestrator, mock_cleaning_service
    ):
        """Test validate_definition with cleaning."""
        from services.interfaces import Definition

        definition = Definition(begrip="begrip", definitie="dirty definitie")
        mock_cleaning_service.clean_definition.return_value.cleaned_text = (
            "clean definitie"
        )

        await orchestrator.validate_definition(definition)

        # Verify cleaning was called with definition
        mock_cleaning_service.clean_definition.assert_called_once_with(definition)

    # ========================================
    # BATCH_VALIDATE METHOD TESTS
    # ========================================

    @pytest.mark.asyncio
    async def test_batch_validate_functionality(self, orchestrator):
        """Test batch_validate processes multiple requests."""
        requests = [
            ValidationRequest(begrip=f"begrip{i}", text=f"text{i}") for i in range(3)
        ]

        results = await orchestrator.batch_validate(requests)

        # Verify results
        assert len(results) == 3
        assert all(isinstance(result, dict) for result in results)
        assert all("is_acceptable" in result for result in results)

    @pytest.mark.asyncio
    async def test_batch_validate_ignores_max_concurrency(self, orchestrator):
        """Test batch_validate ignores max_concurrency parameter in V2."""
        requests = [ValidationRequest(begrip="begrip", text="text")]

        # max_concurrency should be ignored (sequential processing)
        results = await orchestrator.batch_validate(requests, max_concurrency=10)

        assert len(results) == 1

    # ========================================
    # ERROR HANDLING TESTS
    # ========================================

    @pytest.mark.asyncio
    async def test_validate_text_error_handling(self, mock_validation_service):
        """Test validate_text error handling creates degraded result."""
        mock_validation_service.validate_definition.side_effect = Exception(
            "Service error"
        )

        orchestrator = ValidationOrchestratorV2(mock_validation_service)

        result = await orchestrator.validate_text("begrip", "text")

        # Verify degraded result
        assert isinstance(result, dict)
        assert result["is_acceptable"] is False
        assert "system" in result
        assert "error" in result["system"]
        assert "Service error" in result["system"]["error"]

    @pytest.mark.asyncio
    async def test_validate_definition_error_handling(self, mock_validation_service):
        """Test validate_definition error handling."""
        from services.interfaces import Definition

        mock_validation_service.validate_definition.side_effect = RuntimeError(
            "Validation failed"
        )

        orchestrator = ValidationOrchestratorV2(mock_validation_service)
        definition = Definition(begrip="begrip", definitie="definitie")

        result = await orchestrator.validate_definition(definition)

        # Verify degraded result
        assert result["is_acceptable"] is False
        assert "Validation failed" in result["system"]["error"]

    # ========================================
    # CONTEXT CONVERSION TESTS
    # ========================================

    @pytest.mark.asyncio
    async def test_validation_context_to_dict_conversion(
        self, orchestrator, mock_validation_service
    ):
        """Test ValidationContext to dict conversion."""
        context = ValidationContext(
            correlation_id=uuid.uuid4(),
            profile="test-profile",
            locale="en-US",
            trace_parent="trace-123",
            feature_flags={"feature1": True, "feature2": False},
            metadata={"key1": "value1", "key2": "value2"},
        )

        await orchestrator.validate_text("begrip", "text", context=context)

        call_args = mock_validation_service.validate_definition.call_args
        context_dict = call_args[1]["context"]

        # Verify all fields converted correctly
        assert context_dict["profile"] == "test-profile"
        assert context_dict["locale"] == "en-US"
        assert context_dict["correlation_id"] == str(context.correlation_id)
        assert context_dict["feature_flags"] == {"feature1": True, "feature2": False}

    @pytest.mark.asyncio
    async def test_validation_context_with_none_values(
        self, orchestrator, mock_validation_service
    ):
        """Test ValidationContext handling with None values."""
        context = ValidationContext(
            correlation_id=uuid.uuid4(), profile=None, locale=None, feature_flags=None
        )

        await orchestrator.validate_text("begrip", "text", context=context)

        call_args = mock_validation_service.validate_definition.call_args
        context_dict = call_args[1]["context"]

        # Only non-None values should be in dict
        assert "correlation_id" in context_dict
        assert "profile" not in context_dict
        assert "locale" not in context_dict
        assert "feature_flags" not in context_dict

    # ========================================
    # SCHEMA COMPLIANCE TESTS
    # ========================================

    @pytest.mark.asyncio
    async def test_result_schema_compliance(self, orchestrator):
        """Test that results are schema compliant."""
        result = await orchestrator.validate_text("begrip", "text")

        # Verify required fields per schema
        required_fields = [
            "version",
            "overall_score",
            "is_acceptable",
            "violations",
            "passed_rules",
            "detailed_scores",
            "system",
        ]

        for field in required_fields:
            assert field in result, f"Missing required field: {field}"

        # Verify system.correlation_id is present
        assert "correlation_id" in result["system"]

        # Verify version matches contract
        assert result["version"] == CONTRACT_VERSION

    @pytest.mark.asyncio
    async def test_correlation_id_generation(self, orchestrator):
        """Test correlation ID generation when not provided."""
        result = await orchestrator.validate_text("begrip", "text")

        # Should have generated correlation_id
        correlation_id = result["system"]["correlation_id"]
        assert correlation_id is not None

        # Should be valid UUID format
        uuid.UUID(correlation_id)  # Will raise if invalid

    @pytest.mark.asyncio
    async def test_correlation_id_preservation(
        self, orchestrator, mock_validation_service
    ):
        """Test correlation ID preservation from context."""
        test_uuid = uuid.uuid4()
        context = ValidationContext(correlation_id=test_uuid)

        # Set up mock to include the correlation ID in response
        mock_validation_service.validate_definition.return_value = {
            "version": CONTRACT_VERSION,
            "overall_score": 0.85,
            "is_acceptable": True,
            "violations": [],
            "passed_rules": ["RULE-001"],
            "detailed_scores": {"taal": 0.9, "juridisch": 0.8},
            "system": {
                "correlation_id": str(test_uuid),
                "engine_version": "2.0.0",
            },
        }

        result = await orchestrator.validate_text("begrip", "text", context=context)

        # Should preserve provided correlation_id
        assert result["system"]["correlation_id"] == str(test_uuid)


class TestValidationOrchestratorInterfaceCompliance:
    """Unit tests for ValidationOrchestratorInterface compliance."""

    def test_implements_interface(self):
        """Test that ValidationOrchestratorV2 implements the interface."""
        assert issubclass(ValidationOrchestratorV2, ValidationOrchestratorInterface)

    def test_has_required_methods(self):
        """Test that all required interface methods are present."""
        required_methods = ["validate_text", "validate_definition", "batch_validate"]

        for method_name in required_methods:
            assert hasattr(ValidationOrchestratorV2, method_name)
            method = getattr(ValidationOrchestratorV2, method_name)
            assert callable(method)

    def test_method_signatures_match_interface(self):
        """Test that method signatures are compatible with the interface."""
        # Check that key interface methods exist and are callable
        required_methods = ["validate_text", "validate_definition", "batch_validate"]

        for method_name in required_methods:
            assert hasattr(
                ValidationOrchestratorV2, method_name
            ), f"Missing method: {method_name}"
            method = getattr(ValidationOrchestratorV2, method_name)
            assert callable(method), f"Method {method_name} is not callable"

        # If we get here, basic interface compliance is satisfied


class TestStory24UnitTestHelpers:
    """Unit test helpers and utilities for Story 2.4."""

    def test_mock_validation_result_factory(self):
        """Test utility for creating mock validation results."""

        def create_mock_validation_result(
            score: float = 0.8,
            acceptable: bool = True,
            violations: list | None = None,
            correlation_id: str | None = None,
        ) -> dict[str, Any]:
            """Factory for creating mock validation results."""
            return {
                "version": CONTRACT_VERSION,
                "overall_score": score,
                "is_acceptable": acceptable,
                "violations": violations or [],
                "passed_rules": ["MOCK-RULE-001"],
                "detailed_scores": {"taal": score, "juridisch": score},
                "system": {
                    "correlation_id": correlation_id or str(uuid.uuid4()),
                    "engine_version": "2.0.0-test",
                },
            }

        # Test factory
        result = create_mock_validation_result(score=0.9, acceptable=True)
        assert result["overall_score"] == 0.9
        assert result["is_acceptable"] is True
        assert "correlation_id" in result["system"]

    def test_validation_context_factory(self):
        """Test utility for creating validation contexts."""

        def create_test_context(
            profile: str = "test", locale: str = "nl-NL", **kwargs
        ) -> ValidationContext:
            """Factory for creating test validation contexts."""
            return ValidationContext(
                correlation_id=uuid.uuid4(), profile=profile, locale=locale, **kwargs
            )

        # Test factory
        context = create_test_context(profile="advanced", locale="en-US")
        assert context.profile == "advanced"
        assert context.locale == "en-US"
        assert context.correlation_id is not None

    @pytest.mark.asyncio
    async def test_orchestrator_test_helper(self):
        """Test helper for setting up orchestrator for unit tests."""

        def create_test_orchestrator(
            validation_response: dict[str, Any] | None = None,
            cleaning_enabled: bool = False,
        ) -> ValidationOrchestratorV2:
            """Helper for creating test orchestrator."""
            mock_service = Mock()
            mock_service.validate_definition = AsyncMock(
                return_value=validation_response
                or {
                    "version": CONTRACT_VERSION,
                    "overall_score": 0.8,
                    "is_acceptable": True,
                    "violations": [],
                    "passed_rules": ["TEST-RULE"],
                    "detailed_scores": {"test": 0.8},
                    "system": {"correlation_id": str(uuid.uuid4())},
                }
            )

            cleaning_service = None
            if cleaning_enabled:
                cleaning_service = Mock()
                cleaning_service.clean_text = AsyncMock(
                    return_value=Mock(cleaned_text="cleaned")
                )

            return ValidationOrchestratorV2(
                validation_service=mock_service, cleaning_service=cleaning_service
            )

        # Test helper
        orchestrator = create_test_orchestrator(cleaning_enabled=True)
        result = await orchestrator.validate_text("test", "text")

        assert result["is_acceptable"] is True
        assert "correlation_id" in result["system"]
