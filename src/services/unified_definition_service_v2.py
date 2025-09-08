"""
Legacy compatibility stub for UnifiedDefinitionService.

This module exists to allow tests to patch UnifiedDefinitionService while the
new architecture uses ServiceAdapter via get_definition_service().
"""

from typing import Any


class UnifiedDefinitionService:  # pragma: no cover - stub for tests
    _instance = None

    @classmethod
    def get_instance(cls, *args: Any, **kwargs: Any):
        if cls._instance is None:
            cls._instance = object()
        return cls._instance
