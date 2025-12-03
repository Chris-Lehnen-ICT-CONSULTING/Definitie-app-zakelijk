"""
Unit tests for DEF-252 Follow-up: Error Handling Fixes in UIComponentsAdapter.

These tests verify the 4 silent failure fixes:
1. Prompt extraction fallback (logger.warning)
2. Export formats fallback (logger.error + st.warning)
3. Export definition error handling (logger.error + st.error)
4. Prepare review error handling (logger.error + st.error)

Related:
- Issue: DEF-252 Follow-up
- File: src/ui/components_adapter.py
"""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# Early import to ensure module is in sys.modules before patching
import ui.components_adapter as _components_adapter_module

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_session_state_values() -> dict[str, Any]:
    """Default session state values for testing."""
    return {
        "begrip": "testbegrip",
        "gegenereerd": "test definitie",
        "definitie_gecorrigeerd": None,
        "aangepaste_definitie": None,
        "expert_review": "",
        "voorkeursterm": "",
        "organisatorische_context": ["DJI", "OM"],
        "juridische_context": ["Strafrecht"],
        "wettelijke_basis": ["Wetboek van Strafrecht"],
        "datum": "2024-01-01",
        "voorsteller": "test_user",
        "ketenpartners": [],
        "marker": None,
        "voorbeeld_zinnen": [],
        "praktijkvoorbeelden": [],
        "tegenvoorbeelden": [],
        "synoniemen": "",
        "antoniemen": "",
        "toelichting": "",
        "beoordeling": [],
        "beoordeling_gen": [],
        "toetsresultaten": {},
        "bronnen_gebruikt": "",
        "bronnen": [],
        "last_generation_result": {},
        "current_definition_id": None,
        "current_user": "test_user",
    }


@pytest.fixture
def session_state_getter(mock_session_state_values: dict[str, Any]):
    """Create a mock getter for SessionStateManager.get_value."""

    def getter(key: str, default: Any = None) -> Any:
        return mock_session_state_values.get(key, default)

    return getter


# =============================================================================
# Test Class 1: Prompt Extraction Fallback
# =============================================================================


class TestPromptExtractionFallback:
    """Test prompt extraction failure logging (DEF-252 follow-up)."""

    def test_logs_warning_when_session_state_raises_exception(
        self, session_state_getter
    ):
        """Verify logger.warning when SessionStateManager raises exception during prompt extraction."""
        with (
            patch("ui.components_adapter.logger") as mock_logger,
            patch("ui.components_adapter.st"),
            patch("ui.components_adapter.get_context_adapter") as mock_get_adapter,
            patch("ui.components_adapter.SessionStateManager") as mock_ssm,
            patch("ui.components_adapter.get_definition_service") as mock_get_service,
        ):
            # Setup successful context adapter
            mock_adapter = MagicMock()
            mock_adapter.get_merged_context.return_value = {
                "organisatorische_context": [],
                "juridische_context": [],
                "wettelijke_basis": [],
            }
            mock_get_adapter.return_value = mock_adapter

            # Track how many times get_value is called to raise exception only for last_generation_result

            def ssm_getter(key: str, default: Any = None) -> Any:
                # Raise TypeError only for last_generation_result to trigger fallback
                if key == "last_generation_result":
                    raise TypeError("Simulated error in SessionStateManager")
                return session_state_getter(key, default)

            mock_ssm.get_value.side_effect = ssm_getter

            mock_service = MagicMock()
            mock_get_service.return_value = mock_service

            from ui.components_adapter import UIComponentsAdapter

            adapter = UIComponentsAdapter()
            result = adapter._collect_ui_data_for_export()

            # Assert: logger.warning was called for prompt extraction
            warning_calls = [
                call
                for call in mock_logger.warning.call_args_list
                if "Prompt extraction failed" in str(call)
            ]
            assert len(warning_calls) >= 1

            # Assert: prompt_text falls back to None
            assert result.get("prompt_text") is None

    def test_logs_warning_with_telemetry_metadata(self, session_state_getter):
        """Verify logger.warning includes structured telemetry."""
        with (
            patch("ui.components_adapter.logger") as mock_logger,
            patch("ui.components_adapter.st"),
            patch("ui.components_adapter.get_context_adapter") as mock_get_adapter,
            patch("ui.components_adapter.SessionStateManager") as mock_ssm,
            patch("ui.components_adapter.get_definition_service") as mock_get_service,
        ):
            mock_adapter = MagicMock()
            mock_adapter.get_merged_context.return_value = {
                "organisatorische_context": [],
                "juridische_context": [],
                "wettelijke_basis": [],
            }
            mock_get_adapter.return_value = mock_adapter

            # Return data that causes TypeError when accessing nested dict
            def ssm_getter(key: str, default: Any = None) -> Any:
                if key == "last_generation_result":
                    return {"agent_result": None}  # None.get() will fail
                return session_state_getter(key, default)

            mock_ssm.get_value.side_effect = ssm_getter

            mock_service = MagicMock()
            mock_get_service.return_value = mock_service

            from ui.components_adapter import UIComponentsAdapter

            adapter = UIComponentsAdapter()
            adapter._collect_ui_data_for_export()

            # Check telemetry in warning call
            for call in mock_logger.warning.call_args_list:
                if "Prompt extraction failed" in str(call):
                    call_kwargs = call[1]
                    assert "extra" in call_kwargs
                    assert call_kwargs["extra"]["event"] == "prompt_extraction_fallback"
                    assert "error_type" in call_kwargs["extra"]

    def test_happy_path_extracts_prompt_text(self, session_state_getter):
        """Verify prompt extraction works with valid data."""
        with (
            patch("ui.components_adapter.logger") as mock_logger,
            patch("ui.components_adapter.st"),
            patch("ui.components_adapter.get_context_adapter") as mock_get_adapter,
            patch("ui.components_adapter.SessionStateManager") as mock_ssm,
            patch("ui.components_adapter.get_definition_service") as mock_get_service,
        ):
            mock_adapter = MagicMock()
            mock_adapter.get_merged_context.return_value = {
                "organisatorische_context": [],
                "juridische_context": [],
                "wettelijke_basis": [],
            }
            mock_get_adapter.return_value = mock_adapter

            # Return valid nested structure
            def ssm_getter(key: str, default: Any = None) -> Any:
                if key == "last_generation_result":
                    return {
                        "agent_result": {
                            "metadata": {"prompt_text": "Test prompt content"}
                        }
                    }
                return session_state_getter(key, default)

            mock_ssm.get_value.side_effect = ssm_getter

            mock_service = MagicMock()
            mock_get_service.return_value = mock_service

            from ui.components_adapter import UIComponentsAdapter

            adapter = UIComponentsAdapter()
            result = adapter._collect_ui_data_for_export()

            # Assert: prompt_text extracted successfully
            assert result.get("prompt_text") == "Test prompt content"

            # Assert: No warning logged for prompt extraction
            warning_calls = [
                call
                for call in mock_logger.warning.call_args_list
                if "Prompt extraction" in str(call)
            ]
            assert len(warning_calls) == 0


# =============================================================================
# Test Class 2: Export Formats Fallback
# =============================================================================


class TestExportFormatsFallback:
    """Test get_export_formats() fallback behavior (DEF-252 follow-up)."""

    def test_logs_error_and_shows_warning_on_attribute_error(self):
        """Verify logger.error and st.warning on AttributeError."""
        with (
            patch("ui.components_adapter.logger") as mock_logger,
            patch("ui.components_adapter.st") as mock_st,
            patch("ui.components_adapter.get_definition_service") as mock_get_service,
        ):
            mock_service = MagicMock()
            mock_service.ui_service.get_export_formats.side_effect = AttributeError(
                "ui_service not found"
            )
            mock_get_service.return_value = mock_service

            from ui.components_adapter import UIComponentsAdapter

            adapter = UIComponentsAdapter()
            result = adapter.get_export_formats()

            # Assert: logger.error called
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert "Export formats ophalen mislukt" in call_args[0][0]
            assert "AttributeError" in call_args[0][0]

            # Assert: st.warning called
            mock_st.warning.assert_called_once()
            warning_msg = mock_st.warning.call_args[0][0]
            assert "Export formaten konden niet worden opgehaald" in warning_msg

            # Assert: returns basic formats
            assert len(result) == 3
            assert result[0]["value"] == "txt"

    def test_logs_error_and_shows_warning_on_runtime_error(self):
        """Verify fallback triggers on RuntimeError."""
        with (
            patch("ui.components_adapter.logger") as mock_logger,
            patch("ui.components_adapter.st") as mock_st,
            patch("ui.components_adapter.get_definition_service") as mock_get_service,
        ):
            mock_service = MagicMock()
            mock_service.ui_service.get_export_formats.side_effect = RuntimeError(
                "service failure"
            )
            mock_get_service.return_value = mock_service

            from ui.components_adapter import UIComponentsAdapter

            adapter = UIComponentsAdapter()
            result = adapter.get_export_formats()

            mock_logger.error.assert_called_once()
            mock_st.warning.assert_called_once()
            assert len(result) == 3

    def test_logs_error_and_shows_warning_on_connection_error(self):
        """Verify fallback triggers on ConnectionError."""
        with (
            patch("ui.components_adapter.logger") as mock_logger,
            patch("ui.components_adapter.st") as mock_st,
            patch("ui.components_adapter.get_definition_service") as mock_get_service,
        ):
            mock_service = MagicMock()
            mock_service.ui_service.get_export_formats.side_effect = ConnectionError(
                "network failure"
            )
            mock_get_service.return_value = mock_service

            from ui.components_adapter import UIComponentsAdapter

            adapter = UIComponentsAdapter()
            result = adapter.get_export_formats()

            mock_logger.error.assert_called_once()
            mock_st.warning.assert_called_once()
            assert len(result) == 3

    def test_logs_with_telemetry_metadata(self):
        """Verify logger.error includes structured telemetry."""
        with (
            patch("ui.components_adapter.logger") as mock_logger,
            patch("ui.components_adapter.st"),
            patch("ui.components_adapter.get_definition_service") as mock_get_service,
        ):
            mock_service = MagicMock()
            mock_service.ui_service.get_export_formats.side_effect = AttributeError(
                "test"
            )
            mock_get_service.return_value = mock_service

            from ui.components_adapter import UIComponentsAdapter

            adapter = UIComponentsAdapter()
            adapter.get_export_formats()

            call_kwargs = mock_logger.error.call_args[1]
            assert "extra" in call_kwargs
            assert call_kwargs["extra"]["event"] == "export_formats_fallback"
            assert call_kwargs["extra"]["error_type"] == "AttributeError"

    def test_returns_basic_formats_on_failure(self):
        """Verify fallback returns TXT, JSON, CSV formats."""
        with (
            patch("ui.components_adapter.logger"),
            patch("ui.components_adapter.st"),
            patch("ui.components_adapter.get_definition_service") as mock_get_service,
        ):
            mock_service = MagicMock()
            mock_service.ui_service.get_export_formats.side_effect = RuntimeError()
            mock_get_service.return_value = mock_service

            from ui.components_adapter import UIComponentsAdapter

            adapter = UIComponentsAdapter()
            result = adapter.get_export_formats()

            assert len(result) == 3
            values = [f["value"] for f in result]
            assert "txt" in values
            assert "json" in values
            assert "csv" in values
            for f in result:
                assert f["available"] is True

    def test_happy_path_returns_service_formats(self):
        """Verify successful call returns service formats."""
        with (
            patch("ui.components_adapter.logger") as mock_logger,
            patch("ui.components_adapter.st") as mock_st,
            patch("ui.components_adapter.get_definition_service") as mock_get_service,
        ):
            expected_formats = [
                {"value": "docx", "label": "DOCX", "available": True},
                {"value": "pdf", "label": "PDF", "available": True},
            ]
            mock_service = MagicMock()
            mock_service.ui_service.get_export_formats.return_value = expected_formats
            mock_get_service.return_value = mock_service

            from ui.components_adapter import UIComponentsAdapter

            adapter = UIComponentsAdapter()
            result = adapter.get_export_formats()

            assert result == expected_formats
            mock_logger.error.assert_not_called()
            mock_st.warning.assert_not_called()

    def test_uncaught_exceptions_propagate(self):
        """Verify exceptions NOT in the list propagate."""
        with (
            patch("ui.components_adapter.logger"),
            patch("ui.components_adapter.st"),
            patch("ui.components_adapter.get_definition_service") as mock_get_service,
        ):
            mock_service = MagicMock()
            mock_service.ui_service.get_export_formats.side_effect = ValueError(
                "unexpected"
            )
            mock_get_service.return_value = mock_service

            from ui.components_adapter import UIComponentsAdapter

            adapter = UIComponentsAdapter()

            with pytest.raises(ValueError, match="unexpected"):
                adapter.get_export_formats()


# =============================================================================
# Test Class 3: Export Definition Error Handling
# =============================================================================


class TestExportDefinitionErrorHandling:
    """Test export_definition() exception handling (DEF-252 follow-up)."""

    def test_logs_error_on_attribute_error(self, session_state_getter):
        """Verify logger.error called with structured metadata."""
        with (
            patch("ui.components_adapter.logger") as mock_logger,
            patch("ui.components_adapter.st") as mock_st,
            patch("ui.components_adapter.get_context_adapter") as mock_get_adapter,
            patch("ui.components_adapter.SessionStateManager") as mock_ssm,
            patch("ui.components_adapter.get_definition_service") as mock_get_service,
        ):
            mock_adapter = MagicMock()
            mock_adapter.get_merged_context.return_value = {
                "organisatorische_context": [],
                "juridische_context": [],
                "wettelijke_basis": [],
            }
            mock_get_adapter.return_value = mock_adapter

            mock_ssm.get_value.side_effect = session_state_getter

            mock_service = MagicMock()
            mock_service.export_definition.side_effect = AttributeError("missing attr")
            mock_get_service.return_value = mock_service

            from ui.components_adapter import UIComponentsAdapter

            adapter = UIComponentsAdapter()
            result = adapter.export_definition(format="txt")

            # Assert: returns False
            assert result is False

            # Assert: logger.error called with telemetry
            error_calls = [
                call
                for call in mock_logger.error.call_args_list
                if "Export fout" in str(call)
            ]
            assert len(error_calls) >= 1
            call_kwargs = error_calls[0][1]
            assert call_kwargs["extra"]["event"] == "export_error"

            # Assert: st.error called
            mock_st.error.assert_called()

    def test_logs_error_on_os_error(self, session_state_getter):
        """Verify OSError (file access) triggers logging."""
        with (
            patch("ui.components_adapter.logger") as mock_logger,
            patch("ui.components_adapter.st"),
            patch("ui.components_adapter.get_context_adapter") as mock_get_adapter,
            patch("ui.components_adapter.SessionStateManager") as mock_ssm,
            patch("ui.components_adapter.get_definition_service") as mock_get_service,
        ):
            mock_adapter = MagicMock()
            mock_adapter.get_merged_context.return_value = {
                "organisatorische_context": [],
                "juridische_context": [],
                "wettelijke_basis": [],
            }
            mock_get_adapter.return_value = mock_adapter

            mock_ssm.get_value.side_effect = session_state_getter

            mock_service = MagicMock()
            mock_service.export_definition.side_effect = OSError("disk full")
            mock_get_service.return_value = mock_service

            from ui.components_adapter import UIComponentsAdapter

            adapter = UIComponentsAdapter()
            result = adapter.export_definition(format="txt")

            assert result is False
            error_calls = [
                call
                for call in mock_logger.error.call_args_list
                if "Export fout" in str(call)
            ]
            assert len(error_calls) >= 1

    def test_returns_false_on_exception(self, session_state_getter):
        """Verify method returns False on any caught exception."""
        with (
            patch("ui.components_adapter.logger"),
            patch("ui.components_adapter.st"),
            patch("ui.components_adapter.get_context_adapter") as mock_get_adapter,
            patch("ui.components_adapter.SessionStateManager") as mock_ssm,
            patch("ui.components_adapter.get_definition_service") as mock_get_service,
        ):
            mock_adapter = MagicMock()
            mock_adapter.get_merged_context.return_value = {
                "organisatorische_context": [],
                "juridische_context": [],
                "wettelijke_basis": [],
            }
            mock_get_adapter.return_value = mock_adapter

            mock_ssm.get_value.side_effect = session_state_getter

            mock_service = MagicMock()
            mock_service.export_definition.side_effect = RuntimeError("error")
            mock_get_service.return_value = mock_service

            from ui.components_adapter import UIComponentsAdapter

            adapter = UIComponentsAdapter()

            for exc in [
                AttributeError("a"),
                KeyError("k"),
                TypeError("t"),
                ValueError("v"),
                OSError("o"),
                RuntimeError("r"),
            ]:
                mock_service.export_definition.side_effect = exc
                result = adapter.export_definition(format="txt")
                assert result is False

    def test_uncaught_exceptions_propagate(self, session_state_getter):
        """Verify exceptions NOT in the list propagate (e.g., ImportError)."""
        with (
            patch("ui.components_adapter.logger"),
            patch("ui.components_adapter.st"),
            patch("ui.components_adapter.get_context_adapter") as mock_get_adapter,
            patch("ui.components_adapter.SessionStateManager") as mock_ssm,
            patch("ui.components_adapter.get_definition_service") as mock_get_service,
        ):
            mock_adapter = MagicMock()
            mock_adapter.get_merged_context.return_value = {
                "organisatorische_context": [],
                "juridische_context": [],
                "wettelijke_basis": [],
            }
            mock_get_adapter.return_value = mock_adapter

            mock_ssm.get_value.side_effect = session_state_getter

            mock_service = MagicMock()
            # Use ImportError - NOT a subclass of any caught exception:
            # (AttributeError, KeyError, TypeError, ValueError, OSError, RuntimeError)
            # RecursionError is subclass of RuntimeError, so it gets caught!
            mock_service.export_definition.side_effect = ImportError("missing module")
            mock_get_service.return_value = mock_service

            from ui.components_adapter import UIComponentsAdapter

            adapter = UIComponentsAdapter()

            with pytest.raises(ImportError, match="missing module"):
                adapter.export_definition(format="txt")


# =============================================================================
# Test Class 4: Prepare Review Error Handling
# =============================================================================


class TestPrepareForReviewErrorHandling:
    """Test prepare_for_review() exception handling (DEF-252 follow-up)."""

    def test_logs_error_on_attribute_error(self):
        """Verify logger.error with event='review_preparation_error'."""
        with (
            patch("ui.components_adapter.logger") as mock_logger,
            patch("ui.components_adapter.st") as mock_st,
            patch("ui.components_adapter.SessionStateManager") as mock_ssm,
            patch("ui.components_adapter.get_definition_service") as mock_get_service,
        ):
            mock_ssm.get_value.return_value = "test_user"

            mock_service = MagicMock()
            mock_service.ui_service.prepare_definition_for_review.side_effect = (
                AttributeError("missing")
            )
            mock_get_service.return_value = mock_service

            from ui.components_adapter import UIComponentsAdapter

            adapter = UIComponentsAdapter()
            result = adapter.prepare_for_review(definition_id=1)

            assert result is False

            error_calls = [
                call
                for call in mock_logger.error.call_args_list
                if "Review voorbereiding fout" in str(call)
            ]
            assert len(error_calls) >= 1
            call_kwargs = error_calls[0][1]
            assert call_kwargs["extra"]["event"] == "review_preparation_error"

            mock_st.error.assert_called()

    def test_logs_error_on_runtime_error(self):
        """Verify RuntimeError triggers logging."""
        with (
            patch("ui.components_adapter.logger") as mock_logger,
            patch("ui.components_adapter.st"),
            patch("ui.components_adapter.SessionStateManager") as mock_ssm,
            patch("ui.components_adapter.get_definition_service") as mock_get_service,
        ):
            mock_ssm.get_value.return_value = "test_user"

            mock_service = MagicMock()
            mock_service.ui_service.prepare_definition_for_review.side_effect = (
                RuntimeError("service error")
            )
            mock_get_service.return_value = mock_service

            from ui.components_adapter import UIComponentsAdapter

            adapter = UIComponentsAdapter()
            result = adapter.prepare_for_review(definition_id=1)

            assert result is False
            error_calls = [
                call
                for call in mock_logger.error.call_args_list
                if "Review voorbereiding fout" in str(call)
            ]
            assert len(error_calls) >= 1

    def test_returns_false_on_exception(self):
        """Verify method returns False on any caught exception."""
        with (
            patch("ui.components_adapter.logger"),
            patch("ui.components_adapter.st"),
            patch("ui.components_adapter.SessionStateManager") as mock_ssm,
            patch("ui.components_adapter.get_definition_service") as mock_get_service,
        ):
            mock_ssm.get_value.return_value = "test_user"

            mock_service = MagicMock()
            mock_get_service.return_value = mock_service

            from ui.components_adapter import UIComponentsAdapter

            adapter = UIComponentsAdapter()

            for exc in [
                AttributeError("a"),
                KeyError("k"),
                TypeError("t"),
                ValueError("v"),
                RuntimeError("r"),
            ]:
                mock_service.ui_service.prepare_definition_for_review.side_effect = exc
                result = adapter.prepare_for_review(definition_id=1)
                assert result is False

    def test_uncaught_exceptions_propagate(self):
        """Verify exceptions NOT in the list propagate."""
        with (
            patch("ui.components_adapter.logger"),
            patch("ui.components_adapter.st"),
            patch("ui.components_adapter.SessionStateManager") as mock_ssm,
            patch("ui.components_adapter.get_definition_service") as mock_get_service,
        ):
            mock_ssm.get_value.return_value = "test_user"

            mock_service = MagicMock()
            mock_service.ui_service.prepare_definition_for_review.side_effect = OSError(
                "file error"
            )
            mock_get_service.return_value = mock_service

            from ui.components_adapter import UIComponentsAdapter

            adapter = UIComponentsAdapter()

            # OSError is NOT in the caught list for prepare_for_review
            with pytest.raises(OSError, match="file error"):
                adapter.prepare_for_review(definition_id=1)

    def test_happy_path_returns_true(self):
        """Verify successful call returns True."""
        with (
            patch("ui.components_adapter.logger"),
            patch("ui.components_adapter.st") as mock_st,
            patch("ui.components_adapter.SessionStateManager") as mock_ssm,
            patch("ui.components_adapter.get_definition_service") as mock_get_service,
        ):
            mock_ssm.get_value.return_value = "test_user"

            mock_service = MagicMock()
            mock_service.ui_service.prepare_definition_for_review.return_value = {
                "success": True,
                "message": "Definitie klaar voor review",
            }
            mock_get_service.return_value = mock_service

            from ui.components_adapter import UIComponentsAdapter

            adapter = UIComponentsAdapter()
            result = adapter.prepare_for_review(definition_id=1)

            assert result is True
            mock_st.success.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
