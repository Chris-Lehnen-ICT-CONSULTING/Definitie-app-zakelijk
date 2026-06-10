"""DEF-428: de @with_full_resilience-timeout moet de UITVOERING begrenzen.

Regressietest voor de hang: vóór de fix wordt de decorator-`timeout` alleen
gebruikt voor rate-limit-acquire, niet voor de eigenlijke `await func(...)`.
Een hangende provider-call blokkeert daardoor oneindig (32 min gemeten).
"""

import asyncio

import pytest

from utils.integrated_resilience import with_full_resilience

pytestmark = [pytest.mark.unit]


@pytest.mark.asyncio
async def test_with_full_resilience_bounds_execution_time():
    """Een trage call moet binnen ~timeout afbreken met een TimeoutError."""

    @with_full_resilience(
        endpoint_name="def428_hang_guard", timeout=0.5, enable_fallback=False
    )
    async def hangs() -> str:
        # Simuleert een niet-antwoordende provider-call (geen client-timeout).
        await asyncio.sleep(6)
        return "zou nooit teruggegeven mogen worden"

    loop = asyncio.get_event_loop()
    start = loop.time()
    with pytest.raises((asyncio.TimeoutError, TimeoutError)):
        await hangs()
    elapsed = loop.time() - start
    assert elapsed < 3.0, (
        f"decorator-timeout begrenst de uitvoering niet: {elapsed:.1f}s "
        f"(verwacht afbreken rond 0.5s, niet ~6s)"
    )
