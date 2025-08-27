"""
Template Module - Biedt definitie templates per categorie.

Deze module is verantwoordelijk voor:
1. Context-specifieke definitie templates
2. Categorie-gebaseerde voorbeelden
3. Patroon suggesties
"""

import logging
from typing import Any

from .base_module import BasePromptModule, ModuleContext, ModuleOutput

logger = logging.getLogger(__name__)


class TemplateModule(BasePromptModule):
    """
    Module voor definitie templates en patronen.

    Genereert categorie-specifieke templates en voorbeelden
    om consistente definities te bevorderen.
    """

    def __init__(self):
        """Initialize de template module."""
        super().__init__(
            module_id="template", module_name="Definition Templates & Patterns"
        )
        self.include_examples = True
        self.detailed_templates = True

    def initialize(self, config: dict[str, Any]) -> None:
        """
        Initialize module met configuratie.

        Args:
            config: Module configuratie
        """
        self._config = config
        self.include_examples = config.get("include_examples", True)
        self.detailed_templates = config.get("detailed_templates", True)
        self._initialized = True
        logger.info(
            f"TemplateModule geïnitialiseerd "
            f"(examples={self.include_examples}, detailed={self.detailed_templates})"
        )

    def validate_input(self, context: ModuleContext) -> tuple[bool, str | None]:
        """
        Valideer of deze module relevant is.

        Args:
            context: Module context

        Returns:
            (is_valid, error_message)
        """
        # Check of we categorie informatie hebben
        category = context.get_metadata("semantic_category")
        if not category and self.detailed_templates:
            return False, "Geen semantische categorie beschikbaar voor templates"

        return True, None

    def execute(self, context: ModuleContext) -> ModuleOutput:
        """
        Genereer templates en patronen.

        Args:
            context: Module context

        Returns:
            ModuleOutput met templates
        """
        try:
            # Haal metadata op
            category = context.get_metadata("semantic_category", "algemeen")
            word_type = context.get_shared("word_type", "overig")

            # Bouw template sectie
            sections = []

            # Header
            sections.append("### 📋 Definitie Templates:")
            sections.append("")

            # Categorie-specifieke templates
            template = self._get_category_template(category)
            if template:
                sections.append(f"**Template voor {category}:**")
                sections.append(template)
                sections.append("")

            # Algemene patronen
            patterns = self._get_definition_patterns(word_type)
            if patterns:
                sections.append("**Aanbevolen definitiepatronen:**")
                sections.extend(patterns)
                sections.append("")

            # Voorbeelden voor deze categorie
            if self.include_examples:
                examples = self._get_category_examples(category)
                if examples:
                    sections.append(f"**Voorbeelden uit categorie {category}:**")
                    sections.extend(examples)

            # Combineer secties
            content = "\n".join(sections)

            return ModuleOutput(
                content=content,
                metadata={
                    "category": category,
                    "word_type": word_type,
                    "templates_provided": bool(template),
                    "examples_count": len(
                        [s for s in sections if s.startswith("  ✅")]
                    ),
                },
            )

        except Exception as e:
            logger.error(f"TemplateModule execution failed: {e}", exc_info=True)
            return ModuleOutput(
                content="",
                metadata={"error": str(e)},
                success=False,
                error_message=f"Failed to generate templates: {e!s}",
            )

    def get_dependencies(self) -> list[str]:
        """
        Deze module is optioneel afhankelijk van semantic categorisation.

        Returns:
            Lege lijst (soft dependency via metadata)
        """
        return []

    def _get_category_template(self, category: str) -> str | None:
        """
        Verkrijg template voor specifieke categorie.

        Args:
            category: Semantische categorie

        Returns:
            Template string of None
        """
        templates = {
            "Proces": "[Handeling/activiteit] waarbij [actor/systeem] [actie] uitvoert [met welk doel/resultaat]",
            "Object": "[Fysiek/digitaal ding] dat [kenmerkende eigenschap] heeft en [functie/rol] vervult",
            "Actor": "[Persoon/instantie/systeem] die [verantwoordelijkheid/rol] heeft voor [domein/activiteit]",
            "Toestand": "[Status/situatie] waarin [object/actor] zich bevindt wanneer [voorwaarde/kenmerk]",
            "Gebeurtenis": "[Voorval/incident] dat optreedt wanneer [trigger/voorwaarde] en resulteert in [uitkomst]",
            "Maatregel": "[Interventie/actie] die wordt toegepast om [doel] te bereiken bij [situatie]",
            "Informatie": "[Gegevens/data] over [onderwerp] die [doel/gebruik] dient",
            "Regel": "[Voorschrift/norm] dat bepaalt [wat] onder [welke voorwaarden]",
            "Recht": "[Bevoegdheid/aanspraak] van [rechthebbende] om [wat te doen/krijgen]",
            "Verplichting": "[Plicht/opdracht] voor [verplichte partij] om [actie/nalating] te doen",
        }

        return templates.get(category)

    def _get_definition_patterns(self, word_type: str) -> list[str]:
        """
        Verkrijg algemene definitiepatronen.

        Args:
            word_type: Type woord

        Returns:
            Lijst met patronen
        """
        patterns = []

        if word_type == "werkwoord":
            patterns.extend(
                [
                    "- [werkwoord]: handeling waarbij [wie/wat] [actie beschrijving]",
                    "- [werkwoord]: proces van het [activiteit omschrijving]",
                    "- [werkwoord]: activiteit die leidt tot [resultaat/uitkomst]",
                ]
            )
        elif word_type == "deverbaal":
            patterns.extend(
                [
                    "- [deverbaal]: resultaat van het [werkwoord]",
                    "- [deverbaal]: uitkomst waarbij [beschrijving van eindtoestand]",
                    "- [deverbaal]: vastgelegde [wat] na afronding van [proces]",
                ]
            )
        else:
            patterns.extend(
                [
                    "- [begrip]: [categorie] die/dat [onderscheidend kenmerk]",
                    "- [begrip]: [bovenbegrip] met als kenmerk [specificatie]",
                    "- [begrip]: [type/soort] [bovenbegrip] voor [doel/functie]",
                ]
            )

        return patterns

    def _get_category_examples(self, category: str) -> list[str]:
        """
        Verkrijg voorbeelden voor categorie.

        Args:
            category: Semantische categorie

        Returns:
            Lijst met voorbeelden
        """
        examples_map = {
            "Proces": [
                "  ✅ toezicht: systematisch volgen van handelingen om naleving van regels te waarborgen",
                "  ✅ registratie: proces waarbij gegevens formeel worden vastgelegd in een systeem",
                "  ✅ beoordeling: evaluatie van prestaties aan de hand van vooraf bepaalde criteria",
            ],
            "Object": [
                "  ✅ dossier: verzameling documenten die betrekking hebben op één zaak of persoon",
                "  ✅ systeem: geheel van onderling verbonden componenten met een gemeenschappelijk doel",
                "  ✅ register: officiële vastlegging van geordende gegevens voor raadpleging",
            ],
            "Actor": [
                "  ✅ toezichthouder: functionaris belast met het controleren van naleving van voorschriften",
                "  ✅ belanghebbende: persoon met een rechtstreeks belang bij een besluit of handeling",
                "  ✅ bevoegd gezag: instantie met wettelijke macht om besluiten te nemen",
            ],
            "Maatregel": [
                "  ✅ sanctie: corrigerende actie opgelegd bij geconstateerde overtreding",
                "  ✅ waarschuwing: formele kennisgeving van ongewenst gedrag met dreiging van consequenties",
                "  ✅ interventie: doelgerichte handeling om een ongewenste situatie te veranderen",
            ],
            "Regel": [
                "  ✅ voorschrift: bindende bepaling die aangeeft wat verplicht of verboden is",
                "  ✅ richtlijn: aanbeveling voor handelen in specifieke situaties",
                "  ✅ protocol: vastgelegde werkwijze voor standaardsituaties",
            ],
        }

        return examples_map.get(
            category,
            ["  ℹ️ Geen specifieke voorbeelden beschikbaar voor deze categorie"],  # noqa: RUF001
        )
