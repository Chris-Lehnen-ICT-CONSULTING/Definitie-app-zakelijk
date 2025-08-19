"""
Toetsregel STR-07
Automatisch gemigreerd van legacy core.py
"""

import logging
import re

logger = logging.getLogger(__name__)


class STR07Validator:
    """Validator voor STR-07."""

    def __init__(self, config: dict):
        """
        Initialiseer validator met configuratie uit JSON.

        Args:
            config: Dictionary met configuratie uit STR-07.json
        """
        self.config = config
        self.id = config.get("id", "STR-07")
        self.naam = config.get("naam", "")
        self.uitleg = config.get("uitleg", "")
        self.prioriteit = config.get("prioriteit", "midden")

    def validate(
        self, definitie: str, begrip: str, context: dict | None = None
    ) -> tuple[bool, str, float]:
        """
        Valideer definitie volgens STR-07 regel.

        Args:
            definitie: De te valideren definitie
            begrip: Het begrip dat gedefinieerd wordt
            context: Optionele context informatie

        Returns:
            Tuple van (succes, melding, score)
        """
        # Haal regel config op
        regel = self.config

        # Extract context parameters indien nodig
        if context:
            # Context processing kan hier toegevoegd worden indien nodig
            pass

        # Legacy implementatie
        try:
            patronen = regel.get("herkenbaar_patronen", [])
            dubbele_ontkenning = set()
            for patroon in patronen:
                dubbele_ontkenning.update(re.findall(patroon, definitie, re.IGNORECASE))

            foute = any(
                f.lower() in definitie.lower()
                for f in regel.get("foute_voorbeelden", [])
            )

            if not dubbele_ontkenning:
                result = "✔️ STR-07: geen dubbele ontkenning aangetroffen"

            elif foute:
                result = f"❌ STR-07: dubbele ontkenning herkend ({', '.join(dubbele_ontkenning)}), overeenkomend met fout voorbeeld"
            else:
                result = f"❌ STR-07: dubbele ontkenning herkend ({', '.join(dubbele_ontkenning)}), controle nodig"
        except Exception as e:
            logger.error(f"Fout in {self.id} validator: {e}")
            return False, f"⚠️ {self.id}: fout bij uitvoeren toetsregel", 0.0

        # Convert legacy return naar nieuwe format
        if isinstance(result, str):
            # Bepaal succes op basis van emoji
            succes = "✔️" in result or "✅" in result
            score = 1.0 if succes else 0.0
            if "🟡" in result:
                score = 0.5
            return succes, result, score

        # Fallback
        return False, f"⚠️ {self.id}: geen resultaat", 0.0

    def get_generation_hints(self) -> list[str]:
        """
        Geef hints voor definitie generatie.

        Returns:
            Lijst met instructies voor de AI generator
        """
        hints = []

        if self.uitleg:
            hints.append(self.uitleg)

        goede_voorbeelden = self.config.get("goede_voorbeelden", [])
        if goede_voorbeelden:
            hints.append(f"Volg dit voorbeeld: {goede_voorbeelden[0]}")

        return hints


def create_validator(config_path: str = None) -> STR07Validator:
    """
    Factory functie om validator te maken.

    Args:
        config_path: Optioneel pad naar configuratie bestand

    Returns:
        STR07Validator instantie
    """
    import json
    import os

    if not config_path:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "STR-07.json")

    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    return STR07Validator(config)
