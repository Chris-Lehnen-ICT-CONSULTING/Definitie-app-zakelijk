"""
Tests voor SynonymRegistry.add_group_member() idempotent behavior.

Test coverage:
- Idempotent behavior: calling add_group_member() twice returns same ID
- No errors raised on duplicate adds
- Warning logged for duplicate attempts
- Cache invalidation only triggered once for duplicate
- Integration with sync flow (realistic scenario)
"""

import sqlite3
from pathlib import Path

import pytest

from src.repositories.synonym_registry import SynonymRegistry


class TestAddGroupMemberIdempotent:
    """Tests voor add_group_member() idempotent behavior."""

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

    def test_add_group_member_twice_returns_same_id(self, registry):
        """Test dat add_group_member() idempotent is: 2x add = same ID."""
        # Create group
        group = registry.get_or_create_group("oproeping")
        group_id = group.id

        # Add member first time
        member_id_1 = registry.add_group_member(
            group_id=group_id,
            term="oproeping",
            weight=1.0,
            status="active",
            source="manual",
        )

        # Add same member second time (should return existing ID)
        member_id_2 = registry.add_group_member(
            group_id=group_id,
            term="oproeping",
            weight=1.0,
            status="active",
            source="manual",
        )

        # Verify: same ID returned
        assert member_id_1 == member_id_2

        # Verify: only one member in group
        members = registry.get_group_members(group_id)
        assert len(members) == 1
        assert members[0].id == member_id_1

    def test_add_group_member_no_error_on_duplicate(self, registry):
        """Test dat add_group_member() GEEN error raised bij duplicate."""
        # Create group
        group = registry.get_or_create_group("dagvaarding")
        group_id = group.id

        # Add member
        registry.add_group_member(
            group_id=group_id, term="dagvaarding", weight=0.95, source="manual"
        )

        # Add duplicate - should NOT raise error
        try:
            registry.add_group_member(
                group_id=group_id, term="dagvaarding", weight=0.95, source="manual"
            )
        except ValueError as e:
            pytest.fail(f"add_group_member should be idempotent, but raised: {e}")

    def test_add_group_member_logs_warning_on_duplicate(self, registry, caplog):
        """Test dat add_group_member() warning logt bij duplicate."""
        import logging

        caplog.set_level(logging.WARNING)

        # Create group and add member
        group = registry.get_or_create_group("vonnis")
        group_id = group.id

        registry.add_group_member(group_id=group_id, term="vonnis", weight=0.90)

        # Clear logs
        caplog.clear()

        # Add duplicate
        registry.add_group_member(group_id=group_id, term="vonnis", weight=0.90)

        # Verify warning logged
        assert any("already in group" in record.message for record in caplog.records)
        assert any("idempotent" in record.message for record in caplog.records)

    def test_add_group_member_different_terms_creates_multiple(self, registry):
        """Test dat verschillende terms WEL meerdere members creëert."""
        # Create group
        group = registry.get_or_create_group("verdachte")
        group_id = group.id

        # Add different members
        member_id_1 = registry.add_group_member(
            group_id=group_id, term="beklaagde", weight=0.95
        )
        member_id_2 = registry.add_group_member(
            group_id=group_id, term="beschuldigde", weight=0.90
        )

        # Verify: different IDs
        assert member_id_1 != member_id_2

        # Verify: two members in group
        members = registry.get_group_members(group_id)
        assert len(members) == 2

    def test_add_group_member_case_sensitive_duplicate(self, registry):
        """Test dat duplicate check case-sensitive is (design decision)."""
        # Create group
        group = registry.get_or_create_group("rechter")
        group_id = group.id

        # Add lowercase
        member_id_1 = registry.add_group_member(
            group_id=group_id, term="magistraat", weight=0.95
        )

        # Add uppercase (should create separate member - case matters in our design)
        member_id_2 = registry.add_group_member(
            group_id=group_id, term="Magistraat", weight=0.95
        )

        # Design decision: case-sensitive terms are allowed
        # (normalization happens at input layer, not at DB layer)
        assert member_id_1 != member_id_2

        members = registry.get_group_members(group_id)
        assert len(members) == 2

    def test_add_group_member_idempotent_with_definitie_scope(self, registry):
        """Test idempotent behavior werkt ook met definitie_id scope."""
        # Create group
        group = registry.get_or_create_group("arrest")
        group_id = group.id

        # Add scoped member (definitie_id=None for global scope)
        # Note: We use None instead of specific ID to avoid FK constraint issues in tests
        member_id_1 = registry.add_group_member(
            group_id=group_id,
            term="uitspraak",
            weight=0.95,
            definitie_id=None,  # Global scope
            source="manual",
        )

        # Add same member with same scope (should return existing ID)
        member_id_2 = registry.add_group_member(
            group_id=group_id,
            term="uitspraak",
            weight=0.95,
            definitie_id=None,  # Global scope
            source="manual",
        )

        # Verify: same ID returned
        assert member_id_1 == member_id_2

        # Verify: only one member
        members = registry.get_group_members(group_id)
        assert len(members) == 1

    def test_add_group_member_sync_scenario_realistic(self, registry):
        """
        Test realistic sync scenario: upstream probeert duplicates toe te voegen.

        Dit is de use case die de idempotent fix oplost:
        - sync_synonyms_to_registry() probeert alle synoniemen te syncen
        - Duplicate entries kunnen voorkomen door race conditions of upstream bugs
        - add_group_member() moet deze gracefully afhandelen (return existing ID)
        """
        # Create group
        group = registry.get_or_create_group("oproeping")
        group_id = group.id

        # Simulate sync: batch van synoniemen waarvan sommige duplicates zijn
        synonyms_batch = [
            "oproeping",  # First add
            "dagvaarding",  # New
            "oproeping",  # Duplicate!
            "sommatie",  # New
            "oproeping",  # Duplicate again!
        ]

        # Sync all (zonder error te verwachten)
        member_ids = []
        for syn in synonyms_batch:
            member_id = registry.add_group_member(
                group_id=group_id, term=syn, weight=1.0, source="manual"
            )
            member_ids.append(member_id)

        # Verify: sync succeeded zonder errors
        assert len(member_ids) == 5

        # Verify: alleen unieke members in database
        members = registry.get_group_members(group_id)
        unique_terms = {m.term for m in members}
        assert len(members) == 3
        assert unique_terms == {"oproeping", "dagvaarding", "sommatie"}

        # Verify: duplicate IDs zijn hetzelfde
        assert member_ids[0] == member_ids[2] == member_ids[4]  # 'oproeping' IDs

    def test_add_group_member_cache_invalidation_once_for_duplicate(self, registry):
        """Test dat cache invalidation NIET dubbel triggert bij duplicate add."""
        # Track callback invocations
        invalidated_terms = []

        def callback(term: str):
            invalidated_terms.append(term)

        # Register callback
        registry.register_invalidation_callback(callback)

        # Create group
        group = registry.get_or_create_group("vonnis")
        group_id = group.id

        # Add member (triggers invalidation)
        registry.add_group_member(group_id=group_id, term="uitspraak", weight=0.95)

        # Clear callback tracking
        invalidated_terms.clear()

        # Add duplicate (should NOT trigger invalidation again)
        registry.add_group_member(group_id=group_id, term="uitspraak", weight=0.95)

        # Verify: no invalidation triggered for duplicate
        # (because we return early when existing member is found)
        assert len(invalidated_terms) == 0

    def test_add_group_member_returns_int_always(self, registry):
        """Test dat add_group_member() altijd een int (member_id) returnt."""
        # Create group
        group = registry.get_or_create_group("test")
        group_id = group.id

        # First add
        member_id_1 = registry.add_group_member(
            group_id=group_id, term="test_member", weight=0.9
        )
        assert isinstance(member_id_1, int)
        assert member_id_1 > 0

        # Duplicate add
        member_id_2 = registry.add_group_member(
            group_id=group_id, term="test_member", weight=0.9
        )
        assert isinstance(member_id_2, int)
        assert member_id_2 > 0
        assert member_id_2 == member_id_1


class TestAddGroupMemberEdgeCases:
    """Edge case tests voor add_group_member() idempotent behavior."""

    @pytest.fixture
    def registry(self, test_db_path):
        """Create registry with test database and apply schema."""
        schema_path = (
            Path(__file__).parent.parent.parent / "src" / "database" / "schema.sql"
        )

        with sqlite3.connect(test_db_path) as conn:
            conn.execute("PRAGMA foreign_keys=ON")
            with open(schema_path, encoding="utf-8") as f:
                schema_sql = f.read()
                conn.executescript(schema_sql)

        return SynonymRegistry(db_path=test_db_path)

    def test_add_group_member_empty_term_still_raises_error(self, registry):
        """Test dat empty term ALTIJD error raised (niet idempotent voor invalid input)."""
        group = registry.get_or_create_group("test")
        group_id = group.id

        # Empty term should still raise error (validation failure)
        with pytest.raises(ValueError, match="mag niet leeg zijn"):
            registry.add_group_member(group_id=group_id, term="", weight=0.9)

        with pytest.raises(ValueError, match="mag niet leeg zijn"):
            registry.add_group_member(group_id=group_id, term="   ", weight=0.9)

    def test_add_group_member_invalid_weight_still_raises_error(self, registry):
        """Test dat invalid weight ALTIJD error raised."""
        group = registry.get_or_create_group("test")
        group_id = group.id

        # Invalid weight should raise error
        with pytest.raises(ValueError, match="tussen 0.0 en 1.0"):
            registry.add_group_member(group_id=group_id, term="test", weight=1.5)

        with pytest.raises(ValueError, match="tussen 0.0 en 1.0"):
            registry.add_group_member(group_id=group_id, term="test", weight=-0.1)

    def test_add_group_member_nonexistent_group_still_raises_error(self, registry):
        """Test dat non-existent group ALTIJD error raised."""
        # Try to add member to non-existent group
        with pytest.raises(ValueError, match="bestaat niet"):
            registry.add_group_member(group_id=99999, term="test", weight=0.9)
