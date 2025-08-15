"""
Toetsregel SAM-07
Automatisch gemigreerd van legacy core.py
"""

import re
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class SAM07Validator:
    """Validator voor SAM-07."""

    def __init__(self, config: Dict):
        """
        Initialiseer validator met configuratie uit JSON.

        Args:
            config: Dictionary met configuratie uit SAM-07.json
        """
        self.config = config
        self.id = config.get("id", "SAM-07")
        self.naam = config.get("naam", "")
        self.uitleg = config.get("uitleg", "")
        self.prioriteit = config.get("prioriteit", "midden")

    def validate(
        self, definitie: str, begrip: str, context: Optional[Dict] = None
    ) -> Tuple[bool, str, float]:
        """
        Valideer definitie volgens SAM-07 regel.

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
            uitbreidingen = set()
            for patroon in patronen:
                uitbreidingen.update(re.findall(patroon, definitie, re.IGNORECASE))

            goede_voorbeelden = regel.get("goede_voorbeelden", [])
            foute_voorbeelden = regel.get("foute_voorbeelden", [])

            goed = any(vb.lower() in definitie.lower() for vb in goede_voorbeelden)
            fout = any(vb.lower() in definitie.lower() for vb in foute_voorbeelden)

            if not uitbreidingen:
                if fout:
                    result = "❌ SAM-07: geen expliciete uitbreidingen gevonden, maar formulering lijkt op fout voorbeeld"
                else:
                    result = "✔️ SAM-07: geen uitbreidende elementen herkend"

            else:
                if goed:
                    result = f"✔️ SAM-07: uitbreiding(en) herkend ({', '.join(uitbreidingen)}), maar correct gebruikt zoals in goed voorbeeld"
                elif fout:
                    result = f"❌ SAM-07: uitbreiding(en) herkend ({', '.join(uitbreidingen)}), en lijkt op fout voorbeeld"
                else:
                    result = f"❌ SAM-07: uitbreiding(en) herkend ({', '.join(uitbreidingen)}), onvoldoende kernachtig"

            return f"❌ SAM-07: uitbreiding(en) herkend ({', '.join(uitbreidingen)}), zonder correcte toelichting"
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


def create_validator(config_path: str = None) -> SAM07Validator:
    """
    Factory functie om validator te maken.

    Args:
        config_path: Optioneel pad naar configuratie bestand

    Returns:
        SAM07Validator instantie
    """
    import json
    import os

    if not config_path:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "SAM-07.json")

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    return SAM07Validator(config)
