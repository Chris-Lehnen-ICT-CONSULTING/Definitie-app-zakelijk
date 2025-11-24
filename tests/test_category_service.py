"""Tests voor CategoryService."""

from unittest.mock import MagicMock, Mock

import pytest

from src.database.definitie_repository import DefinitieRecord
from src.services.category_service import CategoryService


class TestCategoryService:
    """Test class voor CategoryService."""

    @pytest.fixture
    def mock_repository(self):
        """Mock repository voor tests."""
        return Mock()

    @pytest.fixture
    def category_service(self, mock_repository):
        """CategoryService instance voor tests."""
        return CategoryService(mock_repository)

    @pytest.fixture
    def sample_definition(self):
        """Sample definitie voor tests."""
        definition = Mock(spec=DefinitieRecord)
        definition.id = 1
        definition.begrip = "test_begrip"
        definition.categorie = "ENT"
        definition.status = "DRAFT"
        return definition

    def test_update_category_success(
        self, category_service, mock_repository, sample_definition
    ):
        """Test succesvolle categorie update."""
        # Arrange
        mock_repository.get_definitie_by_id.return_value = sample_definition
        mock_repository.update_definitie.return_value = True

        # Act
        success, error = category_service.update_category(1, "REL")

        # Assert
        assert success is True
        assert error is None
        assert sample_definition.categorie == "REL"
        mock_repository.get_definitie_by_id.assert_called_once_with(1)
        mock_repository.update_definitie.assert_called_once_with(sample_definition)

    def test_update_category_invalid_category(self, category_service):
        """Test update met ongeldige categorie."""
        # Act
        success, error = category_service.update_category(1, "INVALID")

        # Assert
        assert success is False
        assert error == "Ongeldige categorie: INVALID"

    def test_update_category_definition_not_found(
        self, category_service, mock_repository
    ):
        """Test update wanneer definitie niet bestaat."""
        # Arrange
        mock_repository.get_definitie_by_id.return_value = None

        # Act
        success, error = category_service.update_category(999, "REL")

        # Assert
        assert success is False
        assert error == "Definitie met ID 999 niet gevonden"

    def test_update_category_database_error(
        self, category_service, mock_repository, sample_definition
    ):
        """Test update met database fout."""
        # Arrange
        mock_repository.get_definitie_by_id.return_value = sample_definition
        mock_repository.update_definitie.return_value = False

        # Act
        success, error = category_service.update_category(1, "REL")

        # Assert
        assert success is False
        assert error == "Database update mislukt"

    def test_update_category_exception(self, category_service, mock_repository):
        """Test update met exception."""
        # Arrange
        mock_repository.get_definitie_by_id.side_effect = Exception(
            "Database connection error"
        )

        # Act
        success, error = category_service.update_category(1, "REL")

        # Assert
        assert success is False
        assert "Fout bij bijwerken categorie: Database connection error" in error

    def test_get_category_display_name(self, category_service):
        """Test category display namen."""
        # Test bekende categorieën
        assert category_service.get_category_display_name("ENT") == "Entiteit"
        assert category_service.get_category_display_name("REL") == "Relatie"
        assert category_service.get_category_display_name("ACT") == "Activiteit"
        assert category_service.get_category_display_name("ATT") == "Attribuut"
        assert category_service.get_category_display_name("AUT") == "Autorisatie"
        assert category_service.get_category_display_name("STA") == "Status"
        assert category_service.get_category_display_name("OTH") == "Overig"

        # Test onbekende categorie
        assert category_service.get_category_display_name("UNKNOWN") == "UNKNOWN"

    def test_validate_category_change_approved_definition(self, category_service):
        """Test validatie voor goedgekeurde definitie."""
        # Arrange
        definition = Mock(spec=DefinitieRecord)
        definition.status = "APPROVED"

        # Act
        is_valid, error = category_service.validate_category_change(definition, "REL")

        # Assert
        assert is_valid is False
        assert error == "Goedgekeurde definities kunnen niet van categorie wijzigen"

    def test_validate_category_change_draft_definition(self, category_service):
        """Test validatie voor draft definitie."""
        # Arrange
        definition = Mock(spec=DefinitieRecord)
        definition.status = "DRAFT"

        # Act
        is_valid, error = category_service.validate_category_change(definition, "REL")

        # Assert
        assert is_valid is True
        assert error is None

    def test_all_valid_categories(
        self, category_service, mock_repository, sample_definition
    ):
        """Test alle geldige categorieën."""
        # Arrange
        valid_categories = ["ENT", "REL", "ACT", "ATT", "AUT", "STA", "OTH"]
        mock_repository.get_definitie_by_id.return_value = sample_definition
        mock_repository.update_definitie.return_value = True

        # Act & Assert
        for category in valid_categories:
            success, error = category_service.update_category(1, category)
            assert success is True
            assert error is None
            assert sample_definition.categorie == category
