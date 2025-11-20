"""
Toetsregel STR-09
Automatisch gemigreerd van legacy core.py
"""

import logging
import re

logger = logging.getLogger(__name__)


class STR09Validator:
    """Validator voor STR-09."""

    def __init__(self, config: dict):
        """
        Initialiseer validator met configuratie uit JSON.

        Args:
            config: Dictionary met configuratie uit STR-09.json
        """
        self.config = config
        self.id = config.get("id", "STR-09")
        self.naam = config.get("naam", "")
        self.uitleg = config.get("uitleg", "")
        self.prioriteit = config.get("prioriteit", "midden")

    def validate(
        self, definitie: str, begrip: str, context: dict | None = None
    ) -> tuple[bool, str, float]:
        """
        Valideer definitie volgens STR-09 regel.

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
            # ── 1) Combineer JSON-patronen met strikte regex voor "A, B of C" en "X of Y"
            patronen = list(regel.get("herkenbaar_patronen", [])) + [
                r"\b\w+,\s*\w+\s+of\s+\w+\b",  # bv. "A, B of C"
                r"\b\w+\s+of\s+\w+\b",  # bv. "X of Y"
            ]

            # ── 2) Verzamel alle gevonden 'of'-constructies
            of_vormen = set()
            for pat in patronen:
                of_vormen.update(re.findall(pat, definitie, re.IGNORECASE))

            # ── 3) Whitelist uitzonderingen (optioneel)
            whitelist = {
                "en/of",
                "met of zonder",
                "al dan niet",  # voeg hier meer vaste combinaties toe
            }
            ambigue = {ov for ov in of_vormen if ov.lower() not in whitelist}

            # ── 4) Controle op goede/foute voorbeelden uit je JSON
            goed = any(
                vb.lower() in definitie.lower()
                for vb in regel.get("goede_voorbeelden", [])
            )
            fout = any(
                vb.lower() in definitie.lower()
                for vb in regel.get("foute_voorbeelden", [])
            )

            # ── 5) Beslis en retourneer resultaat
            if not ambigue:
                result = "✔️ STR-09: geen dubbelzinnige 'of'-constructies aangetroffen"
            elif ambigue and goed:
                result = "✔️ STR-09: 'of'-constructie komt overeen met goed voorbeeld"
            elif fout:
                result = f"❌ STR-09: dubbelzinnige 'of' gevonden ({', '.join(ambigue)}) en lijkt op fout voorbeeld"
            else:
                result = f"❌ STR-09: dubbelzinnige 'of' gevonden ({', '.join(ambigue)}), context verduidelijken"
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


def create_validator(config_path: str | None = None) -> STR09Validator:
    """
    Factory functie om validator te maken.

    Args:
        config_path: Optioneel pad naar configuratie bestand

    Returns:
        STR09Validator instantie
    """
    import json
    import os

    if not config_path:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "STR-09.json")

    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    return STR09Validator(config)
