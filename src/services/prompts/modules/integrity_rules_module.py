"""
Integrity Rules Module - Implementeert INT validatieregels voor definities.

Deze module is verantwoordelijk voor:
1. Alle INT (Integriteit) validatieregels
2. Definitie integriteit en compleetheid
3. Formulering kwaliteit regels
"""

import logging
from typing import Any

from .base_module import BasePromptModule, ModuleContext, ModuleOutput

logger = logging.getLogger(__name__)


class IntegrityRulesModule(BasePromptModule):
    """
    Module voor integriteit validatieregels (INT).

    Genereert alle INT regels die de integriteit en compleetheid
    van definities valideren.
    """

    def __init__(self):
        """Initialize de integrity rules module."""
        super().__init__(
            module_id="integrity_rules",
            module_name="Integrity Validation Rules (INT)",
            priority=65,  # Medium-hoge prioriteit
        )
        self.include_examples = True

    def initialize(self, config: dict[str, Any]) -> None:
        """
        Initialize module met configuratie.

        Args:
            config: Module configuratie
        """
        self._config = config
        self.include_examples = config.get("include_examples", True)
        self._initialized = True
        logger.debug(
            f"IntegrityRulesModule geïnitialiseerd (examples={self.include_examples})"
        )

    def validate_input(self, context: ModuleContext) -> tuple[bool, str | None]:
        """
        Deze module draait altijd.

        Args:
            context: Module context

        Returns:
            Altijd (True, None)
        """
        return True, None

    def execute(self, context: ModuleContext) -> ModuleOutput:
        """
        Genereer INT validatieregels.

        Args:
            context: Module context

        Returns:
            ModuleOutput met INT regels
        """
        try:
            # Bouw de INT regels sectie
            sections = []

            # Header
            sections.append("### 🔒 Integriteit Regels (INT):")
            sections.append("")

            # INT-01: Compacte en begrijpelijke zin
            sections.extend(self._build_int01_rule())

            # INT-02: Geen beslisregel
            sections.extend(self._build_int02_rule())

            # INT-03: Voornaamwoord-verwijzing duidelijk
            sections.extend(self._build_int03_rule())

            # INT-04: Lidwoord-verwijzing duidelijk
            sections.extend(self._build_int04_rule())

            # INT-06: Definitie bevat geen toelichting
            sections.extend(self._build_int06_rule())

            # INT-07: Alleen toegankelijke afkortingen
            sections.extend(self._build_int07_rule())

            # INT-08: Positieve formulering
            sections.extend(self._build_int08_rule())

            # Combineer secties
            content = "\n".join(sections)

            return ModuleOutput(
                content=content,
                metadata={"rules_count": 7, "include_examples": self.include_examples},
            )

        except Exception as e:
            logger.error(f"IntegrityRulesModule execution failed: {e}", exc_info=True)
            return ModuleOutput(
                content="",
                metadata={"error": str(e)},
                success=False,
                error_message=f"Failed to generate integrity rules: {e!s}",
            )

    def get_dependencies(self) -> list[str]:
        """
        Deze module heeft geen dependencies.

        Returns:
            Lege lijst
        """
        return []

    def _build_int01_rule(self) -> list[str]:
        """Bouw INT-01 regel."""
        rules = []

        rules.append("🔹 **INT-01 - Formuleer compact in één zin**")
        rules.append("- Formuleer compact en in één enkele, begrijpelijke zin.")

        if self.include_examples:
            rules.append(
                "  ✅ transitie-eis: eis die een organisatie moet ondersteunen om migratie van de huidige naar de toekomstige situatie mogelijk te maken"
            )
            rules.append(
                "  ❌ transitie-eis: eis die een organisatie moet ondersteunen om migratie van de huidige naar de toekomstige situatie mogelijk te maken. In tegenstelling tot andere eisen vertegenwoordigen transitie-eisen tijdelijke behoeften, in plaats van meer permanente."
            )

        rules.append("")
        return rules

    def _build_int02_rule(self) -> list[str]:
        """Bouw INT-02 regel."""
        rules = []

        rules.append("🔹 **INT-02 - Vermijd beslisregels**")
        rules.append(
            "- Vermijd beslisregels of voorwaarden ('indien', 'mits', 'tenzij', 'alleen als')."
        )

        if self.include_examples:
            rules.append(
                "  ✅ transitie-eis: eis die een organisatie ondersteunt om migratie van de huidige naar de toekomstige situatie mogelijk te maken"
            )
            rules.append(
                "  ✅ Toegang: toestemming verleend door een bevoegde autoriteit om een systeem te gebruiken"
            )
            rules.append(
                "  ✅ Beschikking: schriftelijk besluit genomen door een bevoegde autoriteit"
            )
            rules.append(
                "  ✅ Register: officiële inschrijving in een openbaar register door een bevoegde instantie"
            )
            rules.append(
                "  ❌ transitie-eis: eis die een organisatie moet ondersteunen om migratie van de huidige naar de toekomstige situatie mogelijk te maken"
            )
            rules.append(
                "  ❌ Toegang: toestemming verleend door een bevoegde autoriteit, indien alle voorwaarden zijn vervuld"
            )
            rules.append(
                "  ❌ Beschikking: schriftelijk besluit, mits de aanvraag compleet is ingediend"
            )
            rules.append(
                "  ❌ Register: officiële inschrijving in een openbaar register, tenzij er bezwaar ligt"
            )

        rules.append("")
        return rules

    def _build_int03_rule(self) -> list[str]:
        """Bouw INT-03 regel."""
        rules = []

        rules.append("🔹 **INT-03 - Zorg voor duidelijke voornaamwoord-verwijzing**")
        rules.append(
            "- Zorg dat voornaamwoorden ('deze', 'dit', 'die') direct verwijzen naar een duidelijk antecedent in dezelfde zin."
        )

        if self.include_examples:
            rules.append(
                "  ✅ Geheel van omstandigheden die de omgeving van een gebeurtenis vormen en die de basis vormen waardoor die gebeurtenis volledig kan worden begrepen en geanalyseerd"
            )
            rules.append(
                "  ✅ Voorwaarde: bepaling die aangeeft onder welke omstandigheden een handeling is toegestaan"
            )
            rules.append(
                "  ❌ Geheel van omstandigheden die de omgeving van een gebeurtenis vormen en die de basis vormen waardoor het volledig kan worden begrepen en geanalyseerd"
            )
            rules.append(
                "  ❌ Voorwaarde: bepaling die aangeeft onder welke omstandigheden deze geldt"
            )

        rules.append("")
        return rules

    def _build_int04_rule(self) -> list[str]:
        """Bouw INT-04 regel."""
        rules = []

        rules.append("🔹 **INT-04 - Maak lidwoord-verwijzingen expliciet**")
        rules.append(
            "- Maak bepaalde lidwoorden ('de instelling', 'het systeem') expliciet door te specificeren welke bedoeld wordt."
        )

        if self.include_examples:
            rules.append(
                "  ✅ Een instelling (de Raad voor de Rechtspraak) neemt beslissingen binnen het strafrechtelijk systeem"
            )
            rules.append(
                "  ✅ Het systeem (Reclasseringsapplicatie) voert controles automatisch uit"
            )
            rules.append(
                "  ❌ De instelling neemt beslissingen binnen het strafrechtelijk systeem"
            )
            rules.append(
                "  ❌ Het systeem voert controles uit zonder verdere specificatie"
            )

        rules.append("")
        return rules

    def _build_int06_rule(self) -> list[str]:
        """Bouw INT-06 regel."""
        rules = []

        rules.append("🔹 **INT-06 - Vermijd toelichtingen**")
        rules.append(
            "- Vermijd toelichtingen of voorbeelden ('bijvoorbeeld', 'zoals', 'namelijk'); geef alleen de afbakening."
        )

        if self.include_examples:
            rules.append("  ✅ model: vereenvoudigde weergave van de werkelijkheid")
            rules.append(
                "  ❌ model: vereenvoudigde weergave van de werkelijkheid, die visueel wordt weergegeven"
            )

        rules.append("")
        return rules

    def _build_int07_rule(self) -> list[str]:
        """Bouw INT-07 regel."""
        rules = []

        rules.append("🔹 **INT-07 - Licht afkortingen toe**")
        rules.append(
            "- Licht afkortingen direct toe in dezelfde zin (bijv. DJI (Dienst Justitiële Inrichtingen))."
        )

        if self.include_examples:
            rules.append("  ✅ Dienst Justitiële Inrichtingen (DJI)")
            rules.append("  ✅ OM (Openbaar Ministerie)")
            rules.append("  ✅ AVG (Algemene verordening gegevensbescherming)")
            rules.append("  ✅ KvK (Kamer van Koophandel)")
            rules.append("  ✅ [[Algemene verordening gegevensbescherming]]")
            rules.append("  ❌ DJI voert toezicht uit")
            rules.append("  ❌ De AVG vereist naleving")
            rules.append("  ❌ OM is bevoegd tot vervolging")
            rules.append("  ❌ KvK registreert bedrijven")

        rules.append("")
        return rules

    def _build_int08_rule(self) -> list[str]:
        """Bouw INT-08 regel."""
        rules = []

        rules.append("🔹 **INT-08 - Formuleer positief**")
        rules.append(
            "- Formuleer positief (wat iets wél is), niet negatief (wat iets niet is)."
        )

        if self.include_examples:
            rules.append(
                "  ✅ bevoegd persoon: medewerker met formele autorisatie om gegevens in te zien"
            )
            rules.append("  ✅ gevangene: persoon die zich niet vrij kan bewegen")
            rules.append("  ❌ bevoegd persoon: iemand die niet onbevoegd is")
            rules.append(
                "  ❌ toegang: mogelijkheid om een ruimte te betreden, uitgezonderd voor onbevoegden"
            )

        rules.append("")
        return rules
