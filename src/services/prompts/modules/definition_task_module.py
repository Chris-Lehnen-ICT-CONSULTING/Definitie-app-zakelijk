"""
Definition Task Module - Finale instructies en metadata.

Deze module is verantwoordelijk voor:
1. Definitie opdracht
2. Checklist
3. Kwaliteitscontrole vragen
4. Metadata voor traceerbaarheid
"""

import logging
from datetime import datetime
from typing import Any

from .base_module import BasePromptModule, ModuleContext, ModuleOutput

logger = logging.getLogger(__name__)


class DefinitionTaskModule(BasePromptModule):
    """
    Module voor finale instructies, checklist en metadata.

    Genereert het laatste deel van de prompt met de specifieke
    opdracht, kwaliteitscontrole en metadata.
    """

    def __init__(self):
        """Initialize de definition task module."""
        super().__init__(
            module_id="definition_task",
            module_name="Final Instructions & Task Definition",
        )
        self.include_quality_control = True
        self.include_metadata = True

    def initialize(self, config: dict[str, Any]) -> None:
        """
        Initialize module met configuratie.

        Args:
            config: Module configuratie
        """
        self._config = config
        self.include_quality_control = config.get("include_quality_control", True)
        self.include_metadata = config.get("include_metadata", True)
        self._initialized = True
        logger.info(
            f"DefinitionTaskModule geïnitialiseerd "
            f"(quality_control={self.include_quality_control}, metadata={self.include_metadata})"
        )

    def validate_input(self, context: ModuleContext) -> tuple[bool, str | None]:
        """
        Valideer dat begrip aanwezig is.

        Args:
            context: Module context

        Returns:
            (valid, error_message)
        """
        if not context.begrip or not context.begrip.strip():
            return False, "Begrip is vereist voor definition task"
        return True, None

    def execute(self, context: ModuleContext) -> ModuleOutput:
        """
        Genereer finale instructies en task definitie.

        Args:
            context: Module context

        Returns:
            ModuleOutput met finale instructies
        """
        try:
            begrip = context.begrip

            # Haal gedeelde informatie op
            word_type = context.get_shared("word_type", "onbekend")
            ontological_category = context.get_shared("ontological_category")
            org_contexts = context.get_shared("organization_contexts", [])
            # Derive juridical and legal-basis contexts from enriched base_context
            try:
                base_ctx = (
                    context.enriched_context.base_context
                    if context and context.enriched_context
                    else {}
                )
            except Exception:
                base_ctx = {}
            jur_contexts = (
                base_ctx.get("juridische_context") or base_ctx.get("juridisch") or []
            )
            wet_basis = (
                base_ctx.get("wettelijke_basis") or base_ctx.get("wettelijk") or []
            )
            has_context = bool(
                org_contexts
                or jur_contexts
                or wet_basis
                or context.get_shared("domain_contexts", [])
            )

            # Bouw secties
            sections = []

            # Finale instructies header
            sections.append("### 🎯 FINALE INSTRUCTIES:")

            # Definitie opdracht
            sections.append(self._build_task_assignment(begrip))

            # Checklist
            sections.append(self._build_checklist(ontological_category))

            # Kwaliteitscontrole
            if self.include_quality_control:
                sections.append(self._build_quality_control(has_context))

            # Metadata
            if self.include_metadata:
                sections.append(
                    self._build_metadata(begrip, word_type, org_contexts, has_context)
                )

            # Ontologische marker instructie
            sections.append(self._build_ontological_marker())

            # Finale definitie opdracht
            sections.append(self._build_final_instruction(begrip))

            # Prompt metadata
            sections.append(
                self._build_prompt_metadata(
                    begrip, word_type, org_contexts, jur_contexts, wet_basis
                )
            )

            # Combineer secties
            content = "\n\n".join(sections)

            return ModuleOutput(
                content=content,
                metadata={
                    "begrip": begrip,
                    "word_type": word_type,
                    "has_context": has_context,
                    "ontological_category": ontological_category,
                },
            )

        except Exception as e:
            logger.error(f"DefinitionTaskModule execution failed: {e}", exc_info=True)
            return ModuleOutput(
                content="",
                metadata={"error": str(e)},
                success=False,
                error_message=f"Failed to generate definition task: {e!s}",
            )

    def get_dependencies(self) -> list[str]:
        """
        Deze module is afhankelijk van SemanticCategorisationModule.

        Returns:
            Lijst met dependency
        """
        return ["semantic_categorisation"]

    def _build_task_assignment(self, begrip: str) -> str:
        """Bouw de definitie opdracht."""
        return f"""#### ✏️ Definitieopdracht:
Formuleer nu de definitie van **{begrip}** volgens deze specificaties:"""

    def _build_checklist(self, ontological_category: str | None) -> str:
        """
        Bouw de checklist.

        Args:
            ontological_category: Ontologische categorie indien bekend

        Returns:
            Checklist tekst
        """
        ont_cat = ""
        if ontological_category:
            category_hints = {
                "proces": "activiteit/handeling",
                "type": "soort/categorie",
                "resultaat": "uitkomst/gevolg",
                "exemplaar": "specifiek geval",
            }
            if ontological_category in category_hints:
                ont_cat = f"\n🎯 Focus: Dit is een **{ontological_category}** ({category_hints[ontological_category]})"

        return f"""📋 **CHECKLIST - Controleer voor je antwoord:**
□ Begint met zelfstandig naamwoord (geen lidwoord/koppelwerkwoord)
□ Eén enkele zin zonder punt aan het einde
□ Geen toelichting, voorbeelden of haakjes
□ Ontologische categorie is duidelijk{ont_cat}
□ Geen verboden woorden (aspect, element, kan, moet, etc.)
□ Context verwerkt zonder expliciete benoeming"""

    def _build_quality_control(self, has_context: bool) -> str:
        """
        Bouw kwaliteitscontrole vragen.

        Args:
            has_context: Of er context aanwezig is

        Returns:
            Kwaliteitscontrole sectie
        """
        context_vraag = "de gegeven context" if has_context else "algemeen gebruik"

        return f"""#### 🔍 KWALITEITSCONTROLE:
Stel jezelf deze vragen:
1. Is direct duidelijk WAT het begrip is (niet het doel)?
2. Kan iemand hiermee bepalen of iets wel/niet onder dit begrip valt?
3. Is de formulering specifiek genoeg voor {context_vraag}?
4. Bevat de definitie alleen essentiële informatie?"""

    def _build_metadata(
        self, begrip: str, word_type: str, org_contexts: list[str], has_context: bool
    ) -> str:
        """
        Bouw metadata sectie.

        Args:
            begrip: Het begrip
            word_type: Type woord
            org_contexts: Organisatorische contexten
            has_context: Of er context is

        Returns:
            Metadata sectie
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return f"""#### 📊 METADATA voor traceerbaarheid:
- Begrip: {begrip}
- Timestamp: {timestamp}
- Context beschikbaar: {"Ja" if has_context else "Nee"}
- Builder versie: Modular Architecture v2.0"""

    def _build_ontological_marker(self) -> str:
        """Bouw ontologische marker instructie."""
        return """---

📋 **Ontologische marker (lever als eerste regel):**
- Ontologische categorie: kies uit [soort, exemplaar, proces, resultaat]"""

    def _build_final_instruction(self, begrip: str) -> str:
        """Bouw finale definitie instructie."""
        return f"✏️ Geef nu de definitie van het begrip **{begrip}** in één enkele zin, zonder toelichting."

    def _build_prompt_metadata(
        self,
        begrip: str,
        word_type: str,
        org_contexts: list[str],
        jur_contexts: list[str],
        wet_basis: list[str],
    ) -> str:
        """
        Bouw prompt metadata sectie.

        Args:
            begrip: Het begrip
            word_type: Type woord
            org_contexts: Organisatorische contexten

        Returns:
            Prompt metadata
        """
        lines = [
            "🆔 Promptmetadata:",
            f"- Begrip: {begrip}",
            f"- Termtype: {word_type}",
        ]

        if org_contexts:
            lines.append(f"- Organisatorische context: {', '.join(org_contexts)}")
        else:
            lines.append("- Organisatorische context: geen")

        if jur_contexts:
            lines.append(f"- Juridische context: {', '.join(jur_contexts)}")
        else:
            lines.append("- Juridische context: geen")

        if wet_basis:
            lines.append(f"- Wettelijke basis: {', '.join(wet_basis)}")
        else:
            lines.append("- Wettelijke basis: geen")

        return "\n".join(lines)
