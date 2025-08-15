"""
Toetsregel VER-01: Versie-onafhankelijk

Een definitie moet versie-onafhankelijk zijn en niet verwijzen naar specifieke versies.
Gemigreerd van legacy core.py
"""

import re
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class VER01Validator:
    """Validator voor VER-01: Versie-onafhankelijk."""

    def __init__(self, config: Dict):
        """
        Initialiseer validator met configuratie uit JSON.

        Args:
            config: Dictionary met configuratie uit VER-01.json
        """
        self.config = config
        self.id = config.get("id", "VER-01")
        self.naam = config.get("naam", "Versie-onafhankelijk")
        self.uitleg = config.get("uitleg", "")
        self.herkenbaar_patronen = config.get("herkenbaar_patronen", [])
        self.prioriteit = config.get("prioriteit", "midden")

        # Compile regex patronen voor performance
        self.compiled_patterns = []
        for pattern in self.herkenbaar_patronen:
            try:
                self.compiled_patterns.append(re.compile(pattern, re.IGNORECASE))
            except re.error as e:
                logger.warning(f"Ongeldig regex patroon in {self.id}: {pattern} - {e}")

    def validate(
        self, definitie: str, begrip: str, context: Optional[Dict] = None
    ) -> Tuple[bool, str, float]:
        """
        Valideer definitie volgens VER-01 regel.

        Controleert of de definitie geen verwijzingen bevat naar specifieke
        versies, releases of tijdsgebonden elementen.

        Args:
            definitie: De te valideren definitie
            begrip: Het begrip dat gedefinieerd wordt
            context: Optionele context informatie

        Returns:
            Tuple van (succes, melding, score)
        """
        # Zoek versie-indicatoren
        versie_gevonden = []
        for pattern in self.compiled_patterns:
            matches = pattern.findall(definitie)
            versie_gevonden.extend(matches)

        if versie_gevonden:
            unieke = ", ".join(sorted(set(versie_gevonden)))
            return (
                False,
                (f"❌ {self.id}: versie-specifieke verwijzingen gevonden: {unieke}"),
                0.0,
            )

        return True, f"✔️ {self.id}: definitie is versie-onafhankelijk", 1.0

    def get_generation_hints(self) -> List[str]:
        """
        Geef hints voor definitie generatie.

        Returns:
            Lijst met instructies voor de AI generator
        """
        hints = []

        hints.append("Vermijd verwijzingen naar specifieke versies of releases")
        hints.append("Gebruik geen versienummers zoals v1.0, 2.0, etc.")
        hints.append("Vermijd tijdsgebonden termen zoals 'huidige', 'nieuwste'")
        hints.append("Maak de definitie tijdloos en versie-onafhankelijk")

        return hints


def create_validator(config_path: str = None) -> VER01Validator:
    """
    Factory functie om validator te maken.

    Args:
        config_path: Optioneel pad naar configuratie bestand

    Returns:
        VER01Validator instantie
    """
    import json
    import os

    # Gebruik default config path als niet opgegeven
    if not config_path:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "VER-01.json")

    # Laad configuratie
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    return VER01Validator(config)
