"""Progress context manager for operation state tracking.

This module provides a context manager for tracking operation progress in the UI.
It isolates the UI layer coupling (SessionStateManager) to a single location,
allowing services/database layers to track progress without importing from ui/.

Created for DEF-173: Fix Legacy Pattern Gates - UI Import Violations.

Usage:
    from services.progress_context import operation_progress

    async def create_definitie(self, ...):
        with operation_progress("saving_to_database"):
            # ... database operation ...

    def validate_definition(self, ...):
        with operation_progress("validating_definition"):
            # ... validation operation ...
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Generator


@contextmanager
def operation_progress(operation_name: str) -> Generator[None, None, None]:
    """Context manager for tracking operation progress in the UI.

    Sets a session state flag to True when entering the context and False when exiting.
    Soft-fails if SessionStateManager is not available (e.g., in tests or non-UI contexts).

    Args:
        operation_name: Name of the operation (used as session state key with "_active" suffix)

    Yields:
        None

    Example:
        with operation_progress("saving_to_database"):
            # UI will see saving_to_database = True
            await repository.save(data)
        # UI will see saving_to_database = False
    """
    # Try to set progress flag - soft-fail if session state unavailable
    try:
        from ui.session_state import SessionStateManager

        SessionStateManager.set_value(operation_name, True)
    except Exception:
        pass  # Soft-fail if session state unavailable (e.g., in tests)

    try:
        yield
    finally:
        # Always try to clear the flag, even on error
        try:
            from ui.session_state import SessionStateManager

            SessionStateManager.set_value(operation_name, False)
        except Exception:
            pass  # Soft-fail if session state unavailable


def set_progress(operation_name: str, active: bool) -> None:
    """Directly set a progress flag (for cases where context manager doesn't fit).

    Soft-fails if SessionStateManager is not available.

    Args:
        operation_name: Name of the operation
        active: Whether the operation is active
    """
    try:
        from ui.session_state import SessionStateManager

        SessionStateManager.set_value(operation_name, active)
    except Exception:
        pass  # Soft-fail if session state unavailable
