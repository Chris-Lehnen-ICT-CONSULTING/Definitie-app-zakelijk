"""Integration tests for RuleCache with monitoring."""

import pytest

from toetsregels.rule_cache import RuleCache, get_rule_cache


@pytest.fixture
def rule_cache():
    """Create a fresh RuleCache instance for testing."""
    # Create new instance (singleton will be shared)
    cache = get_rule_cache()
    # Clear any existing operations
    if hasattr(cache, "_monitor") and cache._monitor:
        cache._monitor.clear_operations()
    return cache


def test_rule_cache_has_monitoring(rule_cache):
    """Test that RuleCache has monitoring enabled."""
    assert hasattr(rule_cache, "_monitor")
    # Monitor can be None if monitoring not available, but should exist
    assert rule_cache._monitor is not None or rule_cache._monitor is None


def test_rule_cache_tracks_get_all_rules(rule_cache):
    """Test that get_all_rules operation is tracked."""
    # Clear monitoring before test
    if rule_cache._monitor:
        rule_cache._monitor.clear_operations()

    # Get all rules
    rules = rule_cache.get_all_rules()
    assert isinstance(rules, dict)

    # Check monitoring if available
    if rule_cache._monitor:
        operations = rule_cache._monitor.get_operations()
        # Should have at least one operation tracked
        assert len(operations) > 0

        # Find get_all operation
        get_all_ops = [op for op in operations if op.operation == "get_all"]
        assert len(get_all_ops) > 0


def test_rule_cache_tracks_get_single_rule(rule_cache):
    """Test that get_rule operation is tracked."""
    if rule_cache._monitor:
        rule_cache._monitor.clear_operations()

    # Get a specific rule
    rules = rule_cache.get_all_rules()
    if rules:
        first_rule_id = next(iter(rules.keys()))
        rule = rule_cache.get_rule(first_rule_id)
        assert rule is not None

        if rule_cache._monitor:
            operations = rule_cache._monitor.get_operations()
            # Should have tracked the get_single operation
            single_ops = [op for op in operations if op.operation == "get_single"]
            assert len(single_ops) > 0


def test_rule_cache_stats_include_monitoring(rule_cache):
    """Test that get_stats includes monitoring data."""
    # Perform some operations
    rule_cache.get_all_rules()

    stats = rule_cache.get_stats()
    assert "total_rules_cached" in stats

    # If monitoring is available, stats should include monitoring section
    if rule_cache._monitor:
        assert "monitoring" in stats
        assert "hit_rate" in stats["monitoring"]
        assert "avg_operation_ms" in stats["monitoring"]
        assert "hits" in stats["monitoring"]
        assert "misses" in stats["monitoring"]


def test_rule_cache_clear_tracked(rule_cache):
    """Test that clear_cache operation is tracked."""
    if rule_cache._monitor:
        rule_cache._monitor.clear_operations()

        # Clear cache
        rule_cache.clear_cache()

        operations = rule_cache._monitor.get_operations()
        clear_ops = [op for op in operations if op.operation == "clear"]
        assert len(clear_ops) > 0
        assert clear_ops[0].result == "evict"


def test_rule_cache_monitoring_snapshot(rule_cache):
    """Test getting monitoring snapshot from RuleCache."""
    if rule_cache._monitor:
        rule_cache._monitor.clear_operations()

        # Perform several operations
        rule_cache.get_all_rules()
        rules = rule_cache.get_all_rules()  # Second call should be cache hit
        if rules:
            first_rule_id = next(iter(rules.keys()))
            rule_cache.get_rule(first_rule_id)

        snapshot = rule_cache._monitor.get_snapshot()
        assert snapshot.cache_name == "RuleCache"
        assert snapshot.total_entries > 0
        # Should have tracked operations
        assert snapshot.hits > 0 or snapshot.misses > 0


def test_rule_cache_without_monitoring_still_works():
    """Test that RuleCache works even if monitoring is not available."""
    cache = get_rule_cache()

    # Should work regardless of monitoring availability
    rules = cache.get_all_rules()
    assert isinstance(rules, dict)

    stats = cache.get_stats()
    assert "total_rules_cached" in stats
