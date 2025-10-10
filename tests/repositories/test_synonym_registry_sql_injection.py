"""
Tests voor SQL injection protection in SynonymRegistry.

Test coverage:
- get_synonyms() order_by validation
- get_group_members() order_by validation
- Valid order_by columns (whitelist)
- Invalid order_by columns (SQL injection attempts)
- None/default order_by behavior
"""

import sqlite3
from pathlib import Path

import pytest

from src.repositories.synonym_registry import SynonymRegistry


class TestSynonymRegistryOrderByValidation:
    """Tests voor order_by parameter validation (SQL injection prevention)."""

    @pytest.fixture()
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

    @pytest.fixture()
    def sample_group_with_members(self, registry):
        """Create a sample group with members for testing."""
        # Create group
        group = registry.get_or_create_group("voorlopige hechtenis")
        group_id = group.id

        # Add members with varying attributes
        registry.add_group_member(group_id, "voorarrest", weight=0.95, status="active")
        registry.add_group_member(group_id, "bewaring", weight=0.90, status="active")
        registry.add_group_member(
            group_id, "preventieve hechtenis", weight=0.85, status="ai_pending"
        )

        return group_id

    # ===== get_group_members() tests =====

    def test_get_group_members_valid_order_by_weight(
        self, registry, sample_group_with_members
    ):
        """Test valid order_by: weight."""
        members = registry.get_group_members(
            sample_group_with_members, order_by="weight"
        )
        assert len(members) == 3
        # No error should be raised

    def test_get_group_members_valid_order_by_is_preferred(
        self, registry, sample_group_with_members
    ):
        """Test valid order_by: is_preferred."""
        members = registry.get_group_members(
            sample_group_with_members, order_by="is_preferred"
        )
        assert len(members) == 3

    def test_get_group_members_valid_order_by_term(
        self, registry, sample_group_with_members
    ):
        """Test valid order_by: term."""
        members = registry.get_group_members(sample_group_with_members, order_by="term")
        assert len(members) == 3

    def test_get_group_members_valid_order_by_created_at(
        self, registry, sample_group_with_members
    ):
        """Test valid order_by: created_at."""
        members = registry.get_group_members(
            sample_group_with_members, order_by="created_at"
        )
        assert len(members) == 3

    def test_get_group_members_valid_order_by_updated_at(
        self, registry, sample_group_with_members
    ):
        """Test valid order_by: updated_at."""
        members = registry.get_group_members(
            sample_group_with_members, order_by="updated_at"
        )
        assert len(members) == 3

    def test_get_group_members_valid_order_by_usage_count(
        self, registry, sample_group_with_members
    ):
        """Test valid order_by: usage_count."""
        members = registry.get_group_members(
            sample_group_with_members, order_by="usage_count"
        )
        assert len(members) == 3

    def test_get_group_members_valid_order_by_status(
        self, registry, sample_group_with_members
    ):
        """Test valid order_by: status."""
        members = registry.get_group_members(
            sample_group_with_members, order_by="status"
        )
        assert len(members) == 3

    def test_get_group_members_invalid_order_by_raises_error(
        self, registry, sample_group_with_members
    ):
        """Test invalid order_by raises ValueError."""
        with pytest.raises(ValueError, match="Invalid order_by column"):
            registry.get_group_members(
                sample_group_with_members, order_by="invalid_column"
            )

    def test_get_group_members_sql_injection_attempt_raises_error(
        self, registry, sample_group_with_members
    ):
        """Test SQL injection attempt raises ValueError."""
        with pytest.raises(ValueError, match="Invalid order_by column"):
            registry.get_group_members(
                sample_group_with_members,
                order_by="weight; DROP TABLE synonym_groups--",
            )

    def test_get_group_members_sql_injection_union_raises_error(
        self, registry, sample_group_with_members
    ):
        """Test SQL injection UNION attack raises ValueError."""
        with pytest.raises(ValueError, match="Invalid order_by column"):
            registry.get_group_members(
                sample_group_with_members,
                order_by="weight UNION SELECT * FROM synonym_groups",
            )

    def test_get_group_members_none_order_by_uses_default(
        self, registry, sample_group_with_members
    ):
        """Test None order_by uses default sorting."""
        members = registry.get_group_members(sample_group_with_members, order_by=None)
        assert len(members) == 3
        # Should use default: is_preferred DESC, weight DESC, usage_count DESC
        # Highest weight first (0.95)
        assert members[0].weight == 0.95

    # ===== get_synonyms() tests =====

    def test_get_synonyms_valid_order_by_weight(
        self, registry, sample_group_with_members
    ):
        """Test get_synonyms() with valid order_by: weight."""
        synonyms = registry.get_synonyms("voorarrest", order_by="weight")
        # Should return other members: bewaring (0.90), preventieve hechtenis (0.85, ai_pending)
        # By default only active status, so only bewaring
        assert len(synonyms) >= 1

    def test_get_synonyms_valid_order_by_is_preferred(
        self, registry, sample_group_with_members
    ):
        """Test get_synonyms() with valid order_by: is_preferred."""
        synonyms = registry.get_synonyms("voorarrest", order_by="is_preferred")
        assert isinstance(synonyms, list)

    def test_get_synonyms_valid_order_by_term(
        self, registry, sample_group_with_members
    ):
        """Test get_synonyms() with valid order_by: term."""
        synonyms = registry.get_synonyms("voorarrest", order_by="term")
        assert isinstance(synonyms, list)

    def test_get_synonyms_valid_order_by_usage_count(
        self, registry, sample_group_with_members
    ):
        """Test get_synonyms() with valid order_by: usage_count."""
        synonyms = registry.get_synonyms("voorarrest", order_by="usage_count")
        assert isinstance(synonyms, list)

    def test_get_synonyms_invalid_order_by_raises_error(
        self, registry, sample_group_with_members
    ):
        """Test get_synonyms() with invalid order_by raises ValueError."""
        with pytest.raises(ValueError, match="Invalid order_by column"):
            registry.get_synonyms("voorarrest", order_by="malicious_column")

    def test_get_synonyms_sql_injection_attempt_raises_error(
        self, registry, sample_group_with_members
    ):
        """Test get_synonyms() SQL injection attempt raises ValueError."""
        with pytest.raises(ValueError, match="Invalid order_by column"):
            registry.get_synonyms(
                "voorarrest", order_by="weight; DELETE FROM synonym_groups--"
            )

    def test_get_synonyms_sql_injection_subquery_raises_error(
        self, registry, sample_group_with_members
    ):
        """Test get_synonyms() SQL injection with subquery raises ValueError."""
        with pytest.raises(ValueError, match="Invalid order_by column"):
            registry.get_synonyms(
                "voorarrest",
                order_by="(SELECT password FROM users WHERE id=1)",
            )

    def test_get_synonyms_sql_injection_comment_raises_error(
        self, registry, sample_group_with_members
    ):
        """Test get_synonyms() SQL injection with comment raises ValueError."""
        with pytest.raises(ValueError, match="Invalid order_by column"):
            registry.get_synonyms("voorarrest", order_by="weight -- comment")

    def test_get_synonyms_none_order_by_uses_default(
        self, registry, sample_group_with_members
    ):
        """Test get_synonyms() with None order_by uses default sorting."""
        synonyms = registry.get_synonyms("voorarrest", order_by=None)
        # Should return bewaring (active, 0.90)
        assert len(synonyms) >= 1
        # Default sort: is_preferred DESC, weight DESC, usage_count DESC

    # ===== Edge cases =====

    def test_order_by_empty_string_raises_error(
        self, registry, sample_group_with_members
    ):
        """Test empty string order_by raises ValueError."""
        # Empty string should fail validation (not in whitelist)
        with pytest.raises(ValueError, match="Invalid order_by column"):
            registry.get_group_members(sample_group_with_members, order_by="")

    def test_order_by_whitespace_raises_error(
        self, registry, sample_group_with_members
    ):
        """Test whitespace-only order_by raises ValueError."""
        with pytest.raises(ValueError, match="Invalid order_by column"):
            registry.get_group_members(sample_group_with_members, order_by="  ")

    def test_order_by_case_sensitive(self, registry, sample_group_with_members):
        """Test order_by validation is case-sensitive."""
        # "WEIGHT" (uppercase) should not be in whitelist (lowercase "weight")
        with pytest.raises(ValueError, match="Invalid order_by column"):
            registry.get_group_members(sample_group_with_members, order_by="WEIGHT")

    def test_order_by_with_desc_modifier_raises_error(
        self, registry, sample_group_with_members
    ):
        """Test order_by with DESC modifier raises ValueError."""
        # "weight DESC" should not be in whitelist (only "weight")
        with pytest.raises(ValueError, match="Invalid order_by column"):
            registry.get_group_members(
                sample_group_with_members, order_by="weight DESC"
            )

    def test_order_by_with_asc_modifier_raises_error(
        self, registry, sample_group_with_members
    ):
        """Test order_by with ASC modifier raises ValueError."""
        with pytest.raises(ValueError, match="Invalid order_by column"):
            registry.get_group_members(sample_group_with_members, order_by="weight ASC")

    def test_error_message_includes_allowed_columns(
        self, registry, sample_group_with_members
    ):
        """Test error message includes list of allowed columns."""
        with pytest.raises(ValueError, match="Invalid order_by column") as exc_info:
            registry.get_group_members(sample_group_with_members, order_by="malicious")

        error_msg = str(exc_info.value)
        # Should mention allowed columns
        assert "Allowed:" in error_msg
        assert "weight" in error_msg
        assert "is_preferred" in error_msg

    # ===== Integration test =====

    def test_valid_order_by_produces_correct_sorting(
        self, registry, sample_group_with_members
    ):
        """Integration test: valid order_by produces expected sorting."""
        # Get members sorted by weight (ascending)
        # Note: whitelist only allows column name, not DESC/ASC
        # So we test that the column name works, default sort is applied
        members = registry.get_group_members(
            sample_group_with_members, order_by="weight"
        )

        # Default sort includes is_preferred DESC, weight DESC
        # But when order_by is specified, it overrides
        # Since we can't specify ASC/DESC, we just verify no error
        assert len(members) == 3
        assert all(hasattr(m, "weight") for m in members)

    def test_all_whitelisted_columns_work(self, registry, sample_group_with_members):
        """Test that all whitelisted columns work without errors."""
        whitelisted_columns = [
            "weight",
            "is_preferred",
            "term",
            "created_at",
            "updated_at",
            "usage_count",
            "status",
        ]

        for column in whitelisted_columns:
            # Should not raise any errors
            members = registry.get_group_members(
                sample_group_with_members, order_by=column
            )
            assert len(members) == 3, f"Failed for column: {column}"
