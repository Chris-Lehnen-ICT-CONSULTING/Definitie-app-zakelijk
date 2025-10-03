"""
Toetsregel SAM-06: Voorkeursterm consistent gebruiken

Als een voorkeursterm is opgegeven, moet deze consistent gebruikt worden.
Gemigreerd van legacy core.py
"""

import logging
import re

logger = logging.getLogger(__name__)


class SAM06Validator:
    """Validator voor SAM-06: Voorkeursterm consistent gebruiken."""

    def __init__(self, config: dict):
        """
        Initialiseer validator met configuratie uit JSON.

        Args:
            config: Dictionary met configuratie uit SAM-06.json
        """
        self.config = config
        self.id = config.get("id", "SAM-06")
        self.naam = config.get("naam", "Voorkeursterm consistent gebruiken")
        self.uitleg = config.get("uitleg", "")
        self.prioriteit = config.get("prioriteit", "hoog")

    def validate(
        self, definitie: str, begrip: str, context: dict | None = None
    ) -> tuple[bool, str, float]:
        """
        Valideer definitie volgens SAM-06 regel.

        Als er een voorkeursterm is opgegeven die verschilt van het begrip,
        controleer dan of de voorkeursterm wordt gebruikt in plaats van het begrip.

        Args:
            definitie: De te valideren definitie
            begrip: Het begrip dat gedefinieerd wordt
            context: Optionele context informatie met voorkeursterm

        Returns:
            Tuple van (succes, melding, score)
        """
        # Haal voorkeursterm uit context
        voorkeursterm = None
        if context:
            voorkeursterm = context.get("voorkeursterm")

        # Als geen voorkeursterm of gelijk aan begrip, dan niet relevant
        if not voorkeursterm or not begrip:
            return True, f"✔️ {self.id}: geen afwijkende voorkeursterm opgegeven", 1.0

        if voorkeursterm.lower() == begrip.lower():
            return True, f"✔️ {self.id}: voorkeursterm is gelijk aan begrip", 1.0

        # Normaliseer voor vergelijking
        definitie_lower = definitie.lower()
        begrip_lower = begrip.lower()
        voorkeursterm_lower = voorkeursterm.lower()

        # Check of begrip voorkomt in definitie
        begrip_pattern = rf"\b{re.escape(begrip_lower)}\b"
        begrip_found = bool(re.search(begrip_pattern, definitie_lower))

        # Check of voorkeursterm voorkomt in definitie
        voorkeursterm_pattern = rf"\b{re.escape(voorkeursterm_lower)}\b"
        voorkeursterm_found = bool(re.search(voorkeursterm_pattern, definitie_lower))

        if begrip_found and not voorkeursterm_found:
            return (
                False,
                (
                    f"❌ {self.id}: begrip '{begrip}' gebruikt in plaats van "
                    f"voorkeursterm '{voorkeursterm}'"
                ),
                0.0,
            )

        if voorkeursterm_found:
            return (
                True,
                (f"✔️ {self.id}: voorkeursterm '{voorkeursterm}' correct gebruikt"),
                1.0,
            )

        # Noch begrip noch voorkeursterm gevonden
        return True, f"✔️ {self.id}: noch begrip noch voorkeursterm in definitie", 0.8

    def get_generation_hints(self) -> list[str]:
        """
        Geef hints voor definitie generatie.

        Returns:
            Lijst met instructies voor de AI generator
        """
        hints = []

        hints.append("Als een voorkeursterm is opgegeven, gebruik deze consistent")
        hints.append("Vermijd het oorspronkelijke begrip als een voorkeursterm bestaat")
        hints.append("Dit bevordert eenduidige communicatie")
        hints.append(
            "Bijvoorbeeld: gebruik 'gevangene' ipv 'gedetineerde' als dat de voorkeursterm is"
        )

        return hints


def create_validator(config_path: str | None = None) -> SAM06Validator:
    """
    Factory functie om validator te maken.

    Args:
        config_path: Optioneel pad naar configuratie bestand

    Returns:
        SAM06Validator instantie
    """
    import json
    import os

    # Gebruik default config path als niet opgegeven
    if not config_path:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "SAM-06.json")

    # Laad configuratie
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    return SAM06Validator(config)
