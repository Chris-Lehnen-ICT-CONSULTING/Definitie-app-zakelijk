"""
Unit tests voor ServiceContainer.
"""
import pytest
from unittest.mock import patch, Mock
import sys
from pathlib import Path

# Voeg src toe aan path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from services.container import ServiceContainer, get_container, reset_container, ContainerConfigs
from services.interfaces import (
    DefinitionGeneratorInterface,

    DefinitionRepositoryInterface,
    DefinitionOrchestratorInterface
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
        assert container._generator is None  # Lazy loading

    def test_container_with_config(self):
        """Test container met custom config."""
        # Arrange
        config = {
            'db_path': 'test.db',
            'generator_model': 'gpt-3.5-turbo'
        }

        # Act
        container = ServiceContainer(config)

        # Assert
        assert container.config['db_path'] == 'test.db'
        assert container.config['generator_model'] == 'gpt-3.5-turbo'

    def test_generator_singleton(self):
        """Test dat generator een singleton is."""
        # Arrange
        container = ServiceContainer()

        # Act
        gen1 = container.generator()
        gen2 = container.generator()

        # Assert
        assert gen1 is gen2
        assert isinstance(gen1, DefinitionGeneratorInterface)

    def test_validator_removed(self):
        """Test dat legacy validator is verwijderd."""
        # Arrange
        container = ServiceContainer()

        # Act & Assert
        # Legacy validator() method should not exist
        assert not hasattr(container, 'validator')

    def test_repository_singleton(self):
        """Test dat repository een singleton is."""
        # Arrange
        container = ServiceContainer({'db_path': ':memory:'})

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
        generator = container.get_service('generator')
        validator = container.get_service('validator')
        invalid = container.get_service('invalid')

        # Assert
        assert isinstance(generator, DefinitionGeneratorInterface)
        # Legacy validator removed - skipping this assertion
        assert invalid is None

    def test_update_config(self):
        """Test config update en reset."""
        # Arrange
        container = ServiceContainer({'db_path': 'old.db'})
        gen1 = container.generator()

        # Act
        container.update_config({'db_path': 'new.db'})
        gen2 = container.generator()

        # Assert
        assert container.config['db_path'] == 'new.db'
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
        assert dev_config['generator_model'] == 'gpt-3.5-turbo'
        assert dev_config['db_path'] == 'dev_definities.db'
        assert dev_config['enable_auto_save'] is False

        # Test testing config
        test_config = ContainerConfigs.testing()
        assert test_config['db_path'] == ':memory:'
        assert test_config['enable_monitoring'] is False

        # Test production config
        prod_config = ContainerConfigs.production()
        assert prod_config['generator_model'] == 'gpt-4'
        assert prod_config['enable_auto_save'] is True
        assert prod_config['min_quality_score'] == 0.7

    @patch('services.container.DefinitionGenerator')
    def test_lazy_loading_generator(self, mock_generator_class):
        """Test lazy loading van generator service."""
        # Arrange
        container = ServiceContainer()
        mock_instance = Mock()
        mock_generator_class.return_value = mock_instance

        # Assert - nog niet geladen
        assert container._generator is None

        # Act
        generator = container.generator()

        # Assert - nu wel geladen
        assert container._generator is not None
        assert generator == mock_instance
        mock_generator_class.assert_called_once()

    def test_environment_config_loading(self):
        """Test laden van environment-specifieke config."""
        # Arrange
        import os

        # Test development
        os.environ['APP_ENV'] = 'development'
        container = ServiceContainer()
        container._load_configuration()

        # Assert development defaults
        assert container.config.get('generator_model') == 'gpt-3.5-turbo'

        # Cleanup
        del os.environ['APP_ENV']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
