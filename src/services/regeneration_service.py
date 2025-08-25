"""Service voor definitie regeneratie met nieuwe categorie."""

import logging
from dataclasses import dataclass
from typing import Any

from services.definition_generator_prompts import UnifiedPromptBuilder

logger = logging.getLogger(__name__)


@dataclass
class RegenerationContext:
    """Context voor definitie regeneratie."""

    begrip: str
    old_category: str
    new_category: str
    previous_definition: str | None = None
    reason: str | None = None

    def to_feedback_entry(self) -> dict[str, Any]:
        """Convert naar feedback entry voor prompt builder."""
        return {
            "definition": self.previous_definition or "",
            "violations": [
                f"Categorie was {self.old_category}, moet nu {self.new_category} zijn"
            ],
            "suggestions": [
                f"Maak een definitie passend bij categorie {self.new_category}",
                f"Focus op {self._get_category_focus(self.new_category)}",
            ],
        }

    def _get_category_focus(self, category: str) -> str:
        """Get focus instructie voor categorie."""
        focus_map = {
            "ENT": "wat het IS (zelfstandig naamwoord)",
            "REL": "de relatie/verband tussen entiteiten",
            "ACT": "het proces/handeling/activiteit",
            "ATT": "de eigenschap/kenmerk",
            "AUT": "de bevoegdheid/autorisatie",
            "STA": "de status/toestand",
            "OTH": "het concept in algemene termen",
        }
        return focus_map.get(category, "het concept")


class RegenerationService:
    """Service voor het regenereren van definities met nieuwe categorie."""

    def __init__(self, prompt_builder: UnifiedPromptBuilder):
        """Initialize service.

        Args:
            prompt_builder: De unified prompt builder service
        """
        self.prompt_builder = prompt_builder
        self._active_context: RegenerationContext | None = None

    def set_regeneration_context(
        self,
        begrip: str,
        old_category: str,
        new_category: str,
        previous_definition: str | None = None,
        reason: str | None = None,
    ) -> None:
        """Set context voor regeneratie.

        Dit wordt aangeroepen wanneer gebruiker kiest voor regeneratie
        na category wijziging.
        """
        self._active_context = RegenerationContext(
            begrip=begrip,
            old_category=old_category,
            new_category=new_category,
            previous_definition=previous_definition,
            reason=reason,
        )

        logger.info(
            f"Regeneration context set for '{begrip}': "
            f"{old_category} -> {new_category}"
        )

    def get_active_context(self) -> RegenerationContext | None:
        """Get actieve regeneration context."""
        return self._active_context

    def clear_context(self) -> None:
        """Clear regeneration context na gebruik."""
        self._active_context = None
        logger.info("Regeneration context cleared")

    def enhance_prompt_with_context(
        self, base_prompt: str, context: RegenerationContext | None = None
    ) -> str:
        """Enhance prompt met regeneration context.

        Dit integreert met de rode kabel (feedback loop) uit GVI plan.
        """
        context = context or self._active_context

        if not context:
            return base_prompt

        # Voeg feedback toe volgens GVI pattern
        feedback_section = f"""

## Categorie Regeneratie Context:
- Het begrip '{context.begrip}' moet nu gedefinieerd worden als {context.new_category}
- Focus op: {context._get_category_focus(context.new_category)}
- Vermijd elementen die passen bij {context.old_category}

Let op: De definitie moet passen bij de nieuwe ontologische categorie!
"""

        return base_prompt + feedback_section

    def get_feedback_history(self) -> list | None:
        """Get feedback history voor prompt builder.

        Conform GVI Rode Kabel implementatie.
        """
        if not self._active_context:
            return None

        return [self._active_context.to_feedback_entry()]
