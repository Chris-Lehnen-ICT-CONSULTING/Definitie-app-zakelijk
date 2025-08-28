"""
Adapter to make sync CleaningService work with V2 async interface.

This adapter wraps the synchronous CleaningService to provide the
asynchronous interface expected by DefinitionOrchestratorV2.
"""

from __future__ import annotations

import asyncio
from typing import Any

from services.interfaces import CleaningServiceInterface, CleaningResult, Definition


class CleaningServiceAdapterV1toV2(CleaningServiceInterface):
    """Adapter that wraps sync CleaningService for async V2 interface."""
    
    def __init__(self, sync_cleaning_service):
        """
        Initialize adapter with sync cleaning service.
        
        Args:
            sync_cleaning_service: The synchronous cleaning service to wrap
        """
        self._svc = sync_cleaning_service
    
    async def clean_text(self, text: str, term: str) -> CleaningResult:
        """
        Clean definition text asynchronously.
        
        Wraps the sync method using asyncio.to_thread for proper async execution.
        """
        return await asyncio.to_thread(self._svc.clean_text, text, term)
    
    async def clean_definition(self, definition: Definition) -> CleaningResult:
        """
        Clean a full definition object asynchronously.
        
        Wraps the sync method using asyncio.to_thread for proper async execution.
        """
        return await asyncio.to_thread(self._svc.clean_definition, definition)
    
    def validate_cleaning_rules(self) -> bool:
        """
        Validate cleaning rules (remains synchronous).
        
        This method doesn't need async as it's a simple validation check.
        """
        return self._svc.validate_cleaning_rules()