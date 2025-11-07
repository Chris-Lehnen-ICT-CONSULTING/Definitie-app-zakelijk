"""
Linguistic Rules Module - Combineert alle taalkundige en grammaticale regels.

Deze module consolideert grammatica, structuur (STR), en vorm (VER) regels
in één module om cognitive load te verminderen (DEF-127).

Vervangt:
- grammar_module.py
- structure_rules_module.py (STR regels)
- ver_rules_module.py (VER regels)
"""

import logging
from typing import Any

from .base_module import BasePromptModule, ModuleContext, ModuleOutput

logger = logging.getLogger(__name__)


class LinguisticRulesModule(BasePromptModule):
    """
    Geconsolideerde module voor alle linguïstische en grammaticale regels.

    Combineert grammatica instructies met STR (structuur) en VER (vorm)
    validatie regels om het aantal modules te verminderen (DEF-127).
    """

    def __init__(self):
        """Initialize de linguistic rules module."""
        super().__init__(
            module_id="linguistic_rules",
            module_name="Linguistic & Grammar Rules",
            priority=60,  # Medium-hoge prioriteit
        )
        self.include_examples = True
        self.extended_grammar = True

    def initialize(self, config: dict[str, Any]) -> None:
        """
        Initialize module met configuratie.

        Args:
            config: Module configuratie
        """
        self._config = config
        self.include_examples = config.get("include_examples", True)
        self.extended_grammar = config.get("extended_grammar", True)
        self._initialized = True
        logger.debug(
            f"LinguisticRulesModule initialized (examples={self.include_examples})"
        )

    def validate_input(self, context: ModuleContext) -> tuple[bool, str | None]:
        """Linguïstische regels draaien altijd."""
        return True, None

    def execute(self, context: ModuleContext) -> ModuleOutput:
        """
        Genereer alle linguïstische en grammaticale regels.

        Returns:
            ModuleOutput met gecombineerde taalregels
        """
        try:
            sections = []
            sections.append("## 📝 Taalkundige & Grammaticale Richtlijnen\n")

            # Section 1: Algemene grammatica regels
            sections.extend(self._generate_grammar_rules())

            # Section 2: STR (Structuur) regels
            sections.extend(self._generate_structure_rules())

            # Section 3: VER (Vorm) regels
            sections.extend(self._generate_form_rules())

            # Section 4: Schrijfstijl richtlijnen
            if self.extended_grammar:
                sections.extend(self._generate_style_guidelines())

            # Combine all sections
            content = "\n".join(sections)

            return ModuleOutput(
                content=content,
                metadata={
                    "include_examples": self.include_examples,
                    "extended_grammar": self.extended_grammar,
                },
            )

        except Exception as e:
            logger.error(f"Error generating linguistic rules: {e}")
            return ModuleOutput(content="", metadata={"error": str(e)})

    def get_dependencies(self) -> list[str]:
        """Deze module heeft geen dependencies."""
        return []

    def _generate_grammar_rules(self) -> list[str]:
        """Genereer algemene grammatica regels."""
        lines = []
        lines.append("\n### 🔤 Grammatica Basisregels\n")

        grammar_rules = [
            "**Enkelvoud**: Definities altijd in enkelvoud formuleren",
            "**Tegenwoordige tijd**: Gebruik tegenwoordige tijd, geen verleden of toekomst",
            "**Actieve vorm**: Vermijd passieve constructies waar mogelijk",
            "**Geen aanhalingstekens**: Term niet tussen aanhalingstekens in definitie",
            "**Lidwoorden**: Correct gebruik van 'de' en 'het'",
            "**Werkwoordsvorm**: Begin met zelfstandig naamwoord of werkwoord",
        ]

        for rule in grammar_rules:
            lines.append(f"- {rule}")

        if self.include_examples:
            lines.append("\n**Voorbeelden:**")
            lines.append("✓ Goed: 'Een overeenkomst is een wilsovereenstemming...'")
            lines.append("✗ Fout: 'Overeenkomsten zijn wilsovereenstemmingen...'")

        return lines

    def _generate_structure_rules(self) -> list[str]:
        """Genereer STR (structuur) validatie regels."""
        lines = []
        lines.append("\n### 🏗️ Structuur Regels (STR)\n")

        try:
            # Load STR rules from toetsregels
            from toetsregels.cached_manager import get_cached_toetsregel_manager

            manager = get_cached_toetsregel_manager()

            # Get all STR rules
            for i in range(1, 10):  # Assuming max 9 STR rules
                regel_key = f"STR-{i:02d}"
                regel = manager.load_regel(regel_key)
                if regel:
                    lines.extend(self._format_validation_rule(regel_key, regel))
                    lines.append("")

        except Exception as e:
            logger.error(f"Error loading STR rules: {e}")
            # Fallback to basic structure rules
            lines.append("- Definitie moet grammaticaal correct zijn")
            lines.append("- Heldere zinsbouw zonder onnodige complexiteit")
            lines.append("- Logische opbouw van algemeen naar specifiek")

        return lines

    def _generate_form_rules(self) -> list[str]:
        """Genereer VER (vorm) validatie regels."""
        lines = []
        lines.append("\n### 📐 Vorm Regels (VER)\n")

        try:
            # Load VER rules from toetsregels
            from toetsregels.cached_manager import get_cached_toetsregel_manager

            manager = get_cached_toetsregel_manager()

            # Get all VER rules
            for i in range(1, 10):  # Assuming max 9 VER rules
                regel_key = f"VER-{i:02d}"
                regel = manager.load_regel(regel_key)
                if regel:
                    lines.extend(self._format_validation_rule(regel_key, regel))
                    lines.append("")

        except Exception as e:
            logger.error(f"Error loading VER rules: {e}")
            # Fallback to basic form rules
            lines.append("- Correcte grammaticale vorm van termen")
            lines.append("- Consistente schrijfwijze door hele definitie")
            lines.append("- Juiste woordvolgorde in Nederlandse zinnen")

        return lines

    def _generate_style_guidelines(self) -> list[str]:
        """Genereer uitgebreide schrijfstijl richtlijnen."""
        lines = []
        lines.append("\n### ✍️ Schrijfstijl Richtlijnen\n")

        style_guidelines = [
            "**Helder Nederlands**: Gebruik toegankelijke, juridisch correcte taal",
            "**Vermijd jargon**: Alleen vakjargon gebruiken waar noodzakelijk",
            "**Korte zinnen**: Bij voorkeur max 25 woorden per zin",
            "**Eenduidige termen**: Gebruik consistente terminologie",
            "**Logische flow**: Van algemeen naar specifiek",
            "**Precisie**: Wees exact zonder overbodig detail",
        ]

        for guideline in style_guidelines:
            lines.append(f"- {guideline}")

        return lines

    def _format_validation_rule(self, regel_key: str, regel_data: dict) -> list[str]:
        """
        Formatteer een validatie regel.

        Args:
            regel_key: Regel identifier
            regel_data: Regel data dictionary

        Returns:
            Lijst van geformatteerde regels
        """
        lines = []

        # Header
        naam = regel_data.get("naam", "Onbekende regel")
        lines.append(f"**{regel_key}** - {naam}")

        # Beschrijving
        if beschrijving := regel_data.get("beschrijving"):
            lines.append(f"  {beschrijving}")

        # AI instructies
        if instructies := regel_data.get("ai_instructies"):
            if isinstance(instructies, list):
                for instructie in instructies[:2]:  # Limit to 2 instructions
                    lines.append(f"  • {instructie}")
            else:
                lines.append(f"  • {instructies}")

        # Voorbeelden (indien enabled en aanwezig)
        if self.include_examples and (voorbeelden := regel_data.get("voorbeelden")):
            if goed := voorbeelden.get("goed"):
                example = goed[0] if isinstance(goed, list) else goed
                lines.append(f"  ✓ {example}")

        return lines
