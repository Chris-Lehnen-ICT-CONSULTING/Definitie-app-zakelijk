"""
Service Factory met Feature Flags.

Dit module biedt de integratie tussen de nieuwe services en de legacy code,
met feature flags voor geleidelijke migratie.
"""

import logging

import streamlit as st
from services.container import ContainerConfigs, ServiceContainer, get_container

# TYPE_CHECKING import verwijderd - UnifiedDefinitionGenerator niet meer nodig
# if TYPE_CHECKING:
#     from services.unified_definition_generator import UnifiedDefinitionGenerator

logger = logging.getLogger(__name__)


def get_definition_service(
    use_container_config: dict | None = None,
) -> "ServiceAdapter":
    """
    Get de juiste service op basis van feature flag.

    Deze functie bepaalt of we de nieuwe clean architecture gebruiken
    of terugvallen op de legacy UnifiedDefinitionGenerator.

    Args:
        use_container_config: Optionele container configuratie

    Returns:
        Service instance (legacy of nieuw via adapter)
    """
    # Check feature flag - environment variable heeft prioriteit voor tests/deployment
    import os

    use_new_services = os.getenv("USE_NEW_SERVICES", "").lower() == "true"

    # Als geen env var, check Streamlit session state
    if not use_new_services and not os.getenv("USE_NEW_SERVICES"):
        try:
            use_new_services = st.session_state.get("use_new_services", True)
        except (ImportError, AttributeError):
            # Buiten Streamlit context, gebruik default
            use_new_services = True

    if use_new_services:
        logger.info("Using new service architecture")
        # Gebruik nieuwe services via adapter
        config = use_container_config or _get_environment_config()
        container = get_container(config)
        return ServiceAdapter(container)
    logger.info("Legacy fallback - gebruik moderne DefinitionOrchestrator")
    # Legacy fallback vervangen door moderne architectuur
    config = use_container_config or _get_environment_config()
    container = get_container(config)
    return ServiceAdapter(container)  # Altijd nieuwe services gebruiken


def _get_environment_config() -> dict:
    """Bepaal environment en return juiste config."""
    import os

    env = os.getenv("APP_ENV", "production")

    if env == "development":
        return ContainerConfigs.development()
    if env == "testing":
        return ContainerConfigs.testing()
    return ContainerConfigs.production()


class ServiceAdapter:
    """
    Adapter die de nieuwe service architecture wrapped voor compatibility
    met de legacy UnifiedDefinitionGenerator interface.

    Dit maakt het mogelijk om de nieuwe services te gebruiken zonder
    alle UI code meteen aan te passen.
    """

    def __init__(self, container: ServiceContainer):
        """
        Initialiseer adapter met service container.

        Args:
            container: De service container met alle services
        """
        self.container = container
        self.orchestrator = container.orchestrator()
        self.web_lookup = container.web_lookup()

    async def generate_definition(self, begrip: str, context_dict: dict, **kwargs):
        """
        Legacy compatible definitie generatie.

        Vertaalt de legacy interface naar de nieuwe service calls.
        """
        from services.interfaces import GenerationRequest

        # Converteer legacy context_dict naar GenerationRequest
        request = GenerationRequest(
            begrip=begrip,
            context=", ".join(context_dict.get("organisatorisch", [])),
            domein=", ".join(context_dict.get("domein", [])),
            organisatie=kwargs.get("organisatie", ""),
            extra_instructies=kwargs.get("extra_instructies"),
        )

        # Gebruik orchestrator
        response = await self.orchestrator.create_definition(request)

        # Converteer response naar legacy format
        if response.success and response.definition:
            return {
                "success": True,
                "definitie_origineel": response.definition.metadata.get(
                    "origineel", response.definition.definitie
                ),
                "definitie_gecorrigeerd": response.definition.definitie,
                "marker": response.definition.metadata.get("marker", ""),
                "toetsresultaten": (
                    response.validation.errors if response.validation else []
                ),
                # Add detailed validation results for UI
                "validation_details": (
                    response.validation if response.validation else None
                ),
                "validation_score": (
                    response.validation.score if response.validation else 0.0
                ),
                "voorbeelden": response.definition.voorbeelden or [],
                "processing_time": response.definition.metadata.get(
                    "processing_time", 0
                ),
            }
        return {
            "success": False,
            "error_message": response.message or "Generatie mislukt",
        }

    def get_stats(self) -> dict:
        """Get statistieken van alle services."""
        return {
            "generator": self.container.generator().get_stats(),
            "validator": self.container.validator().get_stats(),
            "repository": self.container.repository().get_stats(),
            "orchestrator": self.orchestrator.get_stats(),
        }

    async def search_web_sources(self, term: str, sources: list | None = None) -> dict:
        """
        Legacy compatible web lookup.

        Args:
            term: Zoekterm
            sources: Lijst van bronnen om te doorzoeken

        Returns:
            Legacy format resultaat dict
        """
        from services.interfaces import LookupRequest

        request = LookupRequest(term=term, sources=sources, max_results=5)

        results = await self.web_lookup.lookup(request)

        # Converteer naar legacy format
        legacy_results = {}
        for result in results:
            legacy_results[result.source.name] = {
                "definitie": result.definition,
                "context": result.context,
                "voorbeelden": result.examples,
                "verwijzingen": result.references,
                "betrouwbaarheid": result.source.confidence,
            }

        return legacy_results

    def validate_source(self, text: str) -> dict:
        """Legacy compatible bron validatie."""
        source = self.web_lookup.validate_source(text)
        return {
            "bron": source.name,
            "betrouwbaarheid": source.confidence,
            "is_juridisch": source.is_juridical,
        }

    def find_juridische_verwijzingen(self, text: str) -> list:
        """Legacy compatible juridische verwijzingen."""
        refs = self.web_lookup.find_juridical_references(text)
        return [
            {
                "type": ref.type,
                "verwijzing": ref.reference,
                "context": ref.context,
                "betrouwbaarheid": ref.confidence,
            }
            for ref in refs
        ]

    # Voeg meer legacy compatible methods toe indien nodig...


# Feature flag UI component
def render_feature_flag_toggle():
    """
    Render een toggle voor de nieuwe services in de Streamlit sidebar.

    Dit maakt het makkelijk om te switchen tussen oude en nieuwe services.
    """
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🧪 Experimental")

        new_services = st.checkbox(
            "Gebruik nieuwe services",
            value=st.session_state.get("use_new_services", True),
            key="use_new_services",
            help="Schakel over naar de nieuwe clean service architectuur (DEFAULT)",
        )

        if new_services:
            st.info("🚀 Nieuwe services actief!")

            # Toon extra opties
            env = st.selectbox(
                "Environment",
                ["production", "development", "testing"],
                help="Selecteer environment configuratie",
            )

            if env != "production":
                st.warning(f"⚠️ {env.title()} mode actief")

        return new_services
