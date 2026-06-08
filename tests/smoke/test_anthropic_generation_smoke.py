"""Generatie-smoke voor de Anthropic SDK-upgrade (DEF-412: 0.49 → 0.105.2).

Oefent het volledige generatie-pad uit tegen de geïnstalleerde Anthropic SDK:

    AIServiceV2.generate_definition()
        → AsyncGPTClient._make_request_with_retries()
            → AnthropicClient.chat_completion()
                → AsyncAnthropic.messages.create()   (gemockt)

Alleen de buitenste netwerk-call (`messages.create`) is gemockt; de
`AnthropicClient` gebruikt het échte `anthropic.omit`-sentinel,
`anthropic.types.MessageParam` en bouwt zijn `ChatResponse` uit een échte
`anthropic.types.Message` (geen losse MagicMock). Zo bewijst de smoke dat onze
response-extractie (`block.text`, `usage.input_tokens/output_tokens`,
`response.model`) klopt tegen de pydantic-modellen van de nieuwe SDK-versie.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import anthropic
import pytest
from anthropic.types import Message, TextBlock, Usage

from services.ai.anthropic_client import AnthropicClient
from services.ai.base_client import AIClientError
from services.ai.model_router import ModelRouter
from services.ai_service_v2 import AIServiceV2
from services.interfaces import AIServiceError
from utils.async_api import RateLimitConfig

pytestmark = [pytest.mark.smoke]


@pytest.fixture(autouse=True)
def _force_heuristic_token_estimate():
    """Forceer de heuristische token-schatting i.p.v. tiktoken.

    Voor een claude-model valt `_estimate_tokens` terug op
    `tiktoken.get_encoding("o200k_base")`, wat de BPE-vocab probeert te
    downloaden. De suite blokkeert netwerk (conftest `_disable_network`), dus op
    een koude cache (verse CI-runner) zou dat falen. Deze smoke test het
    SDK-pad, niet de token-telling — de heuristiek (char×0.75) is hermetisch.
    """
    with patch("services.ai_service_v2.TIKTOKEN_AVAILABLE", False):
        yield


_REPRESENTATIVE_TEXT = (
    "Een verdachte is een natuurlijke persoon tegen wie een redelijk vermoeden "
    "van schuld aan een strafbaar feit bestaat."
)
_ANTHROPIC_MODEL = "claude-opus-4-5-20251101"


def _representative_message() -> Message:
    """Bouw een echte 0.105.x Message zoals messages.create() die teruggeeft."""
    return Message(
        id="msg_smoke_def412",
        content=[TextBlock(type="text", text=_REPRESENTATIVE_TEXT)],
        model=_ANTHROPIC_MODEL,
        role="assistant",
        stop_reason="end_turn",
        stop_sequence=None,
        type="message",
        usage=Usage(input_tokens=42, output_tokens=58),
    )


def _anthropic_router() -> ModelRouter:
    """ModelRouter geforceerd op de Anthropic-provider voor deze smoke."""
    return ModelRouter(
        {
            "active_provider": "anthropic",
            "task_tiers": {"critical": ["definition_core"], "standard": []},
            "providers": {
                "anthropic": {
                    "critical": _ANTHROPIC_MODEL,
                    "standard": "claude-haiku-4-5-20251001",
                },
            },
        }
    )


@pytest.mark.asyncio
async def test_generate_definition_end_to_end_via_anthropic() -> None:
    """generate_definition() levert end-to-end een correcte AIGenerationResult op."""
    with (
        patch("services.ai.anthropic_client.AsyncAnthropic") as mock_sdk_cls,
        patch.object(
            ModelRouter,
            "active_provider",
            new_callable=PropertyMock,
            return_value="anthropic",
        ),
    ):
        mock_sdk = MagicMock()
        mock_sdk.messages.create = AsyncMock(return_value=_representative_message())
        mock_sdk_cls.return_value = mock_sdk

        anthropic_client = AnthropicClient(api_key="sk-ant-smoke")
        service = AIServiceV2(
            rate_limit_config=RateLimitConfig(max_retries=1),
            ai_client=anthropic_client,
            model_router=_anthropic_router(),
            use_cache=False,
        )

        result = await service.generate_definition(
            prompt="Definieer het begrip 'verdachte' binnen het Nederlandse strafrecht.",
            system_prompt="Je bent een juridisch definitie-expert.",
            task_type="definition_core",
            temperature=0.2,
            max_tokens=200,
        )

    # End-to-end resultaat klopt
    assert result.text == _REPRESENTATIVE_TEXT
    assert result.model == _ANTHROPIC_MODEL
    assert result.cached is False
    assert result.tokens_used > 0  # token-estimatie liep zonder fout

    # De SDK is daadwerkelijk via het volledige pad aangeroepen met onze params
    mock_sdk.messages.create.assert_awaited_once()
    call_kwargs = mock_sdk.messages.create.await_args.kwargs
    assert call_kwargs["model"] == _ANTHROPIC_MODEL
    assert call_kwargs["max_tokens"] == 200
    assert call_kwargs["system"] == "Je bent een juridisch definitie-expert."
    assert call_kwargs["messages"] == [
        {
            "role": "user",
            "content": "Definieer het begrip 'verdachte' binnen het Nederlandse strafrecht.",
        }
    ]


@pytest.mark.asyncio
async def test_multiple_content_blocks_are_joined() -> None:
    """Een Message met meerdere TextBlocks levert de samengevoegde tekst op.

    Borgt de extractie `"\\n".join(text_parts)` in AnthropicClient tegen de
    pydantic-modellen van de nieuwe SDK — de meest relevante response-edge bij
    een model-bump.
    """
    multi_block = Message(
        id="msg_smoke_multiblock",
        content=[
            TextBlock(type="text", text="Eerste deel van de definitie."),
            TextBlock(type="text", text="Tweede deel van de definitie."),
        ],
        model=_ANTHROPIC_MODEL,
        role="assistant",
        stop_reason="end_turn",
        stop_sequence=None,
        type="message",
        usage=Usage(input_tokens=10, output_tokens=20),
    )

    with (
        patch("services.ai.anthropic_client.AsyncAnthropic") as mock_sdk_cls,
        patch.object(
            ModelRouter,
            "active_provider",
            new_callable=PropertyMock,
            return_value="anthropic",
        ),
    ):
        mock_sdk = MagicMock()
        mock_sdk.messages.create = AsyncMock(return_value=multi_block)
        mock_sdk_cls.return_value = mock_sdk

        service = AIServiceV2(
            rate_limit_config=RateLimitConfig(max_retries=1),
            ai_client=AnthropicClient(api_key="sk-ant-smoke"),
            model_router=_anthropic_router(),
            use_cache=False,
        )

        result = await service.generate_definition(
            prompt="Definieer 'verdachte'.",
            task_type="definition_core",
        )

    assert result.text == (
        "Eerste deel van de definitie.\nTweede deel van de definitie."
    )


@pytest.mark.asyncio
async def test_generate_definition_error_maps_to_service_error() -> None:
    """Een Anthropic APIError propageert als AIServiceError door het hele pad."""
    with (
        patch("services.ai.anthropic_client.AsyncAnthropic") as mock_sdk_cls,
        patch.object(
            ModelRouter,
            "active_provider",
            new_callable=PropertyMock,
            return_value="anthropic",
        ),
    ):
        mock_sdk = MagicMock()
        mock_sdk.messages.create = AsyncMock(
            side_effect=anthropic.APIError(
                message="boom",
                request=MagicMock(),
                body=None,
            )
        )
        mock_sdk_cls.return_value = mock_sdk

        service = AIServiceV2(
            rate_limit_config=RateLimitConfig(max_retries=1),
            ai_client=AnthropicClient(api_key="sk-ant-smoke"),
            model_router=_anthropic_router(),
            use_cache=False,
        )

        with pytest.raises(AIServiceError) as exc_info:
            await service.generate_definition(
                prompt="Definieer 'verdachte'.",
                task_type="definition_core",
            )

    # De mapping behoudt de oorzaakketen: AIServiceError ← AIClientError ← APIError
    assert isinstance(exc_info.value.__cause__, AIClientError)
