"""
Unit tests voor ServiceContainer.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Voeg src toe aan path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from services.container import (
    ContainerConfigs,
    ServiceContainer,
    get_container,
    reset_container,
)
from services.interfaces import (
    DefinitionGeneratorInterface,
    DefinitionOrchestratorInterface,
    DefinitionRepositoryInterface,
)


class TestServiceContainer:
    """Test suite voor ServiceContainer."""

    def setup_method(self):
        """Reset container voor elke test."""
        reset_container()

    def test_container_initialization(self):
        """Test basis container initialisatie."""
        # Act
        container = ServiceContainer()

        # Assert
        assert container is not None
        assert isinstance(container.config, dict)
        assert "generator" not in container._instances  # Lazy loading

    def test_container_with_config(self, chdir_tmp_path):
        """Test container met custom config."""
        # Arrange
        config = {"db_path": "test.db", "generator_model": "gpt-3.5-turbo"}

        # Act
        container = ServiceContainer(config)

        # Assert
        assert container.config["db_path"] == "test.db"
        assert container.config["generator_model"] == "gpt-3.5-turbo"

    def test_generator_singleton(self):
        """Test dat generator een singleton is."""
        # Arrange
        container = ServiceContainer()

        # Act
        gen1 = container.generator()
        gen2 = container.generator()

        # Assert
        assert gen1 is gen2
        # V2 orchestrator implements both interfaces
        assert isinstance(
            gen1, (DefinitionGeneratorInterface, DefinitionOrchestratorInterface)
        )

    def test_validator_removed(self):
        """Test dat legacy validator is verwijderd."""
        # Arrange
        container = ServiceContainer()

        # Act & Assert
        # Legacy validator() method should not exist
        assert not hasattr(container, "validator")

    def test_repository_singleton(self):
        """Test dat repository een singleton is."""
        # Arrange
        container = ServiceContainer({"db_path": ":memory:"})

        # Act
        repo1 = container.repository()
        repo2 = container.repository()

        # Assert
        assert repo1 is repo2
        assert isinstance(repo1, DefinitionRepositoryInterface)

    def test_orchestrator_singleton(self):
        """Test dat orchestrator een singleton is."""
        # Arrange
        container = ServiceContainer()

        # Act
        orch1 = container.orchestrator()
        orch2 = container.orchestrator()

        # Assert
        assert orch1 is orch2
        assert isinstance(orch1, DefinitionOrchestratorInterface)

    def test_reset_container(self):
        """Test container reset functionaliteit."""
        # Arrange
        container = ServiceContainer()
        gen1 = container.generator()

        # Act
        container.reset()
        gen2 = container.generator()

        # Assert
        assert gen1 is not gen2  # Nieuwe instances na reset

    def test_get_service_by_name(self):
        """Test ophalen service op naam."""
        # Arrange
        container = ServiceContainer()

        # Act
        generator = container.get_service("generator")
        validator = container.get_service("validator")
        invalid = container.get_service("invalid")

        # Assert
        # V2 orchestrator implements both interfaces
        assert isinstance(
            generator, (DefinitionGeneratorInterface, DefinitionOrchestratorInterface)
        )
        # Legacy validator removed - should return None
        assert validator is None
        assert invalid is None

    def test_update_config(self, chdir_tmp_path):
        """Test config update en reset."""
        # Arrange
        # Disable actual DB usage to avoid creating stray files in project root
        container = ServiceContainer({"db_path": "old.db", "use_database": False})
        # Patch heavy dependency to avoid reading real files when chdir'ed
        from unittest.mock import MagicMock

        with patch(
            "services.validation.config.ValidationConfig.from_yaml",
            return_value=MagicMock(),
        ):
            gen1 = container.generator()

        # Act
        container.update_config({"db_path": "new.db"})
        with patch(
            "services.validation.config.ValidationConfig.from_yaml",
            return_value=MagicMock(),
        ):
            gen2 = container.generator()

        # Assert
        assert container.config["db_path"] == "new.db"
        assert gen1 is not gen2  # Reset na config update

    def test_global_container(self):
        """Test globale container functionaliteit."""
        # Act
        container1 = get_container()
        container2 = get_container()

        # Assert
        assert container1 is container2  # Zelfde instance

        # Reset en check
        reset_container()
        container3 = get_container()
        assert container3 is not container1  # Nieuwe instance na reset

    def test_container_configs(self):
        """Test voorgedefinieerde configuraties."""
        # Test development config
        dev_config = ContainerConfigs.development()
        # Model wordt nu uit centrale config gehaald
        assert dev_config["db_path"] == "data/definities.db"
        assert dev_config["enable_monitoring"] is True
        assert dev_config["enable_ontology"] is True
        # Dead code verwijderd: enable_auto_save, min_quality_score

        # Test testing config
        test_config = ContainerConfigs.testing()
        assert test_config["db_path"] == ":memory:"
        assert test_config["enable_monitoring"] is False
        assert test_config["enable_ontology"] is False
        assert test_config["use_json_rules"] is False
        # Dead code verwijderd: enable_auto_save, enable_validation, enable_enrichment

        # Test production config
        prod_config = ContainerConfigs.production()
        # Model wordt nu uit centrale config gehaald
        assert prod_config["db_path"] == "data/definities.db"
        assert prod_config["enable_monitoring"] is True
        assert prod_config["enable_ontology"] is True
        # Dead code verwijderd: enable_auto_save, enable_all_rules, min_quality_score

    def test_lazy_loading_generator(self):
        """Test lazy loading van generator service."""
        # Arrange
        container = ServiceContainer()

        # Assert - nog niet geladen
        assert "generator" not in container._instances

        # Act
        generator = container.generator()

        # Assert - nu wel geladen
        assert "generator" in container._instances
        assert generator is not None

    def test_environment_config_loading(self):
        """Test laden van environment-specifieke config."""
        # Arrange
        import os

        # Test development
        os.environ["APP_ENV"] = "development"
        container = ServiceContainer()
        container._load_configuration()

        # Assert development defaults - model komt nu uit centrale config
        assert container.db_path == container.config.get(
            "db_path", "data/definities.db"
        )

        # Cleanup
        if "APP_ENV" in os.environ:
            del os.environ["APP_ENV"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
