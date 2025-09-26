"""Centralized async bridge for UI components.

This module provides a central place for handling async/sync conversions
in the UI layer. Services should remain async, UI handles the bridging.

Per US-043: All async-to-sync conversions should go through this module.
"""

import asyncio
import logging
from collections.abc import Coroutine
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


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
    import threading
    from concurrent.futures import ThreadPoolExecutor

    # Check if we're in the main thread with a running event loop (Streamlit)
    try:
        loop = asyncio.get_running_loop()
        # We're in an async context with a running loop
        # Use a thread pool to run the coroutine in isolation
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result(timeout=timeout) if timeout else future.result()
    except RuntimeError:
        # No running loop, we can safely use asyncio.run
        pass

    # No running loop - create new one
    if timeout:
        async def with_timeout():
            return await asyncio.wait_for(coro, timeout)

        return asyncio.run(with_timeout())
    return asyncio.run(coro)


def run_async_safe(
    coro: Coroutine[Any, Any, T],
    default: T | None = None,
    timeout: float | None = 5.0  # Default 5 second timeout for safety
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
    except asyncio.TimeoutError:
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
    return await asyncio.gather(*coros)


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


def create_async_callback(coro_func):
    """Create a sync callback that runs an async function.

    Useful for Streamlit callbacks that need to call async services.

    Args:
        coro_func: Async function to wrap

    Returns:
        Sync function that runs the async function

    Example:
        st.button("Generate", on_click=create_async_callback(async_generate))
    """

    def sync_wrapper(*args, **kwargs):
        coro = coro_func(*args, **kwargs)
        return run_async(coro)

    sync_wrapper.__name__ = f"sync_{coro_func.__name__}"
    sync_wrapper.__doc__ = f"Sync wrapper for {coro_func.__name__}"

    return sync_wrapper


# Service-specific wrappers for UI usage
def generate_definition_sync(
    service_adapter, begrip: str, context_dict: dict, **kwargs
):
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
    return run_async(
        service_adapter.generate_definition(begrip, context_dict, **kwargs),
        timeout=timeout,
    )


def search_web_sources_sync(
    service_factory, term: str, sources: list | None = None
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

    async def do_search():
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
