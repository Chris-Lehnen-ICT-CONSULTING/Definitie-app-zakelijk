"""Tests voor CategoryService."""

from unittest.mock import MagicMock, Mock

import pytest

from database.definitie_repository import DefinitieRecord
from services.category_service import CategoryService

pytestmark = [pytest.mark.unit]


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
        mock_repository.get_definitie.return_value = sample_definition
        mock_repository.record_category_choice.return_value = True

        # Act
        success, error = category_service.update_category(1, "REL", expected_version=3)

        # Assert
        assert success is True
        assert error is None
        mock_repository.get_definitie.assert_called_once_with(1)
        # DEF-751 B2: de toepassen-route loopt via het expliciete commando met
        # de versie van de getoonde kandidaat; zonder identiteit blijft de
        # keuze ongeattribueerd — geen verzonnen "web_user" meer als actor.
        mock_repository.record_category_choice.assert_called_once_with(
            1,
            {},
            waarde="REL",
            herkomst="manual",
            actor=None,
            actor_source=None,
            updated_by=None,
            expected_version=3,
        )
        mock_repository.update_definitie.assert_not_called()

    def test_update_category_invalid_category(self, category_service):
        """Test update met ongeldige categorie."""
        # Act
        success, error = category_service.update_category(
            1, "INVALID", expected_version=1
        )

        # Assert
        assert success is False
        assert error == "Ongeldige categorie: INVALID"

    def test_update_category_definition_not_found(
        self, category_service, mock_repository
    ):
        """Test update wanneer definitie niet bestaat."""
        # Arrange
        mock_repository.get_definitie.return_value = None

        # Act
        success, error = category_service.update_category(
            999, "REL", expected_version=1
        )

        # Assert
        assert success is False
        assert error == "Definitie met ID 999 niet gevonden"

    def test_update_category_version_conflict(
        self, category_service, mock_repository, sample_definition
    ):
        """Test update bij een tussentijdse wijziging (versieguard → False)."""
        # Arrange
        mock_repository.get_definitie.return_value = sample_definition
        mock_repository.record_category_choice.return_value = False

        # Act
        success, error = category_service.update_category(1, "REL", expected_version=1)

        # Assert
        assert success is False
        assert "versieconflict" in error

    def test_update_category_exception(self, category_service, mock_repository):
        """Test update met exception."""
        # Arrange
        mock_repository.get_definitie.side_effect = Exception(
            "Database connection error"
        )

        # Act
        success, error = category_service.update_category(1, "REL", expected_version=1)

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
        definition.status = "established"

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
        mock_repository.get_definitie.return_value = sample_definition
        mock_repository.record_category_choice.return_value = True

        # Act & Assert
        for category in valid_categories:
            success, error = category_service.update_category(
                1, category, expected_version=1
            )
            assert success is True
            assert error is None
