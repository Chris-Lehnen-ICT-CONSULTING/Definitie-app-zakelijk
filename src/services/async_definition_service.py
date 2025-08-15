"""
Async definition processing service for DefinitieAgent.
DEPRECATED: This is now a thin wrapper around UnifiedDefinitionService for backward compatibility.
New code should use UnifiedDefinitionService directly.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass

from utils.exceptions import APIError, ValidationError

# Import the new unified service
from services.unified_definition_service import (
    UnifiedDefinitionService,
    UnifiedServiceConfig,
    ProcessingMode,
    ArchitectureMode,
)

import sys
import os

# Voeg root directory toe aan Python path voor logs module toegang
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


@dataclass
class AsyncProcessingResult:
    """Result container for async definition processing."""

    success: bool
    processing_time: float
    definitie_origineel: str = ""
    definitie_gecorrigeerd: str = ""
    marker: str = ""
    bronnen_tekst: str = ""
    toetsresultaten: List[str] = None
    examples: Optional[Any] = None
    additional_content: Optional[Dict[str, str]] = None
    error_message: str = ""
    cache_hits: int = 0
    total_requests: int = 0


class AsyncDefinitionService:
    """
    DEPRECATED: Legacy wrapper around UnifiedDefinitionService.

    This class provides backward compatibility for existing code.
    New code should use UnifiedDefinitionService directly.

    Async service class for definition processing operations.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Create unified service instance configured for legacy async mode
        self._unified_service = UnifiedDefinitionService()
        self._unified_service.configure(
            UnifiedServiceConfig(
                processing_mode=ProcessingMode.ASYNC,
                architecture_mode=ArchitectureMode.LEGACY,
            )
        )

    async def process_definition(
        self,
        begrip: str,
        context_dict: Dict[str, List[str]],
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> AsyncProcessingResult:
        """
        Process definition with async operations and progress tracking.

        Args:
            begrip: Term to define
            context_dict: Context information
            progress_callback: Optional callback for progress updates

        Returns:
            AsyncProcessingResult with all generated content
        """
        if not begrip.strip():
            raise ValidationError("Begrip mag niet leeg zijn")

        try:
            # Update service config with callback
            self._unified_service.config.progress_callback = progress_callback

            # Delegate to unified service
            result = await self._unified_service.agenerate_definition(
                begrip, context_dict
            )

            # Convert to legacy AsyncProcessingResult
            return AsyncProcessingResult(
                success=result.success,
                processing_time=result.processing_time,
                definitie_origineel=result.definitie_origineel,
                definitie_gecorrigeerd=result.definitie_gecorrigeerd,
                marker=result.marker,
                bronnen_tekst=result.bronnen_tekst,
                toetsresultaten=result.toetsresultaten,
                examples=result.voorbeelden,
                error_message=result.error_message,
                cache_hits=result.cache_hits,
                total_requests=result.total_requests,
            )

        except Exception as e:
            self.logger.error(f"Async definition processing failed: {str(e)}")
            return AsyncProcessingResult(
                success=False, processing_time=0.0, error_message=str(e)
            )

    async def async_generate_definition(
        self, begrip: str, context_dict: Dict[str, List[str]]
    ) -> Tuple[str, str, str]:
        """
        Generate definition using async AI calls.

        Args:
            begrip: Term to define
            context_dict: Context information

        Returns:
            Tuple of (original_definition, cleaned_definition, marker)

        Raises:
            APIError: If AI generation fails
        """
        if not begrip.strip():
            raise ValidationError("Begrip mag niet leeg zijn")

        try:
            # Delegate to unified service
            result = await self._unified_service.agenerate_definition(
                begrip, context_dict
            )

            if not result.success:
                raise APIError(f"Definitie generatie mislukt: {result.error_message}")

            return (
                result.definitie_origineel,
                result.definitie_gecorrigeerd,
                result.marker,
            )

        except Exception as e:
            self.logger.error(f"Async definition generation failed: {str(e)}")
            raise APIError(f"Definitie generatie mislukt: {str(e)}")

    async def async_generate_sources(
        self, begrip: str, context_dict: Dict[str, List[str]]
    ) -> str:
        """
        Generate sources information using async AI.

        Args:
            begrip: Term
            context_dict: Context information

        Returns:
            Sources text

        Raises:
            APIError: If sources generation fails
        """
        try:
            # Delegate to unified service
            bronnen_data = await self._unified_service._lookup_sources_async(
                begrip, context_dict
            )
            return bronnen_data.get("bronnen_tekst", "")

        except Exception as e:
            self.logger.error(f"Async sources generation failed: {str(e)}")
            raise APIError(f"Bronnen generatie mislukt: {str(e)}")

    async def async_validate_definition(
        self, definitie: str, begrip: str, context_dict: Dict[str, List[str]]
    ) -> List[str]:
        """
        Validate definition using async operations.

        Args:
            definitie: Definition text to validate
            begrip: Original term
            context_dict: Context information

        Returns:
            List of validation results

        Raises:
            ValidationError: If validation fails
        """
        try:
            # Delegate to unified service
            toetsresultaten, _ = await self._unified_service._validate_definition_async(
                definitie, begrip, context_dict
            )
            return toetsresultaten

        except Exception as e:
            self.logger.error(f"Async definition validation failed: {str(e)}")
            raise ValidationError(f"Definitie validatie mislukt: {str(e)}")

    async def async_generate_examples(
        self, begrip: str, definitie: str, context_dict: Dict[str, List[str]]
    ) -> Dict[str, List[str]]:
        """
        Generate examples using async operations.

        Args:
            begrip: Term
            definitie: Definition text
            context_dict: Context information

        Returns:
            Dictionary with different types of examples

        Raises:
            APIError: If examples generation fails
        """
        try:
            # Delegate to unified service - import unified examples
            from voorbeelden.unified_voorbeelden import genereer_alle_voorbeelden_async

            voorbeelden = await genereer_alle_voorbeelden_async(
                begrip, definitie, context_dict
            )

            # Convert to legacy format
            return {
                "voorbeeld_zinnen": voorbeelden.get("sentence", []),
                "praktijkvoorbeelden": voorbeelden.get("practical", []),
                "tegenvoorbeelden": voorbeelden.get("counter", []),
                "synoniemen": voorbeelden.get("synonyms", []),
                "antoniemen": voorbeelden.get("antonyms", []),
                "toelichting": voorbeelden.get("explanation", []),
            }

        except Exception as e:
            self.logger.error(f"Async examples generation failed: {str(e)}")
            raise APIError(f"Voorbeelden generatie mislukt: {str(e)}")


# Global instance voor gemakkelijke toegang
_async_service_instance = None


def get_async_service() -> AsyncDefinitionService:
    """Get or create global async service instance."""
    global _async_service_instance
    if _async_service_instance is None:
        _async_service_instance = AsyncDefinitionService()
    return _async_service_instance


# Voor backward compatibility - exporteer ook de key functions
__all__ = ["AsyncDefinitionService", "AsyncProcessingResult", "get_async_service"]
