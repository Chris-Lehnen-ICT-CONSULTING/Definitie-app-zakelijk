#!/usr/bin/env python3
"""Test wat er ECHT gebeurt in de OntologischeAnalyzer."""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Setup logging om ALLES te zien
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_analyzer():
    """Test de analyzer en log elke stap."""
    print("\n" + "="*80)
    print("🧪 TEST: Wat gebeurt er ECHT in OntologischeAnalyzer?")
    print("="*80 + "\n")

    from domain.ontological_categories import OntologischeCategorie
    from ontologie.ontological_analyzer import OntologischeAnalyzer

    # Test begrip
    begrip = "validatie"
    org_context = "gemeente"
    jur_context = "bestuursrecht"

    print(f"📝 Test begrip: '{begrip}'")
    print(f"   Org context: '{org_context}'")
    print(f"   Jur context: '{jur_context}'")
    print("\n" + "-"*80 + "\n")

    try:
        # Initialiseer analyzer
        print("🔧 Initialiseren analyzer...")
        analyzer = OntologischeAnalyzer()
        print("✅ Analyzer geïnitialiseerd\n")

        # Roep bepaal_ontologische_categorie aan
        print("🚀 Start bepaal_ontologische_categorie...")
        import time
        start_time = time.time()

        categorie, resultaat = await analyzer.bepaal_ontologische_categorie(
            begrip, org_context, jur_context
        )

        elapsed = time.time() - start_time
        print(f"\n⏱️  Totale tijd: {elapsed:.3f} seconden")
        print("\n" + "-"*80 + "\n")

        # Toon resultaten
        print(f"📊 RESULTAAT:")
        print(f"   Categorie: {categorie.value}")
        print(f"   Type: {type(categorie)}")
        print(f"\n📋 Analyse resultaat keys:")
        for key in resultaat.keys():
            print(f"   - {key}")

        # Toon reasoning
        if "reasoning" in resultaat:
            print(f"\n💭 REASONING:")
            print(f"{resultaat['reasoning']}")

        # Toon test scores als aanwezig
        if "categorie_resultaat" in resultaat:
            scores = resultaat["categorie_resultaat"].get("test_scores", {})
            if scores:
                print(f"\n🎯 TEST SCORES:")
                for cat, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
                    print(f"   {cat:12} : {score:.3f}")

        # Check of stap 1 werd uitgevoerd
        if "semantisch_profiel" in resultaat:
            profiel = resultaat["semantisch_profiel"]
            definities = profiel.get("definities", [])
            print(f"\n🔍 STAP 1 (Lexicale verkenning):")
            print(f"   Aantal definities gevonden: {len(definities)}")
            print(f"   Bron kwaliteit: {profiel.get('bron_kwaliteit', 0.0)}")
            if definities:
                print(f"   Eerste definitie bron: {definities[0].get('bron', 'N/A')}")

        # Check of stap 2 werd uitgevoerd
        if "context_map" in resultaat:
            context = resultaat["context_map"]
            juridisch = context.get("juridische_verwijzingen", [])
            print(f"\n🏛️  STAP 2 (Context analyse):")
            print(f"   Juridische verwijzingen: {len(juridisch)}")
            print(f"   Domein: {context.get('domein_analyse', {})}")

        print("\n" + "="*80)
        print("✅ TEST VOLTOOID")
        print("="*80 + "\n")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_analyzer())
