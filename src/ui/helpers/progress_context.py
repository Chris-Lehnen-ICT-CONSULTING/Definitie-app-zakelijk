"""Progress context manager for operation state tracking.

This module provides a context manager for tracking operation progress in the UI.
It isolates the UI layer coupling (SessionStateManager) to a single location,
allowing services/database layers to track progress by importing from ui/helpers/.

Created for DEF-173: Fix Legacy Pattern Gates - UI Import Violations.
Enhanced for DEF-198: Fix Layer Violation - Silent Failures + Move to UI Layer.

Usage:
    from ui.helpers.progress_context import operation_progress

    async def create_definitie(self, ...):
        with operation_progress("saving_to_database"):
            # ... database operation ...

    def validate_definition(self, ...):
        with operation_progress("validating_definition"):
            # ... validation operation ...
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Generator

# Initialize logger for this module
logger = logging.getLogger(__name__)


@contextmanager
def operation_progress(operation_name: str) -> Generator[None, None, None]:
    """Context manager for tracking operation progress in the UI.

    Sets a session state flag to True when entering the context and False when exiting.
    Soft-fails if SessionStateManager is not available (e.g., in tests or non-UI contexts).

    Args:
        operation_name: Name of the operation (used as session state key)

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
    except (ImportError, ModuleNotFoundError):
        # Expected: No SessionStateManager in tests/non-UI contexts
        logger.debug(
            "Progress tracking unavailable for '%s' (expected in tests/non-UI contexts)",
            operation_name,
        )
    except AttributeError as e:
        # Unexpected: SessionStateManager exists but set_value missing
        logger.warning(
            "SessionStateManager.set_value() failed for '%s': %s",
            operation_name,
            e,
        )
    except Exception as e:
        # Unexpected: Unknown error - potential bug
        logger.error(
            "Unexpected error setting progress flag for '%s': %s",
            operation_name,
            e,
            exc_info=True,
        )

    try:
        yield
    finally:
        # Always try to clear the flag, even on error
        try:
            from ui.session_state import SessionStateManager

            SessionStateManager.set_value(operation_name, False)
        except (ImportError, ModuleNotFoundError):
            # Expected: No SessionStateManager in tests/non-UI contexts
            logger.debug(
                "Progress tracking cleanup unavailable for '%s' (expected in tests/non-UI contexts)",
                operation_name,
            )
        except AttributeError as e:
            # Unexpected: SessionStateManager exists but set_value missing
            logger.warning(
                "SessionStateManager.set_value() cleanup failed for '%s': %s",
                operation_name,
                e,
            )
        except Exception as e:
            # Unexpected: Unknown error - potential bug
            logger.error(
                "Unexpected error clearing progress flag for '%s': %s",
                operation_name,
                e,
                exc_info=True,
            )


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
    except (ImportError, ModuleNotFoundError):
        # Expected: No SessionStateManager in tests/non-UI contexts
        logger.debug(
            "Progress tracking unavailable for '%s' (active=%s, expected in tests/non-UI contexts)",
            operation_name,
            active,
        )
    except AttributeError as e:
        # Unexpected: SessionStateManager exists but set_value missing
        logger.warning(
            "SessionStateManager.set_value() failed for '%s' (active=%s): %s",
            operation_name,
            active,
            e,
        )
    except Exception as e:
        # Unexpected: Unknown error - potential bug
        logger.error(
            "Unexpected error in set_progress for '%s' (active=%s): %s",
            operation_name,
            active,
            e,
            exc_info=True,
        )
