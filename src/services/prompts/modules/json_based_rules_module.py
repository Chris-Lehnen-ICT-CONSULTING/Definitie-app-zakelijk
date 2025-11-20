"""
JSON-Based Rules Module - Generieke base voor JSON toetsregel modules.

DEF-156 Phase 1: Consolidatie van 5 identieke rule modules
- AraiRulesModule (ARAI)
- ConRulesModule (CON)
- EssRulesModule (ESS)
- SamRulesModule (SAM)
- VerRulesModule (VER)

Deze modules zijn 100% identiek, behalve voor:
- rule_prefix (filter voor JSON keys)
- module_id
- module_name
- header_emoji
- priority

Door deze parameters te externaliseren, reduceren we 640 lines naar 128 lines
(512 line reduction = 80% code eliminatie).
"""

import logging
from typing import Any

from .base_module import BasePromptModule, ModuleContext, ModuleOutput

logger = logging.getLogger(__name__)


class JSONBasedRulesModule(BasePromptModule):
    """
    Generieke module voor validatieregels die uit JSON worden geladen.

    Deze module implementeert het volledige pattern voor JSON-based regel modules:
    1. Load regels from cached toetsregel manager
    2. Filter regels by prefix (ARAI, CON, ESS, SAM, VER)
    3. Format rules met emoji, naam, uitleg, toetsvraag, voorbeelden
    4. Generate markdown sectie met header

    Parameters:
        rule_prefix: Prefix voor filteren (bijv. "ARAI", "CON-")
        module_id: Unieke identifier (bijv. "arai_rules")
        module_name: Display naam (bijv. "ARAI Validation Rules")
        header_emoji: Emoji voor sectie header (bijv. "✅")
        header_text: Display tekst in header (bijv. "Algemene Regels AI (ARAI)")
        priority: Execution priority (60-75)

    Example:
        >>> module = JSONBasedRulesModule(
        ...     rule_prefix="ARAI",
        ...     module_id="arai_rules",
        ...     module_name="ARAI Validation Rules",
        ...     header_emoji="✅",
        ...     header_text="Algemene Regels AI (ARAI)",
        ...     priority=75
        ... )
    """

    def __init__(
        self,
        rule_prefix: str,
        module_id: str,
        module_name: str,
        header_emoji: str,
        header_text: str,
        priority: int,
    ):
        """
        Initialize generic JSON-based rules module.

        Args:
            rule_prefix: Prefix voor filtering (bijv. "ARAI", "CON-")
            module_id: Unieke identifier
            module_name: Display naam
            header_emoji: Emoji voor header
            header_text: Tekst voor header
            priority: Execution priority (60-75)
        """
        super().__init__(
            module_id=module_id, module_name=module_name, priority=priority
        )
        self.rule_prefix = rule_prefix
        self.header_emoji = header_emoji
        self.header_text = header_text
        self.include_examples = True

    def initialize(self, config: dict[str, Any]) -> None:
        """
        Initialize module met configuratie.

        Args:
            config: Module configuratie met optionele 'include_examples' boolean
        """
        self._config = config
        self.include_examples = config.get("include_examples", True)
        self._initialized = True
        logger.debug(
            f"JSONBasedRulesModule '{self.module_id}' geïnitialiseerd "
            f"(prefix={self.rule_prefix}, examples={self.include_examples})"
        )

    def validate_input(self, context: ModuleContext) -> tuple[bool, str | None]:
        """
        Deze module draait altijd.

        Args:
            context: Module context (niet gebruikt)

        Returns:
            Altijd (True, None)
        """
        return True, None

    def execute(self, context: ModuleContext) -> ModuleOutput:
        """
        Genereer validatieregels sectie voor specifieke prefix.

        Args:
            context: Module context (niet gebruikt door deze module)

        Returns:
            ModuleOutput met:
            - content: Markdown sectie met header + formatted rules
            - metadata: rules_count, include_examples, rule_prefix
        """
        try:
            sections = []

            # Header: ### {emoji} {text}:
            sections.append(f"### {self.header_emoji} {self.header_text}:")

            # Load toetsregels on-demand from cached singleton
            from toetsregels.cached_manager import get_cached_toetsregel_manager

            manager = get_cached_toetsregel_manager()
            all_rules = manager.get_all_regels()

            # Filter alleen regels met dit prefix
            filtered_rules = {
                k: v for k, v in all_rules.items() if k.startswith(self.rule_prefix)
            }

            # Sorteer regels alfabetisch
            sorted_rules = sorted(filtered_rules.items())

            # Format elke regel
            for regel_key, regel_data in sorted_rules:
                sections.extend(self._format_rule(regel_key, regel_data))

            # Combineer alle secties
            content = "\n".join(sections)

            return ModuleOutput(
                content=content,
                metadata={
                    "rules_count": len(filtered_rules),
                    "include_examples": self.include_examples,
                    "rule_prefix": self.rule_prefix,
                },
            )

        except Exception as e:
            logger.error(
                f"JSONBasedRulesModule '{self.module_id}' execution failed: {e}",
                exc_info=True,
            )
            return ModuleOutput(
                content="",
                metadata={"error": str(e)},
                success=False,
                error_message=f"Failed to generate {self.rule_prefix} rules: {e!s}",
            )

    def get_dependencies(self) -> list[str]:
        """
        Deze module heeft geen dependencies.

        Returns:
            Lege lijst
        """
        return []

    def _format_rule(self, regel_key: str, regel_data: dict) -> list[str]:
        """
        Formateer een regel uit JSON data naar markdown lines.

        Format:
        🔹 **REGEL-KEY - Naam**
        - Uitleg tekst
        - Toetsvraag: vraag tekst
          ✅ Goed voorbeeld
          ❌ Fout voorbeeld

        Args:
            regel_key: Regel identifier (bijv. "ARAI-01", "CON-02")
            regel_data: Regel data uit JSON met keys:
                - naam: Regel naam
                - uitleg: Uitleg tekst
                - toetsvraag: Toetsvraag tekst
                - goede_voorbeelden: List van goede voorbeelden
                - foute_voorbeelden: List van foute voorbeelden

        Returns:
            List van markdown lines voor deze regel
        """
        lines = []

        # Header met emoji: 🔹 **REGEL-KEY - Naam**
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

        # Voorbeelden (indien enabled in config)
        if self.include_examples:
            # Goede voorbeelden: ✅ tekst
            goede_voorbeelden = regel_data.get("goede_voorbeelden", [])
            for goed in goede_voorbeelden:
                lines.append(f"  ✅ {goed}")

            # Foute voorbeelden: ❌ tekst
            foute_voorbeelden = regel_data.get("foute_voorbeelden", [])
            for fout in foute_voorbeelden:
                lines.append(f"  ❌ {fout}")

        return lines
