"""
PER-007 RED Phase Tests: ASTRA Compliance
ASTRA compliance tests - MUST fail initially to prove validation is too strict.
"""

import logging
from unittest.mock import Mock, call, patch

import pytest

from services.definition_generator_context import HybridContextManager
from services.interfaces import GenerationRequest


class TestASTRACompliance:
    """ASTRA compliance tests - MUST fail initially"""

    @pytest.mark.red_phase
    def test_invalid_org_gives_warning_not_error(self):
        """MUST FAIL: Currently blocks on invalid orgs"""
        # GIVEN: Invalid organization name
        request = GenerationRequest(
            begrip="test", organisatorische_context=["InvalidOrg", "OM"]
        )

        # WHEN: Validation occurs
        manager = HybridContextManager()

        # Capture warnings
        with patch("logging.Logger.warning") as mock_warn:
            # This should NOT raise an error
            try:
                context = manager._build_base_context(request)
            except Exception as e:
                pytest.fail(f"Should warn, not error. Got error: {e}")

            # THEN: Should warn about invalid org
            # This will FAIL - currently blocks instead of warning
            warning_messages = [call[0][0] for call in mock_warn.call_args_list]
            assert any(
                "InvalidOrg" in msg for msg in warning_messages
            ), "No warning about invalid organization"

            # But still process the request
            assert (
                "InvalidOrg" in context["organisatorisch"]
            ), "Invalid org should still be included with warning"
            assert "OM" in context["organisatorisch"], "Valid org should be included"

    @pytest.mark.red_phase
    def test_fuzzy_matching_suggestions(self):
        """MUST FAIL: No fuzzy matching implemented"""
        # GIVEN: Misspelled organization
        misspellings = [
            ("DJI2", "DJI"),  # Extra character
            ("DJJ", "DJI"),  # Wrong character
            ("OMM", "OM"),  # Extra character
            ("Rechtspraaak", "Rechtspraak"),  # Extra character
        ]

        for misspelled, correct in misspellings:
            request = GenerationRequest(
                begrip="test", organisatorische_context=[misspelled]
            )

            # WHEN: Validation with warning capture
            manager = HybridContextManager()

            with patch("logging.Logger.warning") as mock_warn:
                manager._build_base_context(request)

                # THEN: Should suggest correct spelling
                # This will FAIL - no fuzzy matching
                warning_messages = [call[0][0] for call in mock_warn.call_args_list]
                assert any(
                    f"Did you mean: {correct}" in msg for msg in warning_messages
                ), f"No suggestion for {misspelled} -> {correct}"

    @pytest.mark.red_phase
    def test_astra_validator_exists(self):
        """MUST FAIL: ASTRA validator not implemented"""
        # GIVEN: Need for ASTRA validation
        # WHEN: Importing validator
        # THEN: Should exist
        try:
            from services.validation.astra_validator import (
                ASTRA_ORGANIZATIONS,
                validate_organization,
            )

            # Check it has expected organizations
            assert "OM" in ASTRA_ORGANIZATIONS
            assert "DJI" in ASTRA_ORGANIZATIONS
            assert "Rechtspraak" in ASTRA_ORGANIZATIONS

        except ImportError:
            pytest.fail("ASTRA validator not implemented")

    @pytest.mark.red_phase
    def test_telemetry_tracks_custom_entries(self):
        """MUST FAIL: Telemetry not implemented"""
        # GIVEN: Custom organization entry
        request = GenerationRequest(
            begrip="test", organisatorische_context=["CustomOrg"]
        )

        # WHEN: Processed
        manager = HybridContextManager()

        # Mock telemetry service
        with patch("services.telemetry.track_custom_entry") as mock_track:
            manager._build_base_context(request)

            # THEN: Should track for reporting
            # This will FAIL - telemetry not implemented
            mock_track.assert_called_with(
                context_type="organisatorisch",
                value="CustomOrg",
                metadata={"source": "user_input"},
            )

    @pytest.mark.red_phase
    def test_astra_compliance_report_generation(self):
        """MUST FAIL: No compliance reporting"""
        # GIVEN: Request with mixed valid/invalid orgs
        request = GenerationRequest(
            begrip="test",
            organisatorische_context=["OM", "InvalidOrg", "DJI", "CustomOrg"],
        )

        # WHEN: Processing and generating report
        manager = HybridContextManager()
        manager._build_base_context(request)

        # THEN: Should generate compliance report
        # This will FAIL - no compliance reporting
        assert hasattr(
            manager, "get_astra_compliance_report"
        ), "No compliance reporting method"

        report = manager.get_astra_compliance_report()
        assert "valid_organizations" in report
        assert "invalid_organizations" in report
        assert "custom_organizations" in report
        assert report["valid_organizations"] == ["OM", "DJI"]
        assert report["invalid_organizations"] == ["InvalidOrg"]
        assert report["custom_organizations"] == ["CustomOrg"]

    @pytest.mark.red_phase
    def test_astra_warning_levels(self):
        """MUST FAIL: No warning level differentiation"""
        # GIVEN: Different types of issues
        request = GenerationRequest(
            begrip="test",
            organisatorische_context=[
                "OM",  # Valid
                "DJI2",  # Typo - should suggest
                "InvalidOrg",  # Unknown - should warn
                "",  # Empty - should ignore
            ],
        )

        # WHEN: Processing
        manager = HybridContextManager()

        with patch("logging.Logger.warning") as mock_warn, patch("logging.Logger.info") as mock_info:
            manager._build_base_context(request)

            # THEN: Different warning levels
            # This will FAIL - no differentiation
            # Info for suggestions
            info_calls = [call[0][0] for call in mock_info.call_args_list]
            assert any(
                "suggestion" in msg.lower() for msg in info_calls
            ), "No info-level suggestions"

            # Warning for unknown
            warn_calls = [call[0][0] for call in mock_warn.call_args_list]
            assert any(
                "unknown" in msg.lower() for msg in warn_calls
            ), "No warning for unknown org"

    @pytest.mark.red_phase
    def test_astra_allows_abbreviations_and_full_names(self):
        """MUST FAIL: Both abbreviations and full names not accepted"""
        # GIVEN: Mix of abbreviations and full names
        request = GenerationRequest(
            begrip="test",
            organisatorische_context=[
                "OM",
                "Openbaar Ministerie",  # Full name of OM
                "DJI",
                "Dienst Justitiële Inrichtingen",  # Full name of DJI
            ],
        )

        # WHEN: Processing without deduplication
        manager = HybridContextManager()

        with patch("logging.Logger.warning") as mock_warn:
            context = manager._build_base_context(request)

            # THEN: Both forms accepted, no warnings
            # This will FAIL - full names not recognized
            mock_warn.assert_not_called()

            # Should deduplicate to abbreviations
            assert context["organisatorisch"] == [
                "OM",
                "DJI",
            ], "Full names not mapped to abbreviations"

    @pytest.mark.red_phase
    def test_astra_chain_contexts_recognized(self):
        """MUST FAIL: Chain contexts not recognized"""
        # GIVEN: Justice chain contexts
        request = GenerationRequest(
            begrip="test",
            organisatorische_context=["ZSM-keten", "Strafrechtketen", "Jeugdketen"],
        )

        # WHEN: Processing
        manager = HybridContextManager()

        with patch("logging.Logger.warning") as mock_warn:
            context = manager._build_base_context(request)

            # THEN: Chain contexts recognized without warnings
            # This will FAIL - chains not in registry
            mock_warn.assert_not_called()
            assert "ZSM-keten" in context["organisatorisch"]
            assert "Strafrechtketen" in context["organisatorisch"]
            assert "Jeugdketen" in context["organisatorisch"]

    @pytest.mark.red_phase
    def test_astra_metadata_enrichment(self):
        """MUST FAIL: No metadata enrichment for organizations"""
        # GIVEN: Valid ASTRA organization
        request = GenerationRequest(begrip="test", organisatorische_context=["OM"])

        # WHEN: Processing
        manager = HybridContextManager()
        enriched = manager.process_request(request)

        # THEN: Should have enriched metadata
        # This will FAIL - no enrichment implemented
        assert "organization_metadata" in enriched.metadata
        om_metadata = enriched.metadata["organization_metadata"]["OM"]
        assert "full_name" in om_metadata
        assert om_metadata["full_name"] == "Openbaar Ministerie"
        assert "astra_compliant" in om_metadata
        assert om_metadata["astra_compliant"] is True
