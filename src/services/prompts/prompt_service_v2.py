"""
PromptServiceV2 - Category-aware prompt generation service.

Connects existing advanced prompt systems to V2 orchestrator.
Fixes ontological category template selection bug.
REFACTORED: Now uses centralized ContextManager (US-043).
"""

import logging
import os
import time
from dataclasses import dataclass
from typing import Any

from services.definition_generator_config import ContextConfig, UnifiedGeneratorConfig
from services.definition_generator_context import (
    EnrichedContext,
    HybridContextManager,
)
from services.definition_generator_prompts import UnifiedPromptBuilder
from services.interfaces import GenerationRequest
from services.web_lookup.config_loader import load_web_lookup_config
from services.web_lookup.sanitization import sanitize_snippet
from utils.type_helpers import ensure_string
from utils.xml_source_formatter import format_bron, wrap_bronnen

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
    components_used: tuple[str, ...]
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

    def __init__(self, config: PromptServiceConfig | None = None):
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

            # DEF-315: Collect all sources (RAG + web + document) in one <bronnen> block
            prompt_text = self._collect_and_inject_bronnen(
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
                components_used=tuple(components_used),  # frozen dataclass needs tuple
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

    # ==============================
    # DEF-315: XML source formatting
    # ==============================

    def _collect_and_inject_bronnen(
        self, prompt_text: str, enriched_context: EnrichedContext
    ) -> str:
        """Verzamel alle bronnen (RAG + web + document) in één <bronnen> blok."""
        try:
            all_brons: list[str] = []
            nr_offset = 0

            # 1. RAG bronnen (from enriched_context.metadata)
            rag_chunks = (enriched_context.metadata or {}).get("rag_chunks", [])
            for chunk in rag_chunks:
                nr_offset += 1
                all_brons.append(
                    format_bron(
                        nr=nr_offset,
                        type="rag",
                        chunk_text=chunk.get("chunk_text", ""),
                        score=chunk.get("score"),
                        confidence=chunk.get("score"),
                        rechtsgebied=chunk.get("rechtsgebied"),
                        regeling=chunk.get("wet_regeling"),
                        artikel=chunk.get("artikel_lid"),
                    )
                )

            # 2. Web bronnen
            web_brons = self._collect_web_brons(enriched_context, nr_offset)
            nr_offset += len(web_brons)
            all_brons.extend(web_brons)

            # 3. Document bronnen
            doc_brons = self._collect_document_brons(enriched_context, nr_offset)
            all_brons.extend(doc_brons)

            if not all_brons:
                return prompt_text

            block = wrap_bronnen(all_brons)
            return f"{prompt_text}\n\n{block}"

        except Exception:
            # Fail-safe: do not break generation if source collection fails
            logger.warning(
                "Source collection failed; returning original prompt", exc_info=True
            )
            return prompt_text

    def _collect_document_brons(
        self, enriched_context: EnrichedContext, nr_offset: int
    ) -> list[str]:
        """Collect document snippets as XML <bron type="document"> strings.

        Besturing via env-vars:
        - DOCUMENT_SNIPPETS_ENABLED (default: true)
        - DOCUMENT_SNIPPETS_MAX (default: 16)
        - DOCUMENT_SNIPPETS_MAX_CHARS (default: 800)
        """
        try:
            enabled = os.getenv("DOCUMENT_SNIPPETS_ENABLED", "true").lower() == "true"
            if not enabled:
                return []

            docs_meta = (enriched_context.metadata or {}).get("documents", {})
            snippets = (docs_meta or {}).get("snippets", [])
            if not snippets:
                return []

            try:
                max_snippets = int(os.getenv("DOCUMENT_SNIPPETS_MAX", "16"))
            except Exception:
                max_snippets = 16
            try:
                max_chars = int(os.getenv("DOCUMENT_SNIPPETS_MAX_CHARS", "800"))
            except Exception:
                max_chars = 800

            brons: list[str] = []
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

                brons.append(
                    format_bron(
                        nr=nr_offset + count + 1,
                        type="document",
                        chunk_text=snippet_text,
                        confidence=0.70,
                        titel=title,
                        citatie=cite or "",
                    )
                )
                total += len(snippet_text)
                count += 1

            return brons
        except (KeyError, TypeError, AttributeError):
            # DEF-246: Snippet collection failed, return empty list
            return []

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

    def _collect_web_brons(
        self, enriched_context: EnrichedContext, nr_offset: int
    ) -> list[str]:
        """Collect web lookup sources as XML <bron type="web"> strings.

        Keeps all existing selection, sorting, sanitization and budget logic.
        Returns a list of formatted <bron> strings instead of modifying prompt text.
        """
        try:
            aug = self._aug_cfg or {}
            if not aug.get("enabled", False):
                logger.info("Prompt augmentation disabled by config; skipping")
                return []

            web_ctx = (
                enriched_context.metadata.get("web_lookup")
                if enriched_context and enriched_context.metadata
                else None
            )
            if not web_ctx or not isinstance(web_ctx, dict):
                logger.info("No web_lookup context found; skipping prompt augmentation")
                return []

            sources = web_ctx.get("sources") or []
            if not sources:
                logger.info(
                    "No web_lookup sources available; skipping prompt augmentation"
                )
                return []

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

            brons: list[str] = []
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

                # DEF-315: Extract legal metadata from source
                legal = src.get("legal", {}) or {}

                brons.append(
                    format_bron(
                        nr=nr_offset + added + 1,
                        type="web",
                        chunk_text=safe,
                        score=float(src.get("score", 0.0) or 0.0),
                        confidence=float(src.get("score", 0.0) or 0.0),
                        provider=src.get("provider", ""),
                        url=src.get("url", ""),
                        ecli=legal.get("ecli", ""),
                        wet=legal.get("law", ""),
                        artikel=legal.get("article", ""),
                        citatie=legal.get("citation_text", ""),
                    )
                )
                tokens_used += est
                added += 1

            if added == 0:
                logger.info(
                    "Prompt augmentation produced no snippets within budget (total_budget=%s, per_snippet=%s)",
                    total_budget,
                    max_tokens_per_snippet,
                )
                return []

            logger.info(
                "Prompt augmentation collected %s web bron(s), approx_tokens=%s",
                added,
                tokens_used,
            )
            return brons

        except Exception:
            # Fail-safe: do not break generation if augmentation fails
            return []
