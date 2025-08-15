"""
Toetsregel INT-07: Alleen toegankelijke afkortingen

In een definitie gebruikte afkortingen zijn voorzien van een voor de doelgroep direct toegankelijke referentie.
Gemigreerd van legacy core.py
"""

import re
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class INT07Validator:
    """Validator voor INT-07: Alleen toegankelijke afkortingen."""

    def __init__(self, config: Dict):
        """
        Initialiseer validator met configuratie uit JSON.

        Args:
            config: Dictionary met configuratie uit INT-07.json
        """
        self.config = config
        self.id = config.get("id", "INT-07")
        self.naam = config.get("naam", "Alleen toegankelijke afkortingen")
        self.uitleg = config.get("uitleg", "")
        self.herkenbaar_patronen = config.get("herkenbaar_patronen", [])
        self.goede_voorbeelden = config.get("goede_voorbeelden", [])
        self.foute_voorbeelden = config.get("foute_voorbeelden", [])
        self.prioriteit = config.get("prioriteit", "midden")

        # Compile regex patronen voor performance
        self.compiled_patterns = []
        for pattern in self.herkenbaar_patronen:
            try:
                self.compiled_patterns.append(re.compile(pattern))
            except re.error as e:
                logger.warning(f"Ongeldig regex patroon in {self.id}: {pattern} - {e}")

    def validate(
        self, definitie: str, begrip: str, context: Optional[Dict] = None
    ) -> Tuple[bool, str, float]:
        """
        Valideer definitie volgens INT-07 regel.

        Controleert of alle afkortingen in de definitie voorzien zijn van:
        - Directe uitleg tussen haakjes: DJI (Dienst Justitiële Inrichtingen)
        - Markdown link: [AVG](...)
        - Wiki-link: [[...]]

        Args:
            definitie: De te valideren definitie
            begrip: Het begrip dat gedefinieerd wordt
            context: Optionele context informatie

        Returns:
            Tuple van (succes, melding, score)
        """
        tekst = definitie
        tekst_lc = tekst.lower()

        # 1️⃣ Expliciete foute voorbeelden krijgen prioriteit
        for fout in self.foute_voorbeelden:
            if fout.lower() in tekst_lc:
                return (
                    False,
                    f"❌ {self.id}: afkorting zonder uitleg aangetroffen in voorbeeld ('{fout}')",
                    0.0,
                )

        # 2️⃣ Vind álle afkortingen via patronen
        afkorts = set()
        for pattern in self.compiled_patterns:
            afkorts.update(pattern.findall(tekst))

        if not afkorts:
            return True, f"✔️ {self.id}: geen afkortingen in de definitie", 1.0

        # 3️⃣ Voor elke afkorting: controleren op uitleg of link
        zonder_toelichting = []
        for ab in sorted(afkorts):
            esc = re.escape(ab)
            # check op "(...)" direct na de afkorting
            has_parenth = bool(re.search(rf"{esc}\s*\([^)]*?\)", tekst))
            # check op Markdown link [AB](...)
            has_mdlink = bool(re.search(rf"\[{esc}\]\(.*?\)", tekst))
            # check op Wiki-link [[...]]
            has_wikilink = bool(re.search(r"\[\[.*?\]\]", tekst))

            if not (has_parenth or has_mdlink or has_wikilink):
                zonder_toelichting.append(ab)

        # 4️⃣ Eindoordeel
        if zonder_toelichting:
            labels = ", ".join(zonder_toelichting)
            return (
                False,
                f"❌ {self.id}: geen toelichting voor afkorting(en): {labels}",
                0.0,
            )

        return (
            True,
            f"✔️ {self.id}: alle afkortingen voorzien van directe toelichting of link",
            1.0,
        )

    def get_generation_hints(self) -> List[str]:
        """
        Geef hints voor definitie generatie.

        Returns:
            Lijst met instructies voor de AI generator
        """
        hints = []

        hints.append("Geef bij elke afkorting direct de volledige betekenis")
        hints.append("Gebruik formaat: DJI (Dienst Justitiële Inrichtingen)")
        hints.append("Of gebruik hyperlinks: [DJI](link) of [[wiki-link]]")
        hints.append("Vermijd onverklaarde afkortingen voor betere leesbaarheid")

        return hints


def create_validator(config_path: str = None) -> INT07Validator:
    """
    Factory functie om validator te maken.

    Args:
        config_path: Optioneel pad naar configuratie bestand

    Returns:
        INT07Validator instantie
    """
    import json
    import os

    # Gebruik default config path als niet opgegeven
    if not config_path:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "INT-07.json")

    # Laad configuratie
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    return INT07Validator(config)
