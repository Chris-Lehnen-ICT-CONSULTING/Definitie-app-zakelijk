"""DEF-840: de gedeelde ``AsyncRateLimiter`` moet nieuwe event loops overleven.

``AIServiceV2`` deelt één limiter over alle aanroepen; de UI-bridge draait elke
aanroep in een eigen loop (en thread). Een gedeelde ``asyncio.Lock``/
``Semaphore`` bindt aan de eerste loop waarin hij moet wachten en gaf in de
volgende loop "is bound to a different event loop" — wat ``gather`` in de
voorbeeldgeneratie stil in lege velden veranderde.

Alle tests gebruiken de échte limiter; wachtrijvorming is afgedwongen met een
kleine ``max_concurrent``, omdat een primitief pas bij wachten aan een loop bindt.
"""

from __future__ import annotations

import asyncio
import threading
import time
from datetime import UTC, datetime, timedelta

import pytest

from utils.async_api import AsyncRateLimiter, RateLimitConfig

pytestmark = [pytest.mark.unit]


class _Teller:
    """Telt gelijktijdige houders van de limiter (per loop)."""

    def __init__(self) -> None:
        self.actief = 0
        self.max_actief = 0


async def _aanroep(limiter: AsyncRateLimiter, teller: _Teller) -> str:
    await limiter.acquire()
    try:
        teller.actief += 1
        teller.max_actief = max(teller.max_actief, teller.actief)
        await asyncio.sleep(0.02)
        return "ok"
    finally:
        teller.actief -= 1
        limiter.release()


async def _wachtrij(limiter: AsyncRateLimiter, aantal: int) -> tuple[list, int]:
    teller = _Teller()
    uitkomsten = await asyncio.gather(
        *(_aanroep(limiter, teller) for _ in range(aantal)), return_exceptions=True
    )
    return uitkomsten, teller.max_actief


def test_twee_opeenvolgende_loops_met_wachtrij():
    """Wachtrij in loop 1 bindt de primitieven; loop 2 moet gewoon werken."""
    limiter = AsyncRateLimiter(RateLimitConfig(max_concurrent=1))

    for _ in range(2):
        uitkomsten, max_actief = asyncio.run(_wachtrij(limiter, 4))
        assert uitkomsten == ["ok"] * 4, uitkomsten
        assert max_actief == 1


def test_semaphores_van_gesloten_loops_worden_opgeruimd():
    """Elke UI-generatie is een nieuwe loop; oude mogen niet blijven hangen."""
    limiter = AsyncRateLimiter(RateLimitConfig(max_concurrent=1))
    for _ in range(5):
        asyncio.run(_wachtrij(limiter, 2))

    async def _aantal_tijdens_aanroep() -> int:
        await limiter.acquire()
        try:
            return len(limiter._semaphores)
        finally:
            limiter.release()

    assert asyncio.run(_aantal_tijdens_aanroep()) == 1


def test_verzadigd_verzoekbudget_wacht_en_geldt_procesbreed():
    """Een vol minuutbudget uit loop 1 laat loop 2 wachten tot er plek is."""
    limiter = AsyncRateLimiter(RateLimitConfig(requests_per_minute=2))
    asyncio.run(_wachtrij(limiter, 2))
    assert len(limiter.requests_this_minute) == 2

    # Het budget is vol; de oudste boeking vervalt over ±0,2 s.
    bijna_verlopen = datetime.now(UTC) - timedelta(seconds=59.8)
    limiter.requests_this_minute[0] = bijna_verlopen

    start = time.perf_counter()
    uitkomsten, _ = asyncio.run(_wachtrij(limiter, 1))
    duur = time.perf_counter() - start

    assert uitkomsten == ["ok"]
    assert 0.1 < duur < 2.0, f"wachtte {duur:.2f}s; verwacht ±0,2 s"
    assert len(limiter.requests_this_minute) == 2  # oudste vervallen, nieuwe geboekt


def test_gelijktijdige_loops_in_threads():
    """Zoals parallelle Streamlit-sessies: elk een eigen loop, één limiter."""
    limiter = AsyncRateLimiter(RateLimitConfig(max_concurrent=2))
    threads_aantal, per_loop = 4, 5
    start_samen = threading.Barrier(threads_aantal)
    resultaten: list[tuple[list, int]] = []
    fouten: list[BaseException] = []

    def _sessie() -> None:
        try:
            start_samen.wait(timeout=5)
            resultaten.append(asyncio.run(_wachtrij(limiter, per_loop)))
        except BaseException as fout:  # pragma: no cover - alleen bij regressie
            fouten.append(fout)

    threads = [threading.Thread(target=_sessie) for _ in range(threads_aantal)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)

    assert fouten == []
    assert len(resultaten) == threads_aantal
    for uitkomsten, max_actief in resultaten:
        assert uitkomsten == ["ok"] * per_loop, uitkomsten
        assert max_actief <= 2  # gelijktijdigheid per loop begrensd
    # Het verzoekbudget is procesbreed: elke aanroep is precies één keer geboekt.
    assert len(limiter.requests_this_minute) == threads_aantal * per_loop
