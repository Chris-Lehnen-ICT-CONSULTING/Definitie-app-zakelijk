"""
Toetsregel SAM-05: Repository termen gebruiken

Gebruik waar mogelijk termen uit de bestaande repository/woordenlijst.
Gemigreerd van legacy core.py
"""

import re
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class SAM05Validator:
    """Validator voor SAM-05: Repository termen gebruiken."""

    def __init__(self, config: Dict):
        """
        Initialiseer validator met configuratie uit JSON.

        Args:
            config: Dictionary met configuratie uit SAM-05.json
        """
        self.config = config
        self.id = config.get("id", "SAM-05")
        self.naam = config.get("naam", "Repository termen gebruiken")
        self.uitleg = config.get("uitleg", "")
        self.prioriteit = config.get("prioriteit", "midden")

    def validate(
        self, definitie: str, begrip: str, context: Optional[Dict] = None
    ) -> Tuple[bool, str, float]:
        """
        Valideer definitie volgens SAM-05 regel.

        Controleert of de definitie gebruik maakt van bestaande termen uit de repository.
        Dit bevordert consistentie en hergebruik van gestandaardiseerde terminologie.

        Args:
            definitie: De te valideren definitie
            begrip: Het begrip dat gedefinieerd wordt
            context: Optionele context informatie met repository

        Returns:
            Tuple van (succes, melding, score)
        """
        # Haal repository uit context
        repository = None
        if context:
            repository = context.get("repository", {})

        if not repository:
            # Geen repository beschikbaar, kunnen niet controleren
            return True, f"🟡 {self.id}: geen repository beschikbaar voor controle", 0.5

        # Normaliseer definitie
        definitie_lower = definitie.lower()

        # Tel repository termen in definitie
        gevonden_termen = []
        for term in repository:
            term_lower = term.lower()
            # Zoek naar hele woorden, niet delen
            pattern = rf"\b{re.escape(term_lower)}\b"
            if re.search(pattern, definitie_lower):
                gevonden_termen.append(term)

        if gevonden_termen:
            # Bereken score op basis van aantal gevonden termen
            score = min(
                1.0, len(gevonden_termen) * 0.25
            )  # Max 4 termen voor volledige score
            termen_str = ", ".join(sorted(gevonden_termen))
            return (
                True,
                (
                    f"✔️ {self.id}: gebruikt {len(gevonden_termen)} repository termen: {termen_str}"
                ),
                score,
            )
        else:
            return (
                False,
                f"🟡 {self.id}: geen repository termen gebruikt in definitie",
                0.3,
            )

    def get_generation_hints(self) -> List[str]:
        """
        Geef hints voor definitie generatie.

        Returns:
            Lijst met instructies voor de AI generator
        """
        hints = []

        hints.append("Gebruik waar mogelijk bestaande termen uit de repository")
        hints.append("Dit bevordert consistentie en begrip")
        hints.append("Vermijd synoniemen voor termen die al in de repository staan")
        hints.append("Hergebruik gestandaardiseerde terminologie")

        return hints


def create_validator(config_path: str = None) -> SAM05Validator:
    """
    Factory functie om validator te maken.

    Args:
        config_path: Optioneel pad naar configuratie bestand

    Returns:
        SAM05Validator instantie
    """
    import json
    import os

    # Gebruik default config path als niet opgegeven
    if not config_path:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "SAM-05.json")

    # Laad configuratie
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    return SAM05Validator(config)
