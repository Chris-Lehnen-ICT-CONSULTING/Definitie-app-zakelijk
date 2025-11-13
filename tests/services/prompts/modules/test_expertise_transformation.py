"""
Test ExpertiseModule transformation for DEF-126 - validation to generation mindset.

These tests MUST FAIL initially (red phase of TDD) until the transformation
is implemented. They validate the shift from validation-focused to stakeholder-focused
expert role definition.

OLD: "Je bent een expert in beleidsmatige definities voor overheidsgebruik"
NEW: Focus on BELANGHEBBENDEN (stakeholders), EENDUIDIG (unambiguous),
     and WERKELIJKHEID (reality) in the instruction
"""

import pytest
from unittest.mock import MagicMock, patch

from src.services.prompts.modules.expertise_module import ExpertiseModule
from src.services.prompts.modules.base_module import ModuleContext


class TestExpertiseTransformation:
    """Test suite for expertise module transformation to stakeholder focus."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.module = ExpertiseModule()
        self.module.initialize({})

        # Create a mock context
        self.context = MagicMock(spec=ModuleContext)
        self.context.begrip = "vergunning"
        self.context.get_shared = MagicMock(return_value=None)
        self.context.set_shared = MagicMock()

    def test_expert_role_includes_belanghebbenden(self):
        """
        Test that expert role definition mentions BELANGHEBBENDEN (stakeholders).

        The new mindset should explicitly mention that definitions are created
        for all stakeholders, not just for governmental use.
        """
        result = self.module.execute(self.context)

        # Test that the content includes the word BELANGHEBBENDEN
        assert "BELANGHEBBENDEN" in result.content, (
            "Expert role must mention BELANGHEBBENDEN (stakeholders) "
            "to reflect focus on practical usability for all parties"
        )

        # The word should be in uppercase to emphasize importance
        assert "belanghebbenden" not in result.content or "BELANGHEBBENDEN" in result.content, (
            "BELANGHEBBENDEN should be emphasized in uppercase"
        )

    def test_expert_role_includes_eenduidig(self):
        """
        Test that expert role emphasizes EENDUIDIG (unambiguous) understanding.

        The transformation requires that definitions are sufficiently unambiguous
        for practical use.
        """
        result = self.module.execute(self.context)

        # Test that the content emphasizes unambiguous/clear understanding
        assert "EENDUIDIG" in result.content, (
            "Expert role must emphasize EENDUIDIG (unambiguous) "
            "to ensure clarity for all stakeholders"
        )

    def test_expert_role_includes_werkelijkheid(self):
        """
        Test that expert role connects to WERKELIJKHEID (reality).

        Definitions should describe concepts as they exist in reality,
        not just as policy constructs.
        """
        result = self.module.execute(self.context)

        # Test that the content references reality/practical world
        assert "WERKELIJKHEID" in result.content, (
            "Expert role must reference WERKELIJKHEID (reality) "
            "to ground definitions in practical application"
        )

    def test_old_instruction_is_replaced(self):
        """
        Test that the old validation-focused instruction is completely replaced.

        The old instruction "beleidsmatige definities voor overheidsgebruik"
        should no longer appear.
        """
        result = self.module.execute(self.context)

        # Old phrase should NOT be present
        assert "beleidsmatige definities voor overheidsgebruik" not in result.content, (
            "Old government-centric instruction should be removed. "
            "Found old text that should be replaced with stakeholder-focused approach"
        )

        # Also check for partial phrases that indicate old mindset
        assert "voor overheidsgebruik" not in result.content, (
            "Reference to 'governmental use only' should be removed"
        )

    def test_complete_new_instruction_format(self):
        """
        Test that the complete new instruction follows the expected format.

        The new instruction should be a coherent sentence that includes
        all three key elements: BELANGHEBBENDEN, EENDUIDIG, and WERKELIJKHEID.
        """
        result = self.module.execute(self.context)

        # Extract the role definition section (usually the first major statement)
        lines = result.content.split('\n')
        role_definition = None
        for line in lines:
            if "expert" in line.lower() and not line.startswith('#'):
                role_definition = line
                break

        assert role_definition is not None, "Could not find expert role definition"

        # Check that it's a complete, coherent instruction
        assert len(role_definition) > 50, (
            "New instruction should be substantial and complete"
        )

        # Verify it contains the essence of the new approach
        assert "creëren" in role_definition or "maken" in role_definition, (
            "Should focus on creating/making definitions, not just validating"
        )

    def test_basic_requirements_align_with_stakeholder_focus(self):
        """
        Test that basic requirements section aligns with stakeholder focus.

        Requirements should emphasize practical usability and stakeholder needs,
        not just technical correctness.
        """
        result = self.module.execute(self.context)

        # Check if requirements mention practical application
        requirements_section = result.content[result.content.find("BELANGRIJKE VEREISTEN"):]

        # Should still have quality requirements but framed differently
        assert "precies" in requirements_section or "duidelijk" in requirements_section, (
            "Requirements should emphasize clarity and precision for stakeholder understanding"
        )

    def test_word_type_advice_supports_generation_mindset(self):
        """
        Test that word-type specific advice supports definition generation.

        The advice should be constructive and generation-focused,
        not validation-focused.
        """
        # Test with different word types
        test_cases = [
            ("aanvragen", "werkwoord"),
            ("aanvraag", "deverbaal"),
            ("vergunning", "overig")
        ]

        for begrip, expected_type in test_cases:
            self.context.begrip = begrip
            result = self.module.execute(self.context)

            # Verify advice is present and constructive
            assert "definieer" in result.content or "beschrijf" in result.content, (
                f"Advice for {expected_type} should use constructive language "
                "(definieer/beschrijf) not restrictive language"
            )

    def test_metadata_reflects_transformation(self):
        """
        Test that module metadata reflects the transformation.

        The module should track that it's using the new stakeholder-focused approach.
        """
        result = self.module.execute(self.context)

        # Metadata should indicate successful execution
        assert result.success is True
        assert result.metadata is not None

        # Could track version or approach type in metadata
        # This is optional but good practice for tracking transformations

    def test_integration_with_shared_context(self):
        """
        Test that the module properly shares its stakeholder focus with other modules.

        The transformation should influence how other modules operate.
        """
        result = self.module.execute(self.context)

        # Verify word type is still being shared (backward compatibility)
        self.context.set_shared.assert_called()

        # Check that word_type was set
        calls = self.context.set_shared.call_args_list
        word_type_set = any(call[0][0] == "word_type" for call in calls)
        assert word_type_set, "Word type should still be shared with other modules"

    def test_error_handling_maintained(self):
        """
        Test that error handling still works after transformation.

        The transformation should not break existing error handling.
        """
        # Test with empty begrip
        self.context.begrip = ""
        is_valid, error_msg = self.module.validate_input(self.context)

        assert is_valid is False
        assert error_msg is not None
        assert "begrip" in error_msg.lower()

    def test_no_validation_language_in_main_instruction(self):
        """
        Test that validation-focused language is removed from main instruction.

        Words like "controleer", "toets", "valideer" should not appear
        in the main expert role definition.
        """
        result = self.module.execute(self.context)

        # Extract the first part (before requirements)
        main_part = result.content.split("BELANGRIJKE VEREISTEN")[0]

        validation_words = ["controleer", "toets", "valideer", "check"]
        for word in validation_words:
            assert word not in main_part.lower(), (
                f"Validation word '{word}' should not appear in generation-focused instruction"
            )

    @pytest.mark.parametrize("begrip,expected_focus", [
        ("vergunning", "stakeholder clarity"),
        ("aanvraagprocedure", "practical process"),
        ("besluit", "real-world impact"),
    ])
    def test_different_begrippen_get_stakeholder_focus(self, begrip, expected_focus):
        """
        Test that different types of begrippen all get stakeholder-focused treatment.

        Parametrized test to ensure consistency across different input types.
        """
        self.context.begrip = begrip
        result = self.module.execute(self.context)

        # All should have the new stakeholder elements
        assert "BELANGHEBBENDEN" in result.content
        assert "EENDUIDIG" in result.content or "duidelijk" in result.content.lower()
        assert "WERKELIJKHEID" in result.content or "praktijk" in result.content.lower()


class TestExpertiseBackwardCompatibility:
    """Test that essential functionality is preserved during transformation."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.module = ExpertiseModule()
        self.module.initialize({})

        self.context = MagicMock(spec=ModuleContext)
        self.context.begrip = "vergunning"
        self.context.get_shared = MagicMock(return_value=None)
        self.context.set_shared = MagicMock()

    def test_module_structure_preserved(self):
        """Test that the module structure remains valid."""
        assert self.module.module_id == "expertise"
        assert self.module.module_name == "Expert Role & Basic Instructions"
        assert self.module.priority == 100  # Highest priority

    def test_execute_returns_valid_output(self):
        """Test that execute still returns valid ModuleOutput."""
        result = self.module.execute(self.context)

        assert result is not None
        assert hasattr(result, 'content')
        assert hasattr(result, 'metadata')
        assert hasattr(result, 'success')
        assert result.success is True

    def test_word_type_detection_still_works(self):
        """Test that word type detection is not broken."""
        test_cases = [
            ("aanvragen", "werkwoord"),
            ("aanvraag", "deverbaal"),
            ("vergunning", "overig"),
        ]

        for begrip, expected_type in test_cases:
            self.context.begrip = begrip
            result = self.module.execute(self.context)

            # Check metadata for word_type
            assert result.metadata.get('word_type') == expected_type


class TestExpertiseEdgeCases:
    """Test edge cases and boundary conditions for the transformation."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.module = ExpertiseModule()
        self.module.initialize({})

    def test_very_long_begrip(self):
        """Test handling of very long begrippen."""
        context = MagicMock(spec=ModuleContext)
        context.begrip = "zeer lange samengestelde begripsomschrijving met meerdere componenten"
        context.get_shared = MagicMock(return_value=None)
        context.set_shared = MagicMock()

        result = self.module.execute(context)

        # Should still include new elements
        assert "BELANGHEBBENDEN" in result.content
        assert result.success is True

    def test_special_characters_in_begrip(self):
        """Test handling of special characters."""
        context = MagicMock(spec=ModuleContext)
        context.begrip = "e-commerce"
        context.get_shared = MagicMock(return_value=None)
        context.set_shared = MagicMock()

        result = self.module.execute(context)

        # Should handle special characters gracefully
        assert result.success is True
        assert "BELANGHEBBENDEN" in result.content

    def test_empty_config(self):
        """Test that module works with empty config."""
        module = ExpertiseModule()
        module.initialize({})

        context = MagicMock(spec=ModuleContext)
        context.begrip = "test"
        context.get_shared = MagicMock(return_value=None)
        context.set_shared = MagicMock()

        result = module.execute(context)
        assert result.success is True

    def test_exception_handling(self):
        """Test that exceptions are handled gracefully."""
        context = MagicMock(spec=ModuleContext)
        context.begrip = "test"
        # Simulate an exception by making get_shared raise
        context.get_shared = MagicMock(side_effect=Exception("Test error"))
        context.set_shared = MagicMock()

        result = self.module.execute(context)

        # Should return error output
        assert result.success is False
        assert result.error_message is not None
        assert "Test error" in result.error_message