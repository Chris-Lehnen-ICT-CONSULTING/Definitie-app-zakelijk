"""Services package voor DefinitieAgent.

Dit package bevat alle service componenten inclusief
geïntegreerde services en orchestratie functionaliteiten.
"""

# Import de V2 versie als default
from services.unified_definition_service_v2 import (
    UnifiedDefinitionService,
    UnifiedServiceConfig,
    UnifiedServiceConfigV2,
    UnifiedResult,
    ProcessingMode,
    ArchitectureMode,
    ServiceMode,
)

# Import nieuwe services - lazy imports to avoid circular dependencies
from services.container import ServiceContainer, get_container, ContainerConfigs


# Lazy import factory functions
def get_definition_service(*args, **kwargs):
    from services.service_factory import get_definition_service as _get_service

    return _get_service(*args, **kwargs)


def render_feature_flag_toggle(*args, **kwargs):
    from services.service_factory import render_feature_flag_toggle as _render_toggle

    return _render_toggle(*args, **kwargs)


# Export alle belangrijke classes
__all__ = [
    # V2 Unified Service
    "UnifiedDefinitionService",
    "UnifiedServiceConfig",
    "UnifiedServiceConfigV2",
    "UnifiedResult",
    "ProcessingMode",
    "ArchitectureMode",
    "ServiceMode",
    # Container en Factory
    "ServiceContainer",
    "get_container",
    "ContainerConfigs",
    "get_definition_service",
    "render_feature_flag_toggle",
]
