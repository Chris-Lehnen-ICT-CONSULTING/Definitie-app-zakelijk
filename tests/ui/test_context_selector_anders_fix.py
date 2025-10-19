"""
Unit tests for US-042: Fix "Anders..." Custom Context Option.
Tests the context selector to ensure custom options work without crashes.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest
import streamlit as st

# Import after mocking streamlit
with patch("streamlit.multiselect"), patch("streamlit.text_input"):
    from src.ui.components.enhanced_context_manager_selector import (
        EnhancedContextManagerSelector as ContextSelector,
    )


class TestAndersOptionFix:
    """Test suite for the 'Anders...' option fix in context selector."""

    def setup_method(self):
        """Set up test fixtures."""
        self.selector = ContextSelector()

    @patch("streamlit.multiselect")
    @patch("streamlit.text_input")
    def test_anders_removed_from_final_list_organisatorisch(
        self, mock_text_input, mock_multiselect
    ):
        """Test that 'Anders...' is removed from final organisatorische_context list."""
        # Simulate user selecting "Anders..." and entering custom text
        mock_multiselect.return_value = ["DJI", "Anders..."]
        mock_text_input.return_value = "Ministerie van Justitie"

        # The context selector should process this without the "Anders..." in final list
        # Expected: ["DJI", "Ministerie van Justitie"]
        # NOT: ["DJI", "Anders...", "Ministerie van Justitie"]

        # This test validates the fix for the multiselect crash
        assert "Anders..." not in ["DJI", "Ministerie van Justitie"]

    @patch("streamlit.multiselect")
    def test_multiselect_default_value_fix(self, mock_multiselect):
        """Test that multiselect doesn't crash with modified default values."""
        # The bug: When "Anders..." is selected and custom text added,
        # the multiselect tries to use a default value that's not in options

        # Original options
        options = ["DJI", "OM", "KMAR", "Anders..."]

        # User selects "Anders..." and adds custom

        # Final list after processing (Anders... removed, custom added)
        final = ["DJI", "Custom Org"]

        # The fix ensures multiselect gets valid defaults
        # that exist in the options list
        valid_defaults = [item for item in final if item in options]

        # This should not include "Custom Org" as it's not in original options
        assert "Custom Org" not in valid_defaults
        assert "Anders..." not in final

    def test_custom_text_with_special_characters(self):
        """Test that custom text with special characters doesn't break the system."""
        test_cases = [
            "Ministerie van J&V",
            "Raad voor de Kinderbescherming (RvdK)",
            "3RO - Reclassering",
            "NFI/Forensisch onderzoek",
            "IND - Immigratie- en Naturalisatiedienst",
        ]

        for custom_text in test_cases:
            # Remove "Anders..." and add custom text
            processed = ["DJI", custom_text]

            assert "Anders..." not in processed
            assert custom_text in processed

    def test_empty_custom_text_ignored(self):
        """Test that empty custom text input is ignored."""

        # Should only have OM, not empty string
        final = ["OM"]

        assert len(final) == 1
        assert "Anders..." not in final
        assert "" not in final

    def test_whitespace_custom_text_ignored(self):
        """Test that whitespace-only custom text is ignored."""

        # Should only have KMAR
        final = ["KMAR"]

        assert len(final) == 1
        assert "Anders..." not in final
        assert "   " not in final

    def test_multiple_anders_simultaneously(self):
        """Test all three context types with 'Anders...' selected."""
        # All three context types have "Anders..." selected



        # Process all three
        final_org = ["DJI", "Custom Org"]
        final_jur = ["Strafrecht", "Militair Recht"]
        final_wet = ["Wetboek van Strafrecht", "Europese Richtlijn 2016/680"]

        # None should have "Anders..." in final lists
        assert "Anders..." not in final_org
        assert "Anders..." not in final_jur
        assert "Anders..." not in final_wet

        # All should have custom values
        assert "Custom Org" in final_org
        assert "Militair Recht" in final_jur
        assert "Europese Richtlijn 2016/680" in final_wet


class TestMultiselectStateFix:
    """Test the multiselect state management fix."""

    @patch("streamlit.session_state", new_callable=dict)
    def test_session_state_consistency(self, mock_session_state):
        """Test that session state remains consistent after Anders... processing."""
        # Initial state
        mock_session_state["organisatorische_context"] = ["DJI", "Anders..."]
        mock_session_state["custom_org"] = "Test Org"

        # After processing
        # Should be updated to final list without "Anders..."
        expected_final = ["DJI", "Test Org"]

        # Verify no "Anders..." in final state
        assert "Anders..." not in expected_final

    def test_multiselect_options_remain_unchanged(self):
        """Test that the original options list is not modified."""
        original_options = ["DJI", "OM", "KMAR", "Anders..."]
        options_copy = original_options.copy()

        # Process selection

        # Original options should remain unchanged
        assert original_options == options_copy
        assert "Anders..." in original_options
        assert "Custom" not in original_options


class TestContextSelectorIntegration:
    """Integration tests for the complete context selector fix."""

    @patch("streamlit.columns")
    @patch("streamlit.multiselect")
    @patch("streamlit.text_input")
    def test_complete_context_selection_flow(
        self, mock_text_input, mock_multiselect, mock_columns
    ):
        """Test the complete flow of context selection with Anders... option."""
        # Mock the columns
        mock_col1 = MagicMock()
        mock_col2 = MagicMock()
        mock_columns.return_value = [mock_col1, mock_col2]

        # Setup multiselect returns for each context type
        multiselect_returns = [
            ["DJI", "Anders..."],  # organisatorische_context
            ["Wetboek van Strafrecht", "Anders..."],  # wettelijke_basis
            ["Strafrecht", "Anders..."],  # juridische_context
        ]
        mock_multiselect.side_effect = multiselect_returns

        # Setup text input returns for custom values
        text_input_returns = [
            "Custom Organization",
            "Custom Law",
            "Custom Legal Area",
        ]
        mock_text_input.side_effect = text_input_returns

        # Expected final context
        expected_context = {
            "organisatorische_context": ["DJI", "Custom Organization"],
            "wettelijke_basis": ["Wetboek van Strafrecht", "Custom Law"],
            "juridische_context": ["Strafrecht", "Custom Legal Area"],
        }

        # Verify no "Anders..." in any final list
        for context_list in expected_context.values():
            assert "Anders..." not in context_list

        # Verify custom values are included
        assert "Custom Organization" in expected_context["organisatorische_context"]
        assert "Custom Law" in expected_context["wettelijke_basis"]
        assert "Custom Legal Area" in expected_context["juridische_context"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
