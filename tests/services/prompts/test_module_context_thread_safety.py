"""
Thread-safety tests for ModuleContext.shared_state.

DEF-207: Ensures that concurrent access to shared_state from multiple threads
does not cause data corruption or race conditions.

These tests verify the fix for the thread-safety issue in ModuleContext where
parallel module execution via ThreadPoolExecutor could corrupt shared_state.
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import pytest

from services.definition_generator_config import UnifiedGeneratorConfig
from services.definition_generator_context import ContextSource, EnrichedContext
from services.prompts.modules.base_module import ModuleContext


def _make_context(shared_state: dict[str, Any] | None = None) -> ModuleContext:
    """Create a ModuleContext for testing."""
    enriched = EnrichedContext(
        base_context={
            "organisatorische_context": ["OM"],
            "juridische_context": ["Strafrecht"],
        },
        sources=[ContextSource(source_type="test", confidence=1.0, content="test")],
        expanded_terms={},
        confidence_scores={"test": 1.0},
        metadata={},
    )
    return ModuleContext(
        begrip="test",
        enriched_context=enriched,
        config=UnifiedGeneratorConfig(),
        shared_state=shared_state or {},
    )


class TestModuleContextThreadSafety:
    """Thread-safety tests for ModuleContext shared state operations."""

    def test_concurrent_writers_no_data_loss(self):
        """
        Multiple threads writing to different keys should not lose data.

        Each writer writes to its own key, then we verify all data is present.
        """
        context = _make_context()
        num_threads = 10
        writes_per_thread = 100
        errors: list[str] = []

        def writer(thread_id: int) -> None:
            for i in range(writes_per_thread):
                key = f"thread_{thread_id}_item_{i}"
                value = {"thread": thread_id, "iteration": i}
                context.set_shared(key, value)

        # Run all writers in parallel
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(writer, i) for i in range(num_threads)]
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    errors.append(str(e))

        # Verify no errors occurred
        assert not errors, f"Errors during concurrent writes: {errors}"

        # Verify all data was written
        snapshot = context.get_shared_snapshot()
        expected_keys = num_threads * writes_per_thread
        assert (
            len(snapshot) == expected_keys
        ), f"Expected {expected_keys} keys, got {len(snapshot)}"

        # Verify data integrity
        for thread_id in range(num_threads):
            for i in range(writes_per_thread):
                key = f"thread_{thread_id}_item_{i}"
                value = context.get_shared(key)
                assert value is not None, f"Key {key} not found"
                assert value["thread"] == thread_id
                assert value["iteration"] == i

    def test_concurrent_readers_and_writers(self):
        """
        Readers should never see corrupted data while writers are active.

        Writers continuously update a counter, readers verify counter is
        always a valid integer (not corrupted mid-write).
        """
        context = _make_context()
        context.set_shared("counter", 0)

        num_writers = 4
        num_readers = 8
        iterations = 200
        corruption_detected: list[str] = []
        stop_event = threading.Event()

        def writer(writer_id: int) -> None:
            for i in range(iterations):
                if stop_event.is_set():
                    break
                # Atomically increment counter
                current = context.get_shared("counter", 0)
                context.set_shared("counter", current + 1)
                context.set_shared(f"writer_{writer_id}_last", i)

        def reader() -> None:
            while not stop_event.is_set():
                value = context.get_shared("counter")
                if value is not None and not isinstance(value, int):
                    corruption_detected.append(f"Counter corrupted: {value!r}")
                    stop_event.set()
                time.sleep(0.0001)  # Small delay to not starve writers

        # Start readers first
        reader_threads = []
        for _ in range(num_readers):
            t = threading.Thread(target=reader, daemon=True)
            t.start()
            reader_threads.append(t)

        # Run writers
        with ThreadPoolExecutor(max_workers=num_writers) as executor:
            futures = [executor.submit(writer, i) for i in range(num_writers)]
            for future in as_completed(futures):
                future.result()

        # Stop readers
        stop_event.set()
        for t in reader_threads:
            t.join(timeout=1.0)

        assert not corruption_detected, f"Data corruption: {corruption_detected}"

    def test_get_or_set_shared_atomic(self):
        """
        get_or_set_shared should be atomic - factory called exactly once.

        Multiple threads racing to set the same key should result in
        exactly one factory call and all threads seeing the same value.
        """
        context = _make_context()
        factory_calls = []
        factory_lock = threading.Lock()

        def factory() -> dict[str, Any]:
            with factory_lock:
                call_id = len(factory_calls)
                factory_calls.append(call_id)
            # Simulate expensive computation
            time.sleep(0.01)
            return {"created_by": call_id}

        results: list[dict[str, Any]] = []
        results_lock = threading.Lock()

        def get_value() -> None:
            value = context.get_or_set_shared("expensive_key", factory=factory)
            with results_lock:
                results.append(value)

        # Launch many threads simultaneously
        threads = [threading.Thread(target=get_value) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Factory should be called exactly once
        assert (
            len(factory_calls) == 1
        ), f"Factory called {len(factory_calls)} times, expected 1"

        # All results should be identical
        first_result = results[0]
        for result in results:
            assert result == first_result, f"Inconsistent result: {result}"

    def test_get_or_set_shared_factory_exception(self):
        """
        If factory() raises an exception, the key should NOT be set.

        This ensures failed factory calls don't pollute shared_state
        with None or partial values.
        """
        context = _make_context()

        def failing_factory() -> dict[str, Any]:
            raise ValueError("Factory failed intentionally")

        # Factory exception should propagate
        with pytest.raises(ValueError, match="Factory failed intentionally"):
            context.get_or_set_shared("key", factory=failing_factory)

        # Key should NOT exist after failed factory
        assert (
            context.get_shared("key") is None
        ), "Key should not exist after factory exception"
        assert (
            "key" not in context.get_shared_snapshot()
        ), "Key should not be in snapshot"

    def test_update_shared_atomic(self):
        """
        update_shared should apply all updates atomically.

        A reader should never see a partial update state where key_a and key_b
        have different iteration numbers.
        """
        context = _make_context()
        # Initialize with iteration 0
        context.update_shared({"key_a": "v_0_a", "key_b": "v_0_b"})

        partial_states_detected: list[dict[str, str]] = []
        stop_event = threading.Event()
        updater_started = threading.Event()

        def updater() -> None:
            updater_started.set()
            for i in range(1, 101):  # Start from 1, 0 is initial
                if stop_event.is_set():
                    break
                # Update both keys atomically
                context.update_shared(
                    {
                        "key_a": f"v_{i}_a",
                        "key_b": f"v_{i}_b",
                    }
                )

        def checker() -> None:
            # Wait for updater to start
            updater_started.wait(timeout=1.0)
            while not stop_event.is_set():
                snapshot = context.get_shared_snapshot()
                a = snapshot.get("key_a", "")
                b = snapshot.get("key_b", "")
                # Extract iteration numbers from "v_{num}_a" pattern
                try:
                    parts_a = a.split("_")
                    parts_b = b.split("_")
                    if len(parts_a) >= 2 and len(parts_b) >= 2:
                        num_a = parts_a[1]
                        num_b = parts_b[1]
                        if num_a != num_b:
                            partial_states_detected.append({"a": a, "b": b})
                            stop_event.set()
                except (IndexError, ValueError):
                    pass
                time.sleep(0.00001)

        # Start checker
        checker_thread = threading.Thread(target=checker, daemon=True)
        checker_thread.start()

        # Run updater
        updater()
        stop_event.set()
        checker_thread.join(timeout=1.0)

        assert (
            not partial_states_detected
        ), f"Partial state detected: {partial_states_detected}"

    def test_same_key_concurrent_overwrites(self):
        """
        Multiple threads overwriting same key should not corrupt the dict.

        Final value should be one of the written values, not corrupted.
        """
        context = _make_context()
        num_threads = 10
        iterations = 500

        def writer(thread_id: int) -> None:
            for i in range(iterations):
                # Write complex object to increase chance of corruption
                context.set_shared(
                    "shared_key",
                    {
                        "thread": thread_id,
                        "iteration": i,
                        "data": list(range(50)),
                    },
                )

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(writer, i) for i in range(num_threads)]
            for future in as_completed(futures):
                future.result()

        # Final value should be valid
        final = context.get_shared("shared_key")
        assert final is not None
        assert "thread" in final
        assert "iteration" in final
        assert "data" in final
        assert final["data"] == list(range(50))

    def test_reentrant_lock_allows_nested_calls(self):
        """
        RLock should allow same thread to acquire lock multiple times.

        This is important for get_or_set_shared which may call get/set internally.
        """
        context = _make_context()

        # Simulate nested lock acquisition
        def nested_operation() -> None:
            with context._lock:  # First acquisition
                context.set_shared("outer", "value")
                with context._lock:  # Second acquisition (same thread)
                    context.set_shared("inner", "value")
                    # get_or_set_shared internally acquires lock again
                    result = context.get_or_set_shared("nested", default="created")
                    assert result == "created"

        # Should not deadlock
        nested_operation()
        assert context.get_shared("outer") == "value"
        assert context.get_shared("inner") == "value"
        assert context.get_shared("nested") == "created"

    def test_snapshot_isolation(self):
        """
        get_shared_snapshot returns a copy that is isolated from modifications.
        """
        context = _make_context()
        context.set_shared("key1", "value1")

        snapshot = context.get_shared_snapshot()

        # Modify original
        context.set_shared("key1", "modified")
        context.set_shared("key2", "value2")

        # Snapshot should be unchanged
        assert snapshot["key1"] == "value1"
        assert "key2" not in snapshot

    def test_default_shared_state_factory(self):
        """
        Each ModuleContext should get its own shared_state dict by default.
        """
        context1 = _make_context()
        context2 = _make_context()

        context1.set_shared("key", "value1")
        context2.set_shared("key", "value2")

        assert context1.get_shared("key") == "value1"
        assert context2.get_shared("key") == "value2"


class TestModuleContextPerformance:
    """Performance benchmarks for thread-safe operations."""

    def test_set_shared_performance(self):
        """
        Benchmark set_shared performance.

        Note: Lock overhead is expected - the goal is to ensure it's not
        catastrophically slow (>10x slower), not to match raw dict speed.
        In real usage, modules do ~10-50 shared state operations per prompt,
        so even 500% overhead adds < 1ms total.
        """
        num_operations = 10000
        context = _make_context()
        raw_dict: dict[str, int] = {}

        # Benchmark raw dict
        start = time.perf_counter()
        for i in range(num_operations):
            raw_dict[f"key_{i}"] = i
        raw_time = time.perf_counter() - start

        # Benchmark thread-safe set_shared
        start = time.perf_counter()
        for i in range(num_operations):
            context.set_shared(f"key_{i}", i)
        safe_time = time.perf_counter() - start

        # Calculate overhead
        overhead_factor = safe_time / raw_time if raw_time > 0 else 1

        # Log for visibility
        print(f"\nOperations: {num_operations}")
        print(f"Raw dict: {raw_time*1000:.2f}ms")
        print(f"Thread-safe: {safe_time*1000:.2f}ms")
        print(f"Overhead factor: {overhead_factor:.1f}x")

        # Assert reasonable overhead (< 10x slower is acceptable for thread-safety)
        assert overhead_factor < 10, f"Excessive overhead: {overhead_factor:.1f}x"

        # Assert absolute time is reasonable (< 50ms for 10k operations)
        assert (
            safe_time < 0.05
        ), f"Too slow: {safe_time*1000:.2f}ms for {num_operations} ops"

    def test_get_shared_performance(self):
        """
        Benchmark get_shared performance.
        """
        num_operations = 10000
        context = _make_context()
        for i in range(100):
            context.set_shared(f"key_{i}", i)

        raw_dict = context.shared_state.copy()

        # Benchmark raw dict
        start = time.perf_counter()
        for i in range(num_operations):
            _ = raw_dict.get(f"key_{i % 100}")
        raw_time = time.perf_counter() - start

        # Benchmark thread-safe get_shared
        start = time.perf_counter()
        for i in range(num_operations):
            _ = context.get_shared(f"key_{i % 100}")
        safe_time = time.perf_counter() - start

        overhead_factor = safe_time / raw_time if raw_time > 0 else 1

        print(f"\nOperations: {num_operations}")
        print(f"Raw dict: {raw_time*1000:.2f}ms")
        print(f"Thread-safe: {safe_time*1000:.2f}ms")
        print(f"Overhead factor: {overhead_factor:.1f}x")

        assert overhead_factor < 10, f"Excessive overhead: {overhead_factor:.1f}x"
        assert (
            safe_time < 0.05
        ), f"Too slow: {safe_time*1000:.2f}ms for {num_operations} ops"

    def test_concurrent_performance(self):
        """
        Measure performance under actual concurrent load.

        This simulates the PromptOrchestrator's parallel module execution.
        """
        context = _make_context()
        num_threads = 4
        operations_per_thread = 1000

        def mixed_operations(thread_id: int) -> float:
            start = time.perf_counter()
            for i in range(operations_per_thread):
                context.set_shared(f"t{thread_id}_k{i}", i)
                _ = context.get_shared(f"t{thread_id}_k{i}")
                if i % 10 == 0:
                    _ = context.get_shared_snapshot()
            return time.perf_counter() - start

        start = time.perf_counter()
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(mixed_operations, i) for i in range(num_threads)]
            thread_times = [f.result() for f in as_completed(futures)]
        total_time = time.perf_counter() - start

        total_ops = num_threads * operations_per_thread * 2  # set + get per iteration
        ops_per_sec = total_ops / total_time

        print(f"\nConcurrent performance ({num_threads} threads):")
        print(f"Total operations: {total_ops}")
        print(f"Total time: {total_time*1000:.2f}ms")
        print(f"Operations/sec: {ops_per_sec:,.0f}")
        print(f"Thread times: {[f'{t*1000:.2f}ms' for t in thread_times]}")

        # Reasonable threshold for 4 threads doing 4000 ops each
        assert ops_per_sec > 10000, f"Too slow: {ops_per_sec:.0f} ops/sec"
