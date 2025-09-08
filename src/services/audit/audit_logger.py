"""
Minimal audit logger stubs to support compliance tests.
These are no-ops by default and can be patched in tests.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class AuditEvent:
    timestamp: str
    user_id: str | None
    action: str
    context_data: dict[str, Any]
    result: dict[str, Any] | None = None
    session_id: str | None = None


class AuditLogger:
    def __init__(self) -> None:
        pass

    def log(self, event: AuditEvent) -> None:  # pragma: no cover - stub
        return None


def log_event(event: dict[str, Any]) -> None:  # pragma: no cover - stub
    """Module-level helper to log a simple audit event (no-op)."""
    _ = event
