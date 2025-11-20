"""
DEF-154 Prompt Output Verification

Captures actual prompt output from ExpertiseModule to verify:
1. No word_type_advice present
2. Word type detection still works
3. Shared state propagates correctly
4. Output format is correct
"""

from unittest.mock import MagicMock

import pytest

from src.services.prompts.modules.base_module import ModuleContext
from src.services.prompts.modules.expertise_module import ExpertiseModule


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


class TestDEF154PromptOutput:
    """Test actual prompt output from ExpertiseModule."""

    def test_werkwoord_output(self):
        """Test output for werkwoord (verb) type begrip."""
        module = ExpertiseModule()
        module.initialize({})

        ctx = make_mock_context("behandelen")
        result = module.execute(ctx)

        print("\n" + "=" * 80)
        print("WERKWOORD (behandelen) OUTPUT:")
        print("=" * 80)
        print(result.content)
        print("=" * 80)
        print(f"Metadata: {result.metadata}")
        print(f"Word type stored in shared state: {ctx.get_shared('word_type')}")
        print("=" * 80)

        # Verify no category advice
        assert "zelfstandig naamwoord" not in result.content.lower()
        assert "werkwoord" not in result.content.lower()
        assert "woordsoort" not in result.content.lower()

        # Verify word type detection worked
        assert ctx.get_shared("word_type") == "werkwoord"
        assert result.metadata["word_type"] == "werkwoord"

        # Verify core content present
        assert "BELANGHEBBENDEN" in result.content
        assert "EENDUIDIG" in result.content
        assert "WERKELIJKHEID" in result.content

    def test_deverbaal_output(self):
        """Test output for deverbaal (nominalized verb) type begrip."""
        module = ExpertiseModule()
        module.initialize({})

        ctx = make_mock_context("behandeling")
        result = module.execute(ctx)

        print("\n" + "=" * 80)
        print("DEVERBAAL (behandeling) OUTPUT:")
        print("=" * 80)
        print(result.content)
        print("=" * 80)
        print(f"Metadata: {result.metadata}")
        print(f"Word type stored in shared state: {ctx.get_shared('word_type')}")
        print("=" * 80)

        # Verify no category advice
        assert "zelfstandig naamwoord" not in result.content.lower()
        assert "deverbaal" not in result.content.lower()
        assert "deverbalisatie" not in result.content.lower()

        # Verify word type detection worked
        assert ctx.get_shared("word_type") == "deverbaal"
        assert result.metadata["word_type"] == "deverbaal"

        # Verify core content present
        assert "BELANGHEBBENDEN" in result.content

    def test_overig_output(self):
        """Test output for overig (other) type begrip."""
        module = ExpertiseModule()
        module.initialize({})

        ctx = make_mock_context("stakeholder")
        result = module.execute(ctx)

        print("\n" + "=" * 80)
        print("OVERIG (stakeholder) OUTPUT:")
        print("=" * 80)
        print(result.content)
        print("=" * 80)
        print(f"Metadata: {result.metadata}")
        print(f"Word type stored in shared state: {ctx.get_shared('word_type')}")
        print("=" * 80)

        # Verify no category advice
        assert "zelfstandig naamwoord" not in result.content.lower()
        assert "overig" not in result.content.lower()

        # Verify word type detection worked
        assert ctx.get_shared("word_type") == "overig"
        assert result.metadata["word_type"] == "overig"

        # Verify core content present
        assert "BELANGHEBBENDEN" in result.content

    def test_output_structure_consistent(self):
        """Verify output structure is consistent across word types."""
        module = ExpertiseModule()
        module.initialize({})

        test_begrippen = [
            ("behandelen", "werkwoord"),
            ("behandeling", "deverbaal"),
            ("stakeholder", "overig"),
        ]

        for begrip, expected_type in test_begrippen:
            ctx = make_mock_context(begrip)
            result = module.execute(ctx)

            # All should have same structure
            assert "BELANGHEBBENDEN" in result.content
            assert "EENDUIDIG" in result.content
            assert "WERKELIJKHEID" in result.content
            assert "BELANGRIJKE VEREISTEN" in result.content

            # None should have word type advice
            assert "zelfstandig naamwoord" not in result.content.lower()
            assert "woordsoort" not in result.content.lower()

            # All should detect word type correctly
            assert ctx.get_shared("word_type") == expected_type


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])  # -s to show print output
