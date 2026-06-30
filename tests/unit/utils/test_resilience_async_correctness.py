"""DEF-477: async-correctheid in de resilience-laag.

Dekt twee concrete fixes:
1. `get_integrated_system` mag nooit een nog-niet-gestarte instance publiceren
   (race: tussen de None-check en `await start()` werd de instance eerder al
   gepubliceerd, zodat een tweede coroutine een ongestarte instance terugkreeg).
2. `AdaptiveRetryManager.get_retry_delay` degradeert niet langer STIL bij een
   onbekende strategy-waarde — het logt een waarschuwing (root-cause van de
   string-bug die in PR #297 is gefixt).
"""

import asyncio
import logging

import pytest

import utils.integrated_resilience as ir
from utils.enhanced_retry import AdaptiveRetryManager, RetryConfig, RetryStrategy
from utils.integrated_resilience import with_full_resilience
from utils.smart_rate_limiter import RequestPriority

pytestmark = [pytest.mark.unit]


@pytest.mark.asyncio
async def test_record_success_records_real_duration_not_zero(monkeypatch):
    """DEF-462: de duurmetric is de echte poging-duur, niet structureel ~0.

    Vóór de fix was `duration = time.time() - time.time()` → altijd ~0, waardoor
    `record_success` (adaptieve-retry-leren) met een lege metric werd gevoed.
    """
    monkeypatch.setattr(ir, "_integrated_system", None)
    system = ir.IntegratedResilienceSystem()
    await system.start()
    try:
        captured: list[float] = []

        async def fake_record_success(duration: float, endpoint: str = "") -> None:
            captured.append(duration)

        monkeypatch.setattr(system.retry_manager, "record_success", fake_record_success)

        async def work() -> str:
            await asyncio.sleep(0.05)
            return "ok"

        result = await system._execute_with_retry_and_resilience(
            work,
            endpoint_name="def462",
            priority=RequestPriority.NORMAL,
            enable_fallback=False,
        )

        assert result == "ok"
        assert captured, "record_success is niet aangeroepen"
        # Vóór de fix ~0; nu ~de 0.05s sleep van de geslaagde poging.
        assert (
            captured[0] >= 0.04
        ), f"duration te klein (lijkt op de oude bug): {captured[0]}"
    finally:
        await system.stop()
        monkeypatch.setattr(ir, "_integrated_system", None)


@pytest.mark.asyncio
async def test_get_integrated_system_never_returns_unstarted_instance(monkeypatch):
    """Concurrente init-calls krijgen dezelfde, reeds-gestarte instance."""
    monkeypatch.setattr(ir, "_integrated_system", None)

    orig_start = ir.IntegratedResilienceSystem.start

    async def slow_start(self) -> None:
        # Venster waarin een tweede coroutine kan racen vóór start() klaar is.
        await asyncio.sleep(0.05)
        await orig_start(self)

    monkeypatch.setattr(ir.IntegratedResilienceSystem, "start", slow_start)

    # Leg `_started` vast OP het returnmoment van elke caller. Vóór de fix
    # publiceerde de eerste caller de instance vóór start(), waardoor de tweede
    # caller hem ongestart (_started False) terugkreeg — wat alleen zichtbaar is
    # als we op het returnmoment meten, niet ná de gather.
    observed_started: list[bool] = []

    async def call() -> ir.IntegratedResilienceSystem:
        system = await ir.get_integrated_system()
        observed_started.append(system._started)
        return system

    try:
        system_a, system_b = await asyncio.gather(call(), call())
        assert system_a is system_b  # geen dubbele publicatie
        assert all(
            observed_started
        ), f"een caller kreeg een ongestarte instance: {observed_started}"
    finally:
        if ir._integrated_system is not None:
            await ir._integrated_system.stop()
        monkeypatch.setattr(ir, "_integrated_system", None)


@pytest.mark.asyncio
async def test_total_timeout_budget_subtracts_acquire_time(monkeypatch):
    """De acquire-tijd wordt van het totaal-timeout-budget afgetrokken (DEF-477).

    Met een trage acquire (~0.2s) en een totaal-timeout van 0.3s houdt de
    uitvoering nog ~0.1s over. Een functie die 0.2s draait — ruim binnen 0.3s,
    maar buiten het resterende budget — moet daarom alsnog een TimeoutError
    geven. Vóór de fix kreeg de uitvoering opnieuw het volle budget (0.3s) en
    slaagde de call.
    """
    from utils.smart_rate_limiter import SmartRateLimiter

    async def slow_acquire(self, *args, **kwargs) -> bool:
        await asyncio.sleep(0.2)
        return True

    monkeypatch.setattr(SmartRateLimiter, "acquire", slow_acquire)
    monkeypatch.setattr(ir, "_integrated_system", None)

    @with_full_resilience(
        endpoint_name="def477_budget", timeout=0.3, enable_fallback=False
    )
    async def work() -> str:
        await asyncio.sleep(0.2)
        return "klaar"

    try:
        with pytest.raises((asyncio.TimeoutError, TimeoutError)):
            await work()
    finally:
        if ir._integrated_system is not None:
            await ir._integrated_system.stop()
        monkeypatch.setattr(ir, "_integrated_system", None)


@pytest.mark.asyncio
async def test_unknown_retry_strategy_warns_and_falls_back(caplog):
    """Een ongeldige strategy-waarde logt een waarschuwing i.p.v. stil base_delay."""
    config = RetryConfig(
        base_delay=2.0, jitter=False, strategy=RetryStrategy.FIXED_DELAY
    )
    manager = AdaptiveRetryManager(config)
    # Simuleer de oude bug: een niet-enum-waarde in de config.
    manager.config.strategy = "adaptive"  # type: ignore[assignment]

    with caplog.at_level(logging.WARNING):
        delay = await manager.get_retry_delay(ValueError("boom"), attempt=2)

    assert delay == 2.0  # base_delay (geen multiplier, jitter uit)
    assert any("strategy" in r.message.lower() for r in caplog.records)
