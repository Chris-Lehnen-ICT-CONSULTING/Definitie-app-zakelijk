#!/usr/bin/env python3
"""
Test script voor schone voorbeelden generatie architectuur.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from generation.definitie_generator import DefinitieGenerator, GenerationContext, OntologischeCategorie
from voorbeelden import genereer_alle_voorbeelden


def test_clean_architecture():
    """Test de schone architectuur voor voorbeelden generatie."""
    print("🧪 Testing Schone Voorbeelden Architectuur")
    print("=" * 50)

    # Stap 1: Genereer definitie
    print("\n📝 STAP 1: Genereer definitie")
    generator = DefinitieGenerator()

    context = GenerationContext(
        begrip="toets",
        organisatorische_context="KMAR",
        juridische_context="Strafrecht",
        categorie=OntologischeCategorie.TYPE
    )

    try:
        # Genereer ALLEEN definitie
        result = generator.generate(context)
        print(f"✅ Definitie: {result.definitie[:100]}...")
        print(f"📊 Voorbeelden in result: {result.voorbeelden_gegenereerd}")

    except Exception as e:
        print(f"❌ Error genereren definitie: {e}")
        return

    # Stap 2: Genereer voorbeelden apart
    print("\n📚 STAP 2: Genereer voorbeelden (apart)")

    context_dict = {
        'organisatorische_context': [context.organisatorische_context],
        'juridische_context': [context.juridische_context]
    }

    try:
        voorbeelden = genereer_alle_voorbeelden(
            begrip=context.begrip,
            definitie=result.definitie,
            context_dict=context_dict
        )

        print(f"✅ Voorbeelden gegenereerd: {len(voorbeelden)} types")

        for example_type, examples in voorbeelden.items():
            print(f"\n{example_type}:")
            for i, example in enumerate(examples[:2], 1):  # Eerste 2 van elk type
                print(f"  {i}. {example}")

    except Exception as e:
        print(f"❌ Error genereren voorbeelden: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_clean_architecture()
