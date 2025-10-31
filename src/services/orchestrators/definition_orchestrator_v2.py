"""
rug: noqa: PLR0912, PLR0915
DefinitionOrchestratorV2 - Next-generation stateless orchestrator.

This orchestrator replaces the monolithic _generate_definition() method with
a clean, modular service architecture following proven session state elimination patterns.

Key improvements:
- 11-phase structured orchestration flow
- GVI Rode Kabel feedback integration
- DPIA/AVG compliance with PII redaction
- Performance optimization with caching
- Ontological category support (fixes template selection bug)
- Story 2.4: Uses ValidationOrchestratorInterface for clean separation of concerns
"""

import logging
import time
import uuid
from datetime import UTC, datetime

UTC = UTC  # Python 3.10 compatibility  # noqa: PLW0127
import contextlib
from typing import TYPE_CHECKING, Any, Optional

from services.exceptions import (
    DatabaseConnectionError,
    DatabaseConstraintError,
    DuplicateDefinitionError,
    RepositoryError,
)
from services.interfaces import (
    AIServiceInterface as IntelligentAIService,
    CleaningServiceInterface,
    Definition,
    DefinitionOrchestratorInterface,
    DefinitionRepositoryInterface,
    DefinitionResponseV2,
    EnhancementServiceInterface as EnhancementService,
    FeedbackEngineInterface as FeedbackEngine,
    GenerationRequest,
    MonitoringServiceInterface as MonitoringService,
    OrchestratorConfig,
    PromptServiceInterface as PromptServiceV2,
    SecurityServiceInterface as SecurityService,
    ValidationResult,
)
from services.validation.interfaces import ValidationOrchestratorInterface
from utils.dict_helpers import safe_dict_get
from utils.type_helpers import ensure_dict, ensure_list, ensure_string

logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    # Forward-declared interfaces for type checking without import errors
    from services.interfaces import PromptResult, WebLookupServiceInterface
    from src.services.synonym_orchestrator import SynonymOrchestrator


class DefinitionOrchestratorV2(DefinitionOrchestratorInterface):
    """
    Next-generation stateless orchestrator following proven session state
    elimination patterns. Replaces monolithic _generate_definition().

    Core architectural principles:
    - No session state access - all data passed explicitly
    - Structured 11-phase orchestration flow
    - GVI Rode Kabel feedback loop integration
    - DPIA/AVG compliance built-in
    - Comprehensive error handling and monitoring
    """

    def __init__(
        self,
        # Core generation services (required)
        prompt_service: Optional[
            "PromptServiceV2"
        ] = None,  # DEF-66: Now optional for lazy loading
        ai_service: "IntelligentAIService" = None,
        validation_service: "ValidationOrchestratorInterface" = None,
        cleaning_service: "CleaningServiceInterface" = None,
        repository: "DefinitionRepositoryInterface" = None,
        # Optional services
        enhancement_service: Optional["EnhancementService"] = None,
        security_service: Optional["SecurityService"] = None,
        monitoring: Optional["MonitoringService"] = None,
        feedback_engine: Optional["FeedbackEngine"] = None,
        # Configuration
        config: OrchestratorConfig | None = None,
        # Web lookup (Epic 3)
        web_lookup_service: Optional["WebLookupServiceInterface"] = None,
        # Synonym enrichment (Architecture v3.1)
        synonym_orchestrator: Optional["SynonymOrchestrator"] = None,
    ):
        """
        Clean dependency injection - no session state access.

        DEF-66: PromptServiceV2 is now lazy-loaded to reduce initialization time from 509ms to <180ms.
        If not provided, it will be created on first access.
        """
        # V2 Services (required, except prompt_service which is lazy)
        if not ai_service:
            msg = "AIServiceInterface is required"
            raise ValueError(msg)
        if not validation_service:
            msg = "ValidationOrchestratorInterface is required"
            raise ValueError(msg)
        if not cleaning_service:
            msg = "CleaningServiceInterface is required"
            raise ValueError(msg)
        if not repository:
            msg = "DefinitionRepositoryInterface is required"
            raise ValueError(msg)

        # DEF-66: Store prompt_service for lazy loading (private to force property usage)
        self._prompt_service = prompt_service
        self.ai_service = ai_service
        self.validation_service = validation_service
        self.enhancement_service = enhancement_service

        # Security (V2 only)
        self.security_service = security_service

        # Infrastructure
        self.cleaning_service = cleaning_service
        self.repository = repository
        self.monitoring = monitoring

        # Feedback system
        self.feedback_engine = feedback_engine

        # Configuration
        self.config = config or OrchestratorConfig()

        # Epic 3: optional web lookup service
        self.web_lookup_service = web_lookup_service

        # Architecture v3.1: optional synonym enrichment
        self.synonym_orchestrator = synonym_orchestrator

        logger.info(
            "DefinitionOrchestratorV2 initialized with configuration: "
            f"feedback_loop={self.config.enable_feedback_loop}, "
            f"enhancement={self.config.enable_enhancement}, "
            f"caching={self.config.enable_caching}, "
            f"synonym_enrichment={'enabled' if synonym_orchestrator else 'disabled'}"
        )

    @property
    def prompt_service(self) -> "PromptServiceV2":
        """
        Lazy-load PromptServiceV2 on first access (DEF-66 performance optimization).

        This reduces TabbedInterface initialization from 509ms to <180ms by deferring
        the expensive PromptServiceV2 creation (435ms, 85% of init time) until first use.

        Returns:
            PromptServiceV2 instance (cached after first access)
        """
        if self._prompt_service is None:
            logger.debug("DEF-66: Lazy-loading PromptServiceV2 on first access")
            from services.prompts.prompt_service_v2 import PromptServiceV2

            self._prompt_service = PromptServiceV2()
            logger.debug("DEF-66: PromptServiceV2 initialized successfully")

        return self._prompt_service

    def get_service_info(self) -> dict:
        """Return service info voor UI quality control."""
        info = {
            "service_mode": "orchestrator_v2",
            "architecture": "microservices",
            "version": "2.0",
            "validation_service": "V2",
        }

        # Get rule count from validation service if available
        if hasattr(self.validation_service, "get_stats"):
            try:
                stats = self.validation_service.get_stats()
                info["rule_count"] = safe_dict_get(stats, "total_rules", 0)
            except Exception:
                info["rule_count"] = 0
        else:
            info["rule_count"] = 0

        return info

    def get_stats(self) -> dict:
        """Get statistics from orchestrator and services."""
        stats = {"orchestrator": {"requests_processed": 0, "success_rate": 0.0}}

        # Include validation stats if available
        if hasattr(self.validation_service, "get_stats"):
            with contextlib.suppress(Exception):
                stats["validation"] = self.validation_service.get_stats()

        return stats

    async def create_definition(  # noqa: PLR0912, PLR0915
        self, request: GenerationRequest, context: dict[str, Any] | None = None
    ) -> DefinitionResponseV2:
        """
        Main orchestration method - stateless and testable.

        Replaces the monolithic _generate_definition() with clean service calls.
        No session state access - all data passed explicitly.

        The 11-phase orchestration flow:
        1. Security & Privacy (DPIA/AVG Compliance)
        2. Feedback Integration (GVI Rode Kabel)
        3. Intelligent Prompt Generation (with ontological category fix)
        4. AI Generation with Retry Logic
        5. Text Cleaning & Normalization
        6. Validation
        7. Enhancement (if validation failed)
        8. Definition Object Creation
        9. Storage (Conditional on Quality Gate)
        10. Feedback Loop Update (GVI Rode Kabel)
        11. Monitoring & Metrics
        """
        start_time = time.time()
        generation_id = request.id if request.id else str(uuid.uuid4())

        try:
            # Track generation start
            if self.monitoring:
                await self.monitoring.start_generation(generation_id)

            logger.info(
                f"Generation {generation_id}: Starting orchestration for '{request.begrip}' "
                f"with category '{request.ontologische_categorie}'"
            )

            # =====================================
            # PHASE 1: Security & Privacy (DPIA/AVG Compliance)
            # =====================================
            sanitized_request = request
            if self.security_service:
                sanitized_request = await self.security_service.sanitize_request(
                    request
                )
                logger.info(
                    f"Generation {generation_id}: Request sanitized for privacy compliance"
                )
            else:
                logger.debug(
                    f"Generation {generation_id}: Security service not available, using original request"
                )

            # =====================================
            # PHASE 2: Feedback Integration (GVI Rode Kabel)
            # =====================================
            feedback_history = None
            if self.config.enable_feedback_loop and self.feedback_engine:
                feedback_history = await self.feedback_engine.get_feedback_for_request(
                    sanitized_request.begrip, sanitized_request.ontologische_categorie
                )
                logger.info(
                    f"Generation {generation_id}: Feedback loaded ({len(feedback_history or [])} entries)"
                )
            else:
                logger.debug(
                    f"Generation {generation_id}: Feedback system disabled or unavailable"
                )

            # =====================================
            # PHASE 2.4: Synonym Enrichment (Architecture v3.1)
            # =====================================
            enriched_synonyms = []
            ai_pending_count = 0
            synonym_enrichment_status = "not_available"

            if self.synonym_orchestrator:
                logger.info(
                    f"Generation {generation_id}: Starting synonym enrichment for term: {sanitized_request.begrip}"
                )
                try:
                    # Build context for synonym enrichment
                    synonym_context = {
                        "organisatorisch": sanitized_request.organisatorische_context
                        or [],
                        "juridisch": sanitized_request.juridische_context or [],
                        "wettelijk": sanitized_request.wettelijke_basis or [],
                    }

                    # Ensure synonyms (GPT-4 enrichment if needed)
                    # min_count=5 matches architecture specification (line 613)
                    enriched_synonyms, ai_pending_count = (
                        await self.synonym_orchestrator.ensure_synonyms(
                            term=sanitized_request.begrip,
                            min_count=5,
                            context=synonym_context,
                        )
                    )

                    logger.info(
                        f"Generation {generation_id}: Synonym enrichment complete - "
                        f"found {len(enriched_synonyms)} synonyms "
                        f"({ai_pending_count} AI-pending for review)"
                    )
                    synonym_enrichment_status = (
                        "success" if enriched_synonyms else "no_synonyms"
                    )

                except Exception as e:
                    logger.error(
                        f"Generation {generation_id}: Synonym enrichment failed: {type(e).__name__}: {e!s} - "
                        f"proceeding without synonym expansion"
                    )
                    synonym_enrichment_status = "error"
                    # Continue without synonyms - definition generation proceeds
            else:
                logger.debug(
                    f"Generation {generation_id}: Synonym orchestrator not available - "
                    f"proceeding without synonym enrichment"
                )

            # =====================================
            # PHASE 2.5: Web Lookup Context Enrichment (Epic 3)
            # =====================================
            provenance_sources = []
            web_lookup_status = "not_available"  # Track status for metadata
            debug_info = None  # Ensure defined even when web lookup is unavailable
            # Allow timeout override via env for environments with slower network
            import os

            try:
                WEB_LOOKUP_TIMEOUT = float(
                    os.getenv("WEB_LOOKUP_TIMEOUT_SECONDS", "10.0")
                )
            except Exception:
                WEB_LOOKUP_TIMEOUT = 10.0

            # Web lookup runs ALWAYS when service is available (no feature flag)
            if self.web_lookup_service:
                logger.info(
                    f"Generation {generation_id}: Starting web lookup for term: {sanitized_request.begrip}"
                )
                try:
                    from services.interfaces import LookupRequest
                    from services.web_lookup.provenance import build_provenance

                    # Build a compact context string to guide provider selection
                    ctx_parts = []
                    if sanitized_request.organisatorische_context:
                        ctx_parts.extend(sanitized_request.organisatorische_context)
                    if sanitized_request.juridische_context:
                        ctx_parts.extend(sanitized_request.juridische_context)
                    if sanitized_request.wettelijke_basis:
                        ctx_parts.extend(sanitized_request.wettelijke_basis)
                    context_str = " | ".join([str(x) for x in ctx_parts if x]) or None

                    # Allow broader result set so UI can show all hits
                    import os as _os

                    try:
                        _max_res = int(_os.getenv("WEB_LOOKUP_MAX_RESULTS", "20"))
                    except Exception:
                        _max_res = 20
                    lookup_request = LookupRequest(
                        term=sanitized_request.begrip,
                        sources=None,
                        context=context_str,
                        max_results=_max_res,
                        include_examples=False,
                        timeout=WEB_LOOKUP_TIMEOUT,  # Configurable via env var
                    )

                    # Add timeout protection for web lookup
                    import asyncio

                    web_results = await asyncio.wait_for(
                        self.web_lookup_service.lookup(lookup_request),
                        timeout=WEB_LOOKUP_TIMEOUT,
                    )
                    logger.info(
                        f"Generation {generation_id}: Web lookup returned {len(web_results) if web_results else 0} results"
                    )
                    # Capture debug info from service if available
                    try:
                        debug_info = getattr(
                            self.web_lookup_service, "_last_debug", None
                        )
                    except Exception:
                        debug_info = None

                    # Build provenance records
                    # Convert LookupResults to minimal dicts expected by build_provenance
                    prepared = []
                    for r in web_results or []:
                        prepared.append(
                            {
                                "provider": r.source.name.lower(),
                                "title": (
                                    safe_dict_get(r.metadata, "dc_title")
                                    if isinstance(r.metadata, dict)
                                    else None
                                )
                                or r.source.name,
                                "url": r.source.url,
                                "snippet": r.definition or r.context or "",
                                "score": float(r.source.confidence or 0.0),
                                "used_in_prompt": False,
                                "retrieved_at": (
                                    safe_dict_get(r.metadata, "retrieved_at")
                                    if isinstance(r.metadata, dict)
                                    else None
                                ),
                            }
                        )

                    # STORY 3.1: Extract legal metadata for juridical sources
                    provenance_sources = build_provenance(prepared, extract_legal=True)

                    # Mark top-K as used_in_prompt (we'll include these first in any context pack)
                    top_k = max(0, int(getattr(self.config, "web_lookup_top_k", 3)))
                    for i, src in enumerate(provenance_sources):
                        if i < top_k:
                            src["used_in_prompt"] = True

                    # Attach to context so prompt service can optionally use it
                    context = context or {}
                    context["web_lookup"] = {
                        "sources": provenance_sources,
                        "top_k": top_k,
                        "debug": debug_info,
                    }
                    logger.info(
                        f"Generation {generation_id}: Web lookup enriched context with {len(provenance_sources)} sources"
                    )
                    web_lookup_status = (
                        "success" if provenance_sources else "no_results"
                    )

                except TimeoutError:
                    logger.warning(
                        f"Generation {generation_id}: Web lookup timeout after {WEB_LOOKUP_TIMEOUT} seconds - "
                        f"prompt service will use cached lookup results or proceed without"
                    )
                    web_lookup_status = "timeout"
                    # Continue without web context - definition generation proceeds

                except Exception as e:
                    logger.error(
                        f"Generation {generation_id}: Web lookup failed: {type(e).__name__}: {e!s} - "
                        f"proceeding WITHOUT external context"
                    )
                    web_lookup_status = "error"
                    # Continue without web context - definition generation proceeds
            else:
                # Log that web lookup service is NOT available
                logger.warning(
                    f"Generation {generation_id}: Web lookup service not available - "
                    f"proceeding WITHOUT external context enrichment"
                )

            # =====================================
            # PHASE 2.9: Merge document snippets into provenance sources (EPIC-018)
            # =====================================
            try:
                docs_ctx = (
                    ensure_dict(safe_dict_get(context, "documents", {}))
                    if context
                    else {}
                )
                doc_snippets = ensure_list(safe_dict_get(docs_ctx, "snippets", []))
                if doc_snippets:
                    normalized_docs = []
                    for s in doc_snippets:
                        try:
                            normalized_docs.append(
                                {
                                    "provider": "documents",
                                    "title": ensure_string(
                                        safe_dict_get(s, "title")
                                        or safe_dict_get(s, "filename")
                                        or "document"
                                    ),
                                    "url": safe_dict_get(s, "url"),
                                    "snippet": ensure_string(
                                        safe_dict_get(s, "snippet", "")
                                    ),
                                    "score": float(
                                        safe_dict_get(s, "score", 0.0) or 0.0
                                    ),
                                    "used_in_prompt": True,
                                    "doc_id": safe_dict_get(s, "doc_id"),
                                    "source_label": "Geüpload document",
                                }
                            )
                        except Exception:
                            continue
                    if normalized_docs:
                        provenance_sources = normalized_docs + (
                            provenance_sources or []
                        )
                        context = context or {}
                        context["documents"] = {"snippets": normalized_docs}
            except Exception:
                pass

            # =====================================
            # PHASE 3: Intelligent Prompt Generation (with ontological category fix)
            # =====================================
            prompt_result = await self.prompt_service.build_generation_prompt(
                sanitized_request,
                feedback_history=feedback_history,
                context=context,
            )
            logger.info(
                f"Generation {generation_id}: V2 Prompt built ({prompt_result.token_count} tokens, "
                f"ontological_category={sanitized_request.ontologische_categorie})"
            )

            # Debug summary: how many sources vs injected snippets in prompt
            try:
                text = prompt_result.text or ""
                header = "### Contextinformatie uit bronnen:"
                injected_snippets = 0
                if header in text:
                    # Count list items following the header (lines starting with "- ")
                    tail = text.split(header, 1)[1]
                    injected_snippets = tail.count("\n- ")
                logger.info(
                    "Web lookup summary: sources=%s, injected_snippets=%s",
                    len(provenance_sources or []),
                    injected_snippets,
                )
            except Exception:
                # Non-fatal debug
                pass

            # =====================================
            # PHASE 4: AI Generation with Retry Logic
            # =====================================
            # Get temperature from config (0.1 for consistent legal definitions)
            from config.config_manager import get_prompt_temperature

            temperature = (
                safe_dict_get(sanitized_request.options, "temperature")
                if sanitized_request.options
                else None
            )
            if temperature is None:
                temperature = get_prompt_temperature("definition")

            generation_result = await self.ai_service.generate_definition(
                prompt=prompt_result.text,
                temperature=temperature,
                max_tokens=(
                    safe_dict_get(sanitized_request.options, "max_tokens", 500)
                    if sanitized_request.options
                    else 500
                ),
                model=(
                    safe_dict_get(sanitized_request.options, "model")
                    if sanitized_request.options
                    else None
                ),
            )
            logger.info(f"Generation {generation_id}: AI generation complete")

            # =====================================
            # PHASE 5: Generate Voorbeelden (Examples)
            # =====================================
            voorbeelden = {}
            try:
                from utils.voorbeelden_debug import DEBUG_ENABLED, debugger
                from voorbeelden.unified_voorbeelden import (
                    genereer_alle_voorbeelden_async,
                )

                # Build context_dict for voorbeelden generation (V2-only fields)
                voorbeelden_context = {
                    "organisatorisch": sanitized_request.organisatorische_context or [],
                    "juridisch": sanitized_request.juridische_context or [],
                    "wettelijk": sanitized_request.wettelijke_basis or [],
                }

                # Debug logging point C - Before voorbeelden generation
                if DEBUG_ENABLED:
                    debug_gen_id = debugger.start_generation(
                        begrip=sanitized_request.begrip,
                        definitie=(
                            generation_result.text
                            if hasattr(generation_result, "text")
                            else str(generation_result)
                        ),
                    )
                    debugger.log_point(
                        "C",
                        debug_gen_id,
                        context_keys=list(voorbeelden_context.keys()),
                        orchestrator="V2",
                    )
                    debugger.log_session_state(debug_gen_id, "C")

                # Generate voorbeelden using async for better performance (US-052)
                voorbeelden = await genereer_alle_voorbeelden_async(
                    begrip=sanitized_request.begrip,
                    definitie=(
                        generation_result.text
                        if hasattr(generation_result, "text")
                        else str(generation_result)
                    ),
                    context_dict=voorbeelden_context,
                )

                # Debug: Log antoniemen count
                if "antoniemen" in voorbeelden:
                    logger.info(
                        f"Orchestrator generated {len(voorbeelden['antoniemen'])} antoniemen for {sanitized_request.begrip}"
                    )

                # Debug logging point C2 - After voorbeelden generation
                if DEBUG_ENABLED:
                    debugger.log_point(
                        "C2",
                        debug_gen_id,
                        voorbeelden_types=list(voorbeelden.keys()),
                        voorbeelden_counts={
                            k: len(v) if isinstance(v, list) else 1
                            for k, v in voorbeelden.items()
                        },
                    )
                    debugger.log_session_state(debug_gen_id, "C2")

                # Debug logging point A - After voorbeelden generation in V2
                if os.getenv("DEBUG_EXAMPLES"):
                    logger.info(
                        "[EXAMPLES-A] V2 generated | gen_id=%s | begrip=%s | keys=%s | counts=%s",
                        generation_id,
                        sanitized_request.begrip,
                        (
                            list(voorbeelden.keys())
                            if isinstance(voorbeelden, dict)
                            else "NOT_DICT"
                        ),
                        {
                            k: len(v) if isinstance(v, list | str) else "INVALID"
                            for k, v in (voorbeelden or {}).items()
                        },
                    )

                logger.info(
                    f"Generation {generation_id}: Voorbeelden generated ({len(voorbeelden)} types)"
                )
            except Exception as e:
                logger.warning(
                    f"Generation {generation_id}: Voorbeelden generation failed: {e}"
                )
                if DEBUG_ENABLED and "debug_gen_id" in locals():
                    debugger.log_error(debug_gen_id, "C", e)
                # Continue without voorbeelden

            # =====================================
            # PHASE 6: Text Cleaning & Normalization
            # =====================================
            # V2 cleaning service (always available through adapter)
            raw_gpt_output = (
                generation_result.text
                if hasattr(generation_result, "text")
                else str(generation_result)
            )
            cleaning_result = await self.cleaning_service.clean_text(
                raw_gpt_output,
                sanitized_request.begrip,
            )
            cleaned_text = cleaning_result.cleaned_text

            # Extract clean definition for "origineel" display
            # Uses full cleaning to remove ALL unwanted patterns:
            # - "Ontologische categorie:" metadata header
            # - "[term]:" prefix (e.g., "Vervoersverbod:")
            # - Forbidden words, circular definitions, etc.
            from opschoning.opschoning_enhanced import opschonen_enhanced

            definitie_zonder_header = opschonen_enhanced(
                raw_gpt_output, sanitized_request.begrip, handle_gpt_format=True
            )

            logger.info(f"Generation {generation_id}: Text cleaned with V2 service")

            # =====================================
            # PHASE 6: Validation
            # =====================================
            # Use ValidationOrchestratorInterface.validate_text
            from services.validation.interfaces import ValidationContext

            # Tolerant correlation_id: als generation_id geen geldige UUID is, genereer er één
            try:
                corr = uuid.UUID(generation_id)
            except Exception:
                corr = uuid.uuid4()
            # Voeg opties toe aan metadata zodat validator context flags kan lezen
            meta: dict[str, Any] = {"generation_id": generation_id}
            try:
                if sanitized_request.options:
                    # Expliciet doorgeven van force_duplicate voor duplicate-escalatie
                    if bool(
                        safe_dict_get(
                            sanitized_request.options, "force_duplicate", False
                        )
                    ):
                        meta["force_duplicate"] = True
                    # Bewaar volledige options voor toekomstig gebruik (niet verplicht)
                    meta["options"] = dict(sanitized_request.options)
            except Exception:
                pass
            validation_context = ValidationContext(
                correlation_id=corr,
                metadata=meta,
            )
            # Validate using Definition object per interface contract
            temp_definition = Definition(
                begrip=sanitized_request.begrip,
                definitie=cleaned_text,
                organisatorische_context=sanitized_request.organisatorische_context
                or [],
                juridische_context=sanitized_request.juridische_context or [],
                wettelijke_basis=sanitized_request.wettelijke_basis or [],
                ontologische_categorie=sanitized_request.ontologische_categorie,
                created_by=sanitized_request.actor,
            )
            raw_validation = await self.validation_service.validate_definition(
                definition=temp_definition,
                context=validation_context,
            )
            # Normalize to schema-conform dict for internal decisions
            try:
                from services.validation.mappers import ensure_schema_compliance

                validation_result = ensure_schema_compliance(raw_validation)
            except Exception:
                # Defensive fallback to simple mapping
                is_ok = getattr(raw_validation, "is_valid", False)
                vio_list = getattr(raw_validation, "violations", None)
                if vio_list is None:
                    vio_list = getattr(raw_validation, "errors", []) or []
                validation_result = {
                    "is_acceptable": bool(is_ok),
                    "violations": vio_list,
                    "passed_rules": [],
                    "detailed_scores": {},
                    "version": "v2",
                    "system": {},
                }

            logger.info(
                f"Generation {generation_id}: Validation complete (valid: {safe_dict_get(validation_result, 'is_acceptable', False)})"
            )

            # =====================================
            # PHASE 7: Enhancement (if validation failed and enabled)
            # =====================================
            was_enhanced = False
            if (
                not safe_dict_get(validation_result, "is_acceptable", False)
                and self.config.enable_enhancement
                and self.enhancement_service
            ):
                enhanced_text = await self.enhancement_service.enhance_definition(
                    cleaned_text,
                    ensure_list(safe_dict_get(validation_result, "violations", [])),
                    context=sanitized_request,
                )

                # Re-validate enhanced text with new context
                try:
                    corr2 = uuid.UUID(generation_id)
                except Exception:
                    corr2 = uuid.uuid4()
                enhanced_context = ValidationContext(
                    correlation_id=corr2,
                    metadata={"generation_id": generation_id, "enhanced": True},
                )
                # Re-validate enhanced text using Definition object
                enhanced_definition = Definition(
                    begrip=sanitized_request.begrip,
                    definitie=enhanced_text,
                    organisatorische_context=sanitized_request.organisatorische_context
                    or [],
                    juridische_context=sanitized_request.juridische_context or [],
                    wettelijke_basis=sanitized_request.wettelijke_basis or [],
                    ontologische_categorie=sanitized_request.ontologische_categorie,
                    created_by=sanitized_request.actor,
                )
                raw_validation = await self.validation_service.validate_definition(
                    definition=enhanced_definition,
                    context=enhanced_context,
                )
                try:
                    from services.validation.mappers import ensure_schema_compliance

                    validation_result = ensure_schema_compliance(raw_validation)
                except Exception:
                    is_ok = getattr(raw_validation, "is_valid", False)
                    vio_list = getattr(raw_validation, "violations", None)
                    if vio_list is None:
                        vio_list = getattr(raw_validation, "errors", []) or []
                    validation_result = {
                        "is_acceptable": bool(is_ok),
                        "violations": vio_list,
                        "passed_rules": [],
                        "detailed_scores": {},
                        "version": "v2",
                        "system": {},
                    }

                cleaned_text = enhanced_text
                was_enhanced = True
                logger.info(
                    f"Generation {generation_id}: Enhancement applied, re-validated"
                )

            # =====================================
            # PHASE 8: Definition Object Creation
            # =====================================
            definition = self._create_definition_object(
                request=sanitized_request,
                text=cleaned_text,
                validation_result=validation_result,
                generation_metadata={
                    "model": getattr(generation_result, "model", "unknown"),
                    "tokens_used": getattr(generation_result, "tokens_used", 0),
                    "prompt_components": (
                        prompt_result.components_used if prompt_result else []
                    ),
                    "has_feedback": bool(feedback_history),
                    "enhanced": was_enhanced,
                    "generation_time": time.time() - start_time,
                    "generated_at": datetime.now(UTC).isoformat(),
                    "orchestrator_version": "v2.0",
                    "ontological_category_used": sanitized_request.ontologische_categorie,
                    # Epic 3: Web lookup metadata
                    "sources": provenance_sources,
                    "web_lookup_status": web_lookup_status,
                    "web_lookup_available": self.web_lookup_service is not None,
                    "web_lookup_timeout": WEB_LOOKUP_TIMEOUT,
                    "web_sources_count": len(provenance_sources),
                    "web_lookup_debug": debug_info,
                    "web_lookup_debug_available": debug_info is not None,
                    # Architecture v3.1: Synonym enrichment metadata
                    "synonym_enrichment_status": synonym_enrichment_status,
                    "synonym_enrichment_available": self.synonym_orchestrator
                    is not None,
                    "enriched_synonyms_count": len(enriched_synonyms),
                    "ai_pending_synonyms_count": ai_pending_count,
                    "enriched_synonyms": (
                        [
                            {"term": ws.term, "weight": ws.weight}
                            for ws in enriched_synonyms
                        ]
                        if enriched_synonyms
                        else []
                    ),
                    # Add voorbeelden to metadata so UI can display them
                    "voorbeelden": voorbeelden if voorbeelden else {},
                    # Store the prompt text for debug UI
                    "prompt_text": prompt_result.text if prompt_result else "",
                    "prompt_template": prompt_result.text if prompt_result else "",
                    # Store original definition without metadata headers (for UI display)
                    # This is the GPT output with "Ontologische categorie:" header removed
                    "definitie_origineel": definitie_zonder_header,
                    # Doorgeven van force_duplicate voor downstream repository
                    "force_duplicate": (
                        bool(
                            safe_dict_get(
                                sanitized_request.options, "force_duplicate", False
                            )
                        )
                        if getattr(sanitized_request, "options", None)
                        else False
                    ),
                },
            )

            # =====================================
            # PHASE 9: Storage (Conditional on Quality Gate)
            # =====================================
            # Opslag ONGEACHT scores: altijd opslaan (als draft/review) en ID teruggeven
            definition_id = await self._safe_save_definition(definition)
            logger.info(
                f"Generation {generation_id}: Definition saved (ID: {definition_id})"
            )
            try:
                if definition_id:
                    definition.id = int(definition_id)
            except Exception:  # pragma: no cover
                pass

            # Optioneel: sla mislukte poging ook op voor feedback‑learning
            if not safe_dict_get(validation_result, "is_acceptable", False):
                await self._save_failed_attempt(
                    definition, validation_result, generation_id
                )
                logger.warning(
                    f"Generation {generation_id}: Stored as saved definition and logged failed attempt for learning"
                )

            # =====================================
            # PHASE 10: Feedback Loop Update (GVI Rode Kabel)
            # =====================================
            if (
                not safe_dict_get(validation_result, "is_acceptable", False)
                and self.feedback_engine
            ):
                await self.feedback_engine.process_validation_feedback(
                    definition_id=generation_id,
                    validation_result=validation_result,
                    original_request=sanitized_request,
                )
                logger.info(
                    f"Generation {generation_id}: Feedback processed for future improvements"
                )

            # =====================================
            # PHASE 11: Monitoring & Metrics
            # =====================================
            if self.monitoring:
                # Ensure token_count is int or None
                token_count = getattr(generation_result, "tokens_used", None)
                if token_count is not None:
                    token_count = int(token_count)

                await self.monitoring.complete_generation(
                    generation_id=generation_id,
                    success=safe_dict_get(validation_result, "is_acceptable", False),
                    duration=time.time() - start_time,
                    token_count=token_count,
                    components_used=(
                        prompt_result.components_used if prompt_result else []
                    ),
                    had_feedback=bool(feedback_history),
                )

            # =====================================
            # FINAL RESPONSE CREATION
            # =====================================
            final_duration = time.time() - start_time
            logger.info(
                f"Generation {generation_id}: Complete in {final_duration:.2f}s, "
                f"valid={safe_dict_get(validation_result, 'is_acceptable', False)}"
            )

            return DefinitionResponseV2(
                success=True,
                definition=definition,
                validation_result=raw_validation,
                metadata={
                    "generation_id": generation_id,
                    "duration": final_duration,
                    "feedback_integrated": bool(feedback_history),
                    "ontological_category": sanitized_request.ontologische_categorie,
                    "orchestrator_version": "v2.0",
                    "phases_completed": 11,
                    "enhanced": was_enhanced,
                    # Web lookup status for transparency
                    "web_lookup_status": web_lookup_status,
                    "web_lookup_available": self.web_lookup_service is not None,
                    "web_sources_count": len(provenance_sources),
                    # Synonym enrichment status for transparency (Architecture v3.1)
                    "synonym_enrichment_status": synonym_enrichment_status,
                    "enriched_synonyms_count": len(enriched_synonyms),
                    "ai_pending_synonyms_count": ai_pending_count,
                },
            )

        except Exception as e:
            logger.error(f"Generation {generation_id} failed: {e!s}", exc_info=True)
            if self.monitoring:
                await self.monitoring.track_error(
                    generation_id, e, error_type=type(e).__name__
                )

            return DefinitionResponseV2(
                success=False,
                error=f"Generation failed: {e!s}",
                metadata={
                    "generation_id": generation_id,
                    "duration": time.time() - start_time,
                    "error_type": type(e).__name__,
                    "orchestrator_version": "v2.0",
                },
            )

    # =====================================
    # LEGACY INTERFACE COMPATIBILITY
    # =====================================

    # Note: Main create_definition method is already implemented above

    async def update_definition(
        self, definition_id: int, updates: dict[str, Any]
    ) -> DefinitionResponseV2:
        """Update definition - placeholder for future implementation."""
        _ = definition_id, updates  # Mark as used
        logger.warning("update_definition not yet implemented in V2")
        return DefinitionResponseV2(
            success=False,
            error="update_definition not yet implemented in V2 orchestrator",
        )

    async def validate_and_save(self, definition: Definition) -> DefinitionResponseV2:
        """Validate and save - placeholder for future implementation."""
        _ = definition  # Mark as used
        logger.warning("validate_and_save not yet implemented in V2")
        return DefinitionResponseV2(
            success=False,
            error="validate_and_save not yet implemented in V2 orchestrator",
        )

    # =====================================
    # PRIVATE HELPER METHODS
    # =====================================

    def _create_definition_object(
        self,
        request: GenerationRequest,
        text: str,
        validation_result: ValidationResult,
        generation_metadata: dict[str, Any],
    ) -> Definition:
        """Create definition object with all metadata."""
        return Definition(
            begrip=request.begrip,
            definitie=text,
            organisatorische_context=request.organisatorische_context or [],
            juridische_context=request.juridische_context or [],
            wettelijke_basis=request.wettelijke_basis or [],
            # EPIC-010: domein field verwijderd
            ontologische_categorie=request.ontologische_categorie,  # V2: Properly set
            categorie=request.ontologische_categorie,  # DEF-53 fix: explicit mapping to DB field
            ufo_categorie=getattr(request, "ufo_categorie", None),
            valid=safe_dict_get(validation_result, "is_acceptable", False),
            validation_violations=ensure_list(
                safe_dict_get(validation_result, "violations", [])
            ),
            metadata=generation_metadata,
            created_by=request.actor,
            created_at=datetime.now(UTC),
        )

    async def _safe_save_definition(self, definition: Definition) -> int | None:
        """
        Safely save definition with comprehensive error handling.

        Returns:
            Definition ID if successful, None if repository doesn't support save

        Raises:
            DuplicateDefinitionError: If definition already exists
            DatabaseConstraintError: If database constraints violated
            DatabaseConnectionError: If database unavailable
            RepositoryError: For other repository errors
        """
        # Check if repository supports save
        if not hasattr(self.repository, "save"):
            logger.error(
                f"Repository {type(self.repository).__name__} does not have save() method! "
                f"Available methods: {[m for m in dir(self.repository) if not m.startswith('_')]}"
            )
            return None

        # Log save attempt
        logger.info(
            f"Attempting to save definition: begrip='{definition.begrip}', "
            f"categorie={definition.categorie}, "
            f"ontologische_categorie={definition.ontologische_categorie}"
        )

        try:
            result = self.repository.save(definition)
            logger.info(
                f"Successfully saved definition '{definition.begrip}' with ID: {result}"
            )
            return result

        except DuplicateDefinitionError as e:
            logger.warning(
                f"Duplicate definition detected: {e.begrip}. "
                "User may want to update existing definition instead."
            )
            raise  # Let caller handle duplicate (may want to offer update option)

        except DatabaseConstraintError as e:
            logger.error(
                f"Database constraint violation for '{e.begrip}': "
                f"field='{e.field}', error={e}"
            )
            raise  # Critical error - should not happen after Fix 1

        except DatabaseConnectionError as e:
            logger.error(f"Database connection failed: {e.db_path}, error={e}")
            raise  # Infrastructure issue - needs immediate attention

        except RepositoryError as e:
            logger.error(f"Repository error during {e.operation}: {e}")
            raise  # Unexpected repository issue

        except Exception as e:
            # Catch any unexpected errors
            logger.exception(
                f"CRITICAL: Unexpected error saving '{definition.begrip}': {e!s}",
                exc_info=True,
            )
            raise RepositoryError(
                operation="save", begrip=definition.begrip, message=str(e)
            ) from e

    async def _save_failed_attempt(
        self,
        definition: Definition,
        validation_result: ValidationResult,
        generation_id: str,
    ):
        """Save failed attempt for feedback learning."""
        try:
            if hasattr(self.repository, "save_failed_attempt"):
                await self.repository.save_failed_attempt(
                    definition, validation_result, feedback_data=True
                )
            else:
                logger.debug("Repository does not support failed attempt tracking")
        except Exception as e:
            logger.error(f"Failed to save failed attempt: {e!s}")

    def _create_basic_prompt(self, request: GenerationRequest) -> str:
        """Create basic fallback prompt when prompt service unavailable."""
        ontological_hint = ""
        if request.ontologische_categorie:
            ontological_hint = f"\n\nDit begrip is een {request.ontologische_categorie}. Houd hier rekening mee in de definitie."

        return f"""Genereer een Nederlandse definitie voor het begrip: {request.begrip}

Context: {request.context or 'Geen specifieke context gegeven'}
# EPIC-010: domein field verwijderd - gebruik juridische_context
{ontological_hint}

Genereer een heldere, precieze definitie die voldoet aan Nederlandse kwaliteitseisen voor juridisch gebruik."""

    async def _generate_legacy_prompt(
        self,
        request: GenerationRequest,
        feedback_history: list | None,
        context: dict[str, Any] | None,
    ) -> "PromptResult":
        """Generate prompt using legacy services as fallback."""
        from services.interfaces import PromptResult

        basic_prompt = self._create_basic_prompt(request)

        return PromptResult(
            text=basic_prompt,
            token_count=len(basic_prompt.split()) * 1.3,  # Rough estimate
            components_used=["legacy_fallback"],
            feedback_integrated=False,
            optimization_applied=False,
            metadata={"fallback_reason": "prompt_service_unavailable"},
        )

    # =====================================
    # LEGACY SERVICE FALLBACKS
    # ====================================
