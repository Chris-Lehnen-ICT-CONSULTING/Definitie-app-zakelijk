"""
Tests for DEF-237 Status Flags Pattern.

Tests cover:
- GenerationStatus: workflow status tracking
- EditSessionStatus: edit session tracking with race detection
"""

from unittest.mock import MagicMock, patch

import pytest


class TestGenerationStatus:
    """Tests for GenerationStatus class."""

    @pytest.fixture
    def mock_session_state(self):
        """Create isolated mock for SessionStateManager."""
        state_dict = {}

        def get_value(key, default=None):
            return state_dict.get(key, default)

        def set_value(key, value):
            state_dict[key] = value

        def clear_value(key):
            state_dict.pop(key, None)

        with patch("ui.status_flags.SessionStateManager") as mock:
            mock.get_value = MagicMock(side_effect=get_value)
            mock.set_value = MagicMock(side_effect=set_value)
            mock.clear_value = MagicMock(side_effect=clear_value)
            mock._state = state_dict  # Expose for assertions
            yield mock

    def test_initial_state_is_idle(self, mock_session_state):
        """Default state should be IDLE."""
        from ui.status_flags import GenerationState, GenerationStatus

        assert GenerationStatus.get_state() == GenerationState.IDLE
        assert GenerationStatus.is_idle() is True
        assert GenerationStatus.is_busy() is False

    def test_start_check_sets_checking_state(self, mock_session_state):
        """start_check should set CHECKING state."""
        from ui.status_flags import GenerationState, GenerationStatus

        GenerationStatus.start_check("Kwaliteit")

        assert mock_session_state._state["generation_status"] == "checking"
        assert mock_session_state._state["current_begrip"] == "Kwaliteit"

    def test_start_generation_sets_generating_state(self, mock_session_state):
        """start_generation should set GENERATING state."""
        from ui.status_flags import GenerationState, GenerationStatus

        GenerationStatus.start_generation("Kwaliteit", options={"force": True})

        assert mock_session_state._state["generation_status"] == "generating"
        assert mock_session_state._state["current_begrip"] == "Kwaliteit"
        assert mock_session_state._state["generation_options"] == {"force": True}

    def test_mark_complete_sets_complete_state(self, mock_session_state):
        """mark_complete should set COMPLETE state with result."""
        from ui.status_flags import GenerationState, GenerationStatus

        result = {"definitie": "Test definitie"}
        GenerationStatus.mark_complete(result)

        assert mock_session_state._state["generation_status"] == "complete"
        assert mock_session_state._state["last_generation_result"] == result

    def test_mark_error_sets_error_state(self, mock_session_state):
        """mark_error should set ERROR state with message."""
        from ui.status_flags import GenerationState, GenerationStatus

        GenerationStatus.mark_error("API timeout")

        assert mock_session_state._state["generation_status"] == "error"
        assert mock_session_state._state["generation_error"] == "API timeout"

    def test_is_busy_during_generation(self, mock_session_state):
        """is_busy should return True during generation states."""
        from ui.status_flags import GenerationStatus

        GenerationStatus.start_generation("Test")

        assert GenerationStatus.is_busy() is True
        assert GenerationStatus.is_idle() is False

    def test_is_idle_after_complete(self, mock_session_state):
        """is_idle should return True after completion."""
        from ui.status_flags import GenerationStatus

        GenerationStatus.start_generation("Test")
        GenerationStatus.mark_complete({"result": "ok"})

        assert GenerationStatus.is_idle() is True
        assert GenerationStatus.is_busy() is False

    def test_is_idle_after_error(self, mock_session_state):
        """is_idle should return True after error."""
        from ui.status_flags import GenerationStatus

        GenerationStatus.start_generation("Test")
        GenerationStatus.mark_error("Failed")

        assert GenerationStatus.is_idle() is True

    def test_reset_clears_all_state(self, mock_session_state):
        """reset should clear all generation state."""
        from ui.status_flags import GenerationStatus

        GenerationStatus.start_generation("Test", options={"force": True})
        GenerationStatus.mark_complete({"result": "ok"})
        GenerationStatus.reset()

        assert mock_session_state._state.get("generation_status") is None
        assert mock_session_state._state.get("current_begrip") is None
        assert mock_session_state._state.get("last_generation_result") is None

    def test_auto_trigger_flag(self, mock_session_state):
        """Auto trigger flag should be settable and clearable."""
        from ui.status_flags import GenerationStatus

        assert GenerationStatus.should_trigger_auto() is False

        GenerationStatus.set_trigger_auto(True)
        assert GenerationStatus.should_trigger_auto() is True

        GenerationStatus.set_trigger_auto(False)
        assert GenerationStatus.should_trigger_auto() is False

    def test_get_current_begrip(self, mock_session_state):
        """get_current_begrip should return current begrip being processed."""
        from ui.status_flags import GenerationStatus

        assert GenerationStatus.get_current_begrip() is None

        GenerationStatus.start_generation("Kwaliteit")
        assert GenerationStatus.get_current_begrip() == "Kwaliteit"

    def test_unknown_status_defaults_to_idle(self, mock_session_state):
        """Unknown status values should default to IDLE."""
        from ui.status_flags import GenerationState, GenerationStatus

        mock_session_state._state["generation_status"] = "unknown_state"
        assert GenerationStatus.get_state() == GenerationState.IDLE


class TestEditSessionStatus:
    """Tests for EditSessionStatus class."""

    @pytest.fixture
    def mock_session_state(self):
        """Create isolated mock for SessionStateManager."""
        state_dict = {}

        def get_value(key, default=None):
            return state_dict.get(key, default)

        def set_value(key, value):
            state_dict[key] = value

        def clear_value(key):
            state_dict.pop(key, None)

        with patch("ui.status_flags.SessionStateManager") as mock:
            mock.get_value = MagicMock(side_effect=get_value)
            mock.set_value = MagicMock(side_effect=set_value)
            mock.clear_value = MagicMock(side_effect=clear_value)
            mock._state = state_dict
            yield mock

    def test_initial_state_is_idle(self, mock_session_state):
        """Default state should be IDLE."""
        from ui.status_flags import EditSessionStatus, EditState

        assert EditSessionStatus.get_state() == EditState.IDLE
        assert EditSessionStatus.is_idle() is True
        assert EditSessionStatus.is_editing() is False

    def test_start_load_sets_loading_state(self, mock_session_state):
        """start_load should set LOADING state and return version."""
        from ui.status_flags import EditSessionStatus, EditState

        version = EditSessionStatus.start_load(definition_id=123)

        assert mock_session_state._state["edit_session_status"] == "loading"
        assert mock_session_state._state["editing_definition_id"] == 123
        assert mock_session_state._state["edit_load_version"] == 1
        assert version == 1

    def test_start_load_increments_version(self, mock_session_state):
        """Each start_load should increment version."""
        from ui.status_flags import EditSessionStatus

        v1 = EditSessionStatus.start_load(123)
        v2 = EditSessionStatus.start_load(456)

        assert v1 == 1
        assert v2 == 2
        assert mock_session_state._state["edit_load_version"] == 2

    def test_check_load_version_detects_concurrent_load(self, mock_session_state):
        """check_load_version should detect when another load started."""
        from ui.status_flags import EditSessionStatus

        v1 = EditSessionStatus.start_load(123)
        # Simulate concurrent load
        EditSessionStatus.start_load(456)

        assert EditSessionStatus.check_load_version(v1) is False

    def test_check_load_version_passes_without_concurrent(self, mock_session_state):
        """check_load_version should pass when no concurrent load."""
        from ui.status_flags import EditSessionStatus

        v1 = EditSessionStatus.start_load(123)

        assert EditSessionStatus.check_load_version(v1) is True

    def test_mark_loaded_sets_editing_state(self, mock_session_state):
        """mark_loaded should set EDITING state with definition."""
        from ui.status_flags import EditSessionStatus, EditState

        definition = MagicMock(id=123)
        session = {"success": True, "definition": definition}

        EditSessionStatus.mark_loaded(definition, session)

        assert mock_session_state._state["edit_session_status"] == "editing"
        assert mock_session_state._state["editing_definition"] == definition
        assert mock_session_state._state["edit_session"] == session

    def test_is_editing_during_active_session(self, mock_session_state):
        """is_editing should return True during active edit states."""
        from ui.status_flags import EditSessionStatus

        EditSessionStatus.start_load(123)
        assert EditSessionStatus.is_editing() is True

        EditSessionStatus.mark_loaded(MagicMock(), {})
        assert EditSessionStatus.is_editing() is True

    def test_has_active_definition(self, mock_session_state):
        """has_active_definition should check if definition ID is set."""
        from ui.status_flags import EditSessionStatus

        assert EditSessionStatus.has_active_definition() is False

        EditSessionStatus.start_load(123)
        assert EditSessionStatus.has_active_definition() is True

    def test_mark_saved_updates_state(self, mock_session_state):
        """mark_saved should update state and timestamp."""
        from datetime import datetime

        from ui.status_flags import EditSessionStatus, EditState

        EditSessionStatus.mark_saved()

        # Should end up in EDITING state after brief SAVED indicator
        assert mock_session_state._state["edit_session_status"] == "editing"
        # Timestamp should be set (just check it's a datetime instance)
        assert isinstance(mock_session_state._state["last_auto_save"], datetime)

    def test_reset_clears_session_but_keeps_version(self, mock_session_state):
        """reset should clear session state but keep version counter."""
        from ui.status_flags import EditSessionStatus

        v1 = EditSessionStatus.start_load(123)
        EditSessionStatus.mark_loaded(MagicMock(), {})
        EditSessionStatus.reset()

        assert mock_session_state._state.get("edit_session_status") is None
        assert mock_session_state._state.get("editing_definition_id") is None
        # Version should NOT be cleared - keeps incrementing for race detection
        assert mock_session_state._state.get("edit_load_version") == v1

    def test_get_definition_id(self, mock_session_state):
        """get_definition_id should return current definition ID."""
        from ui.status_flags import EditSessionStatus

        assert EditSessionStatus.get_definition_id() is None

        EditSessionStatus.start_load(456)
        assert EditSessionStatus.get_definition_id() == 456

    def test_unknown_status_defaults_to_idle(self, mock_session_state):
        """Unknown status values should default to IDLE."""
        from ui.status_flags import EditSessionStatus, EditState

        mock_session_state._state["edit_session_status"] = "unknown_state"
        assert EditSessionStatus.get_state() == EditState.IDLE


class TestGenerationStatusIntegration:
    """Integration-style tests for GenerationStatus workflow."""

    @pytest.fixture
    def mock_session_state(self):
        """Create isolated mock for SessionStateManager."""
        state_dict = {}

        def get_value(key, default=None):
            return state_dict.get(key, default)

        def set_value(key, value):
            state_dict[key] = value

        def clear_value(key):
            state_dict.pop(key, None)

        with patch("ui.status_flags.SessionStateManager") as mock:
            mock.get_value = MagicMock(side_effect=get_value)
            mock.set_value = MagicMock(side_effect=set_value)
            mock.clear_value = MagicMock(side_effect=clear_value)
            mock._state = state_dict
            yield mock

    def test_full_successful_workflow(self, mock_session_state):
        """Test complete successful generation workflow."""
        from ui.status_flags import GenerationState, GenerationStatus

        # Initial state
        assert GenerationStatus.is_idle()

        # Start check
        GenerationStatus.start_check("Kwaliteit")
        assert GenerationStatus.get_state() == GenerationState.CHECKING
        assert GenerationStatus.is_busy()

        # Check complete (no duplicates)
        GenerationStatus.mark_check_complete({"action": "proceed"})
        assert GenerationStatus.is_idle()
        assert GenerationStatus.get_check_result() == {"action": "proceed"}

        # Start generation
        GenerationStatus.start_generation("Kwaliteit")
        assert GenerationStatus.get_state() == GenerationState.GENERATING
        assert GenerationStatus.is_busy()

        # Validation
        GenerationStatus.start_validation()
        assert GenerationStatus.get_state() == GenerationState.VALIDATING

        # Complete
        result = {"definitie": "Test definitie", "score": 0.9}
        GenerationStatus.mark_complete(result)
        assert GenerationStatus.get_state() == GenerationState.COMPLETE
        assert GenerationStatus.get_result() == result
        assert GenerationStatus.is_idle()

    def test_workflow_with_error(self, mock_session_state):
        """Test generation workflow that encounters an error."""
        from ui.status_flags import GenerationState, GenerationStatus

        GenerationStatus.start_generation("Kwaliteit")
        assert GenerationStatus.is_busy()

        GenerationStatus.mark_error("API rate limit exceeded")
        assert GenerationStatus.get_state() == GenerationState.ERROR
        assert GenerationStatus.get_error() == "API rate limit exceeded"
        assert GenerationStatus.is_idle()  # Error is considered idle for retry


class TestRaceConditionScenarios:
    """Tests specifically for DEF-236 race condition detection."""

    @pytest.fixture
    def mock_session_state(self):
        """Create isolated mock for SessionStateManager."""
        state_dict = {}

        def get_value(key, default=None):
            return state_dict.get(key, default)

        def set_value(key, value):
            state_dict[key] = value

        def clear_value(key):
            state_dict.pop(key, None)

        with patch("ui.status_flags.SessionStateManager") as mock:
            mock.get_value = MagicMock(side_effect=get_value)
            mock.set_value = MagicMock(side_effect=set_value)
            mock.clear_value = MagicMock(side_effect=clear_value)
            mock._state = state_dict
            yield mock

    def test_rapid_definition_switches(self, mock_session_state):
        """Test rapid switching between definitions (simulates user clicking fast)."""
        from ui.status_flags import EditSessionStatus

        # User clicks definition 1
        v1 = EditSessionStatus.start_load(definition_id=1)

        # Before first load completes, user clicks definition 2
        v2 = EditSessionStatus.start_load(definition_id=2)

        # Before second load completes, user clicks definition 3
        v3 = EditSessionStatus.start_load(definition_id=3)

        # Only v3 should be valid
        assert EditSessionStatus.check_load_version(v1) is False
        assert EditSessionStatus.check_load_version(v2) is False
        assert EditSessionStatus.check_load_version(v3) is True

    def test_version_persists_across_reset(self, mock_session_state):
        """Version counter should persist even after reset to prevent stale loads."""
        from ui.status_flags import EditSessionStatus

        v1 = EditSessionStatus.start_load(1)
        EditSessionStatus.reset()

        # After reset, a new load should still increment
        v2 = EditSessionStatus.start_load(2)
        assert v2 == v1 + 1  # Version should continue incrementing
