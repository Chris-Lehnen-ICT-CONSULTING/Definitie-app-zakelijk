"""
Toetsregel INT-06: Definitie bevat geen toelichting

Een definitie bevat geen nadere toelichting of voorbeelden, maar uitsluitend de afbakening van het begrip.
Gemigreerd van legacy core.py
"""

import logging
import re

logger = logging.getLogger(__name__)


class INT06Validator:
    """Validator voor INT-06: Definitie bevat geen toelichting."""

    def __init__(self, config: dict):
        """
        Initialiseer validator met configuratie uit JSON.

        Args:
            config: Dictionary met configuratie uit INT-06.json
        """
        self.config = config
        self.id = config.get("id", "INT-06")
        self.naam = config.get("naam", "Definitie bevat geen toelichting")
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
        self, definitie: str, begrip: str, context: dict | None = None
    ) -> tuple[bool, str, float]:
        """
        Valideer definitie volgens INT-06 regel.

        Een definitie moet zelfstandig afbakenen wat een begrip is, zonder
        nadere uitleg of voorbeelden in dezelfde zin.

        Args:
            definitie: De te valideren definitie
            begrip: Het begrip dat gedefinieerd wordt
            context: Optionele context informatie

        Returns:
            Tuple van (succes, melding, score)
        """
        tekst = definitie.strip().lower()

        # 1️⃣ Expliciete foute voorbeelden eerst (prioriteit)
        for fout in self.foute_voorbeelden:
            if fout.lower() in tekst:
                return (
                    False,
                    (
                        f"❌ {self.id}: definitie bevat expliciete toelichting "
                        f"(voorbeeld: '{fout}')."
                    ),
                    0.0,
                )

        # 2️⃣ Generieke detectie via toelichtingspatronen
        gevonden = []
        for pattern in self.compiled_patterns:
            if pattern.search(tekst):
                gevonden.append(pattern.pattern)

        if gevonden:
            samples = ", ".join(f"'{pat}'" for pat in gevonden)
            return (
                False,
                (
                    f"❌ {self.id}: toelichtende signalen herkend via patronen "
                    f"{samples}."
                ),
                0.0,
            )

        # 3️⃣ Fallback: geen toelichting
        return (
            True,
            f"✔️ {self.id}: geen toelichtende elementen in de definitie gevonden",
            1.0,
        )

    def get_generation_hints(self) -> list[str]:
        """
        Geef hints voor definitie generatie.

        Returns:
            Lijst met instructies voor de AI generator
        """
        hints = []

        hints.append("Houd de definitie kort en krachtig")
        hints.append(
            "Vermijd toelichtende woorden zoals 'bijvoorbeeld', 'zoals', 'namelijk'"
        )
        hints.append("Geef alleen de afbakening van het begrip, geen extra uitleg")
        hints.append(
            "Voorbeelden en toelichting horen in een aparte notitie, niet in de definitie"
        )

        return hints


def create_validator(config_path: str | None = None) -> INT06Validator:
    """
    Factory functie om validator te maken.

    Args:
        config_path: Optioneel pad naar configuratie bestand

    Returns:
        INT06Validator instantie
    """
    import json
    import os

    # Gebruik default config path als niet opgegeven
    if not config_path:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "INT-06.json")

    # Laad configuratie
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    return INT06Validator(config)
