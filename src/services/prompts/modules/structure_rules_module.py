"""
Structure Rules Module - Implementeert STR validatieregels voor definities.

Deze module is verantwoordelijk voor:
1. Alle STR (Structuur) validatieregels
2. Grammaticale structuur validatie
3. Definitie opbouw regels
"""

import logging
from typing import Any

from .base_module import BasePromptModule, ModuleContext, ModuleOutput

logger = logging.getLogger(__name__)


class StructureRulesModule(BasePromptModule):
    """
    Module voor structuur validatieregels (STR).

    Genereert alle STR regels die de grammaticale en structurele
    opbouw van definities valideren.
    """

    def __init__(self):
        """Initialize de structure rules module."""
        super().__init__(
            module_id="structure_rules",
            module_name="Structure Validation Rules (STR)",
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
            f"StructureRulesModule geïnitialiseerd (examples={self.include_examples})"
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
        Genereer STR validatieregels.

        Args:
            context: Module context

        Returns:
            ModuleOutput met STR regels
        """
        try:
            # Bouw de STR regels sectie
            sections = []

            # Header
            sections.append("### 🏗️ Structuur Regels (STR):")
            sections.append("")

            # STR-01: Start met zelfstandig naamwoord
            sections.extend(self._build_str01_rule())

            # STR-02: Kick-off ≠ de term
            sections.extend(self._build_str02_rule())

            # STR-03: Definitie ≠ synoniem
            sections.extend(self._build_str03_rule())

            # STR-04: Kick-off vervolgen met toespitsing
            sections.extend(self._build_str04_rule())

            # STR-05: Definitie ≠ constructie
            sections.extend(self._build_str05_rule())

            # STR-06: Essentie ≠ informatiebehoefte
            sections.extend(self._build_str06_rule())

            # STR-07: Geen dubbele ontkenning
            sections.extend(self._build_str07_rule())

            # STR-08: Dubbelzinnige 'en' is verboden
            sections.extend(self._build_str08_rule())

            # STR-09: Dubbelzinnige 'of' is verboden
            sections.extend(self._build_str09_rule())

            # Combineer secties
            content = "\n".join(sections)

            return ModuleOutput(
                content=content,
                metadata={"rules_count": 9, "include_examples": self.include_examples},
            )

        except Exception as e:
            logger.error(f"StructureRulesModule execution failed: {e}", exc_info=True)
            return ModuleOutput(
                content="",
                metadata={"error": str(e)},
                success=False,
                error_message=f"Failed to generate structure rules: {e!s}",
            )

    def get_dependencies(self) -> list[str]:
        """
        Deze module heeft geen dependencies.

        Returns:
            Lege lijst
        """
        return []

    def _build_str01_rule(self) -> list[str]:
        """Bouw STR-01 regel."""
        rules = []

        rules.append("🔹 **STR-01 - Start met zelfstandig naamwoord**")
        rules.append(
            "- Start met een zelfstandig naamwoord of naamwoordgroep, niet met een werkwoord."
        )
        rules.append(
            "- Handelingsnaamwoorden ('activiteit', 'proces', 'handeling') zijn zelfstandige naamwoorden."
        )

        if self.include_examples:
            rules.append("  ✅ proces dat beslissers identificeert...")
            rules.append("  ✅ maatregel die recidive voorkomt...")
            rules.append("  ❌ is een maatregel die recidive voorkomt")
            rules.append("  ❌ wordt toegepast in het gevangeniswezen")

        rules.append("")
        return rules

    def _build_str02_rule(self) -> list[str]:
        """Bouw STR-02 regel."""
        rules = []

        rules.append("🔹 **STR-02 - Begin met genus + specificatie**")
        rules.append(
            "- Begin met een breder begrip (genus) en specificeer vervolgens de verbijzondering."
        )

        if self.include_examples:
            rules.append("  ✅ analist: professional verantwoordelijk voor …")
            rules.append("  ❌ analist: analist die verantwoordelijk is voor …")

        rules.append("")
        return rules

    def _build_str03_rule(self) -> list[str]:
        """Bouw STR-03 regel."""
        rules = []

        rules.append("🔹 **STR-03 - Geef volledige definitie**")
        rules.append(
            "- Geef een volledige definitie, niet alleen een synoniem van de term."
        )

        if self.include_examples:
            rules.append(
                "  ✅ evaluatie: resultaat van iets beoordelen, appreciëren of interpreteren"
            )
            rules.append("  ❌ evaluatie: beoordeling")
            rules.append("  ❌ registratie: vastlegging (in een systeem)")

        rules.append("")
        return rules

    def _build_str04_rule(self) -> list[str]:
        """Bouw STR-04 regel."""
        rules = []

        rules.append("🔹 **STR-04 - Volg opening met toespitsing**")
        rules.append(
            "- Volg de algemene opening direct met een toespitsing op het specifieke begrip."
        )

        if self.include_examples:
            rules.append("  ✅ proces dat beslissers informeert")
            rules.append("  ✅ gegeven over de verblijfplaats van een betrokkene")
            rules.append("  ❌ proces")
            rules.append("  ❌ gegeven")
            rules.append("  ❌ activiteit die plaatsvindt")

        rules.append("")
        return rules

    def _build_str05_rule(self) -> list[str]:
        """Bouw STR-05 regel."""
        rules = []

        rules.append("🔹 **STR-05 - Beschrijf essentie, niet constructie**")
        rules.append(
            "- Beschrijf wat het begrip is, niet uit welke onderdelen het bestaat."
        )

        if self.include_examples:
            rules.append(
                "  ✅ motorvoertuig: gemotoriseerd voertuig dat niet over rails rijdt, zoals auto's, vrachtwagens en bussen"
            )
            rules.append(
                "  ❌ motorvoertuig: een voertuig met een chassis, vier wielen en een motor van meer dan 50 cc"
            )

        rules.append("")
        return rules

    def _build_str06_rule(self) -> list[str]:
        """Bouw STR-06 regel."""
        rules = []

        rules.append("🔹 **STR-06 - Beschrijf aard, niet doel**")
        rules.append(
            "- Beschrijf de aard van het begrip, niet de reden waarom het nodig is."
        )

        if self.include_examples:
            rules.append(
                "  ✅ beveiligingsmaatregel: voorziening die ongeautoriseerde toegang voorkomt"
            )
            rules.append(
                "  ❌ beveiligingsmaatregel: voorziening om ongeautoriseerde toegang te voorkomen"
            )

        rules.append("")
        return rules

    def _build_str07_rule(self) -> list[str]:
        """Bouw STR-07 regel."""
        rules = []

        rules.append("🔹 **STR-07 - Vermijd dubbele ontkenning**")
        rules.append(
            "- Vermijd dubbele ontkenningen (zoals 'niet onmogelijk', 'niet zonder')."
        )

        if self.include_examples:
            rules.append(
                "  ✅ Beveiliging: maatregelen die toegang beperken tot bevoegde personen"
            )
            rules.append(
                "  ❌ Beveiliging: maatregelen die het niet onmogelijk maken om geen toegang te verkrijgen"
            )

        rules.append("")
        return rules

    def _build_str08_rule(self) -> list[str]:
        """Bouw STR-08 regel."""
        rules = []

        rules.append("🔹 **STR-08 - Gebruik 'en' ondubbelzinnig**")
        rules.append(
            "- Gebruik 'en' ondubbelzinnig: maak expliciet of beide elementen vereist zijn."
        )

        if self.include_examples:
            rules.append(
                "  ✅ Toegang is beperkt tot personen met een geldig toegangspasje en een schriftelijke toestemming"
            )
            rules.append(
                "  ❌ Toegang is beperkt tot personen met een pasje en toestemming"
            )
            rules.append("  ❌ Het systeem vereist login en verificatie")

        rules.append("")
        return rules

    def _build_str09_rule(self) -> list[str]:
        """Bouw STR-09 regel."""
        rules = []

        rules.append("🔹 **STR-09 - Gebruik 'of' ondubbelzinnig**")
        rules.append(
            "- Gebruik 'of' ondubbelzinnig: maak expliciet of het inclusief of exclusief is."
        )

        if self.include_examples:
            rules.append(
                "  ✅ Een persoon met een paspoort of, indien niet beschikbaar, een identiteitskaart"
            )
            rules.append("  ❌ Een persoon met een paspoort of identiteitskaart")
            rules.append(
                "  ❌ Een verdachte is iemand die een misdrijf beraamt of uitvoert"
            )

        rules.append("")
        return rules
