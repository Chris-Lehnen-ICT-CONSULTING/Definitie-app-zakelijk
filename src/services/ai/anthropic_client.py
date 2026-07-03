"""
Anthropic implementation of AsyncAIClient.

Wraps the Anthropic SDK and maps its errors to provider-agnostic types.
"""

from __future__ import annotations

import logging
from typing import Literal, cast

import anthropic
from anthropic import AsyncAnthropic
from anthropic.types import MessageParam

from services.ai.base_client import (
    AIAuthenticationClientError,
    AIClientError,
    AIConnectionClientError,
    AIRateLimitClientError,
    ChatMessage,
    ChatResponse,
    sanitize_error,
)

logger = logging.getLogger(__name__)

# DEF-441: sampling-params (temperature/top_p/top_k) zijn verwijderd op
# Opus 4.7+, Sonnet 5 en Fable/Mythos 5 — meesturen geeft een 400
# ("`temperature` is deprecated for this model"). Allowlist van families
# die de parameter nog accepteren; elk ander (nieuw) model krijgt hem
# niet mee. Weglaten is altijd geldig, dus fail-safe voor model-bumps.
_TEMPERATURE_MODEL_FAMILIES = (
    "claude-3",
    "opus-4-0",
    "opus-4-1",
    "opus-4-5",
    "opus-4-6",
    "sonnet-4",
    "haiku-3",
    "haiku-4",
)


def _accepts_temperature(model: str) -> bool:
    """Accepteert dit model de temperature-parameter nog?"""
    model_lc = model.lower()
    return any(family in model_lc for family in _TEMPERATURE_MODEL_FAMILIES)


class AnthropicClient:
    """AsyncAIClient implementation backed by the Anthropic SDK."""

    def __init__(self, api_key: str, timeout: float = 30.0) -> None:
        self._timeout = timeout
        self._client = AsyncAnthropic(api_key=api_key, timeout=timeout)

    @property
    def provider_name(self) -> str:
        return "anthropic"

    async def chat_completion(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 300,
        timeout: float | None = None,
    ) -> ChatResponse:
        if not messages:
            raise AIClientError("messages must not be empty")

        # Anthropic uses a separate `system` parameter (not a system message in the list).
        # SDK ≥0.52 verving de NotGiven-sentinel voor request-params door Omit/omit;
        # messages.create() typeert `system` nu als `str | Iterable[TextBlockParam] | Omit`.
        system_text: str | anthropic.Omit = anthropic.omit
        api_messages: list[MessageParam] = []
        system_count = 0

        for msg in messages:
            if msg.role == "system":
                system_count += 1
                if system_count > 1:
                    raise AIClientError(
                        "Multiple system messages are not supported by Anthropic. "
                        "Combine them into a single system message."
                    )
                system_text = msg.content
            elif msg.role in ("user", "assistant"):
                # De elif garandeert user/assistant op runtime; mypy narrowt een
                # str-attribuut niet via `in (...)`, dus expliciete cast (DEF-439).
                role = cast(Literal["user", "assistant"], msg.role)
                api_messages.append({"role": role, "content": msg.content})
            else:
                raise AIClientError(
                    f"Unsupported message role for Anthropic: {msg.role!r}. "
                    "Expected 'system', 'user', or 'assistant'."
                )

        temperature_param: float | anthropic.Omit = anthropic.omit
        if _accepts_temperature(model):
            temperature_param = temperature
        else:
            logger.debug(
                "temperature weggelaten voor model %s "
                "(sampling-params verwijderd op Opus 4.7+/Sonnet 5/Fable 5, DEF-441)",
                model,
            )

        try:
            response = await self._client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature_param,
                system=system_text,
                messages=api_messages,
                timeout=timeout or self._timeout,
            )
        except anthropic.RateLimitError as exc:
            logger.warning("Anthropic rate limit hit: %s", sanitize_error(str(exc)))
            raise AIRateLimitClientError(sanitize_error(str(exc))) from exc
        except (anthropic.AuthenticationError, anthropic.PermissionDeniedError) as exc:
            # DEF-429: invalid/missing key is permanent — fail fast, do not retry.
            logger.error("Anthropic authentication error: %s", sanitize_error(str(exc)))
            raise AIAuthenticationClientError(sanitize_error(str(exc))) from exc
        except anthropic.APIConnectionError as exc:
            logger.error("Anthropic connection error: %s", sanitize_error(str(exc)))
            raise AIConnectionClientError(sanitize_error(str(exc))) from exc
        except anthropic.APIError as exc:
            logger.error("Anthropic API error: %s", sanitize_error(str(exc)))
            raise AIClientError(sanitize_error(str(exc))) from exc

        # Extract text from content blocks
        text_parts = [
            block.text for block in response.content if hasattr(block, "text")
        ]
        text = "\n".join(text_parts).strip()

        tokens_used = 0
        if response.usage:
            tokens_used = response.usage.input_tokens + response.usage.output_tokens

        return ChatResponse(
            text=text,
            tokens_used=tokens_used,
            model=response.model,
            metadata={"provider": "anthropic"},
        )

    async def close(self) -> None:
        await self._client.close()
