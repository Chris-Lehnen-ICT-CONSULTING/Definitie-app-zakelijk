#!/usr/bin/env python3
"""Legacy: test om te verifiëren dat legacy builder actief is (informatief)."""
import os
import sys

import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.services.definition_generator_config import UnifiedGeneratorConfig
from src.services.definition_generator_context import EnrichedContext
from src.services.definition_generator_prompts import UnifiedPromptBuilder


def test_legacy_activation():
    """Test of de legacy builder correct wordt geselecteerd."""

    # Maak test context
    context = EnrichedContext(
        base_context={
            "organisatorisch": ["Test"],
            "juridisch": ["Justid"],
            "wettelijk": [],
        },
        sources=[],
        expanded_terms={},
        confidence_scores={},
        metadata={"ontologische_categorie": "proces"},
    )

    # Test strategy selection
    builder = UnifiedPromptBuilder(UnifiedGeneratorConfig())
    strategy = builder._select_strategy("testbegrip", context)

    print(f"🔍 Selected strategy: {strategy}")
    print(f"✅ Success: {'YES' if strategy == 'legacy' else 'NO'}")
    print(
        f"\n📊 Context items count: {sum(len(items) for items in context.base_context.values())}"
    )

    # Test prompt generatie
    print("\n🔧 Testing prompt generation...")
    try:
        prompt = builder.build_prompt("testbegrip", context)
        print(f"📝 Prompt length: {len(prompt)} characters")
        print(
            f"✅ Contains toetsregels: {'toetsregels' in prompt.lower() or 'richtlijnen' in prompt.lower()}"
        )
        print(
            f"✅ Contains ontology instructions: {'ontologische categorie' in prompt.lower()}"
        )

        # Show first 500 chars
        print(
            f"\n📄 First 500 characters of prompt:\n{'-'*50}\n{prompt[:500]}...\n{'-'*50}"
        )

    except Exception as e:
        print(f"❌ Error generating prompt: {e}")

    return strategy == "legacy"


if __name__ == "__main__":
    print("🚀 Testing Legacy Builder Activation\n")
    success = test_legacy_activation()

    if success:
        print("\n✅ SUCCESS: Legacy builder is now active!")
        print("🎯 The system should now use all 78+ validation rules")
    else:
        print("\n❌ FAILED: Legacy builder is still not active")
        print("🔍 Check the fixes and try again")

# Markeer als legacy/informatief, uitgesloten in PR-profielen
pytestmark = pytest.mark.xfail(
    reason="Legacy builder activation script (excluded in PR)", strict=False
)
