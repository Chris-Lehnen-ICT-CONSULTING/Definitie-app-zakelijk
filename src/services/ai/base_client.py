"""
Provider-agnostic AI client abstractions.

Defines the Protocol, data types, and error hierarchy that all AI provider
clients must conform to. Application code imports from here instead of
directly from openai/anthropic SDKs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ChatMessage:
    """Provider-agnostic chat message."""

    role: str  # "system", "user", "assistant"
    content: str


@dataclass(frozen=True)
class ChatResponse:
    """Provider-agnostic chat completion response."""

    text: str
    tokens_used: int  # Total tokens (prompt + completion), 0 if unavailable
    model: str
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Error hierarchy
# ---------------------------------------------------------------------------


class AIClientError(Exception):
    """Base error for all AI client operations."""


class AIRateLimitClientError(AIClientError):
    """Rate limit exceeded by the AI provider."""


class AIConnectionClientError(AIClientError):
    """Connection or network error talking to the AI provider."""


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class AsyncAIClient(Protocol):
    """Protocol that every AI provider client must implement."""

    @property
    def provider_name(self) -> str:
        """Return provider identifier, e.g. 'openai' or 'anthropic'."""
        ...

    async def chat_completion(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 300,
    ) -> ChatResponse:
        """Send a chat completion request and return a provider-agnostic response.

        Raises:
            AIRateLimitClientError: When the provider rate-limits the request.
            AIConnectionClientError: On network / connection failures.
            AIClientError: On any other provider error.
        """
        ...

    async def close(self) -> None:
        """Release underlying SDK resources."""
        ...
