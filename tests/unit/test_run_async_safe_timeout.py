"""DEF-428: _run_async_safe moet een timeout afdwingen i.p.v. oneindig te blokkeren.

Borgt dat een vastlopende generatie-call netjes faalt met TimeoutError op beide
paden (geen draaiende loop -> asyncio.run; draaiende loop -> thread-pool), en dat
een normale snelle coroutine ongewijzigd zijn resultaat teruggeeft.
"""

from __future__ import annotations

import asyncio
from unittest.mock import patch

import pytest

from voorbeelden.unified_voorbeelden import UnifiedExamplesGenerator

pytestmark = [pytest.mark.unit]


@pytest.fixture
def generator() -> UnifiedExamplesGenerator:
    with patch(
        "utils.container_manager.get_cached_container",
        side_effect=RuntimeError("no container"),
    ):
        return UnifiedExamplesGenerator()


def test_timeout_raises_on_hang_no_running_loop(
    generator: UnifiedExamplesGenerator,
) -> None:
    """Zonder draaiende loop (asyncio.run-pad) faalt een hang met TimeoutError."""

    async def _hang() -> None:
        await asyncio.sleep(10)

    with pytest.raises(TimeoutError):
        generator._run_async_safe(_hang(), timeout=0.05)


def test_returns_result_within_timeout(generator: UnifiedExamplesGenerator) -> None:
    """Een snelle coroutine levert gewoon zijn resultaat (gedrag ongewijzigd)."""

    async def _quick() -> str:
        return "ok"

    assert generator._run_async_safe(_quick(), timeout=5) == "ok"


@pytest.mark.asyncio
async def test_timeout_raises_on_hang_in_running_loop(
    generator: UnifiedExamplesGenerator,
) -> None:
    """In een draaiende loop (thread-pool-pad) faalt een hang ook met TimeoutError."""

    async def _hang() -> None:
        await asyncio.sleep(10)

    with pytest.raises(TimeoutError):
        generator._run_async_safe(_hang(), timeout=0.05)
