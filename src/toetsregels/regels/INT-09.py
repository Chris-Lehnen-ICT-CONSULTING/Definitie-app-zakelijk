"""
Toetsregel INT-09: Opsomming in extensionele definitie is limitatief

Een extensionele definitie definieert een begrip door opsomming van alle bedoelde elementen.
Gemigreerd van legacy core.py
"""

import logging
import re

logger = logging.getLogger(__name__)


class INT09Validator:
    """Validator voor INT-09: Opsomming in extensionele definitie is limitatief."""

    def __init__(self, config: dict):
        """
        Initialiseer validator met configuratie uit JSON.

        Args:
            config: Dictionary met configuratie uit INT-09.json
        """
        self.config = config
        self.id = config.get("id", "INT-09")
        self.naam = config.get(
            "naam", "Opsomming in extensionele definitie is limitatief"
        )
        self.uitleg = config.get("uitleg", "")
        self.herkenbaar_patronen = config.get("herkenbaar_patronen", [])
        self.goede_voorbeelden = config.get("goede_voorbeelden", [])
        self.foute_voorbeelden = config.get("foute_voorbeelden", [])
        self.prioriteit = config.get("prioriteit", "midden")

        # Compile regex patronen voor performance
        self.compiled_patterns = []
        for pattern in self.herkenbaar_patronen:
            try:
                self.compiled_patterns.append(
                    re.compile(rf"\b{pattern}\b", re.IGNORECASE)
                )
            except re.error as e:
                logger.warning(f"Ongeldig regex patroon in {self.id}: {pattern} - {e}")

    def validate(
        self, definitie: str, begrip: str, context: dict | None = None
    ) -> tuple[bool, str, float]:
        """
        Valideer definitie volgens INT-09 regel.

        Wanneer een opsomming in een definitie voorkomt, moet expliciet blijken
        dat de genoemde elementen de enige mogelijke zijn. Vermijd termen als
        "zoals", "bijvoorbeeld", "onder andere".

        Args:
            definitie: De te valideren definitie
            begrip: Het begrip dat gedefinieerd wordt
            context: Optionele context informatie

        Returns:
            Tuple van (succes, melding, score)
        """
        # 1️⃣ Verzamel alle treffers (lowercase, uniek)
        tekst_lc = definitie.lower()
        ongewenste_termen = set()

        for pattern in self.compiled_patterns:
            matches = pattern.findall(definitie)
            ongewenste_termen.update(match.lower() for match in matches)

        # 2️⃣ & 3️⃣ Voorbeelden-check
        goede = [vb.lower() for vb in self.goede_voorbeelden]
        fout = [vb.lower() for vb in self.foute_voorbeelden]
        uitleg_aanwezig = any(vb in tekst_lc for vb in goede)
        fout_aanwezig = any(vb in tekst_lc for vb in fout)

        # 4️⃣ Geen ongewenste termen gevonden
        if not ongewenste_termen:
            if uitleg_aanwezig:
                return (
                    True,
                    f"✅ {self.id}: geen ongewenste termen, komt overeen met goed voorbeeld",
                    1.0,
                )
            return (
                True,
                f"✅ {self.id}: geen ongewenste opsommingstermen gevonden",
                1.0,
            )

        # 5️⃣ Wel ongewenste termen gevonden
        termen_str = ", ".join(sorted(ongewenste_termen))

        if uitleg_aanwezig:
            return (
                True,
                f"✅ {self.id}: opsommingswoorden ({termen_str}) voorkomen, maar correct limitatief verwoord",
                0.8,
            )

        if fout_aanwezig:
            return (
                False,
                f"❌ {self.id}: opsommingswoorden ({termen_str}) lijken op fout voorbeeld",
                0.0,
            )

        return (
            False,
            f"❌ {self.id}: opsommingswoorden ({termen_str}) zonder duidelijke limitatieve aanduiding",
            0.0,
        )

    def get_generation_hints(self) -> list[str]:
        """
        Geef hints voor definitie generatie.

        Returns:
            Lijst met instructies voor de AI generator
        """
        hints = []

        hints.append("Bij opsommingen: maak duidelijk dat het een complete lijst is")
        hints.append(
            "Vermijd woorden zoals: 'bijvoorbeeld', 'zoals', 'onder andere', 'enz.'"
        )
        hints.append(
            "Gebruik formuleringen als: 'uitsluitend', 'alleen', 'precies deze'"
        )
        hints.append(
            "Als de lijst niet compleet is, gebruik dan een intensionele definitie"
        )

        return hints


def create_validator(config_path: str = None) -> INT09Validator:
    """
    Factory functie om validator te maken.

    Args:
        config_path: Optioneel pad naar configuratie bestand

    Returns:
        INT09Validator instantie
    """
    import json
    import os

    # Gebruik default config path als niet opgegeven
    if not config_path:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "INT-09.json")

    # Laad configuratie
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    return INT09Validator(config)
