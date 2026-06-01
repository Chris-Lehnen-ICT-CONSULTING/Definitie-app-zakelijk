"""
OpenAI implementation of AsyncAIClient.

Wraps the OpenAI SDK and maps its errors to provider-agnostic types.
"""

from __future__ import annotations

import logging
from typing import Any

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
    sanitize_error,
)

logger = logging.getLogger(__name__)


class OpenAIClient:
    """AsyncAIClient implementation backed by the OpenAI SDK."""

    def __init__(self, api_key: str, timeout: float = 30.0) -> None:
        self._timeout = timeout
        self._client = AsyncOpenAI(api_key=api_key, timeout=timeout)

    @property
    def provider_name(self) -> str:
        return "openai"

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

        sdk_messages: list[ChatCompletionMessageParam] = [
            {"role": m.role, "content": m.content} for m in messages  # type: ignore[misc]
        ]
        try:
            # Newer models (gpt-5+, o1+, o3+) require max_completion_tokens
            # instead of max_tokens. Detect and use the correct parameter.
            uses_new_param = any(model.startswith(p) for p in ("gpt-5", "o1", "o3"))
            # dict[str, Any] zodat de **unpacking matcht met de OpenAI SDK overload
            # (zonder Any inferrert mypy dict[str, int] wat geen overload-variant matcht).
            token_kwargs: dict[str, Any] = (
                {"max_completion_tokens": max_tokens}
                if uses_new_param
                else {"max_tokens": max_tokens}
            )
            response = await self._client.chat.completions.create(
                model=model,
                messages=sdk_messages,
                temperature=temperature,
                timeout=timeout or self._timeout,
                **token_kwargs,
            )
        except RateLimitError as exc:
            logger.warning("OpenAI rate limit hit: %s", sanitize_error(str(exc)))
            raise AIRateLimitClientError(sanitize_error(str(exc))) from exc
        except APIConnectionError as exc:
            logger.error("OpenAI connection error: %s", sanitize_error(str(exc)))
            raise AIConnectionClientError(sanitize_error(str(exc))) from exc
        except OpenAIError as exc:
            logger.error("OpenAI API error: %s", sanitize_error(str(exc)))
            raise AIClientError(sanitize_error(str(exc))) from exc

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
