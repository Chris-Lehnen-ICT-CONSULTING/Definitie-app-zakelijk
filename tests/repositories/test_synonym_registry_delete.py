"""
Tests voor SynonymRegistry.delete_group() method.

Test coverage:
- Delete empty group (cascade=True)
- Delete empty group (cascade=False)
- Delete group with members (cascade=True)
- Delete group with members (cascade=False) - should raise error
- Delete non-existent group - should raise error
- Verify cache invalidation callbacks are triggered
"""

import sqlite3
from pathlib import Path

import pytest

from src.repositories.synonym_registry import SynonymRegistry


class TestSynonymRegistryDelete:
    """Tests voor delete_group() method."""

    @pytest.fixture
    def registry(self, test_db_path):
        """Create registry with test database and apply schema."""
        # Apply full schema (includes definities table needed for FK)
        schema_path = (
            Path(__file__).parent.parent.parent / "src" / "database" / "schema.sql"
        )

        with sqlite3.connect(test_db_path) as conn:
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys=ON")

            with open(schema_path, encoding="utf-8") as f:
                schema_sql = f.read()
                conn.executescript(schema_sql)

        return SynonymRegistry(db_path=test_db_path)

    def test_delete_empty_group_cascade_true(self, registry):
        """Test deleting empty group with cascade=True."""
        # Create empty group
        group = registry.get_or_create_group("test_term")
        group_id = group.id

        # Delete
        success = registry.delete_group(group_id, cascade=True)
        assert success

        # Verify deleted
        deleted_group = registry.get_group(group_id)
        assert deleted_group is None

    def test_delete_empty_group_cascade_false(self, registry):
        """Test deleting empty group with cascade=False."""
        # Create empty group
        group = registry.get_or_create_group("test_term")
        group_id = group.id

        # Delete should succeed (no members)
        success = registry.delete_group(group_id, cascade=False)
        assert success

        # Verify deleted
        deleted_group = registry.get_group(group_id)
        assert deleted_group is None

    def test_delete_group_with_members_cascade_true(self, registry):
        """Test deleting group with members using cascade=True."""
        # Create group with members
        group = registry.get_or_create_group("voorlopige hechtenis")
        group_id = group.id

        # Add members
        registry.add_group_member(group_id, "voorarrest", weight=0.95)
        registry.add_group_member(group_id, "bewaring", weight=0.90)

        # Verify members exist
        members = registry.get_group_members(group_id)
        assert len(members) == 2

        # Delete with cascade
        success = registry.delete_group(group_id, cascade=True)
        assert success

        # Verify group deleted
        deleted_group = registry.get_group(group_id)
        assert deleted_group is None

        # Verify members deleted
        members_after = registry.get_group_members(group_id)
        assert len(members_after) == 0

    def test_delete_group_with_members_cascade_false_raises_error(self, registry):
        """Test deleting group with members using cascade=False raises error."""
        # Create group with members
        group = registry.get_or_create_group("verdachte")
        group_id = group.id

        # Add member
        registry.add_group_member(group_id, "beklaagde", weight=0.90)

        # Attempt delete without cascade should fail
        with pytest.raises(ValueError, match=r"heeft .* members"):
            registry.delete_group(group_id, cascade=False)

        # Verify group still exists
        existing_group = registry.get_group(group_id)
        assert existing_group is not None
        assert existing_group.id == group_id

        # Verify member still exists
        members = registry.get_group_members(group_id)
        assert len(members) == 1

    def test_delete_nonexistent_group_raises_error(self, registry):
        """Test deleting non-existent group raises error."""
        with pytest.raises(ValueError, match="bestaat niet"):
            registry.delete_group(99999, cascade=True)

    def test_delete_group_triggers_invalidation_callbacks(self, registry):
        """Test dat delete_group cache invalidation callbacks triggert."""
        # Track callback invocations
        invalidated_terms = []

        def callback(term: str):
            invalidated_terms.append(term)

        # Register callback
        registry.register_invalidation_callback(callback)

        # Create group with members
        group = registry.get_or_create_group("vonnis")
        group_id = group.id
        registry.add_group_member(group_id, "uitspraak", weight=0.95)
        registry.add_group_member(group_id, "arrest", weight=0.90)

        # Clear previous callbacks from add_group_member
        invalidated_terms.clear()

        # Delete group with cascade
        registry.delete_group(group_id, cascade=True)

        # Verify callbacks triggered for all members + canonical term
        assert "uitspraak" in invalidated_terms
        assert "arrest" in invalidated_terms
        assert "vonnis" in invalidated_terms
        assert len(invalidated_terms) == 3

    def test_delete_group_with_many_members(self, registry):
        """Test deleting group with many members."""
        # Create group with multiple members
        group = registry.get_or_create_group("rechter")
        group_id = group.id

        # Add many members
        members_to_add = [
            "magistraat",
            "rechterlijke macht",
            "juridisch beslisser",
            "rechtsspreker",
            "beslagrechter",
        ]

        for member in members_to_add:
            registry.add_group_member(group_id, member, weight=0.85)

        # Verify all added
        members = registry.get_group_members(group_id)
        assert len(members) == len(members_to_add)

        # Delete with cascade
        success = registry.delete_group(group_id, cascade=True)
        assert success

        # Verify all deleted
        deleted_group = registry.get_group(group_id)
        assert deleted_group is None

        members_after = registry.get_group_members(group_id)
        assert len(members_after) == 0

    def test_delete_group_returns_true_on_success(self, registry):
        """Test dat delete_group True returnt bij succes."""
        group = registry.get_or_create_group("test_success")
        group_id = group.id

        result = registry.delete_group(group_id, cascade=True)
        assert result is True

    def test_cascade_parameter_default_is_true(self, registry):
        """Test dat cascade parameter standaard True is."""
        # Create group with member
        group = registry.get_or_create_group("test_default")
        group_id = group.id
        registry.add_group_member(group_id, "test_member", weight=0.95)

        # Delete without specifying cascade (should default to True)
        success = registry.delete_group(group_id)
        assert success

        # Verify both group and member deleted
        deleted_group = registry.get_group(group_id)
        assert deleted_group is None

        members = registry.get_group_members(group_id)
        assert len(members) == 0
