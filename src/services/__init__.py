"""Services package voor DefinitieAgent.

Dit package bevat alle service componenten inclusief
geïntegreerde services en orchestratie functionaliteiten.
"""

# Import nieuwe services - lazy imports to avoid circular dependencies
from services.container import ContainerConfigs, ServiceContainer, get_container

# Import new unified services
from services.unified_definition_generator import UnifiedDefinitionGenerator
from services.definition_generator_config import UnifiedGeneratorConfig
from services.definition_generator_cache import DefinitionGeneratorCache


# Lazy import factory functions
def get_definition_service(*args, **kwargs):
    from services.service_factory import get_definition_service as _get_service

    return _get_service(*args, **kwargs)


def render_feature_flag_toggle(*args, **kwargs):
    from services.service_factory import render_feature_flag_toggle as _render_toggle

    return _render_toggle(*args, **kwargs)


# Export alle belangrijke classes
__all__ = [
    # Unified Generator
    "UnifiedDefinitionGenerator",
    "UnifiedGeneratorConfig",
    "DefinitionGeneratorCache",
    # Container en Factory
    "ServiceContainer",
    "get_container",
    "ContainerConfigs",
    "get_definition_service",
    "render_feature_flag_toggle",
]
