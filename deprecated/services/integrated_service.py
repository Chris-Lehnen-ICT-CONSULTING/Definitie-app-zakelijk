"""
Geïntegreerde Service Laag - Uniform interface voor alle definitie verwerkingsdiensten.

DEPRECATED: This module is now superseded by UnifiedDefinitionService.
This file is maintained for backward compatibility only.
New code should use UnifiedDefinitionService directly.

Verbindt legacy en moderne architecturen met een consistente API.
Biedt centrale toegang tot alle definitie generatie en validatie functionaliteiten.
"""

import logging  # Logging faciliteiten voor debug en monitoring
from dataclasses import dataclass, field  # Dataklassen voor gestructureerde data
from enum import Enum  # Enumeraties voor constante waarden
from typing import Any, Dict, List, Optional  # Type hints voor betere code documentatie

# Import the new unified service
from services.unified_definition_service import (
    ArchitectureMode,
    ProcessingMode,
    UnifiedDefinitionService,
    UnifiedResult,
    UnifiedServiceConfig,
)

logger = logging.getLogger(__name__)  # Logger instantie voor deze module


class ServiceMode(Enum):
    """Service operatie modi voor verschillende architectuur integraties."""

    LEGACY = "legacy"  # Gebruik alleen legacy systeem componenten
    MODERN = "modern"  # Gebruik alleen moderne modulaire componenten
    HYBRID = "hybrid"  # Combineer legacy en moderne componenten
    AUTO = "auto"  # Automatisch kiezen op basis van beschikbaarheid


@dataclass
class ServiceConfig:
    """Configuratie voor geïntegreerde service met standaard instellingen."""

    mode: ServiceMode = ServiceMode.AUTO  # Service modus (auto-detectie standaard)
    enable_caching: bool = True  # Cache resultaten voor snellere responses
    enable_monitoring: bool = True  # Monitor API gebruik en prestaties
    enable_web_lookup: bool = True  # Zoek in externe web bronnen
    enable_validation: bool = True  # Valideer gegenereerde definities
    default_timeout: float = 30.0  # Standaard timeout in seconden
    max_retries: int = 3  # Maximum aantal herhaalpogingen bij fouten
    parallel_processing: bool = True


@dataclass
class IntegratedResult:
    """Unified result container for all service operations."""

    success: bool
    operation: str
    processing_time: float
    service_mode: ServiceMode

    # Core definition data
    definitie_record: Optional[Any] = None
    validation_result: Optional[Any] = None

    # Legacy compatibility
    definitie_origineel: str = ""
    definitie_gecorrigeerd: str = ""
    marker: str = ""
    toetsresultaten: List[str] = field(default_factory=list)

    # Extended data
    bronnen: List[Any] = field(default_factory=list)
    web_lookup_results: Dict[str, Any] = field(default_factory=dict)
    duplicate_analysis: Dict[str, Any] = field(default_factory=dict)
    examples: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Performance metrics
    cache_hits: int = 0
    total_requests: int = 0
    error_message: str = ""
    warnings: List[str] = field(default_factory=list)


class IntegratedService:
    """
    DEPRECATED: Legacy wrapper around UnifiedDefinitionService.

    This class provides backward compatibility for existing code.
    New code should use UnifiedDefinitionService directly.

    Geïntegreerde service voor alle definitie verwerkingsdiensten.
    """

    def __init__(self, config: Optional[ServiceConfig] = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or ServiceConfig()

        # Create unified service instance
        self._unified_service = UnifiedDefinitionService()

        # Map legacy config to unified config
        unified_config = self._map_config_to_unified(self.config)
        self._unified_service.configure(unified_config)

    def _map_config_to_unified(self, config: ServiceConfig) -> UnifiedServiceConfig:
        """Map legacy ServiceConfig to UnifiedServiceConfig."""
        # Map ServiceMode to ArchitectureMode
        architecture_mode_map = {
            ServiceMode.LEGACY: ArchitectureMode.LEGACY,
            ServiceMode.MODERN: ArchitectureMode.AUTO,
            ServiceMode.HYBRID: ArchitectureMode.AUTO,
            ServiceMode.AUTO: ArchitectureMode.AUTO,
        }

        return UnifiedServiceConfig(
            processing_mode=ProcessingMode.AUTO,
            architecture_mode=architecture_mode_map[config.mode],
            enable_caching=config.enable_caching,
            enable_monitoring=config.enable_monitoring,
            enable_web_lookup=config.enable_web_lookup,
            enable_validation=config.enable_validation,
            default_timeout=config.default_timeout,
            max_retries=config.max_retries,
            parallel_processing=config.parallel_processing,
        )

    def _map_unified_to_integrated_result(
        self, result: UnifiedResult, operation: str
    ) -> IntegratedResult:
        """Map UnifiedResult to IntegratedResult for backward compatibility."""
        return IntegratedResult(
            success=result.success,
            operation=operation,
            processing_time=result.processing_time,
            service_mode=ServiceMode.AUTO,  # Default mapping
            definitie_origineel=result.definitie_origineel,
            definitie_gecorrigeerd=result.definitie_gecorrigeerd,
            marker=result.marker,
            toetsresultaten=result.toetsresultaten,
            examples=result.voorbeelden,
            metadata=result.metadata,
            cache_hits=result.cache_hits,
            total_requests=result.total_requests,
            error_message=result.error_message,
        )

    def generate_definition(
        self, begrip: str, context_dict: Dict[str, List[str]]
    ) -> IntegratedResult:
        """
        Generate definition using integrated service.

        Args:
            begrip: Term to define
            context_dict: Context information

        Returns:
            IntegratedResult with generated definition
        """
        try:
            # Delegate to unified service
            result = self._unified_service.generate_definition(begrip, context_dict)

            # Convert to legacy format
            return self._map_unified_to_integrated_result(result, "generate_definition")

        except Exception as e:
            self.logger.error(f"Integrated definition generation failed: {str(e)}")
            return IntegratedResult(
                success=False,
                operation="generate_definition",
                processing_time=0.0,
                service_mode=ServiceMode.AUTO,
                error_message=str(e),
            )

    async def agenerate_definition(
        self, begrip: str, context_dict: Dict[str, List[str]]
    ) -> IntegratedResult:
        """
        Generate definition using async integrated service.

        Args:
            begrip: Term to define
            context_dict: Context information

        Returns:
            IntegratedResult with generated definition
        """
        try:
            # Delegate to unified service
            result = await self._unified_service.agenerate_definition(
                begrip, context_dict
            )

            # Convert to legacy format
            return self._map_unified_to_integrated_result(
                result, "agenerate_definition"
            )

        except Exception as e:
            self.logger.error(
                f"Async integrated definition generation failed: {str(e)}"
            )
            return IntegratedResult(
                success=False,
                operation="agenerate_definition",
                processing_time=0.0,
                service_mode=ServiceMode.AUTO,
                error_message=str(e),
            )

    def get_service_statistics(self) -> Dict[str, Any]:
        """Get service statistics."""
        return self._unified_service.get_statistics()

    def reset_statistics(self) -> None:
        """Reset service statistics."""
        self._unified_service.reset_statistics()


# Global instance voor gemakkelijke toegang
_integrated_service_instance = None


def get_integrated_service(config: Optional[ServiceConfig] = None) -> IntegratedService:
    """Get or create global integrated service instance."""
    global _integrated_service_instance
    if _integrated_service_instance is None:
        _integrated_service_instance = IntegratedService(config)
    return _integrated_service_instance


# Voor backward compatibility - exporteer ook de key classes
__all__ = [
    "IntegratedService",
    "IntegratedResult",
    "ServiceConfig",
    "ServiceMode",
    "get_integrated_service",
]
