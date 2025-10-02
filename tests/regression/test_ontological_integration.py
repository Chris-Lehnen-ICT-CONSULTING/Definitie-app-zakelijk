#!/usr/bin/env python3
"""Test script voor OntologischeAnalyzer met echte WebLookupService integratie."""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ontologie.ontological_analyzer import OntologischeAnalyzer

logging.basicConfig(level=logging.INFO)


async def test_integration():
    """Test de nieuwe integratie."""
    try:
        print("🧪 Test OntologischeAnalyzer met ModernWebLookupService...")

        # Maak analyzer instance
        analyzer = OntologischeAnalyzer()
        print("✅ Analyzer succesvol geïnitialiseerd")

        # Test lexicale verkenning
        print("\n📚 Test lexicale verkenning voor 'democratie'...")
        resultaat = await analyzer._stap1_lexicale_verkenning("democratie")

        print(f"Gevonden definities: {len(resultaat['definities'])}")
        if resultaat["definities"]:
            print(
                f"Eerste definitie bron: {resultaat['definities'][0].get('bron', 'Onbekend')}"
            )

        print(f"Semantische kenmerken: {resultaat['semantische_kenmerken']}")
        print(f"Bron kwaliteit: {resultaat['bron_kwaliteit']}")

        # Test context analyse
        print("\n📋 Test context analyse...")
        context_resultaat = await analyzer._stap2_context_analyse(
            "verificatie", "Justid", "Migratierecht"
        )

        print(
            f"Juridische verwijzingen: {len(context_resultaat['juridische_verwijzingen'])}"
        )
        print(
            f"Gedetecteerde bronnen: {len(context_resultaat['gedetecteerde_bronnen'])}"
        )

        print("\n✅ Alle tests geslaagd!")

    except Exception as e:
        print(f"\n❌ Test gefaald: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_integration())
