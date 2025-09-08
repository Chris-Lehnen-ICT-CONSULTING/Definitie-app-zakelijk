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
        context_data = self.context_manager.get_context()

        if context_data:
            return context_data.to_dict()

        # Fallback: migrate from session state if it exists (one-time migration)
        migrated = False
        context_dict = {
            "organisatorische_context": [],
            "juridische_context": [],
            "wettelijke_basis": [],
        }

        # Check for legacy session state values
        if hasattr(st, "session_state"):
            legacy_fields = [
                "organisatorische_context",
                "juridische_context",
                "wettelijke_basis",
            ]

            for field in legacy_fields:
                if field in st.session_state:
                    value = st.session_state[field]
                    if value:
                        context_dict[field] = (
                            value if isinstance(value, list) else [value]
                        )
                        migrated = True
                        logger.warning(f"Migrating legacy session state field: {field}")

        # If we migrated data, store it in ContextManager
        if migrated:
            self.context_manager.set_context(
                context_dict, source=ContextSource.IMPORT, actor="migration"
            )

            # Clean up session state to prevent future direct access
            for field in legacy_fields:
                if field in st.session_state:
                    del st.session_state[field]

        return context_dict

    def set_in_session_state(
        self,
        context_data: dict[str, Any],
        source: ContextSource = ContextSource.UI,
        actor: str = "user",
    ) -> None:
        """
        Set context (legacy compatibility).

        Routes the operation through ContextManager while maintaining
        compatibility with code that expects to write to session state.

        Args:
            context_data: Context data to set
            source: Source of the context change
            actor: User or system making the change
        """
        # Route through ContextManager
        self.context_manager.set_context(context_data, source, actor)

        # DO NOT write to session state - break the legacy pattern
        # This ensures all future reads go through ContextManager
        logger.debug("Context set through adapter (session state bypassed)")

    def update_field(
        self,
        field_name: str,
        value: Any,
        source: ContextSource = ContextSource.UI,
        actor: str = "user",
    ) -> None:
        """
        Update a specific context field.

        Args:
            field_name: Name of the field to update
            value: New value for the field
            source: Source of the update
            actor: User or system making the change
        """
        updates = {field_name: value}
        self.context_manager.update_context(updates, source, actor)
        logger.debug(f"Context field '{field_name}' updated through adapter")

    def clear(
        self, source: ContextSource = ContextSource.SYSTEM, actor: str = "system"
    ) -> None:
        """
        Clear all context data.

        Args:
            source: Source of the clear operation
            actor: User or system clearing the context
        """
        self.context_manager.clear_context(source, actor)

        # Also clean up any legacy session state
        if hasattr(st, "session_state"):
            legacy_fields = [
                "organisatorische_context",
                "juridische_context",
                "wettelijke_basis",
            ]
            for field in legacy_fields:
                if field in st.session_state:
                    del st.session_state[field]

        logger.debug("Context cleared through adapter")

    def to_generation_request(self) -> dict[str, Any]:
        """
        Convert current context to GenerationRequest format.

        Returns:
            Dictionary with fields compatible with GenerationRequest
        """
        return self.context_manager.to_generation_request_fields()

    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate current context.

        Returns:
            Tuple of (is_valid, list_of_error_messages)
        """
        from services.validation.context_validator import ContextValidator

        validator = ContextValidator()
        context_data = self.context_manager.get_context()

        if not context_data:
            return True, []  # Empty context is valid

        errors = validator.validate_detailed(context_data.to_dict())

        # Filter to only actual errors (not warnings or info)
        error_messages = [e.message for e in errors if e.severity == "error"]

        return len(error_messages) == 0, error_messages

    @staticmethod
    def migrate_legacy_code(file_path: str) -> str:
        """
        Helper to generate migration suggestions for legacy code.

        Args:
            file_path: Path to file with legacy code

        Returns:
            Migration suggestions as string
        """
        suggestions = []

        legacy_patterns = {
            "st.session_state.organisatorische_context": "adapter.get_from_session_state()['organisatorische_context']",
            "st.session_state['juridische_context']": "adapter.get_from_session_state()['juridische_context']",
            "session_state.get('wettelijke_basis')": "adapter.get_from_session_state().get('wettelijke_basis', [])",
            "st.session_state.organisatorische_context =": "adapter.update_field('organisatorische_context',",
            "st.session_state['juridische_context'] =": "adapter.update_field('juridische_context',",
        }

        suggestions.append(f"Migration suggestions for {file_path}:")
        suggestions.append("=" * 50)
        suggestions.append(
            "Add import: from services.context.context_adapter import ContextAdapter"
        )
        suggestions.append("Initialize: adapter = ContextAdapter()")
        suggestions.append("")
        suggestions.append("Replace patterns:")

        for old, new in legacy_patterns.items():
            suggestions.append(f"  OLD: {old}")
            suggestions.append(f"  NEW: {new}")
            suggestions.append("")

        return "\n".join(suggestions)


# Singleton adapter instance for UI components
_adapter_instance: ContextAdapter | None = None


def get_context_adapter() -> ContextAdapter:
    """
    Get the global ContextAdapter instance.

    Returns:
        Singleton ContextAdapter instance
    """
    global _adapter_instance

    if _adapter_instance is None:
        _adapter_instance = ContextAdapter()

    return _adapter_instance
