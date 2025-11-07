"""
Output Format Module - Combineert output specificaties en templates.

Deze module consolideert output formatting, templates, en structuur instructies
in één module om cognitive load te verminderen (DEF-127).

Vervangt:
- output_specification_module.py
- template_module.py
"""

import logging
from typing import Any

from .base_module import BasePromptModule, ModuleContext, ModuleOutput

logger = logging.getLogger(__name__)


class OutputFormatModule(BasePromptModule):
    """
    Geconsolideerde module voor output formatting, templates en structuur.

    Combineert output specificaties met definitie templates om het aantal
    modules te verminderen (DEF-127).
    """

    # Categorie-specifieke templates
    CATEGORY_TEMPLATES = {
        "object": {
            "template": "Een [term] is een [categorie] dat/die [essentiële kenmerken].",
            "example": "Een overeenkomst is een meerzijdige rechtshandeling waarbij partijen jegens elkaar verbintenissen aangaan.",
            "focus": "essentiële kenmerken en onderscheidende eigenschappen",
        },
        "actor": {
            "template": "Een [term] is een [rol/functie] die [kerntaken/verantwoordelijkheden].",
            "example": "Een werkgever is een natuurlijke of rechtspersoon die op basis van een arbeidsovereenkomst arbeid laat verrichten.",
            "focus": "rol, taken, en verantwoordelijkheden",
        },
        "proces": {
            "template": "[Term] is het [type proces] waarbij [wat gebeurt er] [met welk doel].",
            "example": "Arbitrage is het beslechten van een geschil door een onafhankelijke derde op basis van een arbitrageovereenkomst.",
            "focus": "procesverloop, doel, en resultaat",
        },
        "toestand": {
            "template": "[Term] is de [type toestand] waarin/waarbij [beschrijving situatie].",
            "example": "Faillissement is de toestand waarin een schuldenaar verkeert die heeft opgehouden te betalen.",
            "focus": "kenmerken van de toestand en voorwaarden",
        },
        "gebeurtenis": {
            "template": "[Term] is een [type gebeurtenis] waarbij [wat gebeurt] [onder welke omstandigheden].",
            "example": "Een ongeval is een plotselinge, onverwachte gebeurtenis waarbij schade ontstaat.",
            "focus": "aard van gebeurtenis, omstandigheden, en gevolgen",
        },
    }

    def __init__(self):
        """Initialize de output format module."""
        super().__init__(
            module_id="output_format",
            module_name="Output Format & Templates",
            priority=30,  # Lagere prioriteit - formatting komt later
        )
        self.include_templates = True
        self.strict_format = True
        self.char_limit_warning = 500

    def initialize(self, config: dict[str, Any]) -> None:
        """
        Initialize module met configuratie.

        Args:
            config: Module configuratie
        """
        self._config = config
        self.include_templates = config.get("include_templates", True)
        self.strict_format = config.get("strict_format", True)
        self.char_limit_warning = config.get("char_limit_warning", 500)
        self._initialized = True
        logger.debug(
            f"OutputFormatModule initialized (templates={self.include_templates})"
        )

    def validate_input(self, context: ModuleContext) -> tuple[bool, str | None]:
        """Output formatting draait altijd."""
        return True, None

    def execute(self, context: ModuleContext) -> ModuleOutput:
        """
        Genereer output format specificaties en templates.

        Returns:
            ModuleOutput met formatting instructies
        """
        try:
            sections = []
            sections.append("## 📋 Output Formaat & Structuur\n")

            # Section 1: Basis output specificaties
            sections.extend(self._generate_output_specifications(context))

            # Section 2: Templates (indien enabled)
            if self.include_templates:
                sections.extend(self._generate_templates(context))

            # Section 3: Structuur richtlijnen
            sections.extend(self._generate_structure_guidelines())

            # Section 4: Lengte limieten
            sections.extend(self._generate_length_limits())

            # Section 5: Output format instructies
            if self.strict_format:
                sections.extend(self._generate_format_instructions())

            # Combine all sections
            content = "\n".join(sections)

            return ModuleOutput(
                content=content,
                metadata={
                    "include_templates": self.include_templates,
                    "strict_format": self.strict_format,
                    "char_limit": self.char_limit_warning,
                },
            )

        except Exception as e:
            logger.error(f"Error generating output format: {e}")
            return ModuleOutput(content="", metadata={"error": str(e)})

    def get_dependencies(self) -> list[str]:
        """Deze module heeft geen dependencies."""
        return []

    def _generate_output_specifications(self, context: ModuleContext) -> list[str]:
        """Genereer basis output specificaties."""
        lines = []
        lines.append("\n### 📝 Output Specificaties\n")

        specs = [
            "**Formaat**: Eén complete definitiezin",
            "**Structuur**: [Term] is [genus] [differentia]",
            "**Taal**: Helder juridisch Nederlands",
            "**Lengte**: Bij voorkeur 50-150 woorden",
            "**Stijl**: Formeel maar toegankelijk",
        ]

        for spec in specs:
            lines.append(f"- {spec}")

        return lines

    def _generate_templates(self, context: ModuleContext) -> list[str]:
        """Genereer categorie-specifieke templates."""
        lines = []
        lines.append("\n### 🎯 Definitie Templates\n")

        # Check of we een specifieke categorie hebben in context
        category = None
        if context and context.variables:
            category = context.variables.get("ontological_category")

        if category and category in self.CATEGORY_TEMPLATES:
            # Specifiek template voor deze categorie
            template_info = self.CATEGORY_TEMPLATES[category]
            lines.append(f"**Categorie: {category.title()}**\n")
            lines.append(f"**Template**: {template_info['template']}")
            lines.append(f"**Voorbeeld**: {template_info['example']}")
            lines.append(f"**Focus**: {template_info['focus']}")

        else:
            # Toon alle templates als referentie
            lines.append("**Gebruik het juiste template voor de categorie:**\n")
            for cat, info in self.CATEGORY_TEMPLATES.items():
                lines.append(f"**{cat.title()}**:")
                lines.append(f"- Template: {info['template']}")
                lines.append(f"- Focus: {info['focus']}")
                lines.append("")

        return lines

    def _generate_structure_guidelines(self) -> list[str]:
        """Genereer structuur richtlijnen."""
        lines = []
        lines.append("\n### 🏗️ Definitie Structuur\n")

        guidelines = [
            "**Opening**: Begin direct met de term (geen 'Een' ervoor tenzij grammaticaal nodig)",
            "**Genus**: Plaats de term in een bredere categorie",
            "**Differentia**: Geef onderscheidende kenmerken",
            "**Volgorde**: Van algemeen naar specifiek",
            "**Afsluiting**: Rond af met relevante context indien nodig",
        ]

        for guideline in guidelines:
            lines.append(f"- {guideline}")

        return lines

    def _generate_length_limits(self) -> list[str]:
        """Genereer lengte limieten en waarschuwingen."""
        lines = []
        lines.append("\n### 📏 Lengte Richtlijnen\n")

        lines.append(
            f"⚠️ **Karakterlimiet**: Maximaal {self.char_limit_warning} karakters"
        )
        lines.append("")
        lines.append("**Ideale lengtes:**")
        lines.append("- Simpele begrippen: 50-100 woorden")
        lines.append("- Complexe begrippen: 100-150 woorden")
        lines.append("- Zeer complexe begrippen: max 200 woorden")
        lines.append("")
        lines.append("**Let op**: Prioriteer helderheid boven beknoptheid")

        return lines

    def _generate_format_instructions(self) -> list[str]:
        """Genereer strikte format instructies."""
        lines = []
        lines.append("\n### ⚡ Verplicht Output Formaat\n")

        lines.append("**Output MOET bevatten:**")
        lines.append("1. Eén enkele definitiezin (geen bullet points)")
        lines.append("2. Geen metadata of extra uitleg")
        lines.append("3. Geen voorbeelden in de definitie zelf")
        lines.append("4. Geen verwijzingen naar deze instructies")
        lines.append("5. Alleen de definitie, niets anders")

        lines.append("\n**Definitie begint direct met:**")
        lines.append("- De term zelf (bv: 'Overeenkomst is...')")
        lines.append("- OF 'Een/Het [term] is...' waar grammaticaal vereist")

        return lines
