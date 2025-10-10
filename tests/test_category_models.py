"""Tests voor category domain models."""

from datetime import datetime

import pytest

from src.models.category_models import (
    CategoryChangeResult,
    CategoryUpdateEvent,
    DefinitionCategory,
)


class TestCategoryModels:
    """Test class voor category domain models."""

    def test_definition_category_from_code(self):
        """Test DefinitionCategory factory method."""
        # Test alle valid codes
        test_cases = [
            ("ENT", "Entiteit"),
            ("REL", "Relatie"),
            ("ACT", "Activiteit"),
            ("ATT", "Attribuut"),
            ("AUT", "Autorisatie"),
            ("STA", "Status"),
            ("OTH", "Overig"),
            ("UNKNOWN", "UNKNOWN"),  # Onbekende code
        ]

        for code, expected_name in test_cases:
            category = DefinitionCategory.from_code(code)
            assert category.code == code
            assert category.display_name == expected_name
            assert category.reasoning is None
            assert category.confidence == 0.0

    def test_category_change_result_auto_timestamp(self):
        """Test dat CategoryChangeResult automatisch timestamp krijgt."""
        # Act
        result = CategoryChangeResult(success=True, message="Test")

        # Assert
        assert isinstance(result.timestamp, datetime)
        assert (datetime.now() - result.timestamp).total_seconds() < 1

    def test_category_update_event_full(self):
        """Test CategoryUpdateEvent met alle velden."""
        # Act
        event = CategoryUpdateEvent(
            definition_id=123,
            old_category="ENT",
            new_category="REL",
            changed_by="test_user",
            reason="Test reason",
        )

        # Assert
        assert event.definition_id == 123
        assert event.old_category == "ENT"
        assert event.new_category == "REL"
        assert event.changed_by == "test_user"
        assert event.reason == "Test reason"
        assert isinstance(event.timestamp, datetime)
