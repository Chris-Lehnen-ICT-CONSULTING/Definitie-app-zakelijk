"""
Toetsregel ARAI06: Correcte definitiestart: geen lidwoord, geen koppelwerkwoord, geen herhaling begrip

Deze regel controleert dat de definitie correct start zonder verboden constructies.
Gemigreerd van legacy core.py
"""

import logging
import re
from typing import Dict, List, Optional, Tuple

# Import van verboden woorden functionaliteit
from config.verboden_woorden import genereer_verboden_startregex, laad_verboden_woorden

logger = logging.getLogger(__name__)


class ARAI06Validator:
    """Validator voor ARAI06: Correcte definitiestart."""

    def __init__(self, config: Dict):
        """
        Initialiseer validator met configuratie uit JSON.

        Args:
            config: Dictionary met configuratie uit ARAI06.json
        """
        self.config = config
        self.id = config.get("id", "ARAI06")
        self.naam = config.get("naam", "Correcte definitiestart")
        self.uitleg = config.get("uitleg", "")
        self.herkenbaar_patronen = config.get("herkenbaar_patronen", [])
        self.prioriteit = config.get("prioriteit", "hoog")

        # Compile basis regex patronen voor performance
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
        Valideer definitie volgens ARAI06 regel.

        Controleert of de definitie correct start zonder:
        - Lidwoorden ('de', 'het', 'een')
        - Koppelwerkwoorden ('is', 'omvat', 'betekent')
        - Herhaling van het begrip

        Args:
            definitie: De te valideren definitie
            begrip: Het begrip dat gedefinieerd wordt
            context: Optionele context informatie

        Returns:
            Tuple van (succes, melding, score)
        """
        # 1) Normaliseer
        definitie_lower = definitie.strip().lower()

        # 2) Haal de lijst met verboden woorden op
        try:
            data = laad_verboden_woorden()
            verboden_lijst = data if isinstance(data, list) else []
        except Exception as e:
            logger.warning(f"Kan verboden woorden niet laden: {e}")
            verboden_lijst = []

        # 3) Genereer regex-patronen
        regex_lijst = genereer_verboden_startregex(begrip, verboden_lijst)

        # 4) Sorteer patronen op lengte (langste eerst) om overlap netjes af te handelen
        regex_lijst.sort(key=len, reverse=True)

        # 5) Match van alle patronen
        for patroon in regex_lijst:
            if re.match(patroon, definitie_lower, flags=re.IGNORECASE):
                return (
                    False,
                    (f"❌ {self.id}: begint met verboden constructie: {patroon}"),
                    0.0,
                )

        # 6) Extra controle op basis patronen uit JSON
        for pattern in self.compiled_patterns:
            if pattern.match(definitie_lower):
                match = pattern.match(definitie_lower)
                matched_text = match.group(0) if match else "onbekend"
                return (
                    False,
                    (f"❌ {self.id}: verboden start gedetecteerd: '{matched_text}'"),
                    0.0,
                )

        # 7) Geen match → OK
        return True, f"✔️ {self.id}: geen opbouwfouten", 1.0

    def get_generation_hints(self) -> List[str]:
        """
        Geef hints voor definitie generatie.

        Returns:
            Lijst met instructies voor de AI generator
        """
        hints = []

        hints.append("Start definitie direct met een zelfstandig naamwoord")
        hints.append("Vermijd lidwoorden aan het begin: 'de', 'het', 'een'")
        hints.append("Gebruik geen koppelwerkwoorden: 'is', 'omvat', 'betekent'")
        hints.append("Herhaal het begrip niet in de definitie")
        hints.append("Vermijd constructies zoals 'Het begrip betekent...'")
        hints.append("Voorkom cirkeldefinities door directe formulering")

        return hints


def create_validator(config_path: str = None) -> ARAI06Validator:
    """
    Factory functie om validator te maken.

    Args:
        config_path: Optioneel pad naar configuratie bestand

    Returns:
        ARAI06Validator instantie
    """
    import json
    import os

    # Gebruik default config path als niet opgegeven
    if not config_path:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "ARAI06.json")

    # Laad configuratie
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    return ARAI06Validator(config)
