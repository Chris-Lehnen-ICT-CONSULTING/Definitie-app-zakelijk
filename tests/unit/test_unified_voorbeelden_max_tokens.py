"""max_tokens per voorbeeldtype in de resilient-route.

Praktijk- en tegenvoorbeelden werden afgekapt (stop_reason=max_tokens) bij
max_tokens=1500; gemeten gebruik was 1.830-1.849 tokens. Deze tests leggen de
limiet per type vast, zodat de ruimere limiet niet ongemerkt terugzakt en de
andere typen ongewijzigd blijven.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from voorbeelden.unified_voorbeelden import (
    ExampleRequest,
    ExampleType,
    GenerationMode,
    UnifiedExamplesGenerator,
)

pytestmark = [pytest.mark.unit]

VERWACHTE_MAX_TOKENS = {
    ExampleType.VOORBEELDZINNEN: 1500,
    ExampleType.PRAKTIJKVOORBEELDEN: 3000,
    ExampleType.TEGENVOORBEELDEN: 3000,
    ExampleType.SYNONIEMEN: 1500,
    ExampleType.ANTONIEMEN: 1500,
    ExampleType.TOELICHTING: 1500,
}


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


def test_alle_typen_hebben_een_verwachting():
    assert set(VERWACHTE_MAX_TOKENS) == set(ExampleType)


@pytest.mark.parametrize(
    "example_type",
    [t for t in ExampleType if t != ExampleType.TOELICHTING],
    ids=lambda t: t.name,
)
def test_resilient_common_max_tokens_per_type(generator, example_type):
    asyncio.run(generator._generate_resilient_common(_request(example_type)))

    call_kwargs = generator.ai_service.generate_definition.call_args.kwargs
    assert call_kwargs["max_tokens"] == VERWACHTE_MAX_TOKENS[example_type]


def test_resilient_toelichting_max_tokens(generator):
    # __wrapped__ omzeilt de resilience-decorator (functools.wraps).
    explanation = UnifiedExamplesGenerator._generate_resilient_explanation.__wrapped__
    asyncio.run(explanation(generator, _request(ExampleType.TOELICHTING)))

    call_kwargs = generator.ai_service.generate_definition.call_args.kwargs
    assert call_kwargs["max_tokens"] == VERWACHTE_MAX_TOKENS[ExampleType.TOELICHTING]
