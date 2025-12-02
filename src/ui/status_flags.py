"""
DEF-237: Status Flags Pattern for Session State Management.

Provides explicit status tracking for generation and edit workflows,
acting as a simpler alternative to a full State Machine pattern.

Benefits over raw session state access:
- Type-safe status transitions
- Clear semantic methods (is_idle, start_generation, mark_complete)
- Single source of truth for workflow status
- Easy to test via SessionStateManager mocking

Usage:
    # Generation workflow
    if GenerationStatus.is_idle():
        GenerationStatus.start_generation(begrip="Kwaliteit")
        ...
        GenerationStatus.mark_complete(result)

    # Edit workflow
    if EditSessionStatus.is_idle():
        EditSessionStatus.start_edit(definition_id=123)
        ...
        EditSessionStatus.mark_saved()
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

from ui.session_state import SessionStateManager

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class GenerationState(Enum):
    """Possible states for the generation workflow."""

    IDLE = "idle"
    CHECKING = "checking"  # Duplicate check in progress
    GENERATING = "generating"  # AI generation in progress
    VALIDATING = "validating"  # Rule validation in progress
    COMPLETE = "complete"  # Generation finished successfully
    ERROR = "error"  # Generation failed


@dataclass
class GenerationContext:
    """Context data passed through generation workflow."""

    begrip: str
    organisatorische_context: list[str]
    juridische_context: list[str]
    wettelijke_basis: list[str]
    force_generate: bool = False


class GenerationStatus:
    """Generation workflow status tracking via SessionStateManager.

    Provides explicit status methods instead of direct session state access.
    All state survives st.rerun() via SessionStateManager.
    """

    # Session state keys (aligned with existing codebase patterns)
    STATUS_KEY = "generation_status"
    ERROR_KEY = "generation_error"
    RESULT_KEY = "last_generation_result"
    CHECK_KEY = "last_check_result"
    OPTIONS_KEY = "generation_options"
    BEGRIP_KEY = "current_begrip"
    TRIGGER_KEY = "trigger_auto_generation"

    @staticmethod
    def get_state() -> GenerationState:
        """Get current generation state."""
        status = SessionStateManager.get_value(GenerationStatus.STATUS_KEY, "idle")
        try:
            return GenerationState(status)
        except ValueError:
            logger.warning(f"Unknown generation status '{status}', defaulting to IDLE")
            return GenerationState.IDLE

    @staticmethod
    def is_idle() -> bool:
        """Check if no generation in progress."""
        state = GenerationStatus.get_state()
        return state in (
            GenerationState.IDLE,
            GenerationState.COMPLETE,
            GenerationState.ERROR,
        )

    @staticmethod
    def is_busy() -> bool:
        """Check if generation or validation is in progress."""
        state = GenerationStatus.get_state()
        return state in (
            GenerationState.CHECKING,
            GenerationState.GENERATING,
            GenerationState.VALIDATING,
        )

    @staticmethod
    def start_check(begrip: str) -> None:
        """Mark duplicate check started."""
        SessionStateManager.set_value(
            GenerationStatus.STATUS_KEY, GenerationState.CHECKING.value
        )
        SessionStateManager.set_value(GenerationStatus.BEGRIP_KEY, begrip)
        SessionStateManager.clear_value(GenerationStatus.ERROR_KEY)
        SessionStateManager.clear_value(GenerationStatus.CHECK_KEY)
        logger.debug(f"Generation workflow: started check for '{begrip}'")

    @staticmethod
    def start_generation(begrip: str, options: dict[str, Any] | None = None) -> None:
        """Mark generation started."""
        SessionStateManager.set_value(
            GenerationStatus.STATUS_KEY, GenerationState.GENERATING.value
        )
        SessionStateManager.set_value(GenerationStatus.BEGRIP_KEY, begrip)
        SessionStateManager.clear_value(GenerationStatus.ERROR_KEY)
        if options:
            SessionStateManager.set_value(GenerationStatus.OPTIONS_KEY, options)
        logger.debug(f"Generation workflow: started generation for '{begrip}'")

    @staticmethod
    def start_validation() -> None:
        """Mark validation started."""
        SessionStateManager.set_value(
            GenerationStatus.STATUS_KEY, GenerationState.VALIDATING.value
        )
        logger.debug("Generation workflow: started validation")

    @staticmethod
    def mark_check_complete(check_result: Any) -> None:
        """Mark duplicate check complete with result."""
        SessionStateManager.set_value(GenerationStatus.CHECK_KEY, check_result)
        # Status returns to IDLE after check - generation may or may not follow
        SessionStateManager.set_value(
            GenerationStatus.STATUS_KEY, GenerationState.IDLE.value
        )
        logger.debug("Generation workflow: check complete")

    @staticmethod
    def mark_complete(result: Any) -> None:
        """Mark generation complete with result."""
        SessionStateManager.set_value(
            GenerationStatus.STATUS_KEY, GenerationState.COMPLETE.value
        )
        SessionStateManager.set_value(GenerationStatus.RESULT_KEY, result)
        SessionStateManager.clear_value(GenerationStatus.TRIGGER_KEY)
        logger.debug("Generation workflow: generation complete")

    @staticmethod
    def mark_error(error: str, exc_info: bool = False) -> None:
        """Mark generation failed with error."""
        SessionStateManager.set_value(
            GenerationStatus.STATUS_KEY, GenerationState.ERROR.value
        )
        SessionStateManager.set_value(GenerationStatus.ERROR_KEY, error)
        SessionStateManager.clear_value(GenerationStatus.TRIGGER_KEY)
        logger.error(
            f"Generation workflow failed: {error}",
            exc_info=exc_info,
            extra={"component": "status_flags", "operation": "mark_error"},
        )

    @staticmethod
    def get_error() -> str | None:
        """Get current error message, if any."""
        return SessionStateManager.get_value(GenerationStatus.ERROR_KEY)

    @staticmethod
    def get_result() -> Any | None:
        """Get last generation result."""
        return SessionStateManager.get_value(GenerationStatus.RESULT_KEY)

    @staticmethod
    def get_check_result() -> Any | None:
        """Get last check result."""
        return SessionStateManager.get_value(GenerationStatus.CHECK_KEY)

    @staticmethod
    def get_current_begrip() -> str | None:
        """Get begrip currently being processed."""
        return SessionStateManager.get_value(GenerationStatus.BEGRIP_KEY)

    @staticmethod
    def should_trigger_auto() -> bool:
        """Check if auto-generation should be triggered."""
        return bool(SessionStateManager.get_value(GenerationStatus.TRIGGER_KEY, False))

    @staticmethod
    def set_trigger_auto(trigger: bool = True) -> None:
        """Set auto-generation trigger flag."""
        if trigger:
            SessionStateManager.set_value(GenerationStatus.TRIGGER_KEY, True)
        else:
            SessionStateManager.clear_value(GenerationStatus.TRIGGER_KEY)

    @staticmethod
    def reset() -> None:
        """Clear all generation state."""
        for key in [
            GenerationStatus.STATUS_KEY,
            GenerationStatus.ERROR_KEY,
            GenerationStatus.RESULT_KEY,
            GenerationStatus.CHECK_KEY,
            GenerationStatus.BEGRIP_KEY,
            GenerationStatus.TRIGGER_KEY,
        ]:
            SessionStateManager.clear_value(key)
        logger.debug("Generation workflow: reset all state")


class EditState(Enum):
    """Possible states for the edit session workflow."""

    IDLE = "idle"
    LOADING = "loading"  # Loading definition from database
    EDITING = "editing"  # Active edit session
    SAVING = "saving"  # Save in progress
    SAVED = "saved"  # Just saved successfully


class EditSessionStatus:
    """Edit session workflow status tracking via SessionStateManager.

    Provides explicit status methods for definition editing workflow.
    Includes race condition protection via version tracking (DEF-236).
    """

    # Session state keys (aligned with existing codebase patterns)
    STATUS_KEY = "edit_session_status"
    DEFINITION_ID_KEY = "editing_definition_id"
    DEFINITION_KEY = "editing_definition"
    SESSION_KEY = "edit_session"
    VERSION_KEY = "edit_load_version"
    SEARCH_KEY = "edit_search_results"
    LAST_SAVE_KEY = "last_auto_save"

    @staticmethod
    def get_state() -> EditState:
        """Get current edit session state."""
        status = SessionStateManager.get_value(EditSessionStatus.STATUS_KEY, "idle")
        try:
            return EditState(status)
        except ValueError:
            logger.warning(f"Unknown edit status '{status}', defaulting to IDLE")
            return EditState.IDLE

    @staticmethod
    def is_idle() -> bool:
        """Check if no edit session active."""
        return EditSessionStatus.get_state() == EditState.IDLE

    @staticmethod
    def is_editing() -> bool:
        """Check if an edit session is active."""
        state = EditSessionStatus.get_state()
        return state in (EditState.EDITING, EditState.LOADING, EditState.SAVING)

    @staticmethod
    def has_active_definition() -> bool:
        """Check if a definition is currently loaded for editing."""
        return (
            SessionStateManager.get_value(EditSessionStatus.DEFINITION_ID_KEY)
            is not None
        )

    @staticmethod
    def start_load(definition_id: int) -> int:
        """Mark loading started, return load version for race detection.

        DEF-236: The returned version should be compared after loading
        to detect if a concurrent load occurred.
        """
        SessionStateManager.set_value(
            EditSessionStatus.STATUS_KEY, EditState.LOADING.value
        )
        SessionStateManager.set_value(
            EditSessionStatus.DEFINITION_ID_KEY, definition_id
        )

        # Increment version for race condition detection
        current_version = SessionStateManager.get_value(
            EditSessionStatus.VERSION_KEY, 0
        )
        new_version = current_version + 1
        SessionStateManager.set_value(EditSessionStatus.VERSION_KEY, new_version)

        logger.debug(
            f"Edit workflow: started load v{new_version} for definition {definition_id}"
        )
        return new_version

    @staticmethod
    def check_load_version(expected_version: int) -> bool:
        """Check if load version matches expected (no concurrent load occurred).

        DEF-236: Returns False if another load was triggered during this load.
        """
        current_version = SessionStateManager.get_value(
            EditSessionStatus.VERSION_KEY, 0
        )
        if current_version != expected_version:
            logger.warning(
                f"Concurrent edit load detected: expected v{expected_version}, "
                f"current v{current_version}",
                extra={
                    "component": "status_flags",
                    "operation": "check_load_version",
                    "expected": expected_version,
                    "current": current_version,
                },
            )
            return False
        return True

    @staticmethod
    def mark_loaded(definition: Any, session: dict[str, Any]) -> None:
        """Mark definition loaded and edit session active."""
        SessionStateManager.set_value(
            EditSessionStatus.STATUS_KEY, EditState.EDITING.value
        )
        SessionStateManager.set_value(EditSessionStatus.DEFINITION_KEY, definition)
        SessionStateManager.set_value(EditSessionStatus.SESSION_KEY, session)
        logger.debug("Edit workflow: definition loaded, session active")

    @staticmethod
    def start_save() -> None:
        """Mark save operation started."""
        SessionStateManager.set_value(
            EditSessionStatus.STATUS_KEY, EditState.SAVING.value
        )
        logger.debug("Edit workflow: started save")

    @staticmethod
    def mark_saved() -> None:
        """Mark save completed successfully."""
        from datetime import datetime

        SessionStateManager.set_value(
            EditSessionStatus.STATUS_KEY, EditState.SAVED.value
        )
        SessionStateManager.set_value(EditSessionStatus.LAST_SAVE_KEY, datetime.now())
        logger.debug("Edit workflow: save complete")
        # Return to editing state after brief saved indicator
        SessionStateManager.set_value(
            EditSessionStatus.STATUS_KEY, EditState.EDITING.value
        )

    @staticmethod
    def get_definition_id() -> int | None:
        """Get ID of currently edited definition."""
        return SessionStateManager.get_value(EditSessionStatus.DEFINITION_ID_KEY)

    @staticmethod
    def get_definition() -> Any | None:
        """Get currently loaded definition object."""
        return SessionStateManager.get_value(EditSessionStatus.DEFINITION_KEY)

    @staticmethod
    def get_session() -> dict[str, Any] | None:
        """Get current edit session metadata."""
        return SessionStateManager.get_value(EditSessionStatus.SESSION_KEY)

    @staticmethod
    def reset() -> None:
        """End edit session and clear all state."""
        for key in [
            EditSessionStatus.STATUS_KEY,
            EditSessionStatus.DEFINITION_ID_KEY,
            EditSessionStatus.DEFINITION_KEY,
            EditSessionStatus.SESSION_KEY,
            EditSessionStatus.SEARCH_KEY,
        ]:
            SessionStateManager.clear_value(key)
        # Note: VERSION_KEY is NOT cleared - it keeps incrementing for race detection
        logger.debug("Edit workflow: session reset")
