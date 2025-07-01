"""
Package `prompt_builder`: centraal opbouwen en uitvoeren van GPT-prompts
voor definitiegeneratie.  Exporteert alle publieke functies voor korte
imports, bijvoorbeeld:

    from prompt_builder import build_prompt
"""

# 📦 prompt_builder/__init__.py
# ✅ Centrale export van classgebaseerde promptopbouw

from .prompt_builder import (
    PromptBouwer,             # ✅ Nieuwe naam voor PromptBuilder
    PromptConfiguratie,       # ✅ Nieuwe naam voor PromptConfig
    stuur_prompt_naar_gpt,    # ✅ GPT-aanroepfunctie
)

__all__ = [
    "PromptBouwer",
    "PromptConfiguratie",
    "stuur_prompt_naar_gpt",
]