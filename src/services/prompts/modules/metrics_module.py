"""
Metrics Module - Meet en rapporteer kwaliteitsmetrieken voor definities.

Deze module is verantwoordelijk voor:
1. Character count tracking
2. Complexity scoring
3. Rule compliance metrics
4. Quality indicators
"""

import logging
import re
from typing import Any

from .base_module import BasePromptModule, ModuleContext, ModuleOutput

logger = logging.getLogger(__name__)


class MetricsModule(BasePromptModule):
    """
    Module voor kwaliteitsmetrieken en scoring.

    Genereert metrics en kwaliteitsindicatoren die gebruikt kunnen
    worden voor monitoring en verbetering van definitie kwaliteit.
    """

    def __init__(self):
        """Initialize de metrics module."""
        super().__init__(
            module_id="metrics",
            module_name="Quality Metrics & Scoring",
            priority=30,  # Lage prioriteit - optioneel/informatief
        )
        self.include_detailed_metrics = True
        self.track_history = False

    def initialize(self, config: dict[str, Any]) -> None:
        """
        Initialize module met configuratie.

        Args:
            config: Module configuratie
        """
        self._config = config
        self.include_detailed_metrics = config.get("include_detailed_metrics", True)
        self.track_history = config.get("track_history", False)
        self._initialized = True
        logger.debug(
            f"MetricsModule geïnitialiseerd "
            f"(detailed={self.include_detailed_metrics}, history={self.track_history})"
        )

    def validate_input(self, context: ModuleContext) -> tuple[bool, str | None]:
        """
        Deze module draait altijd maar kan optioneel zijn.

        Args:
            context: Module context

        Returns:
            (is_valid, error_message)
        """
        # Deze module is optioneel en kan altijd draaien
        return True, None

    def execute(self, context: ModuleContext) -> ModuleOutput:
        """
        Genereer metrics en scoring informatie.

        Args:
            context: Module context

        Returns:
            ModuleOutput met metrics
        """
        try:
            # Verzamel basis informatie
            begrip = context.begrip

            # Extract org_contexts from base_context (fix compatibility issue)
            base_context = context.enriched_context.base_context
            org_contexts = base_context.get("organisatorisch", [])

            char_limits = self._get_char_limits(context)

            # Bereken metrics
            metrics = self._calculate_metrics(begrip, org_contexts, char_limits)

            # Bouw metrics sectie
            sections = []

            # Header
            sections.append("### 📊 Kwaliteitsmetrieken:")
            sections.append("")

            # Karakterlimieten
            sections.append("**Karakterlimieten:**")
            sections.append(f"- Minimum: {char_limits['min']} karakters")
            sections.append(f"- Maximum: {char_limits['max']} karakters")
            sections.append(f"- Aanbevolen: {char_limits['recommended']} karakters")
            sections.append("")

            # Complexiteit indicatoren
            if self.include_detailed_metrics:
                sections.append("**Complexiteit indicatoren:**")
                sections.append(f"- Geschatte woorden: {metrics['estimated_words']}")
                sections.append(
                    f"- Complexiteitsscore: {metrics['complexity_score']}/10"
                )
                sections.append(f"- Leesbaarheid: {metrics['readability_level']}")
                sections.append("")

                # Kwaliteitschecks
                sections.append("**Kwaliteitschecks:**")
                for check, status in metrics["quality_checks"].items():
                    icon = "✅" if status else "⚠️"
                    sections.append(f"- {icon} {check}")
                sections.append("")

            # Context-specifieke metrics
            if org_contexts and len(org_contexts) > 1:
                sections.append("**Context complexiteit:**")
                sections.append(f"- Aantal contexten: {len(org_contexts)}")
                sections.append(
                    f"- Multi-context uitdaging: {'Hoog' if len(org_contexts) > 3 else 'Gemiddeld'}"
                )
                sections.append("")

            # Scoring advies
            scoring_advice = self._generate_scoring_advice(metrics)
            if scoring_advice:
                sections.append("**Aanbevelingen voor kwaliteit:**")
                for advice in scoring_advice:
                    sections.append(f"- {advice}")

            # Combineer secties
            content = "\n".join(sections)

            return ModuleOutput(
                content=content,
                metadata={
                    "metrics": metrics,
                    "char_limits": char_limits,
                    "context_count": len(org_contexts) if org_contexts else 0,
                    "has_scoring_advice": bool(scoring_advice),
                },
            )

        except Exception as e:
            logger.error(f"MetricsModule execution failed: {e}", exc_info=True)
            return ModuleOutput(
                content="",
                metadata={"error": str(e)},
                success=False,
                error_message=f"Failed to generate metrics: {e!s}",
            )

    def get_dependencies(self) -> list[str]:
        """
        Deze module heeft geen harde dependencies.

        Returns:
            Lege lijst
        """
        return []

    def _get_char_limits(self, context: ModuleContext) -> dict[str, int]:
        """
        Haal karakterlimieten op uit config.

        Args:
            context: Module context

        Returns:
            Dictionary met min, max, recommended
        """
        config = context.config

        # Standaard waarden
        defaults = {"min": 150, "max": 350, "recommended": 250}

        # Override met config waarden indien aanwezig
        if hasattr(config, "min_chars"):
            defaults["min"] = config.min_chars
        if hasattr(config, "max_chars"):
            defaults["max"] = config.max_chars

        # Bereken aanbevolen als gemiddelde
        defaults["recommended"] = (defaults["min"] + defaults["max"]) // 2

        return defaults

    def _calculate_metrics(
        self, begrip: str, org_contexts: list[str] | None, char_limits: dict[str, int]
    ) -> dict[str, Any]:
        """
        Bereken verschillende kwaliteitsmetrieken.

        Args:
            begrip: Het begrip
            org_contexts: Organisatie contexten
            char_limits: Karakter limieten

        Returns:
            Dictionary met metrics
        """
        # Basis metrics
        metrics = {
            "term_length": len(begrip),
            "term_words": len(begrip.split()),
            "estimated_words": self._estimate_definition_words(char_limits),
            "complexity_score": 5,  # Default medium
            "readability_level": "Gemiddeld",
            "quality_checks": {},
        }

        # Complexiteit score berekening
        complexity_factors = []

        # Term complexiteit
        if len(begrip) > 30:
            complexity_factors.append(2)
        elif len(begrip) > 20:
            complexity_factors.append(1)

        # Multi-word term
        if metrics["term_words"] > 3:
            complexity_factors.append(2)
        elif metrics["term_words"] > 1:
            complexity_factors.append(1)

        # Context complexiteit
        if org_contexts and len(org_contexts) > 3:
            complexity_factors.append(2)
        elif org_contexts and len(org_contexts) > 1:
            complexity_factors.append(1)

        # Bereken totale complexiteit (1-10)
        base_complexity = 3
        added_complexity = sum(complexity_factors)
        metrics["complexity_score"] = min(10, base_complexity + added_complexity)

        # Leesbaarheid niveau
        if metrics["complexity_score"] <= 3:
            metrics["readability_level"] = "Eenvoudig"
        elif metrics["complexity_score"] <= 6:
            metrics["readability_level"] = "Gemiddeld"
        else:
            metrics["readability_level"] = "Complex"

        # Kwaliteitschecks
        metrics["quality_checks"] = {
            "Enkelvoudige zin mogelijk": metrics["estimated_words"] <= 40,
            "Binnen aanbevolen lengte": metrics["estimated_words"] <= 35,
            "Geen extreem lange term": len(begrip) <= 40,
            "Hanteerbare context": not org_contexts or len(org_contexts) <= 3,
            "Duidelijke term": not self._has_special_chars(begrip),
        }

        return metrics

    def _estimate_definition_words(self, char_limits: dict[str, int]) -> int:
        """
        Schat het aantal woorden in definitie op basis van karakterlimiet.

        Args:
            char_limits: Dictionary met karakterlimieten

        Returns:
            Geschat aantal woorden
        """
        # Gemiddelde Nederlandse woordlengte is ~5-6 karakters + spaties
        avg_word_length = 5.5
        recommended_chars = char_limits["recommended"]

        return int(recommended_chars / avg_word_length)

    def _has_special_chars(self, text: str) -> bool:
        """
        Check of tekst speciale karakters bevat.

        Args:
            text: Te checken tekst

        Returns:
            True als speciale karakters aanwezig
        """
        # Check voor niet-alfanumerieke karakters (behalve spaties en koppeltekens)
        special_pattern = r"[^a-zA-Z0-9\s\-]"
        return bool(re.search(special_pattern, text))

    def _generate_scoring_advice(self, metrics: dict[str, Any]) -> list[str]:
        """
        Genereer advies op basis van metrics.

        Args:
            metrics: Berekende metrics

        Returns:
            Lijst met advies punten
        """
        advice = []

        # Complexiteit advies
        if metrics["complexity_score"] > 7:
            advice.append("⚠️ Hoge complexiteit - overweeg vereenvoudiging of opdeling")

        # Woordenaantal advies
        if metrics["estimated_words"] > 40:
            advice.append("⚠️ Mogelijk te lang voor één zin - focus op kernbegrip")
        elif metrics["estimated_words"] < 15:
            advice.append("💡 Ruimte voor meer detail indien nodig")

        # Kwaliteitscheck advies
        failed_checks = [
            check for check, passed in metrics["quality_checks"].items() if not passed
        ]
        if failed_checks:
            advice.append(f"🔍 Aandachtspunten: {', '.join(failed_checks)}")

        # Positieve feedback
        if metrics["complexity_score"] <= 5 and not failed_checks:
            advice.append("✅ Goede balans tussen detail en leesbaarheid")

        return advice
