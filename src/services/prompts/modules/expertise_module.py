"""
Expertise Module - Definieert de expert rol en basis instructies.

Deze module is verantwoordelijk voor:
1. Expert rol definitie
2. Taak instructies
3. Basis schrijfregels
"""

import logging
from typing import Any

from .base_module import BasePromptModule, ModuleContext, ModuleOutput

logger = logging.getLogger(__name__)


class ExpertiseModule(BasePromptModule):
    """
    Module voor expert rol definitie en fundamentele instructies.

    Genereert het eerste deel van de prompt dat de AI's rol en
    basis taken definieert.
    """

    def __init__(self):
        """Initialize de expertise module."""
        super().__init__(
            module_id="expertise",
            module_name="Expert Role & Basic Instructions",
            priority=100,  # Hoogste prioriteit - basis instructies
        )

    def initialize(self, config: dict[str, Any]) -> None:
        """
        Initialize module met configuratie.

        Args:
            config: Module configuratie
        """
        self._config = config
        self._initialized = True
        logger.info("ExpertiseModule geïnitialiseerd")

    def validate_input(self, context: ModuleContext) -> tuple[bool, str | None]:
        """
        Valideer input - deze module heeft altijd geldige input.

        Args:
            context: Module context

        Returns:
            Altijd (True, None) omdat deze module altijd draait
        """
        if not context.begrip:
            return False, "Begrip mag niet leeg zijn"
        return True, None

    def execute(self, context: ModuleContext) -> ModuleOutput:
        """
        Genereer expert rol en basis instructies.

        Args:
            context: Module context met begrip info

        Returns:
            ModuleOutput met expert rol definitie
        """
        try:
            # Bepaal woordsoort voor later gebruik
            woordsoort = self._bepaal_woordsoort(context.begrip)

            # Sla woordsoort op voor andere modules
            context.set_shared("word_type", woordsoort)

            # Bouw de expert rol sectie
            sections = []

            # 1. Rol definitie
            sections.append(self._build_role_definition())

            # 2. Taak instructie
            sections.append(self._build_task_instruction())

            # 3. Woordsoort-specifiek advies
            word_type_advice = self._build_word_type_advice(woordsoort)
            if word_type_advice:
                sections.append(word_type_advice)

            # 4. Basis kwaliteitsvereisten
            sections.append(self._build_basic_requirements())

            # Combineer secties
            content = "\n".join(sections)

            return ModuleOutput(
                content=content,
                metadata={"word_type": woordsoort, "sections_generated": len(sections)},
            )

        except Exception as e:
            logger.error(f"ExpertiseModule execution failed: {e}", exc_info=True)
            return ModuleOutput(
                content="",
                metadata={"error": str(e)},
                success=False,
                error_message=f"Failed to generate expertise section: {e!s}",
            )

    def get_dependencies(self) -> list[str]:
        """
        Deze module heeft geen dependencies.

        Returns:
            Lege lijst
        """
        return []

    def _bepaal_woordsoort(self, begrip: str) -> str:
        """
        Bepaal woordsoort van begrip.

        Args:
            begrip: Het te analyseren begrip

        Returns:
            'werkwoord', 'deverbaal', of 'overig'
        """
        begrip_lower = begrip.lower().strip()

        # Werkwoord detectie
        werkwoord_suffixen = ["eren", "elen", "enen", "igen", "iken", "ijven"]
        if any(begrip_lower.endswith(suffix) for suffix in werkwoord_suffixen):
            return "werkwoord"

        # Simpele werkwoord check
        if (
            len(begrip_lower) > 4
            and begrip_lower.endswith("en")
            and not begrip_lower.endswith(("ing", "atie", "isatie"))
        ):
            return "werkwoord"

        # Deverbaal detectie (zelfstandig naamwoord afgeleid van werkwoord)
        deverbaal_suffixen = ["ing", "atie", "age", "ment", "tie", "sie", "isatie"]
        if any(begrip_lower.endswith(suffix) for suffix in deverbaal_suffixen):
            return "deverbaal"

        return "overig"

    def _build_role_definition(self) -> str:
        """
        Bouw de expert rol definitie.

        Returns:
            Rol definitie tekst
        """
        return "Je bent een expert in beleidsmatige definities voor overheidsgebruik."

    def _build_task_instruction(self) -> str:
        """
        Bouw de taak instructie.

        Returns:
            Taak instructie tekst
        """
        return "Formuleer een heldere definitie die het begrip precies afbakent."

    def _build_word_type_advice(self, woordsoort: str) -> str | None:
        """
        Bouw woordsoort-specifiek schrijfadvies.

        Args:
            woordsoort: Type woord (werkwoord/deverbaal/overig)

        Returns:
            Schrijfadvies of None
        """
        advice_map = {
            "werkwoord": "Als het begrip een handeling beschrijft, definieer het dan als proces of activiteit.",
            "deverbaal": "Als het begrip een resultaat is, beschrijf het dan als uitkomst van een proces.",
            "overig": "Gebruik een zakelijke en generieke stijl voor het definiëren van dit begrip.",
        }

        return advice_map.get(woordsoort)

    def _build_basic_requirements(self) -> str:
        """
        Bouw basis kwaliteitsvereisten.

        Returns:
            Basis vereisten tekst
        """
        return """BELANGRIJKE VEREISTEN:
- Gebruik objectieve, neutrale taal
- Vermijd vage of subjectieve termen
- Focus op de essentie van het begrip
- Wees precies en ondubbelzinnig
- Vermijd normatieve of evaluatieve uitspraken"""
