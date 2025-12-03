"""
Unit tests for DEF-252: Context Fallback Fix in UIComponentsAdapter.

These tests verify that when ContextAdapter fails (raises exceptions), the
UIComponentsAdapter correctly:
1. Logs an error via logger.error() (AC1)
2. Shows a user warning via st.warning() (AC2)
3. Falls back to correct session state keys
4. Does NOT log/warn on the happy path

Related:
- Issue: DEF-252 (Complete Context Fallback Fix)
- File: src/ui/components_adapter.py (lines 110-143)
- Exception types: AttributeError, KeyError, TypeError, ValueError
"""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# Early import to ensure module is in sys.modules before patching
# This resolves "module 'ui' has no attribute 'components_adapter'" errors
import ui.components_adapter as _components_adapter_module


class TestContextFallbackLogging:
    """Test that context fallback logs errors correctly (AC1)."""

    @pytest.fixture
    def mock_session_state_values(self) -> dict[str, Any]:
        """Default session state values for fallback testing."""
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
        }

    @pytest.fixture
    def session_state_getter(self, mock_session_state_values: dict[str, Any]):
        """Create a mock getter for SessionStateManager.get_value."""

        def getter(key: str, default: Any = None) -> Any:
            return mock_session_state_values.get(key, default)

        return getter

    def test_context_fallback_logs_error_on_attribute_error(self, session_state_getter):
        """Verify logger.error is called when ContextAdapter raises AttributeError."""
        with (
            patch("ui.components_adapter.logger") as mock_logger,
            patch("ui.components_adapter.st"),
            patch("ui.components_adapter.get_context_adapter") as mock_get_adapter,
            patch("ui.components_adapter.SessionStateManager") as mock_ssm,
            patch("ui.components_adapter.get_definition_service") as mock_get_service,
        ):
            # Setup: ContextAdapter raises AttributeError
            mock_adapter = MagicMock()
            mock_adapter.get_merged_context.side_effect = AttributeError(
                "get_merged_context not found"
            )
            mock_get_adapter.return_value = mock_adapter

            # Setup SessionStateManager mock
            mock_ssm.get_value.side_effect = session_state_getter

            # Setup service mock
            mock_service = MagicMock()
            mock_get_service.return_value = mock_service

            # Import and instantiate after patching
            from ui.components_adapter import UIComponentsAdapter

            adapter = UIComponentsAdapter()

            # Act: trigger _collect_ui_data_for_export
            adapter._collect_ui_data_for_export()

            # Assert: logger.error was called with fallback info
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert "ContextAdapter fallback activated" in call_args[0][0]
            assert "AttributeError" in call_args[0][0]

    def test_context_fallback_logs_error_on_key_error(self, session_state_getter):
        """Verify logger.error is called when ContextAdapter raises KeyError."""
        with (
            patch("ui.components_adapter.logger") as mock_logger,
            patch("ui.components_adapter.st"),
            patch("ui.components_adapter.get_context_adapter") as mock_get_adapter,
            patch("ui.components_adapter.SessionStateManager") as mock_ssm,
            patch("ui.components_adapter.get_definition_service") as mock_get_service,
        ):
            # Setup: ContextAdapter raises KeyError
            mock_adapter = MagicMock()
            mock_adapter.get_merged_context.side_effect = KeyError(
                "organisatorische_context"
            )
            mock_get_adapter.return_value = mock_adapter

            mock_ssm.get_value.side_effect = session_state_getter

            mock_service = MagicMock()
            mock_get_service.return_value = mock_service

            from ui.components_adapter import UIComponentsAdapter

            adapter = UIComponentsAdapter()
            adapter._collect_ui_data_for_export()

            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert "ContextAdapter fallback activated" in call_args[0][0]
            assert "KeyError" in call_args[0][0]

    def test_context_fallback_logs_error_on_type_error(self, session_state_getter):
        """Verify logger.error is called when ContextAdapter raises TypeError."""
        with (
            patch("ui.components_adapter.logger") as mock_logger,
            patch("ui.components_adapter.st"),
            patch("ui.components_adapter.get_context_adapter") as mock_get_adapter,
            patch("ui.components_adapter.SessionStateManager") as mock_ssm,
            patch("ui.components_adapter.get_definition_service") as mock_get_service,
        ):
            # Setup: ContextAdapter raises TypeError
            mock_adapter = MagicMock()
            mock_adapter.get_merged_context.side_effect = TypeError(
                "cannot subscript NoneType"
            )
            mock_get_adapter.return_value = mock_adapter

            mock_ssm.get_value.side_effect = session_state_getter

            mock_service = MagicMock()
            mock_get_service.return_value = mock_service

            from ui.components_adapter import UIComponentsAdapter

            adapter = UIComponentsAdapter()
            adapter._collect_ui_data_for_export()

            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert "ContextAdapter fallback activated" in call_args[0][0]
            assert "TypeError" in call_args[0][0]

    def test_context_fallback_logs_with_extra_metadata(self, session_state_getter):
        """Verify logger.error includes structured metadata for telemetry."""
        with (
            patch("ui.components_adapter.logger") as mock_logger,
            patch("ui.components_adapter.st"),
            patch("ui.components_adapter.get_context_adapter") as mock_get_adapter,
            patch("ui.components_adapter.SessionStateManager") as mock_ssm,
            patch("ui.components_adapter.get_definition_service") as mock_get_service,
        ):
            mock_adapter = MagicMock()
            mock_adapter.get_merged_context.side_effect = AttributeError("test")
            mock_get_adapter.return_value = mock_adapter

            mock_ssm.get_value.side_effect = session_state_getter

            mock_service = MagicMock()
            mock_get_service.return_value = mock_service

            from ui.components_adapter import UIComponentsAdapter

            adapter = UIComponentsAdapter()
            adapter._collect_ui_data_for_export()

            # Check that extra metadata was passed for structured logging
            call_kwargs = mock_logger.error.call_args[1]
            assert "extra" in call_kwargs
            assert call_kwargs["extra"]["event"] == "context_fallback"
            assert call_kwargs["extra"]["error_type"] == "AttributeError"


class TestContextFallbackWarning:
    """Test that context fallback shows user warning (AC2)."""

    @pytest.fixture
    def mock_session_state_values(self) -> dict[str, Any]:
        """Default session state values for fallback testing."""
        return {
            "begrip": "testbegrip",
            "gegenereerd": "test definitie",
            "definitie_gecorrigeerd": None,
            "aangepaste_definitie": None,
            "expert_review": "",
            "voorkeursterm": "",
            "organisatorische_context": ["DJI"],
            "juridische_context": ["Strafrecht"],
            "wettelijke_basis": ["Wetboek van Strafrecht"],
            "datum": "2024-01-01",
            "voorsteller": "",
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
        }

    @pytest.fixture
    def session_state_getter(self, mock_session_state_values: dict[str, Any]):
        """Create a mock getter for SessionStateManager.get_value."""

        def getter(key: str, default: Any = None) -> Any:
            return mock_session_state_values.get(key, default)

        return getter

    def test_context_fallback_shows_warning_on_attribute_error(
        self, session_state_getter
    ):
        """Verify st.warning is called when fallback is triggered."""
        with (
            patch("ui.components_adapter.logger"),
            patch("ui.components_adapter.st") as mock_st,
            patch("ui.components_adapter.get_context_adapter") as mock_get_adapter,
            patch("ui.components_adapter.SessionStateManager") as mock_ssm,
            patch("ui.components_adapter.get_definition_service") as mock_get_service,
        ):
            mock_adapter = MagicMock()
            mock_adapter.get_merged_context.side_effect = AttributeError("test")
            mock_get_adapter.return_value = mock_adapter

            mock_ssm.get_value.side_effect = session_state_getter

            mock_service = MagicMock()
            mock_get_service.return_value = mock_service

            from ui.components_adapter import UIComponentsAdapter

            adapter = UIComponentsAdapter()
            adapter._collect_ui_data_for_export()

            # Assert: st.warning was called
            mock_st.warning.assert_called_once()
            warning_msg = mock_st.warning.call_args[0][0]
            assert "Context kon niet via ContextManager worden opgehaald" in warning_msg
            assert "Fallback" in warning_msg

    def test_context_fallback_shows_warning_on_key_error(self, session_state_getter):
        """Verify st.warning is called for KeyError fallback."""
        with (
            patch("ui.components_adapter.logger"),
            patch("ui.components_adapter.st") as mock_st,
            patch("ui.components_adapter.get_context_adapter") as mock_get_adapter,
            patch("ui.components_adapter.SessionStateManager") as mock_ssm,
            patch("ui.components_adapter.get_definition_service") as mock_get_service,
        ):
            mock_adapter = MagicMock()
            mock_adapter.get_merged_context.side_effect = KeyError("missing_key")
            mock_get_adapter.return_value = mock_adapter

            mock_ssm.get_value.side_effect = session_state_getter

            mock_service = MagicMock()
            mock_get_service.return_value = mock_service

            from ui.components_adapter import UIComponentsAdapter

            adapter = UIComponentsAdapter()
            adapter._collect_ui_data_for_export()

            mock_st.warning.assert_called_once()

    def test_context_fallback_shows_warning_on_type_error(self, session_state_getter):
        """Verify st.warning is called for TypeError fallback."""
        with (
            patch("ui.components_adapter.logger"),
            patch("ui.components_adapter.st") as mock_st,
            patch("ui.components_adapter.get_context_adapter") as mock_get_adapter,
            patch("ui.components_adapter.SessionStateManager") as mock_ssm,
            patch("ui.components_adapter.get_definition_service") as mock_get_service,
        ):
            mock_adapter = MagicMock()
            mock_adapter.get_merged_context.side_effect = TypeError("type mismatch")
            mock_get_adapter.return_value = mock_adapter

            mock_ssm.get_value.side_effect = session_state_getter

            mock_service = MagicMock()
            mock_get_service.return_value = mock_service

            from ui.components_adapter import UIComponentsAdapter

            adapter = UIComponentsAdapter()
            adapter._collect_ui_data_for_export()

            mock_st.warning.assert_called_once()


class TestFallbackUsesCorrectSessionKeys:
    """Test that fallback uses correct session state keys (DEF-252 fix)."""

    def test_fallback_uses_organisatorische_context_key(self):
        """Verify fallback reads 'organisatorische_context' not 'organisatie'."""
        expected_org = ["DJI", "OM", "Rechtspraak"]

        def session_getter(key: str, default: Any = None) -> Any:
            values = {
                "begrip": "test",
                "gegenereerd": "test def",
                "organisatorische_context": expected_org,
                "juridische_context": ["Strafrecht"],
                "wettelijke_basis": ["Test wet"],
            }
            return values.get(key, default)

        with (
            patch("ui.components_adapter.logger"),
            patch("ui.components_adapter.st"),
            patch("ui.components_adapter.get_context_adapter") as mock_get_adapter,
            patch("ui.components_adapter.SessionStateManager") as mock_ssm,
            patch("ui.components_adapter.get_definition_service") as mock_get_service,
        ):
            mock_adapter = MagicMock()
            mock_adapter.get_merged_context.side_effect = AttributeError("test")
            mock_get_adapter.return_value = mock_adapter

            mock_ssm.get_value.side_effect = session_getter

            mock_service = MagicMock()
            mock_get_service.return_value = mock_service

            from ui.components_adapter import UIComponentsAdapter

            adapter = UIComponentsAdapter()
            result = adapter._collect_ui_data_for_export()

            # Verify the correct key was used
            assert result["context_dict"]["organisatorisch"] == expected_org

            # Verify get_value was called with correct key
            calls = [call[0][0] for call in mock_ssm.get_value.call_args_list]
            assert "organisatorische_context" in calls

    def test_fallback_uses_juridische_context_key(self):
        """Verify fallback reads 'juridische_context'."""
        expected_jur = ["Strafrecht", "Bestuursrecht"]

        def session_getter(key: str, default: Any = None) -> Any:
            values = {
                "begrip": "test",
                "gegenereerd": "test def",
                "organisatorische_context": ["DJI"],
                "juridische_context": expected_jur,
                "wettelijke_basis": ["Test wet"],
            }
            return values.get(key, default)

        with (
            patch("ui.components_adapter.logger"),
            patch("ui.components_adapter.st"),
            patch("ui.components_adapter.get_context_adapter") as mock_get_adapter,
            patch("ui.components_adapter.SessionStateManager") as mock_ssm,
            patch("ui.components_adapter.get_definition_service") as mock_get_service,
        ):
            mock_adapter = MagicMock()
            mock_adapter.get_merged_context.side_effect = KeyError("test")
            mock_get_adapter.return_value = mock_adapter

            mock_ssm.get_value.side_effect = session_getter

            mock_service = MagicMock()
            mock_get_service.return_value = mock_service

            from ui.components_adapter import UIComponentsAdapter

            adapter = UIComponentsAdapter()
            result = adapter._collect_ui_data_for_export()

            assert result["context_dict"]["juridisch"] == expected_jur

            calls = [call[0][0] for call in mock_ssm.get_value.call_args_list]
            assert "juridische_context" in calls

    def test_fallback_uses_wettelijke_basis_key(self):
        """Verify fallback reads 'wettelijke_basis'."""
        expected_wet = ["Wetboek van Strafrecht", "Penitentiaire beginselenwet"]

        def session_getter(key: str, default: Any = None) -> Any:
            values = {
                "begrip": "test",
                "gegenereerd": "test def",
                "organisatorische_context": ["DJI"],
                "juridische_context": ["Strafrecht"],
                "wettelijke_basis": expected_wet,
            }
            return values.get(key, default)

        with (
            patch("ui.components_adapter.logger"),
            patch("ui.components_adapter.st"),
            patch("ui.components_adapter.get_context_adapter") as mock_get_adapter,
            patch("ui.components_adapter.SessionStateManager") as mock_ssm,
            patch("ui.components_adapter.get_definition_service") as mock_get_service,
        ):
            mock_adapter = MagicMock()
            mock_adapter.get_merged_context.side_effect = TypeError("test")
            mock_get_adapter.return_value = mock_adapter

            mock_ssm.get_value.side_effect = session_getter

            mock_service = MagicMock()
            mock_get_service.return_value = mock_service

            from ui.components_adapter import UIComponentsAdapter

            adapter = UIComponentsAdapter()
            result = adapter._collect_ui_data_for_export()

            assert result["context_dict"]["wettelijk"] == expected_wet

            calls = [call[0][0] for call in mock_ssm.get_value.call_args_list]
            assert "wettelijke_basis" in calls

    def test_fallback_returns_empty_lists_for_missing_context(self):
        """Verify fallback returns empty lists when session state has no context."""

        def session_getter(key: str, default: Any = None) -> Any:
            values = {
                "begrip": "test",
                "gegenereerd": "test def",
                # No context keys set - should use defaults
            }
            return values.get(key, default)

        with (
            patch("ui.components_adapter.logger"),
            patch("ui.components_adapter.st"),
            patch("ui.components_adapter.get_context_adapter") as mock_get_adapter,
            patch("ui.components_adapter.SessionStateManager") as mock_ssm,
            patch("ui.components_adapter.get_definition_service") as mock_get_service,
        ):
            mock_adapter = MagicMock()
            mock_adapter.get_merged_context.side_effect = AttributeError("test")
            mock_get_adapter.return_value = mock_adapter

            mock_ssm.get_value.side_effect = session_getter

            mock_service = MagicMock()
            mock_get_service.return_value = mock_service

            from ui.components_adapter import UIComponentsAdapter

            adapter = UIComponentsAdapter()
            result = adapter._collect_ui_data_for_export()

            # Should have empty lists, not None
            assert result["context_dict"]["organisatorisch"] == []
            assert result["context_dict"]["juridisch"] == []
            assert result["context_dict"]["wettelijk"] == []


class TestPrimaryPathNoWarningNoLog:
    """Test that happy path does not trigger warning or error log."""

    def test_primary_path_no_warning_no_error_log(self):
        """Verify happy path (ContextAdapter works) doesn't trigger fallback."""
        with (
            patch("ui.components_adapter.logger") as mock_logger,
            patch("ui.components_adapter.st") as mock_st,
            patch("ui.components_adapter.get_context_adapter") as mock_get_adapter,
            patch("ui.components_adapter.SessionStateManager") as mock_ssm,
            patch("ui.components_adapter.get_definition_service") as mock_get_service,
        ):
            # Setup: ContextAdapter works correctly
            mock_adapter = MagicMock()
            mock_adapter.get_merged_context.return_value = {
                "organisatorische_context": ["DJI"],
                "juridische_context": ["Strafrecht"],
                "wettelijke_basis": ["Test wet"],
            }
            mock_get_adapter.return_value = mock_adapter

            # Setup SessionStateManager for non-context fields
            def session_getter(key: str, default: Any = None) -> Any:
                values = {
                    "begrip": "testbegrip",
                    "gegenereerd": "test definitie",
                    "datum": "2024-01-01",
                }
                return values.get(key, default)

            mock_ssm.get_value.side_effect = session_getter

            mock_service = MagicMock()
            mock_get_service.return_value = mock_service

            from ui.components_adapter import UIComponentsAdapter

            adapter = UIComponentsAdapter()
            result = adapter._collect_ui_data_for_export()

            # Assert: No error log for context fallback
            # Note: logger.error may be called elsewhere, so check specific message
            for call in mock_logger.error.call_args_list:
                if call[0]:
                    assert "ContextAdapter fallback" not in call[0][0]

            # Assert: No warning shown
            mock_st.warning.assert_not_called()

            # Assert: Context was retrieved from adapter
            assert result["context_dict"]["organisatorisch"] == ["DJI"]
            assert result["context_dict"]["juridisch"] == ["Strafrecht"]
            assert result["context_dict"]["wettelijk"] == ["Test wet"]

    def test_primary_path_uses_context_adapter(self):
        """Verify primary path uses ContextAdapter.get_merged_context()."""
        with (
            patch("ui.components_adapter.logger"),
            patch("ui.components_adapter.st"),
            patch("ui.components_adapter.get_context_adapter") as mock_get_adapter,
            patch("ui.components_adapter.SessionStateManager") as mock_ssm,
            patch("ui.components_adapter.get_definition_service") as mock_get_service,
        ):
            mock_adapter = MagicMock()
            mock_adapter.get_merged_context.return_value = {
                "organisatorische_context": ["OM"],
                "juridische_context": ["Civiel recht"],
                "wettelijke_basis": ["BW"],
            }
            mock_get_adapter.return_value = mock_adapter

            def session_getter(key: str, default: Any = None) -> Any:
                return {"begrip": "test", "gegenereerd": "def"}.get(key, default)

            mock_ssm.get_value.side_effect = session_getter

            mock_service = MagicMock()
            mock_get_service.return_value = mock_service

            from ui.components_adapter import UIComponentsAdapter

            adapter = UIComponentsAdapter()
            adapter._collect_ui_data_for_export()

            # Verify adapter was called
            mock_adapter.get_merged_context.assert_called_once()


class TestExceptionTypeNarrowing:
    """Test that only specific exception types trigger fallback."""

    def test_value_error_caught_by_fallback(self):
        """Verify ValueError IS caught by fallback (from ContextManager validation)."""
        with (
            patch("ui.components_adapter.logger") as mock_logger,
            patch("ui.components_adapter.st") as mock_st,
            patch("ui.components_adapter.get_context_adapter") as mock_get_adapter,
            patch("ui.components_adapter.SessionStateManager") as mock_ssm,
            patch("ui.components_adapter.get_definition_service") as mock_get_service,
        ):
            mock_adapter = MagicMock()
            mock_adapter.get_merged_context.side_effect = ValueError("validation error")
            mock_get_adapter.return_value = mock_adapter

            def session_getter(key: str, default: Any = None) -> Any:
                values = {
                    "begrip": "test",
                    "gegenereerd": "def",
                    "organisatorische_context": ["DJI"],
                    "juridische_context": [],
                    "wettelijke_basis": [],
                }
                return values.get(key, default)

            mock_ssm.get_value.side_effect = session_getter

            mock_service = MagicMock()
            mock_get_service.return_value = mock_service

            from ui.components_adapter import UIComponentsAdapter

            adapter = UIComponentsAdapter()

            # ValueError SHOULD be caught and trigger fallback
            result = adapter._collect_ui_data_for_export()

            # Verify fallback was triggered
            mock_logger.error.assert_called_once()
            mock_st.warning.assert_called_once()
            assert "context_dict" in result

    def test_runtime_error_not_caught_by_fallback(self):
        """Verify RuntimeError is NOT caught by fallback (re-raised)."""
        with (
            patch("ui.components_adapter.logger"),
            patch("ui.components_adapter.st"),
            patch("ui.components_adapter.get_context_adapter") as mock_get_adapter,
            patch("ui.components_adapter.SessionStateManager") as mock_ssm,
            patch("ui.components_adapter.get_definition_service") as mock_get_service,
        ):
            mock_adapter = MagicMock()
            mock_adapter.get_merged_context.side_effect = RuntimeError("runtime issue")
            mock_get_adapter.return_value = mock_adapter

            def session_getter(key: str, default: Any = None) -> Any:
                return {"begrip": "test", "gegenereerd": "def"}.get(key, default)

            mock_ssm.get_value.side_effect = session_getter

            mock_service = MagicMock()
            mock_get_service.return_value = mock_service

            from ui.components_adapter import UIComponentsAdapter

            adapter = UIComponentsAdapter()

            # RuntimeError should NOT be caught - should propagate
            with pytest.raises(RuntimeError, match="runtime issue"):
                adapter._collect_ui_data_for_export()


class TestContextDictStructure:
    """Test that context_dict has correct structure after fallback."""

    def test_context_dict_has_all_required_keys(self):
        """Verify context_dict contains organisatorisch, juridisch, wettelijk keys."""

        def session_getter(key: str, default: Any = None) -> Any:
            values = {
                "begrip": "test",
                "gegenereerd": "test def",
                "organisatorische_context": ["DJI"],
                "juridische_context": ["Strafrecht"],
                "wettelijke_basis": ["Wet A"],
            }
            return values.get(key, default)

        with (
            patch("ui.components_adapter.logger"),
            patch("ui.components_adapter.st"),
            patch("ui.components_adapter.get_context_adapter") as mock_get_adapter,
            patch("ui.components_adapter.SessionStateManager") as mock_ssm,
            patch("ui.components_adapter.get_definition_service") as mock_get_service,
        ):
            mock_adapter = MagicMock()
            mock_adapter.get_merged_context.side_effect = AttributeError("test")
            mock_get_adapter.return_value = mock_adapter

            mock_ssm.get_value.side_effect = session_getter

            mock_service = MagicMock()
            mock_get_service.return_value = mock_service

            from ui.components_adapter import UIComponentsAdapter

            adapter = UIComponentsAdapter()
            result = adapter._collect_ui_data_for_export()

            # Verify structure matches ContextDict TypedDict
            context_dict = result["context_dict"]
            assert "organisatorisch" in context_dict
            assert "juridisch" in context_dict
            assert "wettelijk" in context_dict

            # Verify all values are lists
            assert isinstance(context_dict["organisatorisch"], list)
            assert isinstance(context_dict["juridisch"], list)
            assert isinstance(context_dict["wettelijk"], list)

    def test_context_dict_values_preserved(self):
        """Verify context values are preserved correctly in fallback."""
        expected_org = ["DJI", "OM", "CJIB"]
        expected_jur = ["Strafrecht", "Bestuursrecht"]
        expected_wet = ["Wetboek van Strafrecht", "Awb"]

        def session_getter(key: str, default: Any = None) -> Any:
            values = {
                "begrip": "test",
                "gegenereerd": "test def",
                "organisatorische_context": expected_org,
                "juridische_context": expected_jur,
                "wettelijke_basis": expected_wet,
            }
            return values.get(key, default)

        with (
            patch("ui.components_adapter.logger"),
            patch("ui.components_adapter.st"),
            patch("ui.components_adapter.get_context_adapter") as mock_get_adapter,
            patch("ui.components_adapter.SessionStateManager") as mock_ssm,
            patch("ui.components_adapter.get_definition_service") as mock_get_service,
        ):
            mock_adapter = MagicMock()
            mock_adapter.get_merged_context.side_effect = KeyError("test")
            mock_get_adapter.return_value = mock_adapter

            mock_ssm.get_value.side_effect = session_getter

            mock_service = MagicMock()
            mock_get_service.return_value = mock_service

            from ui.components_adapter import UIComponentsAdapter

            adapter = UIComponentsAdapter()
            result = adapter._collect_ui_data_for_export()

            context_dict = result["context_dict"]
            assert context_dict["organisatorisch"] == expected_org
            assert context_dict["juridisch"] == expected_jur
            assert context_dict["wettelijk"] == expected_wet


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
