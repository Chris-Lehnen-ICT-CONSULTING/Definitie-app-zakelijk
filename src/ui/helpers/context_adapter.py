"""
Context Adapter - Bridge between UI components and ContextManager.

This adapter provides backward compatibility for existing UI components
while routing all context operations through the centralized ContextManager.
"""

import logging
from typing import Any

from services.context.context_manager import (
    ContextManager,
    ContextSource,
    get_context_manager,
)

# NOTE: SessionStateManager import moved to method to break circular dependency
# See DEF-86: Circular import deadlock fix

logger = logging.getLogger(__name__)

# DEF-484: key waaronder de per-sessie gevalideerde context in SessionStateManager
# (= st.session_state, per Streamlit-sessie geïsoleerd) wordt bewaard.
_CONTEXT_STATE_KEY = "context_data"


class ContextAdapter:
    """
    Adapter tussen UI-componenten en de context-opslag.

    DEF-484: context wordt PER-SESSIE bewaard via ``SessionStateManager``
    (st.session_state is per Streamlit-sessie geïsoleerd), niet in de
    proces-globale ``ContextManager``-singleton (die lekte tussen sessies).
    ``ContextManager`` wordt hier alleen nog gebruikt voor stateless validatie.
    """

    def __init__(self, context_manager: ContextManager | None = None):
        """
        Initialize the adapter.

        Args:
            context_manager: Optionele ContextManager (alleen voor validatie);
                gebruikt de singleton als niet opgegeven.
        """
        self.context_manager = context_manager or get_context_manager()
        logger.info("ContextAdapter initialized")

    def get_from_session_state(self) -> dict[str, Any]:
        """
        Haal de per-sessie context op uit SessionStateManager.

        DEF-484: leest de per-sessie opgeslagen (gevalideerde) context; valt terug
        op losse context-velden voor backward compatibility. Leest NIET meer de
        proces-globale ContextManager._context (dat lekte tussen sessies).

        Returns:
            Context dictionary compatible with legacy code
        """
        # Late import to break circular dependency (DEF-86)
        from ui.session_state import SessionStateManager

        # Per-sessie opgeslagen, gevalideerde context heeft voorrang.
        stored = SessionStateManager.get_value(_CONTEXT_STATE_KEY)
        if stored:
            return dict(stored)

        # Fallback: losse context-velden uit session state (backward compatibility).
        context: dict[str, Any] = {}
        for key in (
            "begrip",
            "wet_context",
            "organisatie",
            "juridische_context",
            "organisatorische_context",
            "extra_instructies",
        ):
            value = SessionStateManager.get_value(key)
            if value is not None:
                context[key] = value

        logger.debug(f"Retrieved context from session state: {list(context.keys())}")
        return context

    def sync_to_context_manager(self) -> None:
        """
        Persisteer de huidige context per-sessie.

        DEF-484: naam behouden voor backward compatibility, maar bewaart nu
        per-sessie via SessionStateManager i.p.v. in de proces-globale singleton.
        """
        context = self.get_from_session_state()
        if context:
            self.set_in_session_state(
                context_data=context, source=ContextSource.UI, actor="ui"
            )
            logger.info("Synced session context")

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
        # DEF-484: start met de per-sessie context (geen proces-globale _context).
        merged: dict[str, Any] = {}
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
    ) -> bool:
        """Bewaar de opgegeven context per-sessie.

        DEF-484: valideert via de stateless ``ContextManager.validate_context`` en
        bewaart het resultaat per-sessie via ``SessionStateManager`` (niet in de
        proces-globale singleton). ``source``/``actor`` blijven in de signatuur
        voor backward compatibility.

        Returns:
            True if context was set successfully, False otherwise.
        """
        from ui.session_state import SessionStateManager

        try:
            validated = self.context_manager.validate_context(context_data)
            SessionStateManager.set_value(_CONTEXT_STATE_KEY, validated)
            return True
        except (AttributeError, KeyError, TypeError, ValueError) as exc:
            # DEF-252: Narrow exception types and structured logging
            logger.error(
                f"Failed to set context in session: {type(exc).__name__}: {exc}",
                extra={"event": "context_set_error", "error_type": type(exc).__name__},
            )
            return False

    def validate(self) -> tuple[bool, list[str]]:
        """Lightweight validation hook for UI.

        Returns (is_valid, messages). DEF-484: valideert de per-sessie context
        stateless via ContextManager.validate_context.
        """
        try:
            self.context_manager.validate_context(self.get_from_session_state())
            return True, []
        except (AttributeError, KeyError, TypeError, ValueError) as exc:
            # DEF-252: Narrow exception types and structured logging
            logger.warning(
                f"Context validation failed: {type(exc).__name__}: {exc}",
                extra={
                    "event": "context_validation_error",
                    "error_type": type(exc).__name__,
                },
            )
            return False, [str(exc)]

    def prepare_generation_request(self, begrip: str, **kwargs: Any) -> dict[str, Any]:
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
