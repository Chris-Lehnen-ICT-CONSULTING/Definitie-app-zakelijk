"""
Toetsregel INT-10: Geen ontoegankelijke achtergrondkennis nodig

Een definitie moet begrijpelijk zijn zonder specialistische of niet-openbare kennis.
Gemigreerd van legacy core.py
"""

import re
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class INT10Validator:
    """Validator voor INT-10: Geen ontoegankelijke achtergrondkennis nodig."""

    def __init__(self, config: Dict):
        """
        Initialiseer validator met configuratie uit JSON.

        Args:
            config: Dictionary met configuratie uit INT-10.json
        """
        self.config = config
        self.id = config.get("id", "INT-10")
        self.naam = config.get("naam", "Geen ontoegankelijke achtergrondkennis nodig")
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
        Valideer definitie volgens INT-10 regel.

        Een goede definitie is zelfstandig begrijpelijk en mag niet verwijzen
        naar impliciete kennis in hoofden van mensen, interne procedures of
        niet-openbare documenten.

        Args:
            definitie: De te valideren definitie
            begrip: Het begrip dat gedefinieerd wordt
            context: Optionele context informatie

        Returns:
            Tuple van (succes, melding, score)
        """
        tekst_lc = definitie.lower()

        # 1️⃣ Expliciete foute voorbeelden
        for fout in self.foute_voorbeelden:
            if fout.lower() in tekst_lc:
                return (
                    False,
                    (
                        f"❌ {self.id}: definitie verwijst naar ontoegankelijke kennis "
                        f"(voorbeeld match)"
                    ),
                    0.0,
                )

        # 2️⃣ Check patronen die wijzen op externe verwijzingen
        gevonden = []
        for pattern in self.compiled_patterns:
            matches = pattern.findall(definitie)
            gevonden.extend(matches)

        if gevonden:
            unieke = ", ".join(sorted(set(gevonden)))
            return (
                False,
                (
                    f"❌ {self.id}: verwijzing naar mogelijk ontoegankelijke kennis: {unieke}"
                ),
                0.0,
            )

        # 3️⃣ Check op goede voorbeelden
        for goed in self.goede_voorbeelden:
            if goed.lower() in tekst_lc:
                return (
                    True,
                    (
                        f"✔️ {self.id}: definitie zelfstandig begrijpelijk "
                        "(goed voorbeeld match)"
                    ),
                    1.0,
                )

        # 4️⃣ Fallback: geen problematische verwijzingen
        return (
            True,
            f"✔️ {self.id}: definitie vereist geen ontoegankelijke achtergrondkennis",
            1.0,
        )

    def get_generation_hints(self) -> List[str]:
        """
        Geef hints voor definitie generatie.

        Returns:
            Lijst met instructies voor de AI generator
        """
        hints = []

        hints.append("Maak de definitie zelfstandig begrijpelijk")
        hints.append("Vermijd verwijzingen naar interne documenten of procedures")
        hints.append("Leg vaktermen uit of vermijd ze")
        hints.append("Bij wetsverwijzing: geef specifiek artikel en hyperlink")
        hints.append("Vermijd impliciete aannames over voorkennis")

        return hints


def create_validator(config_path: str = None) -> INT10Validator:
    """
    Factory functie om validator te maken.

    Args:
        config_path: Optioneel pad naar configuratie bestand

    Returns:
        INT10Validator instantie
    """
    import json
    import os

    # Gebruik default config path als niet opgegeven
    if not config_path:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "INT-10.json")

    # Laad configuratie
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    return INT10Validator(config)
