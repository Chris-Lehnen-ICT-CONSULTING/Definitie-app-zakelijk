# ✅ PromptBuilder - MINIMALE AI INTERFACE
"""
Prompt Builder - Minimale AI Service Interface

LEGACY NOTICE: Dit bestand bevat alleen nog de essentiële AI interface functionaliteit.
Alle prompt building logic is gemigreerd naar het modulaire systeem in services/prompts/modules/.

Functies:
- stuur_prompt_naar_gpt(): Legacy AI interface (6 bestanden gebruiken dit nog)
- Fallback error handling voor wanneer AI Service faalt

Voor nieuwe code: gebruik direct services/ai_service.py
"""

import logging
import os

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError

# ✅ Initialiseer OpenAI-client voor fallback
load_dotenv()
_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

logger = logging.getLogger(__name__)


def stuur_prompt_naar_gpt(
    prompt: str, model: str = "gpt-5", temperatuur: float = 0.0, max_tokens: int = 300
) -> str:
    """
    Legacy AI interface - DEPRECATED maar nog in gebruik door 6 bestanden.

    Nu gebruikt nieuwe AI Service voor consistency en betere error handling.
    Gebruik direct AIService.generate_definition() voor nieuwe code.

    Args:
        prompt: De prompt tekst
        model: OpenAI model naam (default: gpt-5)
        temperatuur: Temperature waarde (default: 0.0 voor definitie consistentie)
        max_tokens: Maximum tokens

    Returns:
        AI gegenereerde content
    """
    try:
        # Import en gebruik nieuwe AI Service
        from services.ai_service import get_ai_service

        service = get_ai_service()
        return service.generate_definition(
            prompt=prompt, model=model, temperature=temperatuur, max_tokens=max_tokens
        )

    except Exception as e:
        # Fallback naar legacy implementatie bij problemen
        logger.warning(f"AI Service fallback gebruikt: {e}")
        return _legacy_gpt_call(prompt, model, temperatuur, max_tokens)


def _legacy_gpt_call(
    prompt: str, model: str, temperatuur: float, max_tokens: int
) -> str:
    """
    Legacy GPT call implementatie als fallback.

    Args:
        prompt: De prompt tekst
        model: OpenAI model naam
        temperatuur: Temperature waarde
        max_tokens: Maximum tokens

    Returns:
        AI gegenereerde content
    """
    from utils.cache import cache_gpt_call, cached

    # Generate cache key for this specific call
    cache_key = cache_gpt_call(
        prompt=prompt, model=model, temperature=temperatuur, max_tokens=max_tokens
    )

    # Use cached decorator for the actual GPT call
    @cached(ttl=3600)  # Cache for 1 hour
    def _make_gpt_call(
        cache_key: str, prompt: str, model: str, temperatuur: float, max_tokens: int
    ) -> str:
        try:
            antwoord = _client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperatuur,
                max_tokens=max_tokens,
            )
            return antwoord.choices[0].message.content.strip()
        except OpenAIError as fout:
            msg = f"GPT-aanroep mislukt: {fout}"
            raise RuntimeError(msg) from fout

    return _make_gpt_call(cache_key, prompt, model, temperatuur, max_tokens)


# ✅ Legacy support function for old imports
def verkrijg_openai_client() -> OpenAI:
    """Verkrijgt OpenAI client met error handling voor ontbrekende API key."""
    return _client
