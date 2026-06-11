"""
Provider-agnostic AI client package.

Usage:
    from services.ai import create_ai_client

    client = create_ai_client(provider="openai", api_key="sk-...")
    # or
    client = create_ai_client(provider="anthropic", api_key="sk-ant-...")
"""

from __future__ import annotations

from services.ai.base_client import (
    AIAuthenticationClientError,
    AIClientError,
    AIConnectionClientError,
    AIRateLimitClientError,
    AsyncAIClient,
    ChatMessage,
    ChatResponse,
    sanitize_error,
)

_SUPPORTED_PROVIDERS = ("openai", "anthropic")


def create_ai_client(
    provider: str, api_key: str, timeout: float = 30.0
) -> AsyncAIClient:
    """Factory: create the right AI client for *provider*.

    Args:
        provider: ``"openai"`` or ``"anthropic"``.
        api_key: The API key for the chosen provider.
        timeout: Request timeout in seconds (default 30s).

    Returns:
        An ``AsyncAIClient``-conforming instance.

    Raises:
        ValueError: If *provider* is not supported or *api_key* is empty.
    """
    if not api_key:
        msg = f"API key is required for provider {provider!r}"
        raise ValueError(msg)

    if provider == "openai":
        from services.ai.openai_client import OpenAIClient

        return OpenAIClient(api_key=api_key, timeout=timeout)

    if provider == "anthropic":
        from services.ai.anthropic_client import AnthropicClient

        return AnthropicClient(api_key=api_key, timeout=timeout)

    msg = f"Unsupported AI provider: {provider!r}. Choose from {_SUPPORTED_PROVIDERS}"
    raise ValueError(msg)


__all__ = [
    "AIAuthenticationClientError",
    "AIClientError",
    "AIConnectionClientError",
    "AIRateLimitClientError",
    "AsyncAIClient",
    "ChatMessage",
    "ChatResponse",
    "create_ai_client",
    "sanitize_error",
]
