"""
Tests voor ModularPromptBuilder - Modulaire Prompt Architectuur.

Test alle 6 componenten afzonderlijk en als geheel.
Volgt MODULAIRE_PROMPT_ARCHITECTUUR_WORKFLOW.md testing strategie.
"""

import pytest

from services.definition_generator_config import UnifiedGeneratorConfig
from services.definition_generator_context import EnrichedContext
from services.prompts.modular_prompt_builder import (
    ModularPromptBuilder,
    PromptComponentConfig,
)

pytestmark = [pytest.mark.integration]


def create_test_context(
    ontologische_categorie: str | None = None,
    organisatorisch: list | None = None,
    domein: list | None = None,
) -> EnrichedContext:
    """Helper function om test context te maken."""

    base_context = {}
    if organisatorisch:
        base_context["organisatorisch"] = organisatorisch
    if domein:
        base_context["domein"] = domein

    metadata = {}
    if ontologische_categorie:
        metadata["ontologische_categorie"] = ontologische_categorie

    return EnrichedContext(
        base_context=base_context,
        sources=[],
        expanded_terms={},
        confidence_scores={},
        metadata=metadata,
    )


class TestModularPromptBuilderFoundation:
    """Test de foundation (Fase 1) van ModularPromptBuilder."""

    def test_modular_prompt_builder_initialization(self):
        """Test dat ModularPromptBuilder correct initialiseert."""

        # Default configuratie
        builder = ModularPromptBuilder()
        assert builder.component_config is not None
        assert builder.component_config.include_role is True
        assert builder.component_config.include_context is True
        assert builder.component_config.include_ontological is True

        # Custom configuratie
        custom_config = PromptComponentConfig(
            include_validation_rules=False, include_forbidden_patterns=False
        )
        builder_custom = ModularPromptBuilder(custom_config)
        assert builder_custom.component_config.include_validation_rules is False
        assert builder_custom.component_config.include_forbidden_patterns is False

    def test_get_strategy_name(self):
        """Test dat strategy name correct is."""
        builder = ModularPromptBuilder()
        assert builder.get_strategy_name() == "modular"


class TestBasicPromptGeneration:
    """Test basis prompt generatie met Component 1 & 2 (Fase 1.2)."""

    def test_error_handling_empty_begrip(self):
        """Test error handling voor lege begrippen."""
        builder = ModularPromptBuilder()
        context = create_test_context()
        config = UnifiedGeneratorConfig()

        # Empty string
        with pytest.raises(ValueError, match="Begrip mag niet leeg zijn"):
            builder.build_prompt("", context, config)

        # Whitespace only
        with pytest.raises(ValueError, match="Begrip mag niet leeg zijn"):
            builder.build_prompt("   ", context, config)

    def test_performance_baseline(self):
        """Test performance baseline voor Fase 1 componenten."""
        import time

        builder = ModularPromptBuilder()
        context = create_test_context(
            ontologische_categorie="proces",
            organisatorisch=["NP"],
            domein=["Nederlands Politie"],
        )
        config = UnifiedGeneratorConfig()

        start_time = time.time()
        prompt = builder.build_prompt("voorwaardelijk", context, config)
        generation_time = time.time() - start_time

        # Performance moet acceptabel zijn (< 1s voor basis componenten)
        assert (
            generation_time < 1.0
        ), f"Prompt generatie te langzaam: {generation_time:.3f}s"

        # Prompt moet volledige lengte hebben nu alle componenten geïmplementeerd zijn
        assert 5000 < len(prompt) < 20000  # Volledige prompt met alle 6 componenten

    def test_build_prompt_includes_begrip(self):
        """Integratie-invariant: het te definiëren begrip komt voor in de
        geassembleerde prompt (stabiel contract, niet gebonden aan exacte
        sectie-bewoording — vervangt de verwijderde brittle string-asserts)."""
        builder = ModularPromptBuilder()
        context = create_test_context(
            ontologische_categorie="proces", organisatorisch=["NP"]
        )
        config = UnifiedGeneratorConfig()

        prompt = builder.build_prompt(
            "voorwaardelijke_invrijheidstelling", context, config
        )

        assert isinstance(prompt, str) and prompt.strip()
        assert "voorwaardelijke_invrijheidstelling" in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
