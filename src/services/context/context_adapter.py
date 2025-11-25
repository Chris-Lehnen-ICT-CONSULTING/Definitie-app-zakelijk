"""
Context Adapter Service - Framework-neutral context management.

This service provides context management without any UI framework dependencies.
For Streamlit integration, use ui/helpers/context_adapter.py instead.
"""

import logging
from typing import Any, cast

from services.context.context_manager import (
    ContextManager,
    ContextSource,
    get_context_manager,
)

logger = logging.getLogger(__name__)


class ServiceContextAdapter:
    """
    Framework-neutral adapter for context management in services.

    This adapter handles context without any UI dependencies.
    UI layers should use their own adapters to bridge with this service.
    """

    def __init__(self, context_manager: ContextManager | None = None):
        """
        Initialize the adapter.

        Args:
            context_manager: Optional ContextManager instance, uses singleton if not provided
        """
        self.context_manager = context_manager or get_context_manager()
        logger.info("ServiceContextAdapter initialized")

    def get_context(self, key: str | None = None) -> dict[str, Any]:
        """
        Get context from the manager.

        Args:
            key: Optional specific context key to retrieve

        Returns:
            Context dictionary
        """
        if key:
            return self.context_manager.get_context(key) or {}
        return self.context_manager.get_current_context() or {}

    def set_context(
        self,
        key: str,
        value: dict[str, Any],
        source: ContextSource = ContextSource.SYSTEM,
    ) -> None:
        """
        Set context in the manager.

        Args:
            key: Context key
            value: Context value
            source: Source of the context
        """
        self.context_manager.set_context(key, value, source)
        logger.debug(f"Set context for key '{key}' from {source.value}")

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
        # Start with ContextManager's merged context
        merged = self.context_manager.get_merged_context()

        # Add any additional context (highest priority)
        if additional_context:
            merged.update(additional_context)

        return cast("dict[str, Any]", merged)

    def prepare_generation_request(
        self, begrip: str, context_data: dict[str, Any] | None = None, **kwargs
    ) -> dict[str, Any]:
        """
        Prepare a generation request with context.

        Args:
            begrip: The term to generate definition for
            context_data: Optional context data dictionary
            **kwargs: Additional parameters

        Returns:
            Complete request dictionary with context
        """
        # Get merged context
        context = self.get_merged_context(context_data)

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


def get_service_context_adapter() -> ServiceContextAdapter:
    """Get or create the singleton ServiceContextAdapter instance."""
    global _adapter_instance
    if _adapter_instance is None:
        _adapter_instance = ServiceContextAdapter()
    return _adapter_instance
