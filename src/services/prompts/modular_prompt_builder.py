"""
Modulaire Prompt Builder - Nu gebruikt ECHT modulaire architectuur!

Dit bestand is een facade voor backwards compatibility.
De echte implementatie zit in modular_prompt_adapter.py die het
nieuwe PromptOrchestrator + modules systeem gebruikt.

Legacy code is gearchiveerd in modular_prompt_builder.py.backup
"""

from dataclasses import dataclass

# Import de nieuwe implementatie
from .modular_prompt_adapter import ModularPromptAdapter


@dataclass
class PromptComponentConfig:
    """Configuratie voor welke componenten te gebruiken in ModularPromptBuilder."""

    # Basis componenten
    include_role: bool = True
    include_context: bool = True
    include_ontological: bool = True
    include_validation_rules: bool = True
    include_forbidden_patterns: bool = True
    include_final_instructions: bool = True

    # Per-category customization
    detailed_category_guidance: bool = True
    include_examples_in_rules: bool = True
    compact_mode: bool = False  # Voor kortere prompts (experimenteel)

    # Advanced configuratie
    max_prompt_length: int = (
        35000  # Hard limit voor prompt lengte (verhoogd van 20K naar 35K)
    )
    enable_component_metadata: bool = True


# Re-export voor backwards compatibility
ModularPromptBuilder = ModularPromptAdapter

# Re-export config class zodat imports blijven werken
__all__ = ["ModularPromptBuilder", "PromptComponentConfig"]
