"""
Unit tests for the provider-agnostic AI client layer.

Tests cover:
- Factory function (create_ai_client)
- OpenAI and Anthropic client chat_completion
- Error mapping from SDK-specific to provider-agnostic errors
- Immutability of data types
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from unittest.mock import AsyncMock, MagicMock, patch

import anthropic
import openai
import pytest

from services.ai import create_ai_client
from services.ai.anthropic_client import AnthropicClient
from services.ai.base_client import (
    AIConnectionClientError,
    AIRateLimitClientError,
    ChatMessage,
    ChatResponse,
)
from services.ai.openai_client import OpenAIClient

# ---------------------------------------------------------------------------
# Factory tests
# ---------------------------------------------------------------------------


class TestCreateAiClient:
    """Tests for the create_ai_client factory function."""

    def test_create_ai_client_openai(self):
        """create_ai_client('openai', ...) returns OpenAIClient."""
        client = create_ai_client("openai", "sk-test")
        assert isinstance(client, OpenAIClient)
        assert client.provider_name == "openai"

    def test_create_ai_client_anthropic(self):
        """create_ai_client('anthropic', ...) returns AnthropicClient."""
        client = create_ai_client("anthropic", "sk-ant-test")
        assert isinstance(client, AnthropicClient)
        assert client.provider_name == "anthropic"

    def test_create_ai_client_unsupported(self):
        """create_ai_client with unknown provider raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported AI provider"):
            create_ai_client("unknown", "key")


# ---------------------------------------------------------------------------
# OpenAI client tests
# ---------------------------------------------------------------------------


class TestOpenAIClient:
    """Tests for OpenAIClient chat_completion and error mapping."""

    @patch("services.ai.openai_client.AsyncOpenAI")
    async def test_openai_client_chat_completion(self, mock_openai_cls):
        """OpenAIClient.chat_completion returns a proper ChatResponse."""
        # Arrange: mock the SDK response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Test response"))]
        mock_response.usage = MagicMock(total_tokens=42)
        mock_response.model = "gpt-4"

        mock_client_instance = MagicMock()
        mock_client_instance.chat.completions.create = AsyncMock(
            return_value=mock_response
        )
        mock_openai_cls.return_value = mock_client_instance

        client = OpenAIClient(api_key="sk-test")
        messages = [
            ChatMessage(role="user", content="Hello"),
        ]

        # Act
        result = await client.chat_completion(messages=messages, model="gpt-4")

        # Assert
        assert isinstance(result, ChatResponse)
        assert result.text == "Test response"
        assert result.tokens_used == 42
        assert result.model == "gpt-4"
        assert result.metadata == {"provider": "openai"}

    @patch("services.ai.openai_client.AsyncOpenAI")
    async def test_openai_client_maps_rate_limit_error(self, mock_openai_cls):
        """OpenAI RateLimitError is mapped to AIRateLimitClientError."""
        mock_client_instance = MagicMock()
        mock_client_instance.chat.completions.create = AsyncMock(
            side_effect=openai.RateLimitError(
                "rate limited",
                response=MagicMock(status_code=429, headers={}),
                body=None,
            )
        )
        mock_openai_cls.return_value = mock_client_instance

        client = OpenAIClient(api_key="sk-test")
        messages = [ChatMessage(role="user", content="Hello")]

        with pytest.raises(AIRateLimitClientError):
            await client.chat_completion(messages=messages, model="gpt-4")

    @patch("services.ai.openai_client.AsyncOpenAI")
    async def test_openai_client_maps_connection_error(self, mock_openai_cls):
        """OpenAI APIConnectionError is mapped to AIConnectionClientError."""
        mock_client_instance = MagicMock()
        mock_client_instance.chat.completions.create = AsyncMock(
            side_effect=openai.APIConnectionError(request=MagicMock())
        )
        mock_openai_cls.return_value = mock_client_instance

        client = OpenAIClient(api_key="sk-test")
        messages = [ChatMessage(role="user", content="Hello")]

        with pytest.raises(AIConnectionClientError):
            await client.chat_completion(messages=messages, model="gpt-4")


# ---------------------------------------------------------------------------
# Anthropic client tests
# ---------------------------------------------------------------------------


class TestAnthropicClient:
    """Tests for AnthropicClient chat_completion and error mapping."""

    @patch("services.ai.anthropic_client.AsyncAnthropic")
    async def test_anthropic_client_chat_completion(self, mock_anthropic_cls):
        """AnthropicClient.chat_completion returns a proper ChatResponse."""
        # Arrange: mock the SDK response
        mock_block = MagicMock()
        mock_block.text = "Test response"

        mock_response = MagicMock()
        mock_response.content = [mock_block]
        mock_response.usage = MagicMock(input_tokens=10, output_tokens=32)
        mock_response.model = "claude-sonnet-4-5-20250929"

        mock_client_instance = MagicMock()
        mock_client_instance.messages.create = AsyncMock(return_value=mock_response)
        mock_anthropic_cls.return_value = mock_client_instance

        client = AnthropicClient(api_key="sk-ant-test")
        messages = [
            ChatMessage(role="system", content="You are helpful"),
            ChatMessage(role="user", content="Hello"),
        ]

        # Act
        result = await client.chat_completion(
            messages=messages, model="claude-sonnet-4-5-20250929"
        )

        # Assert
        assert isinstance(result, ChatResponse)
        assert result.text == "Test response"
        assert result.tokens_used == 42  # 10 + 32
        assert result.model == "claude-sonnet-4-5-20250929"
        assert result.metadata == {"provider": "anthropic"}

    @patch("services.ai.anthropic_client.AsyncAnthropic")
    async def test_anthropic_client_maps_rate_limit_error(self, mock_anthropic_cls):
        """Anthropic RateLimitError is mapped to AIRateLimitClientError."""
        mock_client_instance = MagicMock()
        mock_client_instance.messages.create = AsyncMock(
            side_effect=anthropic.RateLimitError(
                message="rate limited",
                response=MagicMock(status_code=429, headers={}),
                body=None,
            )
        )
        mock_anthropic_cls.return_value = mock_client_instance

        client = AnthropicClient(api_key="sk-ant-test")
        messages = [ChatMessage(role="user", content="Hello")]

        with pytest.raises(AIRateLimitClientError):
            await client.chat_completion(
                messages=messages, model="claude-sonnet-4-5-20250929"
            )

    @patch("services.ai.anthropic_client.AsyncAnthropic")
    async def test_anthropic_client_maps_connection_error(self, mock_anthropic_cls):
        """Anthropic APIConnectionError is mapped to AIConnectionClientError."""
        mock_client_instance = MagicMock()
        mock_client_instance.messages.create = AsyncMock(
            side_effect=anthropic.APIConnectionError(request=MagicMock())
        )
        mock_anthropic_cls.return_value = mock_client_instance

        client = AnthropicClient(api_key="sk-ant-test")
        messages = [ChatMessage(role="user", content="Hello")]

        with pytest.raises(AIConnectionClientError):
            await client.chat_completion(
                messages=messages, model="claude-sonnet-4-5-20250929"
            )


# ---------------------------------------------------------------------------
# Data type immutability tests
# ---------------------------------------------------------------------------


class TestDataTypeImmutability:
    """Verify that ChatMessage and ChatResponse are frozen (immutable)."""

    def test_chat_message_and_response_are_frozen(self):
        """ChatMessage and ChatResponse reject attribute mutation."""
        msg = ChatMessage(role="user", content="Hello")
        with pytest.raises(FrozenInstanceError):
            msg.content = "Changed"  # type: ignore[misc]

        resp = ChatResponse(text="Answer", tokens_used=10, model="gpt-4")
        with pytest.raises(FrozenInstanceError):
            resp.text = "Changed"  # type: ignore[misc]
