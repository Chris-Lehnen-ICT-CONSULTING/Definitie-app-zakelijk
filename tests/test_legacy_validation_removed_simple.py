"""
Simple test suite to verify legacy validation has been removed.
"""

import os
import sys

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_definition_validator_file_removed():
    """Verify definition_validator.py file has been removed."""
    file_path = os.path.join(
        os.path.dirname(__file__), "..", "src", "services", "definition_validator.py"
    )
    assert not os.path.exists(file_path), "definition_validator.py should be removed"


def test_cannot_import_definition_validator():
    """Verify DefinitionValidator cannot be imported."""
    with pytest.raises(ImportError):
        from services.definition_validator import DefinitionValidator


def test_container_has_no_validator_method():
    """Verify ServiceContainer no longer has validator() method."""
    from services.container import ServiceContainer

    container = ServiceContainer()

    # Should not have validator method
    assert not hasattr(
        container, "validator"
    ), "Container should not have validator() method"

    # Trying to call it should raise AttributeError
    with pytest.raises(AttributeError):
        container.validator()


def test_container_has_no_validator_config():
    """Verify ServiceContainer doesn't create validator_config."""
    from services.container import ServiceContainer

    container = ServiceContainer()

    # Should not have validator_config attribute
    assert not hasattr(
        container, "validator_config"
    ), "Container should not have validator_config"


def test_service_factory_get_stats_no_validator():
    """Verify ServiceFactory.get_stats() works without validator."""
    from services.container import ServiceContainer
    from services.service_factory import ServiceAdapter

    container = ServiceContainer.get_instance()
    adapter = ServiceAdapter(container)

    # Get stats should work without validator
    stats = adapter.get_stats()

    # Should have other stats but not validator
    assert "generator" in stats
    assert "repository" in stats
    assert "orchestrator" in stats
    assert "validator" not in stats, "Stats should not include validator"


def test_no_validator_in_container_source():
    """Verify container.py doesn't reference DefinitionValidator."""
    container_file = os.path.join(
        os.path.dirname(__file__), "..", "src", "services", "container.py"
    )

    with open(container_file) as f:
        content = f.read()

    # Should not import or reference DefinitionValidator
    assert "from services.definition_validator import" not in content
    assert "DefinitionValidator(" not in content

    # Should have comment about removal
    assert "Legacy" in content or "removed" in content


def test_no_validator_in_service_factory_source():
    """Verify service_factory.py doesn't use validator."""
    factory_file = os.path.join(
        os.path.dirname(__file__), "..", "src", "services", "service_factory.py"
    )

    with open(factory_file) as f:
        content = f.read()

    # Should not call container.validator()
    assert "container.validator()" not in content

    # Should have comment about removal
    assert "Legacy validator removed" in content


def test_validation_orchestrator_v2_exists():
    """Verify V2 validation orchestrator is available."""
    from services.orchestrators.validation_orchestrator_v2 import (
        ValidationOrchestratorV2,
    )

    # Should be importable
    assert ValidationOrchestratorV2 is not None

    # Should be a class
    assert isinstance(ValidationOrchestratorV2, type)


def test_orchestrator_handles_validation():
    """Verify DefinitionOrchestratorV2 has validation capabilities."""
    from services.container import ServiceContainer

    container = ServiceContainer.get_instance()
    orchestrator = container.orchestrator()

    # Should have validation orchestrator
    assert hasattr(orchestrator, "validation_orchestrator")
    assert orchestrator.validation_orchestrator is not None


def test_no_validator_interface_in_interfaces():
    """Verify DefinitionValidatorInterface is removed from interfaces."""
    interfaces_file = os.path.join(
        os.path.dirname(__file__), "..", "src", "services", "interfaces.py"
    )

    with open(interfaces_file) as f:
        content = f.read()

    # Should not define DefinitionValidatorInterface
    # (it might still be referenced in comments)
    assert "class DefinitionValidatorInterface" not in content


def test_test_files_updated():
    """Verify test files have been updated to not use validator."""
    test_container_file = os.path.join(
        os.path.dirname(__file__), "services", "test_service_container.py"
    )

    if os.path.exists(test_container_file):
        with open(test_container_file) as f:
            content = f.read()

        # Should have updated test
        assert (
            "test_validator_removed" in content or "Legacy validator removed" in content
        )


def test_validator_test_file_removed():
    """Verify test_definition_validator.py has been removed."""
    test_file = os.path.join(
        os.path.dirname(__file__), "services", "test_definition_validator.py"
    )

    assert not os.path.exists(
        test_file
    ), "test_definition_validator.py should be removed"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
