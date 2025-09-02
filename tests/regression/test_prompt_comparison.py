"""Test script to compare ModularPromptBuilder with Legacy output."""

import hashlib
import json

from prompt_builder.prompt_builder import PromptBouwer
from services.definition_generator_context import EnrichedContext
from services.definition_generator_prompts import UnifiedPromptBuilder
from services.prompts.modular_prompt_builder import (
    ModularPromptBuilder,
    PromptComponentConfig,
)


def create_test_context(category="proces"):
    """Create test context with ontological category."""
    return EnrichedContext(
        base_context={
            "organisatorisch": ["DJI"],
            "domein": ["Rechtspraak"],
        },
        metadata={
            "ontologische_categorie": category,
            "timestamp": "2025-08-26T10:00:00",
        },
        sources=[],
    )


def test_prompt_generation():
    """Test prompt generation across different strategies."""
    print("=== PROMPT GENERATION TEST ===\n")

    # Test cases
    test_cases = [
        ("voorwaardelijk", "proces"),
        ("sanctie", "resultaat"),
        ("verdachte", "type"),
        ("rechtbank Amsterdam", "exemplaar"),
    ]

    # Initialize builders
    modular_builder = ModularPromptBuilder()
    # legacy_builder = PromptBouwer()  # Skip legacy for now
    unified_builder = UnifiedPromptBuilder(None)

    results = []

    for begrip, category in test_cases:
        print(f"\nTesting: {begrip} (category: {category})")
        print("-" * 50)

        context = create_test_context(category)

        # Generate prompts
        try:
            # Modular prompt
            modular_prompt = modular_builder.build_prompt(begrip, context, None)
            modular_hash = hashlib.md5(modular_prompt.encode()).hexdigest()[:8]

            # Stats
            result = {
                "begrip": begrip,
                "category": category,
                "modular_length": len(modular_prompt),
                "modular_hash": modular_hash,
                "category_guidance_present": f"**{category.upper()} CATEGORIE"
                in modular_prompt,
            }

            results.append(result)

            print(f"✓ Modular: {result['modular_length']} chars (hash: {modular_hash})")
            print(
                f"✓ Category guidance: {'Yes' if result['category_guidance_present'] else 'No'}"
            )

            # Check for category-specific content
            if category == "proces" and "activiteit waarbij" in modular_prompt:
                print("✓ Process-specific language found")
            elif category == "resultaat" and "resultaat van" in modular_prompt:
                print("✓ Result-specific language found")
            elif category == "type" and "soort" in modular_prompt:
                print("✓ Type-specific language found")
            elif category == "exemplaar" and "specifiek exemplaar" in modular_prompt:
                print("✓ Instance-specific language found")

        except Exception as e:
            print(f"✗ Error: {e}")
            results.append({"begrip": begrip, "category": category, "error": str(e)})

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for r in results:
        if "error" in r:
            print(f"• {r['begrip']} ({r['category']}): ERROR - {r['error']}")
        else:
            print(
                f"• {r['begrip']} ({r['category']}): "
                f"Modular={r['modular_length']} chars, "
                f"Cat.guidance={'✓' if r['category_guidance_present'] else '✗'}"
            )

    # Test unified builder strategy selection
    print("\n" + "=" * 60)
    print("UNIFIED BUILDER STRATEGY SELECTION TEST")
    print("=" * 60)

    for begrip, category in test_cases[:2]:  # Test first two cases
        context = create_test_context(category)
        strategy = unified_builder._select_strategy(begrip, context, None)
        print(f"• {begrip} ({category}): Selected strategy = {strategy}")

    print("\n✅ Test completed!")


def test_component_configuration():
    """Test component configuration options."""
    print("\n" + "=" * 60)
    print("COMPONENT CONFIGURATION TEST")
    print("=" * 60)

    # Test with different configurations
    configs = [
        ("Full config", PromptComponentConfig()),
        ("No validation rules", PromptComponentConfig(include_validation_rules=False)),
        (
            "No forbidden patterns",
            PromptComponentConfig(include_forbidden_patterns=False),
        ),
        (
            "Minimal (role + ontological only)",
            PromptComponentConfig(
                include_context=False,
                include_validation_rules=False,
                include_forbidden_patterns=False,
                include_final_instructions=False,
            ),
        ),
    ]

    begrip = "toezicht"
    context = create_test_context("proces")

    for name, config in configs:
        builder = ModularPromptBuilder(config)
        prompt = builder.build_prompt(begrip, context, None)
        metadata = builder.get_component_metadata(begrip, context)

        print(f"\n{name}:")
        print(f"  - Active components: {metadata['active_components']}/6")
        print(f"  - Prompt length: {len(prompt)} chars")
        print(f"  - Estimated tokens: {metadata.get('estimated_prompt_tokens', 'N/A')}")


if __name__ == "__main__":
    test_prompt_generation()
    test_component_configuration()
