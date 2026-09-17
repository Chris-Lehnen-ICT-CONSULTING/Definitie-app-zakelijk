"""
PromptServiceV2 - Category-aware prompt generation service.

Connects existing advanced prompt systems to V2 orchestrator.
Fixes ontological category template selection bug.
REFACTORED: Now uses centralized ContextManager (US-043).
"""

import hashlib
import html
import logging
import os
import time
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, TypedDict

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

# DEF-743: kwitantie van het feitelijke brongebruik in de prompt.
# Contract: /tmp/DEF-743-prompt-contract.md → PromptResult.metadata["source_receipt"].
# v2: elk gebruikt én weggelaten record draagt (source_type, input_index) en
# original_content_hash van de OORSPRONKELIJKE passage — vóór sanitisatie,
# truncatie, selectie en sortering — zodat gelijke IDs, ontbrekende IDs,
# gelijke afgekapte prefixen en omgekeerde volgorde onderscheidbaar blijven.
SOURCE_RECEIPT_VERSION = "2"
_SOURCE_CHANNELS = ("rag", "web", "document")
# Identiteitsvelden die ongewijzigd uit de invoer worden overgenomen — alleen
# als ze aanwezig en niet None zijn. Niets wordt afgeleid of verzonnen.
_RAG_IDENTITY_KEYS = (
    "chunk_id",
    "document_id",
    "chunk_index",
    "created_at",
    "filename",
    "bron_type",
    "rechtsgebied",
    "wet_regeling",
    "artikel_lid",
)
_WEB_IDENTITY_KEYS = ("provider", "url", "title", "source_label", "retrieved_at")
_DOC_IDENTITY_KEYS = (
    "doc_id",
    "filename",
    "title",
    "citation_label",
    "selection_basis",
    "url",
)


def _identity(
    src: dict[str, Any], keys: tuple[str, ...], nested: tuple[str, ...] = ()
) -> dict[str, Any]:
    """Kopieer alleen aanwezige, niet-None identiteitsvelden; geneste dicts diep."""
    ident: dict[str, Any] = {k: src[k] for k in keys if src.get(k) is not None}
    for key in nested:
        if isinstance(src.get(key), dict):
            ident[key] = deepcopy(src[key])
    return ident


def _retrieval_score(value: Any) -> float | None:
    """Zoekscore zoals aangeleverd, of None. Nooit een verzonnen 0.00."""
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _content_hash(content: str) -> str:
    return "sha256:" + hashlib.sha256(content.encode("utf-8")).hexdigest()


def _sanitized_passage(raw: str, max_length: int = 500) -> str:
    """`sanitize_snippet` (tags, protocollen, witruimte, lengte) zonder de
    afsluitende HTML-entity-encoding: die is voor tekst-UI's. In de prompt
    escapet `format_bron` precies één keer, zodat het model `&` ziet en niet
    `&amp;amp;`, en de kwitantie-`content` de gesaniteerde passage zelf is.
    """
    return html.unescape(sanitize_snippet(raw, max_length=max_length))


def _used_record(
    *,
    nr: int,
    source_type: str,
    source_id: Any,
    input_index: int,
    identity: dict[str, Any],
    retrieval_score: float | None,
    supplied: str,
    content: str,
    truncated: bool,
    xml: str,
) -> dict[str, Any]:
    """Eén werkelijk in de prompt opgenomen bron: exact wat het model ziet."""
    return {
        "nr": nr,
        "source_type": source_type,
        "source_id": source_id,
        "input_index": input_index,
        "original_content_hash": _content_hash(supplied),
        "identity": identity,
        "retrieval_score": retrieval_score,
        "content": content,
        "content_hash": _content_hash(content),
        "sanitized": content != supplied,
        "truncated": truncated,
        "xml": xml,
        "used_in_prompt": True,
    }


def _supplied_counts(enriched_context: EnrichedContext) -> dict[str, int]:
    """Aantal aangeleverde bronnen per kanaal, vóór enige selectie; faalt naar 0."""
    metadata = getattr(enriched_context, "metadata", None) or {}
    counts = dict.fromkeys(_SOURCE_CHANNELS, 0)
    try:
        counts["rag"] = len(metadata.get("rag_chunks") or [])
    except TypeError:
        pass
    try:
        web_ctx = metadata.get("web_lookup")
        if isinstance(web_ctx, dict):
            counts["web"] = len(web_ctx.get("sources") or [])
    except TypeError:
        pass
    try:
        docs = metadata.get("documents")
        if isinstance(docs, dict):
            counts["document"] = len(docs.get("snippets") or [])
    except TypeError:
        pass
    return counts


class _Correlatie(TypedDict):
    """Correlatie met de oorspronkelijke passage (kwitantie v2): index + tekst."""

    input_index: int
    supplied: str


def _omitted_record(
    source_type: str,
    source_id: Any,
    identity: dict[str, Any],
    reason: str,
    *,
    input_index: int,
    supplied: str,
) -> dict[str, Any]:
    """Aangeleverd maar niet in de prompt — identiteit, index, hash en reden.

    Geen ruwe tekst: de hash van de oorspronkelijke passage volstaat om het
    record ondubbelzinnig aan de aangeleverde bron te binden.
    """
    return {
        "source_type": source_type,
        "source_id": source_id,
        "input_index": input_index,
        "original_content_hash": _content_hash(supplied),
        "identity": identity,
        "reason": reason,
    }


def _supplied_text(src: Any, key: str) -> str:
    """De oorspronkelijke passage zoals aangeleverd (None → "")."""
    return ensure_string(src.get(key) if isinstance(src, dict) else "")


@dataclass
class _ChannelResult:
    """Uitkomst van één bronkanaal ná flags, limieten, sanitisatie en budget."""

    enabled: bool
    supplied: int
    used: list[dict[str, Any]] = field(default_factory=list)
    omitted: list[dict[str, Any]] = field(default_factory=list)


def _web_sources(enriched_context: EnrichedContext) -> list[dict[str, Any]]:
    """De aangeleverde weblookup-bronnen, in aangeleverde volgorde; anders leeg."""
    web_ctx = (
        enriched_context.metadata.get("web_lookup")
        if enriched_context and enriched_context.metadata
        else None
    )
    return list((web_ctx.get("sources") or []) if isinstance(web_ctx, dict) else [])


def _web_omitted(idx: int, src: dict[str, Any], reason: str) -> dict[str, Any]:
    """Een weggelaten webbron, gecorreleerd op aangeleverde index en passagehash."""
    return _omitted_record(
        "web",
        src.get("url") or None,
        _identity(src, _WEB_IDENTITY_KEYS, nested=("legal",)),
        reason,
        input_index=idx,
        supplied=_supplied_text(src, "snippet"),
    )


def _is_auth_web(src: dict[str, Any]) -> bool:
    # Sorteervoorkeur voor de selectie; verschijnt niet als gezag in de prompt.
    prov = (src.get("provider") or "").lower()
    url = (src.get("url") or "").lower()
    return any(x in prov or x in url for x in ("overheid", "rechtspraak"))


def _select_web_sources(
    aug: dict[str, Any],
    indexed: list[tuple[int, dict[str, Any]]],
    result: _ChannelResult,
) -> list[tuple[int, dict[str, Any]]]:
    """Selectie (used_in_prompt / include_all_hits) en juridische sortering.

    Niet-geselecteerde bronnen gaan in aangeleverde volgorde als `not_selected`
    naar `result.omitted`; de geselecteerde paren behouden hun oorspronkelijke
    index, ook na sortering.
    """
    # Select items: if include_all_hits, ignore used_in_prompt and take all
    if bool(aug.get("include_all_hits", False)):
        selected = list(indexed)
    else:
        flagged = [(idx, s) for idx, s in indexed if s.get("used_in_prompt")]
        # Fallback: use first N sources if nothing marked
        selected = flagged if flagged else list(indexed)
    selected_idx = {idx for idx, _ in selected}
    result.omitted.extend(
        _web_omitted(idx, s, "not_selected")
        for idx, s in indexed
        if idx not in selected_idx
    )

    if aug.get("prioritize_juridical", True):
        # Stable sort: authoritative first, then score desc, then title/url
        selected = sorted(
            selected,
            key=lambda item: (
                int(_is_auth_web(item[1]))
                * -1,  # False comes after True when multiplied by -1
                -(float(item[1].get("score", 0.0) or 0.0)),
                str(item[1].get("title", "")),
                str(item[1].get("url", "")),
            ),
        )
    return selected


def _web_limits(aug: dict[str, Any], selected_count: int) -> tuple[int, int, int]:
    """(max_snippets, max_tokens_per_snippet, total_budget) uit de configuratie."""
    # Token budget & snippet length management
    max_snippets = int(aug.get("max_snippets", 3))
    max_tokens_per_snippet = int(aug.get("max_tokens_per_snippet", 100))
    total_budget = int(aug.get("total_token_budget", 400))

    # If include_all_hits, relax snippet/budget constraints to allow all
    if bool(aug.get("include_all_hits", False)):
        max_snippets = max(max_snippets, selected_count)
        # Set a generous budget to avoid early truncation; final model limits still apply
        total_budget = max(total_budget, 5000)
    return max_snippets, max_tokens_per_snippet, total_budget


@dataclass
class _SourceReceipt:
    """Per-aanroep verzamelstaat; leeft alleen binnen één build_generation_prompt."""

    sources: list[dict[str, Any]] = field(default_factory=list)
    omitted: list[dict[str, Any]] = field(default_factory=list)
    errors: list[dict[str, str]] = field(default_factory=list)
    channels: dict[str, dict[str, Any]] = field(
        default_factory=lambda: {
            ch: {"enabled": True, "supplied": 0, "used": 0} for ch in _SOURCE_CHANNELS
        }
    )

    @property
    def xml(self) -> list[str]:
        return [record["xml"] for record in self.sources]

    def commit(self, channel: str, result: _ChannelResult) -> None:
        self.channels[channel] = {
            "enabled": result.enabled,
            "supplied": result.supplied,
            "used": len(result.used),
        }
        self.sources.extend(result.used)
        self.omitted.extend(result.omitted)

    def fail(self, stage: str, exc: BaseException) -> None:
        # Alleen fase en exceptietype: geen boodschap (kan broninhoud bevatten).
        self.errors.append({"stage": stage, "type": type(exc).__name__})

    def discard_all(self) -> None:
        """Weggegooide XML = niets gebruikt; de tellingen volgen."""
        self.sources.clear()
        for channel in self.channels.values():
            channel["used"] = 0

    def to_dict(self) -> dict[str, Any]:
        if self.sources:
            status = "used"
        elif self.errors:
            status = "error"
        else:
            status = "none"
        return {
            "version": SOURCE_RECEIPT_VERSION,
            "status": status,
            "sources": list(self.sources),
            "omitted": list(self.omitted),
            "errors": list(self.errors),
            "channels": {ch: dict(self.channels[ch]) for ch in _SOURCE_CHANNELS},
        }


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

    @staticmethod
    def _approx_tokens(s: str) -> int:
        """Schat het aantal tokens (1 token ≈ 4 tekens)."""
        return max(1, (len(s) + 3) // 4)

    @staticmethod
    def _truncate_to_tokens(s: str, limit: int) -> str:
        """Trunceer tekst tot een geschat token-limiet, op woordgrens."""
        char_limit = max(1, limit * 4)
        if len(s) <= char_limit:
            return s
        cut = s[:char_limit]
        last_space = cut.rfind(" ")
        if last_space > 20:
            cut = cut[:last_space]
        return cut

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

        # Load prompt augmentation config (Epic 3) + RAG injection config (DEF-316)
        try:
            wl_cfg = load_web_lookup_config().get("web_lookup", {})
            self._aug_cfg = wl_cfg.get("prompt_augmentation", {})
            self._rag_injection_cfg = wl_cfg.get("rag_injection", {})
        except Exception:
            self._aug_cfg = {}
            self._rag_injection_cfg = {}

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

            # DEF-751 stap 2: het expliciet verzonden gebruikersantwoord op een
            # gemeld betekenisconflict reist als DATA mee naar het contextblok
            # (ContextAwarenessModule). Alleen uit het typed requestveld;
            # `getattr` omdat oudere request-doubles het veld niet dragen.
            verduidelijking = getattr(request, "betekenisverduidelijking", None)
            if isinstance(verduidelijking, str) and verduidelijking.strip():
                enriched_context.metadata["betekenisverduidelijking"] = (
                    verduidelijking.strip()
                )

            # US-179: Ensure ontological category is present in prompt metadata
            # so SemanticCategorisationModule and TemplateModule can apply
            # category-specific guidance and templates.
            if request.ontologische_categorie and isinstance(
                request.ontologische_categorie, str
            ):
                cat = request.ontologische_categorie.strip().lower()
                enriched_context.metadata["ontologische_categorie"] = cat

                # Minimal mapping from ESS category → template semantic category
                # Proces → "Proces"; type/exemplaar → "Object"; resultaat → "Resultaat"
                # DEF-750: RESULTAAT stuurde eerder generiek naar "Maatregel";
                # een uitkomst is niet noodzakelijk een maatregel.
                mapping = {
                    "proces": "Proces",
                    "activiteit": "Proces",
                    "type": "Object",
                    "soort": "Object",
                    "exemplaar": "Object",
                    "particulier": "Object",
                    "resultaat": "Resultaat",
                    "uitkomst": "Resultaat",
                }
                semantic = mapping.get(cat)
                if semantic and "semantic_category" not in enriched_context.metadata:
                    enriched_context.metadata["semantic_category"] = semantic

            # Generate prompt using existing advanced system with category support
            prompt_text = self.prompt_generator.build_prompt(
                begrip=request.begrip, context=enriched_context
            )

            # DEF-315: Collect all sources (RAG + web + document) in one <bronnen> block
            # DEF-743: en leg exact vast wat daarvan werkelijk in de prompt staat.
            prompt_text, source_receipt = self._collect_bronnen_with_receipt(
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
                    # DEF-743: per-aanroep kwitantie van het feitelijke brongebruik
                    "source_receipt": source_receipt,
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
        """Verzamel alle bronnen (RAG + web + document) in één <bronnen> blok.

        Compatibele wrapper: alleen de prompttekst. De kwitantie komt via
        `_collect_bronnen_with_receipt` (DEF-743).
        """
        prompt_text, _receipt = self._collect_bronnen_with_receipt(
            prompt_text, enriched_context
        )
        return prompt_text

    def _collect_bronnen_with_receipt(
        self, prompt_text: str, enriched_context: EnrichedContext
    ) -> tuple[str, dict[str, Any]]:
        """DEF-743: één <bronnen>-blok plus de kwitantie van wat erin staat.

        Per kanaal (rag → web → document) gelden de bestaande flags, limieten,
        sanitisatie, truncatie en budgetten; pas wat daarna overblijft wordt
        geformatteerd én in de kwitantie opgenomen. Faalt een kanaal, dan wordt
        zijn XML weggegooid en de fout apart geregistreerd — er wordt nooit
        gebruik geclaimd van een bron die niet in de prompt staat. Staat is
        per aanroep; er is geen gedeelde 'laatste kwitantie'.
        """
        receipt = _SourceReceipt()
        # Aangeleverde aantallen vooraf: ook als een kanaal faalt blijft
        # zichtbaar dat er bronnen wáren die niet gebruikt zijn.
        for channel, supplied in _supplied_counts(enriched_context).items():
            receipt.channels[channel]["supplied"] = supplied
        collectors = (
            ("rag", self._collect_rag_records),
            ("web", self._collect_web_records),
            ("document", self._collect_document_records),
        )
        for channel, collect in collectors:
            try:
                result = collect(enriched_context, nr_offset=len(receipt.sources))
            except Exception as e:
                # Fail-safe per kanaal; alleen het exceptietype in het log —
                # geen broninhoud (frame-locals horen niet in logs/Sentry).
                logger.warning(
                    "Bronverzameling '%s' mislukt (%s); kanaal overgeslagen",
                    channel,
                    type(e).__name__,
                )
                receipt.fail(channel, e)
                continue
            receipt.commit(channel, result)

        try:
            if receipt.sources:
                block = wrap_bronnen(receipt.xml)
                prompt_text = f"{prompt_text}\n\n{block}"
        except Exception as e:
            # Fail-safe: generatie gaat door zonder bronnen, en zegt dat ook.
            logger.warning(
                "Bronnenblok invoegen mislukt (%s); prompt zonder bronnen",
                type(e).__name__,
            )
            receipt.fail("inject", e)
            receipt.discard_all()

        return prompt_text, receipt.to_dict()

    def _collect_rag_records(
        self, enriched_context: EnrichedContext, nr_offset: int
    ) -> _ChannelResult:
        """RAG-chunks → <bron type="rag"> na max_chunks, truncatie en tokenbudget.

        DEF-316: truncatie per chunk + totaalbudget. DEF-743: de zoekscore is
        een zoekscore (geen confidence/level); aangeleverde coördinaten gaan
        mee, niets wordt verzonnen; een lege passage is geen bron.
        """
        rag_chunks = list((enriched_context.metadata or {}).get("rag_chunks") or [])
        result = _ChannelResult(enabled=True, supplied=len(rag_chunks))
        rag_cfg = self._rag_injection_cfg or {}
        max_per_chunk = int(rag_cfg.get("max_tokens_per_chunk", 600))
        rag_budget = int(rag_cfg.get("total_token_budget", 2500))
        max_rag_chunks = int(rag_cfg.get("max_chunks", 5))

        tokens_used = 0
        budget_exhausted = False
        for idx, chunk in enumerate(rag_chunks):
            identity = _identity(chunk, _RAG_IDENTITY_KEYS, nested=("metadata",))
            source_id = chunk.get("chunk_id")
            raw = _supplied_text(chunk, "chunk_text")
            # Correlatie met de oorspronkelijke passage (v2): index + hash.
            ref: _Correlatie = {"input_index": idx, "supplied": raw}
            if idx >= max_rag_chunks:
                result.omitted.append(
                    _omitted_record("rag", source_id, identity, "max_count", **ref)
                )
                continue
            if budget_exhausted:
                result.omitted.append(
                    _omitted_record("rag", source_id, identity, "budget", **ref)
                )
                continue
            content = self._truncate_to_tokens(raw, max_per_chunk)
            if not content.strip():
                result.omitted.append(
                    _omitted_record("rag", source_id, identity, "empty_content", **ref)
                )
                continue
            est = self._approx_tokens(content)
            if tokens_used + est > rag_budget:
                budget_exhausted = True
                result.omitted.append(
                    _omitted_record("rag", source_id, identity, "budget", **ref)
                )
                continue

            meta = chunk.get("metadata")
            meta = meta if isinstance(meta, dict) else {}
            score = _retrieval_score(chunk.get("score"))
            nr = nr_offset + len(result.used) + 1
            xml = format_bron(
                nr=nr,
                type="rag",
                chunk_text=content,
                score=score,
                rechtsgebied=chunk.get("rechtsgebied"),
                regeling=chunk.get("wet_regeling"),
                artikel=chunk.get("artikel_lid"),
                lid=meta.get("lid_nummer"),
                # DEF-378: fallback op filename voor chunks zonder bronbestand
                bronbestand=meta.get("bronbestand") or chunk.get("filename"),
                pagina=meta.get("pagina_nummer"),
                sectie=meta.get("sectie"),
                url=meta.get("url"),
            )
            result.used.append(
                _used_record(
                    nr=nr,
                    source_type="rag",
                    source_id=source_id,
                    input_index=idx,
                    identity=identity,
                    retrieval_score=score,
                    supplied=raw,
                    content=content,
                    truncated=content != raw,
                    xml=xml,
                )
            )
            tokens_used += est

        if rag_chunks:
            logger.info(
                "RAG injection: %d/%d chunks used, ~%d tokens (budget: %d)",
                len(result.used),
                len(rag_chunks),
                tokens_used,
                rag_budget,
            )
        return result

    def _collect_document_brons(
        self, enriched_context: EnrichedContext, nr_offset: int
    ) -> list[str]:
        """Collect document snippets as XML <bron type="document"> strings.

        Compatibele wrapper rond `_collect_document_records`; dezelfde
        fail-safe als vóór DEF-743 (lege lijst bij een kapotte snippet-set).
        """
        try:
            return [
                r["xml"]
                for r in self._collect_document_records(
                    enriched_context, nr_offset
                ).used
            ]
        except (KeyError, TypeError, AttributeError):
            # DEF-246: Snippet collection failed, return empty list
            return []

    def _collect_document_records(
        self, enriched_context: EnrichedContext, nr_offset: int
    ) -> _ChannelResult:
        """Documentsnippets → <bron type="document"> na flags, aantal- en tekenbudget.

        Besturing via env-vars:
        - DOCUMENT_SNIPPETS_ENABLED (default: true)
        - DOCUMENT_SNIPPETS_MAX (default: 16)
        - DOCUMENT_SNIPPETS_MAX_CHARS (default: 800)

        DEF-743: geen vaste confidence 0.70 meer; de selectiewijze
        (term_match / selected_short_document) gaat als `selectie` mee.
        """
        enabled = os.getenv("DOCUMENT_SNIPPETS_ENABLED", "true").lower() == "true"
        docs_meta = (enriched_context.metadata or {}).get("documents", {})
        snippets = list((docs_meta or {}).get("snippets", []) or [])
        result = _ChannelResult(enabled=enabled, supplied=len(snippets))
        if not snippets:
            return result
        if not enabled:
            result.omitted.extend(
                _omitted_record(
                    "document",
                    s.get("doc_id"),
                    _identity(s, _DOC_IDENTITY_KEYS),
                    "channel_disabled",
                    input_index=idx,
                    supplied=_supplied_text(s, "snippet"),
                )
                for idx, s in enumerate(snippets)
            )
            return result

        try:
            max_snippets = int(os.getenv("DOCUMENT_SNIPPETS_MAX", "16"))
        except Exception:
            max_snippets = 16
        try:
            max_chars = int(os.getenv("DOCUMENT_SNIPPETS_MAX_CHARS", "800"))
        except Exception:
            max_chars = 800

        total = 0
        for idx, s in enumerate(snippets):
            identity = _identity(s, _DOC_IDENTITY_KEYS)
            source_id = s.get("doc_id")
            raw = _supplied_text(s, "snippet")
            ref: _Correlatie = {"input_index": idx, "supplied": raw}
            if len(result.used) >= max_snippets:
                result.omitted.append(
                    _omitted_record("document", source_id, identity, "max_count", **ref)
                )
                continue
            remaining = max(0, max_chars - total)
            if remaining <= 0:
                result.omitted.append(
                    _omitted_record("document", source_id, identity, "budget", **ref)
                )
                continue
            safe = _sanitized_passage(raw)
            content = safe[:remaining]
            if not content.strip():
                result.omitted.append(
                    _omitted_record(
                        "document", source_id, identity, "empty_content", **ref
                    )
                )
                continue

            title = s.get("title") or s.get("filename") or "document"
            filename = s.get("filename")
            nr = nr_offset + len(result.used) + 1
            xml = format_bron(
                nr=nr,
                type="document",
                chunk_text=content,
                titel=title,
                bestand=filename if filename and filename != title else None,
                citatie=s.get("citation_label") or "",
                selectie=s.get("selection_basis"),
            )
            result.used.append(
                _used_record(
                    nr=nr,
                    source_type="document",
                    source_id=source_id,
                    input_index=idx,
                    identity=identity,
                    retrieval_score=_retrieval_score(s.get("score")),
                    supplied=raw,
                    content=content,
                    truncated=content != _sanitized_passage(raw, max_length=0),
                    xml=xml,
                )
            )
            total += len(content)

        return result

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

        Compatibele wrapper rond `_collect_web_records`; dezelfde fail-safe
        als vóór DEF-743 (lege lijst bij een fout).
        """
        try:
            return [
                r["xml"]
                for r in self._collect_web_records(enriched_context, nr_offset).used
            ]
        except Exception:
            # Fail-safe: do not break generation if augmentation fails
            return []

    def _collect_web_records(
        self, enriched_context: EnrichedContext, nr_offset: int
    ) -> _ChannelResult:
        """Weblookup-bronnen → <bron type="web"> na selectie, sortering, sanitisatie en budget.

        Behoudt de bestaande selectie (used_in_prompt / include_all_hits), de
        juridische sortering en de tokenbudgetten. DEF-743: de zoekscore is een
        zoekscore (geen confidence/level, geen verzonnen 0.00); provider/url/
        titel/ecli/wet/artikel/citatie/opgehaald gaan mee zoals aangeleverd;
        een lege passage is geen bron; geselecteerd ≠ gebruikt.
        """
        aug = self._aug_cfg or {}
        enabled = bool(aug.get("enabled", False))
        sources = _web_sources(enriched_context)
        result = _ChannelResult(enabled=enabled, supplied=len(sources))

        # v2: de aangeleverde positie is de correlatiesleutel — vastgelegd vóór
        # selectie en sortering, zodat gelijke URL's/ontbrekende URL's en een
        # omgekeerde volgorde onderscheidbaar blijven.
        indexed = list(enumerate(sources))

        if not enabled:
            logger.info("Prompt augmentation disabled by config; skipping")
            result.omitted.extend(
                _web_omitted(idx, s, "channel_disabled") for idx, s in indexed
            )
            return result
        if not sources:
            logger.info("No web_lookup sources available; skipping prompt augmentation")
            return result

        selected = _select_web_sources(aug, indexed, result)
        logger.info(
            "Prompt augmentation selection: total_sources=%s, selected_for_consideration=%s",
            len(sources),
            len(selected),
        )
        max_snippets, max_tokens_per_snippet, total_budget = _web_limits(
            aug, len(selected)
        )
        tokens_used = self._web_budget_loop(
            selected,
            result,
            nr_offset=nr_offset,
            max_snippets=max_snippets,
            max_tokens_per_snippet=max_tokens_per_snippet,
            total_budget=total_budget,
        )

        if not result.used:
            logger.info(
                "Prompt augmentation produced no snippets within budget (total_budget=%s, per_snippet=%s)",
                total_budget,
                max_tokens_per_snippet,
            )
        else:
            logger.info(
                "Prompt augmentation collected %s web bron(s), approx_tokens=%s",
                len(result.used),
                tokens_used,
            )
        return result

    def _web_budget_loop(
        self,
        selected: list[tuple[int, dict[str, Any]]],
        result: _ChannelResult,
        *,
        nr_offset: int,
        max_snippets: int,
        max_tokens_per_snippet: int,
        total_budget: int,
    ) -> int:
        """Neem geselecteerde webbronnen op binnen aantal- en tokenbudget.

        In selectievolgorde: aantal vol → `max_count`; budget eerder uitgeput →
        `budget`; lege passage na sanitisatie/truncatie → `empty_content`;
        past niet meer → `budget` (en daarna niets meer). Geeft de geschatte
        tokens van de opgenomen bronnen terug.
        """
        tokens_used = 0
        budget_exhausted = False
        for idx, src in selected:
            identity = _identity(src, _WEB_IDENTITY_KEYS, nested=("legal",))
            source_id = src.get("url") or None
            raw = _supplied_text(src, "snippet")
            ref: _Correlatie = {"input_index": idx, "supplied": raw}
            if len(result.used) >= max_snippets:
                result.omitted.append(
                    _omitted_record("web", source_id, identity, "max_count", **ref)
                )
                continue
            if budget_exhausted:
                result.omitted.append(
                    _omitted_record("web", source_id, identity, "budget", **ref)
                )
                continue
            safe = _sanitized_passage(raw, max_length=2000)
            content = self._truncate_to_tokens(safe, max_tokens_per_snippet)
            if not content.strip():
                result.omitted.append(
                    _omitted_record("web", source_id, identity, "empty_content", **ref)
                )
                continue
            est = self._approx_tokens(content)
            if tokens_used + est > total_budget:
                budget_exhausted = True
                result.omitted.append(
                    _omitted_record("web", source_id, identity, "budget", **ref)
                )
                continue

            # DEF-315: Extract legal metadata from source
            legal = src.get("legal", {}) or {}
            score = _retrieval_score(src.get("score"))
            nr = nr_offset + len(result.used) + 1
            xml = format_bron(
                nr=nr,
                type="web",
                chunk_text=content,
                score=score,
                provider=src.get("provider", ""),
                url=src.get("url", ""),
                titel=src.get("title"),
                ecli=legal.get("ecli", ""),
                wet=legal.get("law", ""),
                artikel=legal.get("article", ""),
                citatie=legal.get("citation_text", ""),
                opgehaald=src.get("retrieved_at"),
            )
            result.used.append(
                _used_record(
                    nr=nr,
                    source_type="web",
                    source_id=source_id,
                    input_index=idx,
                    identity=identity,
                    retrieval_score=score,
                    supplied=raw,
                    content=content,
                    truncated=content != _sanitized_passage(raw, max_length=0),
                    xml=xml,
                )
            )
            tokens_used += est
        return tokens_used
