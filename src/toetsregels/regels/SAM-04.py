"""
Toetsregel SAM-04: Geen cirkelverwijzing

Een definitie mag geen cirkelverwijzing bevatten naar andere begrippen die op hun beurt weer naar dit begrip verwijzen.
Gemigreerd van legacy core.py
"""

import re
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class SAM04Validator:
    """Validator voor SAM-04: Geen cirkelverwijzing."""

    def __init__(self, config: Dict):
        """
        Initialiseer validator met configuratie uit JSON.

        Args:
            config: Dictionary met configuratie uit SAM-04.json
        """
        self.config = config
        self.id = config.get("id", "SAM-04")
        self.naam = config.get("naam", "Geen cirkelverwijzing")
        self.uitleg = config.get("uitleg", "")
        self.herkenbaar_patronen = config.get("herkenbaar_patronen", [])
        self.prioriteit = config.get("prioriteit", "hoog")

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
        Valideer definitie volgens SAM-04 regel.

        Deze regel controleert op mogelijke cirkelverwijzingen door te kijken
        naar verwijzingspatronen zoals "zie", "conform", "volgens".

        Note: Volledige cirkeldetectie vereist kennis van alle definities,
        dus dit is een heuristische check.

        Args:
            definitie: De te valideren definitie
            begrip: Het begrip dat gedefinieerd wordt
            context: Optionele context informatie

        Returns:
            Tuple van (succes, melding, score)
        """
        # Zoek verwijzingspatronen
        verwijzingen = []
        for pattern in self.compiled_patterns:
            matches = pattern.findall(definitie)
            verwijzingen.extend(matches)

        if verwijzingen:
            # Dit is een waarschuwing, geen harde fout
            # Echte cirkeldetectie vereist analyse van alle definities
            unieke = ", ".join(sorted(set(verwijzingen)))
            return (
                False,
                (
                    f"🟡 {self.id}: mogelijke verwijzing naar andere begrippen gevonden ({unieke}). "
                    "Controleer op cirkelverwijzingen"
                ),
                0.5,
            )

        return (
            True,
            f"✔️ {self.id}: geen expliciete verwijzingen naar andere begrippen",
            1.0,
        )

    def get_generation_hints(self) -> List[str]:
        """
        Geef hints voor definitie generatie.

        Returns:
            Lijst met instructies voor de AI generator
        """
        hints = []

        hints.append("Vermijd verwijzingen naar andere te definiëren begrippen")
        hints.append("Gebruik geen formuleringen zoals 'zie', 'conform', 'volgens'")
        hints.append("Maak elke definitie zelfstandig begrijpelijk")
        hints.append("Voorkom wederzijdse afhankelijkheden tussen definities")

        return hints


def create_validator(config_path: str = None) -> SAM04Validator:
    """
    Factory functie om validator te maken.

    Args:
        config_path: Optioneel pad naar configuratie bestand

    Returns:
        SAM04Validator instantie
    """
    import json
    import os

    # Gebruik default config path als niet opgegeven
    if not config_path:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "SAM-04.json")

    # Laad configuratie
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    return SAM04Validator(config)
