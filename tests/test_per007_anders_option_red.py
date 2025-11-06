"""
PER-007 RED Phase Tests: Custom "Anders..." Entry Tests
Tests for custom 'Anders...' option - MUST fail initially to prove the feature is broken.
"""

from unittest.mock import Mock, patch

import pytest
import streamlit as st
from services.definition_generator_context import HybridContextManager
from services.interfaces import GenerationRequest


class TestAndersOption:
    """Tests for custom 'Anders...' option - MUST fail initially"""

    @pytest.mark.red_phase()
    def test_anders_in_organisatorische_context(self):
        """MUST FAIL: Anders option currently crashes"""
        # GIVEN: User selects "Anders..." and enters custom text
        request = GenerationRequest(
            begrip="test", organisatorische_context=["OM", "Anders...", "CustomOrg"]
        )

        # WHEN: Processing the request
        manager = HybridContextManager()
        context = manager._build_base_context(request)

        # THEN: Should handle gracefully
        # This will FAIL - Anders not handled properly
        assert (
            "CustomOrg" in context["organisatorisch"]
        ), "Custom organization not preserved"
        assert (
            "Anders..." not in context["organisatorisch"]
        ), "Anders... marker should be removed after processing"

    @pytest.mark.red_phase()
    def test_anders_with_empty_custom_value(self):
        """MUST FAIL: Empty Anders value currently crashes"""
        # GIVEN: Anders selected but no custom value entered
        request = GenerationRequest(
            begrip="test", juridische_context=["Strafrecht", "Anders...", ""]
        )

        # WHEN: Processing
        manager = HybridContextManager()

        # THEN: Should handle empty gracefully
        # This will FAIL - empty values not handled
        context = manager._build_base_context(request)
        assert "Anders..." not in context["juridisch"], "Anders... should be removed"
        assert "" not in context["juridisch"], "Empty strings should be filtered out"
        assert "Strafrecht" in context["juridisch"], "Valid values should remain"

    @pytest.mark.red_phase()
    def test_anders_preserves_order(self):
        """MUST FAIL: Order not preserved with Anders option"""
        # GIVEN: Specific order with Anders in middle
        request = GenerationRequest(
            begrip="test",
            organisatorische_context=["OM", "Anders...", "CustomOrg", "DJI"],
        )

        # WHEN: Processing
        manager = HybridContextManager()
        context = manager._build_base_context(request)

        # THEN: Order should be preserved (minus Anders)
        # This will FAIL - order not maintained
        expected = ["OM", "CustomOrg", "DJI"]
        assert (
            context["organisatorisch"] == expected
        ), f"Order not preserved. Got {context['organisatorisch']}, expected {expected}"

    @pytest.mark.red_phase()
    def test_anders_with_multiple_custom_entries(self):
        """MUST FAIL: Multiple custom entries not handled"""
        # GIVEN: Multiple Anders entries
        request = GenerationRequest(
            begrip="test",
            juridische_context=[
                "Strafrecht",
                "Anders...",
                "CustomDomain1",
                "Bestuursrecht",
                "Anders...",
                "CustomDomain2",
            ],
        )

        # WHEN: Processing
        manager = HybridContextManager()
        context = manager._build_base_context(request)

        # THEN: All custom entries preserved, all Anders removed
        # This will FAIL - multiple Anders not handled
        expected = ["Strafrecht", "CustomDomain1", "Bestuursrecht", "CustomDomain2"]
        assert (
            context["juridisch"] == expected
        ), "Multiple custom entries not handled correctly"

    @pytest.mark.red_phase()
    def test_anders_preserves_session_state(self):
        """MUST FAIL: Custom entries not preserved in session"""
        # GIVEN: Custom entry via Anders
        custom_org = "Bijzondere Eenheid X"

        # Simulate Streamlit session state
        if "custom_organisations" not in st.session_state:
            st.session_state.custom_organisations = []

        # WHEN: Processing request with custom org
        request = GenerationRequest(
            begrip="test", organisatorische_context=["OM", "Anders...", custom_org]
        )

        manager = HybridContextManager()
        manager._build_base_context(request)

        # THEN: Custom org should be saved to session
        # This will FAIL - session persistence not implemented
        assert custom_org in st.session_state.get(
            "custom_organisations", []
        ), "Custom organization not saved to session state"

        # AND: Should be available for future requests
        assert custom_org in st.session_state.get(
            "preserved_custom_orgs", []
        ), "Custom org not available for reuse"

    @pytest.mark.red_phase()
    def test_anders_deduplication(self):
        """MUST FAIL: Duplicates with Anders not handled"""
        # GIVEN: Duplicate entries with Anders
        request = GenerationRequest(
            begrip="test",
            organisatorische_context=["OM", "Anders...", "OM", "DJI", "OM"],
        )

        # WHEN: Processing with deduplication
        manager = HybridContextManager()
        context = manager._build_base_context(request)

        # THEN: Duplicates removed, order preserved
        # This will FAIL - deduplication not order-preserving
        assert context["organisatorisch"] == [
            "OM",
            "DJI",
        ], "Deduplication failed or order not preserved"

    @pytest.mark.red_phase()
    def test_anders_in_all_three_context_types(self):
        """MUST FAIL: Anders not supported in all context types"""
        # GIVEN: Anders in all three context types
        request = GenerationRequest(
            begrip="test",
            organisatorische_context=["OM", "Anders...", "CustomOrg"],
            juridische_context=["Strafrecht", "Anders...", "CustomJur"],
            wettelijke_basis=["Art. 27 Sv", "Anders...", "CustomWet"],
        )

        # WHEN: Processing all three
        manager = HybridContextManager()
        context = manager._build_base_context(request)

        # THEN: All custom values preserved, all Anders removed
        # This will FAIL - not all context types support Anders
        assert (
            "CustomOrg" in context["organisatorisch"]
        ), "Custom org not in organisatorisch"
        assert "CustomJur" in context["juridisch"], "Custom juridisch not preserved"
        assert "CustomWet" in context["wettelijk"], "Custom wettelijk not preserved"

        # No Anders markers should remain
        all_values = []
        for values in context.values():
            if isinstance(values, list):
                all_values.extend(values)
        assert "Anders..." not in all_values, "Anders... marker still present in output"

    @pytest.mark.red_phase()
    def test_anders_with_special_characters(self):
        """MUST FAIL: Special characters in custom entries not handled"""
        # GIVEN: Custom entry with special characters
        request = GenerationRequest(
            begrip="test",
            organisatorische_context=["OM", "Anders...", "Org-with-dashes & symbols!"],
        )

        # WHEN: Processing
        manager = HybridContextManager()

        # THEN: Should handle special chars gracefully
        # This will FAIL - special chars cause issues
        context = manager._build_base_context(request)
        assert (
            "Org-with-dashes & symbols!" in context["organisatorisch"]
        ), "Special characters not handled"

    @pytest.mark.red_phase()
    def test_anders_validation_warnings(self):
        """MUST FAIL: No validation warnings for custom entries"""
        # GIVEN: Custom organization via Anders
        request = GenerationRequest(
            begrip="test", organisatorische_context=["OM", "Anders...", "NonASTRAOrg"]
        )

        # WHEN: Processing with logging
        manager = HybridContextManager()

        with patch("logging.Logger.info") as mock_info:
            manager._build_base_context(request)

            # THEN: Should log custom entry for tracking
            # This will FAIL - no tracking implemented
            mock_info.assert_called_with("Custom organization via Anders: NonASTRAOrg")
