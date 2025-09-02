#!/usr/bin/env python3
"""
Test script voor de nieuwe ontologische categorisering.

Test de 6-stappen ontologische analyzer met verschillende voorbeelden.
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ontologie.ontological_analyzer import OntologischeAnalyzer, QuickOntologischeAnalyzer


async def test_ontological_analyzer():
    """Test de ontologische analyzer met verschillende begrippen."""
    print("🧪 Testing Ontologische Analyzer")
    print("=" * 50)

    # Test begrippen
    test_begrippen = [
        ("authenticatie", "Gemeente Amsterdam", "Wvggz"),
        ("document", "Overheid", "Wet openbaarheid van bestuur"),
        ("aanvrager", "Gemeente Utrecht", "Awb"),
        ("verificatie", "Ministerie", "Cybersecurity"),
        ("besluit", "Provincie", "Omgevingswet")
    ]

    analyzer = OntologischeAnalyzer()

    for begrip, org_context, jur_context in test_begrippen:
        print(f"\n📋 Analyseren: '{begrip}'")
        print(f"   Organisatie: {org_context}")
        print(f"   Juridisch: {jur_context}")

        try:
            # Test volledige 6-stappen analyse
            categorie, analyse_resultaat = await analyzer.bepaal_ontologische_categorie(
                begrip, org_context, jur_context
            )

            print(f"   ✅ Categorie: {categorie.value}")
            print(f"   📊 Confidence: {analyse_resultaat.get('categorie_resultaat', {}).get('confidence', 0.0):.2f}")

            # Toon semantische kenmerken
            kenmerken = analyse_resultaat.get('semantisch_profiel', {}).get('semantische_kenmerken', {})
            positieve_kenmerken = [k for k, v in kenmerken.items() if v]
            if positieve_kenmerken:
                print(f"   🔍 Kenmerken: {', '.join(positieve_kenmerken)}")

            # Toon gevonden definities
            definities = analyse_resultaat.get('semantisch_profiel', {}).get('definities', [])
            if definities:
                print(f"   📚 Gevonden definities: {len(definities)}")

        except Exception as e:
            print(f"   ❌ Fout: {e}")


async def test_quick_analyzer():
    """Test de quick analyzer."""
    print("\n🚀 Testing Quick Ontologische Analyzer")
    print("=" * 50)

    quick_analyzer = QuickOntologischeAnalyzer()

    test_begrippen = [
        "authenticatie",
        "document",
        "aanvrager",
        "verificatie",
        "besluit",
        "systeem",
        "gebruiker",
        "controle"
    ]

    for begrip in test_begrippen:
        categorie, reasoning = quick_analyzer.quick_categoriseer(begrip)
        print(f"   '{begrip}' → {categorie.value} ({reasoning})")


async def main():
    """Hoofdfunctie voor testing."""
    print("🔬 Ontologische Analyzer Test Suite")
    print("=" * 60)

    try:
        # Test volledige analyzer
        await test_ontological_analyzer()

        # Test quick analyzer
        await test_quick_analyzer()

        print("\n✅ Alle tests voltooid!")

    except Exception as e:
        print(f"\n❌ Test mislukt: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
