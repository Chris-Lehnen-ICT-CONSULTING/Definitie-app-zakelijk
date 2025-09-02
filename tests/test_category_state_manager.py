"""Tests voor CategoryStateManager."""

import pytest
from unittest.mock import Mock, patch
from src.services.category_state_manager import CategoryStateManager
from models.category_models import DefinitionCategory


class TestCategoryStateManager:
    """Test class voor CategoryStateManager."""

    @patch('src.services.category_state_manager.SessionStateManager')
    def test_update_generation_result_category(self, mock_session_manager):
        """Test update van category in generation result."""
        # Arrange
        generation_result = {
            "begrip": "test",
            "determined_category": "ENT",
            "other_data": "preserved"
        }

        # Act
        result = CategoryStateManager.update_generation_result_category(
            generation_result, "REL"
        )

        # Assert
        assert result["determined_category"] == "REL"
        assert result["other_data"] == "preserved"  # Other data preserved
        mock_session_manager.set_value.assert_called_once_with(
            "last_generation_result", result
        )

    def test_get_current_category_exists(self):
        """Test get current category wanneer deze bestaat."""
        # Arrange
        generation_result = {"determined_category": "ENT"}

        # Act
        category = CategoryStateManager.get_current_category(generation_result)

        # Assert
        assert isinstance(category, DefinitionCategory)
        assert category.code == "ENT"
        assert category.display_name == "Entiteit"

    def test_get_current_category_not_exists(self):
        """Test get current category wanneer deze niet bestaat."""
        # Arrange
        generation_result = {}

        # Act
        category = CategoryStateManager.get_current_category(generation_result)

        # Assert
        assert category is None

    @patch('src.services.category_state_manager.SessionStateManager')
    def test_clear_category_selector(self, mock_session_manager):
        """Test clear category selector."""
        # Act
        CategoryStateManager.clear_category_selector()

        # Assert
        mock_session_manager.set_value.assert_called_once_with(
            "show_category_selector", False
        )
