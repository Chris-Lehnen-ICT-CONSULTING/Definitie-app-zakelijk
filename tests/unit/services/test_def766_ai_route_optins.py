"""DEF-766 correctieronde 1 — opt-ins in de AI-laag voor de ESS-03-route (R3/R6).

Echte `AIServiceV2` en echte `AsyncGPTClient`; alleen de providerclient is een
fake aan de netwerkgrens. Bewezen:

* `use_cache=False` per aanroep omzeilt de ruwe antwoordcache van een gedeelde
  `AIServiceV2(use_cache=True)` — een tweede aanroep gaat opnieuw naar de
  provider (R3);
* `max_attempts=1` beperkt de retrylus van `AsyncGPTClient` tot één poging en
  `max_retries=0` reist door naar de providerclient (R6); zonder opt-in blijft
  het bestaande gedrag (meerdere pogingen) intact;
* `token_estimate="heuristic"` slaat de blokkerende tiktoken-raming over;
* de Anthropic-client zet `max_retries` per aanroep op de SDK via
  `with_options`, zodat de SDK zelf niet meer herhaalt.
"""

from __future__ import annotations

import time
from typing import Any
from unittest.mock import MagicMock

import pytest

from services.ai.base_client import AIClientError, ChatResponse
from services.ai_service_v2 import AIServiceV2
from services.interfaces import AIServiceError
from utils.async_api import RateLimitConfig

pytestmark = [pytest.mark.unit]


class FakeProvider:
    """Providerclient aan de netwerkgrens: telt aanroepen, kan tijdelijk falen."""

    provider_name = "fake"

    def __init__(self, *, faal_eerst: int = 0, antwoord: str = "{}"):
        self.calls: list[dict[str, Any]] = []
        self.faal_eerst = faal_eerst
        self.antwoord = antwoord

    async def chat_completion(
        self, messages, model, temperature=0.7, max_tokens=300, timeout=None, **kw
    ):
        self.calls.append({"model": model, "kw": kw})
        if len(self.calls) <= self.faal_eerst:
            raise AIClientError("synthetische tijdelijke fout")
        return ChatResponse(text=self.antwoord, tokens_used=3, model=model)


def _service(provider: FakeProvider, *, use_cache: bool) -> AIServiceV2:
    class Router:
        def get_model(self, task_type):
            return "fake", "fake-model"

    return AIServiceV2(
        rate_limit_config=RateLimitConfig(max_retries=3, backoff_factor=1.0),
        use_cache=use_cache,
        ai_client=provider,
        model_router=Router(),
    )


async def test_use_cache_false_per_aanroep_omzeilt_de_gedeelde_ruwe_cache():
    provider = FakeProvider(antwoord="niet-json antwoord")
    service = _service(provider, use_cache=True)
    prompt = f"uniek-{time.time_ns()}"
    await service.generate_definition(
        prompt=prompt, task_type="validation", use_cache=False
    )
    await service.generate_definition(
        prompt=prompt, task_type="validation", use_cache=False
    )
    assert len(provider.calls) == 2


async def test_max_attempts_1_geeft_precies_een_providerpoging_bij_tijdelijke_fout(
    monkeypatch,
):
    monkeypatch.setattr("asyncio.sleep", _geen_slaap)
    provider = FakeProvider(faal_eerst=5)
    service = _service(provider, use_cache=False)
    with pytest.raises(AIServiceError):
        await service.generate_definition(
            prompt="p", task_type="validation", max_attempts=1, max_retries=0
        )
    assert len(provider.calls) == 1
    assert provider.calls[0]["kw"].get("max_retries") == 0


async def test_zonder_opt_in_blijft_de_bestaande_retrylus_intact(monkeypatch):
    monkeypatch.setattr("asyncio.sleep", _geen_slaap)
    provider = FakeProvider(faal_eerst=5)
    service = _service(provider, use_cache=False)
    with pytest.raises(AIServiceError):
        await service.generate_definition(prompt="p", task_type="validation")
    assert len(provider.calls) == 3  # RateLimitConfig.max_retries
    assert "max_retries" not in provider.calls[0]["kw"]


async def test_heuristische_tokenraming_slaat_tiktoken_over(monkeypatch):
    provider = FakeProvider(antwoord="x" * 400)
    service = _service(provider, use_cache=False)
    geraakt = {"encoder": 0}

    def _trage_encoder(*_a, **_k):
        geraakt["encoder"] += 1
        time.sleep(0.5)

    monkeypatch.setattr(service, "_get_or_create_encoder", _trage_encoder)
    start = time.perf_counter()
    resultaat = await service.generate_definition(
        prompt="p", task_type="validation", token_estimate="heuristic"
    )
    assert time.perf_counter() - start < 0.4
    assert geraakt["encoder"] == 0
    assert isinstance(resultaat.tokens_used, int) and resultaat.tokens_used > 0
    assert resultaat.metadata.get("tokens_estimated") is True


def test_anthropic_client_zet_max_retries_per_aanroep_op_de_sdk(monkeypatch):
    import asyncio

    from services.ai.anthropic_client import AnthropicClient

    client = AnthropicClient.__new__(AnthropicClient)
    sdk = MagicMock()
    variant = MagicMock()
    sdk.with_options.return_value = variant
    antwoord = MagicMock()
    antwoord.content = [MagicMock(text="ok")]
    antwoord.usage = MagicMock(input_tokens=1, output_tokens=1)

    async def _create(**kwargs):
        return antwoord

    variant.messages.create.side_effect = _create
    sdk.messages.create.side_effect = _create
    client._client = sdk
    client._timeout = 5.0
    # Correctieronde 2 (C): de loopwacht staat uit, zodat de SDK-mock over de
    # twee `asyncio.run()`-loops hieronder dezelfde blijft.
    client._rebind_on_new_loop = False
    router = MagicMock()
    router.accepts_temperature.return_value = False
    client._model_router = router
    from services.ai.base_client import ChatMessage

    asyncio.run(
        client.chat_completion(
            [ChatMessage(role="user", content="hoi")], model="m", max_retries=0
        )
    )
    sdk.with_options.assert_called_once_with(max_retries=0)
    variant.messages.create.assert_called_once()
    # Zonder opt-in: de gewone client, geen with_options.
    sdk.reset_mock()
    variant.reset_mock()
    sdk.messages.create.side_effect = _create
    asyncio.run(
        client.chat_completion([ChatMessage(role="user", content="hoi")], model="m")
    )
    sdk.with_options.assert_not_called()
    sdk.messages.create.assert_called_once()


async def _geen_slaap(*_a, **_k):
    return None
