"""Tests voor CategoryStateManager."""

import pytest
from unittest.mock import Mock
from src.services.category_state_manager import CategoryStateManager
from models.category_models import DefinitionCategory


class TestCategoryStateManager:
    """Test class voor CategoryStateManager."""

    def test_update_generation_result_category(self):
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
        # Geen UI side-effecten meer; puur dict-mutatie

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

    def test_clear_category_selector(self):
        """Test clear category selector."""
        # Act
        CategoryStateManager.clear_category_selector()

        # Assert: no-op, geen exception en geen return
        assert CategoryStateManager.clear_category_selector() is None
