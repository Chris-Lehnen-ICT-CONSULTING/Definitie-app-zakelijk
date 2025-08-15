"""
Toetsregel INT-02: Geen beslisregel

Een definitie bevat geen beslisregels of voorwaarden.
Gemigreerd van legacy core.py
"""

import logging
import re
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class INT02Validator:
    """Validator voor INT-02: Geen beslisregel."""

    def __init__(self, config: Dict):
        """
        Initialiseer validator met configuratie uit JSON.

        Args:
            config: Dictionary met configuratie uit INT-02.json
        """
        self.config = config
        self.id = config.get("id", "INT-02")
        self.naam = config.get("naam", "Geen beslisregel")
        self.uitleg = config.get("uitleg", "")
        self.herkenbaar_patronen = config.get("herkenbaar_patronen", [])
        self.goede_voorbeelden = config.get("goede_voorbeelden", [])
        self.foute_voorbeelden = config.get("foute_voorbeelden", [])
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
        Valideer definitie volgens INT-02 regel.

        Een definitie mag niet als beslisregel geformuleerd worden;
        dat hoort in regelgeving, niet in een lemma.

        Args:
            definitie: De te valideren definitie
            begrip: Het begrip dat gedefinieerd wordt
            context: Optionele context informatie

        Returns:
            Tuple van (succes, melding, score)
        """
        tekst = definitie.lower()

        # 1️⃣ Expliciete foute voorbeelden krijgen prioriteit
        for fout in self.foute_voorbeelden:
            if fout.lower() in tekst:
                return (
                    False,
                    f"❌ {self.id}: voorwaardelijke formulering aangetroffen (komt precies overeen met fout voorbeeld)",
                    0.0,
                )

        # 2️⃣ Expliciete goede voorbeelden daarna
        for goed in self.goede_voorbeelden:
            if goed.lower() in tekst:
                return (
                    True,
                    f"✔️ {self.id}: voorbeeldtekst komt overeen met goed voorbeeld (geen beslisregel)",
                    1.0,
                )

        # 3️⃣ Patronen voor voorwaardelijke taal detecteren
        gevonden = []
        for pattern in self.compiled_patterns:
            if pattern.search(definitie):
                gevonden.append(pattern.pattern)

        if gevonden:
            labels = ", ".join(sorted(set(gevonden)))
            return False, f"❌ {self.id}: voorwaardelijke taal herkend ({labels})", 0.0

        # 4️⃣ Fallback: geen beslisregel of voorwaardelijke formulering
        return (
            True,
            f"✔️ {self.id}: geen beslisregels of voorwaardelijke formuleringen aangetroffen",
            1.0,
        )

    def get_generation_hints(self) -> List[str]:
        """
        Geef hints voor definitie generatie.

        Returns:
            Lijst met instructies voor de AI generator
        """
        hints = []

        hints.append("Beschrijf wat iets IS, niet wat ermee moet gebeuren")
        hints.append(
            "Vermijd voorwaardelijke formuleringen zoals 'indien', 'mits', 'tenzij'"
        )
        hints.append("Gebruik geen beslisregels of normatieve uitspraken")
        hints.append("Focus op de essentie van het begrip zonder voorwaarden")

        return hints


def create_validator(config_path: str = None) -> INT02Validator:
    """
    Factory functie om validator te maken.

    Args:
        config_path: Optioneel pad naar configuratie bestand

    Returns:
        INT02Validator instantie
    """
    import json
    import os

    # Gebruik default config path als niet opgegeven
    if not config_path:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "INT-02.json")

    # Laad configuratie
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    return INT02Validator(config)
