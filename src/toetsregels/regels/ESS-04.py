"""
Toetsregel ESS-04: Toetsbaarheid

Een definitie bevat objectief toetsbare elementen (harde deadlines, aantallen, percentages, meetbare criteria).
Gemigreerd van legacy core.py
"""

import re
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class ESS04Validator:
    """Validator voor ESS-04: Toetsbaarheid."""

    def __init__(self, config: Dict):
        """
        Initialiseer validator met configuratie uit JSON.

        Args:
            config: Dictionary met configuratie uit ESS-04.json
        """
        self.config = config
        self.id = config.get("id", "ESS-04")
        self.naam = config.get("naam", "Toetsbaarheid")
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
        Valideer definitie volgens ESS-04 regel.

        Een definitie moet toetsbare criteria bevatten zodat een gebruiker
        objectief kan vaststellen of iets wel of niet onder het begrip valt.

        Args:
            definitie: De te valideren definitie
            begrip: Het begrip dat gedefinieerd wordt
            context: Optionele context informatie

        Returns:
            Tuple van (succes, melding, score)
        """
        d = definitie.lower().strip()

        # 1️⃣ Expliciete FOUT-voorbeelden uit JSON afvangen
        for fout in self.foute_voorbeelden:
            if fout.lower() in d:
                return (
                    False,
                    (
                        f"❌ {self.id}: bevat vage bewoording "
                        "(bijv. 'zo snel mogelijk') – definitie is niet toetsbaar"
                    ),
                    0.0,
                )

        # 2️⃣ Expliciete GOED-voorbeelden uit JSON herkennen
        for goed in self.goede_voorbeelden:
            if goed.lower() in d:
                return (
                    True,
                    (
                        f"✔️ {self.id}: bevat toetsbare criteria "
                        "(volgens goed voorbeeld uit config)"
                    ),
                    1.0,
                )

        # 3️⃣ Patronen uit JSON op zoek naar harde criteria
        gevonden = []
        for pattern in self.compiled_patterns:
            if pattern.search(definitie):
                gevonden.append(pattern.pattern)

        # 3a️⃣ Extra automatische checks voor getallen/tijd/percentage
        # (legacy compatibiliteit)
        if re.search(r"\b\d+\s*(dagen|weken|uren|maanden)\b", d):
            gevonden.append("AUTO: numeriek tijdspatroon")
        if re.search(r"\b\d+\s*%\b", d):
            gevonden.append("AUTO: percentagepatroon")

        if gevonden:
            unieke = ", ".join(sorted(set(gevonden)))
            return True, f"✔️ {self.id}: toetsbaar criterium herkend ({unieke})", 1.0

        # 4️⃣ Fallback: niets gevonden → definitie is niet toetsbaar
        return (
            False,
            (
                f"❌ {self.id}: geen toetsbare elementen gevonden; "
                "definitie bevat geen harde criteria voor objectieve toetsing"
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

        hints.append("Gebruik objectief toetsbare criteria")
        hints.append(
            "Vermijd vage formuleringen zoals 'zo snel mogelijk', 'zo veel mogelijk'"
        )
        hints.append(
            "Gebruik concrete deadlines: 'binnen 3 dagen', 'uiterlijk na 1 week'"
        )
        hints.append("Gebruik meetbare percentages: 'tenminste 80%', 'maximaal 10%'")
        hints.append("Vermeld waarneembare eigenschappen of kenmerken")

        return hints


def create_validator(config_path: str = None) -> ESS04Validator:
    """
    Factory functie om validator te maken.

    Args:
        config_path: Optioneel pad naar configuratie bestand

    Returns:
        ESS04Validator instantie
    """
    import json
    import os

    # Gebruik default config path als niet opgegeven
    if not config_path:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "ESS-04.json")

    # Laad configuratie
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    return ESS04Validator(config)
