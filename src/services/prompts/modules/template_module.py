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

    def __init__(self) -> None:
        """Initialize de template module."""
        super().__init__(
            module_id="template",
            module_name="Definition Templates & Patterns",
            priority=60,  # Medium prioriteit - hulpmiddel
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
        logger.debug(
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
        Deze module leest `word_type` uit shared state; ExpertiseModule schrijft het.

        DEF-582: zonder deze declaratie liep de module parallel aan zijn eigen
        schrijver en las soms de default "overig". De afhankelijkheid op
        semantic categorisation loopt via context-metadata (niet via shared
        state) en wordt door `validate_input` afgevangen.

        Returns:
            Lijst met dependencies
        """
        return ["expertise"]

    def _get_category_template(self, category: str) -> str | None:
        """
        Verkrijg template voor specifieke categorie.

        Args:
            category: Semantische categorie

        Returns:
            Template string of None
        """
        templates = {
            "Proces": "[Handeling/activiteit] waarbij [actor/systeem] [kenmerkende handeling] uitvoert [met een onderscheidend resultaat indien onderbouwd]",
            "Object": "[Fysiek/digitaal ding] met [onderscheidende kenmerken]; neem een functie of rol alleen op bij gegeven begripsbepalende grond volgens ESS-01",
            "Actor": "[Persoon/instantie/systeem] die [verantwoordelijkheid/rol] heeft voor [domein/activiteit]",
            "Toestand": "[Status/situatie] waarin [object/actor] zich bevindt wanneer [voorwaarde/kenmerk]",
            "Gebeurtenis": "[Voorval/incident] dat optreedt wanneer [trigger/voorwaarde] en resulteert in [uitkomst]",
            "Maatregel": "[Interventie/actie] met [onderbouwde kenmerkende inhoud en toepassingsvoorwaarden]; een doel volgt alleen uit gegeven begripsafbakening volgens ESS-01",
            # DEF-750: RESULTAAT is een uitkomst en niet standaard een
            # maatregel; eigen template met de ontstaansrelatie als kenmerk.
            "Resultaat": "[Uitkomst/product] van [handeling of proces] met [onderscheidende inhoud]; een uitkomst is niet noodzakelijk een maatregel — behoud de ontstaansrelatie zonder de activiteit tot hoofdbetekenis te maken",
            "Informatie": "[Gegevens/data] over [onderwerp] met [onderscheidende inhoud of herkomst]",
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
                    "- [begrip]: [bovenbegrip] met [onderbouwd onderscheidend kenmerk]",
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
                "  Grensgeval — toezicht: systematisch volgen van handelingen om naleving van regels te waarborgen. Onderbouw eerst of nalevingswaarborg begripsbepalend is of een gewenst effect; zinsvorm alleen geeft geen goed/fout-label (ESS-01).",
                "  ✅ registratie: proces waarbij gegevens formeel worden vastgelegd in een systeem",
                "  ✅ beoordeling: evaluatie van prestaties aan de hand van vooraf bepaalde criteria",
            ],
            "Object": [
                "  ✅ dossier: verzameling documenten die betrekking hebben op één zaak of persoon",
                "  Grensgeval — systeem: een gemeenschappelijk doel is alleen toelaatbaar met gegeven begripsbepalende grond (ESS-01); zonder grond blijft dit open.",
                "  Grensgeval — register: officiële vastlegging van geordende gegevens voor raadpleging. Onderbouw of raadpleging de gegeven betekenis bepaalt of alleen bijkomend gebruik is (ESS-01); zonder grond blijft dit open.",
            ],
            "Actor": [
                "  ✅ toezichthouder: functionaris belast met het controleren van naleving van voorschriften",
                "  ✅ belanghebbende: persoon met een rechtstreeks belang bij een besluit of handeling",
                "  ✅ bevoegd gezag: instantie met wettelijke macht om besluiten te nemen",
            ],
            "Maatregel": [
                "  ✅ sanctie: corrigerende actie opgelegd bij geconstateerde overtreding",
                "  ✅ waarschuwing: formele kennisgeving van ongewenst gedrag met dreiging van consequenties",
                "  Grensgeval — gegeven afbakening: interventie is een gerichte ingreep in een bestaand proces ter verandering daarvan. Kandidaat: gerichte ingreep in een bestaand proces om de gang daarvan te veranderen. De doelfunctie is alleen toelaatbaar bij deze bevestigde grond volgens ESS-01; zonder grond blijft dit open.",
            ],
            "Resultaat": [
                "  ✅ registratie: resultaat van het vastleggen van meetwaarden in een register",
                "  ✅ verslag: schriftelijke weergave van wat tijdens een bijeenkomst is besproken en besloten",
                "  Grensgeval — beoordeling: uitkomst van een beoordelingsproces waarbij criteria worden toegepast. Benoem de uitkomst als kern en houd de activiteit als ontstaansrelatie (ESS-02); een doel of functie alleen met begripsbepalende grond (ESS-01).",
            ],
            "Regel": [
                "  ✅ voorschrift: bindende bepaling die aangeeft wat verplicht of verboden is",
                "  ✅ richtlijn: aanbeveling voor handelen in specifieke situaties",
                "  ✅ protocol: vastgelegde werkwijze voor standaardsituaties",
            ],
        }

        return examples_map.get(
            category,
            ["  i Geen specifieke voorbeelden beschikbaar voor deze categorie"],
        )
