#!/usr/bin/env python3
"""
Unit tests voor de CoreInstructionsModule (_build_role_and_basic_rules).

Test de output en functionaliteit van de eerste module in isolatie.
"""

import sys
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.definition_generator_context import EnrichedContext
from src.services.prompts.modular_prompt_builder import (
    ModularPromptBuilder,
    PromptComponentConfig,
)


class TestCoreInstructionsModule:
    """Test suite voor CoreInstructionsModule."""

    def setup_method(self):
        """Setup voor elke test."""
        # Configuratie voor alleen core module
        config = PromptComponentConfig(
            include_role=True,
            include_context=False,
            include_ontological=False,
            include_validation_rules=False,
            include_forbidden_patterns=False,
            include_final_instructions=False,
        )
        self.builder = ModularPromptBuilder(config)

    def test_basic_output_structure(self):
        """Test dat de basis structuur correct is."""
        output = self.builder._build_role_and_basic_rules("test_begrip")

        # Check essentiële onderdelen
        assert "expert" in output.lower()
        assert "beleidsmatige definities" in output
        assert "één" in output or "een" in output
        assert "zin" in output
        assert "zonder toelichting" in output
        assert "zakelijke" in output
        assert "generieke" in output

    def test_output_consistency(self):
        """Test dat output consistent is voor verschillende begrippen."""
        output1 = self.builder._build_role_and_basic_rules("blockchain")
        output2 = self.builder._build_role_and_basic_rules("opsporing")
        output3 = self.builder._build_role_and_basic_rules("AI")

        # Output moet identiek zijn (begrip wordt nog niet gebruikt in huidige impl)
        assert output1 == output2 == output3

    def test_no_begriff_specific_content(self):
        """Test dat begrip NIET in de core instructions staat."""
        begrippen = ["blockchain", "opsporing", "natuurinclusief bouwen"]

        for begrip in begrippen:
            output = self.builder._build_role_and_basic_rules(begrip)
            assert (
                begrip not in output
            ), f"Begrip '{begrip}' mag niet in core instructions staan"

    def test_line_count(self):
        """Test aantal regels in output."""
        output = self.builder._build_role_and_basic_rules("test")
        lines = output.split("\n")

        # Huidige implementatie heeft 3 regels
        assert len(lines) == 3

    def test_character_length(self):
        """Test karakter lengte."""
        output = self.builder._build_role_and_basic_rules("test")

        # Huidige implementatie is ongeveer 209 karakters
        assert 200 <= len(output) <= 220

    def test_no_formatting_markers(self):
        """Test dat er geen markdown formatting in zit."""
        output = self.builder._build_role_and_basic_rules("test")

        # Check voor afwezigheid van markdown
        assert "**" not in output
        assert "###" not in output
        assert "#" not in output
        assert "•" not in output
        assert "📌" not in output

    def test_missing_elements(self):
        """Test welke belangrijke elementen ontbreken in huidige implementatie."""
        output = self.builder._build_role_and_basic_rules("test")

        # Deze elementen ontbreken maar zouden nuttig zijn
        missing_elements = {
            "character_limit": "karakter" not in output.lower(),
            "remaining_chars": "resterende" not in output.lower(),
            "quality_criteria": "kwaliteit" not in output.lower(),
            "specific_role": "nederlandse" not in output.lower(),
            "output_format": "formaat" not in output.lower(),
            "ess_reference": "ess" not in output.lower(),
            "warnings": "⚠️" not in output,
            "emphasis": "**" not in output,
            "structure": "###" not in output,
        }

        # Documenteer wat mist voor verbetering
        assert all(
            missing_elements.values()
        ), "Huidige implementatie mist veel elementen"

        # Return voor analyse
        return missing_elements


class TestCoreInstructionsModuleImproved:
    """Test suite voor verbeterde versie van CoreInstructionsModule."""

    @pytest.fixture
    def improved_output(self):
        """Mock improved output voor vergelijking."""
        return """Je bent een ervaren Nederlandse expert in het opstellen van beleidsmatige en juridische definities voor de Nederlandse overheid.

**Je opdracht**: Formuleer een heldere, eenduidige definitie voor het opgegeven begrip.

### Definitie vereisten:
• **Formaat**: Één volledige zin die het begrip volledig verklaart
• **Stijl**: Zakelijk, formeel en geschikt voor officiële overheidsdocumenten
• **Structuur**: Begin met "[begrip] is..." of "[begrip] betreft..."
• **Taal**: Helder Nederlands zonder jargon (tenzij onvermijdelijk)

### Kwaliteitscriteria:
✓ Ondubbelzinnig - geen ruimte voor meerdere interpretaties
✓ Volledig - bevat alle essentiële kenmerken
✓ Afgebakend - maakt duidelijk wat WEL en NIET onder de definitie valt
✓ Contextgevoelig - past bij de Nederlandse overheidscontext

⚠️ **LET OP**:
- Geen toelichtingen, voorbeelden of extra uitleg toevoegen
- Alleen de definitie zelf in één zin
- Vermijd cirkelredeneringen (gebruik het begrip niet in de eigen definitie)
- Maximaal 2500 karakters beschikbaar

BELANGRIJK: Focus op precisie en helderheid. De definitie moet juridisch houdbaar zijn."""

    def test_improved_has_all_elements(self, improved_output):
        """Test dat verbeterde versie alle gewenste elementen bevat."""
        # Check voor aanwezigheid van alle elementen
        assert "ervaren nederlandse expert" in improved_output.lower()
        assert "**je opdracht**" in improved_output.lower()
        assert "### definitie vereisten:" in improved_output.lower()
        assert "### kwaliteitscriteria:" in improved_output.lower()
        assert "⚠️" in improved_output
        assert "karakter" in improved_output.lower()
        assert "•" in improved_output
        assert "✓" in improved_output

    def test_improved_structure(self, improved_output):
        """Test structuur van verbeterde output."""
        lines = improved_output.split("\n")

        # Meer gestructureerd dan huidige 3 regels
        assert len(lines) > 10

        # Check voor secties
        assert any("###" in line for line in lines)
        assert any("**" in line for line in lines)
        assert any("•" in line for line in lines)

    def test_improved_length_appropriate(self, improved_output):
        """Test dat verbeterde versie niet te lang is."""
        # Moet substantieel maar niet overdreven zijn
        assert 500 <= len(improved_output) <= 1500

    def test_improved_actionable(self, improved_output):
        """Test dat instructies duidelijk en uitvoerbaar zijn."""
        # Check voor concrete instructies
        assert "één" in improved_output.lower() or "een" in improved_output.lower()
        assert "zin" in improved_output.lower()
        assert "begin met" in improved_output.lower()
        assert "vermijd" in improved_output.lower()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])

    # Also run analysis
    print("\n=== Analyse van huidige implementatie ===")
    test = TestCoreInstructionsModule()
    test.setup_method()

    output = test.builder._build_role_and_basic_rules("test_begrip")
    print(f"Huidige output ({len(output)} chars):")
    print("-" * 50)
    print(output)
    print("-" * 50)

    missing = test.test_missing_elements()
    print("\nOntbrekende elementen:")
    for element, is_missing in missing.items():
        if is_missing:
            print(f"  ❌ {element}")
        else:
            print(f"  ✅ {element}")
