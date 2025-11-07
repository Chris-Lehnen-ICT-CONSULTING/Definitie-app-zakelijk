"""
Error Prevention Module - Instructies voor effectieve definities.

Deze module is verantwoordelijk voor:
1. Positieve instructies voor goede definities
2. Context-aware richtlijnen
3. Kritieke waarschuwingen waar nodig
4. Validatiematrix
"""

import logging
from typing import Any

from .base_module import BasePromptModule, ModuleContext, ModuleOutput

logger = logging.getLogger(__name__)


class ErrorPreventionModule(BasePromptModule):
    """
    Module voor het genereren van positieve instructies voor definitie-kwaliteit.

    Genereert richtlijnen voor effectieve definities met focus op
    wat WEL te doen in plaats van alleen verboden.
    """

    def __init__(self):
        """Initialize de error prevention module."""
        super().__init__(
            module_id="error_prevention",
            module_name="Definition Quality Instructions",
        )
        self.include_validation_matrix = True
        self.extended_instructions = True

    def initialize(self, config: dict[str, Any]) -> None:
        """
        Initialize module met configuratie.

        Args:
            config: Module configuratie
        """
        self._config = config
        self.include_validation_matrix = config.get("include_validation_matrix", True)
        self.extended_instructions = config.get("extended_instructions", True)
        self._initialized = True
        logger.debug(
            f"ErrorPreventionModule geïnitialiseerd "
            f"(matrix={self.include_validation_matrix}, extended={self.extended_instructions})"
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
        Genereer instructies voor definitie-kwaliteit.

        Args:
            context: Module context

        Returns:
            ModuleOutput met instructies
        """
        try:
            # Haal context informatie op van ContextAwarenessModule
            # EPIC-010: Gebruik alle 3 actieve context types (domein is legacy)
            org_contexts = context.get_shared("organization_contexts", [])
            jur_contexts = context.get_shared("juridical_contexts", [])
            wet_contexts = context.get_shared("legal_basis_contexts", [])

            # Bouw secties
            sections = []

            # Header met positieve framing
            sections.append("### ✅ Instructies voor effectieve definities:")

            # Positieve instructies (geconsolideerd van ~30 naar ~10)
            sections.extend(self._build_positive_instructions())

            # Context-specifieke instructies
            context_instructions = self._build_context_instructions(
                org_contexts, jur_contexts, wet_contexts
            )
            if context_instructions:
                sections.append("\n### 🎯 Context-specifieke richtlijnen:")
                sections.extend(context_instructions)

            # Kritieke waarschuwingen (alleen waar positief niet werkt)
            if self.extended_instructions:
                sections.append("\n### ⚠️ Kritieke aandachtspunten:")
                sections.extend(self._build_critical_warnings())

            # Validatiematrix
            if self.include_validation_matrix:
                sections.append(self._build_validation_matrix())

            # Afsluitende reminder
            sections.append(
                "\n💡 Focus: Schrijf vanuit de essentie van het begrip, niet vanuit de context."
            )

            # Combineer alles
            content = "\n".join(sections)

            return ModuleOutput(
                content=content,
                metadata={
                    "context_count": len(org_contexts)
                    + len(jur_contexts)
                    + len(wet_contexts),
                    "include_matrix": self.include_validation_matrix,
                    "extended_instructions": self.extended_instructions,
                    "instruction_type": "positive",
                },
            )

        except Exception as e:
            logger.error(f"ErrorPreventionModule execution failed: {e}", exc_info=True)
            return ModuleOutput(
                content="",
                metadata={"error": str(e)},
                success=False,
                error_message=f"Failed to generate instruction section: {e!s}",
            )

    def get_dependencies(self) -> list[str]:
        """
        Deze module is afhankelijk van ContextAwarenessModule.

        Returns:
            Lijst met dependency
        """
        return ["context_awareness"]

    def _build_positive_instructions(self) -> list[str]:
        """
        Bouw positieve, actionele instructies.

        CONSOLIDATIE: Van ~30 regels naar ~10 door groepering:
        - Alle "niet starten met" regels → 1 positieve instructie
        - Alle vage termen → 1 specificiteit instructie
        - Alle grammatica regels → 1 taalgebruik instructie
        """
        return [
            # Geconsolideerd van 20+ "niet starten met" regels
            "- 📝 **Start direct met de essentie**: Begin met wat het begrip IS (zonder lidwoorden, koppelwerkwoorden of meta-woorden)",
            # Positieve versie van "geen herhaling/synoniem"
            "- 🎯 **Definieer vanuit functie**: Beschrijf wat het begrip doet of bewerkstelligt, niet wat het lijkt",
            # Geconsolideerd van alle vage termen warnings
            "- 🔍 **Wees specifiek en concreet**: Gebruik precieze termen in plaats van algemene containers",
            # Positieve versie van ontologische markers regel
            "- ✨ **Gebruik ontologische markers bewust**: 'proces', 'activiteit', 'handeling' mogen wanneer ze specificeren WAT het begrip IS",
            "  • Goed: 'systematisch proces waarbij gegevens worden verzameld' ✅",
            "  • Fout: 'proces ter ondersteuning van...' ❌",
            # Geconsolideerd van grammatica regels
            "- 📐 **Gebruik heldere grammatica**: Enkelvoud voor zelfstandig naamwoord, infinitief voor werkwoord, minimale bijzinnen",
            # Nieuwe positieve instructie voor structuur
            "- 🏗️ **Structureer logisch**: Genus proximum (wat is het) → differentia specifica (wat maakt het uniek)",
            # Focus op bruikbaarheid
            "- 🎪 **Test de definitie**: Kan iemand zonder voorkennis het begrip begrijpen en toepassen?",
        ]

    def _build_critical_warnings(self) -> list[str]:
        """
        Bouw alleen kritieke waarschuwingen waar positieve framing onduidelijk zou zijn.

        REDUCTIE: Van ~8 naar 3 door alleen echt kritieke zaken te behouden.
        """
        return [
            # Deze blijft negatief omdat het te complex is om positief te formuleren
            "- ❌ **Vermijd cirkelredenering**: Gebruik het te definiëren begrip niet in de definitie",
            # Context warning blijft omdat dit project-specifiek is
            "- ❌ **Geen letterlijke contextvermelding**: Organisaties, wetboeken of juridische context horen niet in de definitie",
            # Deze blijft als quality gate
            "- ❌ **Geen subjectieve kwalificaties**: Vermijd 'belangrijk', 'essentieel', 'adequaat' - laat de lezer oordelen",
        ]

    def _build_context_instructions(
        self, org_contexts: list[str], jur_contexts: list[str], wet_contexts: list[str]
    ) -> list[str]:
        """
        Bouw context-specifieke positieve instructies.

        Args:
            org_contexts: Organisatorische contexten
            jur_contexts: Juridische contexten
            wet_contexts: Wettelijke basis contexten

        Returns:
            Lijst met context-specifieke instructies
        """
        instructions = []

        # Organisatie mapping voor afkortingen
        org_mappings = {
            "NP": "Nederlands Politie",
            "DJI": "Dienst Justitiële Inrichtingen",
            "OM": "Openbaar Ministerie",
            "ZM": "Zittende Magistratuur",
            "3RO": "Samenwerkingsverband Reclasseringsorganisaties",
            "CJIB": "Centraal Justitieel Incassobureau",
            "KMAR": "Koninklijke Marechaussee",
            "FIOD": "Fiscale Inlichtingen- en Opsporingsdienst",
        }

        # Positieve framing voor context-aware definitie
        if org_contexts or jur_contexts or wet_contexts:
            instructions.append(
                "- 🎯 **Focus op universele toepassing**: Schrijf definities die werken ongeacht de specifieke organisatie of context"
            )

        # Specifieke organisatie instructies (positief geformuleerd)
        if org_contexts:
            orgs_display = []
            for org in org_contexts:
                orgs_display.append(org)
                if org in org_mappings:
                    orgs_display.append(org_mappings[org])

            if orgs_display:
                instructions.append(
                    f"- 📋 **Abstraheer van organisatie**: Definieer het begrip zonder '{', '.join(orgs_display)}' te noemen"
                )

        # Juridische context instructies
        if jur_contexts:
            instructions.append(
                f"- ⚖️ **Generaliseer juridische context**: Maak de definitie toepasbaar buiten '{', '.join(jur_contexts)}'"
            )

        # Wettelijke basis instructies
        if wet_contexts:
            instructions.append(
                f"- 📚 **Abstraheer van wetgeving**: Formuleer zonder directe verwijzing naar '{', '.join(wet_contexts)}'"
            )

        return instructions

    def _build_validation_matrix(self) -> str:
        """Bouw de validatiematrix met positieve framing."""
        return """
### 📊 Kwaliteitscheck Matrix:

| Kwaliteitsaspect                     | Instructie                                  | Waarom belangrijk?                         |
|--------------------------------------|---------------------------------------------|---------------------------------------------|
| **Directe start**                    | Begin met de essentie                      | Voorkomt vage intro's en meta-taal         |
| **Functie-focus**                    | Definieer wat het doet                     | Maakt definitie bruikbaar                  |
| **Specificiteit**                    | Gebruik concrete termen                    | Voorkomt vaagheid                          |
| **Ontologische helderheid**          | Specificeer wat het IS                     | Geeft categorie aan                        |
| **Grammaticale eenvoud**             | Enkelvoud, infinitief, minimale bijzinnen  | Verbetert leesbaarheid                     |
| **Context-onafhankelijkheid**        | Abstraheer van specifieke context          | Universele toepasbaarheid                  |
| **Testbaarheid**                     | Controleer begrip zonder voorkennis        | Valideert effectiviteit                    |"""
