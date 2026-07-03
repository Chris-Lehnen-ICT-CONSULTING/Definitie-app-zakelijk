"""Regressietests DEF-441: temperature-guard per modelfamilie.

Sampling-params (`temperature`/`top_p`/`top_k`) zijn verwijderd op
Opus 4.7+, Sonnet 5 en Fable/Mythos 5 — meesturen geeft een 400
("`temperature` is deprecated for this model"). Op Opus 4.6 en ouder,
Sonnet 4.x en Haiku 3/4.x is de parameter nog geldig.

De guard is een allowlist: alleen families die temperature aantoonbaar
accepteren krijgen hem mee; elk ander (nieuw) model → `anthropic.omit`.
Weglaten is altijd geldig, meesturen kan breken — fail-safe dus.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import anthropic
import pytest

from services.ai.base_client import ChatMessage

pytestmark = [pytest.mark.unit]


async def _capture_create_kwargs(model: str, temperature: float = 0.3) -> dict:
    """Roep chat_completion aan met gemockte SDK en geef de create-kwargs terug."""
    from services.ai.anthropic_client import AnthropicClient

    client = AnthropicClient(api_key="dummy", timeout=5.0)
    fake_response = SimpleNamespace(
        content=[],
        usage=SimpleNamespace(input_tokens=1, output_tokens=1),
        model=model,
    )
    fake_messages = SimpleNamespace(create=AsyncMock(return_value=fake_response))
    client._client = SimpleNamespace(messages=fake_messages)  # type: ignore[assignment]

    await client.chat_completion(
        messages=[ChatMessage(role="user", content="hi")],
        model=model,
        temperature=temperature,
    )
    return dict(fake_messages.create.call_args.kwargs)


class TestTemperatureOmittedOnModernModels:
    """Opus 4.7+/Sonnet 5/Fable 5 en onbekende nieuwe modellen: geen temperature."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "model",
        [
            "claude-opus-4-8",
            "claude-opus-4-7",
            "claude-sonnet-5",
            "claude-fable-5",
            "claude-mythos-5",
            "claude-opus-5",  # hypothetisch toekomstig model → fail-safe weglaten
        ],
    )
    async def test_temperature_is_omitted(self, model: str) -> None:
        kwargs = await _capture_create_kwargs(model)
        sent = kwargs.get("temperature", anthropic.omit)
        assert isinstance(sent, anthropic.Omit), (
            f"temperature werd meegestuurd naar {model} — dat geeft een 400 "
            "('temperature is deprecated for this model', DEF-441)"
        )


class TestTemperatureSentOnLegacyModels:
    """Opus 4.6 en ouder, Sonnet 4.x, Haiku 3/4.x: temperature ongewijzigd meesturen."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "model",
        [
            "claude-opus-4-6",
            "claude-opus-4-5-20251101",
            "claude-opus-4-1",
            "claude-sonnet-4-6",
            "claude-sonnet-4-5-20250929",
            "claude-haiku-4-5-20251001",
            "claude-3-haiku-20240307",
        ],
    )
    async def test_temperature_is_sent_unchanged(self, model: str) -> None:
        kwargs = await _capture_create_kwargs(model, temperature=0.42)
        assert kwargs.get("temperature") == 0.42, (
            f"temperature ontbreekt voor {model} — gedrag voor oudere modellen "
            "moet ongewijzigd blijven (acceptatiecriterium DEF-441)"
        )
