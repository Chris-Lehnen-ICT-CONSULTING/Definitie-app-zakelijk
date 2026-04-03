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
    AIClientError,
    AIConnectionClientError,
    AIRateLimitClientError,
    ChatMessage,
    ChatResponse,
    sanitize_error,
)
from services.ai.openai_client import OpenAIClient

pytestmark = [pytest.mark.unit]

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


# ---------------------------------------------------------------------------
# Input validation tests
# ---------------------------------------------------------------------------


class TestInputValidation:
    """Tests for input validation in clients."""

    @patch("services.ai.openai_client.AsyncOpenAI")
    async def test_openai_rejects_empty_messages(self, mock_openai_cls):
        """OpenAIClient raises AIClientError on empty messages list."""
        client = OpenAIClient(api_key="sk-test")
        with pytest.raises(AIClientError, match="messages must not be empty"):
            await client.chat_completion(messages=[], model="gpt-4")

    @patch("services.ai.anthropic_client.AsyncAnthropic")
    async def test_anthropic_rejects_empty_messages(self, mock_anthropic_cls):
        """AnthropicClient raises AIClientError on empty messages list."""
        client = AnthropicClient(api_key="sk-ant-test")
        with pytest.raises(AIClientError, match="messages must not be empty"):
            await client.chat_completion(
                messages=[], model="claude-sonnet-4-5-20250929"
            )

    def test_factory_rejects_empty_api_key(self):
        """create_ai_client raises ValueError on empty API key."""
        with pytest.raises(ValueError, match="API key is required"):
            create_ai_client("openai", "")

    def test_factory_rejects_none_api_key(self):
        """create_ai_client raises ValueError on None API key."""
        with pytest.raises(ValueError, match="API key is required"):
            create_ai_client("anthropic", None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Anthropic system message validation tests
# ---------------------------------------------------------------------------


class TestAnthropicSystemMessages:
    """Tests for Anthropic multiple system message rejection."""

    @patch("services.ai.anthropic_client.AsyncAnthropic")
    async def test_anthropic_rejects_multiple_system_messages(self, mock_cls):
        """AnthropicClient raises AIClientError on multiple system messages."""
        client = AnthropicClient(api_key="sk-ant-test")
        messages = [
            ChatMessage(role="system", content="First system"),
            ChatMessage(role="system", content="Second system"),
            ChatMessage(role="user", content="Hello"),
        ]
        with pytest.raises(AIClientError, match="Multiple system messages"):
            await client.chat_completion(
                messages=messages, model="claude-sonnet-4-5-20250929"
            )

    @patch("services.ai.anthropic_client.AsyncAnthropic")
    async def test_anthropic_accepts_single_system_message(self, mock_cls):
        """AnthropicClient works fine with exactly one system message."""
        mock_block = MagicMock()
        mock_block.text = "Response"
        mock_response = MagicMock()
        mock_response.content = [mock_block]
        mock_response.usage = MagicMock(input_tokens=5, output_tokens=10)
        mock_response.model = "claude-sonnet-4-5-20250929"

        mock_instance = MagicMock()
        mock_instance.messages.create = AsyncMock(return_value=mock_response)
        mock_cls.return_value = mock_instance

        client = AnthropicClient(api_key="sk-ant-test")
        messages = [
            ChatMessage(role="system", content="You are helpful"),
            ChatMessage(role="user", content="Hello"),
        ]
        result = await client.chat_completion(
            messages=messages, model="claude-sonnet-4-5-20250929"
        )
        assert result.text == "Response"


# ---------------------------------------------------------------------------
# None content in API response tests
# ---------------------------------------------------------------------------


class TestNoneContentHandling:
    """Tests for None/missing content in API responses."""

    @patch("services.ai.openai_client.AsyncOpenAI")
    async def test_openai_handles_none_content(self, mock_openai_cls):
        """OpenAIClient returns empty string when content is None."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content=None))]
        mock_response.usage = MagicMock(total_tokens=5)
        mock_response.model = "gpt-4"

        mock_instance = MagicMock()
        mock_instance.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai_cls.return_value = mock_instance

        client = OpenAIClient(api_key="sk-test")
        messages = [ChatMessage(role="user", content="Hello")]
        result = await client.chat_completion(messages=messages, model="gpt-4")
        assert result.text == ""

    @patch("services.ai.anthropic_client.AsyncAnthropic")
    async def test_anthropic_handles_empty_content_blocks(self, mock_cls):
        """AnthropicClient returns empty string when no text blocks."""
        mock_response = MagicMock()
        mock_response.content = []  # No content blocks
        mock_response.usage = MagicMock(input_tokens=5, output_tokens=0)
        mock_response.model = "claude-sonnet-4-5-20250929"

        mock_instance = MagicMock()
        mock_instance.messages.create = AsyncMock(return_value=mock_response)
        mock_cls.return_value = mock_instance

        client = AnthropicClient(api_key="sk-ant-test")
        messages = [ChatMessage(role="user", content="Hello")]
        result = await client.chat_completion(
            messages=messages, model="claude-sonnet-4-5-20250929"
        )
        assert result.text == ""


# ---------------------------------------------------------------------------
# close() method tests
# ---------------------------------------------------------------------------


class TestCloseMethod:
    """Tests for client close() cleanup."""

    @patch("services.ai.openai_client.AsyncOpenAI")
    async def test_openai_close_delegates_to_sdk(self, mock_openai_cls):
        """OpenAIClient.close() calls underlying SDK close()."""
        mock_instance = MagicMock()
        mock_instance.close = AsyncMock()
        mock_openai_cls.return_value = mock_instance

        client = OpenAIClient(api_key="sk-test")
        await client.close()
        mock_instance.close.assert_awaited_once()

    @patch("services.ai.anthropic_client.AsyncAnthropic")
    async def test_anthropic_close_delegates_to_sdk(self, mock_cls):
        """AnthropicClient.close() calls underlying SDK close()."""
        mock_instance = MagicMock()
        mock_instance.close = AsyncMock()
        mock_cls.return_value = mock_instance

        client = AnthropicClient(api_key="sk-ant-test")
        await client.close()
        mock_instance.close.assert_awaited_once()


# ---------------------------------------------------------------------------
# API key sanitization tests
# ---------------------------------------------------------------------------


class TestSanitizeError:
    """Tests for API key redaction in error messages."""

    def test_sanitize_openai_key(self):
        """OpenAI-style API key is redacted."""
        msg = "Auth error with key sk-proj-abc123def456xyz789"
        assert "sk-proj" not in sanitize_error(msg)
        assert "[REDACTED]" in sanitize_error(msg)

    def test_sanitize_anthropic_key(self):
        """Anthropic-style API key is redacted."""
        msg = "Invalid key: sk-ant-api03-longstringhere1234567890"
        assert "sk-ant" not in sanitize_error(msg)
        assert "[REDACTED]" in sanitize_error(msg)

    def test_sanitize_preserves_safe_text(self):
        """Messages without API keys are unchanged."""
        msg = "Connection timed out after 30s"
        assert sanitize_error(msg) == msg

    @patch("services.ai.openai_client.AsyncOpenAI")
    async def test_openai_error_does_not_leak_key(self, mock_openai_cls):
        """Error messages from OpenAI are sanitized before raising."""
        mock_instance = MagicMock()
        mock_instance.chat.completions.create = AsyncMock(
            side_effect=openai.OpenAIError(
                "Invalid API Key: sk-proj-abc123def456xyz789"
            )
        )
        mock_openai_cls.return_value = mock_instance

        client = OpenAIClient(api_key="sk-test")
        messages = [ChatMessage(role="user", content="Hello")]

        with pytest.raises(AIClientError) as exc_info:
            await client.chat_completion(messages=messages, model="gpt-4")
        assert "sk-proj" not in str(exc_info.value)
        assert "[REDACTED]" in str(exc_info.value)
