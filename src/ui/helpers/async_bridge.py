"""Centralized async bridge for UI components.

This module provides a central place for handling async/sync conversions
in the UI layer. Services should remain async, UI handles the bridging.

Per US-043: All async-to-sync conversions should go through this module.
"""

import asyncio
import logging
from collections.abc import Callable, Coroutine
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

# DEF-519: expliciete, kleine afwikkelmarge bovenop het gevraagde budget. De
# coeperatieve cancel vuurt op `timeout`; deze marge geeft die cancel net de tijd
# om af te ronden voordat de caller hoe dan ook wordt vrijgegeven. Bewust klein
# en begrensd -- geen schaduwtimeout van seconden.
_CLEANUP_MARGIN_S = 0.25


def run_async(coro: Coroutine[Any, Any, T], timeout: float | None = None) -> T:
    """Run an async coroutine from sync context (UI).

    This is the centralized bridge for UI components that need to call
    async services. Services should NOT use this - they should remain async.

    Args:
        coro: The coroutine to run
        timeout: Optional timeout in seconds

    Returns:
        The result of the coroutine

    Example:
        result = run_async(service.async_method(args))
    """
    # DEF-519: ALLEEN de loop-detectie staat in de try/except. Zou de uitvoering
    # er ook in staan, dan wordt een RuntimeError uit de coroutine zelf gelezen
    # als "geen draaiende loop" en draait de al geconsumeerde coroutine opnieuw --
    # de caller krijgt dan een andere exception dan de coroutine gooide.
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        loop_is_running = False
    else:
        loop_is_running = True

    # `timeout is not None` (niet truthiness): timeout=0 is een expliciet budget
    # van nul, geen ontbrekende timeout. wait_for annuleert de coroutine
    # coeperatief binnen de loop die hem draait.
    wrapped = coro if timeout is None else asyncio.wait_for(coro, timeout)

    if timeout is None and not loop_is_running:
        # Geen budget te bewaken: gewoon in de caller-thread draaien.
        return asyncio.run(wrapped)

    # Met een budget draait het werk altijd op een worker-thread -- ook zonder
    # draaiende loop. Een coroutine die blokkeert zonder await-punt negeert de
    # coeperatieve cancel; alleen een aparte thread laat de caller dan alsnog
    # binnen zijn budget terugkeren.
    return _run_in_worker_loop(wrapped, timeout)


def _run_in_worker_loop(coro: Coroutine[Any, Any, T], timeout: float | None) -> T:
    """Draai `coro` in een eigen loop op een worker-thread en keer begrensd terug.

    De executor wordt bewust NIET als context-manager gebruikt: het verlaten
    daarvan doet `shutdown(wait=True)` en laat de caller alsnog op de worker
    wachten -- precies de gemeten budgetoverschrijding (0.30s bij een gevraagde
    0.01s). `shutdown(wait=False)` geeft de caller direct vrij.

    Beperking: een worker die blokkeert zonder await-punt (of die zijn
    CancelledError negeert) kan door Python niet geforceerd worden gestopt. De
    caller komt vrij binnen het budget, maar de thread loopt door tot zijn eigen
    werk klaar is.
    """
    from concurrent.futures import ThreadPoolExecutor

    executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ui-async-bridge")
    try:
        future = executor.submit(asyncio.run, coro)
        budget = None if timeout is None else timeout + _CLEANUP_MARGIN_S
        return future.result(timeout=budget)
    finally:
        executor.shutdown(wait=False)


def run_async_safe(
    coro: Coroutine[Any, Any, T],
    default: T | None = None,
    timeout: float | None = 5.0,  # Default 5 second timeout for safety
) -> T | None:
    """Run an async coroutine safely, returning default on error or timeout.

    Args:
        coro: The coroutine to run
        default: Default value to return on error or timeout
        timeout: Timeout in seconds (default 5.0, None for no timeout)

    Returns:
        The result of the coroutine or default value
    """
    try:
        return run_async(coro, timeout=timeout)
    except TimeoutError:
        logger.warning(f"Async operation timed out after {timeout}s")
        return default
    except Exception as e:
        logger.warning(f"Async operation failed: {e}")
        return default


async def gather_async(*coros: Coroutine[Any, Any, Any]) -> tuple[Any, ...]:
    """Gather multiple async operations.

    Args:
        *coros: Coroutines to run concurrently

    Returns:
        Tuple of results in the same order as inputs
    """
    results = await asyncio.gather(*coros)
    return tuple(results)


def run_parallel(
    *coros: Coroutine[Any, Any, Any], timeout: float | None = None
) -> tuple[Any, ...]:
    """Run multiple async operations in parallel from sync context.

    Args:
        *coros: Coroutines to run concurrently
        timeout: Optional timeout in seconds for all operations

    Returns:
        Tuple of results in the same order as inputs

    Example:
        result1, result2 = run_parallel(
            service.method1(),
            service.method2(),
            timeout=10
        )
    """
    return run_async(gather_async(*coros), timeout=timeout)


def create_async_callback(coro_func: Callable[..., Any]) -> Callable[..., Any]:
    """Create a sync callback that runs an async function.

    Useful for Streamlit callbacks that need to call async services.

    Args:
        coro_func: Async function to wrap

    Returns:
        Sync function that runs the async function

    Example:
        st.button("Generate", on_click=create_async_callback(async_generate))
    """

    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        coro = coro_func(*args, **kwargs)
        return run_async(coro)

    sync_wrapper.__name__ = f"sync_{coro_func.__name__}"
    sync_wrapper.__doc__ = f"Sync wrapper for {coro_func.__name__}"

    return sync_wrapper


# Service-specific wrappers for UI usage
def generate_definition_sync(
    service_adapter: Any, begrip: str, context_dict: dict[str, Any], **kwargs: Any
) -> Any:
    """Sync wrapper for generating definitions from UI.

    This wraps the async generate_definition method from ServiceAdapter
    for use in synchronous UI code.

    Args:
        service_adapter: The ServiceAdapter instance (from get_definition_service)
        begrip: Term to define
        context_dict: Context dictionary
        **kwargs: Additional arguments

    Returns:
        Definition response dictionary
    """
    from config.rate_limit_config import get_endpoint_timeout

    # Gebruik endpoint-specifieke timeout uit rate_limit_config
    timeout = get_endpoint_timeout("definition_generation")
    logger.debug(f"Using timeout of {timeout}s for definition generation")

    # ServiceAdapter.generate_definition is async, dus we gebruiken run_async
    # DEF-451: het getypeerde response wordt hier geserialiseerd naar de UI-dict
    _response = run_async(
        service_adapter.generate_definition(begrip, context_dict, **kwargs),
        timeout=timeout,
    )
    return service_adapter.to_ui_response(_response)


def search_web_sources_sync(
    service_factory: Any, term: str, sources: list | None = None
) -> dict:
    """Sync wrapper for web lookup from UI.

    Args:
        service_factory: The ServiceFactory instance
        term: Search term
        sources: Optional list of sources

    Returns:
        Legacy format search results
    """
    from services.interfaces import LookupRequest

    async def do_search() -> dict[str, Any]:
        request = LookupRequest(term=term, sources=sources, max_results=5)
        results = await service_factory.web_lookup.lookup(request)

        # Convert to legacy format
        legacy_results = {}
        for result in results:
            legacy_results[result.source.name] = {
                "definitie": result.definition,
                "context": result.context,
                "voorbeelden": result.examples,
                "verwijzingen": result.references,
                "betrouwbaarheid": result.source.confidence,
            }
        return legacy_results

    return run_async(do_search(), timeout=15)  # 15 second timeout for web lookup
