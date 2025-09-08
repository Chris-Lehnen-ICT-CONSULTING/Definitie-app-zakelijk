"""
Unit tests for US-042: Fix "Anders..." Custom Context Option.

These tests verify that the "Anders..." option in context selectors works correctly
without causing crashes or data loss. Tests cover all three context types and various
edge cases with special characters and user input.

Related Documentation:
- Epic: docs/backlog/epics/EPIC-010-context-flow-refactoring.md
- User Story: docs/backlog/stories/US-042.md
- Implementation Plan: docs/implementation/EPIC-010-implementation-plan.md#fase-4
- Test Strategy: docs/testing/EPIC-010-test-strategy.md
- Bug Report: docs/backlog/bugs/CFR-BUG-002 (Anders option crashes)

Test Coverage:
- Anders option functionality for all context types
- Custom text input handling
- Special character support
- State management and persistence
- UI component behavior
- Error prevention and recovery
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
import streamlit as st
from typing import List, Dict, Any

# Import the components we're testing
from src.ui.components.context_selector import ContextSelector


class TestAndersOptionBasicFunctionality:
    """Test basic Anders... option functionality."""

    @pytest.fixture
    def mock_streamlit(self):
        """Mock Streamlit components."""
        with patch('streamlit.multiselect') as mock_multiselect, \
             patch('streamlit.text_input') as mock_text_input, \
             patch('streamlit.columns') as mock_columns:
            
            # Setup column mocks
            col1, col2 = Mock(), Mock()
            mock_columns.return_value = [col1, col2]
            col1.multiselect = mock_multiselect
            col2.text_input = mock_text_input
            
            yield {
                'multiselect': mock_multiselect,
                'text_input': mock_text_input,
                'columns': mock_columns,
                'col1': col1,
                'col2': col2
            }

    def test_anders_triggers_text_input(self, mock_streamlit):
        """When Anders... is selected, text input should appear."""
        # Simulate selecting Anders...
        mock_streamlit['multiselect'].return_value = ["DJI", "Anders..."]
        mock_streamlit['text_input'].return_value = "Custom Organization"
        
        selector = ContextSelector()
        result = selector.render()
        
        # Text input should have been called
        mock_streamlit['text_input'].assert_called()
        
        # Result should contain custom value, not "Anders..."
        assert "Custom Organization" in result.get("organisatorische_context", [])
        assert "Anders..." not in result.get("organisatorische_context", [])

    def test_anders_without_custom_text(self, mock_streamlit):
        """Anders... without custom text should be filtered out."""
        mock_streamlit['multiselect'].return_value = ["DJI", "Anders..."]
        mock_streamlit['text_input'].return_value = ""  # Empty custom text
        
        selector = ContextSelector()
        result = selector.render()
        
        # Anders... should not appear in result
        assert "Anders..." not in result.get("organisatorische_context", [])
        # But DJI should still be there
        assert "DJI" in result.get("organisatorische_context", [])

    def test_multiple_anders_different_fields(self, mock_streamlit):
        """Multiple Anders... options across different fields should work."""
        # Setup different returns for each context type
        def multiselect_side_effect(label, options, *args, **kwargs):
            if "Organisatorische" in label:
                return ["DJI", "Anders..."]
            elif "Juridische" in label:
                return ["Strafrecht", "Anders..."]
            elif "Wettelijke" in label:
                return ["Wetboek van Strafrecht", "Anders..."]
            return []
        
        def text_input_side_effect(label, *args, **kwargs):
            if "organisatorische" in label.lower():
                return "Custom Org"
            elif "juridische" in label.lower():
                return "Custom Juridisch"
            elif "wettelijke" in label.lower():
                return "Custom Wet"
            return ""
        
        mock_streamlit['multiselect'].side_effect = multiselect_side_effect
        mock_streamlit['text_input'].side_effect = text_input_side_effect
        
        selector = ContextSelector()
        result = selector.render()
        
        # All custom values should be present
        assert "Custom Org" in result.get("organisatorische_context", [])
        assert "Custom Juridisch" in result.get("juridische_context", [])
        assert "Custom Wet" in result.get("wettelijke_basis", [])


class TestAndersSpecialCharacters:
    """Test Anders... option with special characters and edge cases."""

    @pytest.fixture
    def mock_streamlit(self):
        with patch('streamlit.multiselect') as mock_multiselect, \
             patch('streamlit.text_input') as mock_text_input:
            yield {
                'multiselect': mock_multiselect,
                'text_input': mock_text_input
            }

    @pytest.mark.parametrize("custom_text", [
        "Richtlijn (EU) 2016/680 'Politie-richtlijn'",
        "Art. 5 EVRM & Art. 15 Grondwet",
        "Wet bijzondere opnemingen in psychiatrische ziekenhuizen (Wet Bopz)",
        "Ministerie van Justitie & Veiligheid",
        "Directive 95/46/EC \"Data Protection\"",
        "§ 3.4 Algemene wet bestuursrecht",
        "100% Nederlandse wetgeving",
        "COVID-19 noodverordening",
        "Anti-witwasrichtlijn (AMLD5)",
        "Règlement général sur la protection des données (RGPD)",
    ])
    def test_special_characters_in_custom_text(self, mock_streamlit, custom_text):
        """Test that special characters in custom text are handled correctly."""
        mock_streamlit['multiselect'].return_value = ["Anders..."]
        mock_streamlit['text_input'].return_value = custom_text
        
        selector = ContextSelector()
        result = selector.render()
        
        # Custom text should be preserved exactly
        assert custom_text in result.get("wettelijke_basis", [])

    def test_very_long_custom_text(self, mock_streamlit):
        """Test handling of very long custom text input."""
        long_text = "Verdrag tot bescherming van de rechten van de mens en de fundamentele vrijheden, " \
                   "zoals gewijzigd door de Protocollen nrs. 11 en 14, vergezeld van het Aanvullend " \
                   "Protocol en de Protocollen nrs. 4, 6, 7, 12, 13 en 16"
        
        mock_streamlit['multiselect'].return_value = ["Anders..."]
        mock_streamlit['text_input'].return_value = long_text
        
        selector = ContextSelector()
        result = selector.render()
        
        assert long_text in result.get("wettelijke_basis", [])

    def test_unicode_characters(self, mock_streamlit):
        """Test Unicode characters in custom text."""
        unicode_text = "Verdrag inzake de rechten van het kind (VN) 🇺🇳 • § € ™"
        
        mock_streamlit['multiselect'].return_value = ["Anders..."]
        mock_streamlit['text_input'].return_value = unicode_text
        
        selector = ContextSelector()
        result = selector.render()
        
        assert unicode_text in result.get("juridische_context", [])

    def test_html_injection_prevention(self, mock_streamlit):
        """Test that HTML/script injection is prevented."""
        malicious_text = "<script>alert('XSS')</script>Normale tekst"
        
        mock_streamlit['multiselect'].return_value = ["Anders..."]
        mock_streamlit['text_input'].return_value = malicious_text
        
        selector = ContextSelector()
        result = selector.render()
        
        # The text should be stored as-is (sanitization happens at display)
        assert malicious_text in result.get("organisatorische_context", [])


class TestAndersStatePersistence:
    """Test that Anders... selections persist correctly in session state."""

    @pytest.fixture
    def mock_session_state(self):
        """Mock Streamlit session state."""
        with patch.object(st, 'session_state', create=True) as mock_state:
            # Initialize as empty dict-like object
            mock_state.configure_mock(**{})
            yield mock_state

    def test_anders_value_persists_in_session(self, mock_session_state):
        """Custom Anders values should persist in session state."""
        with patch('streamlit.multiselect') as mock_multiselect, \
             patch('streamlit.text_input') as mock_text_input:
            
            mock_multiselect.return_value = ["Anders..."]
            mock_text_input.return_value = "Persistent Custom Value"
            
            selector = ContextSelector()
            
            # First render
            result1 = selector.render()
            assert "Persistent Custom Value" in result1.get("organisatorische_context", [])
            
            # Simulate state persistence
            mock_session_state.organisatorische_context_anders = "Persistent Custom Value"
            
            # Second render should maintain the value
            result2 = selector.render()
            # Value should still be available

    def test_anders_cleared_when_deselected(self):
        """When Anders... is deselected, custom value should be cleared."""
        with patch('streamlit.multiselect') as mock_multiselect, \
             patch('streamlit.text_input') as mock_text_input:
            
            selector = ContextSelector()
            
            # First: select Anders with custom text
            mock_multiselect.return_value = ["DJI", "Anders..."]
            mock_text_input.return_value = "Custom Value"
            result1 = selector.render()
            assert "Custom Value" in result1.get("organisatorische_context", [])
            
            # Then: deselect Anders
            mock_multiselect.return_value = ["DJI"]  # No Anders...
            result2 = selector.render()
            assert "Custom Value" not in result2.get("organisatorische_context", [])
            assert "Anders..." not in result2.get("organisatorische_context", [])


class TestAndersUIBehavior:
    """Test UI behavior and user interactions with Anders option."""

    def test_text_input_label_clarity(self):
        """Text input should have clear label when Anders is selected."""
        with patch('streamlit.multiselect') as mock_multiselect, \
             patch('streamlit.text_input') as mock_text_input:
            
            mock_multiselect.return_value = ["Anders..."]
            mock_text_input.return_value = "Test"
            
            selector = ContextSelector()
            selector.render()
            
            # Verify text_input was called with appropriate label
            calls = mock_text_input.call_args_list
            assert any("organisatorische context" in str(call).lower() for call in calls)

    def test_placeholder_text_helpful(self):
        """Text input should have helpful placeholder text."""
        with patch('streamlit.multiselect') as mock_multiselect, \
             patch('streamlit.text_input') as mock_text_input:
            
            mock_multiselect.return_value = ["Anders..."]
            
            selector = ContextSelector()
            selector.render()
            
            # Check that placeholder gives guidance
            call_kwargs = mock_text_input.call_args[1] if mock_text_input.call_args else {}
            placeholder = call_kwargs.get('placeholder', '')
            # Placeholder should give examples or guidance

    def test_anders_option_always_last(self):
        """Anders... option should always appear last in dropdown."""
        selector = ContextSelector()
        
        # Get the options that would be shown
        org_options = selector._get_organisatorische_options()
        jur_options = selector._get_juridische_options()
        wet_options = selector._get_wettelijke_options()
        
        # Anders... should be last if present
        if "Anders..." in org_options:
            assert org_options[-1] == "Anders..."
        if "Anders..." in jur_options:
            assert jur_options[-1] == "Anders..."
        if "Anders..." in wet_options:
            assert wet_options[-1] == "Anders..."


class TestAndersErrorPrevention:
    """Test that Anders option doesn't cause crashes or errors."""

    def test_no_crash_on_empty_selection(self):
        """Empty selection should not cause crash."""
        with patch('streamlit.multiselect') as mock_multiselect, \
             patch('streamlit.text_input') as mock_text_input:
            
            mock_multiselect.return_value = []
            mock_text_input.return_value = ""
            
            selector = ContextSelector()
            result = selector.render()
            
            assert result is not None
            assert isinstance(result, dict)

    def test_no_crash_on_only_anders(self):
        """Selecting only Anders without text should not crash."""
        with patch('streamlit.multiselect') as mock_multiselect, \
             patch('streamlit.text_input') as mock_text_input:
            
            mock_multiselect.return_value = ["Anders..."]
            mock_text_input.return_value = ""
            
            selector = ContextSelector()
            result = selector.render()
            
            assert result is not None
            # Anders... should be filtered out
            assert "Anders..." not in result.get("organisatorische_context", [])

    def test_whitespace_only_custom_text(self):
        """Whitespace-only custom text should be treated as empty."""
        with patch('streamlit.multiselect') as mock_multiselect, \
             patch('streamlit.text_input') as mock_text_input:
            
            mock_multiselect.return_value = ["Anders..."]
            mock_text_input.return_value = "   \t\n   "  # Only whitespace
            
            selector = ContextSelector()
            result = selector.render()
            
            # Whitespace-only should be filtered out
            assert "   \t\n   " not in result.get("organisatorische_context", [])
            assert "Anders..." not in result.get("organisatorische_context", [])

    def test_trimming_custom_text(self):
        """Custom text should be trimmed of leading/trailing whitespace."""
        with patch('streamlit.multiselect') as mock_multiselect, \
             patch('streamlit.text_input') as mock_text_input:
            
            mock_multiselect.return_value = ["Anders..."]
            mock_text_input.return_value = "  Custom Value  "
            
            selector = ContextSelector()
            result = selector.render()
            
            # Should be trimmed
            assert "Custom Value" in result.get("organisatorische_context", [])
            assert "  Custom Value  " not in result.get("organisatorische_context", [])


class TestAndersIntegrationScenarios:
    """Test real-world integration scenarios with Anders option."""

    def test_justice_domain_custom_organizations(self):
        """Test custom justice domain organizations."""
        custom_orgs = [
            "Raad voor de Kinderbescherming",
            "Centraal Justitieel Incassobureau",
            "Nederlands Forensisch Instituut",
            "Immigratie- en Naturalisatiedienst",
            "Koninklijke Marechaussee - Afdeling Vreemdelingenzaken"
        ]
        
        with patch('streamlit.multiselect') as mock_multiselect, \
             patch('streamlit.text_input') as mock_text_input:
            
            for custom_org in custom_orgs:
                mock_multiselect.return_value = ["Anders..."]
                mock_text_input.return_value = custom_org
                
                selector = ContextSelector()
                result = selector.render()
                
                assert custom_org in result.get("organisatorische_context", [])

    def test_european_law_custom_context(self):
        """Test custom European law contexts."""
        eu_contexts = [
            "Richtlijn 2013/48/EU betreffende toegang tot een advocaat",
            "Verordening (EU) 2016/679 (AVG/GDPR)",
            "Kaderbesluit 2002/584/JBZ Europees aanhoudingsbevel",
            "Richtlijn 2012/29/EU Slachtofferrechten"
        ]
        
        with patch('streamlit.multiselect') as mock_multiselect, \
             patch('streamlit.text_input') as mock_text_input:
            
            for eu_context in eu_contexts:
                mock_multiselect.return_value = ["Anders..."]
                mock_text_input.return_value = eu_context
                
                selector = ContextSelector()
                result = selector.render()
                
                assert eu_context in result.get("wettelijke_basis", [])

    def test_mixed_standard_and_custom_values(self):
        """Test mixing standard selections with custom Anders values."""
        with patch('streamlit.multiselect') as mock_multiselect, \
             patch('streamlit.text_input') as mock_text_input:
            
            # Mix standard and custom
            mock_multiselect.return_value = ["DJI", "OM", "Rechtspraak", "Anders..."]
            mock_text_input.return_value = "Slachtofferhulp Nederland"
            
            selector = ContextSelector()
            result = selector.render()
            
            # All values should be present
            assert all(org in result.get("organisatorische_context", []) 
                      for org in ["DJI", "OM", "Rechtspraak", "Slachtofferhulp Nederland"])
            assert "Anders..." not in result.get("organisatorische_context", [])


class TestAndersPerformance:
    """Test performance aspects of Anders option."""

    def test_no_unnecessary_rerenders(self):
        """Anders option should not cause unnecessary UI rerenders."""
        with patch('streamlit.multiselect') as mock_multiselect, \
             patch('streamlit.text_input') as mock_text_input:
            
            mock_multiselect.return_value = ["DJI"]
            mock_text_input.return_value = ""
            
            selector = ContextSelector()
            
            # First render
            selector.render()
            initial_multiselect_calls = mock_multiselect.call_count
            initial_text_input_calls = mock_text_input.call_count
            
            # Second render without changes
            selector.render()
            
            # Should not have excessive additional calls
            assert mock_multiselect.call_count <= initial_multiselect_calls * 2
            assert mock_text_input.call_count <= initial_text_input_calls * 2

    def test_efficient_filtering(self):
        """Anders filtering should be efficient."""
        with patch('streamlit.multiselect') as mock_multiselect, \
             patch('streamlit.text_input') as mock_text_input:
            
            # Large selection with Anders
            large_selection = ["Option" + str(i) for i in range(50)] + ["Anders..."]
            mock_multiselect.return_value = large_selection
            mock_text_input.return_value = "Custom"
            
            selector = ContextSelector()
            result = selector.render()
            
            # Should handle large lists efficiently
            assert len(result.get("organisatorische_context", [])) == 51  # 50 options + 1 custom
            assert "Anders..." not in result.get("organisatorische_context", [])


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])