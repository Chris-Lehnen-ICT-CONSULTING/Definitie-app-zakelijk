"""
Toetsregel INT-08: Positieve formulering

Een definitie wordt in principe positief geformuleerd, dus zonder ontkenningen te gebruiken.
Gemigreerd van legacy core.py
"""

import logging
import re

logger = logging.getLogger(__name__)


class INT08Validator:
    """Validator voor INT-08: Positieve formulering."""

    def __init__(self, config: dict):
        """
        Initialiseer validator met configuratie uit JSON.

        Args:
            config: Dictionary met configuratie uit INT-08.json
        """
        self.config = config
        self.id = config.get("id", "INT-08")
        self.naam = config.get("naam", "Positieve formulering")
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
        self, definitie: str, begrip: str, context: dict | None = None
    ) -> tuple[bool, str, float]:
        """
        Valideer definitie volgens INT-08 regel.

        Een definitie wordt in principe positief geformuleerd (geen ontkenningen),
        met uitzondering van specificerende onderdelen (bijv. relatieve bijzinnen).

        Args:
            definitie: De te valideren definitie
            begrip: Het begrip dat gedefinieerd wordt
            context: Optionele context informatie

        Returns:
            Tuple van (succes, melding, score)
        """
        # 1️⃣ Vind alle negatieve patronen
        gevonden = []
        for pattern in self.compiled_patterns:
            gevonden.extend(pattern.findall(definitie))
        negatieve_vormen = {v.lower() for v in gevonden}

        # 2️⃣ Detecteer allowed negaties in specificerende context (relatieve bijzin)
        allowed = set()
        for neg in list(negatieve_vormen):
            patroon_context = rf"\bdie\b.*\b{re.escape(neg)}\b"
            if re.search(patroon_context, definitie, re.IGNORECASE):
                allowed.add(neg)

        # 3️⃣ Bepaal disallowed negaties
        disallowed = sorted(nv for nv in negatieve_vormen if nv not in allowed)

        # 4️⃣ Check voorbeelden
        goede = [vb.lower() for vb in self.goede_voorbeelden]
        fout = [vb.lower() for vb in self.foute_voorbeelden]
        uitleg_aanwezig = any(v in definitie.lower() for v in goede)
        fout_aanwezig = any(v in definitie.lower() for v in fout)

        # 5️⃣ Formuleer resultaat
        if not disallowed:
            if allowed:
                return (
                    True,
                    (
                        f"✅ {self.id}: alleen toegestane negatieve termen "
                        f"({', '.join(allowed)}) in specificerende context"
                    ),
                    1.0,
                )
            if uitleg_aanwezig:
                return (
                    True,
                    f"✅ {self.id}: geen negatieve formuleringen en komt overeen met goed voorbeeld",
                    1.0,
                )
            return (
                True,
                f"✅ {self.id}: definitie bevat geen negatieve formuleringen",
                1.0,
            )

        # Er zijn disallowed negaties
        if uitleg_aanwezig:
            return (
                True,
                (
                    f"✅ {self.id}: negatieve termen ({', '.join(disallowed)}) gevonden, "
                    "maar correct geformuleerd volgens goed voorbeeld"
                ),
                0.8,
            )

        if fout_aanwezig:
            return (
                False,
                (
                    f"❌ {self.id}: negatieve termen ({', '.join(disallowed)}) gevonden, "
                    "lijkt op fout voorbeeld"
                ),
                0.0,
            )

        return (
            False,
            (
                f"❌ {self.id}: negatieve termen ({', '.join(disallowed)}) gevonden, "
                "zonder duidelijke uitleg"
            ),
            0.0,
        )

    def get_generation_hints(self) -> list[str]:
        """
        Geef hints voor definitie generatie.

        Returns:
            Lijst met instructies voor de AI generator
        """
        hints = []

        hints.append("Formuleer positief: zeg wat iets WEL is, niet wat het NIET is")
        hints.append("Vermijd woorden zoals: niet, geen, zonder, uitgezonderd")
        hints.append("Uitzondering: in relatieve bijzinnen ('die niet...') mag het wel")
        hints.append("Gebruik actieve, bevestigende taal")

        return hints


def create_validator(config_path: str = None) -> INT08Validator:
    """
    Factory functie om validator te maken.

    Args:
        config_path: Optioneel pad naar configuratie bestand

    Returns:
        INT08Validator instantie
    """
    import json
    import os

    # Gebruik default config path als niet opgegeven
    if not config_path:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "INT-08.json")

    # Laad configuratie
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    return INT08Validator(config)
