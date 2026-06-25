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

pytestmark = [pytest.mark.unit]


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

    system_a, system_b = await asyncio.gather(
        ir.get_integrated_system(),
        ir.get_integrated_system(),
    )

    try:
        assert system_a is system_b  # geen dubbele creatie
        # Vóór de fix kon de tweede call een instance terugkrijgen waarvan
        # start() nog liep (_started False).
        assert system_a._started is True
    finally:
        await system_a.stop()
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
