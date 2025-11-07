"""
Test voor DEF-135: Error Prevention Module transformatie naar positieve instructies.

Dit test verifieert dat:
1. De module positieve instructies genereert
2. Het aantal regels met ~40% is gereduceerd
3. Context-specifieke instructies positief zijn geformuleerd
4. Alleen kritieke waarschuwingen nog negatief zijn
"""

from unittest.mock import MagicMock

import pytest

from src.services.prompts.modules.base_module import ModuleContext
from src.services.prompts.modules.error_prevention_module import ErrorPreventionModule


class TestErrorPreventionTransformation:
    """Test de transformatie van negatieve regels naar positieve instructies."""

    def setup_method(self):
        """Setup voor elke test."""
        self.module = ErrorPreventionModule()
        self.module.initialize({})

    def test_positive_instructions_count_reduced(self):
        """
        Test dat het aantal instructies met ~40% is gereduceerd.

        Oude versie had:
        - 8 basis fouten
        - ~25 verboden starters
        - Totaal ~33 regels

        Nieuwe versie heeft:
        - 7 positieve instructies
        - 3 kritieke warnings
        - Totaal ~10 hoofdregels (reductie van 70%!)
        """
        instructions = self.module._build_positive_instructions()
        warnings = self.module._build_critical_warnings()

        # We verwachten ongeveer 7 positieve instructies (geconsolideerd)
        assert (
            5 <= len(instructions) <= 10
        ), f"Expected 5-10 instructions, got {len(instructions)}"

        # We verwachten maximaal 3 kritieke warnings
        assert len(warnings) <= 3, f"Expected max 3 warnings, got {len(warnings)}"

        # Totaal aantal regels moet significant lager zijn dan oude ~33
        total = len(instructions) + len(warnings)
        assert total <= 15, f"Total rules should be <= 15 (40% reduction), got {total}"

    def test_positive_framing_with_action_verbs(self):
        """Test dat instructies positief zijn geformuleerd met actiewerkwoorden."""
        instructions = self.module._build_positive_instructions()

        # Check voor positieve actiewerkwoorden
        positive_verbs = [
            "Start",
            "Definieer",
            "Wees",
            "Gebruik",
            "Structureer",
            "Test",
            "Focus",
            "Beschrijf",
        ]

        instructions_text = " ".join(instructions)

        # Minimaal 3 verschillende positieve werkwoorden
        found_verbs = [verb for verb in positive_verbs if verb in instructions_text]
        assert (
            len(found_verbs) >= 3
        ), f"Expected at least 3 positive verbs, found: {found_verbs}"

        # Geen negatieve framing in positieve instructies (behalve voorbeelden)
        negative_words = ["niet", "geen", "vermijd", "nooit"]
        for instruction in instructions:
            # Skip voorbeeld regels (die • bevatten)
            if "•" not in instruction:
                for negative in negative_words:
                    # "niet" mag in uitleg, maar niet als hoofdinstructie
                    if negative in instruction.lower() and "**" in instruction:
                        # Check of het in de bold tekst staat (hoofdinstructie)
                        bold_parts = [
                            part.split("**")[0]
                            for part in instruction.split("**")[1::2]
                        ]
                        for bold in bold_parts:
                            assert (
                                negative not in bold.lower()
                            ), f"Negative word '{negative}' found in positive instruction: {instruction}"

    def test_context_instructions_are_positive(self):
        """Test dat context-specifieke instructies positief zijn geformuleerd."""
        # Mock contexts
        org_contexts = ["NP", "OM"]
        jur_contexts = ["Strafrecht"]
        wet_contexts = ["Wetboek van Strafrecht"]

        instructions = self.module._build_context_instructions(
            org_contexts, jur_contexts, wet_contexts
        )

        # Check dat er instructies zijn
        assert len(instructions) > 0, "Should have context instructions"

        # Check voor positieve framing
        for instruction in instructions:
            # Moet een actie bevatten (vaak met **)
            assert (
                "**" in instruction
            ), f"Instruction should have emphasized action: {instruction}"

            # Check voor positieve actiewoorden in context instructies
            positive_context_words = [
                "Focus",
                "Abstraheer",
                "Generaliseer",
                "Schrijf",
                "Maak",
                "Formuleer",
                "Definieer",
            ]

            has_positive = any(word in instruction for word in positive_context_words)
            assert (
                has_positive
            ), f"Context instruction should have positive framing: {instruction}"

    def test_critical_warnings_remain_for_essential_rules(self):
        """Test dat alleen essentiële regels als waarschuwing blijven."""
        warnings = self.module._build_critical_warnings()

        # Maximaal 3 kritieke warnings
        assert (
            len(warnings) <= 3
        ), f"Should have max 3 critical warnings, got {len(warnings)}"

        # Check dat deze echt kritiek zijn (moeten ❌ bevatten)
        for warning in warnings:
            assert "❌" in warning, f"Critical warning should have ❌ marker: {warning}"

        # Check voor specifieke kritieke onderwerpen
        critical_topics = ["cirkel", "context", "subjectie"]
        warnings_text = " ".join(warnings).lower()

        found_topics = [topic for topic in critical_topics if topic in warnings_text]
        assert (
            len(found_topics) >= 2
        ), f"Should cover at least 2 critical topics, found: {found_topics}"

    def test_module_execution_with_context(self):
        """Test complete module uitvoering met contexts."""
        # Mock enriched context and config
        from src.services.definition_generator_config import UnifiedGeneratorConfig
        from src.services.definition_generator_context import EnrichedContext

        enriched_context = MagicMock(spec=EnrichedContext)
        enriched_context.metadata = {}
        config = MagicMock(spec=UnifiedGeneratorConfig)

        # Setup context
        context = ModuleContext(
            begrip="testbegrip",
            enriched_context=enriched_context,
            config=config,
            shared_state={},
        )

        # Mock shared data
        context.set_shared("organization_contexts", ["NP"])
        context.set_shared("juridical_contexts", ["Strafrecht"])
        context.set_shared("legal_basis_contexts", ["Wetboek van Strafrecht"])

        # Execute module
        result = self.module.execute(context)

        # Verify result
        assert result.success, f"Module execution failed: {result.error_message}"
        assert result.content, "Should have content"

        # Check voor positieve headers
        assert "✅ Instructies voor effectieve definities:" in result.content
        assert "🎯 Context-specifieke richtlijnen:" in result.content

        # Check metadata
        assert result.metadata["instruction_type"] == "positive"
        assert result.metadata["context_count"] == 3  # 1 org + 1 jur + 1 wet

    def test_validation_matrix_has_positive_framing(self):
        """Test dat de validatiematrix positief is geformuleerd."""
        matrix = self.module._build_validation_matrix()

        # Check voor positieve kolomnamen
        assert "Instructie" in matrix
        assert "Waarom belangrijk?" in matrix

        # Check dat het quality aspects bevat, niet problemen
        assert "Kwaliteitsaspect" in matrix

        # Oude matrix had "Probleem" en "Afgedekt?" - deze moeten weg zijn
        assert "Probleem" not in matrix
        assert "Afgedekt?" not in matrix

    def test_consolidated_rules_coverage(self):
        """
        Test dat geconsolideerde regels alle belangrijke aspecten dekken.

        De consolidatie moet dekken:
        1. Start instructies (was 20+ regels)
        2. Specificiteit (was 5+ vage termen)
        3. Grammatica (was 3+ regels)
        4. Structuur (nieuw toegevoegd)
        """
        instructions = self.module._build_positive_instructions()
        instructions_text = " ".join(instructions).lower()

        # Check coverage van belangrijke onderwerpen
        topics = {
            "start": "start direct",
            "functie": "functie",
            "specifiek": "specifiek",
            "grammatica": "grammatica",
            "structuur": "structureer",
            "test": "test",
        }

        covered = {name: topic in instructions_text for name, topic in topics.items()}

        # Minimaal 5 van de 6 topics moeten gedekt zijn
        coverage_count = sum(covered.values())
        assert (
            coverage_count >= 5
        ), f"Should cover at least 5/6 topics, covered: {[k for k, v in covered.items() if v]}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
