"""Unit tests voor AIServiceV2.batch_generate exception-afhandeling (DEF-439).

Borgt de gedragswijziging waarbij `batch_generate` de resultaten van
`asyncio.gather(return_exceptions=True)` op `BaseException` controleert
(i.p.v. alleen `Exception`). Een `BaseException` die geen `Exception` is —
zoals `asyncio.CancelledError` — moet als `AIServiceError` ge-reraised worden
en niet stil als "resultaat" doorglippen.
"""

from unittest.mock import MagicMock

import pytest

from services.ai_service_v2 import AIServiceV2
from services.interfaces import AIBatchRequest, AIGenerationResult, AIServiceError

pytestmark = [pytest.mark.unit]


@pytest.fixture
def ai_service():
    """AIServiceV2 met expliciet default_model en een dummy client.

    `generate_definition` wordt per test vervangen, dus de client/cache/
    rate-limiter worden niet daadwerkelijk aangeroepen.
    """
    return AIServiceV2(default_model="gpt-5.2", ai_client=MagicMock())


def _ok_result(prompt: str) -> AIGenerationResult:
    return AIGenerationResult(
        text=f"definitie voor {prompt}",
        model="gpt-5.2",
        tokens_used=10,
        generation_time=0.1,
    )


@pytest.mark.asyncio
async def test_batch_generate_reraises_baseexception_as_aiserviceerror(ai_service):
    """Een BaseException (niet-Exception) uit gather wordt AIServiceError.

    Vóór DEF-439 controleerde de loop op `isinstance(result, Exception)`,
    waardoor een `BaseException` (bv. CancelledError) als resultaat in de
    lijst belandde i.p.v. ge-reraised te worden.
    """

    class _NonExceptionBaseError(BaseException):
        """BaseException die GEEN Exception is — net als asyncio.CancelledError."""

    async def fake_generate(*, prompt: str, **_kwargs):
        if prompt == "boom":
            raise _NonExceptionBaseError("gesimuleerde cancellation")
        return _ok_result(prompt)

    ai_service.generate_definition = fake_generate

    requests = [AIBatchRequest(prompt="ok"), AIBatchRequest(prompt="boom")]

    with pytest.raises(AIServiceError) as exc_info:
        await ai_service.batch_generate(requests)

    # De batch-index (1) van de falende request hoort in de foutmelding te staan.
    assert "1" in str(exc_info.value)


@pytest.mark.asyncio
async def test_batch_generate_reraises_regular_exception_as_aiserviceerror(ai_service):
    """Een gewone Exception uit gather wordt eveneens AIServiceError (regressie)."""

    async def fake_generate(*, prompt: str, **_kwargs):
        if prompt == "boom":
            raise ValueError("kapot")
        return _ok_result(prompt)

    ai_service.generate_definition = fake_generate

    requests = [AIBatchRequest(prompt="boom"), AIBatchRequest(prompt="ok")]

    with pytest.raises(AIServiceError) as exc_info:
        await ai_service.batch_generate(requests)

    assert "0" in str(exc_info.value)


@pytest.mark.asyncio
async def test_batch_generate_happy_path_returns_results_in_order(ai_service):
    """Zonder fouten komen resultaten in dezelfde volgorde als de requests terug."""

    async def fake_generate(*, prompt: str, **_kwargs):
        return _ok_result(prompt)

    ai_service.generate_definition = fake_generate

    requests = [AIBatchRequest(prompt="a"), AIBatchRequest(prompt="b")]
    results = await ai_service.batch_generate(requests)

    assert [r.text for r in results] == ["definitie voor a", "definitie voor b"]


@pytest.mark.asyncio
async def test_batch_generate_empty_returns_empty(ai_service):
    """Lege request-lijst geeft een lege lijst zonder client-aanroep."""
    assert await ai_service.batch_generate([]) == []
