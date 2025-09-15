"""
Service Factory met Feature Flags.

Dit module biedt de integratie tussen de nieuwe services en de legacy code,
met feature flags voor geleidelijke migratie.
"""

import logging
import os
from typing import Any

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

        # Legacy UI compatibiliteit - minimaal voor oude tests
        if not hasattr(self, "iteration_count"):
            self.iteration_count = 1
        if not hasattr(self, "total_processing_time"):
            self.total_processing_time = getattr(self, "processing_time", 0.0)
        if not hasattr(self, "iterations"):
            self.iterations = []
        # NO MORE best_iteration - V2 doesn't use iterations

    def __getitem__(self, key):
        """Dict-like access voor backward compatibility."""
        return getattr(self, key, None)

    def get(self, key, default=None):
        """Dict-like get method."""
        return getattr(self, key, default)

    def __contains__(self, key):
        """Support 'in' operator voor dict-like behavior."""
        return hasattr(self, key)


## NOTE: get_definition_service is defined later in this file with legacy fallback support.


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
        # UI services worden niet langer vanuit de serviceslaag beheerd

    def get_service_info(self) -> dict:
        """Return service info voor UI detectie."""
        return {
            "service_mode": "container_v2",
            "architecture": "microservices",
            "version": "2.0",
        }

    def normalize_validation(self, result: Any) -> dict:
        """Normalize any validation format to canonical V2 dict.

        Maps various validation formats to the canonical ValidationDetailsDict:
        - ModularValidationService dict format
        - Legacy ValidationResult objects
        - Ensures severity mapping (error->high, warning->medium, other->low)
        """

        if result is None:
            return {
                "overall_score": 0.0,
                "is_acceptable": False,
                "violations": [],
                "passed_rules": [],
            }

        # If already a dict from ModularValidationService
        if isinstance(result, dict):
            # Map violations to canonical format
            violations = []
            for v in result.get("violations", []):
                severity = v.get("severity", "low")
                # Map internal severities to canonical
                if severity in ["error", "critical"]:
                    severity = "high"
                elif severity == "warning":
                    severity = "medium"
                else:
                    severity = "low"

                violations.append(
                    {
                        "rule_id": v.get("rule_id", v.get("code", "unknown")),
                        "severity": severity,
                        "description": v.get("description", v.get("message", "")),
                        "suggestion": v.get("suggestion"),
                    }
                )

            return {
                "overall_score": float(result.get("overall_score", 0.0)),
                "is_acceptable": result.get("is_acceptable", False),
                "violations": violations,
                "passed_rules": result.get("passed_rules", []),
            }

        # Legacy object format (shouldn't happen with V2, but be defensive)
        violations = []
        if hasattr(result, "violations") and result.violations:
            for v in result.violations:
                severity = "low"
                if hasattr(v, "severity"):
                    sev_val = (
                        v.severity.value
                        if hasattr(v.severity, "value")
                        else str(v.severity)
                    )
                    if sev_val in ["high", "critical", "error"]:
                        severity = "high"
                    elif sev_val in ["medium", "warning"]:
                        severity = "medium"

                violations.append(
                    {
                        "rule_id": getattr(v, "rule_id", "unknown"),
                        "severity": severity,
                        "description": getattr(v, "description", ""),
                        "suggestion": getattr(v, "suggestion", None),
                    }
                )

        # Use is_acceptable if available, otherwise check is_valid, otherwise use score threshold
        is_acceptable = False
        if hasattr(result, "is_acceptable"):
            is_acceptable = result.is_acceptable
        elif hasattr(result, "is_valid"):
            is_acceptable = result.is_valid
        elif hasattr(result, "score"):
            is_acceptable = result.score >= 0.5
        elif hasattr(result, "overall_score"):
            # Deprecated: overall_score is replaced by score
            is_acceptable = getattr(result, "overall_score", 0.0) >= 0.5

        overall_score = 0.0
        if hasattr(result, "score"):
            overall_score = float(result.score)
        elif hasattr(result, "overall_score"):
            # Deprecated: overall_score is replaced by score
            overall_score = float(getattr(result, "overall_score", 0.0))

        return {
            "overall_score": overall_score,
            "is_acceptable": is_acceptable,
            "violations": violations,
            "passed_rules": getattr(result, "passed_rules", []),
        }

    def to_ui_response(self, response, agent_result: dict) -> dict:
        """Convert orchestrator response to canonical UI format.

        Creates a UIResponseDict with all required fields populated.
        No best_iteration, no is_valid, only the canonical V2 format.
        """

        # Extract definition text
        definitie_text = ""
        definitie_origineel = ""
        if response.success and response.definition:
            definitie_text = response.definition.definitie
            definitie_origineel = (
                response.definition.metadata.get("definitie_origineel")
                or response.definition.metadata.get("origineel")
                or definitie_text
            )

        # Normalize validation (handle both validation_result and validation)
        validation_data = getattr(response, "validation_result", None) or getattr(
            response, "validation", None
        )
        validation_details = self.normalize_validation(validation_data)

        # Extract voorbeelden from metadata - direct pass-through van canonieke keys
        # REFACTORED: Geen mapping meer nodig, producers leveren al canonieke keys
        voorbeelden = {}
        if response.definition and response.definition.metadata:
            voorbeelden = response.definition.metadata.get("voorbeelden", {})
            # Direct pass-through - orchestrator heeft al canonieke voorbeelden

            # Debug logging point B - ServiceFactory adapter
            if os.getenv("DEBUG_EXAMPLES"):
                logger.info(
                    "[EXAMPLES-B] Adapter | gen_id=%s | metadata.voorbeelden=%s | ui_keys=%s",
                    response.definition.metadata.get("generation_id"),
                    (
                        "present"
                        if response.definition.metadata.get("voorbeelden")
                        else "missing"
                    ),
                    (
                        list((voorbeelden or {}).keys())
                        if isinstance(voorbeelden, dict)
                        else "NOT_DICT"
                    ),
                )

        # Build metadata
        metadata = {}
        if response.definition and response.definition.metadata:
            metadata = {
                "prompt_template": response.definition.metadata.get("prompt_template"),
                "prompt_text": response.definition.metadata.get("prompt_text"),
                "context": response.definition.metadata.get("context", {}),
                "generation_id": response.definition.metadata.get("generation_id", ""),
                "duration": response.definition.metadata.get("processing_time", 0.0),
                "model": response.definition.metadata.get("model", "gpt-4"),
            }

        # Extract sources
        sources = []
        if response.definition and response.definition.metadata:
            sources = response.definition.metadata.get("sources", [])

        # Build canonical UI response
        return {
            "success": response.success,
            "definitie_origineel": definitie_origineel,
            "definitie_gecorrigeerd": definitie_text,
            "final_score": validation_details["overall_score"],
            "validation_details": validation_details,
            "voorbeelden": voorbeelden,
            "metadata": metadata,
            "sources": sources,
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
        # EPIC-010: domein field verwijderd - gebruik juridische_context

        request = GenerationRequest(
            id=str(uuid.uuid4()),  # Generate unique ID for tracking
            begrip=begrip,
            # CRITICAL FIX: Use the new list fields for V2 context mapping
            organisatorische_context=org_list,
            juridische_context=context_dict.get("juridisch", []),
            wettelijke_basis=context_dict.get("wettelijk", []),
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

        # Convert to canonical UI format using normalization
        if response.success and response.definition:
            # Use the new canonical conversion
            ui_response = self.to_ui_response(response, {})

            # Add only minimal legacy compatibility fields
            # Most consumers should use the V2 fields directly
            result_dict = {
                **ui_response,
                "success": True,
                "final_definitie": ui_response[
                    "definitie_gecorrigeerd"
                ],  # Legacy alias
                "marker": response.definition.metadata.get("marker", ""),
                "validation_score": ui_response["final_score"],  # Legacy alias
                # Ensure prompt fields are available for debug
                "prompt_text": ui_response["metadata"].get("prompt_text", ""),
                "prompt_template": ui_response["metadata"].get("prompt_template", ""),
            }

            # Geen extra fallback meer voor prompt_template; UI leest 'prompt_text'
            return result_dict
        return {
            "success": False,
            "error_message": (
                getattr(response, "message", None) or "Generatie mislukt"
            ),
            "definitie_gecorrigeerd": "Generatie mislukt",
            "voorbeelden": {},
            "metadata": (
                getattr(response, "definition", None)
                and getattr(response.definition, "metadata", {})
            )
            or {},
        }

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
        # Gebruik pure serviceslaag voor export (geen UI-service afhankelijkheid)
        from services.export_service import ExportFormat
        export_service = self.container.export_service()
        export_path = export_service.export_definitie(
            definitie_id=definition_id,
            definitie_record=None,
            additional_data=ui_data,
            format=ExportFormat(format.lower()),
        )
        import os
        filename = os.path.basename(export_path) if export_path else None
        return {
            "success": True if export_path else False,
            "path": export_path,
            "filename": filename,
            "message": (f"Definitie succesvol geëxporteerd naar {filename}" if export_path else "Export mislukt"),
            "error": None if export_path else "Export pad onbekend",
        }

    # Voeg meer legacy compatible methods toe indien nodig...


# Feature flag UI component
# UI feature toggle moved to UI layer - services should not depend on Streamlit


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
        """Sync wrapper is verwijderd. Gebruik UI async_bridge vanuit de UI-laag."""
        raise NotImplementedError(
            "genereer_definitie (sync) is verwijderd uit services. "
            "Roep de async methode aan via ui.helpers.async_bridge.generate_definition_sync"
        )

    # Modern wrapper
    def generate_definition(self, begrip: str, context_dict: dict, **kwargs):
        """Sync wrapper is verwijderd; zie NotImplementedError boven."""
        return self.genereer_definitie(begrip=begrip, context=context_dict, **kwargs)

    def get_stats(self) -> dict:
        return self._adapter.get_stats()


def get_definition_service(
    use_container_config: dict | None = None,
):
    """
    Get the V2 service (always returns V2 container).

    Legacy routes removed per US-043. V2 is now the only path.
    Feature toggles should be handled in UI layer only.
    """
    # V2 only - no legacy fallback
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
