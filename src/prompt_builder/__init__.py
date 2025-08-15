"""
Package `prompt_builder`: centraal opbouwen en uitvoeren van GPT-prompts
voor definitiegeneratie.

Exporteert alle publieke functies voor korte imports, bijvoorbeeld:
    from prompt_builder import PromptBouwer

Dit module biedt legacy functionaliteit voor het bouwen van AI prompts.
"""

# 📦 prompt_builder/__init__.py
# ✅ Centrale export van classgebaseerde promptopbouw

from .prompt_builder import PromptBouwer  # ✅ Nieuwe naam voor PromptBuilder
from .prompt_builder import PromptConfiguratie  # ✅ Nieuwe naam voor PromptConfig
from .prompt_builder import stuur_prompt_naar_gpt  # ✅ GPT-aanroepfunctie

__all__ = [
    "PromptBouwer",
    "PromptConfiguratie",
    "stuur_prompt_naar_gpt",
]
