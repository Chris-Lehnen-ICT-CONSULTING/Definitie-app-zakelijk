"""
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
from typing import Any, Optional

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

logger = logging.getLogger(__name__)


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
        prompt_service: "PromptServiceV2",
        ai_service: "IntelligentAIService",
        validation_service: "ValidationOrchestratorInterface",
        cleaning_service: "CleaningServiceInterface",
        repository: "DefinitionRepositoryInterface",
        # Optional services
        enhancement_service: Optional["EnhancementService"] = None,
        security_service: Optional["SecurityService"] = None,
        monitoring: Optional["MonitoringService"] = None,
        feedback_engine: Optional["FeedbackEngine"] = None,
        # Configuration
        config: OrchestratorConfig | None = None,
        # Web lookup (Epic 3)
        web_lookup_service: Optional["WebLookupServiceInterface"] = None,
    ):
        """
        Clean dependency injection - no session state access.

        All core services are required for V2-only operation.
        """
        # V2 Services (required)
        if not prompt_service:
            raise ValueError("PromptServiceV2 is required")
        if not ai_service:
            raise ValueError("AIServiceInterface is required")
        if not validation_service:
            raise ValueError("ValidationOrchestratorInterface is required")
        if not cleaning_service:
            raise ValueError("CleaningServiceInterface is required")
        if not repository:
            raise ValueError("DefinitionRepositoryInterface is required")

        self.prompt_service = prompt_service
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

        logger.info(
            "DefinitionOrchestratorV2 initialized with configuration: "
            f"feedback_loop={self.config.enable_feedback_loop}, "
            f"enhancement={self.config.enable_enhancement}, "
            f"caching={self.config.enable_caching}"
        )

    async def create_definition(
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
            # PHASE 2.5: Web Lookup Context Enrichment (Epic 3)
            # =====================================
            provenance_sources = []
            if (
                getattr(self.config, "enable_web_lookup", True)
                and self.web_lookup_service
            ):
                try:
                    from services.interfaces import LookupRequest
                    from services.web_lookup.provenance import build_provenance

                    lookup_request = LookupRequest(
                        term=sanitized_request.begrip,
                        sources=None,
                        max_results=5,
                        include_examples=False,
                        timeout=self.config.timeout_seconds,
                    )

                    web_results = await self.web_lookup_service.lookup(lookup_request)

                    # Build provenance records
                    # Convert LookupResults to minimal dicts expected by build_provenance
                    prepared = []
                    for r in web_results or []:
                        prepared.append(
                            {
                                "provider": r.source.name.lower(),
                                "title": (
                                    r.metadata.get("dc_title")
                                    if isinstance(r.metadata, dict)
                                    else None
                                )
                                or r.source.name,
                                "url": r.source.url,
                                "snippet": r.definition or r.context or "",
                                "score": float(r.source.confidence or 0.0),
                                "used_in_prompt": False,
                                "retrieved_at": (
                                    r.metadata.get("retrieved_at")
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
                    }
                    logger.info(
                        f"Generation {generation_id}: Web lookup enriched context with {len(provenance_sources)} sources"
                    )
                except Exception as e:
                    logger.warning(
                        f"Generation {generation_id}: Web lookup enrichment failed: {e!s}"
                    )

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
            generation_result = await self.ai_service.generate_definition(
                prompt=prompt_result.text,
                temperature=(
                    sanitized_request.options.get("temperature", 0.7)
                    if sanitized_request.options
                    else 0.7
                ),
                max_tokens=(
                    sanitized_request.options.get("max_tokens", 500)
                    if sanitized_request.options
                    else 500
                ),
                model=(
                    sanitized_request.options.get("model")
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
                from voorbeelden import genereer_alle_voorbeelden

                # Build context_dict for voorbeelden generation
                voorbeelden_context = {
                    "organisatorisch": (
                        [sanitized_request.context] if sanitized_request.context else []
                    ),
                    "juridisch": (
                        context.get("context_dict", {}).get("juridisch", [])
                        if context
                        else []
                    ),
                    "wettelijk": (
                        context.get("context_dict", {}).get("wettelijk", [])
                        if context
                        else []
                    ),
                }

                # Generate voorbeelden using the cleaned text
                voorbeelden = genereer_alle_voorbeelden(
                    begrip=sanitized_request.begrip,
                    definitie=(
                        generation_result.text
                        if hasattr(generation_result, "text")
                        else str(generation_result)
                    ),
                    context_dict=voorbeelden_context,
                )
                logger.info(
                    f"Generation {generation_id}: Voorbeelden generated ({len(voorbeelden)} types)"
                )
            except Exception as e:
                logger.warning(
                    f"Generation {generation_id}: Voorbeelden generation failed: {e}"
                )
                # Continue without voorbeelden

            # =====================================
            # PHASE 6: Text Cleaning & Normalization
            # =====================================
            # V2 cleaning service (always available through adapter)
            cleaning_result = await self.cleaning_service.clean_text(
                (
                    generation_result.text
                    if hasattr(generation_result, "text")
                    else str(generation_result)
                ),
                sanitized_request.begrip,
            )
            cleaned_text = cleaning_result.cleaned_text
            logger.info(f"Generation {generation_id}: Text cleaned with V2 service")

            # =====================================
            # PHASE 6: Validation
            # =====================================
            # Use ValidationOrchestratorInterface.validate_text
            from services.validation.interfaces import ValidationContext

            validation_context = ValidationContext(
                correlation_id=uuid.UUID(generation_id),
                metadata={"generation_id": generation_id},
            )
            validation_result = await self.validation_service.validate_text(
                begrip=sanitized_request.begrip,
                text=cleaned_text,
                ontologische_categorie=sanitized_request.ontologische_categorie,
                context=validation_context,
            )

            logger.info(
                f"Generation {generation_id}: Validation complete (valid: {validation_result.get('is_acceptable', False)})"
            )

            # =====================================
            # PHASE 7: Enhancement (if validation failed and enabled)
            # =====================================
            was_enhanced = False
            if (
                not validation_result.get("is_acceptable", False)
                and self.config.enable_enhancement
                and self.enhancement_service
            ):
                enhanced_text = await self.enhancement_service.enhance_definition(
                    cleaned_text,
                    validation_result.get("violations", []),
                    context=sanitized_request,
                )

                # Re-validate enhanced text with new context
                enhanced_context = ValidationContext(
                    correlation_id=uuid.UUID(generation_id),
                    metadata={"generation_id": generation_id, "enhanced": True},
                )
                validation_result = await self.validation_service.validate_text(
                    begrip=sanitized_request.begrip,
                    text=enhanced_text,
                    ontologische_categorie=sanitized_request.ontologische_categorie,
                    context=enhanced_context,
                )

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
                    # Epic 3: provenance sources (MVP, no DB schema changes)
                    "sources": provenance_sources,
                },
            )

            # =====================================
            # PHASE 9: Storage (Conditional on Quality Gate)
            # =====================================
            definition_id = None
            if validation_result.get("is_acceptable", False):
                definition_id = await self._safe_save_definition(definition)
                logger.info(
                    f"Generation {generation_id}: Definition saved (ID: {definition_id})"
                )
            else:
                # Store failed attempts for feedback learning
                await self._save_failed_attempt(
                    definition, validation_result, generation_id
                )
                logger.warning(
                    f"Generation {generation_id}: Failed attempt stored for feedback learning"
                )

            # =====================================
            # PHASE 10: Feedback Loop Update (GVI Rode Kabel)
            # =====================================
            if (
                not validation_result.get("is_acceptable", False)
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
                    success=validation_result.get("is_acceptable", False),
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
                f"valid={validation_result.get('is_acceptable', False)}"
            )

            return DefinitionResponseV2(
                success=True,
                definition=definition,
                validation_result=validation_result,
                metadata={
                    "generation_id": generation_id,
                    "duration": final_duration,
                    "feedback_integrated": bool(feedback_history),
                    "ontological_category": sanitized_request.ontologische_categorie,
                    "orchestrator_version": "v2.0",
                    "phases_completed": 11,
                    "enhanced": was_enhanced,
                    "prompt_text": prompt_result.text,  # Add prompt text for UI display
                    "voorbeelden": voorbeelden,  # Add generated voorbeelden
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
            context=request.context,
            domein=request.domein,
            ontologische_categorie=request.ontologische_categorie,  # V2: Properly set
            valid=validation_result.get("is_acceptable", False),
            validation_violations=validation_result.get("violations", []),
            metadata=generation_metadata,
            created_by=request.actor,
            created_at=datetime.now(UTC),
        )

    async def _safe_save_definition(self, definition: Definition) -> int | None:
        """Safely save definition with error handling."""
        try:
            if hasattr(self.repository, "save"):
                return self.repository.save(definition)
            logger.warning("Repository does not support save operation")
            return None
        except Exception as e:
            logger.error(f"Failed to save definition: {e!s}")
            return None

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
Domein: {request.domein or 'Algemeen'}
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
    # =====================================

    def _get_legacy_ai_service(self):
        """Get legacy AI service as fallback."""
        try:
            # Use the same AI service as the legacy orchestrator
            class LegacyAIAdapter:
                async def generate_definition(
                    self,
                    prompt: str,
                    temperature: float = 0.7,
                    max_tokens: int = 500,
                    model: str | None = None,
                ):
                    """Use services.ai_service.AIService"""
                    from services.ai_service import get_ai_service
                    from config.config_manager import get_default_model, get_default_temperature
                    
                    # Use central config for defaults
                    if model is None:
                        model = get_default_model()
                    if temperature is None:
                        temperature = get_default_temperature()

                    class MockResponse:
                        def __init__(self, text):
                            self.text = text
                            self.model = model
                            self.tokens_used = len(text.split()) * 1.3  # Rough estimate

                    ai_service = get_ai_service()
                    response_text = ai_service.generate_definition(
                        prompt=prompt,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        model=model,
                    )

                    return MockResponse(response_text)

            return LegacyAIAdapter()
        except ImportError as e:
            logger.warning(f"Legacy AI service not available: {e}")
            return None

    def _get_legacy_validation_service(self):
        """Get legacy validation service as fallback."""
        try:
            # Create a simple validation adapter that works
            class SimpleValidationAdapter:
                def validate(self, definition):
                    """Simple validation that always passes for testing."""
                    from services.interfaces import ValidationResult

                    # Basic length check
                    is_valid = len(definition.definitie) > 10
                    score = 0.8 if is_valid else 0.3

                    return ValidationResult(
                        is_valid=is_valid,
                        definition_text=definition.definitie,
                        score=score,
                        errors=[] if is_valid else ["Definitie te kort"],
                        warnings=[],
                        suggestions=[],
                    )

            return SimpleValidationAdapter()
        except Exception as e:
            logger.warning(f"Legacy validation service not available: {e}")
            return None

    def _get_legacy_cleaning_service(self):
        """Get legacy cleaning service as fallback."""
        try:
            # Simple cleaning adapter
            class SimpleCleaningAdapter:
                def clean_text(self, text: str, term: str):
                    """Simple text cleaning."""
                    from services.interfaces import CleaningResult

                    # Basic cleaning: strip whitespace and normalize
                    cleaned = text.strip()
                    if not cleaned.endswith("."):
                        cleaned += "."

                    was_cleaned = cleaned != text

                    return CleaningResult(
                        original_text=text,
                        cleaned_text=cleaned,
                        was_cleaned=was_cleaned,
                        applied_rules=["normalize_punctuation"] if was_cleaned else [],
                        improvements=["Added period"] if was_cleaned else [],
                    )

                async def clean_definition(self, text: str):
                    """Legacy async interface."""
                    return self.clean_text(text, "").cleaned_text

            return SimpleCleaningAdapter()
        except Exception as e:
            logger.warning(f"Legacy cleaning service not available: {e}")
            return None

    def _get_legacy_repository(self):
        """Get legacy repository as fallback."""
        try:
            from services.definition_repository import DefinitionRepository

            return DefinitionRepository("data/definities.db")
        except ImportError:
            logger.warning("Legacy repository not available")
            return None
