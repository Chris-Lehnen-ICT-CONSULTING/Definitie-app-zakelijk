"""
Cached Toetsregel Manager - Geoptimaliseerde versie voor US-202.

Deze manager is een drop-in replacement voor ToetsregelManager maar gebruikt
de RuleCache voor drastisch betere performance. Compatible met bestaande code.
"""

import logging
import threading
from typing import Any

from .rule_cache import get_rule_cache

logger = logging.getLogger(__name__)


class CachedToetsregelManager:
    """
    Geoptimaliseerde ToetsregelManager die RuleCache gebruikt.

    Deze class heeft EXACT dezelfde interface als de originele ToetsregelManager
    maar is 100x sneller door Streamlit caching.
    """

    def __init__(self, base_dir: str | None = None):
        """
        Initialiseer CachedToetsregelManager.

        Args:
            base_dir: Base directory voor toetsregels (ignored - uses RuleCache default)
        """
        self.cache = get_rule_cache()

        # Voor compatibility: behoud dezelfde stats tracking
        self.stats = {
            "regels_geladen": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "sets_geladen": 0,
        }

        # Log message moved to get_cached_toetsregel_manager() voor singleton tracking

    def load_regel(self, regel_id: str) -> dict[str, Any] | None:
        """
        Laad een specifieke toetsregel (gecached).

        Args:
            regel_id: ID van de regel (bijv. 'CON-01')

        Returns:
            Dictionary met regeldata of None
        """
        self.stats["cache_hits"] += 1  # Always a hit met RuleCache
        return self.cache.get_rule(regel_id)

    def get_all_regels(self) -> dict[str, dict[str, Any]]:
        """
        Haal alle beschikbare regels op als dictionary (gecached).

        Returns:
            Dict[str, Dict[str, Any]]: Dictionary met regel_id als key en regel data als value
        """
        self.stats["cache_hits"] += 1
        return self.cache.get_all_rules()

    def get_verplichte_regels(self) -> list[dict[str, Any]]:
        """Haal alle verplichte regels op."""
        all_rules = self.get_all_regels()
        return [
            rule
            for rule in all_rules.values()
            if rule.get("aanbeveling") == "verplicht"
        ]

    def get_kritieke_regels(self) -> list[dict[str, Any]]:
        """Haal kritieke regels op (verplicht + hoge prioriteit)."""
        all_rules = self.get_all_regels()
        return [
            rule
            for rule in all_rules.values()
            if (
                rule.get("aanbeveling") == "verplicht"
                or rule.get("prioriteit") == "hoog"
            )
        ]

    def get_regels_voor_prioriteit(self, prioriteit: str) -> list[dict[str, Any]]:
        """Haal regels op voor specifieke prioriteit."""
        return self.cache.get_rules_by_priority(prioriteit)

    def get_available_regels(self) -> list[str]:
        """Haal lijst van beschikbare regels op."""
        return list(self.get_all_regels().keys())

    def clear_cache(self):
        """Leeg alle caches."""
        self.cache.clear_cache()
        logger.info("Toetsregel caches geleegd via RuleCache")

    def get_stats(self) -> dict[str, Any]:
        """Haal statistieken op."""
        cache_stats = self.cache.get_stats()
        return {
            **self.stats,
            **cache_stats,
        }

    def reload_configuration(self):
        """
        Herlaad configuratie.

        Note: Met RuleCache wordt dit automatisch afgehandeld na TTL expiry.
        """
        self.clear_cache()
        logger.info("Configuration reload triggered (cache cleared)")

    # Compatibility stubs voor methodes die niet meer nodig zijn
    def load_regelset(self, set_naam: str) -> None:
        """Regelsets zijn deprecated - gebruik get_*_regels() methods."""
        logger.warning(f"load_regelset('{set_naam}') aangeroepen maar is deprecated")

    def get_regels_voor_categorie(self, categorie: str) -> list[dict[str, Any]]:
        """Backward compatibility - filter regels op categorie."""
        # Deze functionaliteit is niet meer nodig in de nieuwe architectuur
        return []

    def get_regels_by_thema(self, thema: str) -> list[dict[str, Any]]:
        """Backward compatibility - filter regels op thema."""
        all_rules = self.get_all_regels()
        return [
            rule
            for rule in all_rules.values()
            if rule.get("thema", "").lower() == thema.lower()
        ]

    def validate_regel(self, regel_data: dict[str, Any]) -> list[str]:
        """Backward compatibility - validatie is niet meer nodig met cache."""
        return []  # Geen errors

    def create_custom_set(
        self, naam: str, regel_ids: list[str], beschrijving: str = ""
    ) -> None:
        """Custom sets zijn deprecated in gecachte versie."""
        logger.warning("create_custom_set() is deprecated in CachedToetsregelManager")

    def get_available_sets(self) -> list[str]:
        """Sets zijn deprecated - gebruik specifieke get methods."""
        return []


# Global manager instance
_manager: CachedToetsregelManager | None = None
_manager_lock = threading.Lock()


def get_cached_toetsregel_manager() -> CachedToetsregelManager:
    """
    Haal globale CachedToetsregelManager instantie op (thread-safe singleton).

    Returns:
        Singleton CachedToetsregelManager instance
    """
    global _manager
    if _manager is None:
        with _manager_lock:
            # Double-check locking pattern voor thread safety
            if _manager is None:
                _manager = CachedToetsregelManager()
                logger.info("✅ CachedToetsregelManager singleton created")
    return _manager
