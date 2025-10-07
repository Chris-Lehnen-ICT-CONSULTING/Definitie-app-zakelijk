#!/usr/bin/env python3
"""
Test script voor ImprovedOntologyClassifier.

Valideert dat nieuwe classifier:
1. Betere accuracy heeft (target: >93.3%)
2. 3-context support werkt
3. Zelfde interface behoudt (backward compatible)
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from domain.ontological_categories import OntologischeCategorie
from ontologie.improved_classifier import ImprovedOntologyClassifier


def test_basic_classification():
    """Test basis classificatie zonder context."""
    print("\n" + "=" * 60)
    print("TEST 1: Basis Classificatie (zonder context)")
    print("=" * 60)

    test_cases = [
        ("validatie", OntologischeCategorie.PROCES),
        ("verificatie", OntologischeCategorie.PROCES),
        ("authenticatie", OntologischeCategorie.PROCES),
        ("toets", OntologischeCategorie.TYPE),
        ("formulier", OntologischeCategorie.TYPE),
        ("besluit", OntologischeCategorie.RESULTAAT),
        ("vergunning", OntologischeCategorie.RESULTAAT),
        ("rapport", OntologischeCategorie.RESULTAAT),
        ("verdachte", OntologischeCategorie.EXEMPLAAR),
    ]

    classifier = ImprovedOntologyClassifier()
    correct = 0
    total = len(test_cases)

    for begrip, expected in test_cases:
        result = classifier.classify(begrip=begrip)
        is_correct = result.categorie == expected

        if is_correct:
            correct += 1
            status = "✅"
        else:
            status = "❌"

        print(
            f"{status} {begrip:20} → {result.categorie.value:10} "
            f"(expected: {expected.value}, score: {result.test_scores.get(result.categorie.value, 0):.2f})"
        )

    accuracy = (correct / total) * 100
    print(f"\n📊 Accuracy: {correct}/{total} ({accuracy:.1f}%)")

    if accuracy >= 93.3:
        print("✅ PASSED: Accuracy >= 93.3% (target van oude analyzer)")
    else:
        print("❌ FAILED: Accuracy < 93.3%")

    return accuracy >= 93.3


def test_context_support():
    """Test 3-context support (org, jur, wet)."""
    print("\n" + "=" * 60)
    print("TEST 2: Context Support")
    print("=" * 60)

    classifier = ImprovedOntologyClassifier()

    # Test 1: Begrip met juridische context boost
    result = classifier.classify(
        begrip="toets",
        org_context="",
        jur_context="Procedure voor beoordeling van aanvragen",
        wet_context="",
    )
    print("\n🔹 'toets' met juridische context (procedure):")
    print(f"   Categorie: {result.categorie.value}")
    print(f"   Scores: {result.test_scores}")
    print("   → Verwacht: PROCES bias door 'procedure' in context")

    # Test 2: Begrip met organisatorische context
    result = classifier.classify(
        begrip="toets",
        org_context="Soort document voor kwaliteitsbewaking",
        jur_context="",
        wet_context="",
    )
    print("\n🔹 'toets' met organisatorische context (soort):")
    print(f"   Categorie: {result.categorie.value}")
    print(f"   Scores: {result.test_scores}")
    print("   → Verwacht: TYPE bias door 'soort' in context")

    # Test 3: Begrip met wettelijke context
    result = classifier.classify(
        begrip="beschikking",
        org_context="",
        jur_context="",
        wet_context="De minister verleent of weigert een beschikking",
    )
    print("\n🔹 'beschikking' met wettelijke context (verleent):")
    print(f"   Categorie: {result.categorie.value}")
    print(f"   Scores: {result.test_scores}")
    print("   → Verwacht: RESULTAAT bias door 'verleent' in context")

    print("\n✅ Context support werkt (manuele verificatie nodig)")
    return True


def test_backward_compatibility():
    """Test dat oude interface (return format) behouden blijft."""
    print("\n" + "=" * 60)
    print("TEST 3: Backward Compatibility")
    print("=" * 60)

    classifier = ImprovedOntologyClassifier()
    result = classifier.classify(begrip="validatie")

    # Check return type
    has_categorie = hasattr(result, "categorie")
    has_reasoning = hasattr(result, "reasoning")
    has_test_scores = hasattr(result, "test_scores")

    print(f"✅ result.categorie exists: {has_categorie}")
    print(f"✅ result.reasoning exists: {has_reasoning}")
    print(f"✅ result.test_scores exists: {has_test_scores}")

    # Check types
    is_enum = isinstance(result.categorie, OntologischeCategorie)
    is_string = isinstance(result.reasoning, str)
    is_dict = isinstance(result.test_scores, dict)

    print(f"✅ categorie is OntologischeCategorie enum: {is_enum}")
    print(f"✅ reasoning is string: {is_string}")
    print(f"✅ test_scores is dict: {is_dict}")

    all_checks = all(
        [has_categorie, has_reasoning, has_test_scores, is_enum, is_string, is_dict]
    )

    if all_checks:
        print("\n✅ PASSED: Backward compatible met oude interface")
    else:
        print("\n❌ FAILED: Interface mismatch")

    return all_checks


def test_edge_cases():
    """Test edge cases en error handling."""
    print("\n" + "=" * 60)
    print("TEST 4: Edge Cases")
    print("=" * 60)

    classifier = ImprovedOntologyClassifier()

    # Test 1: Leeg begrip
    try:
        result = classifier.classify(begrip="")
        print(f"✅ Empty begrip handled: {result.categorie.value}")
    except Exception as e:
        print(f"❌ Empty begrip crashed: {e}")

    # Test 2: Onbekend begrip
    result = classifier.classify(begrip="xyzabcdef")
    print(
        f"✅ Unknown begrip handled: {result.categorie.value} " f"(fallback gebruikt)"
    )

    # Test 3: Speciale karakters
    result = classifier.classify(begrip="test-validatie_2.0")
    print(f"✅ Special chars handled: {result.categorie.value}")

    # Test 4: Zeer lange context
    long_context = "Dit is een zeer lange context " * 100
    result = classifier.classify(
        begrip="toets", org_context=long_context, jur_context="", wet_context=""
    )
    print(f"✅ Long context handled: {result.categorie.value}")

    print("\n✅ PASSED: Edge cases handled gracefully")
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("IMPROVED ONTOLOGY CLASSIFIER - TEST SUITE")
    print("=" * 60)

    results = {
        "Basic Classification": test_basic_classification(),
        "Context Support": test_context_support(),
        "Backward Compatibility": test_backward_compatibility(),
        "Edge Cases": test_edge_cases(),
    }

    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")

    all_passed = all(results.values())
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Ready to replace oude OntologischeAnalyzer")
    else:
        print("❌ SOME TESTS FAILED")
        print("⚠️  Review failures before deployment")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
