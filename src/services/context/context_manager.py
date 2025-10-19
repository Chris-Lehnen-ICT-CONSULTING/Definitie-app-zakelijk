"""
Context Manager Service - Unified context handling for EPIC-010.

This service provides a single, centralized path for all context operations,
replacing multiple legacy routes and direct session state access patterns.

Key features:
- Single source of truth for context data
- Full audit trail for compliance
- Validation at entry point
- Thread-safe operations
- Performance optimized (<100ms processing)
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from threading import Lock
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


class ContextSource(Enum):
    """Source of context modifications for audit trail."""

    UI = "ui"  # User interface input
    API = "api"  # API call
    SYSTEM = "system"  # System generated
    IMPORT = "import"  # Imported from external source
    DEFAULT = "default"  # Default values


@dataclass
class ContextAuditEntry:
    """Audit trail entry for context modifications."""

    timestamp: datetime
    operation: str  # set, update, clear, validate
    source: ContextSource
    actor: str  # User or system identifier
    previous_value: dict[str, Any] | None
    new_value: dict[str, Any]
    correlation_id: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextData:
    """
    Validated context data structure.

    This is the single source of truth for context structure,
    replacing multiple definitions across the codebase.
    """

    organisatorische_context: list[str] = field(default_factory=list)
    juridische_context: list[str] = field(default_factory=list)
    wettelijke_basis: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "organisatorische_context": self.organisatorische_context,
            "juridische_context": self.juridische_context,
            "wettelijke_basis": self.wettelijke_basis,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ContextData":
        """Create from dictionary representation."""
        return cls(
            organisatorische_context=data.get("organisatorische_context", []),
            juridische_context=data.get("juridische_context", []),
            wettelijke_basis=data.get("wettelijke_basis", []),
            metadata=data.get("metadata", {}),
        )


class ContextManager:
    """
    Centralized context management service.

    This service is the ONLY way to access or modify context data,
    ensuring consistency, validation, and audit trail compliance.
    """

    def __init__(self):
        """Initialize the context manager."""
        self._context: ContextData | None = None
        self._audit_trail: list[ContextAuditEntry] = []
        self._lock = Lock()  # Thread safety
        self._correlation_id: str | None = None
        self._cache_timestamp: float | None = None
        self._cache_ttl = 300  # 5 minutes cache TTL

        logger.info("ContextManager initialized")

    def set_context(
        self,
        context_data: dict[str, Any],
        source: ContextSource = ContextSource.UI,
        actor: str = "system",
        correlation_id: str | None = None,
    ) -> ContextData:
        """
        Set context data with validation and audit trail.

        Args:
            context_data: Raw context data to set
            source: Source of the context modification
            actor: User or system making the change
            correlation_id: Optional correlation ID for tracking

        Returns:
            Validated and stored ContextData

        Raises:
            ValueError: If context data is invalid
        """
        start_time = time.perf_counter()

        with self._lock:
            # Validate input
            validated_data = self._validate_context(context_data)

            # Store previous value for audit
            previous_value = self._context.to_dict() if self._context else None

            # Create new context
            self._context = ContextData.from_dict(validated_data)
            self._cache_timestamp = time.perf_counter()
            self._correlation_id = correlation_id or str(uuid4())

            # Record audit entry
            audit_entry = ContextAuditEntry(
                timestamp=datetime.now(),
                operation="set",
                source=source,
                actor=actor,
                previous_value=previous_value,
                new_value=self._context.to_dict(),
                correlation_id=self._correlation_id,
                metadata={
                    "processing_time_ms": (time.perf_counter() - start_time) * 1000
                },
            )
            self._audit_trail.append(audit_entry)

            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.debug(
                f"Context set in {elapsed_ms:.1f}ms by {actor} from {source.value}"
            )

            return self._context

    def get_context(self) -> ContextData | None:
        """
        Get current context data.

        Returns:
            Current ContextData or None if not set
        """
        with self._lock:
            if self._context and self._cache_timestamp:
                cache_age = time.perf_counter() - self._cache_timestamp
                if cache_age > self._cache_ttl:
                    logger.debug(f"Context cache expired (age: {cache_age:.1f}s)")
                    # Don't clear, just log - let consumer decide

            return self._context

    def update_context(
        self,
        updates: dict[str, Any],
        source: ContextSource = ContextSource.UI,
        actor: str = "system",
    ) -> ContextData:
        """
        Update specific context fields.

        Args:
            updates: Fields to update
            source: Source of the update
            actor: User or system making the change

        Returns:
            Updated ContextData
        """
        with self._lock:
            if not self._context:
                # If no context exists, create new one
                return self.set_context(updates, source, actor)

            # Get current data
            current_data = self._context.to_dict()

            # Apply updates
            for key, value in updates.items():
                if key in [
                    "organisatorische_context",
                    "juridische_context",
                    "wettelijke_basis",
                ]:
                    current_data[key] = value
                elif key == "metadata":
                    current_data["metadata"].update(value)

            # Set updated context
            return self.set_context(current_data, source, actor, self._correlation_id)

    def clear_context(
        self, source: ContextSource = ContextSource.SYSTEM, actor: str = "system"
    ) -> None:
        """
        Clear all context data.

        Args:
            source: Source of the clear operation
            actor: User or system clearing the context
        """
        with self._lock:
            previous_value = self._context.to_dict() if self._context else None

            self._context = None
            self._cache_timestamp = None
            self._correlation_id = None

            # Record audit entry
            if previous_value:
                audit_entry = ContextAuditEntry(
                    timestamp=datetime.now(),
                    operation="clear",
                    source=source,
                    actor=actor,
                    previous_value=previous_value,
                    new_value={},
                    correlation_id=str(uuid4()),
                    metadata={},
                )
                self._audit_trail.append(audit_entry)

            logger.debug(f"Context cleared by {actor}")

    def get_audit_trail(
        self, limit: int | None = None, correlation_id: str | None = None
    ) -> list[ContextAuditEntry]:
        """
        Get audit trail entries.

        Args:
            limit: Maximum number of entries to return
            correlation_id: Filter by correlation ID

        Returns:
            List of audit trail entries
        """
        with self._lock:
            entries = self._audit_trail.copy()

            if correlation_id:
                entries = [e for e in entries if e.correlation_id == correlation_id]

            if limit:
                entries = entries[-limit:]

            return entries

    def _validate_context(self, context_data: dict[str, Any]) -> dict[str, Any]:
        """
        Validate context data structure and values.

        Args:
            context_data: Raw context data to validate

        Returns:
            Validated context data

        Raises:
            ValueError: If validation fails
        """
        validated = {}

        # Validate list fields
        list_fields = [
            "organisatorische_context",
            "juridische_context",
            "wettelijke_basis",
        ]
        for field in list_fields:
            value = context_data.get(field, [])

            # Ensure it's a list
            if value is None:
                validated[field] = []
            elif isinstance(value, list):
                # Validate each item is a string
                validated[field] = [
                    str(item)
                    for item in value
                    if item is not None and str(item).strip()
                ]
            elif isinstance(value, str):
                # Convert single string to list
                validated[field] = [value] if value.strip() else []
            else:
                msg = f"Invalid type for {field}: expected list or string, got {type(value)}"
                raise ValueError(
                    msg
                )

        # Validate metadata
        metadata = context_data.get("metadata", {})
        if not isinstance(metadata, dict):
            msg = f"Invalid metadata type: expected dict, got {type(metadata)}"
            raise ValueError(
                msg
            )
        validated["metadata"] = metadata

        return validated

    def get_correlation_id(self) -> str | None:
        """Get current correlation ID for tracking."""
        with self._lock:
            return self._correlation_id

    def to_generation_request_fields(self) -> dict[str, Any]:
        """
        Convert context to GenerationRequest compatible fields.

        This method provides backward compatibility with existing interfaces.

        Returns:
            Dictionary with GenerationRequest context fields
        """
        if not self._context:
            return {
                "organisatorische_context": [],
                "juridische_context": [],
                "wettelijke_basis": [],
            }

        return {
            "organisatorische_context": self._context.organisatorische_context,
            "juridische_context": self._context.juridische_context,
            "wettelijke_basis": self._context.wettelijke_basis,
        }


# Global singleton instance
_context_manager_instance: ContextManager | None = None
_instance_lock = Lock()


def get_context_manager() -> ContextManager:
    """
    Get the global ContextManager instance.

    Returns:
        Singleton ContextManager instance
    """
    global _context_manager_instance

    if _context_manager_instance is None:
        with _instance_lock:
            if _context_manager_instance is None:
                _context_manager_instance = ContextManager()

    return _context_manager_instance
