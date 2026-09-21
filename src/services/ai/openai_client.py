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
    AuthenticationError,
    OpenAIError,
    PermissionDeniedError,
    RateLimitError,
)
from openai.types.chat import ChatCompletionMessageParam

from services.ai.base_client import (
    AIAuthenticationClientError,
    AIClientError,
    AIConnectionClientError,
    AIRateLimitClientError,
    ChatMessage,
    ChatResponse,
    Eventloopwacht,
    foutketen,
    sanitize_error,
)

logger = logging.getLogger(__name__)


class OpenAIClient:
    """AsyncAIClient implementation backed by the OpenAI SDK."""

    def __init__(
        self,
        api_key: str,
        timeout: float = 30.0,
        max_retries: int = 2,
        rebind_on_new_loop: bool = True,
    ) -> None:
        # DEF-566: max_retries gaat 1-op-1 naar de SDK (default 2 = SDK-default);
        # CI-testruns zetten 0 via create_ai_client om retry-stapeling te stoppen.
        self._timeout = timeout
        self._sdk_opties: dict[str, Any] = {
            "api_key": api_key,
            "timeout": timeout,
            "max_retries": max_retries,
        }
        self._client = AsyncOpenAI(**self._sdk_opties)
        # DEF-766 (correctieronde 2, C): zie AnthropicClient._sdk_voor_deze_loop.
        self._rebind_on_new_loop = rebind_on_new_loop
        self._loopwacht = Eventloopwacht()

    @property
    def provider_name(self) -> str:
        return "openai"

    def _sdk_voor_deze_loop(self) -> AsyncOpenAI:
        """Verse SDK-client (nieuw verbindingspool) zodra een andere eventloop
        draait dan bij het vorige gebruik; anders dezelfde client."""
        if self._rebind_on_new_loop and self._loopwacht.gewisseld():
            logger.info(
                "OpenAI-client: andere eventloop dan bij het vorige gebruik; "
                "verse SDK-client (verbindingspool) aangemaakt"
            )
            self._client = AsyncOpenAI(**self._sdk_opties)
        return self._client

    async def chat_completion(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 300,
        timeout: float | None = None,
        max_retries: int | None = None,
    ) -> ChatResponse:
        if not messages:
            raise AIClientError("messages must not be empty")

        sdk_messages: list[ChatCompletionMessageParam] = [
            {"role": m.role, "content": m.content} for m in messages  # type: ignore[misc]
        ]
        # DEF-766 (opt-in): SDK-retries per aanroep; zonder argument de clientdefault.
        basis = self._sdk_voor_deze_loop()
        sdk = (
            basis.with_options(max_retries=int(max_retries))
            if max_retries is not None
            else basis
        )
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
            response = await sdk.chat.completions.create(
                model=model,
                messages=sdk_messages,
                temperature=temperature,
                timeout=timeout or self._timeout,
                **token_kwargs,
            )
        except RateLimitError as exc:
            logger.warning("OpenAI rate limit hit: %s", sanitize_error(str(exc)))
            raise AIRateLimitClientError(sanitize_error(str(exc))) from exc
        except (AuthenticationError, PermissionDeniedError) as exc:
            # DEF-429: invalid/missing key is permanent — fail fast, do not retry.
            logger.error("OpenAI authentication error: %s", sanitize_error(str(exc)))
            raise AIAuthenticationClientError(sanitize_error(str(exc))) from exc
        except APIConnectionError as exc:
            logger.error("OpenAI connection error: %s", foutketen(exc))
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
