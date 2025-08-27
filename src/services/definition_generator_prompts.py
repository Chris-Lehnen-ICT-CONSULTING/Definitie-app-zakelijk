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


class LegacyPromptBuilder(PromptBuilder):
    """Legacy prompt builder (van definitie_generator implementatie)."""

    def __init__(self):
        # Import legacy prompt builder
        try:
            from prompt_builder.prompt_builder import PromptBouwer, PromptConfiguratie

            self._legacy_builder_class = PromptBouwer
            self._legacy_config_class = PromptConfiguratie
            self._legacy_available = True
        except ImportError:
            logger.warning("Legacy prompt builder niet beschikbaar")
            self._legacy_available = False

    def build_prompt(
        self, begrip: str, context: EnrichedContext, config: UnifiedGeneratorConfig
    ) -> str:
        """Build prompt met legacy prompt builder."""
        if not self._legacy_available:
            msg = "Legacy prompt builder niet beschikbaar"
            raise ValueError(msg)

        try:
            # Convert EnrichedContext naar legacy format
            legacy_context = self._convert_to_legacy_context(context)

            # Get web explanation if available
            web_uitleg = ""
            for source in context.sources:
                if source.source_type == "web_lookup" and source.confidence > 0.7:
                    web_uitleg = source.content
                    break

            # Create legacy configuration
            configuratie = self._legacy_config_class(
                begrip=begrip, context_dict=legacy_context, web_uitleg=web_uitleg
            )

            # Build prompt
            bouwer = self._legacy_builder_class(configuratie)
            prompt = bouwer.bouw_prompt()

            logger.debug(f"Legacy prompt gebouwd voor '{begrip}' ({len(prompt)} chars)")
            return prompt

        except Exception as e:
            logger.error(f"Legacy prompt building mislukt: {e}")
            # Fallback to basic prompt
            return self._build_fallback_prompt(begrip, context)

    def _convert_to_legacy_context(
        self, context: EnrichedContext
    ) -> dict[str, list[str]]:
        """Converteer EnrichedContext naar legacy context formaat."""
        # Filter out non-legacy context types
        legacy_types = ["organisatorisch", "juridisch", "wettelijk", "domein"]
        return {
            key: value
            for key, value in context.base_context.items()
            if key in legacy_types
        }

    def _build_fallback_prompt(self, begrip: str, context: EnrichedContext) -> str:
        """Fallback prompt als legacy builder faalt."""
        context_text = context.get_all_context_text()
        return f"""
Genereer een definitie voor het begrip: {begrip}

Context informatie:
{context_text}

Zorg voor een heldere, eenduidige definitie die voldoet aan de Nederlandse juridische standaarden.
"""

    def get_strategy_name(self) -> str:
        return "legacy"


class ContextAwarePromptBuilder(PromptBuilder):
    """Context-aware prompt builder die adapteert aan context rijkheid."""

    def build_prompt(
        self, begrip: str, context: EnrichedContext, config: UnifiedGeneratorConfig
    ) -> str:
        """Build context-aware prompt."""
        # Analyze context richness
        context_score = self._calculate_context_score(context)

        # Select prompt strategy based on context richness
        if context_score >= 0.8:
            return self._build_rich_context_prompt(begrip, context)
        if context_score >= 0.5:
            return self._build_moderate_context_prompt(begrip, context)
        return self._build_minimal_context_prompt(begrip, context)

    def _calculate_context_score(self, context: EnrichedContext) -> float:
        """Bereken context rijkheid score (0.0 - 1.0)."""
        score = 0.0

        # Base context contribution (max 0.3)
        total_base_items = sum(len(items) for items in context.base_context.values())
        score += min(total_base_items / 10, 0.3)

        # Sources contribution (max 0.4)
        source_score = sum(source.confidence for source in context.sources) / max(
            len(context.sources), 1
        )
        score += source_score * 0.4

        # Expanded terms contribution (max 0.2)
        if context.expanded_terms:
            score += min(len(context.expanded_terms) / 5, 0.2)

        # Confidence scores contribution (max 0.1)
        if context.confidence_scores:
            avg_confidence = sum(context.confidence_scores.values()) / len(
                context.confidence_scores
            )
            score += avg_confidence * 0.1

        return min(score, 1.0)

    def _build_rich_context_prompt(self, begrip: str, context: EnrichedContext) -> str:
        """Build prompt voor rijke context."""
        return f"""
Als expert definitie-schrijver, genereer een uitgebreide definitie voor: {begrip}

UITGEBREIDE CONTEXT ANALYSE:
{self._format_detailed_context(context)}

DEFINITITIE VEREISTEN:
- Integreer alle relevante context aspecten
- Zorg voor juridische precisie waar van toepassing
- Maak gebruik van de beschikbare achtergrond informatie
- Zorg voor eenduidige, professionele bewoordingen
- Vermijd cirkelredeneringen en vague termen

GEDETAILLEERDE DEFINITIE:"""

    def _build_moderate_context_prompt(
        self, begrip: str, context: EnrichedContext
    ) -> str:
        """Build prompt voor matige context."""
        return f"""
Genereer een definitie voor het begrip: {begrip}

CONTEXT INFORMATIE:
{context.get_all_context_text()}

AFKORTINGEN:
{self._format_abbreviations(context)}

Zorg voor een heldere definitie die rekening houdt met de beschikbare context.

DEFINITIE:"""

    def _build_minimal_context_prompt(
        self, begrip: str, context: EnrichedContext
    ) -> str:
        """Build prompt voor minimale context."""
        return f"""
Genereer een Nederlandse definitie voor: {begrip}

{context.get_all_context_text() or 'Geen specifieke context beschikbaar.'}

Zorg voor een heldere, eenduidige definitie.

DEFINITIE:"""

    def _format_detailed_context(self, context: EnrichedContext) -> str:
        """Format gedetailleerde context voor rijke prompts."""
        sections = []

        # Base context with categories
        for context_type, items in context.base_context.items():
            if items:
                sections.append(f"{context_type.upper()}:")
                for item in items:
                    sections.append(f"  • {item}")

        # Sources with confidence scores
        if context.sources:
            sections.append("ADDITIONELE BRONNEN:")
            for source in context.sources:
                confidence_indicator = (
                    "🔴"
                    if source.confidence < 0.5
                    else "🟡" if source.confidence < 0.8 else "🟢"
                )
                sections.append(
                    f"  {confidence_indicator} {source.source_type.title()} ({source.confidence:.2f}): {source.content[:150]}..."
                )

        # Expanded terms
        if context.expanded_terms:
            sections.append("AFKORTINGEN & UITBREIDINGEN:")
            for abbr, expansion in context.expanded_terms.items():
                sections.append(f"  • {abbr} = {expansion}")

        return "\n".join(sections)

    def _format_abbreviations(self, context: EnrichedContext) -> str:
        """Format afkortingen voor matige prompts."""
        if not context.expanded_terms:
            return "Geen afkortingen gedetecteerd."

        return "\n".join(
            f"- {abbr}: {expansion}"
            for abbr, expansion in context.expanded_terms.items()
        )

    def get_strategy_name(self) -> str:
        return "context_aware"


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
        # Modular builder (nieuwe prioriteit)
        self.builders["modular"] = ModularPromptBuilder()
        logger.info("ModularPromptBuilder toegevoegd aan strategies")

        # Legacy builder
        try:
            self.builders["legacy"] = LegacyPromptBuilder()
        except Exception as e:
            logger.warning(f"Legacy prompt builder niet beschikbaar: {e}")

        # Context-aware builder
        self.builders["context_aware"] = ContextAwarePromptBuilder()

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
                f"Strategy '{strategy}' niet beschikbaar, fallback naar context-aware"
            )
            builder = self.builders.get("context_aware")
            if not builder:
                msg = "Geen beschikbare prompt builders gevonden"
                raise RuntimeError(msg)

        prompt = builder.build_prompt(begrip, context, self.config)

        logger.info(
            f"Prompt gebouwd met strategy '{builder.get_strategy_name()}' voor '{begrip}' ({len(prompt)} chars)"
        )

        return prompt

    def _select_strategy(self, begrip: str, context: EnrichedContext) -> str:
        """Selecteer beste prompt strategy voor deze situatie."""

        # PRIORITEIT 1: Modular builder - nieuwe standaard voor alle scenarios
        if "modular" in self.builders:
            logger.info(
                f"ModularPromptBuilder beschikbaar - gebruik modular strategy voor '{begrip}'"
            )
            return "modular"

        # Voor rijke context, gebruik context-aware
        if (
            len(context.sources) >= 2
            or context.metadata.get("avg_confidence", 0.0) > 0.8
        ):
            return "context_aware"

        # Default naar context-aware
        return "context_aware"

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
