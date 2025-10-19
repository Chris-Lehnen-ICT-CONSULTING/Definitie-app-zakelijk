"""
PromptServiceV2 - Category-aware prompt generation service.

Connects existing advanced prompt systems to V2 orchestrator.
Fixes ontological category template selection bug.
REFACTORED: Now uses centralized ContextManager (US-043).
"""

import logging
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any

from services.definition_generator_config import ContextConfig, UnifiedGeneratorConfig
from services.definition_generator_context import EnrichedContext, HybridContextManager
from services.definition_generator_prompts import UnifiedPromptBuilder
from services.interfaces import GenerationRequest
from services.web_lookup.config_loader import load_web_lookup_config
from services.web_lookup.sanitization import sanitize_snippet
from utils.type_helpers import ensure_string

logger = logging.getLogger(__name__)

# US-041: Feature flag for context v2 mapping
CONTEXT_V2_ENABLED = os.getenv("CONTEXT_V2_ENABLED", "false").lower() == "true"
# US-043: Use centralized context manager
USE_CONTEXT_MANAGER = os.getenv("USE_CONTEXT_MANAGER", "true").lower() == "true"


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

        # US-043: Initialize HybridContextManager for single context entry point
        # enable_web_lookup is removed; web lookup runs automatically when available
        context_config = ContextConfig(
            enable_rule_interpretation=False,  # Can be enabled later
            context_abbreviations={},
        )
        self.context_manager = HybridContextManager(context_config)

        # Load prompt augmentation config (Epic 3)
        try:
            wl_cfg = load_web_lookup_config().get("web_lookup", {})
            self._aug_cfg = wl_cfg.get("prompt_augmentation", {})
        except Exception:
            self._aug_cfg = {}

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
            # US-043: Use HybridContextManager as single context entry point
            # Build enriched context through the unified manager
            enriched_context = await self.context_manager.build_enriched_context(
                request
            )

            # Merge any additional context from orchestrator (e.g., web_lookup)
            if context:
                # Add web_lookup data to metadata if present
                if "web_lookup" in context:
                    enriched_context.metadata["web_lookup"] = context["web_lookup"]
                # Add any other context fields to metadata
                for key, value in context.items():
                    if key not in enriched_context.metadata:
                        enriched_context.metadata[key] = value

            # US-179: Ensure ontological category is present in prompt metadata
            # so SemanticCategorisationModule and TemplateModule can apply
            # category-specific guidance and templates.
            if request.ontologische_categorie and isinstance(
                request.ontologische_categorie, str
            ):
                cat = request.ontologische_categorie.strip().lower()
                enriched_context.metadata["ontologische_categorie"] = cat

                # Minimal mapping from ESS category → template semantic category
                # Proces → "Proces"; type/exemplaar → "Object"; resultaat → "Maatregel"
                mapping = {
                    "proces": "Proces",
                    "activiteit": "Proces",
                    "type": "Object",
                    "soort": "Object",
                    "exemplaar": "Object",
                    "particulier": "Object",
                    "resultaat": "Maatregel",
                    "uitkomst": "Maatregel",
                }
                semantic = mapping.get(cat)
                if semantic and "semantic_category" not in enriched_context.metadata:
                    enriched_context.metadata["semantic_category"] = semantic

            # Generate prompt using existing advanced system with category support
            prompt_text = self.prompt_generator.build_prompt(
                begrip=request.begrip, context=enriched_context
            )

            # Epic 3: Optional prompt augmentation with web lookup context
            prompt_text = self._maybe_augment_with_web_context(
                prompt_text, enriched_context
            )

            # EPIC-018/US-229: Optional document snippets injectie
            prompt_text = self._maybe_augment_with_document_snippets(
                prompt_text, enriched_context
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

    def _maybe_augment_with_document_snippets(
        self, prompt_text: str, enriched_context: EnrichedContext
    ) -> str:
        """Voeg (optionele) document‑snippets toe aan de prompt.

        Besturing via env‑vars:
        - DOCUMENT_SNIPPETS_ENABLED (default: true)
        - DOCUMENT_SNIPPETS_MAX (default: 2)
        - DOCUMENT_SNIPPETS_MAX_CHARS (default: 800)
        """
        try:
            enabled = os.getenv("DOCUMENT_SNIPPETS_ENABLED", "true").lower() == "true"
            if not enabled:
                return prompt_text

            docs_meta = (enriched_context.metadata or {}).get("documents", {})
            snippets = (docs_meta or {}).get("snippets", [])
            if not snippets:
                return prompt_text

            try:
                max_snippets = int(os.getenv("DOCUMENT_SNIPPETS_MAX", "16"))
            except Exception:
                max_snippets = 16
            try:
                max_chars = int(os.getenv("DOCUMENT_SNIPPETS_MAX_CHARS", "800"))
            except Exception:
                max_chars = 800

            lines: list[str] = ["📄 DOCUMENTCONTEXT (snippets):"]
            total = 0
            count = 0
            for s in snippets:
                if count >= max_snippets:
                    break
                raw = ensure_string(s.get("snippet", ""))
                title = s.get("title") or s.get("filename") or "document"
                cite = s.get("citation_label")
                safe = sanitize_snippet(raw)
                remaining = max(0, max_chars - total)
                if remaining <= 0:
                    break
                snippet_text = safe[:remaining]
                # Note: we prefix with a bullet for readability
                prefix = f"• {title}"
                if cite:
                    prefix += f" ({cite})"
                lines.append(f"{prefix}: {snippet_text}")
                total += len(snippet_text)
                count += 1

            if len(lines) <= 1:
                return prompt_text

            block = "\n".join(lines)
            # Voeg bovenaan toe (context eerst)
            return f"{block}\n\n{prompt_text}"
        except Exception:
            return prompt_text

    def _DEPRECATED_convert_request_to_context(
        self, request: GenerationRequest, extra_context: dict[str, Any] | None = None
    ) -> EnrichedContext:
        """DEPRECATED: Use HybridContextManager.build_enriched_context() instead.

        This method is deprecated as of US-043. It violates the single context
        entry point principle. All context mapping should go through
        HybridContextManager.

        Legacy method for converting V2 GenerationRequest to EnrichedContext.
        """
        import warnings

        warnings.warn(
            "_convert_request_to_context is deprecated. Use HybridContextManager.build_enriched_context() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        # Generate correlation ID for audit trail (ASTRA compliance)
        correlation_id = str(uuid.uuid4())

        # Build base context from request (PER-007: volledige mapping met dedupe)
        base_context: dict[str, list[str]] = {
            "organisatorisch": [],
            "juridisch": [],
            "wettelijk": [],
            # US-041 FIX: Also maintain original field names for compatibility
            "organisatorische_context": [],
            "juridische_context": [],
            "wettelijke_basis": [],
        }

        def extend_unique(values: list[str] | None, into: list[str]) -> None:
            if not values:
                return
            seen = set(into)
            for v in values:
                if v and v not in seen:
                    into.append(v)
                    seen.add(v)

        # Expliciete UI-velden - US-041 FIX: Map to BOTH shortened and full names
        organisatorische = getattr(request, "organisatorische_context", None)
        juridische = getattr(request, "juridische_context", None)
        wettelijke = getattr(request, "wettelijke_basis", None)

        # Feature flag check for enhanced mapping
        if CONTEXT_V2_ENABLED:
            logger.info(
                f"[AUDIT] Context V2 mapping ENABLED | "
                f"correlation_id={correlation_id} | "
                f"begrip={request.begrip} | "
                f"request_id={request.id}"
            )

            # Enhanced mapping with validation
            if organisatorische and not isinstance(organisatorische, list):
                organisatorische = [organisatorische] if organisatorische else []
                logger.warning(
                    f"[AUDIT] Converted non-list organisatorische_context to list | correlation_id={correlation_id}"
                )

            if juridische and not isinstance(juridische, list):
                juridische = [juridische] if juridische else []
                logger.warning(
                    f"[AUDIT] Converted non-list juridische_context to list | correlation_id={correlation_id}"
                )

            if wettelijke and not isinstance(wettelijke, list):
                wettelijke = [wettelijke] if wettelijke else []
                logger.warning(
                    f"[AUDIT] Converted non-list wettelijke_basis to list | correlation_id={correlation_id}"
                )

        # Map to shortened keys (for existing modules)
        extend_unique(organisatorische, base_context["organisatorisch"])
        extend_unique(juridische, base_context["juridisch"])
        extend_unique(wettelijke, base_context["wettelijk"])

        # US-041 FIX: Also map to full keys (for new modules and debugging)
        extend_unique(organisatorische, base_context["organisatorische_context"])
        extend_unique(juridische, base_context["juridische_context"])
        extend_unique(wettelijke, base_context["wettelijke_basis"])

        # Audit logging for ASTRA compliance (no PII)
        if organisatorische or juridische or wettelijke:
            logger.info(
                f"[AUDIT] Context mapping completed | "
                f"correlation_id={correlation_id} | "
                f"org_count={len(organisatorische) if organisatorische else 0} | "
                f"jur_count={len(juridische) if juridische else 0} | "
                f"wet_count={len(wettelijke) if wettelijke else 0} | "
                f"feature_flag={CONTEXT_V2_ENABLED}"
            )

        # Legacy velden
        # EPIC-010: domein field verwijderd - gebruik juridische_context
        # Gebruik legacy vrije context enkel als de nieuwe velden leeg zijn
        # EPIC-010: Do not fallback to legacy string request.context
        # All context must be provided via the list fields above.

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
            "correlation_id": correlation_id,  # US-041: ASTRA audit trail
            "context_v2_enabled": CONTEXT_V2_ENABLED,  # US-041: Feature flag status
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

    # ==============================
    # Epic 3: Prompt Augmentation
    # ==============================
    def build_prompt(self, request: GenerationRequest) -> str:
        """Sync wrapper verwijderd. Gebruik build_generation_prompt (async) via UI async_bridge."""
        msg = (
            "build_prompt (sync) is verwijderd. Gebruik de async methode "
            "build_generation_prompt vanuit de UI via ui.helpers.async_bridge.run_async"
        )
        raise NotImplementedError(msg)

    def _maybe_augment_with_web_context(  # noqa: PLR0911, PLR0915
        self, prompt_text: str, enriched_context: EnrichedContext
    ) -> str:
        try:
            aug = self._aug_cfg or {}
            if not aug.get("enabled", False):
                logger.info("Prompt augmentation disabled by config; skipping")
                return prompt_text

            web_ctx = (
                enriched_context.metadata.get("web_lookup")
                if enriched_context and enriched_context.metadata
                else None
            )
            if not web_ctx or not isinstance(web_ctx, dict):
                logger.info("No web_lookup context found; skipping prompt augmentation")
                return prompt_text

            sources = web_ctx.get("sources") or []
            if not sources:
                logger.info(
                    "No web_lookup sources available; skipping prompt augmentation"
                )
                return prompt_text

            # Select items: if include_all_hits, ignore used_in_prompt and take all
            def _is_auth(src: dict) -> bool:
                prov = (src.get("provider") or "").lower()
                url = (src.get("url") or "").lower()
                return any(x in prov or x in url for x in ("overheid", "rechtspraak"))

            include_all = bool(aug.get("include_all_hits", False))
            if include_all:
                selected = list(sources)
            else:
                used = [s for s in sources if s.get("used_in_prompt")]
                # Fallback: use first N sources if nothing marked
                selected = used if used else sources

            if aug.get("prioritize_juridical", True):
                # Stable sort: authoritative first, then score desc, then title/url
                selected = sorted(
                    selected,
                    key=lambda s: (
                        int(_is_auth(s))
                        * -1,  # False comes after True when multiplied by -1
                        -(float(s.get("score", 0.0) or 0.0)),
                        str(s.get("title", "")),
                        str(s.get("url", "")),
                    ),
                )
            logger.info(
                "Prompt augmentation selection: total_sources=%s, selected_for_consideration=%s",
                len(sources),
                len(selected),
            )

            # Token budget & snippet length management
            max_snippets = int(aug.get("max_snippets", 3))
            max_tokens_per_snippet = int(aug.get("max_tokens_per_snippet", 100))
            total_budget = int(aug.get("total_token_budget", 400))

            # If include_all_hits, relax snippet/budget constraints to allow all
            if include_all:
                try:
                    max_snippets = max(max_snippets, len(selected))
                except Exception:
                    max_snippets = len(selected)
                # Set a generous budget to avoid early truncation; final model limits still apply
                total_budget = max(total_budget, 5000)

            def approx_tokens(s: str) -> int:
                return max(1, (len(s) + 3) // 4)

            def truncate_to_tokens(s: str, limit: int) -> str:
                # Convert tokens to char budget
                char_limit = max(1, limit * 4)
                if len(s) <= char_limit:
                    return s
                # Truncate on word boundary near limit
                cut = s[:char_limit]
                last_space = cut.rfind(" ")
                if last_space > 20:
                    cut = cut[:last_space]
                return cut

            header = aug.get("section_header", "### Contextinformatie uit bronnen:")
            position = aug.get("position", "after_context")

            injected_lines = []
            injected_lines.append(header)
            tokens_used = 0
            added = 0

            for _idx, src in enumerate(selected):
                if added >= max_snippets:
                    break
                raw = src.get("snippet") or ""
                safe = sanitize_snippet(raw, max_length=2000)
                safe = truncate_to_tokens(safe, max_tokens_per_snippet)
                est = approx_tokens(safe)
                if tokens_used + est > total_budget:
                    break
                # STORY 3.1: Use provider-neutral "Bron X" format
                label = f"Bron {added + 1}"
                injected_lines.append(f"- {label}: {safe}")
                tokens_used += est
                added += 1

            if added == 0:
                logger.info(
                    "Prompt augmentation produced no snippets within budget (total_budget=%s, per_snippet=%s)",
                    total_budget,
                    max_tokens_per_snippet,
                )
                return prompt_text

            block = "\n".join(injected_lines)
            logger.info(
                "Prompt augmentation added %s snippet(s), approx_tokens=%s, position=%s",
                added,
                tokens_used,
                position,
            )
            if position == "prepend":
                return f"{block}\n\n{prompt_text}"
            # Default append behavior for after_context/before_examples
            return f"{prompt_text}\n\n{block}"

        except Exception:
            # Fail-safe: do not break generation if augmentation fails
            return prompt_text
