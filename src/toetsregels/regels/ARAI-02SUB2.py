"""
Toetsregel ARAI02SUB2
Automatisch gemigreerd van legacy core.py
"""

import logging
import re
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ARAI02SUB2Validator:
    """Validator voor ARAI02SUB2."""

    def __init__(self, config: Dict):
        """
        Initialiseer validator met configuratie uit JSON.

        Args:
            config: Dictionary met configuratie uit ARAI02SUB2.json
        """
        self.config = config
        self.id = config.get("id", "ARAI02SUB2")
        self.naam = config.get("naam", "")
        self.uitleg = config.get("uitleg", "")
        self.prioriteit = config.get("prioriteit", "midden")

    def validate(
        self, definitie: str, begrip: str, context: Optional[Dict] = None
    ) -> Tuple[bool, str, float]:
        """
        Valideer definitie volgens ARAI02SUB2 regel.

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
            container_termen = set()
            for patroon in patronen:
                container_termen.update(re.findall(patroon, definitie, re.IGNORECASE))

            goed = any(
                g.lower() in definitie.lower()
                for g in regel.get("goede_voorbeelden", [])
            )
            fout = any(
                f.lower() in definitie.lower()
                for f in regel.get("foute_voorbeelden", [])
            )

            if not container_termen:
                if goed:
                    result = "✔️ ARAI02SUB2: geen ambtelijke containerbegrippen, definitie sluit aan bij goed voorbeeld"
                else:
                    result = (
                        "✔️ ARAI02SUB2: geen ambtelijke containerbegrippen aangetroffen"
                    )

            else:
                if fout:
                    result = f"❌ ARAI02SUB2: ambtelijke containerbegrippen gevonden ({', '.join(container_termen)}), zoals in fout voorbeeld"
                else:
                    result = f"❌ ARAI02SUB2: containerbegrippen gevonden ({', '.join(container_termen)}), onvoldoende specifiek"
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

    def get_generation_hints(self) -> List[str]:
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


def create_validator(config_path: str = None) -> ARAI02SUB2Validator:
    """
    Factory functie om validator te maken.

    Args:
        config_path: Optioneel pad naar configuratie bestand

    Returns:
        ARAI02SUB2Validator instantie
    """
    import json
    import os

    if not config_path:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "ARAI02SUB2.json")

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    return ARAI02SUB2Validator(config)
