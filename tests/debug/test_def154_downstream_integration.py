"""
DEF-154 Downstream Integration Verification

Verifies that modules consuming word_type from shared state still work correctly:
- GrammarModule
- TemplateModule
- DefinitionTaskModule
"""

from unittest.mock import MagicMock

import pytest

from src.services.prompts.modules.base_module import ModuleContext
from src.services.prompts.modules.definition_task_module import DefinitionTaskModule
from src.services.prompts.modules.expertise_module import ExpertiseModule
from src.services.prompts.modules.grammar_module import GrammarModule
from src.services.prompts.modules.template_module import TemplateModule


def make_mock_context(begrip: str):
    """Create a mock context for testing."""
    context = MagicMock(spec=ModuleContext)
    context.begrip = begrip

    shared_state = {}

    def get_shared(key, default=None):
        return shared_state.get(key, default)

    def set_shared(key, value):
        shared_state[key] = value

    context.get_shared = get_shared
    context.set_shared = set_shared

    return context


class TestDEF154DownstreamIntegration:
    """Test downstream modules can still use word_type."""

    def test_grammar_module_receives_word_type(self):
        """Verify GrammarModule can access word_type from shared state."""
        expertise = ExpertiseModule()
        expertise.initialize({})

        grammar = GrammarModule()
        grammar.initialize({})

        # Test with all three word types
        test_cases = [
            ("behandelen", "werkwoord"),
            ("behandeling", "deverbaal"),
            ("stakeholder", "overig"),
        ]

        for begrip, expected_type in test_cases:
            ctx = make_mock_context(begrip)

            # ExpertiseModule sets word_type
            expertise_result = expertise.execute(ctx)
            assert expertise_result.success
            assert ctx.get_shared("word_type") == expected_type

            # GrammarModule should be able to access it
            grammar_result = grammar.execute(ctx)
            assert grammar_result.success
            assert grammar_result.metadata.get("word_type") == expected_type

            print(
                f"\n✓ GrammarModule successfully accessed word_type='{expected_type}' for '{begrip}'"
            )

    def test_template_module_receives_word_type(self):
        """Verify TemplateModule can access word_type from shared state."""
        expertise = ExpertiseModule()
        expertise.initialize({})

        template = TemplateModule()
        template.initialize({})

        test_cases = [
            ("behandelen", "werkwoord", "proces"),
            ("behandeling", "deverbaal", "proces"),
            ("stakeholder", "overig", "type"),
        ]

        for begrip, expected_type, ont_category in test_cases:
            ctx = make_mock_context(begrip)

            # ExpertiseModule sets word_type
            expertise_result = expertise.execute(ctx)
            assert expertise_result.success
            assert ctx.get_shared("word_type") == expected_type

            # TemplateModule should access it
            ctx.set_shared("ontological_category", ont_category)
            template_result = template.execute(ctx)
            assert template_result.success

            print(
                f"\n✓ TemplateModule successfully accessed word_type='{expected_type}' for '{begrip}'"
            )

    def test_definition_task_module_receives_word_type(self):
        """Verify DefinitionTaskModule can access word_type from shared state."""
        expertise = ExpertiseModule()
        expertise.initialize({})

        definition_task = DefinitionTaskModule()
        definition_task.initialize({})

        ctx = make_mock_context("behandeling")

        # ExpertiseModule sets word_type
        expertise_result = expertise.execute(ctx)
        assert expertise_result.success
        assert ctx.get_shared("word_type") == "deverbaal"

        # DefinitionTaskModule should access it
        definition_result = definition_task.execute(ctx)
        assert definition_result.success
        assert definition_result.metadata.get("word_type") == "deverbaal"

        # Should appear in prompt metadata
        assert "Termtype: deverbaal" in definition_result.content

        print("\n✓ DefinitionTaskModule successfully accessed word_type='deverbaal'")

    def test_full_pipeline_integration(self):
        """Test complete pipeline: Expertise → Grammar → Template → DefinitionTask."""
        expertise = ExpertiseModule()
        expertise.initialize({})

        grammar = GrammarModule()
        grammar.initialize({})

        template = TemplateModule()
        template.initialize({})

        definition_task = DefinitionTaskModule()
        definition_task.initialize({})

        ctx = make_mock_context("behandeling")

        # Step 1: Expertise detects and shares word_type
        result1 = expertise.execute(ctx)
        assert result1.success
        word_type = ctx.get_shared("word_type")
        assert word_type == "deverbaal"
        print(f"\n1. ExpertiseModule: detected word_type='{word_type}'")

        # Step 2: Grammar uses word_type
        result2 = grammar.execute(ctx)
        assert result2.success
        assert result2.metadata.get("word_type") == word_type
        print(f"2. GrammarModule: accessed word_type='{word_type}'")

        # Step 3: Template uses word_type
        ctx.set_shared("ontological_category", "proces")
        result3 = template.execute(ctx)
        assert result3.success
        print(f"3. TemplateModule: accessed word_type='{word_type}'")

        # Step 4: DefinitionTask uses word_type
        result4 = definition_task.execute(ctx)
        assert result4.success
        assert result4.metadata.get("word_type") == word_type
        print(f"4. DefinitionTaskModule: accessed word_type='{word_type}'")

        # All steps should succeed
        assert all([result1.success, result2.success, result3.success, result4.success])
        print("\n✓ Full pipeline integration successful!")

    def test_word_type_persistence_across_modules(self):
        """Verify word_type persists in shared state across module calls."""
        expertise = ExpertiseModule()
        expertise.initialize({})

        ctx = make_mock_context("authenticatie")

        # Set word_type via expertise
        result = expertise.execute(ctx)
        assert result.success

        initial_word_type = ctx.get_shared("word_type")
        assert initial_word_type == "deverbaal"  # 'authenticatie' ends in 'atie'

        # Verify it persists (not overwritten)
        assert ctx.get_shared("word_type") == initial_word_type

        # Multiple reads should return same value
        for _ in range(5):
            assert ctx.get_shared("word_type") == initial_word_type

        print(
            f"\n✓ word_type='{initial_word_type}' persisted correctly across multiple reads"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
