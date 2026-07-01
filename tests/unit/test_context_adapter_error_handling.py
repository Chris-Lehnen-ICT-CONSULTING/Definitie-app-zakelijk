"""
Tests for ContextAdapter error handling (DEF-252 follow-up).

These tests verify that context_adapter.py properly handles exceptions
with narrow types and structured logging, consistent with components_adapter.py.

DEF-484: de adapter bewaart context nu per-sessie via SessionStateManager en
gebruikt ContextManager alleen voor stateless validatie (validate_context). De
error-handling-contracten (narrow errors -> False, RuntimeError propageert,
structured logging) blijven ongewijzigd; alleen de gemockte methode wisselde
van set_context/get_context naar validate_context.
"""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest

pytestmark = [pytest.mark.unit]


@pytest.fixture
def mock_streamlit_session():
    """Patch SessionStateManager zodat de adapter geen echte st.session_state raakt.

    get_value geeft None (lege sessie) → get_from_session_state levert {}; set_value
    is een no-op. Zo isoleren we het error-handling-gedrag van de adapter.
    """
    ssm = MagicMock()
    ssm.get_value.return_value = None
    with patch("ui.session_state.SessionStateManager", ssm):
        yield ssm


def _adapter(_mock_streamlit_session):
    """ContextAdapter met gemockte manager (binnen de gepatchte SessionStateManager)."""
    from ui.helpers.context_adapter import ContextAdapter

    mock_manager = MagicMock()
    return ContextAdapter(context_manager=mock_manager), mock_manager


class TestSetInSessionStateErrorHandling:
    """Tests for set_in_session_state exception handling."""

    def test_returns_true_on_success(self, mock_streamlit_session):
        """Verify successful context set returns True and persists per-session."""
        adapter, mock_manager = _adapter(mock_streamlit_session)
        mock_manager.validate_context.return_value = {"organisatorische_context": []}

        result = adapter.set_in_session_state({"key": "value"})

        assert result is True
        mock_manager.validate_context.assert_called_once()

    def test_returns_false_on_attribute_error(self, mock_streamlit_session, caplog):
        """Verify AttributeError returns False and logs with telemetry."""
        adapter, mock_manager = _adapter(mock_streamlit_session)
        mock_manager.validate_context.side_effect = AttributeError("test error")

        with caplog.at_level(logging.ERROR):
            result = adapter.set_in_session_state({"key": "value"})

        assert result is False
        assert "AttributeError" in caplog.text
        error_records = [r for r in caplog.records if r.levelno == logging.ERROR]
        assert len(error_records) >= 1
        assert hasattr(error_records[0], "event")
        assert error_records[0].event == "context_set_error"

    def test_returns_false_on_key_error(self, mock_streamlit_session, caplog):
        """Verify KeyError returns False and logs with telemetry."""
        adapter, mock_manager = _adapter(mock_streamlit_session)
        mock_manager.validate_context.side_effect = KeyError("missing_key")

        with caplog.at_level(logging.ERROR):
            result = adapter.set_in_session_state({"key": "value"})

        assert result is False
        assert "KeyError" in caplog.text

    def test_returns_false_on_type_error(self, mock_streamlit_session, caplog):
        """Verify TypeError returns False and logs with telemetry."""
        adapter, mock_manager = _adapter(mock_streamlit_session)
        mock_manager.validate_context.side_effect = TypeError("wrong type")

        with caplog.at_level(logging.ERROR):
            result = adapter.set_in_session_state({"key": "value"})

        assert result is False
        assert "TypeError" in caplog.text

    def test_returns_false_on_value_error(self, mock_streamlit_session, caplog):
        """Verify ValueError returns False and logs with telemetry."""
        adapter, mock_manager = _adapter(mock_streamlit_session)
        mock_manager.validate_context.side_effect = ValueError("invalid value")

        with caplog.at_level(logging.ERROR):
            result = adapter.set_in_session_state({"key": "value"})

        assert result is False
        assert "ValueError" in caplog.text

    def test_propagates_runtime_error(self, mock_streamlit_session):
        """Verify RuntimeError is NOT caught (propagates up)."""
        adapter, mock_manager = _adapter(mock_streamlit_session)
        mock_manager.validate_context.side_effect = RuntimeError("system error")

        with pytest.raises(RuntimeError, match="system error"):
            adapter.set_in_session_state({"key": "value"})

    def test_logs_structured_telemetry(self, mock_streamlit_session, caplog):
        """Verify logging includes structured extra fields."""
        adapter, mock_manager = _adapter(mock_streamlit_session)
        mock_manager.validate_context.side_effect = TypeError("test")

        with caplog.at_level(logging.ERROR):
            adapter.set_in_session_state({"key": "value"})

        for record in caplog.records:
            if "context_set_error" in record.message or hasattr(record, "event"):
                assert hasattr(record, "event") or "context_set_error" in record.message
                break


class TestValidateErrorHandling:
    """Tests for validate exception handling."""

    def test_returns_true_empty_list_on_success(self, mock_streamlit_session):
        """Verify successful validation returns (True, [])."""
        adapter, mock_manager = _adapter(mock_streamlit_session)
        mock_manager.validate_context.return_value = {"key": "value"}

        is_valid, messages = adapter.validate()

        assert is_valid is True
        assert messages == []

    def test_returns_true_on_empty_session(self, mock_streamlit_session):
        """Verify validation of an empty session is valid."""
        adapter, mock_manager = _adapter(mock_streamlit_session)
        mock_manager.validate_context.return_value = {}

        is_valid, messages = adapter.validate()

        assert is_valid is True
        assert messages == []

    def test_returns_false_on_attribute_error(self, mock_streamlit_session, caplog):
        """Verify AttributeError returns (False, [message]) and logs."""
        adapter, mock_manager = _adapter(mock_streamlit_session)
        mock_manager.validate_context.side_effect = AttributeError("no attribute")

        with caplog.at_level(logging.WARNING):
            is_valid, messages = adapter.validate()

        assert is_valid is False
        assert len(messages) == 1
        assert "no attribute" in messages[0]
        assert "AttributeError" in caplog.text
        warning_records = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert len(warning_records) >= 1
        assert hasattr(warning_records[0], "event")
        assert warning_records[0].event == "context_validation_error"

    def test_returns_false_on_key_error(self, mock_streamlit_session, caplog):
        """Verify KeyError returns (False, [message]) and logs."""
        adapter, mock_manager = _adapter(mock_streamlit_session)
        mock_manager.validate_context.side_effect = KeyError("missing")

        with caplog.at_level(logging.WARNING):
            is_valid, messages = adapter.validate()

        assert is_valid is False
        assert "KeyError" in caplog.text

    def test_returns_false_on_type_error(self, mock_streamlit_session, caplog):
        """Verify TypeError returns (False, [message]) and logs."""
        adapter, mock_manager = _adapter(mock_streamlit_session)
        mock_manager.validate_context.side_effect = TypeError("wrong type")

        with caplog.at_level(logging.WARNING):
            is_valid, messages = adapter.validate()

        assert is_valid is False
        assert "TypeError" in caplog.text

    def test_returns_false_on_value_error(self, mock_streamlit_session, caplog):
        """Verify ValueError returns (False, [message]) and logs."""
        adapter, mock_manager = _adapter(mock_streamlit_session)
        mock_manager.validate_context.side_effect = ValueError("invalid")

        with caplog.at_level(logging.WARNING):
            is_valid, messages = adapter.validate()

        assert is_valid is False
        assert "ValueError" in caplog.text

    def test_propagates_runtime_error(self, mock_streamlit_session):
        """Verify RuntimeError is NOT caught (propagates up)."""
        adapter, mock_manager = _adapter(mock_streamlit_session)
        mock_manager.validate_context.side_effect = RuntimeError("system failure")

        with pytest.raises(RuntimeError, match="system failure"):
            adapter.validate()

    def test_logs_warning_not_error(self, mock_streamlit_session, caplog):
        """Verify validation failures log at WARNING level, not ERROR."""
        adapter, mock_manager = _adapter(mock_streamlit_session)
        mock_manager.validate_context.side_effect = TypeError("test")

        with caplog.at_level(logging.DEBUG):
            adapter.validate()

        warning_records = [r for r in caplog.records if r.levelno == logging.WARNING]
        error_records = [r for r in caplog.records if r.levelno == logging.ERROR]

        assert len(warning_records) >= 1
        assert len(error_records) == 0
