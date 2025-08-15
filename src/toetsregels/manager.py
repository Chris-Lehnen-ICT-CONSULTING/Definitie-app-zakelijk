"""
Modulaire Toetsregel Manager voor DefinitieAgent.
Beheert het laden en cachen van toetsregels uit de nieuwe modulaire structuur.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import time

logger = logging.getLogger(__name__)


class RegelPrioriteit(Enum):
    """Prioriteit niveaus voor toetsregels."""

    HOOG = "hoog"
    MIDDEN = "midden"
    LAAG = "laag"


class RegelAanbeveling(Enum):
    """Aanbeveling types voor toetsregels."""

    VERPLICHT = "verplicht"
    AANBEVOLEN = "aanbevolen"
    OPTIONEEL = "optioneel"


@dataclass
class ToetsregelInfo:
    """Informatie over een toetsregel."""

    id: str
    naam: str
    uitleg: str
    prioriteit: RegelPrioriteit
    aanbeveling: RegelAanbeveling
    geldigheid: str
    status: str
    type: str
    thema: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToetsregelInfo":
        """Maak ToetsregelInfo van dictionary."""
        return cls(
            id=data.get("id", ""),
            naam=data.get("naam", ""),
            uitleg=data.get("uitleg", ""),
            prioriteit=RegelPrioriteit(data.get("prioriteit", "midden")),
            aanbeveling=RegelAanbeveling(data.get("aanbeveling", "optioneel")),
            geldigheid=data.get("geldigheid", ""),
            status=data.get("status", ""),
            type=data.get("type", ""),
            thema=data.get("thema", ""),
        )


@dataclass
class RegelSet:
    """Set van toetsregels voor specifiek gebruik."""

    naam: str
    beschrijving: str
    regels: List[str]
    geladen_op: Optional[float] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RegelSet":
        """Maak RegelSet van dictionary."""
        return cls(
            naam=data.get("naam", ""),
            beschrijving=data.get("beschrijving", ""),
            regels=data.get("regels", []),
            geladen_op=time.time(),
        )


class ToetsregelManager:
    """Manager voor modulaire toetsregels systeem."""

    def __init__(self, base_dir: str = None):
        """
        Initialiseer ToetsregelManager.

        Args:
            base_dir: Base directory voor toetsregels
        """
        # Maak pad absoluut relatief aan toetsregels directory
        if base_dir is None:
            # We zitten nu in src/toetsregels/manager.py
            self.base_dir = Path(__file__).parent
        elif not os.path.isabs(base_dir):
            # We zitten nu in src/toetsregels/manager.py
            self.base_dir = Path(__file__).parent
        else:
            self.base_dir = Path(base_dir)
        self.regels_dir = self.base_dir / "regels"
        self.sets_dir = self.base_dir / "sets"
        self.config_file = self.base_dir / "toetsregels-manager.json"

        # Caches
        self._regels_cache: Dict[str, Dict[str, Any]] = {}
        self._sets_cache: Dict[str, RegelSet] = {}
        self._config_cache: Optional[Dict[str, Any]] = None

        # Statistieken
        self.stats = {
            "regels_geladen": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "sets_geladen": 0,
        }

        self._load_configuration()

    def _load_configuration(self):
        """Laad manager configuratie."""
        try:
            if self.config_file.exists():
                with open(self.config_file, "r", encoding="utf-8") as f:
                    self._config_cache = json.load(f)
            else:
                logger.warning(
                    f"Configuratie bestand niet gevonden: {self.config_file}"
                )
                self._config_cache = self._default_config()

        except Exception as e:
            logger.error(f"Fout bij laden configuratie: {e}")
            self._config_cache = self._default_config()

    def _default_config(self) -> Dict[str, Any]:
        """Standaard configuratie."""
        return {
            "versie": "1.0.0",
            "cache_settings": {"enabled": True, "ttl_seconds": 3600, "max_items": 1000},
            "default_sets": {"basis": "sets/per-prioriteit/verplicht-hoog.json"},
        }

    def load_regel(self, regel_id: str) -> Optional[Dict[str, Any]]:
        """
        Laad een specifieke toetsregel.

        Args:
            regel_id: ID van de regel (bijv. 'CON-01')

        Returns:
            Dictionary met regeldata of None
        """
        # Check cache eerst
        if regel_id in self._regels_cache:
            self.stats["cache_hits"] += 1
            return self._regels_cache[regel_id]

        # Laad van bestand
        regel_file = self.regels_dir / f"{regel_id}.json"

        try:
            if regel_file.exists():
                with open(regel_file, "r", encoding="utf-8") as f:
                    regel_data = json.load(f)

                # Cache regel
                self._regels_cache[regel_id] = regel_data
                self.stats["regels_geladen"] += 1
                self.stats["cache_misses"] += 1

                logger.debug(f"Regel {regel_id} geladen van {regel_file}")
                return regel_data
            else:
                logger.warning(f"Regel bestand niet gevonden: {regel_file}")
                return None

        except Exception as e:
            logger.error(f"Fout bij laden regel {regel_id}: {e}")
            return None

    def load_regelset(self, set_naam: str) -> Optional[RegelSet]:
        """
        Laad een voorgedefinieerde regelset.

        Args:
            set_naam: Naam van de set of pad naar set bestand

        Returns:
            RegelSet object of None
        """
        # Check cache
        if set_naam in self._sets_cache:
            return self._sets_cache[set_naam]

        # Bepaal bestandspad
        if set_naam.endswith(".json"):
            set_file = self.base_dir / set_naam
        else:
            # Zoek in verschillende directories
            possible_paths = [
                self.sets_dir / f"{set_naam}.json",
                self.sets_dir / "per-prioriteit" / f"{set_naam}.json",
                self.sets_dir / "per-categorie" / f"{set_naam}.json",
                self.sets_dir / "per-context" / f"{set_naam}.json",
            ]

            set_file = None
            for path in possible_paths:
                if path.exists():
                    set_file = path
                    break

        try:
            if set_file and set_file.exists():
                with open(set_file, "r", encoding="utf-8") as f:
                    set_data = json.load(f)

                regelset = RegelSet.from_dict(set_data)

                # Cache regelset
                self._sets_cache[set_naam] = regelset
                self.stats["sets_geladen"] += 1

                logger.debug(f"Regelset {set_naam} geladen van {set_file}")
                return regelset
            else:
                logger.warning(f"Regelset bestand niet gevonden: {set_naam}")
                return None

        except Exception as e:
            logger.error(f"Fout bij laden regelset {set_naam}: {e}")
            return None

    def get_verplichte_regels(self) -> List[Dict[str, Any]]:
        """Haal alle verplichte regels op."""
        regelset = self.load_regelset("verplicht")
        if not regelset:
            return []

        regels = []
        for regel_id in regelset.regels:
            regel = self.load_regel(regel_id)
            if regel:
                regels.append(regel)

        return regels

    def get_kritieke_regels(self) -> List[Dict[str, Any]]:
        """Haal kritieke regels op (verplicht + hoge prioriteit)."""
        regelset = self.load_regelset("verplicht-hoog")
        if not regelset:
            return []

        regels = []
        for regel_id in regelset.regels:
            regel = self.load_regel(regel_id)
            if regel:
                regels.append(regel)

        return regels

    def get_regels_voor_categorie(self, categorie: str) -> List[Dict[str, Any]]:
        """
        Haal regels op voor specifieke ontologische categorie.

        Args:
            categorie: 'type', 'proces', 'resultaat', of 'exemplaar'
        """
        regelset = self.load_regelset(f"{categorie}-regels")
        if not regelset:
            return []

        regels = []
        for regel_id in regelset.regels:
            regel = self.load_regel(regel_id)
            if regel:
                regels.append(regel)

        return regels

    def get_regels_voor_prioriteit(
        self, prioriteit: RegelPrioriteit
    ) -> List[Dict[str, Any]]:
        """Haal regels op voor specifieke prioriteit."""
        regelset = self.load_regelset(prioriteit.value)
        if not regelset:
            return []

        regels = []
        for regel_id in regelset.regels:
            regel = self.load_regel(regel_id)
            if regel:
                regels.append(regel)

        return regels

    def get_regels_by_thema(self, thema: str) -> List[Dict[str, Any]]:
        """Haal regels op per thema."""
        # Laad alle regels en filter op thema
        regels = []

        # Doorloop alle regel bestanden
        if self.regels_dir.exists():
            for regel_file in self.regels_dir.glob("*.json"):
                regel_id = regel_file.stem
                regel = self.load_regel(regel_id)

                if regel and regel.get("thema", "").lower() == thema.lower():
                    regels.append(regel)

        return regels

    def validate_regel(self, regel_data: Dict[str, Any]) -> List[str]:
        """
        Valideer een regel tegen het schema.

        Returns:
            List van validatie fouten (leeg = geldig)
        """
        errors = []

        config = self._config_cache or {}
        verplichte_velden = config.get("validatie", {}).get("verplichte_velden", [])

        # Check verplichte velden
        for veld in verplichte_velden:
            if veld not in regel_data:
                errors.append(f"Verplicht veld ontbreekt: {veld}")

        # Check prioriteit
        prioriteit = regel_data.get("prioriteit")
        toegestane_prioriteiten = config.get("validatie", {}).get(
            "toegestane_prioriteiten", []
        )
        if prioriteit and prioriteit not in toegestane_prioriteiten:
            errors.append(f"Ongeldige prioriteit: {prioriteit}")

        # Check aanbeveling
        aanbeveling = regel_data.get("aanbeveling")
        toegestane_aanbevelingen = config.get("validatie", {}).get(
            "toegestane_aanbevelingen", []
        )
        if aanbeveling and aanbeveling not in toegestane_aanbevelingen:
            errors.append(f"Ongeldige aanbeveling: {aanbeveling}")

        return errors

    def create_custom_set(
        self, naam: str, regel_ids: List[str], beschrijving: str = ""
    ) -> RegelSet:
        """Maak een aangepaste regelset."""
        regelset = RegelSet(
            naam=naam,
            beschrijving=beschrijving,
            regels=regel_ids,
            geladen_op=time.time(),
        )

        # Cache de set
        self._sets_cache[naam] = regelset

        return regelset

    def get_available_sets(self) -> List[str]:
        """Haal lijst van beschikbare regelsets op."""
        sets = []

        if self.sets_dir.exists():
            for set_file in self.sets_dir.rglob("*.json"):
                # Relatief pad vanaf sets directory
                rel_path = set_file.relative_to(self.sets_dir)
                sets.append(str(rel_path))

        return sorted(sets)

    def get_available_regels(self) -> List[str]:
        """Haal lijst van beschikbare regels op."""
        regels = []

        if self.regels_dir.exists():
            for regel_file in self.regels_dir.glob("*.json"):
                regels.append(regel_file.stem)

        return sorted(regels)

    def clear_cache(self):
        """Leeg alle caches."""
        self._regels_cache.clear()
        self._sets_cache.clear()

        logger.info("Toetsregel caches geleegd")

    def get_stats(self) -> Dict[str, Any]:
        """Haal statistieken op."""
        return {
            **self.stats,
            "cache_size": len(self._regels_cache),
            "sets_cache_size": len(self._sets_cache),
            "available_regels": len(self.get_available_regels()),
            "available_sets": len(self.get_available_sets()),
        }

    def reload_configuration(self):
        """Herlaad configuratie."""
        self.clear_cache()
        self._load_configuration()
        logger.info("Toetsregel configuratie herladen")


# Global manager instance
_manager: Optional[ToetsregelManager] = None


def get_toetsregel_manager() -> ToetsregelManager:
    """Haal globale ToetsregelManager instantie op."""
    global _manager
    if _manager is None:
        _manager = ToetsregelManager()
    return _manager


# Convenience functions voor backward compatibility
def get_verplichte_regels() -> List[Dict[str, Any]]:
    """Haal verplichte regels op (backward compatibility)."""
    return get_toetsregel_manager().get_verplichte_regels()


def get_kritieke_regels() -> List[Dict[str, Any]]:
    """Haal kritieke regels op (backward compatibility)."""
    return get_toetsregel_manager().get_kritieke_regels()


def load_regel(regel_id: str) -> Optional[Dict[str, Any]]:
    """Laad specifieke regel (backward compatibility)."""
    return get_toetsregel_manager().load_regel(regel_id)


if __name__ == "__main__":
    # Test de ToetsregelManager
    print("🧪 Testing ToetsregelManager")
    print("=" * 30)

    manager = ToetsregelManager()

    # Test regel laden
    con01 = manager.load_regel("CON-01")
    if con01:
        print(f"✅ CON-01 geladen: {con01['naam'][:50]}...")

    # Test regelset laden
    kritiek = manager.get_kritieke_regels()
    print(f"✅ Kritieke regels: {len(kritiek)} regels")

    # Test statistieken
    stats = manager.get_stats()
    print(f"📊 Statistieken: {stats}")

    # Test beschikbare sets
    sets = manager.get_available_sets()
    print(f"📁 Beschikbare sets: {len(sets)}")
    for set_naam in sets[:5]:  # Toon eerste 5
        print(f"   - {set_naam}")
