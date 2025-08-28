#!/usr/bin/env python3
"""
Trace prompt strategy decision flow voor vaststellingsovereenkomst.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from services.definition_generator_config import UnifiedGeneratorConfig
from services.definition_generator_context import EnrichedContext
from services.definition_generator_prompts import UnifiedPromptBuilder

# Simuleer de context zoals die wordt aangemaakt in orchestrator
base_context = {
    "organisatorisch": ["Justid"],
    "juridisch": [],
    "wettelijk": [],
    "ontologische_categorie": "proces",  # Dit is het probleem!
}

context = EnrichedContext(
    base_context=base_context,
    sources=[],
    expanded_terms={},
    confidence_scores={},
    metadata={"ontologische_categorie": "proces"},
)

# Trace de decision flow
print("=== TRACE PROMPT STRATEGY DECISION ===\n")

# Maak prompt builder
config = UnifiedGeneratorConfig()
builder = UnifiedPromptBuilder(config)

print(f"Available strategies: {builder.get_available_strategies()}")
print("\nContext analysis:")
print(f"- Sources count: {len(context.sources)}")
print("- Base context items:")

# Tel items zoals _select_strategy doet
total_items = 0
for key, value in base_context.items():
    item_count = len(value) if hasattr(value, "__len__") else 1
    print(f"  - {key}: {value} → {item_count} items")
    total_items += item_count

print(f"\nTotal context items: {total_items}")
print("Legacy threshold: ≤ 3 items")
print(f"Legacy selected? {total_items <= 3}")

# Check wat strategy wordt gekozen
strategy = builder._select_strategy("vaststellingsovereenkomst", context)
print(f"\nSelected strategy: {strategy}")

# Toon wat er gebeurt als we categorie fixen
print("\n=== ALS WE CATEGORIE ALS LIJST ZETTEN ===")
base_context_fixed = {
    "organisatorisch": ["Justid"],
    "juridisch": [],
    "wettelijk": [],
    # Categorie hoort niet in base_context!
}
context_fixed = EnrichedContext(
    base_context=base_context_fixed,
    sources=[],
    expanded_terms={},
    confidence_scores={},
    metadata={"ontologische_categorie": "proces"},
)

total_items_fixed = sum(len(items) for items in base_context_fixed.values())
print(f"Total items (fixed): {total_items_fixed}")
print(f"Legacy selected? {total_items_fixed <= 3}")
