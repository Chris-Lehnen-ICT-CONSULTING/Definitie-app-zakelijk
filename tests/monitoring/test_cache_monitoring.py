"""Tests for cache monitoring."""

import time

import pytest

from src.monitoring.cache_monitoring import CacheMonitor, CacheOperation, CacheSnapshot


def test_cache_monitor_tracks_operations():
    """Test that cache monitor correctly tracks operations."""
    monitor = CacheMonitor("TestCache")

    with monitor.track_operation("get", "key1") as result:
        result["result"] = "hit"
        result["source"] = "memory"

    snapshot = monitor.get_snapshot()
    assert snapshot.hits == 1
    assert snapshot.misses == 0
    assert snapshot.hit_rate == 1.0
    assert snapshot.avg_operation_ms > 0
    assert snapshot.cache_name == "TestCache"


def test_cache_monitor_tracks_misses():
    """Test that cache monitor correctly tracks misses."""
    monitor = CacheMonitor("TestCache")

    with monitor.track_operation("get", "key1") as result:
        result["result"] = "miss"
        result["source"] = "disk"

    snapshot = monitor.get_snapshot()
    assert snapshot.hits == 0
    assert snapshot.misses == 1
    assert snapshot.hit_rate == 0.0


def test_cache_monitor_calculates_hit_rate():
    """Test hit rate calculation with mixed hits and misses."""
    monitor = CacheMonitor("TestCache")

    # 3 hits
    for i in range(3):
        with monitor.track_operation("get", f"key{i}") as result:
            result["result"] = "hit"

    # 1 miss
    with monitor.track_operation("get", "key4") as result:
        result["result"] = "miss"

    snapshot = monitor.get_snapshot()
    assert snapshot.hits == 3
    assert snapshot.misses == 1
    assert snapshot.hit_rate == 0.75  # 3/4


def test_cache_monitor_tracks_evictions():
    """Test that evictions are tracked correctly."""
    monitor = CacheMonitor("TestCache")

    with monitor.track_operation("clear", "all") as result:
        result["result"] = "evict"
        result["source"] = "all"

    snapshot = monitor.get_snapshot()
    assert snapshot.evictions == 1


def test_cache_monitor_disabled():
    """Test that disabled monitor doesn't track operations."""
    monitor = CacheMonitor("TestCache", enabled=False)

    with monitor.track_operation("get", "key1") as result:
        result["result"] = "hit"

    snapshot = monitor.get_snapshot()
    assert snapshot.hits == 0  # Nothing tracked
    assert snapshot.total_entries == 0


def test_cache_monitor_tracks_timing():
    """Test that operation timing is tracked."""
    monitor = CacheMonitor("TestCache")

    with monitor.track_operation("get", "key1") as result:
        time.sleep(0.01)  # 10ms
        result["result"] = "hit"

    snapshot = monitor.get_snapshot()
    # Should be at least 10ms
    assert snapshot.avg_operation_ms >= 10


def test_cache_monitor_tracks_multiple_operations():
    """Test tracking multiple different operations."""
    monitor = CacheMonitor("TestCache")

    # Get operations
    with monitor.track_operation("get", "key1") as result:
        result["result"] = "hit"

    with monitor.track_operation("get", "key2") as result:
        result["result"] = "miss"

    # Set operation
    with monitor.track_operation("set", "key3") as result:
        result["result"] = "store"

    operations = monitor.get_operations()
    assert len(operations) == 3
    assert operations[0].operation == "get"
    assert operations[2].operation == "set"


def test_cache_monitor_get_operations_with_limit():
    """Test getting limited number of recent operations."""
    monitor = CacheMonitor("TestCache")

    # Add 5 operations
    for i in range(5):
        with monitor.track_operation("get", f"key{i}") as result:
            result["result"] = "hit"

    # Get only last 3
    recent = monitor.get_operations(limit=3)
    assert len(recent) == 3
    assert recent[0].key == "key2"
    assert recent[2].key == "key4"


def test_cache_monitor_clear_operations():
    """Test clearing operation history."""
    monitor = CacheMonitor("TestCache")

    with monitor.track_operation("get", "key1") as result:
        result["result"] = "hit"

    assert len(monitor.get_operations()) == 1

    monitor.clear_operations()
    assert len(monitor.get_operations()) == 0


def test_cache_operation_dataclass():
    """Test CacheOperation dataclass creation."""
    op = CacheOperation(
        cache_name="TestCache",
        operation="get",
        timestamp=time.time(),
        duration_ms=5.0,
        result="hit",
        source="memory",
        key="test_key",
        size_bytes=1024,
    )

    assert op.cache_name == "TestCache"
    assert op.operation == "get"
    assert op.result == "hit"
    assert op.source == "memory"
    assert op.key == "test_key"
    assert op.size_bytes == 1024


def test_cache_snapshot_dataclass():
    """Test CacheSnapshot dataclass creation."""
    snapshot = CacheSnapshot(
        timestamp=time.time(),
        cache_name="TestCache",
        total_entries=100,
        memory_usage_bytes=1024000,
        hit_rate=0.85,
        avg_operation_ms=2.5,
        hits=85,
        misses=15,
        evictions=5,
    )

    assert snapshot.cache_name == "TestCache"
    assert snapshot.total_entries == 100
    assert snapshot.hit_rate == 0.85
    assert snapshot.hits == 85
    assert snapshot.misses == 15
    assert snapshot.evictions == 5


def test_cache_monitor_empty_snapshot():
    """Test snapshot when no operations have been tracked."""
    monitor = CacheMonitor("TestCache")

    snapshot = monitor.get_snapshot()
    assert snapshot.hits == 0
    assert snapshot.misses == 0
    assert snapshot.hit_rate == 0.0
    assert snapshot.avg_operation_ms == 0.0
    assert snapshot.total_entries == 0


def test_cache_monitor_logs_slow_operations(caplog):
    """Test that slow operations are logged."""
    import logging

    caplog.set_level(logging.WARNING)

    monitor = CacheMonitor("TestCache")

    with monitor.track_operation("get", "slow_key") as result:
        time.sleep(0.11)  # 110ms - over 100ms threshold
        result["result"] = "hit"

    # Check that warning was logged
    assert "Slow cache op" in caplog.text
    assert "TestCache.get" in caplog.text


def test_cache_monitor_stores_size_bytes():
    """Test that size_bytes is stored in operations."""
    monitor = CacheMonitor("TestCache")

    with monitor.track_operation("get", "key1") as result:
        result["result"] = "hit"
        result["size_bytes"] = 2048

    operations = monitor.get_operations()
    assert operations[0].size_bytes == 2048


def test_cache_monitor_handles_unknown_result():
    """Test handling of operations without explicit result."""
    monitor = CacheMonitor("TestCache")

    with monitor.track_operation("get", "key1"):
        # Don't set result
        pass

    operations = monitor.get_operations()
    assert operations[0].result == "unknown"


def test_cache_monitor_context_manager_exception():
    """Test that monitor handles exceptions in tracked code."""
    monitor = CacheMonitor("TestCache")

    msg = "Test exception"
    try:
        with monitor.track_operation("get", "key1") as result:
            result["result"] = "hit"
            raise ValueError(msg)
    except ValueError:
        pass  # Expected

    # Operation should still be tracked
    snapshot = monitor.get_snapshot()
    assert snapshot.hits == 1
