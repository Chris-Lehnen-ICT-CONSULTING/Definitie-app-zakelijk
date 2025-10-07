"""
ARAI Rules Module - Implementeert ARAI validatieregels voor definities.

Deze module is verantwoordelijk voor:
1. Alle ARAI (Algemene Regels AI) validatieregels
2. Basis definitie kwaliteitsregels
3. Algemene schrijfrichtlijnen
"""

import logging
from typing import Any

from .base_module import BasePromptModule, ModuleContext, ModuleOutput

logger = logging.getLogger(__name__)


class AraiRulesModule(BasePromptModule):
    """
    Module voor ARAI validatieregels.

    Genereert alle ARAI regels die algemene kwaliteitsrichtlijnen
    voor definities bevatten.
    """

    def __init__(self):
        """Initialize de ARAI rules module."""
        super().__init__(
            module_id="arai_rules",
            module_name="ARAI Validation Rules",
            priority=75,  # Hoge prioriteit - basis regels
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
            f"AraiRulesModule geïnitialiseerd (examples={self.include_examples})"
        )

    def validate_input(self, context: ModuleContext) -> tuple[bool, str | None]:
        """Deze module draait altijd."""
        return True, None

    def execute(self, context: ModuleContext) -> ModuleOutput:
        """Genereer ARAI validatieregels."""
        try:
            sections = []
            sections.append("### ✅ Algemene Regels AI (ARAI):")

            # Load toetsregels on-demand from cached singleton
            from toetsregels.cached_manager import get_cached_toetsregel_manager

            manager = get_cached_toetsregel_manager()
            all_rules = manager.get_all_regels()

            # Filter alleen ARAI regels
            arai_rules = {k: v for k, v in all_rules.items() if k.startswith("ARAI")}

            # Sorteer regels
            sorted_rules = sorted(arai_rules.items())

            for regel_key, regel_data in sorted_rules:
                sections.extend(self._format_rule(regel_key, regel_data))

            content = "\n".join(sections)

            return ModuleOutput(
                content=content,
                metadata={
                    "rules_count": len(arai_rules),
                    "include_examples": self.include_examples,
                    "rule_prefix": "ARAI",
                },
            )

        except Exception as e:
            logger.error(f"AraiRulesModule execution failed: {e}", exc_info=True)
            return ModuleOutput(
                content="",
                metadata={"error": str(e)},
                success=False,
                error_message=f"Failed to generate ARAI rules: {e!s}",
            )

    def get_dependencies(self) -> list[str]:
        """Deze module heeft geen dependencies."""
        return []

    def _format_rule(self, regel_key: str, regel_data: dict) -> list[str]:
        """Formateer een regel uit JSON data."""
        lines = []

        # Header met emoji
        naam = regel_data.get("naam", "Onbekende regel")
        lines.append(f"🔹 **{regel_key} - {naam}**")

        # Uitleg
        uitleg = regel_data.get("uitleg", "")
        if uitleg:
            lines.append(f"- {uitleg}")

        # Toetsvraag
        toetsvraag = regel_data.get("toetsvraag", "")
        if toetsvraag:
            lines.append(f"- Toetsvraag: {toetsvraag}")

        # Voorbeelden (indien enabled)
        if self.include_examples:
            # Goede voorbeelden
            goede_voorbeelden = regel_data.get("goede_voorbeelden", [])
            for goed in goede_voorbeelden:
                lines.append(f"  ✅ {goed}")

            # Foute voorbeelden
            foute_voorbeelden = regel_data.get("foute_voorbeelden", [])
            for fout in foute_voorbeelden:
                lines.append(f"  ❌ {fout}")

        return lines
