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
from datetime import datetime, timezone
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
            # PHASE 5: Text Cleaning & Normalization
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
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "orchestrator_version": "v2.0",
                    "ontological_category_used": sanitized_request.ontologische_categorie,
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
            created_at=datetime.now(timezone.utc),
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
