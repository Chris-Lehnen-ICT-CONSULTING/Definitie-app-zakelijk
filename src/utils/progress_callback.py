"""Progress callback system for operation state tracking.

This module provides a clean architecture solution for progress tracking:
- Services/database layers import from utils/ (allowed by architecture)
- UI layer registers a callback at startup
- No layer violations: utils/ is a shared dependency

Created for DEF-198: Fix Layer Violation with proper architecture.

Usage in services:
    from utils.progress_callback import operation_progress, notify_progress

    with operation_progress("saving_to_database"):
        # ... operation ...

Usage in UI (main.py):
    # Import and register the callback at startup (see main.py for actual usage)
    register_progress_callback(SessionStateManager.set_value)
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from contextlib import contextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Generator

logger = logging.getLogger(__name__)

# Global callback - set by UI layer at startup
_progress_callback: Callable[[str, bool], None] | None = None


def register_progress_callback(callback: Callable[[str, bool], None]) -> None:
    """Register a callback for progress notifications.

    Called by UI layer at startup to wire up SessionStateManager.

    Args:
        callback: Function that takes (operation_name: str, active: bool)
    """
    global _progress_callback
    _progress_callback = callback
    logger.debug("Progress callback registered")


def unregister_progress_callback() -> None:
    """Unregister the progress callback (for testing)."""
    global _progress_callback
    _progress_callback = None
    logger.debug("Progress callback unregistered")


def notify_progress(operation_name: str, active: bool) -> None:
    """Notify progress state change.

    Soft-fails if no callback is registered (e.g., in tests or CLI contexts).

    Args:
        operation_name: Name of the operation
        active: Whether the operation is active
    """
    if _progress_callback is None:
        logger.debug(
            "Progress notification for '%s' (active=%s) - no callback registered",
            operation_name,
            active,
        )
        return

    try:
        _progress_callback(operation_name, active)
    except Exception as e:
        # Never let progress tracking break business logic
        logger.warning(
            "Progress callback failed for '%s' (active=%s): %s",
            operation_name,
            active,
            e,
        )


@contextmanager
def operation_progress(operation_name: str) -> Generator[None, None, None]:
    """Context manager for tracking operation progress.

    Sets progress to True on entry, False on exit.
    Soft-fails if no callback is registered.

    Args:
        operation_name: Name of the operation (used as session state key)

    Yields:
        None

    Example:
        with operation_progress("saving_to_database"):
            await repository.save(data)
    """
    notify_progress(operation_name, True)
    try:
        yield
    finally:
        notify_progress(operation_name, False)
