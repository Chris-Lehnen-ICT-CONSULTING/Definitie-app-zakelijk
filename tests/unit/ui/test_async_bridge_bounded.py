"""DEF-519: run_async moet begrensd terugkeren binnen het gevraagde budget.

Gemeten regressie: bij een gevraagde timeout van 0.01s keerde de bridge pas na
circa 0.30s terug, omdat de executor-context bij het verlaten alsnog op de
worker wachtte.

Geborgd: begrensde terugkeer in zowel sync- als actieve-loop-context (ook bij
een niet-coeperatieve en bij een annulering-negerende worker), echte
cancellation voor coeperatieve taken, exception-identiteit, timeout=None en
timeout=0.

Onvermijdelijke beperking: Python kan een thread die zonder await-punt blokkeert
niet geforceerd stoppen. De tests bewijzen dat de caller op tijd vrijkomt en dat
de worker daarna via zijn eigen release-event eindigt -- niet dat een
cancellation hem heeft afgebroken.

Elke testworker heeft een eigen eindige deadline, zodat ook een RED-run het
testproces niet kan ophangen.
"""

from __future__ import annotations

import asyncio
import gc
import threading
import time
import warnings
from collections.abc import Coroutine
from typing import Any

import pytest

from ui.helpers.async_bridge import run_async, run_async_safe, run_parallel

pytestmark = [pytest.mark.unit]


# Gevraagd budget in de tests.
REQUESTED_TIMEOUT_S = 0.05

# Contractuele afwikkelmarge van de bridge.
CLEANUP_MARGIN_S = 0.25

# Strakke grens: budget + marge + kleine schedulingsspeling. Een schaduwtimeout
# van bijvoorbeeld 0.9s komt hier niet doorheen.
TIGHT_BUDGET_S = REQUESTED_TIMEOUT_S + CLEANUP_MARGIN_S + 0.20

# Ruime, deterministische buitengrens voor tests die niet de marge zelf meten.
# Blijft ver onder SLOW_WORK_S, dus wachten-op-de-worker valt er altijd door.
OUTER_DEADLINE_S = REQUESTED_TIMEOUT_S + 1.0

# Duur van traag werk; nooit oneindig.
SLOW_WORK_S = 2.5

# Harde eigen deadline van een blokkerende testworker.
BLOCK_LIMIT_S = 2.5

# Maximale wachttijd op een eigen event voordat een test faalt.
EVENT_WAIT_S = 1.5

_DEFAULT_SENTINEL = object()


async def _slow() -> str:
    """Coeperatief traag werk: yield naar de loop, dus annuleerbaar."""
    await asyncio.sleep(SLOW_WORK_S)
    return "te laat"


def _cooperative_worker() -> tuple[Coroutine[Any, Any, None], threading.Event]:
    """Traag werk dat zijn CancelledError registreert."""
    cancelled = threading.Event()

    async def _work() -> None:
        try:
            await asyncio.sleep(SLOW_WORK_S)
        except asyncio.CancelledError:
            cancelled.set()
            raise

    return _work(), cancelled


def _blocking_worker() -> (
    tuple[Coroutine[Any, Any, None], threading.Event, threading.Event]
):
    """Niet-coeperatief: blokkeert zonder await-punt, dus niet annuleerbaar."""
    release = threading.Event()
    finished = threading.Event()

    async def _work() -> None:
        release.wait(timeout=BLOCK_LIMIT_S)
        finished.set()

    return _work(), release, finished


def _cancel_resistant_worker() -> (
    tuple[Coroutine[Any, Any, None], threading.Event, threading.Event]
):
    """Vangt de annulering af en blijft dan blokkeren: cancel helpt niet."""
    release = threading.Event()
    finished = threading.Event()

    async def _work() -> None:
        try:
            await asyncio.sleep(SLOW_WORK_S)
        except asyncio.CancelledError:
            release.wait(timeout=BLOCK_LIMIT_S)
            finished.set()
            raise
        finished.set()

    return _work(), release, finished


def _assert_released(elapsed: float, limit: float, context: str, worker: str) -> None:
    assert elapsed <= limit, (
        f"{context}: caller pas na {elapsed:.6f}s vrij (grens {limit:.3f}s) "
        f"bij gevraagde timeout {REQUESTED_TIMEOUT_S}s en {worker}"
    )


# --- 1. Begrensd terugkeren binnen het budget -------------------------------


def test_timeout_returns_within_budget_without_running_loop() -> None:
    start = time.monotonic()
    with pytest.raises(TimeoutError):
        run_async(_slow(), timeout=REQUESTED_TIMEOUT_S)
    _assert_released(
        time.monotonic() - start, OUTER_DEADLINE_S, "sync", "coeperatief werk"
    )


@pytest.mark.asyncio
async def test_timeout_returns_within_budget_in_running_loop() -> None:
    """KERNREGRESSIE: het thread-pool-pad mag niet op de worker wachten."""
    start = time.monotonic()
    with pytest.raises(TimeoutError):
        run_async(_slow(), timeout=REQUESTED_TIMEOUT_S)
    _assert_released(
        time.monotonic() - start,
        OUTER_DEADLINE_S,
        "actieve loop",
        "coeperatief werk",
    )


# --- 2. Afwikkelmarge en opruiming van de losgelaten thread -----------------


def test_released_worker_thread_actually_exits() -> None:
    """De losgelaten worker-thread verdwijnt echt zodra zijn werk klaar is.

    De coroutine legt zelf vast op welke thread hij draait. Na de timeout geeft
    de test die worker vrij en joint uitsluitend die ene vastgelegde thread:
    bewijst dat de bridge geen draaiende thread achterlaat en dat de caller
    ondertussen op een andere thread zat.
    """
    release = threading.Event()
    finished = threading.Event()
    captured: list[threading.Thread] = []

    async def _work() -> None:
        captured.append(threading.current_thread())
        release.wait(timeout=BLOCK_LIMIT_S)
        finished.set()

    caller_thread = threading.current_thread()
    try:
        with pytest.raises(TimeoutError):
            run_async(_work(), timeout=REQUESTED_TIMEOUT_S)
    finally:
        release.set()

    assert captured, "de coroutine is nooit gestart op een eigen thread"
    worker = captured[0]
    assert (
        worker is not caller_thread
    ), "het werk draaide op de caller-thread; die kan niet vroegtijdig vrijkomen"

    worker.join(timeout=EVENT_WAIT_S)
    assert not worker.is_alive(), (
        f"worker-thread {worker.name} draait nog na {EVENT_WAIT_S}s: "
        "de bridge laat een thread achter"
    )
    assert finished.is_set(), "de vrijgegeven worker heeft zijn werk niet afgemaakt"


def test_cleanup_margin_is_respected_without_running_loop() -> None:
    """Sync-context: budget + marge, gemeten op een niet-annuleerbare worker."""
    coro, release, _finished = _blocking_worker()
    start = time.monotonic()
    try:
        with pytest.raises(TimeoutError):
            run_async(coro, timeout=REQUESTED_TIMEOUT_S)
        elapsed = time.monotonic() - start
    finally:
        release.set()
    _assert_released(elapsed, TIGHT_BUDGET_S, "sync", "blokkerende worker")


@pytest.mark.asyncio
async def test_cleanup_margin_is_respected_in_running_loop() -> None:
    """Actieve loop: budget + marge, gemeten op een niet-annuleerbare worker."""
    coro, release, _finished = _blocking_worker()
    start = time.monotonic()
    try:
        with pytest.raises(TimeoutError):
            run_async(coro, timeout=REQUESTED_TIMEOUT_S)
        elapsed = time.monotonic() - start
    finally:
        release.set()
    _assert_released(elapsed, TIGHT_BUDGET_S, "actieve loop", "blokkerende worker")


# --- 3. Coeperatieve annulering ---------------------------------------------


def test_cooperative_task_is_cancelled_without_running_loop() -> None:
    coro, cancelled = _cooperative_worker()
    with pytest.raises(TimeoutError):
        run_async(coro, timeout=REQUESTED_TIMEOUT_S)
    assert cancelled.wait(
        timeout=EVENT_WAIT_S
    ), "sync: de coeperatieve taak kreeg geen CancelledError bij timeout"


@pytest.mark.asyncio
async def test_cooperative_task_is_cancelled_in_running_loop() -> None:
    coro, cancelled = _cooperative_worker()
    with pytest.raises(TimeoutError):
        run_async(coro, timeout=REQUESTED_TIMEOUT_S)
    assert cancelled.wait(
        timeout=EVENT_WAIT_S
    ), "actieve loop: de coeperatieve taak kreeg geen CancelledError bij timeout"


# --- 4. Niet-coeperatieve worker houdt de caller niet vast ------------------


def test_non_cooperative_worker_does_not_hold_caller_without_running_loop() -> None:
    """Sync-context mag niet oneindig op een blokkerende worker wachten."""
    coro, release, finished = _blocking_worker()
    start = time.monotonic()
    try:
        with pytest.raises(TimeoutError):
            run_async(coro, timeout=REQUESTED_TIMEOUT_S)
        elapsed = time.monotonic() - start
    finally:
        release.set()
    _assert_released(elapsed, OUTER_DEADLINE_S, "sync", "blokkerende worker")
    assert finished.wait(
        timeout=EVENT_WAIT_S
    ), "sync: de losgelaten worker is niet afgerond na het vrijgeven"


@pytest.mark.asyncio
async def test_non_cooperative_worker_does_not_hold_caller_in_running_loop() -> None:
    coro, release, finished = _blocking_worker()
    start = time.monotonic()
    try:
        with pytest.raises(TimeoutError):
            run_async(coro, timeout=REQUESTED_TIMEOUT_S)
        elapsed = time.monotonic() - start
    finally:
        release.set()
    _assert_released(elapsed, OUTER_DEADLINE_S, "actieve loop", "blokkerende worker")
    assert finished.wait(
        timeout=EVENT_WAIT_S
    ), "actieve loop: de losgelaten worker is niet afgerond na het vrijgeven"


# --- 5. Worker die de annulering negeert ------------------------------------


def test_cancel_resistant_worker_does_not_hold_caller_without_running_loop() -> None:
    """Een genegeerde CancelledError mag de caller niet alsnog vastzetten."""
    coro, release, finished = _cancel_resistant_worker()
    start = time.monotonic()
    try:
        with pytest.raises(TimeoutError):
            run_async(coro, timeout=REQUESTED_TIMEOUT_S)
        elapsed = time.monotonic() - start
    finally:
        release.set()
    _assert_released(elapsed, OUTER_DEADLINE_S, "sync", "cancel-negerende worker")
    assert finished.wait(
        timeout=EVENT_WAIT_S
    ), "sync: de cancel-negerende worker is niet afgerond na het vrijgeven"


@pytest.mark.asyncio
async def test_cancel_resistant_worker_does_not_hold_caller_in_running_loop() -> None:
    coro, release, finished = _cancel_resistant_worker()
    start = time.monotonic()
    try:
        with pytest.raises(TimeoutError):
            run_async(coro, timeout=REQUESTED_TIMEOUT_S)
        elapsed = time.monotonic() - start
    finally:
        release.set()
    _assert_released(
        elapsed, OUTER_DEADLINE_S, "actieve loop", "cancel-negerende worker"
    )
    assert finished.wait(
        timeout=EVENT_WAIT_S
    ), "actieve loop: de cancel-negerende worker is niet afgerond na het vrijgeven"


# --- 6. run_async_safe: exacte default binnen budget ------------------------


def test_run_async_safe_returns_exact_default_without_running_loop() -> None:
    start = time.monotonic()
    result = run_async_safe(
        _slow(), default=_DEFAULT_SENTINEL, timeout=REQUESTED_TIMEOUT_S
    )
    elapsed = time.monotonic() - start

    assert result is _DEFAULT_SENTINEL
    _assert_released(elapsed, OUTER_DEADLINE_S, "sync", "run_async_safe")


@pytest.mark.asyncio
async def test_run_async_safe_returns_exact_default_in_running_loop() -> None:
    start = time.monotonic()
    result = run_async_safe(
        _slow(), default=_DEFAULT_SENTINEL, timeout=REQUESTED_TIMEOUT_S
    )
    elapsed = time.monotonic() - start

    assert result is _DEFAULT_SENTINEL
    _assert_released(elapsed, OUTER_DEADLINE_S, "actieve loop", "run_async_safe")


# --- 7. Exception-identiteit blijft behouden --------------------------------


def test_runtime_error_identity_preserved_without_running_loop() -> None:
    sentinel = RuntimeError("DEF-519 unieke fout uit de coroutine")

    async def _boom() -> None:
        raise sentinel

    with pytest.raises(RuntimeError) as excinfo:
        run_async(_boom(), timeout=5)

    assert excinfo.value is sentinel


@pytest.mark.asyncio
async def test_runtime_error_identity_preserved_in_running_loop() -> None:
    """De try/except om get_running_loop mag ALLEEN de detectie afvangen.

    Vangt hij ook de uitvoering af, dan valt een RuntimeError uit de coroutine
    door naar de asyncio.run-fallback en krijgt de caller een andere fout terug.
    """
    sentinel = RuntimeError("DEF-519 unieke fout uit de coroutine")

    async def _boom() -> None:
        raise sentinel

    with pytest.raises(RuntimeError) as excinfo:
        run_async(_boom(), timeout=5)

    assert (
        excinfo.value is sentinel
    ), f"exception-identiteit verloren: {excinfo.value!r} i.p.v. {sentinel!r}"


@pytest.mark.asyncio
async def test_user_exception_identity_preserved_in_running_loop() -> None:
    sentinel = ValueError("DEF-519 unieke waardefout")

    async def _boom() -> None:
        raise sentinel

    with pytest.raises(ValueError, match="unieke waardefout") as excinfo:
        run_async(_boom(), timeout=5)

    assert excinfo.value is sentinel


# --- 8. timeout=None en timeout=0 -------------------------------------------


def test_timeout_none_returns_result_without_running_loop() -> None:
    async def _quick() -> str:
        return "ok"

    assert run_async(_quick(), timeout=None) == "ok"


@pytest.mark.asyncio
async def test_timeout_none_returns_result_in_running_loop() -> None:
    async def _quick() -> str:
        return "ok"

    assert run_async(_quick(), timeout=None) == "ok"


def test_timeout_zero_is_immediate_budget_without_running_loop() -> None:
    """timeout=0 is een expliciet budget van nul, geen ontbrekende timeout."""
    start = time.monotonic()
    with pytest.raises(TimeoutError):
        run_async(_slow(), timeout=0)
    _assert_released(time.monotonic() - start, OUTER_DEADLINE_S, "sync", "timeout=0")


@pytest.mark.asyncio
async def test_timeout_zero_is_immediate_budget_in_running_loop() -> None:
    start = time.monotonic()
    with pytest.raises(TimeoutError):
        run_async(_slow(), timeout=0)
    _assert_released(
        time.monotonic() - start, OUTER_DEADLINE_S, "actieve loop", "timeout=0"
    )


def test_timeout_zero_leaves_no_unawaited_coroutine() -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        with pytest.raises(TimeoutError):
            run_async(_slow(), timeout=0)
        gc.collect()

    never_awaited = [w for w in caught if "never awaited" in str(w.message)]
    assert never_awaited == [], f"niet-awaited coroutine(s): {never_awaited}"


# --- 9. run_parallel deelt hetzelfde begrensde pad --------------------------


@pytest.mark.asyncio
async def test_run_parallel_timeout_is_bounded_in_running_loop() -> None:
    start = time.monotonic()
    with pytest.raises(TimeoutError):
        run_parallel(_slow(), _slow(), timeout=REQUESTED_TIMEOUT_S)
    _assert_released(
        time.monotonic() - start, OUTER_DEADLINE_S, "actieve loop", "run_parallel"
    )


@pytest.mark.asyncio
async def test_run_parallel_still_returns_results_in_running_loop() -> None:
    async def _one() -> int:
        return 1

    async def _two() -> int:
        return 2

    assert run_parallel(_one(), _two(), timeout=5) == (1, 2)
