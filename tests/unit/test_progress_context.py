"""Comprehensive test suite for progress_context.py.

Tests the progress tracking context manager and direct setter function,
including happy path, soft-fail behavior, exception handling, logging,
and concurrent operations.

Created for DEF-198: Fix Layer Violation in progress_context.py
Addresses silent failures gap analysis requirements.

TDD: These tests were written BEFORE the implementation changes.
"""

from __future__ import annotations

import logging
import sys
import threading
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, Mock, create_autospec, patch

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator


# Note: Import path will change after file move
# Current: from services.progress_context import operation_progress, set_progress
# After: from ui.helpers.progress_context import operation_progress, set_progress


def get_progress_functions():
    """Import progress functions from current location (handles move)."""
    try:
        from ui.helpers.progress_context import operation_progress, set_progress

        return operation_progress, set_progress
    except ImportError:
        from services.progress_context import operation_progress, set_progress

        return operation_progress, set_progress


def get_module_path():
    """Get the module path for patching based on current file location."""
    try:
        import ui.helpers.progress_context

        return "ui.helpers.progress_context"
    except ImportError:
        return "services.progress_context"


@pytest.fixture
def mock_session_state_module():
    """Create a mock ui.session_state module with SessionStateManager.

    This fixture properly mocks the module that progress_context imports.
    """
    mock_module = MagicMock()
    mock_manager = MagicMock()
    mock_module.SessionStateManager = mock_manager

    with patch.dict(sys.modules, {"ui.session_state": mock_module}):
        yield mock_manager


class TestOperationProgressHappyPath:
    """Test normal operation when SessionStateManager is available."""

    def test_context_manager_sets_and_clears_flag(self, mock_session_state_module):
        """Test that operation_progress sets flag to True on enter, False on exit.

        Verifies:
        - SessionStateManager.set_value called with (operation_name, True) on enter
        - SessionStateManager.set_value called with (operation_name, False) on exit
        - Total of 2 calls to set_value
        """
        operation_progress, _ = get_progress_functions()
        mock_state = mock_session_state_module

        with operation_progress("test_operation"):
            pass

        assert mock_state.set_value.call_count == 2
        mock_state.set_value.assert_any_call("test_operation", True)
        mock_state.set_value.assert_any_call("test_operation", False)

    def test_context_manager_with_different_operation_names(
        self, mock_session_state_module
    ):
        """Test that operation name is correctly passed to session state.

        Verifies:
        - Different operation names result in different session state keys
        - Operation names are passed as-is (no transformation)
        """
        operation_progress, _ = get_progress_functions()
        mock_state = mock_session_state_module

        with operation_progress("saving_to_database"):
            pass

        calls = mock_state.set_value.call_args_list
        assert calls[0][0][0] == "saving_to_database"
        assert calls[1][0][0] == "saving_to_database"

    def test_multiple_sequential_operations(self, mock_session_state_module):
        """Test multiple sequential context manager invocations.

        Verifies:
        - Multiple operations don't interfere with each other
        - Each operation gets its own enter/exit cycle
        - Call count accumulates correctly
        """
        operation_progress, _ = get_progress_functions()
        mock_state = mock_session_state_module

        with operation_progress("operation_1"):
            pass
        with operation_progress("operation_2"):
            pass

        assert mock_state.set_value.call_count == 4  # 2 ops x 2 calls each


class TestOperationProgressSoftFail:
    """Test soft-fail behavior when SessionStateManager unavailable."""

    def test_import_failure_does_not_raise(self):
        """Test that import failure is caught silently and doesn't raise.

        Verifies:
        - When ui.session_state is not available, ImportError is caught
        - Context manager still yields control to user code
        """
        operation_progress, _ = get_progress_functions()

        # Remove any cached module to force import failure
        # Should not raise - soft-fail behavior
        with (
            patch.dict(sys.modules, {"ui.session_state": None}),
            operation_progress("test_operation"),
        ):
            pass  # User code executes

    def test_set_value_exception_does_not_raise(self, mock_session_state_module):
        """Test that exception in set_value is caught silently.

        Verifies:
        - Runtime exception in SessionStateManager.set_value is caught
        - Exception doesn't propagate to user code
        - Context manager completes normally
        """
        operation_progress, _ = get_progress_functions()
        mock_state = mock_session_state_module
        mock_state.set_value.side_effect = RuntimeError("Session state error")

        # Should not raise - soft-fail behavior
        with operation_progress("test_operation"):
            pass

    def test_user_code_executes_despite_import_failure(self):
        """Test that user code runs even if session state unavailable.

        Verifies:
        - Soft-fail doesn't skip user code execution
        - Side effects in user code still occur
        """
        operation_progress, _ = get_progress_functions()

        with patch.dict(sys.modules, {"ui.session_state": None}):
            side_effect_tracker = []
            with operation_progress("test_operation"):
                side_effect_tracker.append("executed")

            assert side_effect_tracker == ["executed"]


class TestOperationProgressExceptionHandling:
    """Test exception handling and cleanup behavior."""

    def test_cleanup_happens_on_user_exception(self, mock_session_state_module):
        """Test that finally block executes even when user code raises.

        Verifies:
        - set_value(operation, False) is called in finally block
        - Cleanup happens before exception propagates
        """
        operation_progress, _ = get_progress_functions()
        mock_state = mock_session_state_module

        with (
            pytest.raises(ValueError, match="User code error"),
            operation_progress("test_operation"),
        ):
            raise ValueError("User code error")

        # Should have called: set_value(True) + set_value(False)
        assert mock_state.set_value.call_count == 2
        mock_state.set_value.assert_any_call("test_operation", False)

    def test_user_exception_propagates_after_cleanup(self, mock_session_state_module):
        """Test that user exceptions are not swallowed by context manager.

        Verifies:
        - Original exception type is preserved
        - Exception message is preserved
        """
        operation_progress, _ = get_progress_functions()

        with (
            pytest.raises(RuntimeError, match="Custom error"),
            operation_progress("test_operation"),
        ):
            raise RuntimeError("Custom error")

    def test_cleanup_with_multiple_exception_types(self, mock_session_state_module):
        """Test cleanup happens correctly with various exception types.

        Verifies:
        - ValueError, RuntimeError, KeyError all trigger cleanup
        - Cleanup is exception-type agnostic
        """
        operation_progress, _ = get_progress_functions()
        mock_state = mock_session_state_module

        exception_types = [ValueError, RuntimeError, KeyError]

        for exc_type in exception_types:
            mock_state.reset_mock()
            with (
                pytest.raises(exc_type, match="Test error"),
                operation_progress("test_operation"),
            ):
                raise exc_type("Test error")

            # Verify cleanup happened
            mock_state.set_value.assert_any_call("test_operation", False)


class TestSetProgressFunction:
    """Test the direct set_progress() function."""

    def test_set_progress_true(self, mock_session_state_module):
        """Test set_progress with active=True.

        Verifies:
        - set_value called with correct operation name
        - set_value called with True value
        """
        _, set_progress = get_progress_functions()
        mock_state = mock_session_state_module

        set_progress("my_operation", True)

        mock_state.set_value.assert_called_once_with("my_operation", True)

    def test_set_progress_false(self, mock_session_state_module):
        """Test set_progress with active=False.

        Verifies:
        - set_value called with False value
        """
        _, set_progress = get_progress_functions()
        mock_state = mock_session_state_module

        set_progress("my_operation", False)

        mock_state.set_value.assert_called_once_with("my_operation", False)

    def test_set_progress_soft_fail(self):
        """Test set_progress handles import failure silently.

        Verifies:
        - Import failure doesn't raise exception
        - Function completes normally
        """
        _, set_progress = get_progress_functions()

        with patch.dict(sys.modules, {"ui.session_state": None}):
            # Should not raise
            set_progress("my_operation", True)


class TestProgressContextLogging:
    """Test logging behavior for soft-fail scenarios.

    Note: These tests require logging to be added to progress_context.py.
    They will FAIL initially (TDD red phase) until logging is implemented.
    """

    def test_import_failure_logs_debug_message(self, caplog):
        """Test that import failures are logged at DEBUG level.

        Verifies:
        - DEBUG log emitted when import fails
        - Log indicates progress tracking unavailable
        """
        operation_progress, _ = get_progress_functions()

        with (
            patch.dict(sys.modules, {"ui.session_state": None}),
            caplog.at_level(logging.DEBUG),
            operation_progress("test_operation"),
        ):
            pass

        # Check for expected log message pattern
        debug_logs = [r for r in caplog.records if r.levelno == logging.DEBUG]
        assert any(
            "unavailable" in r.message.lower() or "test_operation" in r.message
            for r in debug_logs
        ), f"Expected debug log about unavailable state, got: {caplog.text}"

    def test_no_error_logging_on_expected_failures(self, caplog):
        """Test that expected failures (ImportError) don't log at ERROR level.

        Verifies:
        - ImportError is expected and logged at DEBUG, not ERROR
        - ERROR logs reserved for unexpected failures
        """
        operation_progress, _ = get_progress_functions()

        with (
            patch.dict(sys.modules, {"ui.session_state": None}),
            caplog.at_level(logging.DEBUG),
            operation_progress("test_operation"),
        ):
            pass

        # Should NOT have ERROR level logs for expected import failures
        error_logs = [r for r in caplog.records if r.levelno >= logging.ERROR]
        assert (
            len(error_logs) == 0
        ), f"Unexpected ERROR logs: {[r.message for r in error_logs]}"

    def test_no_logging_on_success(self, caplog, mock_session_state_module):
        """Test that successful operations don't generate debug logs.

        Verifies:
        - Happy path is silent (minimal logs)
        - Logs only appear on soft-fail scenarios
        """
        operation_progress, _ = get_progress_functions()

        with caplog.at_level(logging.DEBUG), operation_progress("test_operation"):
            pass

        # Should have no "unavailable" logs for successful operations
        assert "unavailable" not in caplog.text.lower()


class TestProgressContextConcurrency:
    """Test thread safety and concurrent operations."""

    def test_concurrent_different_operations(self, mock_session_state_module):
        """Test multiple threads with different operation names don't interfere.

        Verifies:
        - Thread A's operation doesn't affect Thread B's operation
        - All operations complete successfully
        """
        operation_progress, _ = get_progress_functions()
        mock_state = mock_session_state_module
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
        assert mock_state.set_value.call_count == 10

    def test_nested_context_managers(self, mock_session_state_module):
        """Test nested operation_progress calls.

        Verifies:
        - Outer context manager completes after inner
        - Both operations tracked independently
        """
        operation_progress, _ = get_progress_functions()
        mock_state = mock_session_state_module

        with (
            operation_progress("outer_operation"),
            operation_progress("inner_operation"),
        ):
            pass

        # Should have 2 ops x 2 calls = 4 total
        assert mock_state.set_value.call_count == 4


class TestProgressContextIntegration:
    """Integration tests that verify the full flow."""

    def test_progress_context_works_without_streamlit(self):
        """Test that progress context gracefully handles missing Streamlit.

        This is the primary use case - tests run without Streamlit.
        """
        operation_progress, _ = get_progress_functions()

        # Should work without raising any exceptions
        executed = False
        with operation_progress("test_operation"):
            executed = True

        assert executed

    def test_set_progress_works_without_streamlit(self):
        """Test that set_progress gracefully handles missing Streamlit."""
        _, set_progress = get_progress_functions()

        # Should not raise
        set_progress("test_operation", True)
        set_progress("test_operation", False)
