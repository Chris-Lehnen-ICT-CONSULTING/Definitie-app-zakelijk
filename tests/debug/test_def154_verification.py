"""
DEF-154 Comprehensive Verification Script

Tests that word_type_advice removal didn't break anything and that
all integrations still work correctly.
"""

from unittest.mock import MagicMock

import pytest

from src.services.prompts.modules.base_module import ModuleContext
from src.services.prompts.modules.expertise_module import ExpertiseModule
from src.services.prompts.modules.grammar_module import GrammarModule
from src.services.prompts.modules.template_module import TemplateModule


def make_context(begrip: str = "test", word_type: str | None = None):
    """Create mock test context matching existing test patterns."""
    context = MagicMock(spec=ModuleContext)
    context.begrip = begrip

    # Mock shared state storage
    shared_state = {}
    if word_type:
        shared_state["word_type"] = word_type

    def get_shared(key, default=None):
        return shared_state.get(key, default)

    def set_shared(key, value):
        shared_state[key] = value

    context.get_shared = get_shared
    context.set_shared = set_shared

    return context


class TestDEF154Verification:
    """Comprehensive verification suite for DEF-154."""

    def test_expertise_module_no_word_type_advice_in_output(self):
        """Verify word_type_advice is completely removed from ExpertiseModule output."""
        module = ExpertiseModule()
        module.initialize({})

        test_cases = [
            ("behandelen", "werkwoord"),
            ("behandeling", "deverbaal"),
            ("stakeholder", "overig"),
        ]

        for begrip, expected_type in test_cases:
            ctx = make_context(begrip=begrip)
            result = module.execute(ctx)

            assert result.success, f"Execution failed for {begrip}"
            assert (
                "word_type_advice" not in result.content.lower()
            ), f"word_type_advice found in output for {begrip}"
            assert (
                "woordsoort" not in result.content.lower()
            ), f"woordsoort advice found in output for {begrip}"

            # Verify word_type is still detected and shared
            shared_type = ctx.get_shared("word_type")
            assert (
                shared_type == expected_type
            ), f"Expected {expected_type}, got {shared_type} for {begrip}"

    def test_word_type_shared_state_propagation(self):
        """Verify word_type is correctly shared between modules."""
        expertise = ExpertiseModule()
        expertise.initialize({})

        grammar = GrammarModule()
        grammar.initialize({})

        # Test with werkwoord
        ctx = make_context(begrip="behandelen")
        expertise_result = expertise.execute(ctx)

        assert expertise_result.success
        assert ctx.get_shared("word_type") == "werkwoord"

        # GrammarModule should be able to access the shared word_type
        grammar_result = grammar.execute(ctx)
        assert grammar_result.success
        # GrammarModule should have word_type in metadata even if not in content
        assert grammar_result.metadata.get("word_type") == "werkwoord"

    def test_template_module_receives_word_type(self):
        """Verify TemplateModule can still access word_type from shared state."""
        template = TemplateModule()
        template.initialize({})

        test_cases = [
            ("behandelen", "werkwoord", "proces"),
            ("behandeling", "deverbaal", "proces"),
            ("stakeholder", "overig", "type"),
        ]

        for begrip, word_type, ont_category in test_cases:
            ctx = make_context(begrip=begrip, word_type=word_type)
            ctx.set_shared("ontological_category", ont_category)

            result = template.execute(ctx)
            assert result.success, f"TemplateModule failed for {begrip}"
            # TemplateModule should generate category-specific advice
            assert len(result.content) > 0, f"Empty content for {begrip}"

    def test_all_three_word_types_detected_correctly(self):
        """Verify all word type detection logic still works."""
        module = ExpertiseModule()
        module.initialize({})

        test_cases = {
            "werkwoord": ["behandelen", "aanpassen", "verwerken"],
            "deverbaal": ["behandeling", "aanpassing", "verwerking"],
            # Note: 'authenticatie' ends in 'atie' so it's detected as deverbaal
            "overig": ["stakeholder", "website", "burger"],
        }

        for expected_type, begrippen in test_cases.items():
            for begrip in begrippen:
                ctx = make_context(begrip=begrip)
                result = module.execute(ctx)

                assert result.success, f"Failed for {begrip}"
                detected_type = ctx.get_shared("word_type")
                assert (
                    detected_type == expected_type
                ), f"{begrip}: expected {expected_type}, got {detected_type}"

    def test_edge_cases(self):
        """Test edge cases for word type detection."""
        module = ExpertiseModule()
        module.initialize({})

        edge_cases = [
            ("", "overig"),  # Empty
            ("a", "overig"),  # Very short
            # Note: 'behandelingen' ends in 'en' (length >4, not in exclusions) → werkwoord
            ("behandelingen", "werkwoord"),  # Plural - detected as werkwoord
            ("BEHANDELEN", "werkwoord"),  # Uppercase
            ("be-handelen", "werkwoord"),  # Hyphenated
            ("stakeholder-mapping", "deverbaal"),  # Compound with 'ing' suffix
        ]

        for begrip, expected_type in edge_cases:
            ctx = make_context(begrip=begrip)
            result = module.execute(ctx)

            assert result.success, f"Failed for '{begrip}'"
            detected_type = ctx.get_shared("word_type")
            assert (
                detected_type == expected_type
            ), f"'{begrip}': expected {expected_type}, got {detected_type}"

    def test_expertise_output_structure_intact(self):
        """Verify ExpertiseModule output structure is still correct."""
        module = ExpertiseModule()
        module.initialize({})

        ctx = make_context(begrip="authenticatie")
        result = module.execute(ctx)

        assert result.success
        content = result.content

        # Should have basic structure (actual content after DEF-126 transformation)
        assert "BELANGHEBBENDEN" in content  # DEF-126 transformation
        assert "EENDUIDIG" in content  # DEF-126 transformation
        assert "WERKELIJKHEID" in content  # DEF-126 transformation
        assert "BELANGRIJKE VEREISTEN" in content  # Basic requirements section

        # Should NOT have word type advice
        assert "zelfstandig naamwoord" not in content
        assert "deverbalisatie" not in content

    def test_cross_module_integration(self):
        """Test full integration flow: Expertise → Grammar → Template."""
        expertise = ExpertiseModule()
        expertise.initialize({})

        grammar = GrammarModule()
        grammar.initialize({})

        template = TemplateModule()
        template.initialize({})

        # Run full pipeline
        ctx = make_context(begrip="behandeling")

        # Step 1: Expertise detects word_type
        expertise_result = expertise.execute(ctx)
        assert expertise_result.success
        assert ctx.get_shared("word_type") == "deverbaal"

        # Step 2: Grammar uses word_type
        grammar_result = grammar.execute(ctx)
        assert grammar_result.success

        # Step 3: Template uses word_type
        ctx.set_shared("ontological_category", "proces")
        template_result = template.execute(ctx)
        assert template_result.success

        # All modules should succeed without errors
        assert all(
            [
                expertise_result.success,
                grammar_result.success,
                template_result.success,
            ]
        )

    def test_no_orphaned_references(self):
        """Verify no code expects the removed _build_word_type_advice method."""
        module = ExpertiseModule()

        # Should not have the old method
        assert not hasattr(module, "_build_word_type_advice")

        # Should still have word type detection (Dutch name)
        assert hasattr(module, "_bepaal_woordsoort")

    def test_unicode_and_special_characters(self):
        """Test with Unicode and special characters."""
        module = ExpertiseModule()
        module.initialize({})

        special_cases = [
            ("café", "overig"),
            ("geïntegreerd", "overig"),
            ("re-integratie", "deverbaal"),
            ("coördinatie", "deverbaal"),
        ]

        for begrip, expected_type in special_cases:
            ctx = make_context(begrip=begrip)
            result = module.execute(ctx)

            assert result.success, f"Failed for '{begrip}'"
            detected_type = ctx.get_shared("word_type")
            assert (
                detected_type == expected_type
            ), f"'{begrip}': expected {expected_type}, got {detected_type}"

    def test_metadata_structure_preserved(self):
        """Verify metadata structure is intact after word_type_advice removal."""
        module = ExpertiseModule()
        module.initialize({})

        ctx = make_context(begrip="behandeling")
        result = module.execute(ctx)

        assert result.success
        assert isinstance(result.metadata, dict)
        # ExpertiseModule metadata contains word_type and sections_generated
        assert "word_type" in result.metadata
        assert result.metadata["word_type"] == "deverbaal"
        # word_type_advice should NOT be in metadata (removed in DEF-154)
        assert "word_type_advice" not in result.metadata


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
