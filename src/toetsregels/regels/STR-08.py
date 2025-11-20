"""
Toetsregel STR-08
Automatisch gemigreerd van legacy core.py
"""

import logging
import re

logger = logging.getLogger(__name__)


class STR08Validator:
    """Validator voor STR-08."""

    def __init__(self, config: dict):
        """
        Initialiseer validator met configuratie uit JSON.

        Args:
            config: Dictionary met configuratie uit STR-08.json
        """
        self.config = config
        self.id = config.get("id", "STR-08")
        self.naam = config.get("naam", "")
        self.uitleg = config.get("uitleg", "")
        self.prioriteit = config.get("prioriteit", "midden")

    def validate(
        self, definitie: str, begrip: str, context: dict | None = None
    ) -> tuple[bool, str, float]:
        """
        Valideer definitie volgens STR-08 regel.

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
            # ── 1) Start met je JSON-patronen en breid uit met strikte regex voor "A, B en C" en "X en Y"
            patronen = list(regel.get("herkenbaar_patronen", [])) + [
                r"\b\w+,\s*\w+\s+en\s+\w+\b",  # bv. "A, B en C"
                r"\b\w+\s+en\s+\w+\b",  # bv. "X en Y"
            ]

            # ── 2) Match alle gevonden 'en'-constructies
            en_vormen = set()
            for pat in patronen:
                en_vormen.update(re.findall(pat, definitie, re.IGNORECASE))

            # ── 3) Whitelist uitzonderingen (optioneel)
            whitelist = {
                "in en uitsluiting",
                "vraag en antwoord",
                "verificatie en bevestiging",
                # voeg hier meer vaste combinaties toe
            }
            en_vormen = {ev for ev in en_vormen if ev.lower() not in whitelist}

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
            if not en_vormen:
                result = "✔️ STR-08: geen dubbelzinnige 'en'-constructies aangetroffen"
            elif en_vormen and goed:
                result = (
                    "✔️ STR-08: 'en' staat er wel, maar komt overeen met goed voorbeeld"
                )
            elif fout:
                result = f"❌ STR-08: dubbelzinnige 'en' gevonden ({', '.join(en_vormen)}) en lijkt op fout voorbeeld"
            else:
                result = f"❌ STR-08: dubbelzinnige 'en' gevonden ({', '.join(en_vormen)}), context verduidelijken"
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


def create_validator(config_path: str | None = None) -> STR08Validator:
    """
    Factory functie om validator te maken.

    Args:
        config_path: Optioneel pad naar configuratie bestand

    Returns:
        STR08Validator instantie
    """
    import json
    import os

    if not config_path:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "STR-08.json")

    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    return STR08Validator(config)
