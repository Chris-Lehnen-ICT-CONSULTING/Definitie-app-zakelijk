"""
Anthropic implementation of AsyncAIClient.

Wraps the Anthropic SDK and maps its errors to provider-agnostic types.
"""

from __future__ import annotations

import logging

import anthropic
from anthropic import AsyncAnthropic

from services.ai.base_client import (
    AIClientError,
    AIConnectionClientError,
    AIRateLimitClientError,
    ChatMessage,
    ChatResponse,
)

logger = logging.getLogger(__name__)


class AnthropicClient:
    """AsyncAIClient implementation backed by the Anthropic SDK."""

    def __init__(self, api_key: str) -> None:
        self._client = AsyncAnthropic(api_key=api_key)

    @property
    def provider_name(self) -> str:
        return "anthropic"

    async def chat_completion(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 300,
    ) -> ChatResponse:
        # Anthropic uses a separate `system` parameter (not a system message in the list)
        system_text: str | anthropic.NotGiven = anthropic.NOT_GIVEN
        api_messages: list[dict[str, str]] = []

        for msg in messages:
            if msg.role == "system":
                system_text = msg.content
            else:
                api_messages.append({"role": msg.role, "content": msg.content})

        try:
            response = await self._client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_text,
                messages=api_messages,
            )
        except anthropic.RateLimitError as exc:
            raise AIRateLimitClientError(str(exc)) from exc
        except anthropic.APIConnectionError as exc:
            raise AIConnectionClientError(str(exc)) from exc
        except anthropic.APIError as exc:
            raise AIClientError(str(exc)) from exc

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
