"""
Juridische synoniemen service - REFACTORED as lightweight façade over SynonymOrchestrator.

ARCHITECTURE CHANGE (v3.1):
Dit is GEEN standalone service meer. Het is een backward-compatible façade die
alle calls delegeert naar SynonymOrchestrator (graph-based registry + TTL cache).

De oude YAML-based implementatie is vervangen door:
- SynonymRegistry (DB layer) → Graph-based synonym_groups/members
- SynonymOrchestrator (Business logic) → TTL cache + GPT-4 enrichment + governance
- JuridischeSynoniemService (Façade) → Backward compatibility wrapper

Architecture Reference:
    docs/architectuur/synonym-orchestrator-architecture-v3.1.md
    Lines 504-542: Façade specification

Migration Path:
    1. PHASE 2.2: Create this façade (this file)
    2. PHASE 2.3: Update imports in web_lookup services
    3. PHASE 3.x: Remove YAML file + old config updater

Backward Compatibility:
    ✅ get_synoniemen() - Returns list[str] (no weights)
    ✅ get_synonyms_with_weights() - Returns list[tuple[str, float]]
    ✅ expand_query_terms() - Query expansion with max_synonyms
    ✅ has_synoniemen() - Boolean check
    ✅ get_synonym_service() - Singleton factory
"""

import logging
from typing import Any

from services.synonym_orchestrator import SynonymOrchestrator

logger = logging.getLogger(__name__)


class JuridischeSynoniemService:
    """
    Backward compatible façade over SynonymOrchestrator.

    Dit is een thin wrapper die bestaande code kan blijven gebruiken
    zonder wijzigingen. Alle business logic zit in de orchestrator!

    Architecture Principle: NO BUSINESS LOGIC HERE
    - All queries → orchestrator.get_synonyms_for_lookup()
    - All enrichment → orchestrator.ensure_synonyms()
    - This class ONLY adapts the API

    Example Usage (backward compatible):
        service = JuridischeSynoniemService(orchestrator)
        synoniemen = service.get_synoniemen("onherroepelijk")
        # → ["kracht van gewijsde", "rechtskracht", ...]

        expanded = service.expand_query_terms("voorlopige hechtenis", max_synonyms=3)
        # → ["voorlopige hechtenis", "voorarrest", "bewaring", "inverzekeringstelling"]
    """

    def __init__(self, orchestrator: SynonymOrchestrator):
        """
        Initialiseer façade met orchestrator dependency.

        Args:
            orchestrator: SynonymOrchestrator instance (business logic layer)

        Architecture Note:
            - Orchestrator is injected via ServiceContainer
            - NO direct DB access (that's in registry)
            - NO YAML loading (migrated to DB)
        """
        self.orchestrator = orchestrator
        logger.info("JuridischeSynoniemService initialized as orchestrator façade")

    # ========================================
    # BACKWARD COMPATIBLE API
    # ========================================

    def get_synoniemen(self, term: str) -> list[str]:
        """
        Haal synoniemen op voor een term (backward compatible - returns strings).

        Dit is de LEGACY API die strings retourneert zonder weights.
        Nieuwe code zou get_synonyms_with_weights() moeten gebruiken.

        Flow:
        1. Delegate to orchestrator.get_synonyms_for_lookup()
        2. Extract term strings (drop weights)
        3. Filter out the term itself (legacy behavior)

        Args:
            term: Zoekterm

        Returns:
            Lijst van synoniemen (strings only, sorted by weight)

        Example:
            >>> service.get_synoniemen("onherroepelijk")
            ['kracht van gewijsde', 'rechtskracht', 'definitieve uitspraak']

        Architecture Reference:
            Lines 520-527 in architecture doc
        """
        if not term or not term.strip():
            return []

        # Delegate to orchestrator (business logic!)
        weighted = self.orchestrator.get_synonyms_for_lookup(
            term=term,
            max_results=8,  # Historical default from YAML-based service
            min_weight=0.7,  # Reasonable threshold for weblookup
        )

        # Extract strings, exclude the term itself (legacy behavior)
        term_normalized = term.lower().strip()
        return [ws.term for ws in weighted if ws.term != term_normalized]

    def get_synonyms_with_weights(self, term: str) -> list[tuple[str, float]]:
        """
        Haal synoniemen op met confidence weights (v2.0 compatible).

        Dit is de ENHANCED API die weights retourneert voor ranking/scoring.

        Flow:
        1. Delegate to orchestrator.get_synonyms_for_lookup()
        2. Return (term, weight) tuples
        3. Filter out the term itself

        Args:
            term: Zoekterm

        Returns:
            Lijst van (synonym, weight) tuples, sorted by weight (highest first)

        Example:
            >>> service.get_synonyms_with_weights("onherroepelijk")
            [("kracht van gewijsde", 0.95), ("rechtskracht", 0.90), ...]

        Architecture Reference:
            Lines 529-532 in architecture doc
        """
        if not term or not term.strip():
            return []

        # Delegate to orchestrator
        weighted = self.orchestrator.get_synonyms_for_lookup(term=term, max_results=8)

        # Extract tuples, exclude the term itself
        term_normalized = term.lower().strip()
        return [(ws.term, ws.weight) for ws in weighted if ws.term != term_normalized]

    def expand_query_terms(self, term: str, max_synonyms: int = 3) -> list[str]:
        """
        Expand term met synoniemen voor query diversificatie.

        Gebruikt synoniemen om query recall te verhogen. Beperkt aantal
        synoniemen om query complexity te managen.

        Flow:
        1. Start with original term
        2. Delegate to orchestrator for synonyms
        3. Append top-N synonyms
        4. Return expanded list

        Args:
            term: Originele zoekterm
            max_synonyms: Maximum aantal synoniemen toe te voegen (default: 3)

        Returns:
            Lijst met [originele_term, synonym1, synonym2, ...]

        Example:
            >>> service.expand_query_terms("voorlopige hechtenis", max_synonyms=2)
            ['voorlopige hechtenis', 'voorarrest', 'bewaring']

        Architecture Reference:
            Lines 534-537 in architecture doc
        """
        if not term or not term.strip():
            return [term] if term else []

        # Start with original term
        expanded = [term]

        # Delegate to orchestrator for synonyms
        weighted = self.orchestrator.get_synonyms_for_lookup(
            term=term, max_results=max_synonyms
        )

        # Append synonyms (excluding the term itself if present)
        term_normalized = term.lower().strip()
        synonyms = [ws.term for ws in weighted if ws.term != term_normalized]
        expanded.extend(synonyms[:max_synonyms])

        return expanded

    def has_synoniemen(self, term: str) -> bool:
        """
        Check of een term synoniemen heeft.

        Flow:
        1. Call get_synoniemen()
        2. Check if list is non-empty

        Args:
            term: Zoekterm

        Returns:
            True als term synoniemen heeft, anders False

        Example:
            >>> service.has_synoniemen("onherroepelijk")
            True

            >>> service.has_synoniemen("nonexistent_term")
            False

        Architecture Reference:
            Lines 539-541 in architecture doc
        """
        return len(self.get_synoniemen(term)) > 0

    # ========================================
    # LEGACY METHODS (Deprecated but kept for compatibility)
    # ========================================

    def get_all_terms(self) -> set[str]:
        """
        Haal alle bekende termen op (LEGACY - limited in graph model).

        WARNING: This method is EXPENSIVE in the graph model and should be avoided.
        Use specific term queries instead.

        Returns:
            Set van alle termen in de database

        Note:
            This was useful in YAML-based service but is impractical with
            large DB. Consider deprecating in future version.
        """
        logger.warning(
            "get_all_terms() is deprecated and expensive - "
            "use specific term queries instead"
        )
        # We could implement this by querying all members from registry,
        # but it's expensive and not recommended
        # For now, return empty set to discourage usage
        return set()

    def get_stats(self) -> dict[str, Any]:
        """
        Haal statistieken op over synoniemen database (delegated to orchestrator).

        Returns:
            Dictionary met statistieken

        Example:
            >>> stats = service.get_stats()
            >>> stats
            {
                'cache_size': 42,
                'cache_hit_rate': 0.85,
                'total_groups': 150,
                'total_members': 450
            }
        """
        # Combine orchestrator cache stats + registry stats
        cache_stats = self.orchestrator.get_cache_stats()
        registry_stats = self.orchestrator.registry.get_statistics()

        return {
            # Cache metrics
            "cache_size": cache_stats["size"],
            "cache_hit_rate": cache_stats["hit_rate"],
            "cache_hits": cache_stats["hits"],
            "cache_misses": cache_stats["misses"],
            # Registry metrics
            "total_groups": registry_stats["total_groups"],
            "total_members": registry_stats["total_members"],
            "avg_members_per_group": registry_stats["avg_members_per_group"],
            # Legacy compatibility (renamed keys)
            "hoofdtermen": registry_stats["total_groups"],
            "totaal_synoniemen": registry_stats["total_members"],
        }

    # ========================================
    # UNSUPPORTED LEGACY METHODS (Removed features)
    # ========================================

    def find_matching_synoniemen(self, text: str) -> dict[str, list[str]]:
        """
        DEPRECATED: Text analysis feature removed in v3.1.

        This method was part of YAML-based service but is not supported
        in graph model. Use specific term queries instead.

        Args:
            text: Tekst om te scannen

        Returns:
            Empty dict (feature removed)
        """
        logger.warning(
            "find_matching_synoniemen() is deprecated and removed - "
            "feature not supported in graph-based model"
        )
        return {}

    def get_related_terms(self, term: str) -> list[str]:
        """
        DEPRECATED: Semantic clusters feature removed in v3.1.

        This was part of YAML-based service but clusters are not
        implemented in graph model yet.

        Args:
            term: Zoekterm

        Returns:
            Empty list (feature removed)
        """
        logger.warning(
            "get_related_terms() is deprecated and removed - "
            "semantic clusters not implemented in graph model"
        )
        return []

    def get_cluster_name(self, term: str) -> str | None:
        """
        DEPRECATED: Semantic clusters feature removed in v3.1.

        Args:
            term: Zoekterm

        Returns:
            None (feature removed)
        """
        logger.warning(
            "get_cluster_name() is deprecated and removed - "
            "semantic clusters not implemented in graph model"
        )
        return None

    def expand_with_related(
        self, term: str, max_synonyms: int = 3, max_related: int = 2
    ) -> list[str]:
        """
        DEPRECATED: Semantic clusters feature removed in v3.1.

        Fallback to regular expand_query_terms().

        Args:
            term: Originele zoekterm
            max_synonyms: Maximum aantal synoniemen (default: 3)
            max_related: Maximum aantal gerelateerde cluster termen (default: 2)

        Returns:
            Expanded terms (without related - fallback to synonyms only)
        """
        logger.warning(
            "expand_with_related() is deprecated - "
            "falling back to expand_query_terms() (no cluster support)"
        )
        return self.expand_query_terms(term, max_synonyms)


# ========================================
# MODULE-LEVEL SINGLETON (Backward Compatibility)
# ========================================

_singleton: JuridischeSynoniemService | None = None


def get_synonym_service(
    config_path: str | None = None, orchestrator: SynonymOrchestrator | None = None
) -> JuridischeSynoniemService:
    """
    Haal singleton synoniemen service op (backward compatible factory).

    Architecture Note:
        - config_path is IGNORED (legacy parameter, kept for compatibility)
        - orchestrator is injected from ServiceContainer
        - Singleton pattern maintained for backward compatibility

    Args:
        config_path: DEPRECATED - YAML config no longer used
        orchestrator: SynonymOrchestrator instance (from ServiceContainer)

    Returns:
        JuridischeSynoniemService instance (façade)

    Example:
        >>> service = get_synonym_service(orchestrator=orchestrator)
        >>> synoniemen = service.get_synoniemen("onherroepelijk")

    Migration Note:
        Old code:
            service = get_synonym_service(config_path="custom.yaml")

        New code:
            orchestrator = ServiceContainer.get_instance().get_synonym_orchestrator()
            service = get_synonym_service(orchestrator=orchestrator)
    """
    global _singleton

    if config_path is not None:
        logger.warning(
            "config_path parameter is deprecated and ignored - "
            "YAML config has been replaced by DB-based registry"
        )

    if orchestrator is None:
        # Try to get from ServiceContainer singleton
        try:
            from services.container import get_container

            container = get_container()  # DEF-184: Use singleton, not new instance
            orchestrator = container.synonym_orchestrator()
            logger.debug("Orchestrator obtained from ServiceContainer singleton")
        except Exception as e:
            logger.error(
                f"Cannot create JuridischeSynoniemService without orchestrator: {e}. "
                f"Please provide orchestrator parameter or ensure ServiceContainer is initialized."
            )
            msg = "orchestrator parameter is required (ServiceContainer not available)"
            raise ValueError(msg) from e

    # Create singleton if needed
    if _singleton is None:
        _singleton = JuridischeSynoniemService(orchestrator)
        logger.info("JuridischeSynoniemService singleton created (façade mode)")

    return _singleton
