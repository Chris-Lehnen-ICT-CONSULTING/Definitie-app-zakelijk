"""
Test ErrorPrevention → QualityEnhancement transformation for DEF-126.

⚠️ OBSOLETE (DEF-169): This test suite is no longer relevant.

REASON:
ErrorPreventionModule has been disabled because it's 100% redundant with
JSONBasedRulesModule. The entire "Veelgemaakte fouten" section (~1,000 tokens)
is already covered by validation rules (ARAI-06, STR-01, ESS-02, etc.).

DECISION:
Instead of transforming ErrorPreventionModule → QualityEnhancementModule,
we removed the module entirely to save tokens without quality loss.

PREVIOUS PLAN (DEF-126):
These tests MUST FAIL initially (red phase of TDD) until the transformation
is implemented. They validate the shift from error prevention (negative)
to quality enhancement (positive).

KEY CHANGES (no longer relevant):
1. Module renamed: ErrorPreventionModule → QualityEnhancementModule
2. Language shift: "VERMIJD X" → "GEBRUIK Y"
3. Removed forbidden starters: "proces waarbij" and "handeling die"

STATUS: Tests will skip if ErrorPreventionModule is not available.
"""

from importlib import import_module
from unittest.mock import MagicMock, patch

import pytest

from src.services.prompts.modules.base_module import ModuleContext


class TestQualityEnhancementTransformation:
    """Test suite for error prevention to quality enhancement transformation."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Try to import the new module name first (for when it's implemented)
        try:
            module_class = import_module(
                "src.services.prompts.modules.quality_enhancement_module"
            )
            self.module = module_class.QualityEnhancementModule()
            self.module_name_correct = True
        except (ImportError, AttributeError):
            # Fall back to old module for initial failing tests
            from src.services.prompts.modules.error_prevention_module import (
                ErrorPreventionModule,
            )

            self.module = ErrorPreventionModule()
            self.module_name_correct = False

        self.module.initialize(
            {"include_validation_matrix": True, "extended_forbidden_list": True}
        )

        # Create mock context
        self.context = MagicMock(spec=ModuleContext)
        self.context.begrip = "vergunning"
        self.context.get_shared = MagicMock(side_effect=self._get_shared_mock)

    def _get_shared_mock(self, key, default=None):
        """Mock implementation for get_shared."""
        shared_data = {
            "organization_contexts": ["gemeente"],
            "juridical_contexts": [],
            "legal_basis_contexts": [],
        }
        return shared_data.get(key, default)

    def test_module_is_renamed_to_quality_enhancement(self):
        """
        Test that the module is renamed from ErrorPreventionModule to QualityEnhancementModule.

        This is a fundamental part of the mindset shift from preventing errors
        to enhancing quality.
        """
        # Check if we can import the new module
        try:
            from src.services.prompts.modules.quality_enhancement_module import (
                QualityEnhancementModule,
            )

            module = QualityEnhancementModule()

            # Verify the module has the right ID
            assert (
                module.module_id == "quality_enhancement"
            ), "Module ID should be 'quality_enhancement' not 'error_prevention'"

            # Verify the module name reflects the change
            assert (
                "Quality" in module.module_name
            ), "Module name should reference 'Quality' not 'Error Prevention'"

            assert (
                "Error Prevention" not in module.module_name
            ), "Module name should not contain 'Error Prevention'"

        except ImportError:
            pytest.fail(
                "QualityEnhancementModule not found. "
                "Module should be renamed from error_prevention_module.py to quality_enhancement_module.py"
            )

    def test_header_uses_positive_framing(self):
        """
        Test that section headers use positive, enhancement-focused language.

        Instead of "Veelgemaakte fouten (vermijden!)" should use positive framing.
        """
        result = self.module.execute(self.context)

        # Old negative header should be gone
        assert (
            "Veelgemaakte fouten (vermijden!)" not in result.content
        ), "Negative 'mistakes to avoid' header should be replaced with positive framing"

        # Should have a positive header instead
        positive_headers = [
            "Kwaliteitsrichtlijnen",
            "Best Practices",
            "Constructieprincipes",
            "Kwaliteitscriteria",
            "Definitieprincipes",
        ]

        has_positive_header = any(
            header in result.content for header in positive_headers
        )
        assert has_positive_header, (
            "Should have positive, quality-focused header like 'Kwaliteitsrichtlijnen' "
            "or 'Best Practices'"
        )

    def test_gebruik_instead_of_vermijd(self):
        """
        Test that instructions use "GEBRUIK" (use) instead of "VERMIJD" (avoid).

        This represents the fundamental shift from negative to positive instructions.
        """
        result = self.module.execute(self.context)

        # Count negative vs positive instructions
        vermijd_count = result.content.count("Vermijd") + result.content.count(
            "VERMIJD"
        )
        gebruik_count = result.content.count("Gebruik") + result.content.count(
            "GEBRUIK"
        )

        assert (
            gebruik_count > 0
        ), "Should have 'GEBRUIK' (use) instructions for positive guidance"

        assert gebruik_count >= vermijd_count, (
            f"Should have more positive instructions (gebruik: {gebruik_count}) "
            f"than negative ones (vermijd: {vermijd_count})"
        )

    def test_proces_waarbij_removed_from_forbidden(self):
        """
        Test that "proces waarbij" is REMOVED from forbidden starters.

        This is a specific requirement of DEF-126 - these constructive phrases
        should no longer be forbidden.
        """
        result = self.module.execute(self.context)

        # "proces waarbij" should NOT be in the forbidden list
        assert (
            "proces waarbij" not in result.content
            or "Start niet met 'proces waarbij'" not in result.content
        ), (
            "'proces waarbij' should be REMOVED from forbidden starters. "
            "This constructive phrase is now allowed."
        )

    def test_handeling_die_removed_from_forbidden(self):
        """
        Test that "handeling die" is REMOVED from forbidden starters.

        This is a specific requirement of DEF-126 - these constructive phrases
        should no longer be forbidden.
        """
        result = self.module.execute(self.context)

        # "handeling die" should NOT be in the forbidden list
        assert (
            "handeling die" not in result.content
            or "Start niet met 'handeling die'" not in result.content
        ), (
            "'handeling die' should be REMOVED from forbidden starters. "
            "This constructive phrase is now allowed."
        )

    def test_positive_construction_guidelines(self):
        """
        Test that the module provides positive construction guidelines.

        Instead of just saying what not to do, should guide what TO do.
        """
        result = self.module.execute(self.context)

        # Look for positive construction words
        positive_indicators = [
            "gebruik",
            "start met",
            "formuleer",
            "construeer",
            "bouw",
            "zorg voor",
            "waarborg",
            "implementeer",
        ]

        positive_count = sum(
            1 for word in positive_indicators if word in result.content.lower()
        )

        assert positive_count >= 3, (
            f"Should have at least 3 positive construction indicators, found {positive_count}. "
            "Focus should be on guiding what TO do."
        )

    def test_no_cross_marks_in_main_content(self):
        """
        Test that cross marks (❌) are minimized or eliminated.

        Visual indicators should be positive (✓, ✅, →) not negative (❌).
        """
        result = self.module.execute(self.context)

        cross_count = result.content.count("❌")

        # Should have few or no cross marks
        assert cross_count < 5, (
            f"Found {cross_count} cross marks (❌). "
            "Should use positive indicators (✓, →) instead of negative ones."
        )

    def test_validation_matrix_uses_positive_language(self):
        """
        Test that the validation matrix uses enhancement-focused language.

        The matrix should focus on quality criteria, not problems.
        """
        result = self.module.execute(self.context)

        if "matrix" in result.content.lower() or "|" in result.content:
            # Find the matrix section
            matrix_start = result.content.find("|")
            if matrix_start > 0:
                matrix_section = result.content[matrix_start : matrix_start + 1000]

                # Should use positive column headers
                positive_headers = [
                    "Kwaliteitskenmerk",
                    "Criterium",
                    "Principe",
                    "Richtlijn",
                ]
                has_positive = any(
                    header in matrix_section for header in positive_headers
                )

                assert has_positive or "Probleem" not in matrix_section, (
                    "Validation matrix should use positive headers like 'Kwaliteitskenmerk' "
                    "instead of 'Probleem'"
                )

    def test_constructive_alternatives_provided(self):
        """
        Test that constructive alternatives are provided for common patterns.

        Instead of just forbidding patterns, should suggest better alternatives.
        """
        result = self.module.execute(self.context)

        # Look for alternative suggestions
        alternative_indicators = [
            "in plaats van",
            "gebruik liever",
            "beter is",
            "alternatief:",
            "vervang door",
            "→",
        ]

        has_alternatives = any(
            indicator in result.content.lower() for indicator in alternative_indicators
        )

        assert has_alternatives, (
            "Should provide constructive alternatives using phrases like "
            "'gebruik liever' or 'in plaats van'"
        )

    def test_context_specific_guidance_is_positive(self):
        """
        Test that context-specific sections use positive guidance.

        Even context-specific rules should be framed positively.
        """
        # Test with organizational context
        self.context.get_shared = MagicMock(
            side_effect=lambda key, default=None: (
                ["gemeente", "provincie"] if key == "organization_contexts" else default
            )
        )

        result = self.module.execute(self.context)

        if "CONTEXT-SPECIFIEK" in result.content:
            context_section = result.content[
                result.content.find("CONTEXT-SPECIFIEK") : result.content.find(
                    "CONTEXT-SPECIFIEK"
                )
                + 500
            ]

            # Should frame context rules positively
            assert (
                "VERBODEN" not in context_section or "RICHTLIJNEN" in context_section
            ), (
                "Context-specific section should use 'RICHTLIJNEN' (guidelines) "
                "not 'VERBODEN' (forbidden)"
            )

    def test_basic_errors_section_becomes_quality_principles(self):
        """
        Test that basic errors section is transformed to quality principles.

        The _build_basic_errors method should become _build_quality_principles
        or similar.
        """
        result = self.module.execute(self.context)

        # Should not have "errors" framing
        assert (
            "fouten" not in result.content.lower()[:500]
            or "kwaliteit" in result.content.lower()[:500]
        ), "Opening sections should focus on 'kwaliteit' (quality) not 'fouten' (errors)"

    def test_forbidden_starters_list_is_reduced(self):
        """
        Test that the forbidden starters list is significantly reduced.

        With "proces waarbij" and "handeling die" removed, and positive framing,
        the list should be shorter.
        """
        result = self.module.execute(self.context)

        # Count lines that look like forbidden starter warnings
        forbidden_lines = [
            line
            for line in result.content.split("\n")
            if "Start niet met" in line or "niet met '" in line
        ]

        # Should have fewer forbidden starters (since we removed some)
        assert len(forbidden_lines) < 35, (
            f"Found {len(forbidden_lines)} forbidden starter lines. "
            "List should be reduced with removal of 'proces waarbij' and 'handeling die'"
        )

    def test_module_output_structure_maintained(self):
        """
        Test that the module still returns valid output structure.

        The transformation should not break the module interface.
        """
        result = self.module.execute(self.context)

        assert result is not None
        assert hasattr(result, "content")
        assert hasattr(result, "metadata")
        assert hasattr(result, "success")
        assert result.success is True

    def test_dependencies_unchanged(self):
        """
        Test that module dependencies remain the same.

        The quality enhancement module should still depend on context_awareness.
        """
        deps = self.module.get_dependencies()
        assert "context_awareness" in deps


class TestQualityEnhancementPositiveExamples:
    """Test that the module provides positive examples and guidance."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        try:
            from src.services.prompts.modules.quality_enhancement_module import (
                QualityEnhancementModule,
            )

            self.module = QualityEnhancementModule()
        except ImportError:
            from src.services.prompts.modules.error_prevention_module import (
                ErrorPreventionModule,
            )

            self.module = ErrorPreventionModule()

        self.module.initialize({})
        self.context = MagicMock(spec=ModuleContext)
        self.context.begrip = "vergunning"
        self.context.get_shared = MagicMock(return_value=[])

    def test_provides_good_examples(self):
        """
        Test that the module provides examples of good definitions.

        Should show what TO do, not just what NOT to do.
        """
        result = self.module.execute(self.context)

        # Look for example indicators
        example_indicators = [
            "bijvoorbeeld:",
            "voorbeeld:",
            "zoals:",
            "goede definitie:",
            "correct:",
            "✓",
        ]

        has_examples = any(
            indicator in result.content.lower() for indicator in example_indicators
        )

        assert has_examples, "Should provide positive examples of good definitions"

    def test_emphasizes_clarity_and_precision(self):
        """
        Test that quality criteria emphasize clarity and precision.

        These are positive qualities to strive for.
        """
        result = self.module.execute(self.context)

        quality_terms = ["helder", "duidelijk", "precies", "specifiek", "concreet"]
        quality_count = sum(
            1 for term in quality_terms if term in result.content.lower()
        )

        assert (
            quality_count >= 2
        ), "Should emphasize positive qualities like 'helder', 'duidelijk', 'precies'"

    def test_construction_order_guidance(self):
        """
        Test that the module provides guidance on construction order.

        Should guide HOW to build a good definition step by step.
        """
        result = self.module.execute(self.context)

        order_indicators = [
            "eerst",
            "vervolgens",
            "daarna",
            "ten slotte",
            "stap 1",
            "stap 2",
            "1.",
            "2.",
            "→",
        ]

        has_order = any(
            indicator in result.content.lower() for indicator in order_indicators
        )

        assert has_order, "Should provide step-by-step construction guidance"


class TestQualityEnhancementEdgeCases:
    """Test edge cases and boundary conditions for the transformation."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        try:
            from src.services.prompts.modules.quality_enhancement_module import (
                QualityEnhancementModule,
            )

            self.module = QualityEnhancementModule()
        except ImportError:
            from src.services.prompts.modules.error_prevention_module import (
                ErrorPreventionModule,
            )

            self.module = ErrorPreventionModule()

    def test_empty_context_still_positive(self):
        """Test that even with no context, the module uses positive language."""
        module = self.module
        module.initialize({})

        context = MagicMock(spec=ModuleContext)
        context.begrip = "test"
        context.get_shared = MagicMock(return_value=[])

        result = module.execute(context)

        # Should still be positive even without context
        assert (
            "GEBRUIK" in result.content or "kwaliteit" in result.content.lower()
        ), "Should maintain positive framing even without context"

    def test_multiple_contexts_handled_positively(self):
        """Test that multiple contexts are handled with positive framing."""
        module = self.module
        module.initialize({})

        context = MagicMock(spec=ModuleContext)
        context.begrip = "test"
        context.get_shared = MagicMock(
            side_effect=lambda key, default=None: {
                "organization_contexts": ["OM", "ZM", "CJIB"],
                "juridical_contexts": ["Strafrecht", "Bestuursrecht"],
                "legal_basis_contexts": ["WvS", "Awb"],
            }.get(key, default)
        )

        result = module.execute(context)

        # With many contexts, should still be constructive
        assert result.success is True

        # Count positive vs negative words
        positive_words = ["gebruik", "kwaliteit", "richtlijn", "principe"]
        negative_words = ["vermijd", "verboden", "niet", "geen"]

        positive_count = sum(
            result.content.lower().count(word) for word in positive_words
        )
        _ = sum(  # Calculate but don't assert on negative words
            result.content.lower().count(word) for word in negative_words
        )

        assert (
            positive_count > 0
        ), "Should have positive guidance even with complex context"

    def test_configuration_flags_respected(self):
        """Test that configuration flags still work after transformation."""
        # Test with validation matrix disabled
        module1 = self.module
        module1.initialize({"include_validation_matrix": False})

        context = MagicMock(spec=ModuleContext)
        context.begrip = "test"
        context.get_shared = MagicMock(return_value=[])

        result1 = module1.execute(context)

        # Test with validation matrix enabled
        module2 = self.module
        module2.initialize({"include_validation_matrix": True})

        result2 = module2.execute(context)

        # With matrix should have more content (table)
        assert "|" not in result1.content or "|" in result2.content

    def test_special_characters_in_context(self):
        """Test handling of special characters in context."""
        module = self.module
        module.initialize({})

        context = MagicMock(spec=ModuleContext)
        context.begrip = "e-commerce"
        context.get_shared = MagicMock(
            side_effect=lambda key, default=None: (
                ["3RO", "e-Overheid"] if key == "organization_contexts" else default
            )
        )

        result = module.execute(context)

        assert result.success is True
        # Should handle special chars gracefully
        assert "3RO" in result.content or "organisatie" in result.content.lower()


class TestQualityEnhancementIntegration:
    """Test integration aspects of the quality enhancement transformation."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        try:
            from src.services.prompts.modules.quality_enhancement_module import (
                QualityEnhancementModule,
            )

            self.module = QualityEnhancementModule()
        except ImportError:
            from src.services.prompts.modules.error_prevention_module import (
                ErrorPreventionModule,
            )

            self.module = ErrorPreventionModule()

        self.module.initialize({})

    def test_works_with_prompt_orchestrator(self):
        """
        Test that the transformed module works with PromptOrchestrator.

        The module should maintain compatibility with the orchestration system.
        """
        # The module should have the right interface
        assert hasattr(self.module, "module_id")
        assert hasattr(self.module, "execute")
        assert hasattr(self.module, "get_dependencies")
        assert hasattr(self.module, "validate_input")

        # Dependencies should be properly declared
        deps = self.module.get_dependencies()
        assert isinstance(deps, list)

    def test_metadata_reflects_quality_focus(self):
        """
        Test that metadata reflects the quality enhancement focus.

        Metadata should track quality metrics, not just error counts.
        """
        context = MagicMock(spec=ModuleContext)
        context.begrip = "test"
        context.get_shared = MagicMock(return_value=[])

        result = self.module.execute(context)

        # Metadata should exist
        assert result.metadata is not None

        # Could track quality indicators instead of just forbidden counts
        # This is optional but shows mindset shift

    def test_error_handling_maintains_positive_tone(self):
        """
        Test that error messages maintain a constructive tone.

        Even error messages should be helpful and constructive.
        """
        context = MagicMock(spec=ModuleContext)
        context.begrip = "test"
        # Force an error
        context.get_shared = MagicMock(side_effect=Exception("Test error"))

        result = self.module.execute(context)

        if not result.success:
            # Error message should be constructive
            assert (
                "Failed to generate" in result.error_message
                or "quality" in result.error_message.lower()
            ), "Error messages should be constructive"
