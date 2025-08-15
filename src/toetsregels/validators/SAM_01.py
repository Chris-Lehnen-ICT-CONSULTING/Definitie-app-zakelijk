"""
Toetsregel SAM-01: Kwalificatie leidt niet tot afwijking

Een definitie mag niet zodanig zijn geformuleerd dat deze afwijkt van de betekenis die de term in andere contexten heeft.
Gemigreerd van legacy core.py
"""

import re
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class SAM01Validator:
    """Validator voor SAM-01: Kwalificatie leidt niet tot afwijking."""

    def __init__(self, config: Dict):
        """
        Initialiseer validator met configuratie uit JSON.

        Args:
            config: Dictionary met configuratie uit SAM-01.json
        """
        self.config = config
        self.id = config.get("id", "SAM-01")
        self.naam = config.get("naam", "Kwalificatie leidt niet tot afwijking")
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
        Valideer definitie volgens SAM-01 regel.

        Controleert of kwalificaties zoals 'technisch', 'juridisch', 'operationeel'
        niet leiden tot een betekenis die afwijkt van het algemeen aanvaarde begrip.

        Args:
            definitie: De te valideren definitie
            begrip: Het begrip dat gedefinieerd wordt
            context: Optionele context informatie

        Returns:
            Tuple van (succes, melding, score)
        """
        tekst_lc = definitie.lower()

        # Check voor expliciete foute voorbeelden
        for fout in self.foute_voorbeelden:
            if fout.lower() in tekst_lc:
                return (
                    False,
                    (
                        f"❌ {self.id}: kwalificatie leidt tot misleidende betekenisafwijking "
                        "(fout voorbeeld)"
                    ),
                    0.0,
                )

        # Zoek kwalificaties
        gevonden_kwalificaties = []
        for pattern in self.compiled_patterns:
            matches = pattern.findall(definitie)
            gevonden_kwalificaties.extend(matches)

        # Check voor goede voorbeelden
        for goed in self.goede_voorbeelden:
            if goed.lower() in tekst_lc:
                if gevonden_kwalificaties:
                    return (
                        True,
                        (
                            f"✔️ {self.id}: kwalificatie(s) gevonden ({', '.join(gevonden_kwalificaties)}), "
                            "maar correct gebruikt volgens voorbeeld"
                        ),
                        1.0,
                    )
                else:
                    return (
                        True,
                        f"✔️ {self.id}: geen misleidende kwalificaties aangetroffen",
                        1.0,
                    )

        # Als er kwalificaties zijn zonder goede voorbeelden
        if gevonden_kwalificaties:
            return (
                False,
                (
                    f"🟡 {self.id}: kwalificatie(s) gevonden ({', '.join(gevonden_kwalificaties)}), "
                    "controleer of betekenis consistent blijft"
                ),
                0.5,
            )

        # Geen kwalificaties gevonden
        return (
            True,
            f"✔️ {self.id}: geen potentieel misleidende kwalificaties aangetroffen",
            1.0,
        )

    def get_generation_hints(self) -> List[str]:
        """
        Geef hints voor definitie generatie.

        Returns:
            Lijst met instructies voor de AI generator
        """
        hints = []

        hints.append(
            "Gebruik kwalificaties (technisch, juridisch, etc.) alleen als ze de betekenis verduidelijken"
        )
        hints.append(
            "Zorg dat de definitie consistent blijft met algemeen gebruik van de term"
        )
        hints.append("Vermijd semantisch misleidende kwalificaties")
        hints.append(
            "Als een kwalificatie nodig is, leg dan uit hoe deze de betekenis beïnvloedt"
        )

        return hints


def create_validator(config_path: str = None) -> SAM01Validator:
    """
    Factory functie om validator te maken.

    Args:
        config_path: Optioneel pad naar configuratie bestand

    Returns:
        SAM01Validator instantie
    """
    import json
    import os

    # Gebruik default config path als niet opgegeven
    if not config_path:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "SAM-01.json")

    # Laad configuratie
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    return SAM01Validator(config)
