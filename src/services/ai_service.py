"""
AI Service - Centralized OpenAI interface with caching and error handling.

Deze service vervangt stuur_prompt_naar_gpt() uit prompt_builder.py
en biedt een moderne, herbruikbare interface voor AI calls.
"""

import logging
import os
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError
from utils.cache import cache_gpt_call, cached

from config.config_manager import get_default_model, get_default_temperature

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class AIRequest:
    """Request object voor AI calls."""

    prompt: str
    model: str | None = None
    temperature: float | None = None
    max_tokens: int = 300
    system_message: str | None = None

    def __post_init__(self):
        """Fill in defaults from central configuration."""
        if self.model is None:
            self.model = get_default_model()
        if self.temperature is None:
            self.temperature = get_default_temperature()


@dataclass
class AIResponse:
    """Response object van AI calls."""

    content: str
    model: str
    tokens_used: int
    cached: bool = False
    metadata: dict[str, Any] = None


class AIService:
    """
    Centralized service voor alle AI operaties.

    Vervangt de legacy stuur_prompt_naar_gpt() functie met:
    - Better error handling
    - Intelligent caching
    - Request/response objects
    - Logging en monitoring
    """

    def __init__(self):
        """Initialize AI service met OpenAI client."""
        self._client = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize OpenAI client met error handling."""
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "OPENAI_API_KEY ontbreekt. Zet deze in .env of je CI-secrets."
                )

            self._client = OpenAI(api_key=api_key)
            logger.info("AIService geïnitialiseerd met OpenAI client")

        except Exception as e:
            logger.error(f"Fout bij initialiseren OpenAI client: {e}")
            raise

    async def generate_async(self, request: AIRequest) -> AIResponse:
        """
        Asynchrone AI generation (placeholder voor toekomstige implementatie).

        Args:
            request: AI request object

        Returns:
            AI response object
        """
        # Voor nu redirect naar sync versie
        return self.generate(request)

    def generate(self, request: AIRequest) -> AIResponse:
        """
        Genereer AI response met caching en error handling.

        Args:
            request: AI request object

        Returns:
            AI response object

        Raises:
            AIServiceError: Bij AI service fouten
        """
        try:
            # Generate cache key
            cache_key = cache_gpt_call(
                prompt=request.prompt,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )

            # Use cached decorator voor actual call
            @cached(ttl=3600)  # Cache voor 1 uur
            def _make_ai_call(
                cache_key: str,
                prompt: str,
                model: str,
                temperature: float,
                max_tokens: int,
                system_message: str | None = None,
            ) -> tuple[str, int, bool]:
                logger.debug(
                    f"AI call: model={model}, temp={temperature}, max_tokens={max_tokens}"
                )

                # Prepare messages
                messages = []
                if system_message:
                    messages.append({"role": "system", "content": system_message})
                messages.append({"role": "user", "content": prompt})

                # Model-specifieke API parameters
                if model == "gpt-5":
                    # ALLEEN GPT-5 gebruikt max_completion_tokens
                    response = self._client.chat.completions.create(
                        model=model,
                        messages=messages,
                        temperature=temperature,
                        max_completion_tokens=max_tokens,
                    )
                else:
                    # GPT-4.1 en andere modellen gebruiken gewoon max_tokens
                    response = self._client.chat.completions.create(
                        model=model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )

                content = response.choices[0].message.content.strip()
                tokens = response.usage.total_tokens if response.usage else 0

                return content, tokens, False  # False = not from cache

            # Make the call
            content, tokens, from_cache = _make_ai_call(
                cache_key=cache_key,
                prompt=request.prompt,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                system_message=request.system_message,
            )

            logger.info(
                f"AI response generated: {len(content)} chars, "
                f"{tokens} tokens, cached={from_cache}"
            )

            return AIResponse(
                content=content,
                model=request.model,
                tokens_used=tokens,
                cached=from_cache,
                metadata={
                    "request_params": {
                        "temperature": request.temperature,
                        "max_tokens": request.max_tokens,
                    }
                },
            )

        except OpenAIError as e:
            logger.error(f"OpenAI API fout: {e}")
            raise AIServiceError(f"AI service call mislukt: {e}") from e
        except Exception as e:
            logger.error(f"Onverwachte fout in AI service: {e}")
            raise AIServiceError(f"AI service interne fout: {e}") from e

    def generate_definition(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int = 300,
    ) -> str:
        """
        Legacy compatibility method - vervangt stuur_prompt_naar_gpt().

        Args:
            prompt: De prompt tekst
            model: OpenAI model naam
            temperature: Temperature waarde
            max_tokens: Maximum tokens

        Returns:
            AI gegenereerde content

        Raises:
            AIServiceError: Bij AI service fouten
        """
        # Use central config for defaults
        if model is None:
            model = get_default_model()
        if temperature is None:
            temperature = get_default_temperature()
        request = AIRequest(
            prompt=prompt, model=model, temperature=temperature, max_tokens=max_tokens
        )

        response = self.generate(request)
        return response.content


class AIServiceError(Exception):
    """Exception voor AI service fouten."""


# Global service instance voor backward compatibility
_ai_service = None


def get_ai_service() -> AIService:
    """
    Get global AI service instance.

    Returns:
        AIService instance
    """
    global _ai_service  # noqa: PLW0603
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service


def stuur_prompt_naar_gpt(
    prompt: str,
    model: str | None = None,
    temperatuur: float | None = None,
    max_tokens: int = 300,
) -> str:
    """
    Legacy compatibility function - DEPRECATED.

    Use AIService.generate_definition() or get_ai_service().generate() instead.

    Args:
        prompt: De prompt tekst
        model: OpenAI model naam
        temperatuur: Temperature waarde
        max_tokens: Maximum tokens

    Returns:
        AI gegenereerde content
    """
    logger.warning(
        "stuur_prompt_naar_gpt() is deprecated. "
        "Use AIService.generate_definition() instead."
    )

    # Use central config for defaults
    if model is None:
        model = get_default_model()
    if temperatuur is None:
        temperatuur = get_default_temperature()
    service = get_ai_service()
    return service.generate_definition(
        prompt=prompt, model=model, temperature=temperatuur, max_tokens=max_tokens
    )
