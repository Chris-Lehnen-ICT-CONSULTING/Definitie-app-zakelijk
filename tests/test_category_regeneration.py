"""Tests voor category regeneration functionaliteit."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import streamlit as st
from src.ui.components.definition_generator_tab import DefinitionGeneratorTab
from src.ui.components.category_regeneration_helper import CategoryRegenerationHelper


class TestCategoryRegeneration:
    """Test class voor category regeneration flow."""

    @pytest.fixture
    def mock_checker(self):
        """Mock DefinitieChecker."""
        return Mock()

    @pytest.fixture
    def generator_tab(self, mock_checker):
        """DefinitionGeneratorTab instance."""
        with patch('src.ui.components.definition_generator_tab.get_definitie_repository'):
            return DefinitionGeneratorTab(mock_checker)

    @patch('streamlit.warning')
    @patch('streamlit.info')
    @patch('src.ui.components.definition_generator_tab.SessionStateManager')
    def test_trigger_regeneration_with_category(
        self,
        mock_session,
        mock_info,
        mock_warning,
        generator_tab
    ):
        """Test trigger regeneration method."""
        # Arrange
        saved_record = Mock()
        saved_record.definitie = "Oude definitie"

        # Act
        generator_tab._trigger_regeneration_with_category(
            begrip="TestBegrip",
            new_category="ACT",
            old_category="ENT",
            saved_record=saved_record
        )

        # Assert
        mock_warning.assert_called_once()
        assert "Activiteit" in str(mock_warning.call_args)

        # Check session state update
        mock_session.set_value.assert_called_once()
        call_args = mock_session.set_value.call_args[0]
        assert call_args[0] == "regenerate_with_category"
        assert call_args[1]["begrip"] == "TestBegrip"
        assert call_args[1]["category"] == "ACT"
        assert "ENT" in call_args[1]["feedback"]
        assert "ACT" in call_args[1]["feedback"]

    def test_category_regeneration_helper_check(self):
        """Test CategoryRegenerationHelper check method."""
        # Arrange
        test_data = {
            "begrip": "TestBegrip",
            "category": "REL",
            "feedback": "Test feedback"
        }

        with patch('src.ui.components.category_regeneration_helper.SessionStateManager') as mock_sm:
            mock_sm.get_value.return_value = test_data

            # Act
            result = CategoryRegenerationHelper.check_for_regeneration_request()

            # Assert
            assert result == test_data
            mock_sm.clear_value.assert_called_once_with("regenerate_with_category")

    def test_category_regeneration_helper_no_request(self):
        """Test helper wanneer geen regeneration request."""
        with patch('src.ui.components.category_regeneration_helper.SessionStateManager') as mock_sm:
            mock_sm.get_value.return_value = None

            # Act
            result = CategoryRegenerationHelper.check_for_regeneration_request()

            # Assert
            assert result is None
            mock_sm.clear_value.assert_not_called()
