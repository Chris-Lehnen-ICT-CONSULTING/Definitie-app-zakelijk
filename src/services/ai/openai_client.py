"""
OpenAI implementation of AsyncAIClient.

Wraps the OpenAI SDK and maps its errors to provider-agnostic types.
"""

from __future__ import annotations

import logging

from openai import (
    APIConnectionError,
    AsyncOpenAI,
    OpenAIError,
    RateLimitError,
)
from openai.types.chat import ChatCompletionMessageParam

from services.ai.base_client import (
    AIClientError,
    AIConnectionClientError,
    AIRateLimitClientError,
    ChatMessage,
    ChatResponse,
)

logger = logging.getLogger(__name__)


class OpenAIClient:
    """AsyncAIClient implementation backed by the OpenAI SDK."""

    def __init__(self, api_key: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key)

    @property
    def provider_name(self) -> str:
        return "openai"

    async def chat_completion(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 300,
    ) -> ChatResponse:
        sdk_messages: list[ChatCompletionMessageParam] = [
            {"role": m.role, "content": m.content} for m in messages  # type: ignore[misc]
        ]
        try:
            response = await self._client.chat.completions.create(
                model=model,
                messages=sdk_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except RateLimitError as exc:
            raise AIRateLimitClientError(str(exc)) from exc
        except APIConnectionError as exc:
            raise AIConnectionClientError(str(exc)) from exc
        except OpenAIError as exc:
            raise AIClientError(str(exc)) from exc

        content = response.choices[0].message.content
        text = content.strip() if content else ""

        tokens_used = 0
        if response.usage:
            tokens_used = response.usage.total_tokens

        return ChatResponse(
            text=text,
            tokens_used=tokens_used,
            model=response.model,
            metadata={"provider": "openai"},
        )

    async def close(self) -> None:
        await self._client.close()
