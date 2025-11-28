"""Comprehensive test suite for utils/progress_callback.py.

Tests the progress tracking callback system including:
- Callback registration and invocation
- Context manager behavior
- Soft-fail when no callback registered
- Exception handling and cleanup
- Concurrent operations

Created for DEF-198: Clean architecture fix for layer violation.
"""

from __future__ import annotations

import logging
import threading
from unittest.mock import MagicMock

import pytest

from utils.progress_callback import (
    notify_progress,
    operation_progress,
    register_progress_callback,
    unregister_progress_callback,
)


@pytest.fixture(autouse=True)
def reset_callback():
    """Ensure callback is unregistered before and after each test."""
    unregister_progress_callback()
    yield
    unregister_progress_callback()


@pytest.fixture
def mock_callback():
    """Create and register a mock callback."""
    callback = MagicMock()
    register_progress_callback(callback)
    return callback


class TestCallbackRegistration:
    """Test callback registration and unregistration."""

    def test_register_callback(self):
        """Test that callback can be registered."""
        callback = MagicMock()
        register_progress_callback(callback)

        notify_progress("test_op", True)
        callback.assert_called_once_with("test_op", True)

    def test_unregister_callback(self):
        """Test that callback can be unregistered."""
        callback = MagicMock()
        register_progress_callback(callback)
        unregister_progress_callback()

        notify_progress("test_op", True)
        callback.assert_not_called()

    def test_replace_callback(self):
        """Test that registering new callback replaces old one."""
        callback1 = MagicMock()
        callback2 = MagicMock()

        register_progress_callback(callback1)
        register_progress_callback(callback2)

        notify_progress("test_op", True)

        callback1.assert_not_called()
        callback2.assert_called_once()


class TestOperationProgressHappyPath:
    """Test normal operation when callback is registered."""

    def test_context_manager_sets_and_clears_flag(self, mock_callback):
        """Test that operation_progress sets flag to True on enter, False on exit."""
        with operation_progress("test_operation"):
            pass

        assert mock_callback.call_count == 2
        mock_callback.assert_any_call("test_operation", True)
        mock_callback.assert_any_call("test_operation", False)

    def test_context_manager_with_different_operation_names(self, mock_callback):
        """Test that operation name is correctly passed to callback."""
        with operation_progress("saving_to_database"):
            pass

        calls = mock_callback.call_args_list
        assert calls[0][0][0] == "saving_to_database"
        assert calls[1][0][0] == "saving_to_database"

    def test_multiple_sequential_operations(self, mock_callback):
        """Test multiple sequential context manager invocations."""
        with operation_progress("operation_1"):
            pass
        with operation_progress("operation_2"):
            pass

        assert mock_callback.call_count == 4  # 2 ops x 2 calls each


class TestOperationProgressSoftFail:
    """Test soft-fail behavior when no callback registered."""

    def test_no_callback_does_not_raise(self):
        """Test that missing callback doesn't raise exception."""
        # No callback registered - should not raise
        with operation_progress("test_operation"):
            pass

    def test_user_code_executes_without_callback(self):
        """Test that user code runs even without callback."""
        side_effect_tracker = []
        with operation_progress("test_operation"):
            side_effect_tracker.append("executed")

        assert side_effect_tracker == ["executed"]

    def test_notify_progress_without_callback(self):
        """Test notify_progress handles missing callback gracefully."""
        # Should not raise
        notify_progress("test_op", True)
        notify_progress("test_op", False)


class TestOperationProgressExceptionHandling:
    """Test exception handling and cleanup behavior."""

    def test_cleanup_happens_on_user_exception(self, mock_callback):
        """Test that finally block executes even when user code raises."""
        with (
            pytest.raises(ValueError, match="User code error"),
            operation_progress("test_operation"),
        ):
            raise ValueError("User code error")

        # Should have called: callback(True) + callback(False)
        assert mock_callback.call_count == 2
        mock_callback.assert_any_call("test_operation", False)

    def test_user_exception_propagates_after_cleanup(self, mock_callback):
        """Test that user exceptions are not swallowed by context manager."""
        with (
            pytest.raises(RuntimeError, match="Custom error"),
            operation_progress("test_operation"),
        ):
            raise RuntimeError("Custom error")

    def test_callback_exception_does_not_break_user_code(self):
        """Test that callback exception doesn't propagate to user code."""
        callback = MagicMock(side_effect=RuntimeError("Callback error"))
        register_progress_callback(callback)

        executed = False
        with operation_progress("test_operation"):
            executed = True

        assert executed  # User code should still run

    def test_cleanup_with_multiple_exception_types(self, mock_callback):
        """Test cleanup happens correctly with various exception types."""
        exception_types = [ValueError, RuntimeError, KeyError]

        for exc_type in exception_types:
            mock_callback.reset_mock()
            with (
                pytest.raises(exc_type, match="Test error"),
                operation_progress("test_operation"),
            ):
                raise exc_type("Test error")

            # Verify cleanup happened
            mock_callback.assert_any_call("test_operation", False)


class TestNotifyProgressFunction:
    """Test the direct notify_progress() function."""

    def test_notify_progress_true(self, mock_callback):
        """Test notify_progress with active=True."""
        notify_progress("my_operation", True)
        mock_callback.assert_called_once_with("my_operation", True)

    def test_notify_progress_false(self, mock_callback):
        """Test notify_progress with active=False."""
        notify_progress("my_operation", False)
        mock_callback.assert_called_once_with("my_operation", False)


class TestProgressCallbackLogging:
    """Test logging behavior for soft-fail scenarios."""

    def test_no_callback_logs_debug_message(self, caplog):
        """Test that missing callback logs at DEBUG level."""
        with caplog.at_level(logging.DEBUG):
            notify_progress("test_operation", True)

        debug_logs = [r for r in caplog.records if r.levelno == logging.DEBUG]
        assert any(
            "no callback" in r.message.lower() or "test_operation" in r.message
            for r in debug_logs
        ), f"Expected debug log about no callback, got: {caplog.text}"

    def test_callback_error_logs_warning(self, caplog):
        """Test that callback errors are logged at WARNING level."""
        callback = MagicMock(side_effect=RuntimeError("Callback error"))
        register_progress_callback(callback)

        with caplog.at_level(logging.WARNING):
            notify_progress("test_operation", True)

        warning_logs = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert len(warning_logs) >= 1, f"Expected WARNING log, got: {caplog.text}"

    def test_no_logging_on_success(self, caplog, mock_callback):
        """Test that successful operations don't generate warning/error logs."""
        with caplog.at_level(logging.DEBUG), operation_progress("test_operation"):
            pass

        # Should have no warning or error logs for successful operations
        warning_or_higher = [r for r in caplog.records if r.levelno >= logging.WARNING]
        assert len(warning_or_higher) == 0, f"Unexpected logs: {caplog.text}"


class TestProgressCallbackConcurrency:
    """Test thread safety and concurrent operations."""

    def test_concurrent_different_operations(self, mock_callback):
        """Test multiple threads with different operation names don't interfere."""
        results = []

        def operation(name):
            with operation_progress(name):
                results.append(name)

        threads = [
            threading.Thread(target=operation, args=(f"op_{i}",)) for i in range(5)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 5
        # 5 operations x 2 calls each (enter + exit)
        assert mock_callback.call_count == 10

    def test_nested_context_managers(self, mock_callback):
        """Test nested operation_progress calls."""
        with (
            operation_progress("outer_operation"),
            operation_progress("inner_operation"),
        ):
            pass

        # Should have 2 ops x 2 calls = 4 total
        assert mock_callback.call_count == 4


class TestProgressCallbackIntegration:
    """Integration tests that verify the full flow."""

    def test_progress_callback_works_without_registration(self):
        """Test that progress callback gracefully handles no registration."""
        executed = False
        with operation_progress("test_operation"):
            executed = True

        assert executed

    def test_full_flow_with_session_state_mock(self):
        """Test the full flow simulating SessionStateManager.set_value."""
        state = {}

        def mock_set_value(key, value):
            state[key] = value

        register_progress_callback(mock_set_value)

        assert "saving" not in state

        with operation_progress("saving"):
            assert state["saving"] is True

        assert state["saving"] is False
