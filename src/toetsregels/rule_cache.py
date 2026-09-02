"""
Rule Cache voor geoptimaliseerde validatieregel loading.

Deze implementatie laadt JSON-regelbestanden één keer en cachet ze in
een proces-lokale cache (TTL via utils.cache). Dit minimaliseert IO,
behoudt een kleine memory footprint en is direct integreerbaar met
ModularValidationService — zonder UI/Streamlit-afhankelijkheid.
"""

import logging
import threading
import time
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any, cast

from utils.cache import cached, clear_cache as _global_cache_clear

from .runtime_contract import (
    RuleContractError,
    build_rule_record,
    canonical_rule_id,
    lees_regelbestand,
    load_root_contract_policy,
    valideer_regelset,
)

logger = logging.getLogger(__name__)


def _index_op_canonieke_id(ids: Iterable[str]) -> dict[str, str]:
    """Canonieke ID -> oorspronkelijke schrijfwijze.

    De schrijfwijzen lopen historisch door elkaar (``CON-01``, ``CON_01``,
    ``ARAI01``). Vergelijken gebeurt op de canonieke vorm; melden gebeurt in
    de vorm die een lezer terugvindt in de regelmap of in de root-SSOT.
    """
    return {canonical_rule_id(rid): str(rid) for rid in ids if str(rid).strip()}


def _afwijking(links: Mapping[str, str], rechts: Mapping[str, str]) -> list[str]:
    """ID's die wél in ``links`` zitten en niet in ``rechts``.

    Gemeld in de oorspronkelijke schrijfwijze van de kant waar zij vandaan
    komen, zodat een lezer ze rechtstreeks terugvindt.
    """
    return sorted(links[k] for k in set(links) - set(rechts))


# TTL (seconden) voor de proces-lokale in-memory memo in RuleCache.
# Gelijk aan de @cached-TTL zodat memo en FileCache dezelfde levensduur delen.
_MEMO_TTL_S = 3600

# Import monitoring infrastructure
try:
    from monitoring.cache_monitoring import CacheMonitor

    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False
    logger.warning("Cache monitoring not available, continuing without monitoring")

# DEF-606: het uitvoerbare (normatieve) deel van het regelcontract — de
# velden die de evaluators onder services/validation/evaluators/ lezen. De
# overige JSON-velden zijn prompt-/documentatiemetadata (uitleg,
# toelichting, voorbeelden, brondocument, …). Het runtime-record bewaart
# ALLE bronvelden: de eerdere whitelist-projectie liet deze velden stil
# verdwijnen, waardoor de betrokken checks in productie nooit vuurden.
RUNTIME_VELDEN: tuple[str, ...] = (
    "aanbeveling",
    "circular_definition",
    "forbidden_phrases",
    "herkenbaar_patronen",
    "max_chars",
    "max_words",
    "min_chars",
    "min_commas",
    "min_words",
    "prioriteit",
    "redundancy_patterns",
    "required_patterns",
    "vereist_param",
)

# Sleutels waarvan consumers (validatie + prompt generation) op
# aanwezigheid rekenen; het record garandeert ze met deze defaults.
#
# DEF-606: hier staan uitsluitend OPTIONELE/compatibiliteitsvelden. De
# root-required velden (id, naam, uitleg, prioriteit, runtime_contract)
# stonden hier eerder óók — met lege defaults. Een bronrecord zonder `naam`
# of `prioriteit` kreeg die dan aangevuld en passeerde de contractcontrole
# alsnog: de default verborg precies het gat dat de controle moest vinden.
# Defaults worden nu pas toegepast ná succesvolle bronvalidatie.
_RECORD_DEFAULTS: dict[str, Any] = {
    "aanbeveling": "optioneel",
    "herkenbaar_patronen": [],
    "herkenbaar_patronen_type": [],
    "herkenbaar_patronen_particulier": [],
    "herkenbaar_patronen_proces": [],
    "herkenbaar_patronen_resultaat": [],
    "weight": None,
    "toetsvraag": "",
    "goede_voorbeelden": [],
    "foute_voorbeelden": [],
}


def _vers_record(regel_id: str, regel_data: dict[str, Any]) -> dict[str, Any]:
    """Bouw een record met vérse default-containers per regel.

    Uitsluitend aan te roepen op een reeds gevalideerd bronrecord.

    Een kale ``{**_RECORD_DEFAULTS, **regel_data}`` zou de default-lists
    delen tussen alle records die het veld niet zelf zetten; één in-place
    mutatie downstream zou dan naar alle regels lekken (en clear_cache
    overleven, want de lists zitten in de module-constante).
    """
    record: dict[str, Any] = {
        veld: (list(waarde) if isinstance(waarde, list) else waarde)
        for veld, waarde in _RECORD_DEFAULTS.items()
    }
    record.update(regel_data)
    return record


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

    if not rules_path.exists():
        logger.warning(f"Regels directory bestaat niet: {regels_dir}")
        return {}

    # Load alle JSON files in één keer
    json_files = sorted(rules_path.glob("*.json"))
    logger.info(f"Loading {len(json_files)} regel files van {regels_dir}")

    # DEF-606: fail-closed. De vorige versie sloeg een kapot bestand over met
    # logger.error + continue; die regel verdween dan een uur lang stil uit de
    # gecachte set. Een uitzondering hier laat het laden zichtbaar mislukken
    # en zet niets in de cache.
    bronrecords = {
        json_file.stem: lees_regelbestand(json_file) for json_file in json_files
    }

    # Valideer het ÓNBEWERKTE bronrecord: volledigheid tegen het manifest in
    # de root-SSOT plus het volledige RuleRecord-contract. Defaults mogen pas
    # daarna, anders vult een default een verplicht veld in en passeert een
    # kapot record alsnog.
    valideer_regelset(bronrecords, bron=f"RuleCache({regels_dir})")

    # Volledig runtime-record — álle bronvelden gaan mee (normatieve
    # uitvoeringsvelden mogen niet stil verdwijnen), defaults garanderen
    # sleutel-aanwezigheid voor de optionele velden. ~300KB voor 53 regels.
    all_rules = {
        regel_id: _vers_record(regel_id, data) for regel_id, data in bronrecords.items()
    }

    logger.info(f"✅ {len(all_rules)} regels geladen, gevalideerd en gecached")
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

    # DEF-606: alleen een ontbrekend bestand levert None; een bestaand maar
    # kapot bestand faalt zichtbaar in plaats van stil te verdwijnen. Het
    # losse pad is even streng als het bulkpad: ook hier moet het volledige
    # RuleRecord-contract kloppen, niet alleen de JSON-vorm.
    regel_data = lees_regelbestand(regel_path)
    build_rule_record(regel_id, regel_data)
    return regel_data


class RuleCache:
    """
    Singleton cache voor validatieregels met thread-safe initialization.

    Deze class biedt een clean interface voor regel access terwijl
    alle caching wordt afgehandeld door de @cached decorator.
    """

    _instance: "RuleCache | None" = None
    _lock = threading.Lock()
    _initialized: bool = False  # DEF-439: pattern 6 (class-level type-declaratie)

    def __new__(cls) -> "RuleCache":
        if cls._instance is None:
            with cls._lock:
                # Double-check locking pattern voor thread safety
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
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

        # DEF-496: proces-lokale in-memory memo voor de bulk-regels.
        # De @cached-loader leest bij elke hit nog van disk (FileCache.get →
        # safe_load); deze memo houdt het resultaat binnen de TTL in geheugen.
        self._rules_memo: dict[str, dict[str, Any]] | None = None
        self._rules_memo_ts: float = 0.0

        # Initialize monitoring
        # DEF-439: pattern 6 (union-annotatie vóór eerste assignment)
        self._monitor: CacheMonitor | None
        if MONITORING_AVAILABLE:
            self._monitor = CacheMonitor("RuleCache", enabled=True)
            logger.info(f"RuleCache geïnitialiseerd met monitoring: {self.regels_dir}")
        else:
            self._monitor = None
            logger.info(
                f"RuleCache geïnitialiseerd zonder monitoring: {self.regels_dir}"
            )

    def _load_all_rules(self) -> dict[str, dict[str, Any]]:
        """
        Haal de bulk-regels op uit de proces-lokale in-memory memo.

        Binnen de TTL wordt de eerder geladen dict direct uit geheugen
        teruggegeven, zodat get_all_rules() tijdens validatie niet
        herhaaldelijk ~300KB JSON van disk deserialiseert. Buiten de TTL
        (of na clear_cache) valt het terug op de @cached-loader. DEF-496.
        """
        now = time.monotonic()
        memo = self._rules_memo
        if memo is not None and (now - self._rules_memo_ts) < _MEMO_TTL_S:
            return memo

        rules = cast(
            dict[str, dict[str, Any]], _load_all_rules_cached(str(self.regels_dir))
        )
        self._rules_memo = rules
        self._rules_memo_ts = now
        return rules

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
                rules = self._load_all_rules()

                # Heuristic: if this is the first call, it's a miss
                if self.stats["get_all_calls"] == 1:
                    result["result"] = "miss"
                    result["source"] = "disk"
                else:
                    result["result"] = "hit"
                    result["source"] = "memory"

                return rules
        else:
            return self._load_all_rules()

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
                return cast(dict[str, Any] | None, rule)
        else:
            # Probeer eerst uit de bulk cache
            all_rules = self.get_all_rules()
            if regel_id in all_rules:
                return all_rules[regel_id]

            # Fallback naar single rule loading
            return cast(
                dict[str, Any] | None,
                _load_single_rule_cached(str(self.regels_dir), regel_id),
            )

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

    def clear_cache(self) -> None:
        """
        Clear de cache voor regels.

        Let op: gebruikt de globale cachefacade en kan ook andere
        decorator-caches legen, conform eerdere Streamlit-clear semantiek.
        """
        # DEF-496: invalideer de in-memory memo zodat een clear echt herlaadt.
        self._rules_memo = None
        self._rules_memo_ts = 0.0

        if self._monitor:
            with self._monitor.track_operation("clear", "cache") as result:
                try:
                    _global_cache_clear()
                    result["result"] = "evict"
                    result["source"] = "all"
                    logger.info("Rule cache gecleared (global cache cleared)")
                except (RuntimeError, OSError) as e:
                    result["result"] = "error"
                    result["source"] = "all"
                    logger.warning(f"Rule cache clear failed: {e}")
        else:
            try:
                _global_cache_clear()
                logger.info("Rule cache gecleared (global cache cleared)")
            except (RuntimeError, OSError) as e:
                logger.warning(f"Rule cache clear failed: {e}")

    @staticmethod
    def _contractregel_ids() -> tuple[str, ...]:
        """De verwachte regel-ID-set, vers uit de root-SSOT.

        Bewust niet via het met ``lru_cache`` afgedekte
        ``root_contract_policy()``: die geeft na een wijziging van de SSOT
        opnieuw de oude verwachting terug, en dan meet ``get_stats`` de
        volledigheid tegen een verouderd contract. De globale cache wordt
        hier niet geleegd - dat zou een verborgen neveneffect zijn voor elke
        andere lezer - en ``get_stats`` is een diagnosepad, geen validatiepad.
        """
        return load_root_contract_policy().rule_ids

    def get_stats(self) -> dict[str, Any]:
        """Haal cache statistieken op."""
        all_rules = self.get_all_rules()
        bestanden = sorted(self.regels_dir.glob("*.json"))

        # DEF-621: volledigheid is verzamelingsgelijkheid tegen de
        # contractuele ID-set, geen telling. ``len(all_rules) ==
        # files_on_disk`` was tautologisch: verdwijnen er 46 van de 53, dan
        # geldt 7 == 7, en bij nul bestanden meldt 0 == 0 een lege regelset
        # als compleet. Een onleesbare SSOT levert een lege verwachting op en
        # is daarmee nooit compleet - fail-closed, net als het validatiepad.
        #
        # Drie verzamelingen, niet twee. `get_all_rules()` levert binnen de
        # TTL een warme cache; verdwijnt daarna een regelbestand, dan blijft
        # die cache compleet terwijl de bron het contract niet meer dekt. Een
        # vergelijking van alleen verwacht en geladen zou dat bronverlies een
        # uur lang groen rapporteren. Alleen de stems tellen mee - er wordt
        # hier geen JSON gelezen en niets ge-invalideerd; dit is een
        # diagnosepad en mag geen cache-effect hebben.
        try:
            contract_ids = self._contractregel_ids()
        except RuleContractError as exc:
            logger.error(f"Contractuele regel-ID-set niet leesbaar: {exc}")
            contract_ids = ()
        verwacht = _index_op_canonieke_id(contract_ids)
        geladen = _index_op_canonieke_id(all_rules)
        op_schijf = _index_op_canonieke_id(pad.stem for pad in bestanden)

        stats = {
            **self.stats,
            "total_rules_cached": len(all_rules),
            "cache_dir": str(self.regels_dir),
            # DEF-621: zichtbare degraded-state — health/monitoring kan
            # hierop alarmeren i.p.v. dat een kapot regelbestand een uur
            # lang stil uit de set verdwijnt.
            "rules_files_on_disk": len(bestanden),
            # Het rúwe aantal contract-ID's, vóór canonieke samenvoeging:
            # anders zou de noemer meebewegen met een botsing.
            "rules_expected_count": len(contract_ids),
            # Gescheiden assen: de eerste twee gaan over de geladen set, de
            # laatste twee over de bron op schijf. Zo blijft zichtbaar of de
            # cache zelf incompleet is of dat hij juist compleet is terwijl
            # de bron dat niet meer is.
            "rules_missing": _afwijking(verwacht, geladen),
            "rules_unexpected": _afwijking(geladen, verwacht),
            "rules_source_missing": _afwijking(verwacht, op_schijf),
            "rules_source_unexpected": _afwijking(op_schijf, verwacht),
            # Verzamelingen én tellingen. De canonieke index klapt twee
            # schrijfwijzen van hetzelfde ID samen (`ARAI-01.json` naast
            # `ARAI_01.json` wordt één `ARAI01`), dus een zuivere
            # setvergelijking ziet 53 == 53 terwijl er 54 bestanden staan en
            # niemand weet welke van de twee geldt. De cardinaliteitseis
            # ontmaskert die botsing; de setvergelijking kan dat per
            # definitie niet.
            "rules_load_complete": (
                bool(verwacht)
                and set(geladen) == set(verwacht)
                and set(op_schijf) == set(verwacht)
                and len(all_rules) == len(contract_ids)
                and len(bestanden) == len(contract_ids)
            ),
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
