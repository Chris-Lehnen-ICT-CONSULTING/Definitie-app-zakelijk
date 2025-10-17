#!/usr/bin/env python3
"""Vergelijk QuickAnalyzer vs. Volledige 6-stappen Analyzer."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

async def compare_analyzers():
    """Test of QuickAnalyzer hetzelfde resultaat geeft als volledige analyzer."""
    from ontologie.ontological_analyzer import (OntologischeAnalyzer,
                                                QuickOntologischeAnalyzer)

    print("\n" + "="*80)
    print("🧪 VERGELIJKING: QuickAnalyzer vs. 6-Stappen Analyzer")
    print("="*80 + "\n")

    # Test begrippen uit verschillende categorieën
    test_begrippen = [
        # PROCES (eindigt op -atie, -ing, -tie)
        "validatie",
        "authenticatie",
        "registratie",
        "behandeling",
        "beoordeling",

        # TYPE (bevat type/soort/klasse woorden)
        "toets",
        "document",
        "systeem",
        "formulier",

        # RESULTAAT (bevat resultaat/uitkomst woorden)
        "sanctie",
        "besluit",
        "rapport",

        # GEMENGD (moeilijke gevallen)
        "aanvraag",
        "vergunning",
        "rechter",
    ]

    full_analyzer = OntologischeAnalyzer()
    quick_analyzer = QuickOntologischeAnalyzer()

    differences = []
    agreements = []

    for begrip in test_begrippen:
        print(f"📝 Begrip: '{begrip}'")
        print("-" * 80)

        # Quick Analyzer
        quick_cat, quick_reason = quick_analyzer.quick_categoriseer(begrip)
        print(f"   Quick:  {quick_cat.value:12} - {quick_reason}")

        # Full Analyzer (met timing)
        import time
        start = time.time()
        full_cat, full_result = await full_analyzer.bepaal_ontologische_categorie(
            begrip, "", ""
        )
        elapsed = time.time() - start

        # Haal test scores op
        test_scores = full_result.get("categorie_resultaat", {}).get("test_scores", {})
        confidence = full_result.get("categorie_resultaat", {}).get("confidence", 0.0)

        print(f"   Full:   {full_cat.value:12} - confidence: {confidence:.2f} ({elapsed:.3f}s)")

        # Toon test scores
        if test_scores:
            scores_str = ", ".join([f"{k}:{v:.2f}" for k, v in sorted(test_scores.items(), key=lambda x: x[1], reverse=True)])
            print(f"           Scores: {scores_str}")

        # Vergelijk
        if quick_cat == full_cat:
            print(f"   ✅ OVEREENSTEMMING")
            agreements.append(begrip)
        else:
            print(f"   ❌ VERSCHIL! Quick={quick_cat.value}, Full={full_cat.value}")
            differences.append({
                "begrip": begrip,
                "quick": quick_cat.value,
                "full": full_cat.value,
                "confidence": confidence,
                "scores": test_scores
            })

        print()

    # Samenvatting
    print("="*80)
    print("📊 SAMENVATTING")
    print("="*80)
    print(f"Totaal getest: {len(test_begrippen)}")
    print(f"Overeenstemming: {len(agreements)} ({len(agreements)/len(test_begrippen)*100:.1f}%)")
    print(f"Verschillen: {len(differences)} ({len(differences)/len(test_begrippen)*100:.1f}%)")

    if differences:
        print("\n❌ VERSCHILLEN:")
        for diff in differences:
            print(f"   • {diff['begrip']:15} Quick={diff['quick']:10} Full={diff['full']:10} (conf={diff['confidence']:.2f})")
            if diff['scores']:
                print(f"     Scores: {diff['scores']}")

    if agreements:
        print(f"\n✅ OVEREENSTEMMING: {', '.join(agreements)}")

    print("\n" + "="*80)
    print("🔍 CONCLUSIE")
    print("="*80)

    if len(differences) == 0:
        print("✅ QuickAnalyzer geeft IDENTIEKE resultaten aan 6-stappen analyzer")
        print("   → 6-stappen is overengineered")
    elif len(differences) <= 2:
        print(f"⚠️  QuickAnalyzer verschilt in {len(differences)} gevallen")
        print("   → Mogelijk verwaarloosbaar verschil")
    else:
        print(f"❌ QuickAnalyzer verschilt significant ({len(differences)} gevallen)")
        print("   → 6-stappen analyzer voegt waarde toe")

if __name__ == "__main__":
    asyncio.run(compare_analyzers())
