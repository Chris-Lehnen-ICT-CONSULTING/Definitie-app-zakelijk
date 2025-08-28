"""
Package `prompt_builder`: Legacy AI interface voor prompt execution.

LEGACY NOTICE: Dit package bevat alleen nog essentiële AI interface functionaliteit.
Alle prompt building logic is gemigreerd naar services/prompts/modules/.

Voor nieuwe code: gebruik direct services.ai_service.AIService
"""

# 📦 prompt_builder/__init__.py
# ✅ Legacy AI interface export

from .prompt_builder import (
    stuur_prompt_naar_gpt,  # ✅ Legacy AI interface (nog 6 consumers)
    verkrijg_openai_client,  # ✅ Legacy OpenAI client access
)

__all__ = [
    "stuur_prompt_naar_gpt",
    "verkrijg_openai_client",
]
