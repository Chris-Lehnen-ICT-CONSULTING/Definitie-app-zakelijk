"""Services package voor DefinitieAgent.

Dit package bevat alle service componenten inclusief
geïntegreerde services en orchestratie functionaliteiten.
"""

# Import nieuwe services - lazy imports to avoid circular dependencies
from services.container import (ContainerConfigs, ServiceContainer,
                                get_container)
from services.definition_generator_cache import DefinitionGeneratorCache
from services.definition_generator_config import UnifiedGeneratorConfig
from services.modern_web_lookup_service import ModernWebLookupService

# UnifiedDefinitionGenerator vervangen door moderne architectuur
# from services.unified_definition_generator import UnifiedDefinitionGenerator


# Lazy import factory functions
def get_definition_service(*args, **kwargs):
    from services.service_factory import get_definition_service as _get_service

    return _get_service(*args, **kwargs)


# Export alle belangrijke classes
__all__ = [
    "ContainerConfigs",
    "DefinitionGeneratorCache",
    # Container en Factory
    "ServiceContainer",
    # Unified Generator (DEPRECATED - vervangen door DefinitionOrchestrator)
    # "UnifiedDefinitionGenerator",
    "UnifiedGeneratorConfig",
    "get_container",
    "get_definition_service",
    # Optional direct access to web lookup service
    "ModernWebLookupService",
]
