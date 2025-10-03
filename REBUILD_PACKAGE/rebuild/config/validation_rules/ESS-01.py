"""
Toetsregel ESS-01: Essentie, niet doel

Een definitie beschrijft wat iets is, niet wat het doel of de bedoeling ervan is.
Gemigreerd van legacy core.py
"""

import logging
import re

logger = logging.getLogger(__name__)


class ESS01Validator:
    """Validator voor ESS-01: Essentie, niet doel."""

    def __init__(self, config: dict):
        """
        Initialiseer validator met configuratie uit JSON.

        Args:
            config: Dictionary met configuratie uit ESS-01.json
        """
        self.config = config
        self.id = config.get("id", "ESS-01")
        self.naam = config.get("naam", "Essentie, niet doel")
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
        self, definitie: str, begrip: str, context: dict | None = None
    ) -> tuple[bool, str, float]:
        """
        Valideer definitie volgens ESS-01 regel.

        Controleert of de definitie doelgerichte formuleringen bevat.
        Een definitie moet beschrijven WAT iets is, niet WAARVOOR het is.

        Args:
            definitie: De te valideren definitie
            begrip: Het begrip dat gedefinieerd wordt
            context: Optionele context informatie

        Returns:
            Tuple van (succes, melding, score)
        """
        # Check elk doel-patroon: zodra er één match is → fout
        for pattern in self.compiled_patterns:
            match = pattern.search(definitie)
            if match:
                return (
                    False,
                    (
                        f"❌ {self.id}: doelpatroon '{match.group(0)}' herkend in definitie "
                        f"(patroon: {pattern.pattern})"
                    ),
                    0.0,
                )

        # Geen enkel doel-patroon gevonden → OK
        return True, f"✔️ {self.id}: geen doelgerichte formuleringen aangetroffen", 1.0

    def get_generation_hints(self) -> list[str]:
        """
        Geef hints voor definitie generatie.

        Returns:
            Lijst met instructies voor de AI generator
        """
        hints = []

        hints.append("Beschrijf WAT iets is, niet waarvoor het dient")
        hints.append(
            "Vermijd formuleringen zoals: 'om te', 'met als doel', 'bedoeld voor'"
        )
        hints.append("Focus op de aard en kenmerken van het begrip")
        hints.append("Vermijd doel- of gebruiksgericht taalgebruik")

        goede_voorbeelden = self.config.get("goede_voorbeelden", [])
        if goede_voorbeelden:
            hints.append(f"Goed voorbeeld: {goede_voorbeelden[0]}")

        return hints


def create_validator(config_path: str | None = None) -> ESS01Validator:
    """
    Factory functie om validator te maken.

    Args:
        config_path: Optioneel pad naar configuratie bestand

    Returns:
        ESS01Validator instantie
    """
    import json
    import os

    # Gebruik default config path als niet opgegeven
    if not config_path:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "ESS-01.json")

    # Laad configuratie
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    return ESS01Validator(config)
