"""
PromptServiceV2 - Category-aware prompt generation service.

Connects existing advanced prompt systems to V2 orchestrator.
Fixes ontological category template selection bug.
"""

import logging
import time
from dataclasses import dataclass
from typing import Any

from services.definition_generator_config import UnifiedGeneratorConfig
from services.definition_generator_context import EnrichedContext
from services.definition_generator_prompts import UnifiedPromptBuilder
from services.interfaces import GenerationRequest

logger = logging.getLogger(__name__)


@dataclass
class PromptResult:
    """Enhanced prompt result with feedback integration."""

    text: str
    token_count: int
    components_used: list[str]
    feedback_integrated: bool
    optimization_applied: bool
    metadata: dict[str, Any]


@dataclass
class PromptServiceConfig:
    """Configuration for prompt service behavior."""

    max_token_limit: int = 10000  # Hard limit
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600
    feedback_integration: bool = True
    token_optimization: bool = True


class PromptServiceV2:
    """
    Next-generation prompt service with ontological category support.

    FIXES: Ontological category bug by using existing advanced template selection.
    Connects DefinitionGeneratorPrompts to V2 orchestrator.
    """

    def __init__(self, config: PromptServiceConfig = None):
        """Initialize with existing advanced prompt generator."""
        self.config = config or PromptServiceConfig()
        unified_config = UnifiedGeneratorConfig()
        self.prompt_generator = UnifiedPromptBuilder(unified_config)

    async def build_generation_prompt(
        self,
        request: GenerationRequest,
        feedback_history: list[dict] | None = None,
        context: dict[str, Any] | None = None,
    ) -> PromptResult:
        """
        Build intelligent prompt with ontological category support.

        FIXED: Now uses ontological category for proper template selection.
        """
        start_time = time.time()

        try:
            # Convert V2 request to enriched context for existing prompt generator
            enriched_context = self._convert_request_to_context(request, context)

            # Generate prompt using existing advanced system with category support
            prompt_text = self.prompt_generator.build_prompt(
                begrip=request.begrip, context=enriched_context
            )

            # Estimate token count
            token_count = len(prompt_text.split()) * 1.3  # Conservative estimate

            # Determine which components were used based on metadata
            components_used = ["base_template"]
            if request.ontologische_categorie:
                components_used.append(f"ontologische_{request.ontologische_categorie}")
            if enriched_context.metadata.get("juridisch_context"):
                components_used.append("juridisch_template")

            # Create result
            result = PromptResult(
                text=prompt_text,
                token_count=int(token_count),
                components_used=components_used,
                feedback_integrated=bool(feedback_history),
                optimization_applied=False,
                metadata={
                    "generation_time": time.time() - start_time,
                    "ontologische_categorie": request.ontologische_categorie,
                    "template_selected": enriched_context.metadata.get("template_used"),
                    "feedback_entries": (
                        len(feedback_history) if feedback_history else 0
                    ),
                },
            )

            logger.info(
                f"V2 Prompt built for '{request.begrip}': {result.token_count} tokens, "
                f"category={request.ontologische_categorie}, "
                f"components={result.components_used}"
            )

            return result

        except Exception as e:
            logger.error(
                f"V2 prompt generation failed for {request.begrip}: {e!s}",
                exc_info=True,
            )
            raise

    def _convert_request_to_context(
        self, request: GenerationRequest, extra_context: dict[str, Any] | None = None
    ) -> EnrichedContext:
        """Convert V2 GenerationRequest to EnrichedContext for existing prompt system."""

        # Build base context from request
        base_context = {}

        if request.context:
            # Parse organisational context
            base_context["organisatorisch"] = [request.context]

        if request.domein:
            # Parse domain context
            base_context["domein"] = [request.domein]

        # 🚨 CRITICAL FIX: Preserve context_dict from extra_context
        # This fixes the voorbeelden dictionary regression
        if extra_context and "context_dict" in extra_context:
            context_dict = extra_context["context_dict"]
            logger.debug(
                f"Preserving context_dict with keys: {list(context_dict.keys())}"
            )

            # Merge context_dict into base_context (prioritize context_dict)
            for key, value in context_dict.items():
                if isinstance(value, list) and value:  # Only add non-empty lists
                    base_context[key] = value
                    logger.debug(f"Added context_dict[{key}] = {value}")

        # Create sources list (empty for now, could be extended)
        sources = []

        # Build metadata with ontological category
        metadata = {
            "ontologische_categorie": request.ontologische_categorie,
            "semantic_category": request.ontologische_categorie,  # For template module compatibility
            "request_id": request.id,
            "actor": request.actor,
            "legal_basis": request.legal_basis,
        }

        if extra_context:
            # Add all extra_context to metadata (including context_dict for reference)
            metadata.update(extra_context)

        # Create enriched context
        enriched = EnrichedContext(
            base_context=base_context,
            sources=sources,
            expanded_terms={},  # Could be extended with abbreviation expansion
            confidence_scores={},
            metadata=metadata,
        )

        logger.info(
            f"EnrichedContext created with base_context keys: {list(base_context.keys())}"
        )
        return enriched
