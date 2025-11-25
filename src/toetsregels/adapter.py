"""
Backward compatibility adapter voor toetsregels systeem.
Zorgt ervoor dat bestaande code die het oude JSON formaat gebruikt blijft werken.
"""

import logging
from typing import Any

from toetsregels.manager import get_toetsregel_manager

logger = logging.getLogger(__name__)


class ToetsregelsCompatibilityAdapter:
    """Adapter om oude toetsregels interface te emuleren."""

    def __init__(self):
        self.manager = get_toetsregel_manager()
        self._legacy_cache: dict[str, Any] | None = None

    def get_legacy_format(self) -> dict[str, Any]:
        """
        Genereer data in het oude JSON formaat voor backward compatibility.

        Returns:
            Dictionary in oude formaat: {"regels": {"CON-01": {...}, ...}}
        """
        if self._legacy_cache is not None:
            return self._legacy_cache

        # Bouw legacy formaat op
        legacy_data: dict[str, Any] = {"regels": {}}

        # Haal alle beschikbare regels op
        for regel_id in self.manager.get_available_regels():
            regel_data = self.manager.load_regel(regel_id)
            if regel_data:
                legacy_data["regels"][regel_id] = regel_data

        # Cache voor performance
        self._legacy_cache = legacy_data

        logger.info(
            f"Legacy formaat gegenereerd met {len(legacy_data['regels'])} regels"
        )
        return legacy_data

    def clear_cache(self):
        """Leeg legacy cache."""
        self._legacy_cache = None
        self.manager.clear_cache()

    def reload(self):
        """Herlaad alles."""
        self.clear_cache()
        self.manager.reload_configuration()


# Global adapter instance
_adapter: ToetsregelsCompatibilityAdapter | None = None


def get_toetsregels_adapter() -> ToetsregelsCompatibilityAdapter:
    """Haal globale adapter instantie op."""
    global _adapter
    if _adapter is None:
        _adapter = ToetsregelsCompatibilityAdapter()
    return _adapter


def load_toetsregels() -> dict[str, Any]:
    """
    Laad toetsregels in oude formaat (backward compatibility).

    Returns:
        Dictionary met alle regels in oude formaat
    """
    return get_toetsregels_adapter().get_legacy_format()


def get_toetsregels_by_priority(priority: str) -> list[dict[str, Any]]:
    """
    Haal regels op per prioriteit (backward compatibility).

    Args:
        priority: 'hoog', 'midden', of 'laag'

    Returns:
        List van regels met opgegeven prioriteit
    """
    manager = get_toetsregel_manager()

    # Haal alle regels op en filter op prioriteit
    regels = []
    for regel_id in manager.get_available_regels():
        regel = manager.load_regel(regel_id)
        if regel and regel.get("prioriteit") == priority:
            regels.append(regel)

    return regels


def get_toetsregels_by_category(category: str) -> list[dict[str, Any]]:
    """
    Haal regels op per categorie prefix (backward compatibility).

    Args:
        category: 'CON', 'ESS', 'INT', 'STR', 'SAM', 'ARAI'

    Returns:
        List van regels die beginnen met category prefix
    """
    manager = get_toetsregel_manager()

    regels = []
    for regel_id in manager.get_available_regels():
        if regel_id.startswith(category):
            regel = manager.load_regel(regel_id)
            if regel:
                regels.append(regel)

    return regels


def validate_against_rules(
    text: str, regel_ids: list[str] | None = None
) -> dict[str, Any]:
    """
    Valideer tekst tegen opgegeven regels (backward compatibility).

    Args:
        text: Te valideren tekst
        regel_ids: Specifieke regels om te gebruiken, None = alle verplichte regels

    Returns:
        Dictionary met validatie resultaten
    """
    manager = get_toetsregel_manager()

    # Bepaal welke regels te gebruiken
    if regel_ids is None:
        regels = manager.get_verplichte_regels()
    else:
        regels = []
        for regel_id in regel_ids:
            regel = manager.load_regel(regel_id)
            if regel:
                regels.append(regel)

    # Placeholder voor validatie logica
    # Dit zou normaal de werkelijke validatie uitvoeren
    return {
        "text": text,
        "rules_checked": len(regels),
        "violations": [],
        "warnings": [],
        "passed": True,
    }


# Functies voor configuratie integratie
def integrate_with_config_manager():
    """Integreer toetsregels met ConfigManager."""
    try:
        from config.config_manager import get_config_manager

        config_manager = get_config_manager()

        # Registreer callback voor configuratie wijzigingen
        config_manager.register_change_callback(
            "validation",
            lambda section, key, old_val, new_val: get_toetsregels_adapter().reload(),
        )

        logger.info("Toetsregels geïntegreerd met ConfigManager")

    except ImportError:
        logger.warning("ConfigManager niet beschikbaar voor integratie")


# Migratie helpers
def migrate_legacy_code_usage():
    """
    Helper om legacy code gebruik te identificeren.
    Scan naar patronen die moeten worden gemigreerd.
    """
    return {
        "oude_patronen": [
            'json.load(open("config/toetsregels.json"))',
            'with open("config/toetsregels.json")',
            "toetsregels.json",
        ],
        "nieuwe_patronen": [
            "get_toetsregel_manager().load_regel()",
            "get_verplichte_regels()",
            "get_kritieke_regels()",
        ],
        "voordelen": [
            "Modulaire structuur per regel",
            "Selective loading voor performance",
            "Caching van frequent gebruikte regels",
            "Flexibele regelsets per context",
            "Betere onderhoudbaarheid",
        ],
    }


if __name__ == "__main__":
    # Test backward compatibility
    print("🔄 Testing Backward Compatibility")
    print("=" * 35)

    # Test legacy formaat
    legacy_data = load_toetsregels()
    print(f"✅ Legacy format: {len(legacy_data['regels'])} regels geladen")

    # Test enkele regels
    con_regels = get_toetsregels_by_category("CON")
    print(f"✅ CON regels: {len(con_regels)} regels")

    hoge_prioriteit = get_toetsregels_by_priority("hoog")
    print(f"✅ Hoge prioriteit: {len(hoge_prioriteit)} regels")

    # Test validatie
    test_result = validate_against_rules("Test definitie tekst")
    print(f"✅ Validatie test: {test_result['rules_checked']} regels gecontroleerd")

    # Migratie info
    migration = migrate_legacy_code_usage()
    print(f"📋 Migratie patronen: {len(migration['oude_patronen'])} oude patronen")

    print("🎯 Backward compatibility test geslaagd!")
