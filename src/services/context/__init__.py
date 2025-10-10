"""
Context Management Module - Unified context handling for EPIC-010.

This module provides centralized context management, replacing
multiple legacy routes and direct session state access patterns.

Key components:
- ContextManager: Central service for all context operations
- ContextAdapter: Bridge for UI components
- ContextValidator: Validation service

Usage:
    from services.context import get_context_manager, get_context_adapter

    # For services
    manager = get_context_manager()
    context = manager.get_context()

    # For UI components
    adapter = get_context_adapter()
    context_dict = adapter.get_from_session_state()
"""

from services.context.context_adapter import (ServiceContextAdapter,
                                              get_service_context_adapter)
from services.context.context_manager import (ContextAuditEntry, ContextData,
                                              ContextManager, ContextSource,
                                              get_context_manager)

__all__ = [
    # Manager
    "ContextManager",
    "get_context_manager",
    "ContextData",
    "ContextSource",
    "ContextAuditEntry",
    # Service Adapter (framework-neutral)
    "ServiceContextAdapter",
    "get_service_context_adapter",
]
