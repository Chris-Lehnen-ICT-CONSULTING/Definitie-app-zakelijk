"""
ESS Rules Module - Implementeert ESS validatieregels voor definities.

Deze module is verantwoordelijk voor:
1. Alle ESS (Essentie) validatieregels
2. Ontologische categorisatie regels
3. Toetsbaarheid en onderscheidendheid
"""

import logging
from typing import Any

from config.config_loader import laad_toetsregels

from .base_module import BasePromptModule, ModuleContext, ModuleOutput

logger = logging.getLogger(__name__)


class EssRulesModule(BasePromptModule):
    """
    Module voor ESS (Essentie) validatieregels.

    Genereert alle ESS regels die de essentie van definities valideren,
    inclusief ontologische categorisatie en toetsbaarheid.
    """

    def __init__(self):
        """Initialize de ESS rules module."""
        super().__init__(
            module_id="ess_rules",
            module_name="Essence Validation Rules (ESS)",
            priority=75,  # Hoge prioriteit - essentie is cruciaal
        )
        self.include_examples = True
        self._toetsregels = None

    def initialize(self, config: dict[str, Any]) -> None:
        """
        Initialize module met configuratie.

        Args:
            config: Module configuratie
        """
        self._config = config
        self.include_examples = config.get("include_examples", True)
        self._initialized = True

        # Load toetsregels from JSON
        try:
            self._toetsregels = laad_toetsregels()
            logger.info(
                f"EssRulesModule geïnitialiseerd (examples={self.include_examples})"
            )
        except Exception as e:
            logger.error(f"Fout bij laden toetsregels: {e}")
            self._toetsregels = {}

    def validate_input(self, context: ModuleContext) -> tuple[bool, str | None]:
        """Deze module draait altijd."""
        return True, None

    def execute(self, context: ModuleContext) -> ModuleOutput:
        """Genereer ESS validatieregels."""
        try:
            sections = []
            sections.append("### 🎯 Essentie Regels (ESS):")

            # Filter alleen ESS regels
            ess_rules = {
                k: v for k, v in self._toetsregels.items() if k.startswith("ESS-")
            }

            # Sorteer regels
            sorted_rules = sorted(ess_rules.items())

            for regel_key, regel_data in sorted_rules:
                sections.extend(self._format_rule(regel_key, regel_data))

            content = "\n".join(sections)

            return ModuleOutput(
                content=content,
                metadata={
                    "rules_count": len(ess_rules),
                    "include_examples": self.include_examples,
                    "rule_prefix": "ESS",
                },
            )

        except Exception as e:
            logger.error(f"EssRulesModule execution failed: {e}", exc_info=True)
            return ModuleOutput(
                content="",
                metadata={"error": str(e)},
                success=False,
                error_message=f"Failed to generate ESS rules: {e!s}",
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
