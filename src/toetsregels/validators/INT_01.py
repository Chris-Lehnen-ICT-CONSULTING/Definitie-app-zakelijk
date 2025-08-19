"""
Toetsregel INT-01: Compacte en begrijpelijke zin

Een definitie is compact en in één enkele zin geformuleerd.
Gemigreerd van legacy core.py
"""

import logging
import re

logger = logging.getLogger(__name__)


class INT01Validator:
    """Validator voor INT-01: Compacte en begrijpelijke zin."""

    def __init__(self, config: dict):
        """
        Initialiseer validator met configuratie uit JSON.

        Args:
            config: Dictionary met configuratie uit INT-01.json
        """
        self.config = config
        self.id = config.get("id", "INT-01")
        self.naam = config.get("naam", "Compacte en begrijpelijke zin")
        self.uitleg = config.get(
            "uitleg", "Een definitie is compact en in één enkele zin geformuleerd."
        )
        self.herkenbaar_patronen = config.get("herkenbaar_patronen", [])
        self.goede_voorbeelden = config.get("goede_voorbeelden", [])
        self.foute_voorbeelden = config.get("foute_voorbeelden", [])
        self.prioriteit = config.get("prioriteit", "midden")

        # Compile regex patronen voor performance
        self.compiled_patterns = []
        for pattern in self.herkenbaar_patronen:
            try:
                # Speciale behandeling voor simpele strings als ","
                if pattern in [",", ";"]:
                    # Direct gebruik zonder regex voor simpele karakters
                    self.compiled_patterns.append(pattern)
                else:
                    self.compiled_patterns.append(re.compile(pattern, re.IGNORECASE))
            except re.error as e:
                logger.warning(f"Ongeldig regex patroon in {self.id}: {pattern} - {e}")

    def validate(
        self, definitie: str, begrip: str, context: dict | None = None
    ) -> tuple[bool, str, float]:
        """
        Valideer definitie volgens INT-01 regel.

        Deze regel controleert of de definitie compact is en niet te complex
        door te kijken naar complexiteits-indicatoren zoals bijzinnen,
        opsommingen en complexe structuren.

        Args:
            definitie: De te valideren definitie
            begrip: Het begrip dat gedefinieerd wordt
            context: Optionele context informatie

        Returns:
            Tuple van (succes, melding, score)
        """
        # Verzamel gevonden complexiteits-indicatoren
        complexiteit_gevonden = set()

        for pattern in self.compiled_patterns:
            if isinstance(pattern, str):
                # Direct string match voor simpele karakters
                if pattern in definitie:
                    complexiteit_gevonden.add(pattern)
            else:
                # Regex pattern match
                matches = pattern.findall(definitie)
                complexiteit_gevonden.update(match.lower() for match in matches)

        # Check voorbeelden
        definitie_lower = definitie.lower()
        goede_aanwezig = any(
            voorbeeld.lower() in definitie_lower for voorbeeld in self.goede_voorbeelden
        )
        foute_aanwezig = any(
            voorbeeld.lower() in definitie_lower for voorbeeld in self.foute_voorbeelden
        )

        # Bepaal resultaat volgens legacy logica
        if not complexiteit_gevonden:
            if goede_aanwezig:
                return (
                    True,
                    f"✔️ {self.id}: definitie is compact en komt overeen met goed voorbeeld",
                    1.0,
                )
            return (
                True,
                f"✔️ {self.id}: geen complexe elementen herkend - mogelijk goed geformuleerd",
                0.9,
            )

        if foute_aanwezig:
            return (
                False,
                (
                    f"❌ {self.id}: complexe elementen gevonden ({', '.join(sorted(complexiteit_gevonden))}), "
                    f"en definitie lijkt op fout voorbeeld"
                ),
                0.0,
            )
        # Bereken score op basis van aantal complexiteits-indicatoren
        score = max(0.0, 1.0 - (len(complexiteit_gevonden) * 0.2))
        return (
            False,
            (
                f"❌ {self.id}: complexe elementen gevonden ({', '.join(sorted(complexiteit_gevonden))}), "
                f"maar geen expliciet fout voorbeeld herkend"
            ),
            score,
        )

    def get_generation_hints(self) -> list[str]:
        """
        Geef hints voor definitie generatie.

        Returns:
            Lijst met instructies voor de AI generator
        """
        hints = []

        hints.append("Formuleer de definitie in één enkele, heldere zin")
        hints.append("Vermijd complexe bijzinnen en opsommingen")
        hints.append("Gebruik geen puntkomma's of meerdere komma's")
        hints.append("Vermijd woorden zoals 'waarbij', 'welke', 'alsmede', 'indien'")

        if self.goede_voorbeelden:
            hints.append(f"Goed voorbeeld: {self.goede_voorbeelden[0]}")

        return hints


def create_validator(config_path: str | None = None) -> INT01Validator:
    """
    Factory functie om validator te maken.

    Args:
        config_path: Optioneel pad naar configuratie bestand

    Returns:
        INT01Validator instantie
    """
    import json
    import os

    # Gebruik default config path als niet opgegeven
    if not config_path:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "INT-01.json")

    # Laad configuratie
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    return INT01Validator(config)
