"""
Definition Generator Prompts Module.

Unified prompt building systeem dat alle prompt strategieën combineert:
- Legacy prompt builder (van definitie_generator)
- Services prompt building (van services implementatie)
- Advanced generation prompts (van generation implementatie)
"""

import logging
from abc import ABC, abstractmethod
from enum import Enum

from services.definition_generator_config import UnifiedGeneratorConfig
from services.definition_generator_context import EnrichedContext
from services.prompts.modular_prompt_builder import ModularPromptBuilder

logger = logging.getLogger(__name__)


class PromptStrategy(Enum):
    """Strategieën voor prompt building."""

    MODULAR = "modular"  # ModularPromptBuilder met 6 configureerbare componenten
    LEGACY = "legacy"  # Gebruik legacy prompt builder
    CONTEXT_AWARE = "context"  # Context-aware prompts
    RULE_BASED = "rule_based"  # Gebaseerd op toetsregels
    ADAPTIVE = "adaptive"  # Adaptieve prompts gebaseerd op begrip type
    HYBRID = "hybrid"  # Combinatie van alle strategieën


class PromptBuilder(ABC):
    """Abstract base class voor prompt builders."""

    @abstractmethod
    def build_prompt(
        self, begrip: str, context: EnrichedContext, config: UnifiedGeneratorConfig
    ) -> str:
        """Build prompt voor definitie generatie."""

    @abstractmethod
    def get_strategy_name(self) -> str:
        """Verkrijg naam van deze strategy."""


# ARCHIVED: LegacyPromptBuilder en ContextAwarePromptBuilder zijn gearchiveerd naar:
# docs/architectuur/definitie service/archief/2025-08-27-legacy-prompt-builders/
# Deze klassen werden niet gebruikt in runtime (zie analyse).
#
# MIGRATIE COMPLEET: Alle business logic is gemigreerd naar Enhanced ContextAwarenessModule
# in het modulaire systeem. De context scoring, confidence indicators, source formatting
# en adaptive prompt logic zijn nu geïntegreerd in de modulaire architectuur.


class UnifiedPromptBuilder:
    """
    Unified Prompt Builder die alle prompt strategieën combineert.

    Dit is de hoofdklasse die gebruikt wordt door de UnifiedDefinitionGenerator.
    """

    def __init__(self, config: UnifiedGeneratorConfig):
        self.config = config

        # Initialize available prompt builders
        self.builders: dict[str, PromptBuilder] = {}

        self._init_builders()

        logger.info(
            f"UnifiedPromptBuilder geïnitialiseerd met {len(self.builders)} strategies"
        )

    def _init_builders(self):
        """Initialiseer beschikbare prompt builders."""
        # Modular builder - enige actieve strategy
        self.builders["modular"] = ModularPromptBuilder()
        logger.info("ModularPromptBuilder geïnitialiseerd als primaire strategy")

        # ARCHIVED: Legacy en context-aware builders zijn gearchiveerd
        # Alle business logic is gemigreerd naar Enhanced ContextAwarenessModule

    def build_prompt(self, begrip: str, context: EnrichedContext) -> str:
        """
        Build prompt met de best passende strategy.

        Args:
            begrip: Het begrip om te definiëren
            context: Verrijkte context informatie

        Returns:
            Gegenereerde prompt string
        """
        # Select best strategy
        strategy = self._select_strategy(begrip, context)

        # Build prompt with selected strategy
        builder = self.builders.get(strategy)
        if not builder:
            logger.warning(
                f"Strategy '{strategy}' niet beschikbaar, fallback naar modular"
            )
            builder = self.builders.get("modular")
            if not builder:
                msg = "ModularPromptBuilder niet beschikbaar - kritieke fout"
                raise RuntimeError(msg)

        prompt = builder.build_prompt(begrip, context, self.config)

        logger.info(
            f"Prompt gebouwd met strategy '{builder.get_strategy_name()}' voor '{begrip}' ({len(prompt)} chars)"
        )

        return prompt

    def _select_strategy(self, begrip: str, context: EnrichedContext) -> str:
        """Selecteer beste prompt strategy voor deze situatie."""
        # ENIGE STRATEGIE: ModularPromptBuilder - alle andere zijn gearchiveerd
        # De Enhanced ContextAwarenessModule in het modulaire systeem handelt
        # automatisch alle context adaptatie af
        return "modular"

    def get_available_strategies(self) -> list[str]:
        """Verkrijg lijst van beschikbare strategies."""
        return list(self.builders.keys())

    def force_strategy(self, strategy: str) -> bool:
        """Forceer gebruik van specifieke strategy (voor testing)."""
        if strategy in self.builders:
            self._forced_strategy = strategy
            return True
        return False

    def clear_forced_strategy(self):
        """Clear geforceerde strategy."""
        if hasattr(self, "_forced_strategy"):
            delattr(self, "_forced_strategy")


# Backwards compatibility alias
DefinitionGeneratorPrompts = UnifiedPromptBuilder
