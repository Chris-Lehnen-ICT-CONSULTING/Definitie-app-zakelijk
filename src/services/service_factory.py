"""
Service Factory met Feature Flags.

Dit module biedt de integratie tussen de nieuwe services en de legacy code,
met feature flags voor geleidelijke migratie.
"""

import logging
import os
from typing import Any

from services.container import ContainerConfigs, ServiceContainer
from utils.container_manager import get_cached_container
from utils.dict_helpers import safe_dict_get
from utils.type_helpers import ensure_dict, ensure_list, ensure_string

# TYPE_CHECKING import verwijderd - UnifiedDefinitionGenerator niet meer nodig
# if TYPE_CHECKING:
#     from services.unified_definition_generator import UnifiedDefinitionGenerator

logger = logging.getLogger(__name__)


# Eenvoudige module-level cache om herhaalde zware initialisatie te voorkomen
_SERVICE_ADAPTER_CACHE: dict[tuple, "ServiceAdapter"] = {}


def get_container(config: dict | None = None) -> ServiceContainer:
    """Compatibility shim for tests expecting get_container in this module.

    Delegates to the cached container manager; honors optional custom config by
    creating a separately cached instance.
    """
    if config is None:
        return get_cached_container()
    from utils.container_manager import get_container_with_config

    return get_container_with_config(config)


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
        # NO MORE best iteration — V2 doesn't use iterations

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

    def _safe_float(self, value: Any, default: float = 0.0) -> float:
        """Safely convert any value to float with fallback.

        Handles None, empty strings, and conversion errors.
        """
        if value is None or value == "":
            return default
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _normalize_severity(self, severity: Any) -> str:
        """Normalize various severity formats to canonical values.

        Maps: error/critical -> high, warning -> medium, other -> low
        """
        # Extract string value from enums or objects
        if hasattr(severity, "value"):
            severity = severity.value
        severity = str(severity).lower() if severity else "low"

        # Map to canonical values
        if severity in ["error", "critical", "high"]:
            return "high"
        elif severity in ["warning", "medium"]:
            return "medium"
        return "low"

    def _extract_violations(self, source: Any) -> list[dict]:
        """Extract and normalize violations from dict or object format."""
        violations = []

        # Handle dict format
        if isinstance(source, dict):
            violations = self._extract_dict_violations(source)
        # Handle object format
        elif hasattr(source, "violations") and source.violations:
            violations = self._extract_object_violations(source)

        return violations

    def _extract_dict_violations(self, source: dict) -> list[dict]:
        """Extract violations from dict format."""
        violations = []
        for v in ensure_list(safe_dict_get(source, "violations", [])):
            violations.append({
                "rule_id": safe_dict_get(v, "rule_id", safe_dict_get(v, "code", "unknown")),
                "severity": self._normalize_severity(safe_dict_get(v, "severity")),
                "description": safe_dict_get(v, "description", safe_dict_get(v, "message", "")),
                "suggestion": safe_dict_get(v, "suggestion"),
            })
        return violations

    def _extract_object_violations(self, source: Any) -> list[dict]:
        """Extract violations from object format."""
        violations = []
        for v in source.violations:
            violations.append({
                "rule_id": getattr(v, "rule_id", "unknown"),
                "severity": self._normalize_severity(getattr(v, "severity", None)),
                "description": getattr(v, "description", ""),
                "suggestion": getattr(v, "suggestion", None),
            })
        return violations

    def _extract_score(self, result: Any) -> float:
        """Extract score from various result formats with safe fallback."""
        # Try modern 'score' field first
        if hasattr(result, "score"):
            return self._safe_float(result.score)
        # Try dict access
        if isinstance(result, dict) and "score" in result:
            return self._safe_float(result["score"])
        # Fallback to deprecated key 'overall_score' (dict format only)
        if isinstance(result, dict) and "overall_score" in result:
            return self._safe_float(result["overall_score"])
        # As a last resort, attempt to convert known result objects to dict-like structures
        for method_name in ("to_dict", "dict", "model_dump"):
            try:
                method = getattr(result, method_name, None)
                if callable(method):
                    data = method()
                    if isinstance(data, dict):
                        if "score" in data:
                            return self._safe_float(data["score"])
                        if "overall_score" in data:
                            return self._safe_float(data["overall_score"])
            except Exception:
                # Ignore conversion issues and fall through to default
                pass
        return 0.0

    def _extract_is_acceptable(self, result: Any, score: float) -> bool:
        """Extract acceptance status with fallback to score threshold."""
        # Try direct fields first
        for field in ["is_acceptable", "is_valid"]:
            if hasattr(result, field):
                return bool(getattr(result, field))
            if isinstance(result, dict) and field in result:
                return bool(result[field])
        # Fallback to score threshold
        return score >= 0.5

    def normalize_validation(self, result: Any) -> dict:
        """Normalize any validation format to canonical V2 dict.

        Maps various validation formats to the canonical ValidationDetailsDict:
        - Schema-conform TypedDict via ensure_schema_compliance
        - Legacy ValidationResult dataclass/object via adapter
        - Ensures severity mapping (error->high, warning->medium, other->low) for legacy items
        """
        # Handle None case
        if result is None:
            return {
                "overall_score": 0.0,
                "is_acceptable": False,
                "violations": [],
                "passed_rules": [],
            }

        # If it's already a dict-like result, normalize directly
        if isinstance(result, dict):
            return {
                "overall_score": self._safe_float(
                    safe_dict_get(result, "overall_score", safe_dict_get(result, "score", 0.0))
                ),
                "is_acceptable": bool(
                    safe_dict_get(result, "is_acceptable", safe_dict_get(result, "is_valid", False))
                ),
                "violations": ensure_list(safe_dict_get(result, "violations", [])),
                "passed_rules": ensure_list(safe_dict_get(result, "passed_rules", [])),
            }

        # Try common object->dict converters first (supports Mock().to_dict())
        for method_name in ("to_dict", "dict", "model_dump"):
            conv = getattr(result, method_name, None)
            if callable(conv):
                try:
                    data = conv()
                    if isinstance(data, dict):
                        return {
                            "overall_score": self._safe_float(
                                safe_dict_get(data, "overall_score", safe_dict_get(data, "score", 0.0))
                            ),
                            "is_acceptable": bool(
                                safe_dict_get(data, "is_acceptable", safe_dict_get(data, "is_valid", False))
                            ),
                            "violations": ensure_list(safe_dict_get(data, "violations", [])),
                            "passed_rules": ensure_list(safe_dict_get(data, "passed_rules", [])),
                        }
                except Exception:
                    pass

        # Prefer schema-compliant adapter for dataclass/TypedDict
        try:
            from services.validation.mappers import ensure_schema_compliance  # lazy import

            schema = ensure_schema_compliance(result)
            # Derive score robustly: prefer schema value, otherwise fallback extract
            extracted_score = self._extract_score(result)
            overall = self._safe_float(schema.get("overall_score", extracted_score))

            # Derive acceptance robustly: prefer schema, else based on score
            is_acceptable = schema.get("is_acceptable")
            if is_acceptable is None:
                is_acceptable = self._extract_is_acceptable(result, overall)

            return {
                "overall_score": overall,
                "is_acceptable": bool(is_acceptable),
                "violations": ensure_list(schema.get("violations", [])),
                "passed_rules": ensure_list(schema.get("passed_rules", [])),
            }
        except Exception:
            pass

        # Final fallback: attribute extraction
        violations = self._extract_violations(result)
        overall_score = self._extract_score(result)
        is_acceptable = self._extract_is_acceptable(result, overall_score)
        passed_rules: list = []
        if hasattr(result, "passed_rules"):
            passed_rules = getattr(result, "passed_rules", [])

        return {
            "overall_score": overall_score,
            "is_acceptable": is_acceptable,
            "violations": violations,
            "passed_rules": passed_rules,
        }

    def _handle_regeneration_context(self, begrip: str, kwargs: dict) -> str:
        """Handle regeneration context enhancement if present."""
        regeneration_context = safe_dict_get(kwargs, "regeneration_context")
        extra_instructions = ensure_string(safe_dict_get(kwargs, "extra_instructies", ""))

        if not regeneration_context:
            return extra_instructions

        from services.regeneration_service import RegenerationService
        # Create temporary service to enhance prompt
        temp_service = RegenerationService(None)  # No prompt builder needed for enhancement
        extra_instructions = temp_service.enhance_prompt_with_context(
            extra_instructions or "", regeneration_context
        )
        logger.info(f"Enhanced prompt with regeneration context for '{begrip}'")
        return extra_instructions

    def to_ui_response(self, response, agent_result: dict) -> dict:
        """Convert orchestrator response to canonical UI format.

        Creates a UIResponseDict with all required fields populated.
        No best iteration attr, no is_valid, only the canonical V2 format.
        """

        # Extract definition text
        definitie_text = ""
        definitie_origineel = ""
        if response.success and response.definition:
            definitie_text = response.definition.definitie
            definitie_origineel = (
                safe_dict_get(response.definition.metadata, "definitie_origineel")
                or safe_dict_get(response.definition.metadata, "origineel")
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
            voorbeelden = ensure_dict(safe_dict_get(response.definition.metadata, "voorbeelden", {}))
            # Direct pass-through - orchestrator heeft al canonieke voorbeelden

            # Debug logging point B - ServiceFactory adapter
            if os.getenv("DEBUG_EXAMPLES"):
                logger.info(
                    "[EXAMPLES-B] Adapter | gen_id=%s | metadata.voorbeelden=%s | ui_keys=%s",
                    safe_dict_get(response.definition.metadata, "generation_id"),
                    (
                        "present"
                        if safe_dict_get(response.definition.metadata, "voorbeelden")
                        else "missing"
                    ),
                    (
                        list((voorbeelden or {}).keys())
                        if isinstance(voorbeelden, dict)
                        else "NOT_DICT"
                    ),
                )

        # Build metadata (include selected web lookup fields for UI status/debugging)
        metadata = {}
        if response.definition and response.definition.metadata:
            md = response.definition.metadata
            metadata = {
                "prompt_template": safe_dict_get(md, "prompt_template"),
                "prompt_text": safe_dict_get(md, "prompt_text"),
                "context": ensure_dict(safe_dict_get(md, "context", {})),
                "generation_id": ensure_string(safe_dict_get(md, "generation_id", "")),
                "duration": safe_dict_get(md, "processing_time", 0.0),
                "model": ensure_string(safe_dict_get(md, "model", "gpt-4")),
            }
            for k in (
                "web_lookup_status",
                "web_lookup_available",
                "web_lookup_timeout",
                "web_sources_count",
                "web_lookup_debug",
                "web_lookup_debug_available",
            ):
                v = safe_dict_get(md, k)
                if v is not None:
                    metadata[k] = v

        # Extract sources
        sources = []
        if response.definition and response.definition.metadata:
            sources = ensure_list(safe_dict_get(response.definition.metadata, "sources", []))

        # Build canonical UI response
        result = {
            "success": response.success,
            "definitie_origineel": definitie_origineel,
            "definitie_gecorrigeerd": definitie_text,
            "final_score": safe_dict_get(validation_details, "overall_score", 0.0),
            "validation_details": validation_details,
            "voorbeelden": voorbeelden,
            "metadata": metadata,
            "sources": sources,
        }

        # Voeg opgeslagen ID toe indien beschikbaar (orchestrator heeft opgeslagen)
        try:
            if getattr(response, "definition", None) and getattr(response.definition, "id", None):
                result["saved_definition_id"] = int(response.definition.id)
        except Exception:
            pass
        return result

    async def generate_definition(self, begrip: str, context_dict: dict, **kwargs):
        """
        Legacy compatible definitie generatie (SYNC for legacy UI).

        Vertaalt de legacy interface naar de nieuwe service calls.
        Deze methode is sync om legacy UI compatibility te behouden.
        """
        from services.interfaces import GenerationRequest

        # Handle regeneration context
        extra_instructions = self._handle_regeneration_context(begrip, kwargs)

        # Converteer legacy context_dict naar GenerationRequest
        # Extract ontologische categorie uit kwargs
        categorie = safe_dict_get(kwargs, "categorie")
        ontologische_categorie = None
        if categorie:
            # Converteer OntologischeCategorie enum naar string
            if hasattr(categorie, "value"):
                ontologische_categorie = categorie.value
            else:
                ontologische_categorie = str(categorie)

        import uuid

        # Map legacy dictionary to V2 fields and keep legacy string fields populated for compatibility
        org_list = ensure_list(safe_dict_get(context_dict, "organisatorisch", []))
        context_text = (
            ", ".join(org_list) if isinstance(org_list, list) else str(org_list or "")
        )
        # EPIC-010: domein field verwijderd - gebruik juridische_context

        # Collect options (feature flags etc.)
        opts = ensure_dict(safe_dict_get(kwargs, "options", {}))

        # Document context (EPIC-018): compacte samenvatting door UI aangeleverd
        doc_context = ensure_string(safe_dict_get(kwargs, "document_context", "")).strip()

        request = GenerationRequest(
            id=str(uuid.uuid4()),  # Generate unique ID for tracking
            begrip=begrip,
            # CRITICAL FIX: Use the new list fields for V2 context mapping
            organisatorische_context=org_list,
            juridische_context=ensure_list(safe_dict_get(context_dict, "juridisch", [])),
            wettelijke_basis=ensure_list(safe_dict_get(context_dict, "wettelijk", [])),
            # Standard fields
            organisatie=ensure_string(safe_dict_get(kwargs, "organisatie", "")),
            extra_instructies=extra_instructions,
            ontologische_categorie=ontologische_categorie,  # Categorie uit 6-stappen protocol
            actor="legacy_ui",  # Track that this comes from legacy UI
            legal_basis="legitimate_interest",  # Default legal basis for DPIA compliance
            # Populate legacy string context for compatibility with tests/UI
            context=context_text,
            options=opts or None,
            document_context=(doc_context or None),
        )

        # Compose additional context (documents/web lookup augmentation, etc.)
        extra_context: dict[str, Any] = {}
        # EPIC-018: document snippets meegeven aan orchestrator context
        doc_snippets_kw = safe_dict_get(kwargs, "document_snippets", None)
        if doc_snippets_kw:
            try:
                # Ensure list of dicts
                from utils.type_helpers import ensure_list, ensure_dict

                snippets_list = [ensure_dict(x) for x in ensure_list(doc_snippets_kw)]
                if snippets_list:
                    extra_context["documents"] = {"snippets": snippets_list}
            except Exception:
                pass

        # Handle V2 orchestrator async call properly
        response = await self.orchestrator.create_definition(request, context=extra_context or None)

        # Early return for failure case
        if not response.success or not response.definition:
            return self._create_failure_response(response)

        # Convert to canonical UI format using normalization
        ui_response = self.to_ui_response(response, {})

        # Add minimal legacy compatibility fields
        result_dict = {
            **ui_response,
            "success": True,
            "final_definitie": ui_response["definitie_gecorrigeerd"],  # Legacy alias
            "marker": ensure_string(safe_dict_get(response.definition.metadata, "marker", "")),
            "validation_score": ui_response["final_score"],  # Legacy alias
            # Ensure prompt fields are available for debug
            "prompt_text": ensure_string(safe_dict_get(ui_response["metadata"], "prompt_text", "")),
            "prompt_template": safe_dict_get(ui_response["metadata"], "prompt_template", ""),
        }
        return result_dict

    def _create_failure_response(self, response: Any) -> dict:
        """Create a standardized failure response."""
        return {
            "success": False,
            "error_message": getattr(response, "message", None) or "Generatie mislukt",
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

## NOTE:
## Keep a single, test‑patchable symbol named `get_container` in this module.
## Previous duplicate definition attempted to import a non‑existent
## `utils.container_manager.get_container`, causing ImportError at runtime.
## The implementation above (cached container manager) is the canonical one.


class ServiceFactory:
    """Legacy-compatible factory wrapper to avoid ImportError in older imports.

    Provides a minimal surface compatible with older tests that expect a
    class named ServiceFactory exposing service operations.
    """

    def __init__(self, container: ServiceContainer | None = None):
        self._container = container or get_cached_container()
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
        cached = safe_dict_get(_SERVICE_ADAPTER_CACHE, key)
        if cached is not None:
            return cached

    # US-201: Gebruik cached container via lokale shim (test‑friendly)
    container = get_container(config)

    adapter = ServiceAdapter(container)
    if not is_pytest:
        _SERVICE_ADAPTER_CACHE[key] = adapter
    return adapter
