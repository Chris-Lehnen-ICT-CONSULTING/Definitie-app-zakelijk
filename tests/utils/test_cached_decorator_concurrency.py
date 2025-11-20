"""
Concurrency tests for @cached decorator race condition fix.

Tests verify that function-level lock with double-check pattern prevents
duplicate execution when multiple threads request the same cached value.

Background:
- Issue: RuleCache.load_all_rules() executed 4x during startup
- Root cause: No locking in @cached decorator
- Solution: Function-level lock + double-check pattern
- Expected: Only 1 execution regardless of concurrent requests
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from utils.cache import cached, clear_cache, configure_cache


@pytest.fixture(autouse=True)
def _clean_cache():
    """
    Auto-cleanup cache before/after each test to prevent test pollution.

    Resets global cache to default configuration and clears all cached data.
    This prevents comprehensive cache tests from polluting concurrency tests.
    """
    # Reset to default cache configuration
    configure_cache(enable_cache=True, cache_dir="cache", default_ttl=3600)
    clear_cache()  # Clean before test
    yield
    clear_cache()  # Clean after test


def test_no_duplicate_execution_same_key():
    """
    Verify only 1 execution when 4 threads request same cached value.

    This simulates the toetsregel loading scenario:
    - Thread 1-4: load_all_rules(regels_dir="/same/path")
    - All threads want same cache key
    - Expected: Function executes exactly ONCE
    - Expected: All threads receive same result
    """
    execution_count = 0
    execution_lock = threading.Lock()

    @cached(ttl=10)
    def expensive_func(arg):
        nonlocal execution_count
        with execution_lock:
            execution_count += 1
        time.sleep(0.05)  # Simulate expensive operation (50ms)
        return f"result_{arg}"

    # 4 threads, same key (like toetsregel loading)
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(expensive_func, "same") for _ in range(4)]
        results = [f.result() for f in futures]

    # Assert: Only 1 execution
    assert execution_count == 1, f"Expected 1 execution, got {execution_count}"

    # Assert: All results identical
    assert all(r == "result_same" for r in results), "Results should be identical"


def test_parallel_execution_different_keys():
    """
    Verify parallel execution when threads request different cached values.

    This tests that function-level lock doesn't over-serialize:
    - Thread 1: expensive_func("key1")
    - Thread 2: expensive_func("key2")
    - Expected: Both execute (different keys)
    - Note: Function-level lock serializes these, which is acceptable
    """
    execution_count = 0
    execution_lock = threading.Lock()
    execution_log = []

    @cached(ttl=10)
    def expensive_func(arg):
        nonlocal execution_count
        with execution_lock:
            execution_count += 1
            execution_log.append(arg)
        time.sleep(0.02)  # Simulate work
        return f"result_{arg}"

    # 2 threads, different keys
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(expensive_func, "key1"),
            executor.submit(expensive_func, "key2"),
        ]
        results = [f.result() for f in futures]

    # Assert: Both executed (different keys)
    assert execution_count == 2, f"Expected 2 executions, got {execution_count}"
    assert set(execution_log) == {"key1", "key2"}

    # Assert: Results differ
    assert "result_key1" in results
    assert "result_key2" in results


def test_cache_hit_after_first_execution():
    """
    Verify subsequent calls hit cache without re-execution.

    Scenario:
    1. Thread 1 executes and caches result
    2. Thread 2-4 request same value
    3. Expected: Thread 2-4 hit cache (no execution)
    """
    execution_count = 0

    @cached(ttl=10)
    def expensive_func(arg):
        nonlocal execution_count
        execution_count += 1
        return f"result_{arg}"

    # First call: should execute
    result1 = expensive_func("test")
    assert execution_count == 1

    # Subsequent calls: should hit cache
    result2 = expensive_func("test")
    result3 = expensive_func("test")
    assert execution_count == 1, "Should not re-execute for cached value"
    assert result1 == result2 == result3


def test_exception_handling():
    """
    Verify exceptions don't pollute cache.

    Expected behavior:
    - Exception raised: NOT cached
    - Subsequent call: Re-executes (no cached exception)
    - Success result: Cached normally
    """
    call_count = 0

    @cached(ttl=10)
    def failing_func(should_fail: bool):
        nonlocal call_count
        call_count += 1
        if should_fail:
            msg = "Intentional failure"
            raise ValueError(msg)
        return "success"

    # First call: raises exception
    with pytest.raises(ValueError, match="Intentional failure"):
        failing_func(True)
    assert call_count == 1

    # Second call with same arg: should retry (exception not cached)
    with pytest.raises(ValueError, match="Intentional failure"):
        failing_func(True)
    assert call_count == 2, "Should retry after exception"

    # Call with different arg: should succeed and cache
    result = failing_func(False)
    assert result == "success"
    assert call_count == 3

    # Subsequent success call: should hit cache
    result2 = failing_func(False)
    assert result2 == "success"
    assert call_count == 3, "Should hit cache for successful result"


def test_double_check_prevents_race_condition():
    """
    Verify double-check pattern prevents race condition.

    Scenario (without double-check):
    1. Thread 1: Cache miss → Acquires lock → Executes
    2. Thread 2: Cache miss (reads before Thread 1 writes) → Waits for lock
    3. Thread 1: Writes cache → Releases lock
    4. Thread 2: Acquires lock → Executes AGAIN (RACE CONDITION)

    With double-check:
    - Thread 2 checks cache AFTER acquiring lock
    - Thread 2 sees Thread 1's result → Returns cached value
    - Thread 2 does NOT execute
    """
    execution_count = 0
    execution_times = []
    execution_lock = threading.Lock()

    @cached(ttl=10)
    def expensive_func(arg):
        nonlocal execution_count
        with execution_lock:
            execution_count += 1
            execution_times.append(time.time())
        time.sleep(0.1)  # Long operation to amplify race window
        return f"result_{arg}"

    # Launch 2 threads with small delay to amplify race condition
    def thread1():
        return expensive_func("test")

    def thread2():
        time.sleep(0.01)  # Slight delay to ensure Thread 1 enters first
        return expensive_func("test")

    with ThreadPoolExecutor(max_workers=2) as executor:
        future1 = executor.submit(thread1)
        future2 = executor.submit(thread2)
        result1 = future1.result()
        result2 = future2.result()

    # Assert: Only 1 execution despite race window
    assert (
        execution_count == 1
    ), f"Double-check failed: got {execution_count} executions"
    assert result1 == result2 == "result_test"


def test_high_concurrency_stress_test():
    """
    Stress test: 20 concurrent threads requesting same cached value.

    This simulates worst-case startup scenario with many workers.
    Expected: Only 1 execution, all threads receive result.
    """
    execution_count = 0
    execution_lock = threading.Lock()

    @cached(ttl=10)
    def expensive_func(arg):
        nonlocal execution_count
        with execution_lock:
            execution_count += 1
        time.sleep(0.05)  # Simulate expense
        return f"result_{arg}"

    # 20 threads, same key
    num_threads = 20
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [
            executor.submit(expensive_func, "stress") for _ in range(num_threads)
        ]
        results = [f.result() for f in futures]

    # Assert: Only 1 execution
    assert (
        execution_count == 1
    ), f"Stress test failed: {execution_count} executions for {num_threads} threads"

    # Assert: All results identical
    assert all(r == "result_stress" for r in results)
    assert len(results) == num_threads


def test_mixed_concurrency_pattern():
    """
    Test mixed scenario: Multiple keys with concurrent requests per key.

    Scenario:
    - 2 threads request key="A"
    - 2 threads request key="B"
    - Expected: 2 executions total (1 per key)
    """
    execution_count = 0
    execution_lock = threading.Lock()
    execution_log = []

    @cached(ttl=10)
    def expensive_func(arg):
        nonlocal execution_count
        with execution_lock:
            execution_count += 1
            execution_log.append(arg)
        time.sleep(0.03)
        return f"result_{arg}"

    # 4 threads: 2x key_a, 2x key_b
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(expensive_func, "key_a"),
            executor.submit(expensive_func, "key_a"),
            executor.submit(expensive_func, "key_b"),
            executor.submit(expensive_func, "key_b"),
        ]
        results = [f.result() for f in futures]

    # Assert: 2 executions (1 per unique key)
    assert execution_count == 2, f"Expected 2 executions, got {execution_count}"

    # Assert: Both keys executed
    assert set(execution_log) == {"key_a", "key_b"}

    # Assert: Results correct
    assert results.count("result_key_a") == 2
    assert results.count("result_key_b") == 2
