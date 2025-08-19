"""
Toetsregel CON-02: Baseren op authentieke bron

Deze regel controleert of er een expliciete bronvermelding aanwezig is via het veld 'bronnen_gebruikt'.
Gemigreerd van legacy core.py
"""

import logging
import re

logger = logging.getLogger(__name__)


class CON02Validator:
    """Validator voor CON-02: Baseren op authentieke bron."""

    def __init__(self, config: dict):
        """
        Initialiseer validator met configuratie uit JSON.

        Args:
            config: Dictionary met configuratie uit CON-02.json
        """
        self.config = config
        self.id = config.get("id", "CON-02")
        self.naam = config.get("naam", "Baseren op authentieke bron")
        self.uitleg = config.get("uitleg", "")
        self.bronpatronen_specifiek = config.get("bronpatronen_specifiek", [])
        self.bronpatronen_algemeen = config.get("bronpatronen_algemeen", [])
        self.prioriteit = config.get("prioriteit", "hoog")

        # Compile regex patronen voor performance
        self.compiled_specifiek = []
        self.compiled_algemeen = []

        for pattern in self.bronpatronen_specifiek:
            try:
                self.compiled_specifiek.append(re.compile(pattern, re.IGNORECASE))
            except re.error as e:
                logger.warning(
                    f"Ongeldig specifiek patroon in {self.id}: {pattern} - {e}"
                )

        for pattern in self.bronpatronen_algemeen:
            try:
                self.compiled_algemeen.append(re.compile(pattern, re.IGNORECASE))
            except re.error as e:
                logger.warning(
                    f"Ongeldig algemeen patroon in {self.id}: {pattern} - {e}"
                )

    def validate(
        self, definitie: str, begrip: str, context: dict | None = None
    ) -> tuple[bool, str, float]:
        """
        Valideer definitie volgens CON-02 regel.

        Deze toets kijkt naar het 'bronnen_gebruikt' veld, niet naar de definitie zelf.
        Een goede definitie is gebaseerd op een gezaghebbende bron (wetgeving, beleidsregel, standaard).

        Args:
            definitie: De te valideren definitie
            begrip: Het begrip dat gedefinieerd wordt
            context: Optionele context informatie met bronnen_gebruikt

        Returns:
            Tuple van (succes, melding, score)
        """
        # Haal bronnen_gebruikt uit context
        bronnen_gebruikt = None
        if context:
            bronnen_gebruikt = context.get("bronnen_gebruikt")

        # 1️⃣ ❌ geen bronnen opgegeven
        if not bronnen_gebruikt or not bronnen_gebruikt.strip():
            return (
                False,
                f"❌ {self.id}: geen opgegeven bronnen gevonden (veld 'bronnen_gebruikt' is leeg of ontbreekt)",
                0.0,
            )

        bg = bronnen_gebruikt.strip()
        lc = bg.lower()

        # 2️⃣ ✔️ check concrete patronen
        for pattern in self.compiled_specifiek:
            if pattern.search(lc):
                return (
                    True,
                    f"✔️ {self.id}: bronvermelding voldoende specifiek → {bg}",
                    1.0,
                )

        # 3️⃣ 🟡 check algemene patronen
        for pattern in self.compiled_algemeen:
            if pattern.search(lc):
                return (
                    False,
                    f"🟡 {self.id}: bronvermelding aanwezig ({bg}), maar mogelijk te algemeen",
                    0.5,
                )

        # 4️⃣ ❌ fallback
        return (
            False,
            f"❌ {self.id}: bronvermelding gevonden ({bg}), maar niet herkend als authentiek of specifiek",
            0.0,
        )

    def get_generation_hints(self) -> list[str]:
        """
        Geef hints voor definitie generatie.

        Returns:
            Lijst met instructies voor de AI generator
        """
        hints = []

        hints.append("Baseer de definitie op een gezaghebbende bron")
        hints.append("Verwijs specifiek naar artikelen, paragrafen of hoofdstukken")
        hints.append(
            "Voorbeelden: 'art. 3.2 Besluit justitiële gegevens', 'Titel 1.4 Awb'"
        )
        hints.append(
            "Vermijd te algemene verwijzingen zoals alleen 'de AVG' of 'wetgeving'"
        )

        return hints


def create_validator(config_path: str = None) -> CON02Validator:
    """
    Factory functie om validator te maken.

    Args:
        config_path: Optioneel pad naar configuratie bestand

    Returns:
        CON02Validator instantie
    """
    import json
    import os

    # Gebruik default config path als niet opgegeven
    if not config_path:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "CON-02.json")

    # Laad configuratie
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    return CON02Validator(config)
