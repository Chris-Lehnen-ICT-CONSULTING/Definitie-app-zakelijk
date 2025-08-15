"""
Definition processing service for DefinitieAgent.
DEPRECATED: This is now a thin wrapper around UnifiedDefinitionService for backward compatibility.
New code should use UnifiedDefinitionService directly.
"""

import logging
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

# Import the new unified service
from services.unified_definition_service import (
    ArchitectureMode,
    ProcessingMode,
    UnifiedDefinitionService,
    UnifiedServiceConfig,
)
from utils.exceptions import (
    APIError,
    ValidationError,
    handle_api_error,
    handle_validation_error,
)

# Voeg root directory toe aan Python path voor logs module toegang
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


class DefinitionService:
    """
    DEPRECATED: Legacy wrapper around UnifiedDefinitionService.

    This class provides backward compatibility for existing code.
    New code should use UnifiedDefinitionService directly.

    Deze service laag beheert de complete workflow voor definitie generatie,
    validatie en aanvullende content generatie.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Create unified service instance configured for legacy sync mode
        self._unified_service = UnifiedDefinitionService()
        self._unified_service.configure(
            UnifiedServiceConfig(
                processing_mode=ProcessingMode.SYNC,
                architecture_mode=ArchitectureMode.LEGACY,
            )
        )

    @handle_api_error
    def generate_definition(
        self, begrip: str, context_dict: Dict[str, List[str]]
    ) -> Tuple[str, str, str]:
        """
        Genereer definitie met behulp van AI.

        Args:
            begrip: Te definiëren begrip
            context_dict: Context informatie voor generatie

        Returns:
            Tuple van (originele_definitie, opgeschoonde_definitie, marker)

        Raises:
            APIError: Als AI generatie mislukt
        """
        if not begrip.strip():
            raise ValidationError("Begrip mag niet leeg zijn")

        try:
            # Delegate to unified service
            result = self._unified_service.generate_definition(
                begrip, context_dict, force_sync=True
            )

            if not result.success:
                raise APIError(f"Definitie generatie mislukt: {result.error_message}")

            return (
                result.definitie_origineel,
                result.definitie_gecorrigeerd,
                result.marker,
            )

        except Exception as e:
            self.logger.error(f"Definition generation failed: {str(e)}")
            raise APIError(f"Definitie generatie mislukt: {str(e)}")

    @handle_api_error
    def generate_sources(self, begrip: str, context_dict: Dict[str, List[str]]) -> str:
        """
        Genereer broninformatie met behulp van AI.

        Args:
            begrip: Begrip waarvoor bronnen gezocht worden
            context_dict: Context informatie voor bronnen

        Returns:
            Bronnen tekst met relevante wetgeving en richtlijnen

        Raises:
            APIError: Als bronnen generatie mislukt
        """
        try:
            # Delegate to unified service
            bronnen_data = self._unified_service._lookup_sources_sync(
                begrip, context_dict
            )
            return bronnen_data.get("bronnen_tekst", "")

        except Exception as e:
            self.logger.error(f"Sources generation failed: {str(e)}")
            raise APIError(f"Bronnen generatie mislukt: {str(e)}")

    @handle_validation_error
    def validate_definition(
        self,
        definitie: str,
        toetsregels: Dict[str, Any],
        begrip: str,
        marker: str = "",
        voorkeursterm: str = "",
        bronnen_gebruikt: Optional[str] = None,
        contexten: Optional[Dict[str, List[str]]] = None,
        gebruik_logging: bool = False,
    ) -> List[str]:
        """
        Valideer definitie tegen kwaliteitsregels.

        Args:
            definitie: Te valideren definitie tekst
            toetsregels: Kwaliteitsregels voor validatie
            begrip: Oorspronkelijk begrip
            marker: Ontologische categorie marker
            voorkeursterm: Voorkeursterm voor het begrip
            bronnen_gebruikt: Gebruikte bronnen
            contexten: Context informatie
            gebruik_logging: Of gedetailleerde logging gebruikt wordt

        Returns:
            Lijst met validatie resultaten en feedback

        Raises:
            ValidationError: Als validatie mislukt
        """
        try:
            # Delegate to unified service
            toetsresultaten, _ = self._unified_service._validate_definition_sync(
                definitie, begrip, contexten or {}
            )
            return toetsresultaten

        except Exception as e:
            self.logger.error(f"Definitie validatie mislukt: {str(e)}")
            raise ValidationError(f"Definitie validatie mislukt: {str(e)}")

    @handle_api_error
    def generate_examples(
        self, begrip: str, definitie: str, context_dict: Dict[str, List[str]]
    ) -> Dict[str, List[str]]:
        """
        Genereer voorbeeldzinnen en praktijkcases.

        Args:
            begrip: Begrip waarvoor voorbeelden gegenereerd worden
            definitie: Definitie tekst als basis
            context_dict: Context informatie voor voorbeelden

        Returns:
            Dictionary met verschillende soorten voorbeelden

        Raises:
            APIError: Als voorbeelden generatie mislukt
        """
        try:
            # Delegate to unified service - import unified examples
            from voorbeelden.unified_voorbeelden import (
                GenerationMode,
                genereer_alle_voorbeelden,
            )

            voorbeelden = genereer_alle_voorbeelden(
                begrip, definitie, context_dict, mode=GenerationMode.SYNC
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
            self.logger.error(f"Examples generation failed: {str(e)}")
            raise APIError(f"Voorbeelden generatie mislukt: {str(e)}")


# Voor backward compatibility - exporteer ook de key functions
__all__ = ["DefinitionService"]
