"""Tests voor AnthropicClient role-validatie (DEF-408 post-merge hotfix).

Specifiek: PR #197 refactor verwijderde `# type: ignore[typeddict-item]` door
expliciet onbekende msg.role waarden te raisen als AIClientError. Deze tests
borgen dat nieuwe failure-pad voor regressie.
"""

from __future__ import annotations

import pytest

from services.ai.anthropic_client import AnthropicClient
from services.ai.base_client import AIClientError, ChatMessage

pytestmark = [pytest.mark.unit]


@pytest.mark.asyncio
async def test_chat_completion_raises_on_unknown_role() -> None:
    """Onbekende msg.role waarden moeten AIClientError raisen.

    Voorheen werd zo'n bericht stil doorgegeven aan de Anthropic API (via
    `# type: ignore[typeddict-item]`). PR #197 maakte dit fail-fast.
    Regressie zou silent productiecrash zijn — borgen via test.
    """
    client = AnthropicClient(api_key="dummy", timeout=5.0)

    messages = [
        ChatMessage(role="user", content="hi"),
        ChatMessage(role="tool", content="result"),  # ongeldige role
    ]

    with pytest.raises(AIClientError) as exc_info:
        await client.chat_completion(messages=messages, model="claude-3-haiku-20240307")

    assert "Unsupported message role" in str(exc_info.value)
    assert "tool" in str(exc_info.value)


@pytest.mark.asyncio
async def test_chat_completion_raises_on_empty_messages() -> None:
    """Lege messages-lijst moet AIClientError raisen (bestaande contract)."""
    client = AnthropicClient(api_key="dummy", timeout=5.0)

    with pytest.raises(AIClientError) as exc_info:
        await client.chat_completion(messages=[], model="claude-3-haiku-20240307")

    assert "messages must not be empty" in str(exc_info.value)


@pytest.mark.asyncio
async def test_chat_completion_raises_on_multiple_system_messages() -> None:
    """Meerdere system-messages moeten AIClientError raisen (bestaand contract)."""
    client = AnthropicClient(api_key="dummy", timeout=5.0)

    messages = [
        ChatMessage(role="system", content="you are helpful"),
        ChatMessage(role="system", content="extra system"),
        ChatMessage(role="user", content="hi"),
    ]

    with pytest.raises(AIClientError) as exc_info:
        await client.chat_completion(messages=messages, model="claude-3-haiku-20240307")

    assert "Multiple system messages" in str(exc_info.value)
