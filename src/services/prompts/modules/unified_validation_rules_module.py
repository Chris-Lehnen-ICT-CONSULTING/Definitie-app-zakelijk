"""
Unified Validation Rules Module - Consolideert alle validatie regel categorieën.

Deze module combineert alle validatie regels (ARAI, CON, ESS, SAM, INT)
in één module om cognitive load te verminderen (DEF-127).

Vervangt:
- arai_rules_module.py
- con_rules_module.py
- ess_rules_module.py (behalve semantic categorisation)
- integrity_rules_module.py
- sam_rules_module.py
"""

import logging
from typing import Any

from .base_module import BasePromptModule, ModuleContext, ModuleOutput

logger = logging.getLogger(__name__)


class UnifiedValidationRulesModule(BasePromptModule):
    """
    Unified module voor alle validatie regel categorieën.

    Consolideert ARAI, CON, ESS, SAM, en INT regels in één module
    om het aantal concepten te verminderen van 19 naar <15 (DEF-127).
    """

    # Mapping van categorieën naar emoji's voor visuele hiërarchie
    CATEGORY_EMOJIS = {
        "ARAI": "📏",  # Algemene Richtlijnen
        "CON": "🌐",  # Context
        "ESS": "🎯",  # Essentie
        "SAM": "🔗",  # Samenhang
        "INT": "✅",  # Integriteit
    }

    CATEGORY_NAMES = {
        "ARAI": "Algemene Richtlijnen",
        "CON": "Context Regels",
        "ESS": "Essentie Regels",
        "SAM": "Samenhang Regels",
        "INT": "Integriteit Regels",
    }

    def __init__(self, categories: list[str] | None = None):
        """
        Initialize de unified validation rules module.

        Args:
            categories: Lijst van categorieën om te laden.
                       Default: alle categorieën.
        """
        super().__init__(
            module_id="unified_validation_rules",
            module_name="Unified Validation Rules",
            priority=70,  # Hoge prioriteit voor validatie regels
        )

        # Default to all categories if none specified
        self.categories = categories or ["ARAI", "CON", "ESS", "SAM", "INT"]
        self.include_examples = True

    def initialize(self, config: dict[str, Any]) -> None:
        """
        Initialize module met configuratie.

        Args:
            config: Module configuratie
        """
        self._config = config
        self.include_examples = config.get("include_examples", True)

        # Allow override of categories via config
        if "categories" in config:
            self.categories = config["categories"]

        self._initialized = True
        logger.debug(
            f"UnifiedValidationRulesModule initialized with categories: {self.categories}"
        )

    def validate_input(self, context: ModuleContext) -> tuple[bool, str | None]:
        """Validatie regels draaien altijd."""
        return True, None

    def execute(self, context: ModuleContext) -> ModuleOutput:
        """
        Genereer alle validatie regels voor de geconfigureerde categorieën.

        Returns:
            ModuleOutput met alle validatie regels
        """
        try:
            sections = []
            sections.append("## 📋 Validatie Regels\n")

            # Load toetsregels on-demand from cached singleton
            from toetsregels.cached_manager import get_cached_toetsregel_manager

            manager = get_cached_toetsregel_manager()

            # Process each category
            for category in self.categories:
                if category not in self.CATEGORY_EMOJIS:
                    logger.warning(f"Unknown category: {category}")
                    continue

                # Get rules for this category
                category_rules = self._get_category_rules(manager, category)
                if not category_rules:
                    continue

                # Add category header
                emoji = self.CATEGORY_EMOJIS[category]
                name = self.CATEGORY_NAMES[category]
                sections.append(f"\n### {emoji} {name} ({category})\n")

                # Add rules for this category
                for regel_key, regel_data in category_rules.items():
                    rule_lines = self._format_rule(regel_key, regel_data)
                    sections.extend(rule_lines)
                    sections.append("")  # Empty line between rules

            # Combine all sections
            content = "\n".join(sections)

            return ModuleOutput(
                content=content,
                metadata={
                    "categories": self.categories,
                    "rules_included": len(category_rules) if category_rules else 0,
                },
            )

        except Exception as e:
            logger.error(f"Error generating unified validation rules: {e}")
            return ModuleOutput(content="", metadata={"error": str(e)})

    def get_dependencies(self) -> list[str]:
        """Deze module heeft geen dependencies."""
        return []

    def _get_category_rules(self, manager, category: str) -> dict:
        """
        Haal alle regels op voor een specifieke categorie.

        Args:
            manager: Toetsregel manager instance
            category: Categorie code (ARAI, CON, etc.)

        Returns:
            Dictionary met regels voor deze categorie
        """
        try:
            # Get all rules and filter by category
            all_rules = {}

            # Load rules based on category prefix
            if category == "ARAI":
                # ARAI rules have different numbering (ARAI-01, etc.)
                for i in range(1, 10):  # Assuming max 9 ARAI rules
                    regel_key = f"ARAI-{i:02d}"
                    regel = manager.load_regel(regel_key)
                    if regel:
                        all_rules[regel_key] = regel

            else:
                # Other categories use 3-letter prefix (CON-01, ESS-02, etc.)
                for i in range(1, 20):  # Assuming max 19 rules per category
                    regel_key = f"{category}-{i:02d}"
                    regel = manager.load_regel(regel_key)
                    if regel:
                        all_rules[regel_key] = regel

            return all_rules

        except Exception as e:
            logger.error(f"Error loading {category} rules: {e}")
            return {}

    def _format_rule(self, regel_key: str, regel_data: dict) -> list[str]:
        """
        Formatteer een regel uit JSON data.

        Args:
            regel_key: Regel identifier
            regel_data: Regel data dictionary

        Returns:
            Lijst van geformatteerde regel regels
        """
        lines = []

        # Header met emoji
        naam = regel_data.get("naam", "Onbekende regel")
        lines.append(f"**{regel_key}** - {naam}")

        # Beschrijving
        if beschrijving := regel_data.get("beschrijving"):
            lines.append(f"- {beschrijving}")

        # Instructies voor AI
        if instructies := regel_data.get("ai_instructies"):
            if isinstance(instructies, list):
                for instructie in instructies:
                    lines.append(f"  • {instructie}")
            else:
                lines.append(f"  • {instructies}")

        # Voorbeelden (indien enabled)
        if self.include_examples and (voorbeelden := regel_data.get("voorbeelden")):
            if goed := voorbeelden.get("goed"):
                lines.append(f"  ✓ Goed: {goed[0] if isinstance(goed, list) else goed}")
            if fout := voorbeelden.get("fout"):
                lines.append(f"  ✗ Fout: {fout[0] if isinstance(fout, list) else fout}")

        return lines
