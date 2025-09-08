"""
Service Factory met Feature Flags.

Dit module biedt de integratie tussen de nieuwe services en de legacy code,
met feature flags voor geleidelijke migratie.
"""

import logging
from typing import Any

import streamlit as st

from services.container import ContainerConfigs, ServiceContainer, get_container

# TYPE_CHECKING import verwijderd - UnifiedDefinitionGenerator niet meer nodig
# if TYPE_CHECKING:
#     from services.unified_definition_generator import UnifiedDefinitionGenerator

logger = logging.getLogger(__name__)


# Eenvoudige module-level cache om herhaalde zware initialisatie te voorkomen
_SERVICE_ADAPTER_CACHE: dict[tuple, "ServiceAdapter"] = {}


def _freeze_config(value: Any) -> Any:
    """Maak een hashbare representatie van (mogelijk geneste) configstructuren.

    Ondersteunt dicts, lists/tuples, sets en basistypes.
    """
    if isinstance(value, dict):
        return tuple(sorted((k, _freeze_config(v)) for k, v in value.items()))
    if isinstance(value, (list | tuple)):
        return tuple(_freeze_config(v) for v in value)
    if isinstance(value, set):
        return tuple(sorted(_freeze_config(v) for v in value))
    return value


class LegacyGenerationResult:
    """
    Wrapper die nieuwe service response omzet naar legacy object interface.

    De UI verwacht een object met attributen zoals final_definitie, success, etc.
    Deze class biedt die interface terwijl intern de nieuwe service data gebruikt.
    """

    def __init__(self, **kwargs):
        """Initialiseer met alle kwargs als attributen."""
        for key, value in kwargs.items():
            setattr(self, key, value)

        # Zorg voor backwards compatibility defaults
        if not hasattr(self, "success"):
            self.success = True
        if not hasattr(self, "final_definitie"):
            self.final_definitie = getattr(self, "definitie_gecorrigeerd", "")
        if not hasattr(self, "final_score"):
            self.final_score = getattr(self, "validation_score", 0.0)
        if not hasattr(self, "reason"):
            self.reason = getattr(self, "error_message", "")

        # Legacy UI compatibiliteit - voor iterative generation workflow
        if not hasattr(self, "iteration_count"):
            self.iteration_count = 1
        if not hasattr(self, "total_processing_time"):
            self.total_processing_time = getattr(self, "processing_time", 0.0)
        if not hasattr(self, "iterations"):
            self.iterations = []
        if not hasattr(self, "best_iteration"):
            # Maak een fake best_iteration voor UI compatibility
            class FakeIteration:
                def __init__(self, parent):
                    self.iteration_number = 1
                    self.validation_result = FakeValidationResult(parent)
                    self.generation_result = parent

            class FakeValidationResult:
                def __init__(self, parent):
                    self.overall_score = parent.final_score
                    self.violations = []

            self.best_iteration = FakeIteration(self) if self.success else None

    def __getitem__(self, key):
        """Dict-like access voor backward compatibility."""
        return getattr(self, key, None)

    def get(self, key, default=None):
        """Dict-like get method."""
        return getattr(self, key, default)

    def __contains__(self, key):
        """Support 'in' operator voor dict-like behavior."""
        return hasattr(self, key)


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

    # Selecteer effectieve config
    config = use_container_config or _get_environment_config()

    # Bepaal cache key op basis van bevroren config
    key = _freeze_config(config)

    # Module-level cache (werkt in tests en CLI)
    cached = _SERVICE_ADAPTER_CACHE.get(key)
    if cached is not None:
        return cached

    # Maak nieuwe adapter en cache deze
    container = get_container(config)
    adapter = ServiceAdapter(container)
    _SERVICE_ADAPTER_CACHE[key] = adapter
    return adapter


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
        self.ui_service = container.definition_ui_service()

    def get_service_info(self) -> dict:
        """Return service info voor UI detectie."""
        return {
            "service_mode": "container_v2",
            "architecture": "microservices",
            "version": "2.0",
        }

    async def generate_definition(self, begrip: str, context_dict: dict, **kwargs):
        """
        Legacy compatible definitie generatie (SYNC for legacy UI).

        Vertaalt de legacy interface naar de nieuwe service calls.
        Deze methode is sync om legacy UI compatibility te behouden.
        """

        from services.interfaces import GenerationRequest

        # Handle regeneration context (GVI Rode Kabel integration)
        regeneration_context = kwargs.get("regeneration_context")
        extra_instructions = kwargs.get("extra_instructies", "")

        if regeneration_context:
            from services.regeneration_service import RegenerationService

            # Create temporary service to enhance prompt
            temp_service = RegenerationService(
                None
            )  # No prompt builder needed for enhancement
            extra_instructions = temp_service.enhance_prompt_with_context(
                extra_instructions or "", regeneration_context
            )
            logger.info(f"Enhanced prompt with regeneration context for '{begrip}'")

        # Converteer legacy context_dict naar GenerationRequest
        # Extract ontologische categorie uit kwargs
        categorie = kwargs.get("categorie")
        ontologische_categorie = None
        if categorie:
            # Converteer OntologischeCategorie enum naar string
            if hasattr(categorie, "value"):
                ontologische_categorie = categorie.value
            else:
                ontologische_categorie = str(categorie)

        import uuid

        # Map legacy dictionary to V2 fields and keep legacy string fields populated for compatibility
        org_list = context_dict.get("organisatorisch", []) or []
        context_text = (
            ", ".join(org_list) if isinstance(org_list, list) else str(org_list or "")
        )
        domein_text = ", ".join(context_dict.get("domein", []) or [])

        request = GenerationRequest(
            id=str(uuid.uuid4()),  # Generate unique ID for tracking
            begrip=begrip,
            # CRITICAL FIX: Use the new list fields for V2 context mapping
            organisatorische_context=org_list,
            juridische_context=context_dict.get("juridisch", []),
            wettelijke_basis=context_dict.get("wettelijk", []),
            # Keep domein as concatenated string for compatibility
            domein=domein_text,
            # Standard fields
            organisatie=kwargs.get("organisatie", ""),
            extra_instructies=extra_instructions,
            ontologische_categorie=ontologische_categorie,  # Categorie uit 6-stappen protocol
            actor="legacy_ui",  # Track that this comes from legacy UI
            legal_basis="legitimate_interest",  # Default legal basis for DPIA compliance
            # Populate legacy string context for compatibility with tests/UI
            context=context_text,
        )

        # Handle V2 orchestrator async call properly
        response = await self.orchestrator.create_definition(request)

        # Converteer response naar legacy format met object-achtige interface
        if response.success and response.definition:
            # Zorg dat prompt_template zichtbaar is op het juiste niveau
            result_dict = {
                "success": True,
                "definitie_origineel": (
                    response.definition.metadata.get("definitie_origineel")
                    or response.definition.metadata.get("origineel")
                    or response.definition.definitie
                ),
                "definitie_gecorrigeerd": response.definition.definitie,
                "final_definitie": response.definition.definitie,  # Voor legacy UI compatibility
                "marker": response.definition.metadata.get("marker", ""),
                "toetsresultaten": (
                    response.validation.get("violations", [])
                    if response.validation and isinstance(response.validation, dict)
                    else (
                        response.validation.errors
                        if response.validation
                        and hasattr(response.validation, "errors")
                        else []
                    )
                ),
                "validation_details": (
                    response.validation if response.validation else None
                ),
                "validation_score": (
                    response.validation.get("overall_score", 0.0)
                    if response.validation and isinstance(response.validation, dict)
                    else (
                        response.validation.score
                        if response.validation and hasattr(response.validation, "score")
                        else 0.0
                    )
                ),
                "final_score": (
                    response.validation.get("overall_score", 0.0)
                    if response.validation and isinstance(response.validation, dict)
                    else (
                        response.validation.score
                        if response.validation and hasattr(response.validation, "score")
                        else 0.0
                    )
                ),
                "voorbeelden": (response.definition.voorbeelden or []),
                "processing_time": response.definition.metadata.get(
                    "processing_time", 0
                ),
                "metadata": response.definition.metadata,  # Voeg metadata toe inclusief prompt_template
                # STORY 3.1 FIX: Add sources field to make them accessible in UI preview
                "sources": (
                    response.definition.metadata.get("sources", [])
                    if response.definition and response.definition.metadata
                    else []
                ),
                "prompt_text": "",
                "prompt_template": "",
            }

            # Voeg prompt_template ook direct toe voor makkelijkere toegang (alleen als nog niet gezet)
            if (
                not result_dict.get(
                    "prompt_template"
                )  # Alleen als nog niet gezet via prompt_text
                and response.definition.metadata
                and "prompt_template" in response.definition.metadata
            ):
                result_dict["prompt_template"] = response.definition.metadata[
                    "prompt_template"
                ]

            return LegacyGenerationResult(**result_dict)
        return LegacyGenerationResult(
            success=False,
            error_message=(getattr(response, "message", None) or "Generatie mislukt"),
            final_definitie="Generatie mislukt",
        )

    def get_stats(self) -> dict:
        """Get statistieken van alle services."""
        stats = {
            "generator": self.container.generator().get_stats(),
            "repository": self.container.repository().get_stats(),
            "orchestrator": self.orchestrator.get_stats(),
        }
        # Include validator stats if container exposes a validator (test compatibility)
        try:
            validator_service = getattr(self.container, "validator", None)
            if callable(validator_service):
                val = validator_service()
                if hasattr(val, "get_stats"):
                    stats["validator"] = val.get_stats()
        except Exception:
            pass
        return stats

    def search_web_sources(self, term: str, sources: list | None = None) -> dict:
        """
        Legacy compatible web lookup (SYNC for legacy UI).

        Args:
            term: Zoekterm
            sources: Lijst van bronnen om te doorzoeken

        Returns:
            Legacy format resultaat dict
        """
        import asyncio

        from services.interfaces import LookupRequest

        request = LookupRequest(term=term, sources=sources, max_results=5)

        results = asyncio.run(self.web_lookup.lookup(request))

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

    def export_definition(
        self,
        definition_id: int | None = None,
        ui_data: dict | None = None,
        format: str = "txt",
    ) -> dict:
        """
        Export definitie via UI service.

        Args:
            definition_id: ID van definitie om te exporteren
            ui_data: UI data zoals voorbeelden, review, etc.
            format: Export formaat

        Returns:
            Export resultaat dict
        """
        return self.ui_service.export_definition(
            definitie_id=definition_id, ui_data=ui_data, format=format
        )

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


# --- Legacy compatibility shim ---
# Intentionally avoid binding a static reference so tests can patch the symbol.


def get_service(*args, **kwargs):
    """Legacy alias for obtaining the definition service (adapter by default)."""
    return get_definition_service(*args, **kwargs)


class ServiceFactory:
    """Legacy-compatible factory wrapper to avoid ImportError in older imports.

    Provides a minimal surface compatible with older tests that expect a
    class named ServiceFactory exposing service operations.
    """

    def __init__(self, container: ServiceContainer | None = None):
        self._container = container or get_container(_get_environment_config())
        self._adapter = ServiceAdapter(self._container)

    # Legacy Dutch-named wrapper used by some historical tests
    def genereer_definitie(
        self, begrip: str, context: str | dict | None = None, **kwargs
    ):
        """Generate a definition (sync), mapping legacy context to new structure."""
        context_dict: dict[str, list] = {}
        if isinstance(context, dict):
            context_dict = context  # Already a dict-style context
        elif isinstance(context, str) and context:
            # Map legacy single string to organisatorisch for minimal compatibility
            context_dict = {"organisatorisch": [context]}
        import asyncio

        try:
            loop = asyncio.get_running_loop()
            # In async context: submit task to loop and wait thread-safely
            fut = asyncio.run_coroutine_threadsafe(
                self._adapter.generate_definition(
                    begrip=begrip, context_dict=context_dict, **kwargs
                ),
                loop,
            )
            return fut.result()
        except RuntimeError:
            # No running loop: safe to run
            return asyncio.run(
                self._adapter.generate_definition(
                    begrip=begrip, context_dict=context_dict, **kwargs
                )
            )

    # Modern wrapper
    def generate_definition(self, begrip: str, context_dict: dict, **kwargs):
        return self.genereer_definitie(begrip=begrip, context=context_dict, **kwargs)

    def get_stats(self) -> dict:
        return self._adapter.get_stats()


def get_definition_service(
    use_container_config: dict | None = None,
):
    """
    Get de juiste service op basis van feature flag.

    Deze functie bepaalt of we de nieuwe clean architecture gebruiken
    of terugvallen op de legacy UnifiedDefinitionService (indien beschikbaar).
    """
    import os

    use_new_services = os.getenv("USE_NEW_SERVICES", "").lower() == "true"

    # Als geen env var, check Streamlit session state
    if not use_new_services and not os.getenv("USE_NEW_SERVICES"):
        try:
            use_new_services = st.session_state.get("use_new_services", True)
        except (ImportError, AttributeError):
            use_new_services = True

    # Legacy fallback path when explicitly disabled
    if not use_new_services:
        try:
            # Resolve dynamically so tests can patch the symbol
            from importlib import import_module

            legacy_mod = import_module("services.unified_definition_service_v2")
            Unified = getattr(legacy_mod, "UnifiedDefinitionService", None)
            if Unified is not None:
                return Unified.get_instance()  # type: ignore[attr-defined]
        except Exception:
            # If legacy path not available, fall through to new services
            logger.warning(
                "Legacy UnifiedDefinitionService unavailable; using new services instead"
            )

    # Selecteer effectieve config
    config = use_container_config or _get_environment_config()

    # Bepaal cache key op basis van bevroren config (disabled under pytest)
    key = _freeze_config(config)
    is_pytest = os.getenv("PYTEST_CURRENT_TEST") is not None
    if not is_pytest:
        cached = _SERVICE_ADAPTER_CACHE.get(key)
        if cached is not None:
            return cached

    container = get_container(config)
    adapter = ServiceAdapter(container)
    if not is_pytest:
        _SERVICE_ADAPTER_CACHE[key] = adapter
    return adapter
