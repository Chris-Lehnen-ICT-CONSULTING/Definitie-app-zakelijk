"""
Toetsregel INT-03: Voornaamwoord-verwijzing duidelijk

Definities mogen geen voornaamwoorden bevatten waarvan niet direct duidelijk is waarnaar verwezen wordt.
Gemigreerd van legacy core.py
"""

import logging
import re
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class INT03Validator:
    """Validator voor INT-03: Voornaamwoord-verwijzing duidelijk."""

    def __init__(self, config: Dict):
        """
        Initialiseer validator met configuratie uit JSON.

        Args:
            config: Dictionary met configuratie uit INT-03.json
        """
        self.config = config
        self.id = config.get("id", "INT-03")
        self.naam = config.get("naam", "Voornaamwoord-verwijzing duidelijk")
        self.uitleg = config.get("uitleg", "")
        self.herkenbaar_patronen = config.get("herkenbaar_patronen", [])
        self.goede_voorbeelden = config.get("goede_voorbeelden", [])
        self.foute_voorbeelden = config.get("foute_voorbeelden", [])
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
        Valideer definitie volgens INT-03 regel.

        Een definitie mag geen onduidelijke verwijzingen naar "iets" bevatten
        via voornaamwoorden als 'deze', 'dit', 'die', enz. Elk voornaamwoord
        moet in de zin zelf direct naar zijn antecedent verwijzen.

        Args:
            definitie: De te valideren definitie
            begrip: Het begrip dat gedefinieerd wordt
            context: Optionele context informatie

        Returns:
            Tuple van (succes, melding, score)
        """
        tekst = definitie.strip()
        tekst_lc = tekst.lower()

        # 1️⃣ Verzamel alle voornaamwoordhits
        gevonden = []
        for pattern in self.compiled_patterns:
            for m in pattern.finditer(tekst):
                gevonden.append(m.group(0))

        # 2️⃣ Geen voornaamwoorden → OK
        if not gevonden:
            return (
                True,
                f"✔️ {self.id}: geen onduidelijke voornaamwoord-verwijzing aangetroffen",
                1.0,
            )

        # 3️⃣ Controle op expliciet goed voorbeeld
        for goed in self.goede_voorbeelden:
            if goed.lower() in tekst_lc:
                # We vertrouwen hier op de JSON-voorbeeldzin dat die de
                # voornaamwoorden op een correcte manier gebruikt
                return (
                    True,
                    (
                        f"✔️ {self.id}: voornaamwoorden gevonden "
                        f"({', '.join(sorted(set(gevonden)))}) maar correct opgehelderd"
                    ),
                    1.0,
                )

        # 4️⃣ Anders: foutmelding met de gematchte voornaamwoorden
        distinct = ", ".join(sorted(set(gevonden)))
        return (
            False,
            (
                f"❌ {self.id}: onduidelijke voornaamwoord-verwijzingen aangetroffen "
                f"({distinct}); antecedent niet expliciet gemaakt"
            ),
            0.0,
        )

    def get_generation_hints(self) -> List[str]:
        """
        Geef hints voor definitie generatie.

        Returns:
            Lijst met instructies voor de AI generator
        """
        hints = []

        hints.append(
            "Vermijd voornaamwoorden zoals 'deze', 'dit', 'die' zonder duidelijk antecedent"
        )
        hints.append(
            "Als je voornaamwoorden gebruikt, maak dan direct duidelijk waarnaar ze verwijzen"
        )
        hints.append(
            "Herhaal liever het zelfstandig naamwoord dan een onduidelijk voornaamwoord te gebruiken"
        )
        hints.append(
            "Zorg dat de definitie zelfstandig leesbaar is zonder externe context"
        )

        return hints


def create_validator(config_path: str = None) -> INT03Validator:
    """
    Factory functie om validator te maken.

    Args:
        config_path: Optioneel pad naar configuratie bestand

    Returns:
        INT03Validator instantie
    """
    import json
    import os

    # Gebruik default config path als niet opgegeven
    if not config_path:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "INT-03.json")

    # Laad configuratie
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    return INT03Validator(config)
