#!/usr/bin/env python3
"""
Test script voor DEF-137: Container Terms Verfijning.

Dit script test of de verfijning van container terms correct is geïmplementeerd:
- Vage containerbegrippen blijven verboden
- Proces/activiteit/handeling zijn toegestaan in definitie
- Meta-woorden blijven verboden als starter
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from services.definition_generator_config import UnifiedGeneratorConfig
from services.definition_generator_context import EnrichedContext
from services.prompts.modules.base_module import ModuleContext
from services.prompts.modules.error_prevention_module import ErrorPreventionModule


def create_test_context():
    """Helper functie om test context te maken."""
    enriched_context = EnrichedContext(
        base_context={},
        sources=[],
        expanded_terms={},
        confidence_scores={},
        metadata={},
    )

    config = UnifiedGeneratorConfig()

    return ModuleContext(
        begrip="testbegrip",
        enriched_context=enriched_context,
        config=config,
        shared_state={},
    )


def test_vague_container_terms_forbidden():
    """Test dat vage containerbegrippen verboden blijven."""
    module = ErrorPreventionModule()
    module.initialize({})

    context = create_test_context()
    result = module.execute(context)

    assert result.success, "Module execution failed"
    content = result.content

    # Check dat vage containerbegrippen verboden zijn
    vague_terms = ["aspect", "element", "factor", "onderdeel", "component", "dimensie"]

    for term in vague_terms:
        assert (
            term in content
        ), f"Vage containerbegrip '{term}' ontbreekt in verboden lijst!"

    # Check dat deze in de juiste context staan
    assert (
        "vage containerbegrippen" in content
    ), "Moet 'vage' specificeren bij containerbegrippen"

    print("✅ Vage container terms blijven verboden")


def test_proces_activiteit_allowed():
    """Test dat proces/activiteit/handeling toegestaan zijn."""
    module = ErrorPreventionModule()
    module.initialize({})

    context = create_test_context()
    result = module.execute(context)

    assert result.success, "Module execution failed"
    content = result.content

    # Check dat er een verduidelijking is dat proces/activiteit WEL mogen
    assert (
        "ONTOLOGISCHE MARKERS" in content
        and "'proces', 'activiteit', 'handeling'" in content
        and "toegestaan" in content
    ), "Verduidelijking over toegestane proces/activiteit ontbreekt!"

    # Check dat dit als positieve regel staat
    assert (
        "✅ ONTOLOGISCHE MARKERS:" in content
    ), "Positieve markering voor toegestane termen ontbreekt"

    # Check dat old forbidden rule is removed/updated
    assert (
        "('proces', 'activiteit')" not in content or "vage" in content
    ), "Oude regel met proces/activiteit als algemeen verboden nog aanwezig!"

    print("✅ Proces/activiteit/handeling zijn toegestaan in definitie")


def test_meta_words_still_forbidden_as_starters():
    """Test dat meta-woorden nog steeds verboden zijn als starters."""
    module = ErrorPreventionModule()
    module.initialize({"extended_forbidden_list": True})

    context = create_test_context()
    result = module.execute(context)

    assert result.success, "Module execution failed"
    content = result.content

    # Check dat meta-woorden als starters verboden blijven
    forbidden_starters = [
        "proces waarbij",
        "handeling die",
        "vorm van",
        "type van",
        "soort van",
    ]

    for starter in forbidden_starters:
        assert (
            f"Start niet met '{starter}'" in content
        ), f"Meta-woord starter '{starter}' moet nog steeds verboden zijn!"

    print("✅ Meta-woorden blijven verboden als starters")


def test_bijzinnen_clarification():
    """Test dat bijzinnen verfijning correct is."""
    module = ErrorPreventionModule()
    module.initialize({})

    context = create_test_context()
    result = module.execute(context)

    assert result.success, "Module execution failed"
    content = result.content

    # Check verfijning van bijzinnen regel
    assert (
        "onnodige bijzinnen" in content or "gebruik met mate" in content
    ), "Bijzinnen regel moet genuanceerd zijn"

    # Check dat het niet meer absoluut verboden is
    assert (
        "Vermijd bijzinnen" not in content
        or "onnodige" in content
        or "met mate" in content
    ), "Bijzinnen regel moet genuanceerd zijn, niet absoluut"

    print("✅ Bijzinnen regel is verfijnd")


def test_forbidden_starters_comments():
    """Test dat forbidden starters juiste documentatie heeft."""
    module = ErrorPreventionModule()

    # Direct test de method voor duidelijkheid
    forbidden_list = module._build_forbidden_starters()

    # Join de lijst voor analyse
    full_text = "\n".join(forbidden_list)

    # Check categorisatie aanwezig (indirect via output)
    assert "Start niet met 'is'" in full_text, "Koppelwerkwoorden moeten verboden zijn"
    assert "Start niet met 'de'" in full_text, "Lidwoorden moeten verboden zijn"
    assert (
        "Start niet met 'proces waarbij'" in full_text
    ), "Meta-woord combinaties moeten verboden zijn"

    print("✅ Forbidden starters hebben juiste structuur")


def test_no_conflict_with_ontological_instructions():
    """Test dat er geen conflict is met ontologische instructies."""
    module = ErrorPreventionModule()
    module.initialize({})

    context = create_test_context()
    result = module.execute(context)

    assert result.success, "Module execution failed"
    content = result.content

    # Proces/activiteit moeten toegestaan zijn voor definitie inhoud
    assert (
        "ONTOLOGISCHE MARKERS" in content
        and "'proces', 'activiteit', 'handeling'" in content
        and "toegestaan" in content
    ), "Moet expliciet vermelden dat deze toegestaan zijn"

    # Maar niet als starter
    assert (
        "Start niet met 'proces waarbij'" in content
    ), "Proces waarbij moet verboden blijven als starter"

    print("✅ Geen conflict met ontologische instructies")


def run_all_tests():
    """Run alle tests voor DEF-137."""
    print("\n" + "=" * 60)
    print("🧪 DEF-137 CONTAINER TERMS VERFIJNING TESTS")
    print("=" * 60 + "\n")

    try:
        test_vague_container_terms_forbidden()
        test_proces_activiteit_allowed()
        test_meta_words_still_forbidden_as_starters()
        test_bijzinnen_clarification()
        test_forbidden_starters_comments()
        test_no_conflict_with_ontological_instructions()

        print("\n" + "=" * 60)
        print("🎉 ALLE DEF-137 TESTS GESLAAGD!")
        print("=" * 60 + "\n")

        print("📋 Samenvatting:")
        print("- ✅ Vage containerbegrippen blijven verboden")
        print("- ✅ Proces/activiteit/handeling toegestaan in definitie")
        print("- ✅ Meta-woorden blijven verboden als starter")
        print("- ✅ Bijzinnen regel is verfijnd")
        print("- ✅ Geen conflict met ontologische instructies")

        return True

    except AssertionError as e:
        print(f"\n❌ TEST GEFAALD: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
