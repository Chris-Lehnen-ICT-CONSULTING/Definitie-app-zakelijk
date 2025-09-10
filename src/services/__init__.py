"""Services package voor DefinitieAgent.

Dit package bevat alle service componenten inclusief
geïntegreerde services en orchestratie functionaliteiten.
"""

# Import nieuwe services - lazy imports to avoid circular dependencies
from services.container import ContainerConfigs, ServiceContainer, get_container
from services.definition_generator_cache import DefinitionGeneratorCache
from services.definition_generator_config import UnifiedGeneratorConfig

# UnifiedDefinitionGenerator vervangen door moderne architectuur
# from services.unified_definition_generator import UnifiedDefinitionGenerator


# Lazy import factory functions
def get_definition_service(*args, **kwargs):
    from services.service_factory import get_definition_service as _get_service

    return _get_service(*args, **kwargs)


def render_feature_flag_toggle(*args, **kwargs):
    # Moved to UI layer - services should not have UI dependencies
    # This stub is kept for backward compatibility but does nothing
    import logging

    logger = logging.getLogger(__name__)
    logger.warning(
        "render_feature_flag_toggle called from services - import from ui.helpers.feature_toggle instead"
    )
    return True


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
    "render_feature_flag_toggle",
]
