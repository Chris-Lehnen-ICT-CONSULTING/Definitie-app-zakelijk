"""DEF-429 (P2): SmartRateLimiter moet event-loop-recreatie overleven.

Regressietest voor de cross-loop deadlock. Het module-globale
``_integrated_system``-singleton cachet per-endpoint ``SmartRateLimiter``-
instances. Hun ``_process_queues``-achtergrondtaak wordt via ``start()``
gebonden aan de event-loop van de *eerste* call. ``_run_async_safe``
(``unified_voorbeelden.py``) draait elke generatie via een wegwerp-
``asyncio.run()``-loop die daarna sluit. De 2e+ call hergebruikt het singleton
met een **dode** processor-taak → ``acquire()`` zet een future in de queue die
niemand meer verwerkt → timeout op de decorator-timeout.

Vóór de self-healing fix faalt ``test_acquire_survives_loop_recreation``:
de tweede ``asyncio.run`` levert ``False`` (permission geweigerd na timeout).
"""

import asyncio

import pytest

from utils.smart_rate_limiter import RateLimitConfig, RequestPriority, SmartRateLimiter

pytestmark = [pytest.mark.unit]


def _fast_config() -> RateLimitConfig:
    """Ruime capaciteit zodat permission direct verleend kan worden;
    de test meet de cross-loop-binding, niet de rate-limiting zelf."""
    return RateLimitConfig(
        tokens_per_second=100.0,
        bucket_capacity=100,
        target_response_time=1.0,
    )


def test_acquire_survives_loop_recreation():
    """Een in loop-1 gestarte limiter moet in een 2e asyncio.run-loop nog
    steeds NORMAL-priority permission verlenen (self-healing processor)."""
    limiter = SmartRateLimiter(_fast_config())

    async def first() -> bool:
        await limiter.start()
        return await limiter.acquire(RequestPriority.NORMAL, timeout=2.0)

    async def second() -> bool:
        # GEEN start(): simuleert singleton-hergebruik in een verse loop.
        return await limiter.acquire(RequestPriority.NORMAL, timeout=2.0)

    assert asyncio.run(first()) is True, "loop-1 hoort gewoon te slagen"
    # Vóór de fix: de processor-taak hangt aan de gesloten loop-1 →
    # deze acquire krijgt geen token toegewezen → timeout → False.
    assert asyncio.run(second()) is True, (
        "cross-loop regressie: 2e asyncio.run-loop kreeg geen permission "
        "(processor-taak gebonden aan gesloten loop-1)"
    )


def test_acquire_same_loop_reuse_still_works():
    """Borg dat self-healing geen regressie geeft binnen één loop: twee
    sequentiële acquires in dezelfde loop blijven gewoon werken."""
    limiter = SmartRateLimiter(_fast_config())

    async def scenario() -> tuple[bool, bool]:
        await limiter.start()
        first = await limiter.acquire(RequestPriority.NORMAL, timeout=2.0)
        second = await limiter.acquire(RequestPriority.NORMAL, timeout=2.0)
        return first, second

    first, second = asyncio.run(scenario())
    assert first is True
    assert second is True
