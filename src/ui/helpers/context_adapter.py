"""
Context Adapter - Bridge between UI components and ContextManager.

This adapter provides backward compatibility for existing UI components
while routing all context operations through the centralized ContextManager.
"""

import logging
from typing import Any

import streamlit as st

from services.context.context_manager import (
    ContextManager,
    ContextSource,
    get_context_manager,
)

logger = logging.getLogger(__name__)


class ContextAdapter:
    """
    Adapter for migrating UI components to ContextManager.

    Provides compatibility layer for existing code while ensuring
    all context operations go through the centralized manager.
    """

    def __init__(self, context_manager: ContextManager | None = None):
        """
        Initialize the adapter.

        Args:
            context_manager: Optional ContextManager instance, uses singleton if not provided
        """
        self.context_manager = context_manager or get_context_manager()
        logger.info("ContextAdapter initialized")

    def get_from_session_state(self) -> dict[str, Any]:
        """
        Get context from session state (legacy compatibility).

        This method provides backward compatibility for code that expects
        to read context from st.session_state directly.

        Returns:
            Context dictionary compatible with legacy code
        """
        # First check if ContextManager has context
        current = self.context_manager.get_context()
        if current is not None:
            return current.to_dict()

        # Fallback to session state for backward compatibility
        context = {}

        # Extract context fields from session state
        if hasattr(st.session_state, "begrip"):
            context["begrip"] = st.session_state.begrip

        if hasattr(st.session_state, "wet_context"):
            context["wet_context"] = st.session_state.wet_context

        if hasattr(st.session_state, "organisatie"):
            context["organisatie"] = st.session_state.organisatie

        if hasattr(st.session_state, "juridische_context"):
            context["juridische_context"] = st.session_state.juridische_context

        if hasattr(st.session_state, "organisatorische_context"):
            context["organisatorische_context"] = (
                st.session_state.organisatorische_context
            )

        if hasattr(st.session_state, "extra_instructies"):
            context["extra_instructies"] = st.session_state.extra_instructies

        logger.debug(f"Retrieved context from session state: {list(context.keys())}")
        return context

    def sync_to_context_manager(self) -> None:
        """
        Sync session state context to ContextManager.

        This ensures the centralized manager has the latest context
        from the UI session state.
        """
        context = self.get_from_session_state()
        if context:
            self.context_manager.set_context(
                context_data=context,
                source=ContextSource.UI,  # Session state comes from UI
                actor="ui",
            )
            logger.info("Synced session state to ContextManager")

    def get_merged_context(
        self, additional_context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Get merged context from all sources.

        Args:
            additional_context: Optional additional context to merge

        Returns:
            Merged context dictionary
        """
        # Start with ContextManager context (if any)
        merged: dict[str, Any] = {}
        current = self.context_manager.get_context()
        if current is not None:
            merged.update(current.to_dict())

        # Add session state context (may override)
        session_context = self.get_from_session_state()
        if session_context:
            merged.update(session_context)

        # Add any additional context (highest priority)
        if additional_context:
            merged.update(additional_context)

        return merged

    # Backward-compatible helper names used by UI code
    def set_in_session_state(
        self,
        context_data: dict[str, Any],
        source: ContextSource = ContextSource.UI,
        actor: str = "ui",
    ) -> None:
        """Store provided context in the central manager.

        This mirrors the previous pattern of updating st.session_state but
        now routes through ContextManager for a single source of truth.
        """
        try:
            self.context_manager.set_context(
                context_data=context_data, source=source, actor=actor
            )
        except Exception as exc:
            logger.error(f"Failed to set context in manager: {exc}")

    def validate(self) -> tuple[bool, list[str]]:
        """Lightweight validation hook for UI.

        Returns (is_valid, messages). Uses ContextManager semantics: if current
        context can be retrieved, consider it valid. UI-specific validation
        remains in the component.
        """
        try:
            current = self.context_manager.get_context()
            _ = current.to_dict() if current is not None else {}
            return True, []
        except Exception as exc:
            logger.warning(f"Context validation failed: {exc}")
            return False, [str(exc)]

    def prepare_generation_request(self, begrip: str, **kwargs) -> dict[str, Any]:
        """
        Prepare a generation request with context.

        Args:
            begrip: The term to generate definition for
            **kwargs: Additional parameters

        Returns:
            Complete request dictionary with context
        """
        # Get merged context
        context = self.get_merged_context(kwargs.get("context"))

        # Build request
        request = {
            "begrip": begrip,
            "context": context.get("wet_context", ""),
            "organisatie": context.get("organisatie", ""),
            "juridische_context": context.get("juridische_context", []),
            "organisatorische_context": context.get("organisatorische_context", []),
            "extra_instructies": context.get("extra_instructies", ""),
        }

        # Add any additional kwargs
        request.update(kwargs)

        logger.debug(f"Prepared generation request for '{begrip}'")
        return request


# Singleton instance for easy access
_adapter_instance = None


def get_context_adapter() -> ContextAdapter:
    """Get or create the singleton ContextAdapter instance."""
    global _adapter_instance
    if _adapter_instance is None:
        _adapter_instance = ContextAdapter()
    return _adapter_instance
