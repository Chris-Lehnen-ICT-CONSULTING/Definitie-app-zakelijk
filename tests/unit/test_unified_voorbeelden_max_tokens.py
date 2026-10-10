"""max_tokens en timeouts per voorbeeldtype in de resilient-route.

Praktijk- en tegenvoorbeelden werden afgekapt (stop_reason=max_tokens) bij
max_tokens=1500; gemeten gebruik was 1.830-1.849 tokens. Een ruimer
tokenbudget helpt alleen als geen enkele timeout eerder afbreekt: de per-type
timeout van de resilience-decorator, de interne timeout van de AI-service
(timeout_seconds, default 30 s) en de requesttimeout van de SDK-client
(request_timeout; None = clientdefault 30 s).

Deze tests lopen via de echte resilient-route (``_generate_resilient`` →
resilience-decorator → AI-service); alleen het resilience-systeem en de
AI-service zijn vervangen, zodat zichtbaar wordt wat er per type aankomt.
"""

import asyncio
import inspect
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.ai_service_v2 import AIServiceV2
from voorbeelden.unified_voorbeelden import (
    ExampleRequest,
    ExampleType,
    GenerationMode,
    UnifiedExamplesGenerator,
)

pytestmark = [pytest.mark.unit]

_AI_DEFAULTS = inspect.signature(AIServiceV2.generate_definition).parameters
AI_DEFAULT_TIMEOUT = _AI_DEFAULTS["timeout_seconds"].default
AI_DEFAULT_REQUEST_TIMEOUT = _AI_DEFAULTS["request_timeout"].default

# type: (max_tokens, decorator-timeout, timeout_seconds, request_timeout)
VERWACHT = {
    ExampleType.VOORBEELDZINNEN: (1500, 20.0, AI_DEFAULT_TIMEOUT, None),
    ExampleType.PRAKTIJKVOORBEELDEN: (3000, 60, 60, 60),
    ExampleType.TEGENVOORBEELDEN: (3000, 60, 60, 60),
    ExampleType.SYNONIEMEN: (1500, 30.0, AI_DEFAULT_TIMEOUT, None),
    ExampleType.ANTONIEMEN: (1500, 30.0, AI_DEFAULT_TIMEOUT, None),
    ExampleType.TOELICHTING: (1500, 30.0, AI_DEFAULT_TIMEOUT, None),
}


class _RegistrerendSysteem:
    """Vervangt het integrated resilience-systeem; noteert de timeout."""

    def __init__(self) -> None:
        self.timeouts: list[float | None] = []

    async def execute_with_full_resilience(
        self, func: Any, *args: Any, timeout: float | None = None, **kwargs: Any
    ) -> Any:
        self.timeouts.append(timeout)
        for sleutel in (
            "endpoint_name",
            "priority",
            "enable_fallback",
            "model",
            "expected_tokens",
        ):
            kwargs.pop(sleutel, None)
        return await func(*args, **kwargs)


@pytest.fixture
def generator():
    with patch(
        "utils.container_manager.get_cached_container",
        side_effect=RuntimeError("no container"),
    ):
        gen = UnifiedExamplesGenerator()
    gen.ai_service = MagicMock()
    gen.ai_service.generate_definition = AsyncMock(
        return_value=MagicMock(text="1. Voorbeeld een\n2. Voorbeeld twee")
    )
    return gen


def _request(example_type: ExampleType) -> ExampleRequest:
    return ExampleRequest(
        begrip="test",
        definitie="test definitie",
        context_dict={"organisatorisch": [], "juridisch": [], "wettelijk": []},
        example_type=example_type,
        generation_mode=GenerationMode.RESILIENT,
        temperature=0.5,
    )


def _via_resilient_route(generator, example_type):
    systeem = _RegistrerendSysteem()

    async def _systeem():
        return systeem

    with patch("utils.integrated_resilience.get_integrated_system", _systeem):
        asyncio.run(generator._generate_resilient(_request(example_type)))

    call_kwargs = generator.ai_service.generate_definition.call_args.kwargs
    return systeem.timeouts, call_kwargs


def test_alle_typen_hebben_een_verwachting():
    assert set(VERWACHT) == set(ExampleType)


@pytest.mark.parametrize("example_type", list(ExampleType), ids=lambda t: t.name)
def test_max_tokens_per_type(generator, example_type):
    _, call_kwargs = _via_resilient_route(generator, example_type)

    assert call_kwargs["max_tokens"] == VERWACHT[example_type][0]


@pytest.mark.parametrize("example_type", list(ExampleType), ids=lambda t: t.name)
def test_decorator_timeout_per_type(generator, example_type):
    timeouts, _ = _via_resilient_route(generator, example_type)

    assert timeouts == [VERWACHT[example_type][1]]


@pytest.mark.parametrize("example_type", list(ExampleType), ids=lambda t: t.name)
def test_ai_service_timeouts_per_type(generator, example_type):
    _, call_kwargs = _via_resilient_route(generator, example_type)

    effectief_timeout = call_kwargs.get("timeout_seconds", AI_DEFAULT_TIMEOUT)
    effectief_request = call_kwargs.get("request_timeout", AI_DEFAULT_REQUEST_TIMEOUT)
    assert effectief_timeout == VERWACHT[example_type][2]
    assert effectief_request == VERWACHT[example_type][3]
