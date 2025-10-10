"""
Hybrid Context Engine - Hoofdcomponent voor hybride context verrijking.
Combineert web lookup met document processing voor optimale definitie generatie.
"""

import logging  # Logging faciliteiten voor debug en monitoring
from dataclasses import \
    dataclass  # Dataklassen voor gestructureerde context data
from datetime import (  # Datum en tijd functionaliteit voor timestamps, timezone
    UTC, datetime)
from typing import Any  # Type hints voor betere code documentatie

from document_processing.document_processor import \
    get_document_processor  # Document processor factory
# Legacy web_lookup import replaced with modern service
# from web_lookup.lookup import zoek_definitie_combinatie  # DEPRECATED
from services.modern_web_lookup_service import ModernWebLookupService

from .context_fusion import ContextFusion  # Context fusie en samenvoeging
from .smart_source_selector import \
    SmartSourceSelector  # Intelligente bron selectie

# Create modern service instance
_web_lookup_service = ModernWebLookupService()


# Compatibility wrapper
async def zoek_definitie_combinatie(term: str, *args, **kwargs):
    """Compatibility wrapper for legacy web lookup"""
    from services.interfaces import LookupRequest

    request = LookupRequest(term=term, max_results=5)
    return await _web_lookup_service.lookup(request)


# Imports zijn al bovenaan toegevoegd

logger = logging.getLogger(__name__)  # Logger instantie voor hybrid context engine


@dataclass
class HybridContext:
    """Hybride context resultaat met gecombineerde web en document data."""

    # Context data - gecombineerde en verrijkte context informatie
    unified_context: str  # Samengevoegde context tekst
    confidence_score: float  # Betrouwbaarheidsscore (0.0-1.0)

    # Web lookup data - resultaten van externe bronnen
    web_context: dict[str, Any]  # Context data uit web bronnen
    web_sources: list[str]  # Gebruikte web bronnen URLs

    # Document data - resultaten van document analyse
    document_context: dict[str, Any]  # Context data uit geüploade documenten
    document_sources: list[dict[str, Any]]  # Gebruikte document metadata

    # Fusion metadata - informatie over samenvoeging proces
    fusion_strategy: str  # Gebruikte fusie strategie
    conflicts_resolved: int  # Aantal opgeloste conflicten
    context_quality: str  # Kwaliteitsbeoordeling van context

    # Attribution - bronvermelding en traceerbaarheid
    primary_sources: list[str]  # Primaire bronnen voor de context
    supporting_sources: list[str]  # Ondersteunende bronnen
    created_at: datetime  # Tijdstip van context creatie


class HybridContextEngine:
    """
    Hybride Context Engine - Combineert intelligente web lookup met document processing.

    Workflow:
    1. Document analyse voor intelligente source selectie
    2. Enhanced web lookup op basis van document context
    3. Context fusion met conflict resolution
    4. Unified context generation met bronvermelding
    """

    def __init__(self):
        """Initialiseer hybride context engine."""
        self.source_selector = SmartSourceSelector()
        self.context_fusion = ContextFusion()
        self.document_processor = get_document_processor()

    def create_hybrid_context(
        self,
        begrip: str,
        organisatorische_context: str | None = None,
        juridische_context: str | None = None,
        selected_document_ids: list[str] | None = None,
    ) -> HybridContext:
        """
        Creëer hybride context door web lookup en document processing te combineren.

        Args:
            begrip: Het begrip waarvoor context gezocht wordt
            organisatorische_context: Organisatorische context
            juridische_context: Juridische context
            selected_document_ids: IDs van geselecteerde documenten

        Returns:
            HybridContext object met gecombineerde context
        """
        try:
            logger.info(f"Start hybride context creatie voor '{begrip}'")

            # Stap 1: Document context ophalen (indien beschikbaar)
            document_context = self._get_document_context(selected_document_ids)

            # Stap 2: Intelligente source selectie op basis van document context
            source_strategy = self.source_selector.select_optimal_sources(
                begrip=begrip,
                organisatorische_context=organisatorische_context,
                juridische_context=juridische_context,
                document_context=document_context,
            )

            # Stap 3: Enhanced web lookup uitvoeren
            web_context = self._execute_enhanced_web_lookup(
                begrip=begrip,
                source_strategy=source_strategy,
                document_keywords=document_context.get("aggregated_keywords", []),
            )

            # Stap 4: Context fusion - combineer web en document context
            fusion_result = self.context_fusion.fuse_contexts(
                web_context=web_context,
                document_context=document_context,
                begrip=begrip,
            )

            # Stap 5: Creëer unified hybrid context
            hybrid_context = HybridContext(
                unified_context=fusion_result["unified_context"],
                confidence_score=fusion_result["confidence_score"],
                web_context=web_context,
                web_sources=fusion_result["web_sources"],
                document_context=document_context,
                document_sources=document_context.get("document_sources", []),
                fusion_strategy=fusion_result["strategy"],
                conflicts_resolved=fusion_result["conflicts_resolved"],
                context_quality=fusion_result["quality_assessment"],
                primary_sources=fusion_result["primary_sources"],
                supporting_sources=fusion_result["supporting_sources"],
                created_at=datetime.now(UTC),
            )

            logger.info(
                f"Hybride context succesvol aangemaakt (confidence: {hybrid_context.confidence_score:.2f})"
            )
            return hybrid_context

        except Exception as e:
            logger.error(f"Fout bij creëren hybride context voor '{begrip}': {e}")

            # Fallback: return web-only context
            return self._create_fallback_context(
                begrip, organisatorische_context, juridische_context
            )

    def _get_document_context(
        self, selected_document_ids: list[str] | None
    ) -> dict[str, Any]:
        """Haal document context op."""
        if not selected_document_ids:
            return {
                "document_count": 0,
                "total_text_length": 0,
                "aggregated_keywords": [],
                "aggregated_concepts": [],
                "aggregated_legal_refs": [],
                "aggregated_context_hints": [],
                "document_sources": [],
            }

        try:
            return self.document_processor.get_aggregated_context(selected_document_ids)
        except Exception as e:
            logger.error(f"Fout bij ophalen document context: {e}")
            return {
                "document_count": 0,
                "aggregated_keywords": [],
                "document_sources": [],
            }

    def _execute_enhanced_web_lookup(
        self, begrip: str, source_strategy: dict[str, Any], document_keywords: list[str]
    ) -> dict[str, Any]:
        """Voer enhanced web lookup uit op basis van source strategy."""
        try:
            # Basis web lookup uitvoeren
            web_results = zoek_definitie_combinatie(begrip)

            # Enhance results met document keywords
            return self._enhance_web_results(
                web_results, document_keywords, source_strategy
            )

        except Exception as e:
            logger.error(f"Fout bij enhanced web lookup: {e}")
            # Fallback naar basis web lookup
            try:
                return zoek_definitie_combinatie(begrip) or {}
            except Exception:
                return {}

    def _enhance_web_results(
        self,
        web_results: Any,
        document_keywords: list[str],
        source_strategy: dict[str, Any],
    ) -> dict[str, Any]:
        """Verbeter web lookup resultaten met document context."""

        if not web_results or not document_keywords:
            return {}

        # Handle verschillende web_results formats
        if isinstance(web_results, list):
            # Convert list to dict format
            enhanced_results = {}
            for i, result in enumerate(web_results):
                if isinstance(result, dict):
                    enhanced_results[f"result_{i}"] = result
        elif isinstance(web_results, dict):
            enhanced_results = web_results.copy()
        else:
            # Unsupported format
            return {}

        # Filter en prioriteer bronnen op basis van document keywords
        for source_name, source_data in enhanced_results.items():
            if isinstance(source_data, dict) and "tekst" in source_data:
                source_text = source_data["tekst"].lower()

                # Bereken relevantie score op basis van document keywords
                relevance_score = self._calculate_relevance_score(
                    source_text, document_keywords
                )

                # Voeg relevantie metadata toe
                enhanced_results[source_name] = source_data.copy()
                enhanced_results[source_name]["document_relevance"] = relevance_score
                enhanced_results[source_name]["enhanced_by_documents"] = (
                    relevance_score > 0.3
                )

        # Voeg metadata toe over enhancement
        enhanced_results["_enhancement_metadata"] = {
            "document_keywords_used": len(document_keywords),
            "sources_enhanced": sum(
                1
                for k, v in enhanced_results.items()
                if isinstance(v, dict) and v.get("enhanced_by_documents", False)
            ),
            "strategy_applied": source_strategy.get("strategy_name", "default"),
        }

        return enhanced_results

    def _calculate_relevance_score(
        self, source_text: str, document_keywords: list[str]
    ) -> float:
        """Bereken relevantie score tussen source text en document keywords."""
        if not document_keywords or not source_text:
            return 0.0

        matches = 0
        for keyword in document_keywords[:10]:  # Beperk tot top 10 keywords
            if keyword.lower() in source_text:
                matches += 1

        return min(matches / len(document_keywords[:10]), 1.0)

    def _create_fallback_context(
        self,
        begrip: str,
        organisatorische_context: str | None,
        juridische_context: str | None,
    ) -> HybridContext:
        """Creëer fallback context als hybride proces faalt."""
        try:
            web_results = zoek_definitie_combinatie(begrip) or {}

            return HybridContext(
                unified_context=f"Basis context voor '{begrip}' uit web bronnen.",
                confidence_score=0.5,
                web_context=web_results,
                web_sources=list(web_results.keys()) if web_results else [],
                document_context={"document_count": 0},
                document_sources=[],
                fusion_strategy="fallback_web_only",
                conflicts_resolved=0,
                context_quality="basic",
                primary_sources=list(web_results.keys())[:3] if web_results else [],
                supporting_sources=[],
                created_at=datetime.now(UTC),
            )
        except Exception as e:
            logger.error(f"Zelfs fallback context faalde: {e}")

            # Absolute minimum fallback
            return HybridContext(
                unified_context=f"Minimale context voor '{begrip}'.",
                confidence_score=0.1,
                web_context={},
                web_sources=[],
                document_context={"document_count": 0},
                document_sources=[],
                fusion_strategy="emergency_fallback",
                conflicts_resolved=0,
                context_quality="minimal",
                primary_sources=[],
                supporting_sources=[],
                created_at=datetime.now(UTC),
            )

    def get_context_summary(self, hybrid_context: HybridContext) -> dict[str, Any]:
        """Genereer samenvatting van hybride context voor UI display."""
        return {
            "context_quality": hybrid_context.context_quality,
            "confidence_score": hybrid_context.confidence_score,
            "total_sources": len(hybrid_context.web_sources)
            + len(hybrid_context.document_sources),
            "web_sources_count": len(hybrid_context.web_sources),
            "document_sources_count": len(hybrid_context.document_sources),
            "conflicts_resolved": hybrid_context.conflicts_resolved,
            "fusion_strategy": hybrid_context.fusion_strategy,
            "primary_sources": hybrid_context.primary_sources,
            "enhancement_level": self._determine_enhancement_level(hybrid_context),
        }

    def _determine_enhancement_level(self, context: HybridContext) -> str:
        """Bepaal enhancement level van de context."""
        if (
            context.document_context.get("document_count", 0) > 0
            and len(context.web_sources) > 0
        ):
            if context.confidence_score > 0.8:
                return "excellent"
            if context.confidence_score > 0.6:
                return "good"
            return "moderate"
        if len(context.web_sources) > 0:
            return "web_only"
        if context.document_context.get("document_count", 0) > 0:
            return "document_only"
        return "minimal"


# Global hybrid context engine instance
_hybrid_context_engine = None


def get_hybrid_context_engine() -> HybridContextEngine:
    """Krijg globale hybrid context engine instance."""
    global _hybrid_context_engine
    if _hybrid_context_engine is None:
        _hybrid_context_engine = HybridContextEngine()
    return _hybrid_context_engine
