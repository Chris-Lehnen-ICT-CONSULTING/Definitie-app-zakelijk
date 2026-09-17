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
    # Harde kap op de promptlengte (20K → 35K; DEF-751 stap 2: → 60K). Sinds
    # reviewcorrectie 2 wordt boven de kap niet meer stil afgekapt (dat
    # knipte eindinstructie en conflictcontract weg) maar expliciet geweigerd
    # (`PromptTeLangError`, vóór de modelaanroep). Gemeten 17-09-2026: de
    # rijke prompt (drie contexttypen, categorie type) is ~35,6K zonder
    # contextblokinhoud; het contextblok is ná escaping ≤ 20K
    # (`ContextAwarenessModule`), dus een correcte prompt blijft ≤ ~56K. Het
    # bronnenblok wordt pas ná deze kap toegevoegd.
    max_prompt_length: int = 60000
    enable_component_metadata: bool = True


# Re-export voor backwards compatibility
ModularPromptBuilder = ModularPromptAdapter

# Re-export config class zodat imports blijven werken
__all__ = ["ModularPromptBuilder", "PromptComponentConfig"]
