"""DEF-493 B: regressietests voor de UI async-bridge `run_async`.

Borgt het contract waar alle UI-call-sites (o.a. `pages/synonym_admin.py`,
DEF-476) op steunen: `run_async` moet een coroutine correct uitvoeren én zijn
resultaat teruggeven, óók wanneer het wordt aangeroepen vanuit een al draaiende
event loop (de Streamlit-situatie). In dat geval mag het NIET de historische
`RuntimeError: asyncio.run() cannot be called from a running event loop`
gooien — het valt terug op de ThreadPoolExecutor-tak.

Dekt beide paden (geen loop → asyncio.run; draaiende loop → thread-pool) voor
happy-path, timeout en exception-propagatie.
"""

from __future__ import annotations

import asyncio

import pytest

from ui.helpers.async_bridge import run_async, run_parallel

pytestmark = [pytest.mark.unit]


# --- Pad 1: geen draaiende loop (asyncio.run-tak) ---------------------------


def test_run_async_no_running_loop_returns_result() -> None:
    """Vanuit sync-context levert run_async gewoon het resultaat."""

    async def _quick() -> str:
        return "ok"

    assert run_async(_quick()) == "ok"


def test_run_async_no_running_loop_timeout_raises() -> None:
    """Een hang faalt met TimeoutError op het asyncio.run-pad."""

    async def _hang() -> None:
        await asyncio.sleep(1.0)

    with pytest.raises(TimeoutError):
        run_async(_hang(), timeout=0.05)


def test_run_async_no_running_loop_exception_propagates() -> None:
    """Een coro-fout propageert ongewijzigd (wordt geen TimeoutError)."""

    async def _boom() -> None:
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        run_async(_boom(), timeout=5)


# --- Pad 2: draaiende loop (thread-pool-tak, de Streamlit-situatie) ---------


@pytest.mark.asyncio
async def test_run_async_within_running_loop_returns_result() -> None:
    """KERNREGRESSIE: run_async vanuit een draaiende loop crasht niet en
    levert het resultaat (geen nested-loop RuntimeError)."""

    async def _quick() -> str:
        return "ok"

    # We draaien in een async test => er is een draaiende loop actief.
    assert asyncio.get_running_loop() is not None
    assert run_async(_quick()) == "ok"


@pytest.mark.asyncio
async def test_run_async_within_running_loop_timeout_raises() -> None:
    """Een hang faalt ook met TimeoutError via de thread-pool-tak."""

    async def _hang() -> None:
        await asyncio.sleep(1.0)

    with pytest.raises(TimeoutError):
        run_async(_hang(), timeout=0.05)


@pytest.mark.asyncio
async def test_run_async_within_running_loop_exception_propagates() -> None:
    """Een coro-fout propageert ook via de thread-pool-tak ongewijzigd."""

    async def _boom() -> None:
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        run_async(_boom(), timeout=5)


# --- run_parallel deelt het run_async-pad -----------------------------------


@pytest.mark.asyncio
async def test_run_parallel_within_running_loop_returns_all_results() -> None:
    """run_parallel (via run_async) werkt ook vanuit een draaiende loop."""

    async def _one() -> int:
        return 1

    async def _two() -> int:
        return 2

    assert run_parallel(_one(), _two()) == (1, 2)
