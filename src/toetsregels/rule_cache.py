"""
Rule Cache voor geoptimaliseerde validatieregel loading.

Deze implementatie laadt JSON-regelbestanden één keer en cachet ze in
een proces-lokale cache (TTL via utils.cache). Dit minimaliseert IO,
behoudt een kleine memory footprint en is direct integreerbaar met
ModularValidationService — zonder UI/Streamlit-afhankelijkheid.
"""

import contextlib
import json
import logging
import threading
from pathlib import Path
from typing import Any

from utils.cache import cached, clear_cache as _global_cache_clear

logger = logging.getLogger(__name__)

# Import monitoring infrastructure
try:
    from monitoring.cache_monitoring import CacheMonitor

    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False
    logger.warning("Cache monitoring not available, continuing without monitoring")


@cached(ttl=3600)
def _load_all_rules_cached(regels_dir: str) -> dict[str, dict[str, Any]]:
    """
    Load alle validatieregels van disk met pure-Python caching.

    Deze functie wordt SLECHTS EENMAAL uitgevoerd per uur (ttl=3600).
    Alle volgende calls returnen de gecachte data direct uit memory.

    Args:
        regels_dir: Path naar de regels directory

    Returns:
        Dictionary met regel_id als key en regel data als value
    """
    rules_path = Path(regels_dir)
    all_rules = {}

    if not rules_path.exists():
        logger.warning(f"Regels directory bestaat niet: {regels_dir}")
        return all_rules

    # Load alle JSON files in één keer
    json_files = sorted(rules_path.glob("*.json"))
    logger.info(f"Loading {len(json_files)} regel files van {regels_dir}")

    for json_file in json_files:
        regel_id = json_file.stem
        try:
            with open(json_file, encoding="utf-8") as f:
                regel_data = json.load(f)
                # Bewaar alle velden voor completeness (validatie + prompt generation)
                # Memory cost: ~300KB extra voor 45 regels (negligible)
                all_rules[regel_id] = {
                    "id": regel_data.get("id", regel_id),
                    "naam": regel_data.get("naam", ""),
                    "prioriteit": regel_data.get("prioriteit", "midden"),
                    "aanbeveling": regel_data.get("aanbeveling", "optioneel"),
                    # Pattern fields (voor validatie)
                    "herkenbaar_patronen": regel_data.get("herkenbaar_patronen", []),
                    "herkenbaar_patronen_type": regel_data.get(
                        "herkenbaar_patronen_type", []
                    ),
                    "herkenbaar_patronen_particulier": regel_data.get(
                        "herkenbaar_patronen_particulier", []
                    ),
                    "herkenbaar_patronen_proces": regel_data.get(
                        "herkenbaar_patronen_proces", []
                    ),
                    "herkenbaar_patronen_resultaat": regel_data.get(
                        "herkenbaar_patronen_resultaat", []
                    ),
                    "weight": regel_data.get("weight"),  # Als aanwezig
                    # Content fields (voor prompt generation) - DEF-156 fix
                    "uitleg": regel_data.get("uitleg", ""),
                    "toetsvraag": regel_data.get("toetsvraag", ""),
                    "goede_voorbeelden": regel_data.get("goede_voorbeelden", []),
                    "foute_voorbeelden": regel_data.get("foute_voorbeelden", []),
                }
        except Exception as e:
            logger.error(f"Fout bij laden regel {regel_id}: {e}")
            continue

    logger.info(f"✅ {len(all_rules)} regels succesvol geladen en gecached")
    return all_rules


@cached(ttl=3600)
def _load_single_rule_cached(regels_dir: str, regel_id: str) -> dict[str, Any] | None:
    """
    Load een enkele regel met caching.

    Args:
        regels_dir: Path naar de regels directory
        regel_id: ID van de regel (bijv. 'CON-01')

    Returns:
        Dictionary met regeldata of None
    """
    regel_path = Path(regels_dir) / f"{regel_id}.json"

    if not regel_path.exists():
        logger.warning(f"Regel bestand niet gevonden: {regel_path}")
        return None

    try:
        with open(regel_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Fout bij laden regel {regel_id}: {e}")
        return None


class RuleCache:
    """
    Singleton cache voor validatieregels met thread-safe initialization.

    Deze class biedt een clean interface voor regel access terwijl
    alle caching wordt afgehandeld door de @cached decorator.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                # Double-check locking pattern voor thread safety
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # Default naar src/toetsregels/regels directory
        self.regels_dir = Path(__file__).parent / "regels"
        self._initialized = True

        # Track statistics
        self.stats = {
            "get_all_calls": 0,
            "get_single_calls": 0,
        }

        # Initialize monitoring
        if MONITORING_AVAILABLE:
            self._monitor = CacheMonitor("RuleCache", enabled=True)
            logger.info(f"RuleCache geïnitialiseerd met monitoring: {self.regels_dir}")
        else:
            self._monitor = None
            logger.info(
                f"RuleCache geïnitialiseerd zonder monitoring: {self.regels_dir}"
            )

    def get_all_rules(self) -> dict[str, dict[str, Any]]:
        """
        Haal alle regels op (gecached).

        Returns:
            Dictionary met alle regels
        """
        self.stats["get_all_calls"] += 1

        # Track operation if monitoring is enabled
        if self._monitor:
            with self._monitor.track_operation("get_all", "all_rules") as result:
                # Check if this is a cache hit or miss
                # Since we're using @cached decorator, we can't directly detect
                # but we can track the call
                rules = _load_all_rules_cached(str(self.regels_dir))

                # Heuristic: if this is the first call, it's a miss
                if self.stats["get_all_calls"] == 1:
                    result["result"] = "miss"
                    result["source"] = "disk"
                else:
                    result["result"] = "hit"
                    result["source"] = "memory"

                return rules
        else:
            return _load_all_rules_cached(str(self.regels_dir))

    def get_rule(self, regel_id: str) -> dict[str, Any] | None:
        """
        Haal een specifieke regel op (gecached).

        Args:
            regel_id: ID van de regel

        Returns:
            Regel data of None
        """
        self.stats["get_single_calls"] += 1

        if self._monitor:
            with self._monitor.track_operation("get_single", regel_id) as result:
                # Probeer eerst uit de bulk cache
                all_rules = self.get_all_rules()
                if regel_id in all_rules:
                    result["result"] = "hit"
                    result["source"] = "memory"
                    return all_rules[regel_id]

                # Fallback naar single rule loading
                rule = _load_single_rule_cached(str(self.regels_dir), regel_id)
                if rule:
                    result["result"] = "miss"
                    result["source"] = "disk"
                else:
                    result["result"] = "miss"
                    result["source"] = "not_found"
                return rule
        else:
            # Probeer eerst uit de bulk cache
            all_rules = self.get_all_rules()
            if regel_id in all_rules:
                return all_rules[regel_id]

            # Fallback naar single rule loading
            return _load_single_rule_cached(str(self.regels_dir), regel_id)

    def get_rules_by_priority(self, priority: str) -> list[dict[str, Any]]:
        """
        Haal regels op gefilterd op prioriteit.

        Args:
            priority: 'hoog', 'midden', of 'laag'

        Returns:
            List van regels met de gegeven prioriteit
        """
        all_rules = self.get_all_rules()
        return [
            rule for rule in all_rules.values() if rule.get("prioriteit") == priority
        ]

    def get_rule_weights(self) -> dict[str, float]:
        """
        Haal weights mapping op voor alle regels.

        Returns:
            Dictionary met regel_id -> weight
        """
        all_rules = self.get_all_rules()
        weights = {}

        for regel_id, regel_data in all_rules.items():
            # Gebruik expliciete weight of bepaal op basis van prioriteit
            if "weight" in regel_data and regel_data["weight"] is not None:
                weights[regel_id] = float(regel_data["weight"])
            else:
                priority = regel_data.get("prioriteit", "midden")
                if priority == "hoog":
                    weights[regel_id] = 1.0
                elif priority == "midden":
                    weights[regel_id] = 0.7
                else:  # laag
                    weights[regel_id] = 0.4

        return weights

    def clear_cache(self):
        """
        Clear de cache voor regels.

        Let op: gebruikt de globale cachefacade en kan ook andere
        decorator-caches legen, conform eerdere Streamlit-clear semantiek.
        """
        if self._monitor:
            with self._monitor.track_operation("clear", "cache") as result:
                try:
                    _global_cache_clear()
                    result["result"] = "evict"
                    result["source"] = "all"
                except Exception:
                    result["result"] = "error"
                    result["source"] = "all"
                logger.info("Rule cache gecleared (global cache cleared)")
        else:
            with contextlib.suppress(Exception):
                _global_cache_clear()
            logger.info("Rule cache gecleared (global cache cleared)")

    def get_stats(self) -> dict[str, Any]:
        """Haal cache statistieken op."""
        all_rules = self.get_all_rules()
        stats = {
            **self.stats,
            "total_rules_cached": len(all_rules),
            "cache_dir": str(self.regels_dir),
        }

        # Add monitoring snapshot if available
        if self._monitor:
            snapshot = self._monitor.get_snapshot()
            stats["monitoring"] = {
                "hit_rate": snapshot.hit_rate,
                "avg_operation_ms": snapshot.avg_operation_ms,
                "hits": snapshot.hits,
                "misses": snapshot.misses,
                "total_operations": snapshot.total_entries,
            }

        return stats


# Global singleton instance
_rule_cache: RuleCache | None = None
_rule_cache_lock = threading.Lock()


def get_rule_cache() -> RuleCache:
    """
    Haal de globale RuleCache instance op (thread-safe singleton).

    Returns:
        Singleton RuleCache instance
    """
    global _rule_cache
    if _rule_cache is None:
        with _rule_cache_lock:
            # Double-check locking pattern voor thread safety
            if _rule_cache is None:
                _rule_cache = RuleCache()
    return _rule_cache
