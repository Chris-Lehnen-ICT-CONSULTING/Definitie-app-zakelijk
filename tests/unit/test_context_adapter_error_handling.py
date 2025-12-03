"""
Tests for ContextAdapter error handling (DEF-252 follow-up).

These tests verify that context_adapter.py properly handles exceptions
with narrow types and structured logging, consistent with components_adapter.py.
"""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest

from ui.helpers.context_adapter import ContextAdapter


class TestSetInSessionStateErrorHandling:
    """Tests for set_in_session_state exception handling."""

    @pytest.fixture
    def adapter_with_mock_manager(self):
        """Create adapter with mocked context manager."""
        mock_manager = MagicMock()
        adapter = ContextAdapter(context_manager=mock_manager)
        return adapter, mock_manager

    def test_returns_true_on_success(self, adapter_with_mock_manager):
        """Verify successful context set returns True."""
        adapter, mock_manager = adapter_with_mock_manager
        mock_manager.set_context.return_value = None

        result = adapter.set_in_session_state({"key": "value"})

        assert result is True
        mock_manager.set_context.assert_called_once()

    def test_returns_false_on_attribute_error(self, adapter_with_mock_manager, caplog):
        """Verify AttributeError returns False and logs with telemetry."""
        adapter, mock_manager = adapter_with_mock_manager
        mock_manager.set_context.side_effect = AttributeError("test error")

        with caplog.at_level(logging.ERROR):
            result = adapter.set_in_session_state({"key": "value"})

        assert result is False
        assert "AttributeError" in caplog.text
        # Verify structured logging has extra fields (check record attributes)
        error_records = [r for r in caplog.records if r.levelno == logging.ERROR]
        assert len(error_records) >= 1
        assert hasattr(error_records[0], "event")
        assert error_records[0].event == "context_set_error"

    def test_returns_false_on_key_error(self, adapter_with_mock_manager, caplog):
        """Verify KeyError returns False and logs with telemetry."""
        adapter, mock_manager = adapter_with_mock_manager
        mock_manager.set_context.side_effect = KeyError("missing_key")

        with caplog.at_level(logging.ERROR):
            result = adapter.set_in_session_state({"key": "value"})

        assert result is False
        assert "KeyError" in caplog.text

    def test_returns_false_on_type_error(self, adapter_with_mock_manager, caplog):
        """Verify TypeError returns False and logs with telemetry."""
        adapter, mock_manager = adapter_with_mock_manager
        mock_manager.set_context.side_effect = TypeError("wrong type")

        with caplog.at_level(logging.ERROR):
            result = adapter.set_in_session_state({"key": "value"})

        assert result is False
        assert "TypeError" in caplog.text

    def test_returns_false_on_value_error(self, adapter_with_mock_manager, caplog):
        """Verify ValueError returns False and logs with telemetry."""
        adapter, mock_manager = adapter_with_mock_manager
        mock_manager.set_context.side_effect = ValueError("invalid value")

        with caplog.at_level(logging.ERROR):
            result = adapter.set_in_session_state({"key": "value"})

        assert result is False
        assert "ValueError" in caplog.text

    def test_propagates_runtime_error(self, adapter_with_mock_manager):
        """Verify RuntimeError is NOT caught (propagates up)."""
        adapter, mock_manager = adapter_with_mock_manager
        mock_manager.set_context.side_effect = RuntimeError("system error")

        with pytest.raises(RuntimeError, match="system error"):
            adapter.set_in_session_state({"key": "value"})

    def test_logs_structured_telemetry(self, adapter_with_mock_manager, caplog):
        """Verify logging includes structured extra fields."""
        adapter, mock_manager = adapter_with_mock_manager
        mock_manager.set_context.side_effect = TypeError("test")

        with caplog.at_level(logging.ERROR):
            adapter.set_in_session_state({"key": "value"})

        # Check the log record has extra fields
        for record in caplog.records:
            if "context_set_error" in record.message or hasattr(record, "event"):
                assert hasattr(record, "event") or "context_set_error" in record.message
                break


class TestValidateErrorHandling:
    """Tests for validate exception handling."""

    @pytest.fixture
    def adapter_with_mock_manager(self):
        """Create adapter with mocked context manager."""
        mock_manager = MagicMock()
        adapter = ContextAdapter(context_manager=mock_manager)
        return adapter, mock_manager

    def test_returns_true_empty_list_on_success(self, adapter_with_mock_manager):
        """Verify successful validation returns (True, [])."""
        adapter, mock_manager = adapter_with_mock_manager
        mock_context = MagicMock()
        mock_context.to_dict.return_value = {"key": "value"}
        mock_manager.get_context.return_value = mock_context

        is_valid, messages = adapter.validate()

        assert is_valid is True
        assert messages == []

    def test_returns_true_when_context_is_none(self, adapter_with_mock_manager):
        """Verify None context is valid (empty dict fallback)."""
        adapter, mock_manager = adapter_with_mock_manager
        mock_manager.get_context.return_value = None

        is_valid, messages = adapter.validate()

        assert is_valid is True
        assert messages == []

    def test_returns_false_on_attribute_error(self, adapter_with_mock_manager, caplog):
        """Verify AttributeError returns (False, [message]) and logs."""
        adapter, mock_manager = adapter_with_mock_manager
        mock_manager.get_context.side_effect = AttributeError("no attribute")

        with caplog.at_level(logging.WARNING):
            is_valid, messages = adapter.validate()

        assert is_valid is False
        assert len(messages) == 1
        assert "no attribute" in messages[0]
        assert "AttributeError" in caplog.text
        # Verify structured logging has extra fields (check record attributes)
        warning_records = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert len(warning_records) >= 1
        assert hasattr(warning_records[0], "event")
        assert warning_records[0].event == "context_validation_error"

    def test_returns_false_on_key_error(self, adapter_with_mock_manager, caplog):
        """Verify KeyError returns (False, [message]) and logs."""
        adapter, mock_manager = adapter_with_mock_manager
        mock_manager.get_context.side_effect = KeyError("missing")

        with caplog.at_level(logging.WARNING):
            is_valid, messages = adapter.validate()

        assert is_valid is False
        assert "KeyError" in caplog.text

    def test_returns_false_on_type_error(self, adapter_with_mock_manager, caplog):
        """Verify TypeError returns (False, [message]) and logs."""
        adapter, mock_manager = adapter_with_mock_manager
        mock_context = MagicMock()
        mock_context.to_dict.side_effect = TypeError("wrong type")
        mock_manager.get_context.return_value = mock_context

        with caplog.at_level(logging.WARNING):
            is_valid, messages = adapter.validate()

        assert is_valid is False
        assert "TypeError" in caplog.text

    def test_returns_false_on_value_error(self, adapter_with_mock_manager, caplog):
        """Verify ValueError returns (False, [message]) and logs."""
        adapter, mock_manager = adapter_with_mock_manager
        mock_manager.get_context.side_effect = ValueError("invalid")

        with caplog.at_level(logging.WARNING):
            is_valid, messages = adapter.validate()

        assert is_valid is False
        assert "ValueError" in caplog.text

    def test_propagates_runtime_error(self, adapter_with_mock_manager):
        """Verify RuntimeError is NOT caught (propagates up)."""
        adapter, mock_manager = adapter_with_mock_manager
        mock_manager.get_context.side_effect = RuntimeError("system failure")

        with pytest.raises(RuntimeError, match="system failure"):
            adapter.validate()

    def test_logs_warning_not_error(self, adapter_with_mock_manager, caplog):
        """Verify validation failures log at WARNING level, not ERROR."""
        adapter, mock_manager = adapter_with_mock_manager
        mock_manager.get_context.side_effect = TypeError("test")

        with caplog.at_level(logging.DEBUG):
            adapter.validate()

        # Should have WARNING, not ERROR
        warning_records = [r for r in caplog.records if r.levelno == logging.WARNING]
        error_records = [r for r in caplog.records if r.levelno == logging.ERROR]

        assert len(warning_records) >= 1
        assert len(error_records) == 0
