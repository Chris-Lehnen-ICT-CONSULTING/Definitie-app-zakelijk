"""Tests voor CategoryService v2 functionaliteit."""

from datetime import datetime
from unittest.mock import MagicMock, Mock

import pytest

from models.category_models import CategoryChangeResult
from src.database.definitie_repository import DefinitieRecord
from src.services.category_service import CategoryService


class TestCategoryServiceV2:
    """Test class voor CategoryService v2 methods."""

    @pytest.fixture()
    def mock_repository(self):
        """Mock repository voor tests."""
        return Mock()

    @pytest.fixture()
    def category_service(self, mock_repository):
        """CategoryService instance voor tests."""
        return CategoryService(mock_repository)

    @pytest.fixture()
    def sample_definition(self):
        """Sample definitie voor tests."""
        definition = Mock(spec=DefinitieRecord)
        definition.id = 1
        definition.begrip = "test_begrip"
        definition.categorie = "ENT"
        definition.status = "DRAFT"
        return definition

    def test_update_category_v2_success(
        self, category_service, mock_repository, sample_definition
    ):
        """Test succesvolle categorie update met v2."""
        # Arrange
        mock_repository.get_definitie_by_id.return_value = sample_definition
        mock_repository.update_definitie.return_value = True

        # Act
        result = category_service.update_category_v2(
            definition_id=1,
            new_category="REL",
            user="test_user",
            reason="Test wijziging",
        )

        # Assert
        assert isinstance(result, CategoryChangeResult)
        assert result.success is True
        assert result.previous_category == "ENT"
        assert result.new_category == "REL"
        assert "Relatie" in result.message
        assert result.timestamp is not None

    def test_update_category_v2_with_validation_failure(
        self, category_service, mock_repository
    ):
        """Test update met validatie fout."""
        # Arrange
        definition = Mock(spec=DefinitieRecord)
        definition.status = "APPROVED"  # Goedgekeurde definities mogen niet wijzigen
        mock_repository.get_definitie_by_id.return_value = definition

        # Act
        result = category_service.update_category_v2(
            definition_id=1, new_category="REL", user="test_user"
        )

        # Assert
        assert result.success is False
        assert "Goedgekeurde definities" in result.message

    def test_legacy_compatibility(
        self, category_service, mock_repository, sample_definition
    ):
        """Test dat legacy method nog werkt."""
        # Arrange
        mock_repository.get_definitie_by_id.return_value = sample_definition
        mock_repository.update_definitie.return_value = True

        # Act
        success, error = category_service.update_category(1, "REL")

        # Assert
        assert success is True
        assert error is None

    def test_category_change_result_model(self):
        """Test CategoryChangeResult model."""
        # Act
        result = CategoryChangeResult(
            success=True,
            message="Test message",
            previous_category="ENT",
            new_category="REL",
        )

        # Assert
        assert result.success is True
        assert result.message == "Test message"
        assert result.previous_category == "ENT"
        assert result.new_category == "REL"
        assert isinstance(result.timestamp, datetime)
