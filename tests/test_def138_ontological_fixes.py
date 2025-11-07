#!/usr/bin/env python3
"""
Test script voor DEF-138: Ontologische Categorie Instructie Fixes.

Dit script test of de nieuwe instructies correct zijn geïmplementeerd:
- Geen meta-woorden in definitie starters
- Correcte instructies per categorie
- Duidelijke scheiding tussen instructie en definitie
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from services.definition_generator_config import UnifiedGeneratorConfig
from services.definition_generator_context import EnrichedContext
from services.prompts.modules.base_module import ModuleContext
from services.prompts.modules.semantic_categorisation_module import (
    SemanticCategorisationModule,
)


def create_test_context(ontological_category=None):
    """Helper functie om test context te maken."""
    # Maak een minimale EnrichedContext
    enriched_context = EnrichedContext(
        base_context={},
        sources=[],
        expanded_terms={},
        confidence_scores={},
        metadata=(
            {"ontologische_categorie": ontological_category}
            if ontological_category
            else {}
        ),
    )

    # Maak een minimale config
    config = UnifiedGeneratorConfig()

    # Maak de ModuleContext
    return ModuleContext(
        begrip="testbegrip",
        enriched_context=enriched_context,
        config=config,
        shared_state={},
    )


def test_base_section_no_meta_words():
    """Test dat basis sectie geen meta-woorden meer adviseert."""
    module = SemanticCategorisationModule()
    module.initialize({})

    # Test zonder categorie (alleen basis sectie)
    context = create_test_context()
    result = module.execute(context)

    assert result.success, "Module execution failed"
    content = result.content

    # Check dat oude meta-woord instructies NIET meer aanwezig zijn
    forbidden_phrases = [
        "'activiteit waarbij...'",
        "'soort...'",
        "'type... dat...'",
        "'resultaat van...'",
        "'exemplaar van... dat...'",
    ]

    for phrase in forbidden_phrases:
        assert (
            phrase not in content
        ), f"Oude meta-woord instructie '{phrase}' nog aanwezig in basis sectie!"

    # Check dat nieuwe instructies WEL aanwezig zijn
    required_phrases = [
        "Begin DIRECT met het zelfstandig naamwoord",
        "GEEN meta-woorden zoals 'proces', 'type', 'resultaat', 'exemplaar'",
        "ONTOLOGISCHE CATEGORIE INSTRUCTIES",
    ]

    for phrase in required_phrases:
        assert phrase in content, f"Vereiste nieuwe instructie '{phrase}' ontbreekt!"

    print("✅ Basis sectie test geslaagd - geen meta-woorden meer")


def test_proces_category():
    """Test PROCES categorie nieuwe instructies."""
    module = SemanticCategorisationModule()
    module.initialize({"detailed_guidance": True})

    context = create_test_context("PROCES")
    result = module.execute(context)

    assert result.success, "Module execution failed"
    content = result.content

    # Check goede voorbeelden
    assert "observatie van gedrag" in content, "Goed PROCES voorbeeld ontbreekt"
    assert "verzameling van data" in content, "Goed PROCES voorbeeld ontbreekt"

    # Check foute voorbeelden
    assert '"proces waarin..."' in content, "Fout PROCES voorbeeld ontbreekt"
    assert '"activiteit waarbij..."' in content, "Fout PROCES voorbeeld ontbreekt"

    # Check instructie
    assert "HANDELINGSNAAMWOORD" in content, "PROCES instructie ontbreekt"

    print("✅ PROCES categorie test geslaagd")


def test_type_category():
    """Test TYPE categorie nieuwe instructies."""
    module = SemanticCategorisationModule()
    module.initialize({"detailed_guidance": True})

    context = create_test_context("TYPE")
    result = module.execute(context)

    assert result.success, "Module execution failed"
    content = result.content

    # Check goede voorbeelden
    assert (
        "document dat juridische beslissingen" in content
    ), "Goed TYPE voorbeeld ontbreekt"
    assert "persoon die bevoegd is" in content, "Goed TYPE voorbeeld ontbreekt"

    # Check foute voorbeelden
    assert '"soort document dat..."' in content, "Fout TYPE voorbeeld ontbreekt"
    assert '"type persoon die..."' in content, "Fout TYPE voorbeeld ontbreekt"

    # Check instructie
    assert (
        "ZELFSTANDIG NAAMWOORD dat de klasse aanduidt" in content
    ), "TYPE instructie ontbreekt"

    print("✅ TYPE categorie test geslaagd")


def test_resultaat_category():
    """Test RESULTAAT categorie nieuwe instructies."""
    module = SemanticCategorisationModule()
    module.initialize({"detailed_guidance": True})

    context = create_test_context("RESULTAAT")
    result = module.execute(context)

    assert result.success, "Module execution failed"
    content = result.content

    # Check goede voorbeelden
    assert "rapport opgesteld na" in content, "Goed RESULTAAT voorbeeld ontbreekt"
    assert "besluit genomen na" in content, "Goed RESULTAAT voorbeeld ontbreekt"

    # Check foute voorbeelden
    assert '"resultaat van analyse..."' in content, "Fout RESULTAAT voorbeeld ontbreekt"
    assert (
        '"uitkomst van een proces..."' in content
    ), "Fout RESULTAAT voorbeeld ontbreekt"

    # Check instructie
    assert (
        "ZELFSTANDIG NAAMWOORD dat de uitkomst benoemt" in content
    ), "RESULTAAT instructie ontbreekt"

    print("✅ RESULTAAT categorie test geslaagd")


def test_exemplaar_category():
    """Test EXEMPLAAR categorie nieuwe instructies."""
    module = SemanticCategorisationModule()
    module.initialize({"detailed_guidance": True})

    context = create_test_context("EXEMPLAAR")
    result = module.execute(context)

    assert result.success, "Module execution failed"
    content = result.content

    # Check goede voorbeelden
    assert "Wet van 15 maart 2024" in content, "Goed EXEMPLAAR voorbeeld ontbreekt"
    assert "Zaak 2024/1234" in content, "Goed EXEMPLAAR voorbeeld ontbreekt"

    # Check foute voorbeelden
    assert '"exemplaar van een wet..."' in content, "Fout EXEMPLAAR voorbeeld ontbreekt"
    assert (
        '"specifiek geval van zaak..."' in content
    ), "Fout EXEMPLAAR voorbeeld ontbreekt"

    # Check instructie
    assert (
        "NAAM of AANDUIDING van het specifieke geval" in content
    ), "EXEMPLAAR instructie ontbreekt"

    print("✅ EXEMPLAAR categorie test geslaagd")


def test_no_is_een_instruction():
    """Test dat GEEN enkele categorie meer 'is een' adviseert."""
    module = SemanticCategorisationModule()
    module.initialize({"detailed_guidance": True})

    categories = ["PROCES", "TYPE", "RESULTAAT", "EXEMPLAAR"]

    for category in categories:
        context = create_test_context(category)
        result = module.execute(context)

        assert result.success, f"Module execution failed for {category}"
        content = result.content

        # Check dat "is een" alleen in FOUTE voorbeelden voorkomt
        lines = content.split("\n")
        for line in lines:
            if "is een" in line.lower() and "✅" in line:
                assert False, f"'is een' gevonden in GOED voorbeeld voor {category}!"
            if "is een" in line.lower() and "KICK-OFF" in line:
                assert False, f"'is een' gevonden in instructie voor {category}!"

    print("✅ Geen 'is een' in instructies test geslaagd")


def run_all_tests():
    """Run alle tests voor DEF-138."""
    print("\n" + "=" * 60)
    print("🧪 DEF-138 ONTOLOGISCHE INSTRUCTIE TESTS")
    print("=" * 60 + "\n")

    try:
        test_base_section_no_meta_words()
        test_proces_category()
        test_type_category()
        test_resultaat_category()
        test_exemplaar_category()
        test_no_is_een_instruction()

        print("\n" + "=" * 60)
        print("🎉 ALLE DEF-138 TESTS GESLAAGD!")
        print("=" * 60 + "\n")

        print("📋 Samenvatting:")
        print("- ✅ Basis sectie bevat geen meta-woord instructies meer")
        print("- ✅ PROCES categorie start met handelingsnaamwoord")
        print("- ✅ TYPE categorie start met klasse-aanduiding")
        print("- ✅ RESULTAAT categorie start met uitkomst")
        print("- ✅ EXEMPLAAR categorie start met identificatie")
        print("- ✅ Geen enkele categorie adviseert 'is een' meer")

        return True

    except AssertionError as e:
        print(f"\n❌ TEST GEFAALD: {e}")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
