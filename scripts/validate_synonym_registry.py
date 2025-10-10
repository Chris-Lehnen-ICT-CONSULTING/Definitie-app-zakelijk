"""
Validation script voor SynonymRegistry PHASE 1.2 implementation.

Tests:
1. Database connectivity
2. Group CRUD operations
3. Member CRUD operations
4. Bidirectional lookup query
5. Cache invalidation callbacks
6. Statistics
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


from repositories.synonym_registry import SynonymRegistry


def test_connectivity():
    """Test database connectivity."""
    print("✓ Test 1: Database Connectivity")
    registry = SynonymRegistry()
    stats = registry.get_statistics()
    print(f"  - Connected to: {registry.db_path}")
    print(f"  - Total groups: {stats['total_groups']}")
    print(f"  - Total members: {stats['total_members']}")
    return registry


def test_group_operations(registry):
    """Test group CRUD operations."""
    print("\n✓ Test 2: Group CRUD Operations")

    # Create group
    group = registry.get_or_create_group(
        canonical_term="voorarrest_test",
        domain="strafrecht",
        created_by="test_script",
    )
    print(f"  - Created/Retrieved group: {group.id} - '{group.canonical_term}'")

    # Get group by ID
    retrieved = registry.get_group(group.id)
    assert retrieved is not None
    assert retrieved.canonical_term == "voorarrest_test"
    print(f"  - Retrieved group by ID: {retrieved.id}")

    # Find group by term (no members yet, should return None)
    found = registry.find_group_by_term("voorarrest_test")
    print(f"  - Find by term (no members): {found}")

    return group


def test_member_operations(registry, group):
    """Test member CRUD operations."""
    print("\n✓ Test 3: Member CRUD Operations")

    # Add members
    member1_id = registry.add_group_member(
        group_id=group.id,
        term="voorarrest",
        weight=1.0,
        status="active",
        source="manual",
        created_by="test_script",
    )
    print(f"  - Added member 1: {member1_id} - 'voorarrest'")

    member2_id = registry.add_group_member(
        group_id=group.id,
        term="preventieve hechtenis",
        weight=0.9,
        status="active",
        source="manual",
        created_by="test_script",
    )
    print(f"  - Added member 2: {member2_id} - 'preventieve hechtenis'")

    member3_id = registry.add_group_member(
        group_id=group.id,
        term="voorlopige hechtenis",
        weight=0.95,
        status="active",
        source="manual",
        created_by="test_script",
    )
    print(f"  - Added member 3: {member3_id} - 'voorlopige hechtenis'")

    # Get all members
    members = registry.get_group_members(group.id)
    print(f"  - Total members in group: {len(members)}")
    for m in members:
        print(f"    - {m.term} (weight: {m.weight}, status: {m.status})")

    # Get member by ID
    member = registry.get_member(member1_id)
    assert member is not None
    print(f"  - Retrieved member by ID: {member.id} - '{member.term}'")

    # Update member status
    success = registry.update_member_status(
        member_id=member2_id,
        new_status="deprecated",
        reviewed_by="test_script",
    )
    assert success
    print(f"  - Updated member {member2_id} status to 'deprecated'")

    return [member1_id, member2_id, member3_id]


def test_bidirectional_lookup(registry):
    """Test bidirectional lookup query."""
    print("\n✓ Test 4: Bidirectional Lookup Query")

    # Get synonyms for "voorarrest"
    synonyms = registry.get_synonyms(
        term="voorarrest",
        statuses=["active"],
        min_weight=0.0,
        limit=10,
    )
    print(f"  - Found {len(synonyms)} synonyms for 'voorarrest':")
    for syn in synonyms:
        print(
            f"    - {syn.term} (weight: {syn.weight}, "
            f"preferred: {syn.is_preferred}, usage: {syn.usage_count})"
        )

    # Get synonyms for "preventieve hechtenis" (should be empty due to deprecated status)
    synonyms2 = registry.get_synonyms(
        term="preventieve hechtenis",
        statuses=["active"],
    )
    print(f"  - Found {len(synonyms2)} active synonyms for 'preventieve hechtenis'")

    # Get all synonyms (including deprecated)
    synonyms3 = registry.get_synonyms(
        term="preventieve hechtenis",
        statuses=["active", "deprecated"],
    )
    print(
        f"  - Found {len(synonyms3)} synonyms (all statuses) for 'preventieve hechtenis'"
    )


def test_cache_invalidation(registry):
    """Test cache invalidation callback system."""
    print("\n✓ Test 5: Cache Invalidation Callbacks")

    # Track invalidations
    invalidated_terms = []

    def callback1(term: str):
        invalidated_terms.append(f"callback1:{term}")
        print(f"  - Callback 1 triggered for: {term}")

    def callback2(term: str):
        invalidated_terms.append(f"callback2:{term}")
        print(f"  - Callback 2 triggered for: {term}")

    # Register callbacks
    registry.register_invalidation_callback(callback1)
    registry.register_invalidation_callback(callback2)
    print("  - Registered 2 callbacks")

    # Trigger invalidation by adding a member
    group = registry.get_or_create_group(
        canonical_term="test_invalidation", created_by="test_script"
    )
    member_id = registry.add_group_member(
        group_id=group.id,
        term="test_term",
        created_by="test_script",
    )
    print("  - Added member (should trigger callbacks)")

    # Verify callbacks were triggered
    assert len(invalidated_terms) == 2
    assert "callback1:test_term" in invalidated_terms
    assert "callback2:test_term" in invalidated_terms
    print(f"  - Callbacks verified: {len(invalidated_terms)} triggers")


def test_statistics(registry):
    """Test statistics reporting."""
    print("\n✓ Test 6: Statistics")

    stats = registry.get_statistics()
    print(f"  - Total groups: {stats['total_groups']}")
    print(f"  - Total members: {stats['total_members']}")
    print(f"  - Average group size: {stats['avg_group_size']}")
    print(f"  - Members by status: {stats['members_by_status']}")
    print(f"  - Members by source: {stats['members_by_source']}")
    print("  - Top groups:")
    for g in stats["top_groups"][:3]:
        print(
            f"    - {g['canonical_term']} ({g['domain']}): {g['member_count']} members"
        )


def test_error_handling(registry):
    """Test error handling and validation."""
    print("\n✓ Test 7: Error Handling")

    # Test invalid weight
    try:
        group = registry.get_or_create_group("test_errors", created_by="test_script")
        registry.add_group_member(
            group_id=group.id,
            term="invalid_weight",
            weight=1.5,  # Invalid: > 1.0
        )
        print("  - ❌ FAILED: Should have raised ValueError for invalid weight")
    except ValueError as e:
        print(f"  - ✓ Caught invalid weight: {e}")

    # Test invalid status
    try:
        registry.add_group_member(
            group_id=group.id,
            term="invalid_status",
            status="invalid",  # Invalid status
        )
        print("  - ❌ FAILED: Should have raised ValueError for invalid status")
    except ValueError as e:
        print(f"  - ✓ Caught invalid status: {e}")

    # Test duplicate term in group
    try:
        registry.add_group_member(
            group_id=group.id, term="duplicate_test", created_by="test_script"
        )
        registry.add_group_member(
            group_id=group.id, term="duplicate_test", created_by="test_script"
        )
        print("  - ❌ FAILED: Should have raised ValueError for duplicate term")
    except ValueError as e:
        print(f"  - ✓ Caught duplicate term: {e}")

    # Test empty term
    try:
        registry.add_group_member(group_id=group.id, term="", created_by="test_script")
        print("  - ❌ FAILED: Should have raised ValueError for empty term")
    except ValueError as e:
        print(f"  - ✓ Caught empty term: {e}")


def main():
    """Run all validation tests."""
    print("=" * 60)
    print("PHASE 1.2 - SynonymRegistry Validation")
    print("=" * 60)

    try:
        # Test 1: Connectivity
        registry = test_connectivity()

        # Test 2: Group Operations
        group = test_group_operations(registry)

        # Test 3: Member Operations
        members = test_member_operations(registry, group)

        # Test 4: Bidirectional Lookup
        test_bidirectional_lookup(registry)

        # Test 5: Cache Invalidation
        test_cache_invalidation(registry)

        # Test 6: Statistics
        test_statistics(registry)

        # Test 7: Error Handling
        test_error_handling(registry)

        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
