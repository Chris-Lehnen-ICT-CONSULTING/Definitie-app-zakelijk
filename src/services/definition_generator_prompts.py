"""
Definition Generator Prompts Module.

Unified prompt building systeem dat alle prompt strategieën combineert:
- Legacy prompt builder (van definitie_generator)
- Services prompt building (van services implementatie)
- Advanced generation prompts (van generation implementatie)
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
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


@dataclass
class PromptTemplate:
    """Template voor prompt generatie."""

    name: str
    template: str
    variables: list[str]
    category: str  # "basic", "advanced", "specialized"
    confidence_threshold: float = 0.5

    def format(self, **kwargs) -> str:
        """Format template met gegeven variabelen."""
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            logger.warning(f"Missing variable {e} in template {self.name}")
            return self.template


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


class BasicPromptBuilder(PromptBuilder):
    """Basis prompt builder met eenvoudige templates."""

    def __init__(self):
        self.templates = self._load_basic_templates()

    def _load_basic_templates(self) -> dict[str, PromptTemplate]:
        """Laad basis prompt templates."""
        return {
            "default": PromptTemplate(
                name="default",
                template="""
Genereer een Nederlandse definitie voor het begrip: {begrip}

{context_section}

Zorg ervoor dat de definitie:
- Helder en eenduidig is
- Voldoet aan juridische standaarden
- Passend is voor de gegeven context
- Geen cirkelredeneringen bevat

Definitie:""",
                variables=["begrip", "context_section"],
                category="basic",
            ),
            "juridisch": PromptTemplate(
                name="juridisch",
                template="""
Genereer een juridische definitie voor het begrip: {begrip}

Juridische context:
{juridische_context}

Wettelijke context:
{wettelijke_context}

De definitie moet:
- Juridisch precies zijn
- Refereren aan relevante wettelijke kaders
- Geschikt zijn voor gebruik in juridische documenten
- Eenduidig interpreteerbaar zijn

Juridische definitie:""",
                variables=["begrip", "juridische_context", "wettelijke_context"],
                category="specialized",
            ),
            "proces": PromptTemplate(
                name="proces",
                template="""
Genereer een definitie voor het proces/procedure: {begrip}

Organisatorische context:
{organisatorische_context}

De definitie moet:
- De stappen of fasen beschrijven
- Duidelijk aangeven wat het doel is
- Geschikt zijn voor operationele gebruik
- Actionable zijn voor uitvoering

Proces definitie:""",
                variables=["begrip", "organisatorische_context"],
                category="specialized",
            ),
            # Ontologische categorie templates
            "ontologie_type": PromptTemplate(
                name="ontologie_type",
                template="""
Genereer een definitie voor het TYPE begrip: {begrip}

{context_section}

BELANGRIJK - Ontologische categorie: TYPE
De definitie moet beginnen met een formulering zoals:
- "{begrip} is een soort/type..."
- "{begrip} betreft een categorie van..."
- "{begrip} is een klasse van..."

De definitie moet:
- Het genus (bovenliggende categorie) benoemen
- De differentia (onderscheidende kenmerken) specificeren
- Duidelijk zijn over wat wel/niet tot deze categorie behoort

Type definitie:""",
                variables=["begrip", "context_section"],
                category="ontological",
            ),
            "ontologie_proces": PromptTemplate(
                name="ontologie_proces",
                template="""
Genereer een definitie voor het PROCES begrip: {begrip}

{context_section}

BELANGRIJK - Ontologische categorie: PROCES
De definitie moet beginnen met een formulering zoals:
- "{begrip} is een activiteit waarbij..."
- "{begrip} is het proces waarin..."
- "{begrip} behelst de handeling van..."

De definitie moet:
- De activiteit/handeling beschrijven
- Begin en eind aangeven
- Actoren en rollen specificeren
- Doel of uitkomst benoemen

Proces definitie:""",
                variables=["begrip", "context_section"],
                category="ontological",
            ),
            "ontologie_resultaat": PromptTemplate(
                name="ontologie_resultaat",
                template="""
Genereer een definitie voor het RESULTAAT begrip: {begrip}

{context_section}

BELANGRIJK - Ontologische categorie: RESULTAAT
De definitie moet beginnen met een formulering zoals:
- "{begrip} is het resultaat van..."
- "{begrip} is de uitkomst van..."
- "{begrip} betreft het gevolg van..."

De definitie moet:
- Het voorafgaande proces benoemen
- De vorm/nature van het resultaat specificeren
- Duidelijk zijn over wat het resultaat inhoudt
- Eventuele vervolgstappen aangeven

Resultaat definitie:""",
                variables=["begrip", "context_section"],
                category="ontological",
            ),
            "ontologie_exemplaar": PromptTemplate(
                name="ontologie_exemplaar",
                template="""
Genereer een definitie voor het EXEMPLAAR begrip: {begrip}

{context_section}

BELANGRIJK - Ontologische categorie: EXEMPLAAR
De definitie moet beginnen met een formulering zoals:
- "{begrip} is een exemplaar van..."
- "{begrip} is een specifieke instantie van..."
- "{begrip} betreft een concrete uitwerking van..."

De definitie moet:
- Het algemene type waartoe het behoort benoemen
- De specifieke kenmerken van dit exemplaar aangeven
- Duidelijk zijn over wat dit exemplaar uniek maakt
- Context specificeren waarin dit exemplaar relevant is

Exemplaar definitie:""",
                variables=["begrip", "context_section"],
                category="ontological",
            ),
        }

    def build_prompt(
        self, begrip: str, context: EnrichedContext, config: UnifiedGeneratorConfig
    ) -> str:
        """Build basic prompt gebaseerd op begrip type."""
        # Select appropriate template
        template = self._select_template(begrip, context)

        # Prepare template variables
        variables = self._prepare_template_variables(begrip, context, template)

        # Format prompt
        prompt = template.format(**variables)

        logger.debug(
            f"Basic prompt gebouwd met template '{template.name}' voor '{begrip}'"
        )
        return prompt

    def _select_template(self, begrip: str, context: EnrichedContext) -> PromptTemplate:
        """Selecteer juiste template gebaseerd op begrip en context."""
        begrip_lower = begrip.lower()

        # PRIORITEIT 1: Ontologische categorie uit 6-stappen protocol
        ontologische_categorie = context.metadata.get("ontologische_categorie")
        if ontologische_categorie:
            template_mapping = {
                "type": "ontologie_type",
                "proces": "ontologie_proces",
                "resultaat": "ontologie_resultaat",
                "exemplaar": "ontologie_exemplaar",
            }
            template_key = template_mapping.get(ontologische_categorie.lower())
            if template_key and template_key in self.templates:
                logger.info(
                    f"Gebruikelijke ontologische template: {template_key} voor categorie: {ontologische_categorie}"
                )
                return self.templates[template_key]

        # PRIORITEIT 2: Check for juridische context (legacy)
        juridische_items = context.base_context.get("juridisch", [])
        wettelijke_items = context.base_context.get("wettelijk", [])

        if juridische_items or wettelijke_items:
            return self.templates["juridisch"]

        # PRIORITEIT 3: Check for proces begrippen (legacy pattern matching)
        if any(
            word in begrip_lower
            for word in ["proces", "procedure", "methode", "workflow"]
        ):
            return self.templates["proces"]

        # PRIORITEIT 4: Default template
        return self.templates["default"]

    def _prepare_template_variables(
        self, begrip: str, context: EnrichedContext, template: PromptTemplate
    ) -> dict[str, str]:
        """Bereid template variabelen voor."""
        variables = {"begrip": begrip}

        # Context sections
        if "context_section" in template.variables:
            variables["context_section"] = self._build_context_section(context)

        if "juridische_context" in template.variables:
            juridische_items = context.base_context.get("juridisch", [])
            variables["juridische_context"] = (
                "\n".join(f"- {item}" for item in juridische_items)
                or "Geen specifieke juridische context"
            )

        if "wettelijke_context" in template.variables:
            wettelijke_items = context.base_context.get("wettelijk", [])
            variables["wettelijke_context"] = (
                "\n".join(f"- {item}" for item in wettelijke_items)
                or "Geen specifieke wettelijke context"
            )

        if "organisatorische_context" in template.variables:
            org_items = context.base_context.get("organisatorisch", [])
            variables["organisatorische_context"] = (
                "\n".join(f"- {item}" for item in org_items)
                or "Geen specifieke organisatorische context"
            )

        return variables

    def _build_context_section(self, context: EnrichedContext) -> str:
        """Bouw context sectie voor general template."""
        sections = []

        for context_type, items in context.base_context.items():
            if items:
                section_title = context_type.replace("_", " ").title()
                section_content = "\n".join(f"- {item}" for item in items)
                sections.append(f"{section_title}:\n{section_content}")

        # Add high-confidence sources
        for source in context.sources:
            if source.confidence > 0.8:
                sections.append(
                    f"{source.source_type.title()}:\n- {source.content[:200]}..."
                )

        return (
            "\n\n".join(sections)
            if sections
            else "Geen aanvullende context beschikbaar."
        )

    def get_strategy_name(self) -> str:
        return "basic"


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

        # Basic builder (always available)
        self.builders["basic"] = BasicPromptBuilder()

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
                f"Strategy '{strategy}' niet beschikbaar, fallback naar basic"
            )
            builder = self.builders["basic"]

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

        # Default naar basic
        return "basic"

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
