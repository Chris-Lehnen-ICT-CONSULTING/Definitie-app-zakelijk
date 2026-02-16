"""
Enhanced Context Awareness Module - Intelligent context processing met adaptieve formatting.

Deze module integreert alle business logic van de Context Aware builder:
1. Context richness scoring (0.0-1.0)
2. Dynamische prompt aanpassing op basis van context kwaliteit
3. Confidence indicators (high/medium/low levels)
4. Advanced source formatting
5. Abbreviation/expansion handling
6. Verwerking van V2-contexten (organisatorisch, juridisch, wettelijk)
"""

import logging
from typing import Any

from .base_module import BasePromptModule, ModuleContext, ModuleOutput

logger = logging.getLogger(__name__)


class ContextAwarenessModule(BasePromptModule):
    """
    Enhanced module voor intelligente context verwerking.

    Combineert alle context processing logic in één module:
    - Context richness scoring
    - Adaptive formatting based on context quality
    - Source confidence visualization
    - Abbreviation handling
    - V2-contextverwerking: organisatorisch/juridisch/wettelijk (geen legacy 'domein')

    DEF-188: Added IMPLICIT_CONTEXT_MECHANISMS teaching GPT-4 HOW to embed context.
    """

    # DEF-188: 3 Mechanisms for implicit context processing
    IMPLICIT_CONTEXT_MECHANISMS = """
📌 HOE CONTEXT IMPLICIET VERWERKEN (3 Mechanismen):

**MECHANISME 1 - VOCABULAIRE:**
Gebruik domein-specifieke termen.
❌ "persoon" → ✅ "verdachte" (strafrechtelijk)
❌ "gebouw" → ✅ "penitentiaire inrichting" (DJI)
❌ "straf" → ✅ "sanctie" (formeel juridisch)

**MECHANISME 2 - SCOPE:**
Vernauw begrippen met domein-qualifiers.
❌ "regels" → ✅ "gedragsregels"
❌ "beslissing" → ✅ "beschikking"
❌ "procedure" → ✅ "formele procedure"

**MECHANISME 3 - RELATIES:**
Refereer context-specifieke verbanden.
❌ "herhaling" → ✅ "recidive"
❌ "begeleiding" → ✅ "reclasseringstoezicht"
❌ "functionaris" → ✅ "officier van justitie"

🧪 TEST: Kan een expert de context raden ZONDER label?
"""

    def __init__(self):
        """Initialize de enhanced context awareness module."""
        super().__init__(
            module_id="context_awareness",
            module_name="Enhanced Context Processing Module",
            priority=70,  # Hoge prioriteit - context is belangrijk
        )
        self.adaptive_formatting = True
        self.confidence_indicators = True
        self.include_abbreviations = True

    def initialize(self, config: dict[str, Any]) -> None:
        """
        Initialize module met configuratie.

        Args:
            config: Module configuratie
        """
        self._config = config
        self.adaptive_formatting = config.get("adaptive_formatting", True)
        self.confidence_indicators = config.get("confidence_indicators", True)
        self.include_abbreviations = config.get("include_abbreviations", True)
        self._initialized = True
        logger.debug(
            f"Enhanced ContextAwarenessModule geïnitialiseerd "
            f"(adaptive={self.adaptive_formatting}, confidence={self.confidence_indicators})"
        )

    def validate_input(self, context: ModuleContext) -> tuple[bool, str | None]:
        """
        Valideer input - deze module werkt altijd (ook bij geen context).

        Args:
            context: Module context

        Returns:
            (True, None) - module werkt altijd
        """
        # Deze module werkt altijd - zelfs bij geen context
        # Dan geeft het aan dat er geen context beschikbaar is
        return True, None

    def execute(self, context: ModuleContext) -> ModuleOutput:
        """
        Genereer adaptive context sectie gebaseerd op context richness.

        Args:
            context: Module context

        Returns:
            ModuleOutput met adaptive context formatting
        """
        try:
            # Bereken context richness score
            context_score = self._calculate_context_score(context.enriched_context)

            # Sla score op voor andere modules
            context.set_shared("context_richness_score", context_score)

            # Bepaal formatting strategie op basis van score
            if context_score >= 0.8:
                content = self._build_rich_context_section(context)
                formatting_level = "rich"
            elif context_score >= 0.5:
                content = self._build_moderate_context_section(context)
                formatting_level = "moderate"
            else:
                content = self._build_minimal_context_section(context)
                formatting_level = "minimal"

            # Extract en deel traditionele context voor andere modules
            self._share_traditional_context(context)

            return ModuleOutput(
                content=content,
                metadata={
                    "context_score": context_score,
                    "formatting_level": formatting_level,
                    "adaptive_formatting": self.adaptive_formatting,
                    "sources_count": len(context.enriched_context.sources),
                    "base_context_items": sum(
                        len(items)
                        for items in context.enriched_context.base_context.values()
                    ),
                    "expanded_terms_count": len(
                        context.enriched_context.expanded_terms or {}
                    ),
                },
            )

        except Exception as e:
            logger.error(
                f"Enhanced ContextAwarenessModule execution failed: {e}", exc_info=True
            )
            return ModuleOutput(
                content=self._build_fallback_context_section(),
                metadata={"error": str(e), "fallback_used": True},
                success=False,
                error_message=f"Failed to generate enhanced context section: {e!s}",
            )

    def get_dependencies(self) -> list[str]:
        """
        Deze module heeft geen dependencies.

        Returns:
            Lege lijst
        """
        return []

    def _calculate_context_score(self, enriched_context) -> float:
        """
        Bereken context richheid score (0.0 - 1.0).

        Gebaseerd op ContextAwarePromptBuilder logic.

        Args:
            enriched_context: EnrichedContext object

        Returns:
            Score tussen 0.0 en 1.0
        """
        score = 0.0

        # Base context contribution (max 0.3)
        total_base_items = sum(
            len(items) for items in enriched_context.base_context.values()
        )
        score += min(total_base_items / 10, 0.3)

        # Sources contribution (max 0.4)
        if enriched_context.sources:
            source_score = sum(
                source.confidence for source in enriched_context.sources
            ) / len(enriched_context.sources)
            score += source_score * 0.4

        # Expanded terms contribution (max 0.2)
        if enriched_context.expanded_terms:
            score += min(len(enriched_context.expanded_terms) / 5, 0.2)

        # Confidence scores contribution (max 0.1)
        if (
            hasattr(enriched_context, "confidence_scores")
            and enriched_context.confidence_scores
        ):
            avg_confidence = sum(enriched_context.confidence_scores.values()) / len(
                enriched_context.confidence_scores
            )
            score += avg_confidence * 0.1

        return min(score, 1.0)

    def _build_rich_context_section(self, context: ModuleContext) -> str:
        """
        Build uitgebreide context sectie voor rijke context (score ≥ 0.8).

        Args:
            context: Module context

        Returns:
            Uitgebreide context sectie
        """
        sections = []
        enriched_context = context.enriched_context

        sections.append("📊 UITGEBREIDE CONTEXT ANALYSE:")
        sections.append(
            "⚠️ VERPLICHT: Gebruik onderstaande specifieke context om de definitie te formuleren voor deze organisatorische, juridische en wettelijke setting. Maak de definitie contextspecifiek zonder de context expliciet te benoemen."
        )
        sections.append("")

        # Base context met categorieën
        sections.extend(
            self._format_detailed_base_context(enriched_context.base_context)
        )

        # Sources met confidence indicators
        if enriched_context.sources:
            sections.append("")
            sections.extend(
                self._format_sources_with_confidence(enriched_context.sources)
            )

        # Expanded terms
        if self.include_abbreviations and enriched_context.expanded_terms:
            sections.append("")
            sections.extend(
                self._format_abbreviations_detailed(enriched_context.expanded_terms)
            )

        # DEF-188: Add implicit context mechanisms
        sections.append("")
        sections.append(self.IMPLICIT_CONTEXT_MECHANISMS.strip())

        return "\n".join(sections)

    def _build_moderate_context_section(self, context: ModuleContext) -> str:
        """
        Build standaard context sectie voor matige context (0.5 ≤ score < 0.8).

        Args:
            context: Module context

        Returns:
            Standaard context sectie
        """
        sections = []
        enriched_context = context.enriched_context

        sections.append("📌 VERPLICHTE CONTEXT INFORMATIE:")
        sections.append(
            "⚠️ BELANGRIJKE INSTRUCTIE: Verwerk de onderstaande context IMPLICIET in de definitie. "
            "Maak de definitie specifiek voor deze context door je woordkeuze en formulering aan te passen, "
            "maar VERMIJD het expliciet noemen van contextnamen (zoals organisatienamen, wettelijke kaders, etc.)."
        )
        sections.append("")

        # Basis context formatting
        context_text = enriched_context.get_all_context_text()
        if context_text:
            sections.append("🎯 SPECIFIEKE CONTEXT VOOR DEZE DEFINITIE:")
            sections.append(context_text)
        else:
            sections.append("Geen specifieke context beschikbaar.")

        # Afkortingen indien beschikbaar
        if self.include_abbreviations and enriched_context.expanded_terms:
            sections.append("")
            sections.append("AFKORTINGEN:")
            sections.extend(
                self._format_abbreviations_simple(enriched_context.expanded_terms)
            )

        # DEF-188: Add implicit context mechanisms
        sections.append("")
        sections.append(self.IMPLICIT_CONTEXT_MECHANISMS.strip())

        return "\n".join(sections)

    def _build_minimal_context_section(self, context: ModuleContext) -> str:
        """
        Build minimale context sectie voor beperkte context (score < 0.5).

        Args:
            context: Module context

        Returns:
            Minimale context sectie
        """
        enriched_context = context.enriched_context
        context_text = enriched_context.get_all_context_text()

        # DEF-188: Add mechanisms even for minimal context
        mechanisms = f"\n\n{self.IMPLICIT_CONTEXT_MECHANISMS.strip()}"

        if context_text:
            base = f"📍 VERPLICHTE CONTEXT: {context_text}\n⚠️ INSTRUCTIE: Formuleer de definitie specifiek voor bovenstaande organisatorische, juridische en wettelijke context zonder deze expliciet te benoemen."
            return base + mechanisms

        return "📍 Context: Geen specifieke context beschikbaar." + mechanisms

    def _format_detailed_base_context(self, base_context: dict) -> list[str]:
        """
        Format base context met categorieën voor rijke context.

        Args:
            base_context: Dictionary met base context

        Returns:
            Lijst van geformatteerde context regels
        """
        sections = []

        for context_type, items in base_context.items():
            if items:
                sections.append(f"{context_type.upper()}:")
                if isinstance(items, list):
                    for item in items:
                        sections.append(f"  • {item}")
                else:
                    sections.append(f"  • {items}")

        return sections

    def _format_sources_with_confidence(self, sources) -> list[str]:
        """
        Format sources met confidence indicators.

        Args:
            sources: Lijst van source objecten

        Returns:
            Lijst van geformatteerde source regels
        """
        sections = ["ADDITIONELE BRONNEN:"]

        for source in sources:
            level = self._confidence_to_level(source.confidence)
            sections.append(
                f"  [{level}] {source.source_type.title()} "
                f"(confidence={source.confidence:.2f}): {source.content[:150]}..."
            )

        return sections

    @staticmethod
    def _confidence_to_level(confidence: float) -> str:
        """Vertaal confidence naar level label (DEF-315)."""
        if confidence >= 0.8:
            return "high"
        if confidence >= 0.5:
            return "medium"
        return "low"

    def _format_abbreviations_detailed(self, expanded_terms: dict) -> list[str]:
        """
        Format afkortingen voor rijke context.

        Args:
            expanded_terms: Dictionary met afkortingen

        Returns:
            Lijst van geformatteerde afkortingen
        """
        sections = ["AFKORTINGEN & UITBREIDINGEN:"]
        for abbr, expansion in expanded_terms.items():
            sections.append(f"  • {abbr} = {expansion}")

        return sections

    def _format_abbreviations_simple(self, expanded_terms: dict) -> list[str]:
        """
        Format afkortingen voor matige context.

        Args:
            expanded_terms: Dictionary met afkortingen

        Returns:
            Lijst van geformatteerde afkortingen
        """
        if not expanded_terms:
            return ["Geen afkortingen gedetecteerd."]

        return [f"- {abbr}: {expansion}" for abbr, expansion in expanded_terms.items()]

    def _share_traditional_context(self, context: ModuleContext) -> None:
        """
        Deel alle actieve context types voor andere modules.

        EPIC-010: Harmonisatie van context handling
        - Verwijderd: legacy 'domein' field (gebruik juridische_context)
        - Toegevoegd: juridical_contexts en legal_basis_contexts sharing

        Args:
            context: Module context
        """
        base_context = context.enriched_context.base_context

        # Extract alle ACTIEVE contexten (domein is legacy en wordt niet meer gebruikt)
        org_contexts = self._extract_contexts(base_context.get("organisatorisch"))
        jur_contexts = self._extract_contexts(base_context.get("juridisch"))
        wet_contexts = self._extract_contexts(base_context.get("wettelijk"))

        # Deel alle actieve contexten voor andere modules
        if org_contexts:
            context.set_shared("organization_contexts", org_contexts)
        if jur_contexts:
            context.set_shared("juridical_contexts", jur_contexts)
        if wet_contexts:
            context.set_shared("legal_basis_contexts", wet_contexts)

        # Legacy domein wordt NIET meer gedeeld (EPIC-010)

    def _extract_contexts(self, context_value: Any) -> list[str]:
        """
        Extract context lijst uit verschillende input formaten.

        Backwards compatibility method.

        Args:
            context_value: Context waarde (bool, str, list, etc.)

        Returns:
            Lijst van context strings
        """
        if not context_value:
            return []

        # Handle verschillende input types
        if isinstance(context_value, bool):
            # Legacy support: True betekent geen specifieke context
            return []
        if isinstance(context_value, str):
            return [context_value]
        if isinstance(context_value, list):
            return [str(item) for item in context_value if item]

        logger.warning(
            f"Onbekend context type: {type(context_value)} - {context_value}"
        )
        return []

    def _build_fallback_context_section(self) -> str:
        """
        Build fallback context sectie bij errors.

        Returns:
            Fallback context sectie
        """
        return "📍 Context: Context verwerking gefaald, geen specifieke context beschikbaar."
