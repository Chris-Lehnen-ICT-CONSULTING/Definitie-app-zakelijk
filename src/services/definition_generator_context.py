"""
Definition Generator Context Module.

Hybrid context systeem dat intelligente context building biedt door:
- Basis context parsing (van services implementatie)
- Web lookup integratie (van definitie_generator implementatie)
- Hybrid context engine (van generation implementatie)
- Rule interpretation voor creatieve prompt building
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from services.definition_generator_config import ContextConfig
from services.interfaces import GenerationRequest

logger = logging.getLogger(__name__)

# Context afkortingen (van generation implementatie)
CONTEXT_AFKORTINGEN = {
    "OM": "Openbaar Ministerie",
    "ZM": "Zittende Magistratuur",
    "3RO": "Samenwerkingsverband Reclasseringsorganisaties",
    "DJI": "Dienst Justitiële Inrichtingen",
    "NP": "Nederlands Politie",
    "FIOD": "Fiscale Inlichtingen- en Opsporingsdienst",
    "Justid": "Dienst Justitiële Informatievoorziening",
    "KMAR": "Koninklijke Marechaussee",
    "CJIB": "Centraal Justitieel Incassobureau",
    "AVG": "Algemene verordening gegevensbescherming",
}


class ContextType(Enum):
    """Types van context informatie."""

    ORGANISATORISCH = "organisatorisch"
    JURIDISCH = "juridisch"
    WETTELIJK = "wettelijk"
    DOMEIN = "domein"
    TECHNISCH = "technisch"
    HISTORISCH = "historisch"


@dataclass
class ContextSource:
    """Bron van context informatie."""

    source_type: str  # "web_lookup", "document", "user_input", "rule_interpretation"
    confidence: float  # 0.0 - 1.0
    content: str
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class EnrichedContext:
    """Verrijkte context met meerdere bronnen."""

    base_context: Dict[str, List[str]]
    sources: List[ContextSource]
    expanded_terms: Dict[str, str]  # afkortingen -> volledige namen
    confidence_scores: Dict[str, float]
    metadata: Dict[str, Any]

    def get_all_context_text(self) -> str:
        """Verkrijg alle context als één tekst blok."""
        all_text = []

        # Basis context
        for context_type, items in self.base_context.items():
            if items:
                all_text.append(f"{context_type.title()}: {', '.join(items)}")

        # Source content
        for source in self.sources:
            if source.confidence > 0.7:  # Alleen high-confidence sources
                all_text.append(f"{source.source_type}: {source.content}")

        return "\n".join(all_text)


class HybridContextManager:
    """
    Hybrid Context Manager die alle context strategieën combineert:

    Van services/definition_generator.py:
    - Basis context parsing van GenerationRequest
    - Context type classificatie (juridisch, wettelijk, etc.)

    Van definitie_generator/generator.py:
    - Web lookup integratie voor achtergrond informatie
    - Caching van context results

    Van generation/definitie_generator.py:
    - Hybrid context engine integratie
    - Rule interpretation voor intelligente context
    - Context afkortingen expansie
    - Feedback integration voor context verbetering
    """

    def __init__(self, config: ContextConfig):
        self.config = config
        self._web_lookup = None
        self._hybrid_engine = None
        self._context_cache = {}

        # Initialize components
        self._init_web_lookup()
        self._init_hybrid_engine()

        logger.info("HybridContextManager geïnitialiseerd")

    def _init_web_lookup(self):
        """Initialiseer web lookup component."""
        if self.config.enable_web_lookup:
            try:
                from web_lookup import zoek_definitie_combinatie

                self._web_lookup = zoek_definitie_combinatie
                logger.info("Web lookup component geïnitialiseerd")
            except ImportError:
                logger.warning("Web lookup niet beschikbaar")
                self._web_lookup = None

    def _init_hybrid_engine(self):
        """Initialiseer hybrid context engine."""
        try:
            from hybrid_context.hybrid_context_engine import get_hybrid_context_engine

            self._hybrid_engine = get_hybrid_context_engine()
            logger.info("Hybrid context engine geïnitialiseerd")
        except ImportError:
            logger.warning("Hybrid context engine niet beschikbaar")
            self._hybrid_engine = None

    async def build_enriched_context(
        self, request: GenerationRequest
    ) -> EnrichedContext:
        """
        Bouw verrijkte context door alle strategieën te combineren.

        Args:
            request: GenerationRequest met basis context informatie

        Returns:
            EnrichedContext met alle context bronnen gecombineerd
        """
        # 1. Start met basis context (services pattern)
        base_context = self._build_base_context(request)

        # 2. Expandeer afkortingen
        expanded_terms = self._expand_abbreviations(base_context)

        # 3. Verzamel context bronnen
        sources = []
        confidence_scores = {}

        # Web lookup bron (definitie_generator pattern)
        if self._web_lookup and self.config.enable_web_lookup:
            web_source = await self._get_web_context(request.begrip)
            if web_source:
                sources.append(web_source)
                confidence_scores["web_lookup"] = web_source.confidence

        # Hybrid context bron (generation pattern)
        if self._hybrid_engine:
            hybrid_source = await self._get_hybrid_context(request)
            if hybrid_source:
                sources.append(hybrid_source)
                confidence_scores["hybrid_context"] = hybrid_source.confidence

        # Document context (als beschikbaar)
        if hasattr(request, "document_context") and request.document_context:
            doc_source = ContextSource(
                source_type="document",
                confidence=0.9,
                content=request.document_context,
                metadata={"source": "user_document"},
            )
            sources.append(doc_source)
            confidence_scores["document"] = 0.9

        # 4. Rule interpretation context
        if self.config.enable_rule_interpretation:
            rule_source = await self._get_rule_interpretation_context(request)
            if rule_source:
                sources.append(rule_source)
                confidence_scores["rule_interpretation"] = rule_source.confidence

        # 5. Bouw finale verrijkte context
        enriched_context = EnrichedContext(
            base_context=base_context,
            sources=sources,
            expanded_terms=expanded_terms,
            confidence_scores=confidence_scores,
            metadata={
                "total_sources": len(sources),
                "avg_confidence": (
                    sum(confidence_scores.values()) / len(confidence_scores)
                    if confidence_scores
                    else 0.0
                ),
                "web_lookup_enabled": self.config.enable_web_lookup,
                "hybrid_engine_available": self._hybrid_engine is not None,
            },
        )

        logger.info(
            f"Verrijkte context gebouwd met {len(sources)} bronnen voor '{request.begrip}'"
        )
        return enriched_context

    def _build_base_context(self, request: GenerationRequest) -> Dict[str, List[str]]:
        """Bouw basis context dictionary (van services implementatie)."""
        context = {
            "organisatorisch": [],
            "juridisch": [],
            "wettelijk": [],
            "domein": [],
            "technisch": [],
            "historisch": [],
        }

        # Basis velden
        if request.organisatie:
            context["organisatorisch"].append(request.organisatie)
        if request.domein:
            context["domein"].append(request.domein)

        # Parse context string
        if request.context:
            self._parse_context_string(request.context, context)

        return context

    def _parse_context_string(
        self, context_string: str, context_dict: Dict[str, List[str]]
    ):
        """Parse context string naar verschillende categorieën."""
        context_parts = context_string.split(",")

        for part in context_parts:
            part = part.strip()
            if not part:
                continue

            # Classificeer context type
            if any(
                word in part.lower()
                for word in ["wet", "artikel", "lid", "besluit", "verordening"]
            ):
                context_dict["wettelijk"].append(part)
            elif any(
                word in part.lower()
                for word in ["recht", "juridisch", "procedure", "proces"]
            ):
                context_dict["juridisch"].append(part)
            elif any(
                word in part.lower()
                for word in ["systeem", "technisch", "applicatie", "database"]
            ):
                context_dict["technisch"].append(part)
            elif any(
                word in part.lower()
                for word in ["historie", "historisch", "vroeger", "oorspronkelijk"]
            ):
                context_dict["historisch"].append(part)
            else:
                context_dict["organisatorisch"].append(part)

    def _expand_abbreviations(
        self, base_context: Dict[str, List[str]]
    ) -> Dict[str, str]:
        """Expandeer afkortingen naar volledige namen."""
        expanded = {}

        # Gebruik configuratie afkortingen
        abbreviations = {**CONTEXT_AFKORTINGEN, **self.config.context_abbreviations}

        for context_type, items in base_context.items():
            for item in items:
                words = item.split()
                for word in words:
                    clean_word = word.strip(".,;:")
                    if clean_word in abbreviations:
                        expanded[clean_word] = abbreviations[clean_word]

        return expanded

    async def _get_web_context(self, begrip: str) -> Optional[ContextSource]:
        """Verkrijg web context via web lookup."""
        try:
            web_info = self._web_lookup(begrip)
            if web_info and len(web_info.strip()) > 10:  # Minimale content check
                return ContextSource(
                    source_type="web_lookup",
                    confidence=0.8,
                    content=web_info[:500],  # Limit content length
                    metadata={"lookup_time": "current", "source": "web_scraping"},
                )
        except Exception as e:
            logger.warning(f"Web lookup mislukt voor '{begrip}': {e}")

        return None

    async def _get_hybrid_context(
        self, request: GenerationRequest
    ) -> Optional[ContextSource]:
        """Verkrijg context van hybrid context engine."""
        try:
            # Deze methode zou de hybrid context engine aanroepen
            # Voor nu een placeholder implementatie
            if self._hybrid_engine:
                hybrid_data = await self._call_hybrid_engine(request)
                if hybrid_data:
                    return ContextSource(
                        source_type="hybrid_context",
                        confidence=0.85,
                        content=hybrid_data.get("context_summary", ""),
                        metadata=hybrid_data.get("metadata", {}),
                    )
        except Exception as e:
            logger.warning(f"Hybrid context mislukt voor '{request.begrip}': {e}")

        return None

    async def _call_hybrid_engine(
        self, request: GenerationRequest
    ) -> Optional[Dict[str, Any]]:
        """Roep hybrid context engine aan."""
        # Placeholder voor hybrid context engine call
        # In werkelijke implementatie zou dit een complexe AI context engine aanroepen
        return {
            "context_summary": f"Hybrid context voor {request.begrip} gebaseerd op multiple bronnen",
            "metadata": {
                "sources_used": ["documents", "knowledge_base", "rules"],
                "confidence": 0.85,
            },
        }

    async def _get_rule_interpretation_context(
        self, request: GenerationRequest
    ) -> Optional[ContextSource]:
        """Verkrijg context via rule interpretation."""
        try:
            # Rule interpretation logic
            if self.config.rule_interpretation_mode == "creative":
                rule_context = self._creative_rule_interpretation(request)
            elif self.config.rule_interpretation_mode == "strict":
                rule_context = self._strict_rule_interpretation(request)
            else:  # balanced
                rule_context = self._balanced_rule_interpretation(request)

            if rule_context:
                return ContextSource(
                    source_type="rule_interpretation",
                    confidence=0.75,
                    content=rule_context,
                    metadata={
                        "interpretation_mode": self.config.rule_interpretation_mode,
                        "rules_applied": ["ESS-01", "CON-01", "STR-01"],  # Voorbeelden
                    },
                )
        except Exception as e:
            logger.warning(f"Rule interpretation mislukt voor '{request.begrip}': {e}")

        return None

    def _creative_rule_interpretation(self, request: GenerationRequest) -> str:
        """Creatieve rule interpretation (van generation implementatie)."""
        # Implementatie die toetsregels interpreteert als creatieve richtlijnen
        begrip_lower = request.begrip.lower()

        creative_hints = []

        # Structuur hints
        if any(word in begrip_lower for word in ["proces", "procedure", "methode"]):
            creative_hints.append("Focus op stappen en flow in de definitie")

        # Domeint hints
        if request.domein:
            if "juridisch" in request.domein.lower():
                creative_hints.append(
                    "Gebruik juridische terminologie en refereer naar wettelijke kaders"
                )

        # Context hints
        if request.context:
            if (
                "openbaar ministerie" in request.context.lower()
                or "OM" in request.context
            ):
                creative_hints.append("Relateer aan strafrecht en vervolging context")

        return (
            "; ".join(creative_hints)
            if creative_hints
            else "Gebruik heldere, eenduidige bewoordingen"
        )

    def _strict_rule_interpretation(self, request: GenerationRequest) -> str:
        """Strikte rule interpretation."""
        return "Volg exacte toetsregel specificaties zonder creatieve interpretatie"

    def _balanced_rule_interpretation(self, request: GenerationRequest) -> str:
        """Gebalanceerde rule interpretation."""
        return (
            "Combineer toetsregel compliance met begrip-specifieke context aanpassingen"
        )

    def get_context_summary(self, enriched_context: EnrichedContext) -> str:
        """Verkrijg een samenvatting van de context voor logging/debugging."""
        summary_parts = []

        # Basis context summary
        total_items = sum(
            len(items) for items in enriched_context.base_context.values()
        )
        summary_parts.append(f"Basis context: {total_items} items")

        # Sources summary
        summary_parts.append(f"Context bronnen: {len(enriched_context.sources)}")

        # Confidence summary
        avg_confidence = enriched_context.metadata.get("avg_confidence", 0.0)
        summary_parts.append(f"Gemiddeld vertrouwen: {avg_confidence:.2f}")

        # Expanded terms
        if enriched_context.expanded_terms:
            summary_parts.append(
                f"Afkortingen geëxpandeerd: {len(enriched_context.expanded_terms)}"
            )

        return " | ".join(summary_parts)
