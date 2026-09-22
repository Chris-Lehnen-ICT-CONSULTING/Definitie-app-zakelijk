"""DEF-766 (correctieronde 3, F1): `stop_reason` zichtbaar op de Anthropic-grens.

De API meldt een afgekapt antwoord met `stop_reason: "max_tokens"`. De client
las dat veld niet, waardoor afkapping stroomopwaarts niet te onderscheiden was
van een werkelijk misvormd antwoord. `ChatResponse` krijgt een additief veld
`stop_reason`; de Anthropic-client vult het en logt een waarschuwing bij
`max_tokens` — zonder sleutel of promptinhoud.
"""

from __future__ import annotations

import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from services.ai.base_client import ChatMessage, ChatResponse

pytestmark = [pytest.mark.unit]

PROMPT = "geheime-promptinhoud-die-niet-in-het-log-mag"
SLEUTEL = "sk-ant-geheim-1234567890abcdef"


async def _completion(response) -> ChatResponse:
    from services.ai.anthropic_client import AnthropicClient

    client = AnthropicClient(api_key=SLEUTEL, timeout=5.0)
    fake_messages = SimpleNamespace(create=AsyncMock(return_value=response))
    client._client = SimpleNamespace(messages=fake_messages)  # type: ignore[assignment]
    return await client.chat_completion(
        messages=[ChatMessage(role="user", content=PROMPT)],
        model="claude-opus-5",
        max_tokens=1200,
    )


def _response(stop_reason, text: str = '{"a": 1'):
    return SimpleNamespace(
        content=[SimpleNamespace(text=text)],
        usage=SimpleNamespace(input_tokens=10, output_tokens=1200),
        model="claude-opus-5",
        stop_reason=stop_reason,
    )


def test_chat_response_blijft_construeerbaar_zonder_stop_reason() -> None:
    """Additief: bestaande constructies (fakes, OpenAI-client) blijven werken."""
    antwoord = ChatResponse(text="ok", tokens_used=1, model="m")
    assert antwoord.stop_reason is None


@pytest.mark.asyncio
async def test_max_tokens_wordt_doorgegeven_en_gewaarschuwd(caplog) -> None:
    with caplog.at_level(logging.WARNING, logger="services.ai.anthropic_client"):
        antwoord = await _completion(_response("max_tokens"))
    assert antwoord.stop_reason == "max_tokens"
    assert antwoord.text == '{"a": 1'
    waarschuwingen = [
        r
        for r in caplog.records
        if r.levelno >= logging.WARNING and "max_tokens" in r.getMessage()
    ]
    assert (
        waarschuwingen
    ), "afkapping (stop_reason=max_tokens) hoort een waarschuwing te loggen"
    for record in waarschuwingen:
        bericht = record.getMessage()
        assert PROMPT not in bericht, "promptinhoud mag niet in het log"
        assert SLEUTEL not in bericht, "API-sleutel mag niet in het log"


@pytest.mark.asyncio
async def test_end_turn_wordt_doorgegeven_zonder_waarschuwing(caplog) -> None:
    with caplog.at_level(logging.WARNING, logger="services.ai.anthropic_client"):
        antwoord = await _completion(_response("end_turn", text='{"a": 1}'))
    assert antwoord.stop_reason == "end_turn"
    assert not [
        r
        for r in caplog.records
        if r.levelno >= logging.WARNING and "max_tokens" in r.getMessage()
    ]


@pytest.mark.asyncio
async def test_ontbrekend_stop_reason_is_none() -> None:
    """Fakes zonder het veld (bestaande tests) leveren None, geen fout."""
    antwoord = await _completion(
        SimpleNamespace(
            content=[],
            usage=SimpleNamespace(input_tokens=1, output_tokens=1),
            model="claude-opus-5",
        )
    )
    assert antwoord.stop_reason is None


@pytest.mark.asyncio
async def test_niet_string_stop_reason_wordt_none() -> None:
    """Een mock-attribuut of ander type wordt niet als reden doorgegeven."""
    antwoord = await _completion(_response(object()))
    assert antwoord.stop_reason is None
