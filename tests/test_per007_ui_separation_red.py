"""
PER-007 RED Phase Tests: UI Preview String Rejection
These tests MUST fail initially to prove the system incorrectly accepts UI strings as data source.
"""

from unittest.mock import Mock, patch

import pytest

from services.definition_generator_context import (EnrichedContext,
                                                   HybridContextManager)
from services.interfaces import GenerationRequest
from services.prompts.prompt_service_v2 import PromptServiceV2


class TestUIPreviewRejection:
    """Tests that MUST fail in RED phase - proving UI strings are wrongly accepted"""

    @pytest.mark.red_phase()
    def test_prompt_builder_rejects_ui_preview_string(self):
        """MUST FAIL: System should reject UI preview strings as input"""
        # GIVEN: A UI preview string with emojis and formatting
        ui_preview = "📋 Org: OM, DJI | ⚖️ Juridisch: Strafrecht | 📜 Wet: Art. 27 Sv"

        # WHEN: Someone tries to use it as context input
        prompt_service = PromptServiceV2()

        # THEN: System should raise TypeError or ValueError
        with pytest.raises(
            (TypeError, ValueError),
            match="UI preview strings cannot be used as data source",
        ):
            # This should fail in RED phase - system wrongly accepts this
            # Note: This method doesn't exist yet - proving we need to implement it
            prompt_service._parse_ui_string_as_context(ui_preview)

    @pytest.mark.red_phase()
    def test_context_manager_rejects_concatenated_strings(self):
        """MUST FAIL: Context manager should reject concatenated context strings"""
        # GIVEN: A request with UI-formatted context
        request = GenerationRequest(
            begrip="verdachte",
            context="📋 Org: OM | ⚖️ Juridisch: Strafrecht",  # UI string
        )

        # WHEN: Processing the context
        manager = HybridContextManager()

        # THEN: Should raise error about using UI strings
        with pytest.raises(ValueError, match="Use structured lists, not UI strings"):
            # This should fail in RED phase - system processes it incorrectly
            # Note: This method doesn't exist yet
            manager.process_ui_string_context(request)

    @pytest.mark.red_phase()
    def test_enriched_context_validates_source_type(self):
        """MUST FAIL: EnrichedContext should validate it's built from lists, not strings"""
        # GIVEN: Attempt to create context from wrong source
        # WHEN: Building EnrichedContext from UI string
        # THEN: Should fail validation
        with pytest.raises(
            TypeError, match="EnrichedContext requires structured lists"
        ):
            # This should fail - from_ui_string shouldn't exist
            EnrichedContext.from_ui_string("📋 Org: OM | ⚖️ Juridisch: Strafrecht")

    @pytest.mark.red_phase()
    def test_ui_formatter_is_output_only(self):
        """MUST FAIL: UI formatter should only output, never accept UI strings as input"""
        # GIVEN: A UI preview string
        ui_string = "📋 Org: OM, DJI | ⚖️ Juridisch: Strafrecht"

        # WHEN: Trying to reverse-parse it
        from services.ui.formatters import \
            ContextFormatter  # Doesn't exist yet

        formatter = ContextFormatter()

        # THEN: Should refuse to parse UI strings
        with pytest.raises(ValueError, match="ContextFormatter is output-only"):
            formatter.parse_ui_string(ui_string)

    @pytest.mark.red_phase()
    def test_prompt_service_blocks_emoji_contamination(self):
        """MUST FAIL: Prompt service should block any emoji-containing strings"""
        # GIVEN: Context with emoji contamination
        request = GenerationRequest(
            begrip="test", organisatorische_context=["📋 OM", "DJI"]  # Emoji in data!
        )

        # WHEN: Building prompt
        prompt_service = PromptServiceV2()

        # THEN: Should detect and reject emoji contamination
        with pytest.raises(ValueError, match="Emojis not allowed in structured data"):
            prompt_service.build_prompt(request)

    @pytest.mark.red_phase()
    def test_context_formatter_enforces_separation(self):
        """MUST FAIL: Context formatter must enforce strict separation"""
        # GIVEN: Valid structured context
        context = EnrichedContext(
            base_context={
                "organisatorisch": ["OM", "DJI"],
                "juridisch": ["Strafrecht"],
                "wettelijk": ["Art. 27 Sv"],
            },
            sources=[],
            expanded_terms={},
            confidence_scores={},
            metadata={},
        )

        # WHEN: Formatting for UI
        from services.ui.formatters import ContextFormatter

        formatter = ContextFormatter()
        ui_preview = formatter.format_ui_preview(context)

        # THEN: UI preview should NEVER be usable as input
        # This marker should be added to prevent misuse
        assert ui_preview.startswith(
            "[UI_ONLY]"
        ), "UI preview not marked as display-only"

        # AND: Trying to use it as input should fail
        with pytest.raises(
            ValueError, match="UI preview cannot be used as data source"
        ):
            formatter.validate_not_ui_string(ui_preview)
