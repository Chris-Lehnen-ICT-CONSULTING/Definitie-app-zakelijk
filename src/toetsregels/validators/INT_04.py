"""
Toetsregel INT-04: Lidwoord-verwijzing duidelijk

Definities mogen geen onduidelijke verwijzingen met de lidwoorden 'de' of 'het' bevatten.
Gemigreerd van legacy core.py
"""

import logging
import re

logger = logging.getLogger(__name__)


class INT04Validator:
    """Validator voor INT-04: Lidwoord-verwijzing duidelijk."""

    def __init__(self, config: dict):
        """
        Initialiseer validator met configuratie uit JSON.

        Args:
            config: Dictionary met configuratie uit INT-04.json
        """
        self.config = config
        self.id = config.get("id", "INT-04")
        self.naam = config.get("naam", "Lidwoord-verwijzing duidelijk")
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
        self, definitie: str, begrip: str, context: dict | None = None
    ) -> tuple[bool, str, float]:
        """
        Valideer definitie volgens INT-04 regel.

        Bij een bepaald lidwoord ('de', 'het') in een definitie moet
        direct helder zijn waarnaar verwezen wordt. Anders is de zin
        vaag of contextafhankelijk.

        Args:
            definitie: De te valideren definitie
            begrip: Het begrip dat gedefinieerd wordt
            context: Optionele context informatie

        Returns:
            Tuple van (succes, melding, score)
        """
        tekst = definitie.strip()
        tekst_lc = tekst.lower()

        # 1️⃣ Verzamel alle 'de …' / 'het …' matches
        hits = []
        for pattern in self.compiled_patterns:
            for match in pattern.finditer(tekst):
                hits.append(match.group(0))

        # 2️⃣ Geen onduidelijke lidwoord-verwijzingen
        if not hits:
            return (
                True,
                f"✔️ {self.id}: geen onduidelijke lidwoord-verwijzingen aangetroffen",
                1.0,
            )

        # 3️⃣ Controle op expliciete goede voorbeelden
        for goed in self.goede_voorbeelden:
            if goed.lower() in tekst_lc:
                unieke = ", ".join(sorted(set(hits)))
                return (
                    True,
                    (
                        f"✔️ {self.id}: lidwoord-verwijzingen ({unieke}) "
                        f"maar correct gespecificeerd volgens voorbeeld"
                    ),
                    1.0,
                )

        # ❌ Fallback: onduidelijke verwijzingen blijven staan
        unieke = ", ".join(sorted(set(hits)))
        return (
            False,
            (
                f"❌ {self.id}: onduidelijke lidwoord-verwijzingen ({unieke}); "
                f"specificeer expliciet of gebruik onbepaald lidwoord"
            ),
            0.0,
        )

    def get_generation_hints(self) -> list[str]:
        """
        Geef hints voor definitie generatie.

        Returns:
            Lijst met instructies voor de AI generator
        """
        hints = []

        hints.append(
            "Bij gebruik van 'de' of 'het', specificeer direct welke instelling/systeem bedoeld wordt"
        )
        hints.append(
            "Bijvoorbeeld: 'de instelling (Raad voor de Rechtspraak)' ipv alleen 'de instelling'"
        )
        hints.append(
            "Of gebruik onbepaalde lidwoorden: 'een instelling' ipv 'de instelling'"
        )
        hints.append("Zorg dat elke verwijzing zelfstandig te begrijpen is")

        return hints


def create_validator(config_path: str | None = None) -> INT04Validator:
    """
    Factory functie om validator te maken.

    Args:
        config_path: Optioneel pad naar configuratie bestand

    Returns:
        INT04Validator instantie
    """
    import json
    import os

    # Gebruik default config path als niet opgegeven
    if not config_path:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "INT-04.json")

    # Laad configuratie
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    return INT04Validator(config)
