"""Test validate_definition path with Definition object."""

import pytest


@pytest.mark.integration
@pytest.mark.asyncio
async def test_orchestrator_validate_definition_with_definition_object():
    """Test that validate_definition path works with Definition object."""
    from services.container import ServiceContainer, ContainerConfigs
    from services.interfaces import Definition, GenerationRequest
    from services.validation.interfaces import CONTRACT_VERSION

    container = ServiceContainer(ContainerConfigs.testing())
    orch = container.orchestrator()

    # Create Definition object
    definition = Definition(
        begrip="testbegrip",
        definitie="Een definitie voor het testen van de Definition object path.",
        ontologische_categorie="concept"
    )

    # Get validation service directly since orchestrator doesn't have validate_definition
    # The validation is done through the ValidationOrchestratorV2
    validation_service = orch.validation_service

    # Validate using the validation service - it takes a Definition object
    result = await validation_service.validate_definition(definition)

    # Verify result shape
    assert isinstance(result, dict)
    assert result["version"] == CONTRACT_VERSION
    assert "overall_score" in result
    assert "is_acceptable" in result
    assert "violations" in result
    assert "system" in result
    assert "correlation_id" in result["system"]
