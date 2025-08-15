"""
Toetsregel ESS-02: Ontologische categorie expliciteren

Indien een begrip meerdere ontologische categorieën kan aanduiden, moet uit de definitie
ondubbelzinnig blijken welke van deze vier bedoeld wordt: type, particulier, proces of resultaat.
Gemigreerd van legacy core.py
"""

import re
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class ESS02Validator:
    """Validator voor ESS-02: Ontologische categorie expliciteren."""

    def __init__(self, config: Dict):
        """
        Initialiseer validator met configuratie uit JSON.

        Args:
            config: Dictionary met configuratie uit ESS-02.json
        """
        self.config = config
        self.id = config.get("id", "ESS-02")
        self.naam = config.get("naam", "Ontologische categorie expliciteren")
        self.uitleg = config.get("uitleg", "")
        self.prioriteit = config.get("prioriteit", "hoog")

        # Compile regex patronen per categorie voor performance
        self.compiled_patterns = {
            "type": [],
            "particulier": [],
            "proces": [],
            "resultaat": [],
        }

        pattern_mapping = {
            "type": "herkenbaar_patronen_type",
            "particulier": "herkenbaar_patronen_particulier",
            "proces": "herkenbaar_patronen_proces",
            "resultaat": "herkenbaar_patronen_resultaat",
        }

        for category, pattern_key in pattern_mapping.items():
            patterns = config.get(pattern_key, [])
            for pattern in patterns:
                try:
                    self.compiled_patterns[category].append(
                        re.compile(pattern, re.IGNORECASE)
                    )
                except re.error as e:
                    logger.warning(
                        f"Ongeldig regex patroon in {self.id} voor {category}: {pattern} - {e}"
                    )

    def validate(
        self, definitie: str, begrip: str, context: Optional[Dict] = None
    ) -> Tuple[bool, str, float]:
        """
        Valideer definitie volgens ESS-02 regel.

        Controleert of de definitie duidelijk aangeeft of het begrip een:
        - type (soort)
        - particulier (exemplaar)
        - proces (activiteit)
        - resultaat (uitkomst)
        is.

        Args:
            definitie: De te valideren definitie
            begrip: Het begrip dat gedefinieerd wordt
            context: Optionele context informatie

        Returns:
            Tuple van (succes, melding, score)
        """
        d = definitie.lower().strip()

        # 0️⃣ Metadata-override indien meegeleverd
        marker = context.get("marker") if context else None
        if marker:
            m = marker.lower()
            if m in {"soort", "type"}:
                return (
                    True,
                    f"✔️ {self.id}: eenduidig als soort gedefinieerd (via metadata)",
                    1.0,
                )
            if m in {"exemplaar", "particulier"}:
                return (
                    True,
                    f"✔️ {self.id}: eenduidig als exemplaar gedefinieerd (via metadata)",
                    1.0,
                )
            if m in {"proces", "activiteit"}:
                return (
                    True,
                    f"✔️ {self.id}: eenduidig als proces gedefinieerd (via metadata)",
                    1.0,
                )
            if m in {"resultaat", "uitkomst"}:
                return (
                    True,
                    f"✔️ {self.id}: eenduidig als resultaat gedefinieerd (via metadata)",
                    1.0,
                )
            return (
                False,
                f"❌ {self.id}: ongeldige marker '{marker}'; gebruik soort/exemplaar/proces/resultaat",
                0.0,
            )

        # 1️⃣ Expliciete foute voorbeelden per categorie
        categories = [
            ("type", "foute_voorbeelden_type"),
            ("particulier", "foute_voorbeelden_particulier"),
            ("proces", "foute_voorbeelden_proces"),
            ("resultaat", "foute_voorbeelden_resultaat"),
        ]
        for cat, key in categories:
            for voorbeeld in self.config.get(key, []):
                if voorbeeld.lower() in d:
                    return (
                        False,
                        (
                            f"❌ {self.id}: expliciet fout voorbeeld voor {cat} gevonden "
                            f"– vermijd deze formulering"
                        ),
                        0.0,
                    )

        # 2️⃣ Detectie via patronen per categorie
        hits = {}
        for cat, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(d):
                    hits.setdefault(cat, []).append(pattern.pattern)

        # 3️⃣ Één categorie → ✔️
        if len(hits) == 1:
            cat, pats = next(iter(hits.items()))
            unieke = ", ".join(sorted(set(pats)))
            return (
                True,
                f"✔️ {self.id}: eenduidig als {cat} gedefinieerd ({unieke})",
                1.0,
            )

        # 4️⃣ Meerdere categorieën → ❌ ambiguïteit
        if len(hits) > 1:
            found = ", ".join(sorted(hits.keys()))
            return (
                False,
                (
                    f"❌ {self.id}: ambiguïteit – meerdere categories herkend ({found}); "
                    "kies één betekenislaag"
                ),
                0.0,
            )

        # 5️⃣ Geen hits → goede voorbeelden per categorie
        good_keys = {
            "type": "goede_voorbeelden_type",
            "particulier": "goede_voorbeelden_particulier",
            "proces": "goede_voorbeelden_proces",
            "resultaat": "goede_voorbeelden_resultaat",
        }
        for cat, key in good_keys.items():
            for voorbeeld in self.config.get(key, []):
                if voorbeeld.lower() in d:
                    return (
                        True,
                        f"✔️ {self.id}: eenduidig als {cat} gedefinieerd (voorbeeld match)",
                        1.0,
                    )

        # 6️⃣ Fallback → geen marker
        return (
            False,
            (
                f"❌ {self.id}: geen duidelijke ontologische marker "
                "(type, particulier, proces of resultaat) gevonden"
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

        hints.append(
            "Geef duidelijk aan of het begrip een type, particulier, proces of resultaat is"
        )
        hints.append("Type: gebruik 'is een categorie/soort/klasse'")
        hints.append("Particulier: gebruik 'is een exemplaar'")
        hints.append("Proces: gebruik 'is een proces/activiteit/handeling'")
        hints.append("Resultaat: gebruik 'is het resultaat van' of 'is de uitkomst'")

        return hints


def create_validator(config_path: str = None) -> ESS02Validator:
    """
    Factory functie om validator te maken.

    Args:
        config_path: Optioneel pad naar configuratie bestand

    Returns:
        ESS02Validator instantie
    """
    import json
    import os

    # Gebruik default config path als niet opgegeven
    if not config_path:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "ESS-02.json")

    # Laad configuratie
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    return ESS02Validator(config)
