"""
Package `prompt_builder`: centraal opbouwen en uitvoeren van GPT-prompts
voor definitiegeneratie.  Exporteert alle publieke functies voor korte
imports, bijvoorbeeld:

    from prompt_builder import build_prompt
"""

from .prompt_builder import (
    bouw_prompt_met_gesplitste_richtlijnen,
    stuur_prompt_naar_gpt,
    bepaal_term_type,
    filter_toetsregels_voor_prompt,
)

# Alias zodat ook 'build_prompt(...)' gebruikt kan worden
from .prompt_builder import bouw_prompt_met_gesplitste_richtlijnen as build_prompt

__all__ = [
    "bouw_prompt_met_gesplitste_richtlijnen",
    "stuur_prompt_naar_gpt",
    "bepaal_term_type",
    "filter_toetsregels_voor_prompt",
    "build_prompt",
]