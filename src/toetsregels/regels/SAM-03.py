"""
Toetsregel SAM-03: Geen tautologie

Een definitie mag geen tautologie bevatten (het begrip mag niet in eigen definitie voorkomen).
Gemigreerd van legacy core.py
"""

import re
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class SAM03Validator:
    """Validator voor SAM-03: Geen tautologie."""

    def __init__(self, config: Dict):
        """
        Initialiseer validator met configuratie uit JSON.

        Args:
            config: Dictionary met configuratie uit SAM-03.json
        """
        self.config = config
        self.id = config.get("id", "SAM-03")
        self.naam = config.get("naam", "Geen tautologie")
        self.uitleg = config.get("uitleg", "")
        self.prioriteit = config.get("prioriteit", "hoog")

    def validate(
        self, definitie: str, begrip: str, context: Optional[Dict] = None
    ) -> Tuple[bool, str, float]:
        """
        Valideer definitie volgens SAM-03 regel.

        Controleert of het te definiëren begrip niet in zijn eigen definitie voorkomt.
        Dit voorkomt cirkelredeneringen.

        Args:
            definitie: De te valideren definitie
            begrip: Het begrip dat gedefinieerd wordt
            context: Optionele context informatie

        Returns:
            Tuple van (succes, melding, score)
        """
        if not begrip:
            return True, f"✔️ {self.id}: geen begrip opgegeven om te controleren", 1.0

        # Normaliseer voor vergelijking
        begrip_lower = begrip.lower().strip()
        definitie_lower = definitie.lower()

        # Maak regex patroon voor het begrip (woord grenzen)
        begrip_pattern = rf"\b{re.escape(begrip_lower)}\b"

        # Check of het begrip in de definitie voorkomt
        if re.search(begrip_pattern, definitie_lower):
            # Check voor samenstellingen (begrip als deel van groter woord)
            # Dit is toegestaan volgens sommige interpretaties
            matches = list(re.finditer(begrip_pattern, definitie_lower))

            return (
                False,
                (
                    f"❌ {self.id}: tautologie - het begrip '{begrip}' komt voor in eigen definitie"
                ),
                0.0,
            )

        return True, f"✔️ {self.id}: geen tautologie aangetroffen", 1.0

    def get_generation_hints(self) -> List[str]:
        """
        Geef hints voor definitie generatie.

        Returns:
            Lijst met instructies voor de AI generator
        """
        hints = []

        hints.append("Gebruik het te definiëren begrip NIET in de definitie zelf")
        hints.append("Vermijd cirkelredeneringen")
        hints.append(
            "Gebruik synoniemen of omschrijvingen in plaats van het begrip zelf"
        )
        hints.append("Bijvoorbeeld: definieer 'auto' niet als 'een auto die...'")

        return hints


def create_validator(config_path: str = None) -> SAM03Validator:
    """
    Factory functie om validator te maken.

    Args:
        config_path: Optioneel pad naar configuratie bestand

    Returns:
        SAM03Validator instantie
    """
    import json
    import os

    # Gebruik default config path als niet opgegeven
    if not config_path:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "SAM-03.json")

    # Laad configuratie
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    return SAM03Validator(config)
