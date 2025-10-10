"""
SynonymOrchestrator - Business logic layer voor Synonym Orchestrator Architecture v3.1.

Deze module implementeert de orchestrator laag die:
- TTL caching met invalidatie biedt
- Governance policy enforcement toepast
- GPT-4 enrichment coördineert (sync tijdens definitiegeneratie)
- Cache metrics tracked

Architecture Reference:
    docs/architectuur/synonym-orchestrator-architecture-v3.1.md
    Lines 326-502: SynonymOrchestrator specification
"""

import asyncio
import json
import logging
import threading
from collections import OrderedDict
from datetime import UTC, datetime
from typing import Any

from config.synonym_config import SynonymPolicy, get_synonym_config
from models.synonym_models import WeightedSynonym
from repositories.synonym_registry import SynonymRegistry
from services.gpt4_synonym_suggester import GPT4SynonymSuggester

logger = logging.getLogger(__name__)
enrichment_logger = logging.getLogger("synonym_enrichment")


def _setup_enrichment_logger():
    """
    Setup dedicated file handler voor enrichment logging.

    Configured once at module level - enrichment logs go to dedicated file
    for easier monitoring and debugging of GPT-4 enrichment flow.

    Log Format:
        2025-10-10 14:32:15 - INFO - Starting GPT-4 enrichment for 'term'
        2025-10-10 14:32:23 - INFO - Enrichment complete: 3 suggestions, 8.2s
        2025-10-10 14:32:45 - ERROR - GPT-4 timeout for 'term' after 30.1s
    """
    # Only setup once (idempotent)
    if enrichment_logger.handlers:
        return

    # Create logs directory if not exists
    import os

    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)

    # File handler: logs/synonym_enrichment.log
    file_handler = logging.FileHandler(
        os.path.join(logs_dir, "synonym_enrichment.log"), encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)

    # Console handler voor errors/warnings
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)

    # Format: timestamp - level - message
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers
    enrichment_logger.addHandler(file_handler)
    enrichment_logger.addHandler(console_handler)
    enrichment_logger.setLevel(logging.DEBUG)

    # Prevent propagation to root logger (avoid duplicate logs)
    enrichment_logger.propagate = False

    enrichment_logger.info("Enrichment logger initialized")


# Setup enrichment logger at module load
_setup_enrichment_logger()


class SynonymOrchestrator:
    """
    Business logic voor synonym operations.

    Responsibilities:
    - Get synonyms met governance policy enforcement
    - TTL caching met invalidatie
    - GPT-4 enrichment (sync tijdens definitiegeneratie)
    - Usage tracking

    Architecture:
        Cache Layer (TTL) → Registry Layer (DB) → GPT-4 Enrichment
    """

    def __init__(self, registry: SynonymRegistry, gpt4_suggester: GPT4SynonymSuggester):
        """
        Initialiseer orchestrator met dependencies.

        Args:
            registry: SynonymRegistry voor DB toegang
            gpt4_suggester: GPT4SynonymSuggester voor AI enrichment
        """
        self.registry = registry
        self.gpt4_suggester = gpt4_suggester
        self.config = get_synonym_config()  # Centraal!

        # TTL Cache: {term_normalized: (synonyms, timestamp, version)}
        # Version counter pattern prevents race conditions during invalidation
        # Using OrderedDict for O(1) LRU eviction
        self._cache: OrderedDict[str, tuple[list[WeightedSynonym], datetime, int]] = (
            OrderedDict()
        )
        self._cache_lock = threading.RLock()  # Reentrant lock voor thread safety
        self._cache_version = 0  # Global version counter (incremented on invalidation)
        self._cache_hits = 0
        self._cache_misses = 0

        logger.info(
            f"SynonymOrchestrator initialized: "
            f"policy={self.config.policy.value}, "
            f"cache_ttl={self.config.cache_ttl_seconds}s, "
            f"min_synonyms={self.config.min_synonyms_threshold}"
        )

    # ========================================
    # CORE QUERY METHODS
    # ========================================

    def get_synonyms_for_lookup(
        self, term: str, max_results: int = 5, min_weight: float | None = None
    ) -> list[WeightedSynonym]:
        """
        Get synonyms met TTL cache + governance.

        Dit is de CORE query method voor alle synonym lookups.

        Priority (ORDER BY):
        1. Preferred members (is_preferred=TRUE)
        2. Active members (status='active', weight >= threshold)
        3. AI pending (ONLY if policy='pragmatic')

        Cache Logic:
        - Check TTL: timestamp < cache_ttl_seconds → cache HIT
        - If expired OR not exists → query registry → store in cache

        Args:
            term: De term om synoniemen voor te vinden
            max_results: Maximum aantal resultaten (default: 5)
            min_weight: Minimum gewicht threshold
                (default: config.min_weight_for_weblookup)

        Returns:
            Lijst van WeightedSynonym objecten (sorted by priority)

        Architecture Reference:
            Lines 356-398: get_synonyms_for_lookup specification
        """
        if not term or not term.strip():
            return []

        term_normalized = term.lower().strip()

        # Check cache
        if self._is_cached(term_normalized):
            self._cache_hits += 1
            cached_synonyms = self._get_from_cache(term_normalized)
            result_count = len(cached_synonyms[:max_results])
            logger.debug(f"Cache HIT for '{term}' (returned {result_count} results)")
            return cached_synonyms[:max_results]

        # Cache miss - query registry
        self._cache_misses += 1
        logger.debug(f"Cache MISS for '{term}' (querying registry)")

        # Determine statuses (governance policy!)
        statuses = ["active"]
        if self.config.policy == SynonymPolicy.PRAGMATIC:
            statuses.append("ai_pending")
            logger.debug(
                f"Governance policy: {self.config.policy.value} (allowing ai_pending)"
            )
        else:
            logger.debug(
                f"Governance policy: {self.config.policy.value} (strict - active only)"
            )

        # Query registry
        min_weight = min_weight or self.config.min_weight_for_weblookup

        try:
            synonyms = self.registry.get_synonyms(
                term=term_normalized,
                statuses=statuses,
                min_weight=min_weight,
                order_by=None,  # Use default ordering
                limit=max_results * 2,  # Cache extra voor future queries
            )

            # Store in cache
            self._store_in_cache(term_normalized, synonyms)

            logger.info(
                f"Found {len(synonyms)} synonyms for '{term}' "
                f"(statuses: {statuses}, min_weight: {min_weight})"
            )

            return synonyms[:max_results]

        except Exception as e:
            logger.error(f"Registry query failed for '{term}': {e}", exc_info=True)
            return []  # Fail gracefully

    async def ensure_synonyms(
        self, term: str, min_count: int = 5, context: dict | None = None
    ) -> tuple[list[WeightedSynonym], int]:
        """
        Ensure term has min_count synoniemen (GPT-4 sync OK!).

        Called VÓÓRdat definitiegeneratie start. Als er onvoldoende synoniemen
        zijn in de registry, wordt GPT-4 enrichment getriggerd (sync blocking).

        Flow:
        1. Check existing via get_synonyms_for_lookup()
        2. If >= min_count → return existing (fast path ✅)
        3. Else → GPT-4 enrichment (slow path):
           - Call GPT-4 suggester (with timeout)
           - Save suggestions as ai_pending (NOT active!)
           - Re-fetch synonyms (nu met ai_pending if policy allows)
           - Return enriched list

        Args:
            term: De term om synoniemen voor te vinden
            min_count: Minimum aantal synoniemen (default: 5)
            context: Optionele context dict met:
                - 'definitie': Definitie text voor context
                - 'tokens': Extra tokens voor GPT-4
                - 'domain': Juridisch domein

        Returns:
            Tuple van (synonyms, ai_pending_count):
            - synonyms: Lijst van WeightedSynonym objecten
            - ai_pending_count: Aantal nieuwe AI suggesties toegevoegd

        Architecture Reference:
            Lines 400-482: ensure_synonyms flow specification
        """
        if not term or not term.strip():
            return [], 0

        # Check existing
        existing = self.get_synonyms_for_lookup(term, max_results=10)

        if len(existing) >= min_count:
            enrichment_logger.info(
                f"Cache hit for '{term}' (has {len(existing)} >= {min_count})"
            )
            return existing[:min_count], 0  # ✅ Fast path

        # Slow path: GPT-4 enrichment (sync blocking OK - user clicked "Genereer")
        enrichment_logger.info(
            f"Starting GPT-4 enrichment for '{term}' "
            f"(only {len(existing)} found, need {min_count})"
        )

        start_time = datetime.now(UTC)

        try:
            # Call GPT-4 with timeout
            ai_suggestions = await asyncio.wait_for(
                self.gpt4_suggester.suggest_synonyms(
                    term=term,
                    definitie=context.get("definitie") if context else None,
                    context=context.get("tokens") if context else None,
                ),
                timeout=self.config.gpt4_timeout_seconds,
            )

            duration = (datetime.now(UTC) - start_time).total_seconds()

            # Handle empty suggestions (placeholder mode or no results)
            if not ai_suggestions:
                enrichment_logger.warning(
                    f"GPT-4 returned no suggestions for '{term}' "
                    f"(duration: {duration:.2f}s)"
                )
                return existing, 0

            # Save as ai_pending (NOT active - requires approval!)
            group = self.registry.get_or_create_group(
                canonical_term=term, created_by="gpt4_enrichment"
            )

            ai_count = 0
            for suggestion in ai_suggestions:
                try:
                    self.registry.add_group_member(
                        group_id=group.id,
                        term=suggestion.synoniem,
                        weight=suggestion.confidence,
                        status="ai_pending",  # Governance gate!
                        source="ai_suggested",
                        context_json=json.dumps(
                            {
                                "rationale": suggestion.rationale,
                                "model": "gpt-4-turbo",
                                "triggered_by": "definition_generation",
                                "timestamp": datetime.now(UTC).isoformat(),
                            }
                        ),
                        created_by="gpt4_suggester",
                    )
                    ai_count += 1
                except ValueError as e:
                    # Handle duplicates or validation errors gracefully
                    enrichment_logger.warning(
                        f"Failed to add suggestion '{suggestion.synoniem}' "
                        f"for '{term}': {e}"
                    )

            enrichment_logger.info(
                f"Enrichment complete for '{term}': "
                f"{ai_count} suggestions added, duration: {duration:.2f}s"
            )

            # Invalidate cache (force refresh)
            self.invalidate_cache(term)

            # Re-fetch (nu met ai_pending if policy allows)
            enriched = self.get_synonyms_for_lookup(term, max_results=10)

            return enriched[:min_count], ai_count

        except TimeoutError:
            duration = (datetime.now(UTC) - start_time).total_seconds()
            enrichment_logger.error(
                f"GPT-4 timeout for '{term}' after {duration:.2f}s "
                f"(timeout threshold: {self.config.gpt4_timeout_seconds}s)"
            )
            return existing, 0  # Fail gracefully

        except Exception as e:
            duration = (datetime.now(UTC) - start_time).total_seconds()
            enrichment_logger.error(
                f"GPT-4 enrichment failed for '{term}' after {duration:.2f}s: {e}",
                exc_info=True,
            )
            return existing, 0  # Fail gracefully

    # ========================================
    # CACHE MANAGEMENT
    # ========================================

    def _is_cached(self, term_normalized: str) -> bool:
        """
        Check if term is in cache AND not expired (TTL + version check).

        Version counter pattern: Cache entry is invalid if version doesn't match
        current global version. This prevents race conditions where Thread A reads
        stale data after Thread B invalidates the cache.

        Args:
            term_normalized: Normalized term (lowercase, stripped)

        Returns:
            True als cached AND niet expired AND version matches, anders False
        """
        with self._cache_lock:
            if term_normalized not in self._cache:
                return False

            # Check version (prevents race condition)
            _, timestamp, version = self._cache[term_normalized]
            if version != self._cache_version:
                # Version mismatch - cache was invalidated
                del self._cache[term_normalized]
                logger.debug(
                    f"Cache entry invalidated for '{term_normalized}' "
                    f"(version mismatch: {version} != {self._cache_version})"
                )
                return False

            # Check TTL
            age_seconds = (datetime.now(UTC) - timestamp).total_seconds()

            if age_seconds >= self.config.cache_ttl_seconds:
                # Expired - remove from cache
                del self._cache[term_normalized]
                logger.debug(
                    f"Cache entry expired for '{term_normalized}' "
                    f"(age: {age_seconds:.1f}s)"
                )
                return False

            # Mark as recently used (LRU update)
            self._cache.move_to_end(term_normalized)

            return True

    def _get_from_cache(self, term_normalized: str) -> list[WeightedSynonym]:
        """
        Haal synoniemen uit cache (assumes _is_cached returned True).

        Args:
            term_normalized: Normalized term

        Returns:
            Lijst van WeightedSynonym objecten
        """
        with self._cache_lock:
            synonyms, _, _ = self._cache[term_normalized]
            return synonyms

    def _store_in_cache(self, term_normalized: str, synonyms: list[WeightedSynonym]):
        """
        Store synoniemen in cache met timestamp.

        Implements max size enforcement (O(1) LRU eviction via OrderedDict).

        Args:
            term_normalized: Normalized term
            synonyms: Lijst van WeightedSynonym objecten
        """
        with self._cache_lock:
            # Enforce max size (O(1) LRU eviction)
            if len(self._cache) >= self.config.cache_max_size and self._cache:
                # Remove oldest entry (first item in OrderedDict) - O(1) operation
                oldest_term, _ = self._cache.popitem(last=False)
                logger.debug(
                    f"Cache size limit reached ({self.config.cache_max_size}), "
                    f"evicted oldest entry: '{oldest_term}'"
                )

            # Store with timestamp, version, and mark as recently used
            self._cache[term_normalized] = (
                synonyms,
                datetime.now(UTC),
                self._cache_version,
            )
            self._cache.move_to_end(term_normalized)  # Mark as recently used
            logger.debug(
                f"Cached {len(synonyms)} synonyms for '{term_normalized}' "
                f"(cache size: {len(self._cache)})"
            )

    def invalidate_cache(self, term: str | None = None):
        """
        Invalidate cache (called by registry callbacks).

        Dit wordt aangeroepen door SynonymRegistry wanneer data verandert
        (via registered callback).

        Uses version counter pattern: incrementing global version invalidates
        all existing entries without actually deleting them (lazy invalidation).

        Args:
            term: De term om te invalideren (None = flush ALL)
        """
        with self._cache_lock:
            if term:
                # Increment version to invalidate (prevents race conditions)
                self._cache_version += 1
                term_normalized = term.lower().strip()

                # Also delete the specific entry for memory efficiency
                if term_normalized in self._cache:
                    del self._cache[term_normalized]
                    logger.info(
                        f"Cache invalidated for '{term}' "
                        f"(version incremented to {self._cache_version})"
                    )
                else:
                    logger.debug(
                        f"Cache invalidation requested for '{term}' (not cached), "
                        f"version incremented to {self._cache_version}"
                    )
            else:
                # Flush all via version counter increment (O(1) invalidation!)
                cache_size = len(self._cache)
                self._cache_version += 1
                self._cache.clear()  # Clear for memory efficiency
                logger.info(
                    f"Cache flushed (all {cache_size} entries removed, "
                    f"version incremented to {self._cache_version})"
                )

    # ========================================
    # CACHE METRICS
    # ========================================

    @property
    def cache_hit_rate(self) -> float:
        """
        Cache performance metric.

        Returns:
            Hit rate als float (0.0-1.0), 0.0 als geen queries yet
        """
        total = self._cache_hits + self._cache_misses
        return self._cache_hits / total if total > 0 else 0.0

    def get_cache_stats(self) -> dict[str, Any]:
        """
        Get cache statistics voor monitoring.

        Returns:
            Dictionary met cache metrics:
            - size: Huidige aantal entries in cache
            - hits: Totaal aantal cache hits
            - misses: Totaal aantal cache misses
            - hit_rate: Hit rate percentage (0.0-1.0)
            - max_size: Maximum cache size (config)
            - ttl_seconds: TTL in seconden (config)
        """
        with self._cache_lock:
            return {
                "size": len(self._cache),
                "hits": self._cache_hits,
                "misses": self._cache_misses,
                "hit_rate": self.cache_hit_rate,
                "max_size": self.config.cache_max_size,
                "ttl_seconds": self.config.cache_ttl_seconds,
            }

    def reset_cache_stats(self):
        """
        Reset cache statistics (voor testing).

        Gebruikt in unit tests om metrics te resetten tussen tests.
        """
        with self._cache_lock:
            self._cache_hits = 0
            self._cache_misses = 0
            logger.debug("Cache statistics reset")

    # ========================================
    # UTILITY METHODS
    # ========================================

    def get_health_check(self) -> dict[str, Any]:
        """
        Health check voor monitoring.

        Returns:
            Dictionary met health status:
            - status: 'healthy' of 'unhealthy'
            - cache_stats: Cache metrics
            - registry_stats: Registry statistics
            - config: Current configuration
        """
        try:
            cache_stats = self.get_cache_stats()
            registry_stats = self.registry.get_statistics()

            # Determine health status
            status = "healthy"
            warnings = []

            # Check cache hit rate
            total_queries = cache_stats["hits"] + cache_stats["misses"]
            if cache_stats["hit_rate"] < 0.5 and total_queries > 100:
                warnings.append(f"Low cache hit rate: {cache_stats['hit_rate']:.1%}")

            # Check registry
            if registry_stats["total_groups"] == 0:
                warnings.append("Registry is empty (no synonym groups)")

            if warnings:
                status = "warning"

            return {
                "status": status,
                "warnings": warnings,
                "cache_stats": cache_stats,
                "registry_stats": registry_stats,
                "config": self.config.to_dict(),
                "timestamp": datetime.now(UTC).isoformat(),
            }

        except Exception as e:
            logger.error(f"Health check failed: {e}", exc_info=True)
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(UTC).isoformat(),
            }
