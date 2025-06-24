"""
Module prompt_builder: centraal opbouwen en uitvoeren van GPT-prompts voor definitiegeneratie.
"""
from .prompt_builder import (
    selecteer_essentiele_regels,
    selecteer_aanvullende_regels,
    bouw_prompt_met_gesplitste_richtlijnen,
    stuur_prompt_naar_gpt,
    )

__all__ = [
    "selecteer_essentiele_regels",
    "selecteer_aanvullende_regels",
    "bouw_prompt_met_gesplitste_richtlijnen",
    "stuur_prompt_naar_gpt",
   ]
