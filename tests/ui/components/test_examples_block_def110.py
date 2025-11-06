"""
Tests for DEF-110: Stale Voorbeelden Bug Fix

DEF-110 fixes data persistence across definition switches by implementing:
1. force_cleanup_voorbeelden(): Nuclear cleanup of all voorbeelden widget state
2. _reset_voorbeelden_context(): Context tracking with sentinel pattern for None IDs

Integration: Called by definition_edit_tab._render_examples_section() before rendering.

Test Coverage:
- Force cleanup removes all voorbeelden keys but preserves others
- Context reset triggers cleanup on definition change
- Context preserved when definition stays same
- None ID handling with sentinel pattern (generator tab case)
- Transitions between None and saved definitions
"""

from unittest.mock import MagicMock, patch

import pytest

from ui.components.examples_block import _reset_voorbeelden_context
from ui.session_state import force_cleanup_voorbeelden


class TestDEF110StaleVoorbeeldenFix:
    """Tests for DEF-110 stale voorbeelden bug fix."""

    @pytest.fixture()
    def mock_session_state(self):
        """Mock Streamlit session state with voorbeelden keys and control keys."""
        return {
            # Voorbeelden widget keys (should be cleaned)
            "test_vz_edit": "voorbeeld 1\nvoorbeeld 2",
            "test_pv_edit": "praktijk 1\npraktijk 2",
            "test_tv_edit": "tegen 1",
            "test_syn_edit": "synoniem1, synoniem2",
            "test_ant_edit": "antoniem1, antoniem2",
            "test_tol_edit": "Toelichting tekst",
            "test_examples": {"voorbeeldzinnen": ["v1", "v2"]},
            # Control keys (should NOT be cleaned)
            "other_key": "preserved",
            "test_definitie": "Some definition text",
            "unrelated_vz_key": "This should stay (no prefix match)",
        }

    @pytest.fixture()
    def mock_session_state_manager(self):
        """Mock SessionStateManager for context tracking."""
        with patch("ui.components.examples_block.SessionStateManager") as mock:
            # Store context in dict for testing
            context_storage = {}

            def get_value(key, default=None):
                return context_storage.get(key, default)

            def set_value(key, value):
                context_storage[key] = value

            mock.get_value.side_effect = get_value
            mock.set_value.side_effect = set_value

            yield mock, context_storage

    def test_force_cleanup_removes_all_voorbeelden_keys(self, mock_session_state):
        """Test that _force_cleanup removes all voorbeelden keys but preserves others."""
        with patch("streamlit.session_state", mock_session_state):
            # Execute cleanup
            force_cleanup_voorbeelden("test")

            # Assert: All voorbeelden keys removed
            assert "test_vz_edit" not in mock_session_state
            assert "test_pv_edit" not in mock_session_state
            assert "test_tv_edit" not in mock_session_state
            assert "test_syn_edit" not in mock_session_state
            assert "test_ant_edit" not in mock_session_state
            assert "test_tol_edit" not in mock_session_state
            assert "test_examples" not in mock_session_state

            # Assert: Control keys preserved
            assert "other_key" in mock_session_state
            assert mock_session_state["other_key"] == "preserved"
            assert "test_definitie" in mock_session_state
            assert "unrelated_vz_key" in mock_session_state

    def test_force_cleanup_handles_already_deleted_keys(self, mock_session_state):
        """Test that cleanup handles KeyError gracefully for already-deleted keys."""
        with patch("streamlit.session_state", mock_session_state):
            # Delete some keys manually first
            del mock_session_state["test_vz_edit"]
            del mock_session_state["test_syn_edit"]

            # Should not raise exception
            force_cleanup_voorbeelden("test")

            # Assert: Remaining voorbeelden keys cleaned
            assert "test_pv_edit" not in mock_session_state
            assert "test_examples" not in mock_session_state

            # Assert: Control keys preserved
            assert "other_key" in mock_session_state

    def test_reset_context_triggers_cleanup_on_definition_change(
        self, mock_session_state_manager
    ):
        """Test that context reset triggers cleanup when definition_id changes."""
        _mock_ssm, context_storage = mock_session_state_manager

        # Setup: Initial context for definition 106
        context_storage["test_context_id"] = 106

        with patch(
            "ui.components.examples_block.force_cleanup_voorbeelden"
        ) as mock_cleanup:
            # Execute: Switch to definition 105
            _reset_voorbeelden_context("test", definition_id=105)

            # Assert: Cleanup was called
            mock_cleanup.assert_called_once_with("test")

            # Assert: New context stored
            assert context_storage["test_context_id"] == 105

    def test_reset_context_preserves_same_definition(self, mock_session_state_manager):
        """Test that context reset does NOT trigger cleanup for same definition."""
        _mock_ssm, context_storage = mock_session_state_manager

        # Setup: Initial context for definition 106
        context_storage["test_context_id"] = 106

        with patch(
            "ui.components.examples_block.force_cleanup_voorbeelden"
        ) as mock_cleanup:
            # Execute: "Switch" to same definition 106
            _reset_voorbeelden_context("test", definition_id=106)

            # Assert: Cleanup NOT called (same definition)
            mock_cleanup.assert_not_called()

            # Assert: Context unchanged
            assert context_storage["test_context_id"] == 106

    def test_reset_context_handles_none_ids_correctly(self, mock_session_state_manager):
        """Test that None IDs use sentinel pattern correctly (no false positives)."""
        _mock_ssm, context_storage = mock_session_state_manager

        # Setup: Initial context with None (generator tab)
        context_storage["test_context_id"] = None

        with patch(
            "ui.components.examples_block.force_cleanup_voorbeelden"
        ) as mock_cleanup:
            # Execute: Reset with None again
            _reset_voorbeelden_context("test", definition_id=None)

            # Assert: Cleanup NOT called (None == None, same context)
            mock_cleanup.assert_not_called()

            # Assert: Context unchanged
            assert context_storage["test_context_id"] is None

    def test_reset_context_switches_from_none_to_saved_definition(
        self, mock_session_state_manager
    ):
        """Test that switching from None to saved definition triggers cleanup."""
        _mock_ssm, context_storage = mock_session_state_manager

        # Setup: Initial context with None (unsaved definition in generator tab)
        context_storage["test_context_id"] = None

        with patch(
            "ui.components.examples_block.force_cleanup_voorbeelden"
        ) as mock_cleanup:
            # Execute: Switch to saved definition 106
            _reset_voorbeelden_context("test", definition_id=106)

            # Assert: Cleanup WAS called (None → 106 is a change)
            mock_cleanup.assert_called_once_with("test")

            # Assert: New context stored
            assert context_storage["test_context_id"] == 106

    def test_reset_context_switches_from_saved_to_none(
        self, mock_session_state_manager
    ):
        """Test that switching from saved definition to None triggers cleanup."""
        _mock_ssm, context_storage = mock_session_state_manager

        # Setup: Initial context with saved definition
        context_storage["test_context_id"] = 106

        with patch(
            "ui.components.examples_block.force_cleanup_voorbeelden"
        ) as mock_cleanup:
            # Execute: Switch to None (new unsaved definition)
            _reset_voorbeelden_context("test", definition_id=None)

            # Assert: Cleanup WAS called (106 → None is a change)
            mock_cleanup.assert_called_once_with("test")

            # Assert: New context stored
            assert context_storage["test_context_id"] is None

    def test_reset_context_handles_first_initialization(
        self, mock_session_state_manager
    ):
        """Test that first initialization triggers cleanup (sentinel → definition)."""
        _mock_ssm, context_storage = mock_session_state_manager

        # Setup: No context stored (first time)
        # context_storage is empty

        with patch(
            "ui.components.examples_block.force_cleanup_voorbeelden"
        ) as mock_cleanup:
            # Execute: First initialization with definition 106
            _reset_voorbeelden_context("test", definition_id=106)

            # Assert: Cleanup WAS called (sentinel → 106 is a change)
            mock_cleanup.assert_called_once_with("test")

            # Assert: Context stored
            assert context_storage["test_context_id"] == 106

    def test_force_cleanup_handles_empty_session_state(self):
        """Test that cleanup handles empty session state gracefully."""
        empty_state = {}

        with patch("streamlit.session_state", empty_state):
            # Should not raise exception
            force_cleanup_voorbeelden("test")

            # Assert: State still empty
            assert len(empty_state) == 0

    def test_force_cleanup_only_targets_specified_prefix(self, mock_session_state):
        """Test that cleanup only removes keys for specified prefix."""
        # Add keys for different prefix
        mock_session_state["other_vz_edit"] = "other voorbeelden"
        mock_session_state["other_examples"] = {"voorbeeldzinnen": ["v1"]}

        with patch("streamlit.session_state", mock_session_state):
            # Execute: Cleanup only "test" prefix
            force_cleanup_voorbeelden("test")

            # Assert: "test" prefix cleaned
            assert "test_vz_edit" not in mock_session_state
            assert "test_examples" not in mock_session_state

            # Assert: "other" prefix preserved
            assert "other_vz_edit" in mock_session_state
            assert mock_session_state["other_vz_edit"] == "other voorbeelden"
            assert "other_examples" in mock_session_state

    def test_reset_context_with_complex_definition_id_sequence(
        self, mock_session_state_manager
    ):
        """Test context tracking through realistic definition switching sequence."""
        _mock_ssm, context_storage = mock_session_state_manager

        with patch(
            "ui.components.examples_block.force_cleanup_voorbeelden"
        ) as mock_cleanup:
            # Sequence: None → 105 → 105 → 106 → None → 105
            transitions = [
                (None, True),  # First init: sentinel → None (cleanup)
                (105, True),  # None → 105 (cleanup)
                (105, False),  # 105 → 105 (no cleanup)
                (106, True),  # 105 → 106 (cleanup)
                (None, True),  # 106 → None (cleanup)
                (105, True),  # None → 105 (cleanup)
            ]

            cleanup_count = 0
            for definition_id, should_cleanup in transitions:
                _reset_voorbeelden_context("test", definition_id=definition_id)

                if should_cleanup:
                    cleanup_count += 1
                    assert (
                        mock_cleanup.call_count == cleanup_count
                    ), f"Expected cleanup for transition to {definition_id}"
                else:
                    assert (
                        mock_cleanup.call_count == cleanup_count
                    ), f"Unexpected cleanup for transition to {definition_id}"

                # Verify context updated
                assert context_storage["test_context_id"] == definition_id

            # Final assertion: Total cleanups = 5 (all transitions except 105→105)
            assert mock_cleanup.call_count == 5
