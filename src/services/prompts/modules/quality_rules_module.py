"""
Quality Rules Module - Implementeert alle validatieregels voor definities.

Deze module is verantwoordelijk voor:
1. Alle CON, ESS, INT, SAM, STR en ARAI validatieregels
2. Gestructureerde presentatie met voorbeelden
3. Context-aware regel selectie
4. JSON-based rule loading voor consistency
"""

import logging
from typing import Any

from config.config_loader import laad_toetsregels
from .base_module import BasePromptModule, ModuleContext, ModuleOutput

logger = logging.getLogger(__name__)


class QualityRulesModule(BasePromptModule):
    """
    Module voor alle validatie/toetsregels.

    Genereert de complete set van validatieregels die gebruikt
    moeten worden bij het definiëren van begrippen.
    """

    def __init__(self):
        """Initialize de quality rules module."""
        super().__init__(
            module_id="quality_rules",
            module_name="Validation Rules Module",
            priority=70,  # Belangrijke prioriteit - validatie regels
        )
        self.include_arai_rules = True
        self.include_examples = True
        self._toetsregels = None  # Lazy loading van toetsregels

    def initialize(self, config: dict[str, Any]) -> None:
        """
        Initialize module met configuratie.

        Args:
            config: Module configuratie
        """
        self._config = config
        self.include_arai_rules = config.get("include_arai_rules", True)
        self.include_examples = config.get("include_examples", True)
        self._initialized = True
        
        # Load toetsregels from JSON
        try:
            self._toetsregels = laad_toetsregels()
            logger.info(
                f"QualityRulesModule geïnitialiseerd met {len(self._toetsregels)} regels "
                f"(arai={self.include_arai_rules}, examples={self.include_examples})"
            )
        except Exception as e:
            logger.error(f"Fout bij laden toetsregels: {e}")
            self._toetsregels = {}
            raise

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
        Genereer alle validatieregels.

        Args:
            context: Module context

        Returns:
            ModuleOutput met validatieregels
        """
        try:
            # Bouw validatieregels sectie uit JSON data
            sections = []
            
            # Start sectie
            sections.append("### ✅ Richtlijnen voor de definitie:")
            
            # Filter en sorteer regels
            filtered_rules = self._filter_rules()
            rule_count = len(filtered_rules)
            
            # Formateer elke regel uit JSON data
            for regel_key, regel_data in filtered_rules.items():
                sections.extend(self._format_rule(regel_key, regel_data))
            
            # Combineer secties
            content = "\n".join(sections)
            
            return ModuleOutput(
                content=content,
                metadata={
                    "total_rules": rule_count,
                    "include_arai": self.include_arai_rules,
                    "include_examples": self.include_examples,
                    "rules_from_json": True,
                },
            )

        except Exception as e:
            logger.error(f"QualityRulesModule execution failed: {e}", exc_info=True)
            return ModuleOutput(
                content="",
                metadata={"error": str(e)},
                success=False,
                error_message=f"Failed to generate quality rules: {e!s}",
            )

    def get_dependencies(self) -> list[str]:
        """
        Deze module heeft geen dependencies.

        Returns:
            Lege lijst
        """
        return []
    
    def _filter_rules(self) -> dict[str, dict]:
        """
        Filter toetsregels op basis van configuratie.
        
        Returns:
            Gefilterde regels dictionary
        """
        if not self._toetsregels:
            return {}
            
        # Alle regels zijn welkom, geen filtering zoals legacy systeem
        filtered = {}
        
        for rule_key, rule_data in self._toetsregels.items():
            # Skip ARAI regels als niet enabled
            if not self.include_arai_rules and rule_key.startswith("ARAI"):
                continue
            filtered[rule_key] = rule_data
            
        return filtered
    
    def _format_rule(self, regel_key: str, regel_data: dict) -> list[str]:
        """
        Formateer een regel uit JSON data naar mooie prompt text.
        
        Args:
            regel_key: Regel identifier (bijv. 'CON-01')
            regel_data: Regel data uit JSON
        
        Returns:
            Lijst van geformatteerde regel regels
        """
        lines = []
        
        # Header met emoji
        naam = regel_data.get('naam', 'Onbekende regel')
        lines.append(f"🔹 **{regel_key} - {naam}**")
        
        # Uitleg
        uitleg = regel_data.get('uitleg', '')
        if uitleg:
            lines.append(f"- {uitleg}")
        
        # Toetsvraag
        toetsvraag = regel_data.get('toetsvraag', '')
        if toetsvraag:
            lines.append(f"- Toetsvraag: {toetsvraag}")
        
        # Voorbeelden (indien enabled)
        if self.include_examples:
            # Goede voorbeelden
            goede_voorbeelden = regel_data.get('goede_voorbeelden', [])
            for goed in goede_voorbeelden:
                lines.append(f"  ✅ {goed}")
            
            # Foute voorbeelden
            foute_voorbeelden = regel_data.get('foute_voorbeelden', [])
            for fout in foute_voorbeelden:
                lines.append(f"  ❌ {fout}")
        
        return lines
