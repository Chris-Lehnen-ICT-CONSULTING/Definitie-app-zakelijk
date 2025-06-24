"""
Package `prompt_builder`: centraal opbouwen en uitvoeren van GPT-prompts
voor definitiegeneratie.  Exporteert alle publieke functies voor korte
imports, bijvoorbeeld:

    from prompt_builder import build_prompt
"""

from .prompt_builder import (
    selecteer_essentiele_regels,
    selecteer_aanvullende_regels,
    bouw_prompt_met_gesplitste_richtlijnen,
    stuur_prompt_naar_gpt,
    build_prompt,
)

__all__ = [
    "selecteer_essentiele_regels",
    "selecteer_aanvullende_regels",
    "bouw_prompt_met_gesplitste_richtlijnen",
    "stuur_prompt_naar_gpt",
    "build_prompt",
]