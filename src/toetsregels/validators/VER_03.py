"""
Toetsregel VER-03: Geen verwijzingen naar specifieke data

Een definitie mag geen verwijzingen bevatten naar specifieke data of tijdstippen.
Gemigreerd van legacy core.py
"""

import logging
import re
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class VER03Validator:
    """Validator voor VER-03: Geen verwijzingen naar specifieke data."""

    def __init__(self, config: Dict):
        """
        Initialiseer validator met configuratie uit JSON.

        Args:
            config: Dictionary met configuratie uit VER-03.json
        """
        self.config = config
        self.id = config.get("id", "VER-03")
        self.naam = config.get("naam", "Geen verwijzingen naar specifieke data")
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
        Valideer definitie volgens VER-03 regel.

        Controleert of de definitie geen verwijzingen bevat naar specifieke
        data, jaartallen of tijdstippen die de definitie tijdgebonden maken.

        Args:
            definitie: De te valideren definitie
            begrip: Het begrip dat gedefinieerd wordt
            context: Optionele context informatie

        Returns:
            Tuple van (succes, melding, score)
        """
        # Zoek datumpatronen
        datums_gevonden = []
        for pattern in self.compiled_patterns:
            matches = pattern.findall(definitie)
            datums_gevonden.extend(matches)

        if datums_gevonden:
            unieke = ", ".join(sorted(set(datums_gevonden)))
            return (
                False,
                (f"❌ {self.id}: specifieke data of tijdstippen gevonden: {unieke}"),
                0.0,
            )

        return (
            True,
            f"✔️ {self.id}: geen specifieke data of tijdstippen in definitie",
            1.0,
        )

    def get_generation_hints(self) -> List[str]:
        """
        Geef hints voor definitie generatie.

        Returns:
            Lijst met instructies voor de AI generator
        """
        hints = []

        hints.append("Vermijd specifieke data en jaartallen")
        hints.append("Gebruik geen concrete tijdstippen")
        hints.append("Formuleer tijdloos, zonder verwijzingen naar specifieke momenten")
        hints.append(
            "Bijvoorbeeld: gebruik 'sinds inwerkingtreding' ipv 'sinds 1 januari 2023'"
        )

        return hints


def create_validator(config_path: str = None) -> VER03Validator:
    """
    Factory functie om validator te maken.

    Args:
        config_path: Optioneel pad naar configuratie bestand

    Returns:
        VER03Validator instantie
    """
    import json
    import os

    # Gebruik default config path als niet opgegeven
    if not config_path:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "VER-03.json")

    # Laad configuratie
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    return VER03Validator(config)
