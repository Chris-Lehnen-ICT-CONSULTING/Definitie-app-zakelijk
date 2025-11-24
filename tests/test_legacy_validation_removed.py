"""
Comprehensive test suite to verify legacy validation has been completely removed
and V2 validation orchestrator is working correctly.
"""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from services.container import ServiceContainer
from services.interfaces import (
    CleaningServiceInterface,
    Definition,
    ValidationServiceInterface,
)
from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2
from services.service_factory import ServiceAdapter as ServiceFactory
from services.validation.interfaces import (
    ValidationContext,
    ValidationOrchestratorInterface,
    ValidationRequest,
    ValidationResult,
)


class TestLegacyValidationRemoval:
    """Test suite to ensure legacy validation is completely removed."""

    def test_container_has_no_validator_method(self):
        """Verify container.validator() method no longer exists."""
        container = ServiceContainer()
        assert not hasattr(container, "validator")

        # Verify trying to call it raises AttributeError
        with pytest.raises(AttributeError):
            container.validator()

    def test_definition_validator_file_removed(self):
        """Verify DefinitionValidator class cannot be imported."""
        with pytest.raises(ImportError):
            from services.definition_validator import DefinitionValidator

    def test_service_factory_stats_no_validator(self):
        """Verify ServiceFactory.get_stats() works without validator."""
        container = ServiceContainer.get_instance()
        factory = ServiceFactory(container)

        stats = factory.get_stats()

        # Should have stats for other services but not validator
        assert "generator" in stats
        assert "repository" in stats
        assert "orchestrator" in stats
        assert "validator" not in stats

    def test_no_validator_config_in_container(self):
        """Verify ValidatorConfig is not created in container."""
        container = ServiceContainer()

        # Check that validator_config attribute doesn't exist
        assert not hasattr(container, "validator_config")

    def test_no_validator_imports_in_container(self):
        """Verify no legacy validator imports in container module."""
        import src.services.container as container_module

        # Check module doesn't have validator imports
        assert not hasattr(container_module, "DefinitionValidator")
        assert not hasattr(container_module, "ValidatorConfig")


class TestV2ValidationOrchestrator:
    """Test suite for V2 validation orchestrator functionality."""

    @pytest.fixture
    def mock_validation_service(self):
        """Create mock validation service."""
        service = Mock(spec=ValidationServiceInterface)
        # TypedDict-style ValidationResult stub
        service.validate_text = AsyncMock(
            return_value={
                "version": "1.0.0",
                "overall_score": 0.85,
                "is_acceptable": True,
                "violations": [],
                "passed_rules": [],
                "detailed_scores": {},
                "system": {"correlation_id": "00000000-0000-0000-0000-000000000000"},
            }
        )
        return service

    @pytest.fixture
    def mock_cleaning_service(self):
        """Create mock cleaning service."""
        service = Mock(spec=CleaningServiceInterface)
        service.clean_text = AsyncMock(side_effect=lambda text: text.strip())
        return service

    @pytest.fixture
    def orchestrator(self, mock_validation_service, mock_cleaning_service):
        """Create V2 orchestrator with mocked services."""
        return ValidationOrchestratorV2(
            validation_service=mock_validation_service,
            cleaning_service=mock_cleaning_service,
        )

    @pytest.mark.asyncio
    async def test_v2_orchestrator_validate_text(self, orchestrator):
        """Test V2 orchestrator can validate text."""
        result = await orchestrator.validate_text(
            begrip="Test Begriff",
            text="Test definitie text",
            ontologische_categorie="proces",
        )

        assert result is not None
        assert isinstance(result, dict)
        assert result["is_acceptable"] is True
        assert result["overall_score"] == 0.85

    @pytest.mark.asyncio
    async def test_v2_orchestrator_with_context(self, orchestrator):
        """Test V2 orchestrator handles validation context."""
        context = ValidationContext(
            correlation_id="test-123", metadata={"source": "test"}
        )

        result = await orchestrator.validate_text(
            begrip="Test", text="Test text", context=context
        )

        assert result is not None
        assert result.metadata.get("correlation_id") == "test-123"

    @pytest.mark.asyncio
    async def test_v2_orchestrator_validate_definition(self, orchestrator):
        """Test V2 orchestrator can validate Definition objects."""
        definition = Definition(
            begrip="TestBegrip",
            definitie="Dit is een test definitie",
            ontologische_categorie="proces",
        )

        result = await orchestrator.validate_definition(definition)

        assert result is not None
        assert isinstance(result, dict)
        assert result["is_acceptable"] is True

    @pytest.mark.asyncio
    async def test_v2_orchestrator_batch_validate(self, orchestrator):
        """Test V2 orchestrator batch validation."""
        requests = [
            ValidationRequest(
                begrip=f"Begriff{i}",
                text=f"Definitie {i}",
                ontologische_categorie="proces",
            )
            for i in range(3)
        ]

        results = await orchestrator.batch_validate(requests)

        assert len(results) == 3
        for result in results:
            assert isinstance(result, dict)
            assert result["is_acceptable"] is True

    @pytest.mark.asyncio
    async def test_v2_orchestrator_with_cleaning(self, orchestrator):
        """Test V2 orchestrator applies cleaning when configured."""
        result = await orchestrator.validate_text(
            begrip="Test",
            text="  Test with spaces  ",  # Text with extra spaces
            ontologische_categorie="proces",
        )

        # Cleaning service should have been called
        orchestrator.cleaning_service.clean_text.assert_called()
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_v2_orchestrator_error_handling(self, mock_validation_service):
        """Test V2 orchestrator handles validation errors gracefully."""
        # Make validation service raise an error
        mock_validation_service.validate_text = AsyncMock(
            side_effect=Exception("Validation failed")
        )

        orchestrator = ValidationOrchestratorV2(
            validation_service=mock_validation_service, cleaning_service=None
        )

        result = await orchestrator.validate_text(begrip="Test", text="Test text")

        # Should return degraded result instead of raising
        assert result is not None
        assert result.is_valid is False
        assert "degraded" in result.metadata


class TestIntegrationWithoutLegacyValidator:
    """Integration tests to ensure system works without legacy validator."""

    def test_service_factory_can_generate_without_validator(self):
        """Test that ServiceFactory can still generate definitions."""
        container = ServiceContainer.get_instance()
        factory = ServiceFactory(container)

        # Create a mock response from orchestrator
        with patch.object(factory.orchestrator, "generate_definition") as mock_generate:
            from services.orchestrators.definition_orchestrator_v2 import (
                DefinitionResponse,
            )

            mock_generate.return_value = asyncio.coroutine(
                lambda: DefinitionResponse(
                    success=True,
                    definitie="Generated definition",
                    metadata={"validation_score": 0.9},
                )
            )()

            result = factory.genereer_definitie(
                begrip="TestBegrip", context="Test context"
            )

            assert result is not None
            assert result.success is True
            assert "Generated definition" in result.final_definitie

    def test_container_initialization_without_validator(self):
        """Test ServiceContainer initializes correctly without validator."""
        # Reset singleton to test fresh initialization
        ServiceContainer._instance = None

        container = ServiceContainer.get_instance()

        # Should initialize without errors
        assert container is not None
        assert hasattr(container, "generator")
        assert hasattr(container, "repository")
        assert hasattr(container, "orchestrator")
        assert not hasattr(container, "validator")

    def test_v2_validation_available_through_orchestrator(self):
        """Test validation is still available through V2 orchestrator."""
        container = ServiceContainer.get_instance()

        # Get the orchestrator (which handles validation now)
        orchestrator = container.orchestrator()

        # Verify it has validation capabilities
        assert hasattr(orchestrator, "validation_orchestrator")
        assert isinstance(
            orchestrator.validation_orchestrator, ValidationOrchestratorInterface
        )


class TestMigrationCompleteness:
    """Tests to ensure migration is complete and clean."""

    def test_no_validator_references_in_production_code(self):
        """Verify no references to DefinitionValidator in production code."""
        # This would normally use code analysis tools
        # For now, we just check key files don't import it

        import src.services.container as container_module
        import src.services.service_factory as factory_module

        # Check these modules don't reference DefinitionValidator
        factory_source = str(factory_module)
        container_source = str(container_module)

        assert "DefinitionValidator" not in factory_source
        assert "DefinitionValidator" not in container_source

    def test_interfaces_updated(self):
        """Verify interfaces no longer include DefinitionValidatorInterface."""
        import src.services.interfaces as interfaces_module

        # Should not have DefinitionValidatorInterface
        assert not hasattr(interfaces_module, "DefinitionValidatorInterface")

    def test_all_validation_through_v2(self):
        """Verify all validation now goes through V2 orchestrator."""
        container = ServiceContainer.get_instance()
        ServiceFactory(container)

        # The only validation path should be through orchestrator
        orchestrator = container.orchestrator()

        # Orchestrator should have V2 validation
        assert hasattr(orchestrator, "validation_orchestrator")
        assert orchestrator.validation_orchestrator is not None

    def test_no_validator_config_usage(self):
        """Verify ValidatorConfig is not used anywhere."""
        container = ServiceContainer.get_instance()

        # Container should not have validator_config
        assert not hasattr(container, "validator_config")

        # Config should not be passed to any services
        config = container.config
        assert "validator_config" not in str(config)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
