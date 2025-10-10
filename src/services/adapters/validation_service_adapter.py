"""
Adapter to make sync ValidationService work with V2 async interface.

This adapter wraps the synchronous ValidationService to provide the
asynchronous interface expected by DefinitionOrchestratorV2.
"""

from __future__ import annotations

import asyncio
from typing import Any

from services.interfaces import (Definition, ValidationResult,
                                 ValidationServiceInterface)


class ValidationServiceAdapterV1toV2(ValidationServiceInterface):
    """Adapter that wraps sync ValidationService for async V2 interface."""

    def __init__(self, sync_validation_service):
        """
        Initialize adapter with sync validation service.

        Args:
            sync_validation_service: The synchronous validation service to wrap
        """
        self.legacy_validator = sync_validation_service

    async def validate_definition(
        self,
        begrip: str,
        text: str,
        ontologische_categorie: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> ValidationResult:
        """
        Validate definition asynchronously.

        Wraps the sync validator using asyncio.to_thread for proper async execution.
        """
        definition = Definition(
            begrip=begrip, definitie=text, ontologische_categorie=ontologische_categorie
        )
        # Run sync validation in thread to avoid blocking
        return await asyncio.to_thread(self.legacy_validator.validate, definition)

    async def batch_validate(
        self, definitions: list[tuple[str, str]]
    ) -> list[ValidationResult]:
        """
        Validate multiple definitions in batch.

        Processes each definition sequentially using the async validate_definition.
        """
        results = []
        for begrip, text in definitions:
            result = await self.validate_definition(begrip, text)
            results.append(result)
        return results
