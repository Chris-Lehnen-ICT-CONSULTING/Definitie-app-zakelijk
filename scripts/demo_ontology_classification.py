#!/usr/bin/env python3
"""
Demo script voor Ontology Classification System.

Toont hoe het nieuwe classificatie systeem gebruikt wordt.

Usage:
    python scripts/demo_ontology_classification.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from unittest.mock import Mock

from src.services.classification.ontology_classifier import OntologyClassifierService


def create_demo_classifier():
    """Create demo classifier met mocked AI service."""
    # Mock AI service voor demo (geen spec zodat we attributes kunnen toevoegen)
    ai_service = Mock()

    # Setup mock responses voor verschillende begrippen
    def mock_generate(prompt, system_prompt=None, **kwargs):
        """Mock LLM responses based on begrip in prompt."""
        if "appel" in prompt.lower():
            return json.dumps(
                {
                    "level": "TYPE",
                    "confidence": 0.88,
                    "rationale": "Het begrip 'appel' verwijst naar een algemene categorie fruit zonder specifieke instantie. De definitie gebruikt termen die toepasbaar zijn op alle appels.",
                    "linguistic_cues": [
                        "algemene categorie",
                        "soort fruit",
                        "toepasbaar op meerdere instanties",
                    ],
                }
            )
        elif "verificatie" in prompt.lower() or "verifiëren" in prompt.lower():
            return json.dumps(
                {
                    "level": "PROCES",
                    "confidence": 0.92,
                    "rationale": "Het begrip beschrijft een handeling die wordt uitgevoerd. De '-tie' suffix en termen zoals 'controleren' wijzen op een proces.",
                    "linguistic_cues": [
                        "handeling",
                        "-tie suffix",
                        "werkwoord 'controleren'",
                        "activiteit",
                    ],
                }
            )
        elif "verleende vergunning" in prompt.lower():
            return json.dumps(
                {
                    "level": "RESULTAAT",
                    "confidence": 0.85,
                    "rationale": "Het begrip beschrijft de uitkomst van een proces (vergunningverlening). Het woord 'verleende' is een voltooid deelwoord, wat duidt op een afgerond proces.",
                    "linguistic_cues": [
                        "voltooid deelwoord 'verleende'",
                        "resultaat van proces",
                        "eindproduct",
                    ],
                }
            )
        elif "dit specifieke document" in prompt.lower():
            return json.dumps(
                {
                    "level": "EXEMPLAAR",
                    "confidence": 0.90,
                    "rationale": "Het begrip verwijst naar een concrete, specifieke instantie ('dit specifieke'). De demonstratief 'dit' wijst op een uniek exemplaar.",
                    "linguistic_cues": [
                        "demonstratief 'dit'",
                        "bijvoeglijk 'specifieke'",
                        "concrete verwijzing",
                    ],
                }
            )
        else:
            return json.dumps(
                {
                    "level": "ONBESLIST",
                    "confidence": 0.3,
                    "rationale": "Het begrip is niet eenduidig te classificeren zonder meer context.",
                    "linguistic_cues": ["ambigue betekenis"],
                }
            )

    ai_service.generate_completion.side_effect = mock_generate

    # Create classifier
    classifier = OntologyClassifierService(ai_service)

    # Override prompt template voor demo
    classifier.system_prompt = "Demo system prompt"
    classifier.user_template = (
        "Begrip: {begrip}\nDefinitie: {definitie}\n{context_section}"
    )

    return classifier


def print_section(title):
    """Print section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_result(result):
    """Print classification result."""
    emoji_map = {
        "TYPE": "📦",
        "EXEMPLAAR": "🎯",
        "PROCES": "⚙️",
        "RESULTAAT": "✅",
        "ONBESLIST": "❓",
    }

    emoji = emoji_map.get(result.level, "❓")

    print(f"{emoji} Classificatie: {result.level}")
    print(f"   Confidence: {result.confidence:.0%}")
    print(f"   Redenering: {result.rationale}")

    if result.linguistic_cues:
        print("   Linguïstische aanwijzingen:")
        for cue in result.linguistic_cues:
            print(f"     - {cue}")

    if result.validation_warnings:
        print("   ⚠️  Validatie waarschuwingen:")
        for warning in result.validation_warnings:
            print(f"     - {warning}")

    print()


def demo_basic_classification():
    """Demo: Basis classificatie."""
    print_section("DEMO 1: Basis Classificatie")

    classifier = create_demo_classifier()

    # Voorbeeld 1: TYPE
    print("Begrip: appel")
    print("Definitie: Een soort fruit dat behoort tot de rozenfamilie\n")
    result = classifier.classify(
        begrip="appel", definitie="Een soort fruit dat behoort tot de rozenfamilie"
    )
    print_result(result)


def demo_with_context():
    """Demo: Classificatie met context."""
    print_section("DEMO 2: Classificatie met Context")

    classifier = create_demo_classifier()

    print("Begrip: verificatie")
    print("Definitie: Het controleren van de juistheid van gegevens")
    print("Context: Juridische procedures")
    print("Voorbeelden:")
    print("  - Het verifiëren van identiteit bij aanmelding")
    print("  - De verificatie van documenten door de ambtenaar\n")

    result = classifier.classify(
        begrip="verificatie",
        definitie="Het controleren van de juistheid van gegevens",
        context="Juridische procedures",
        voorbeelden=[
            "Het verifiëren van identiteit bij aanmelding",
            "De verificatie van documenten door de ambtenaar",
        ],
    )
    print_result(result)


def demo_batch_classification():
    """Demo: Batch classificatie."""
    print_section("DEMO 3: Batch Classificatie")

    classifier = create_demo_classifier()

    items = [
        {"begrip": "appel", "definitie": "Een soort fruit"},
        {"begrip": "verifiëren", "definitie": "Het controleren van juistheid"},
        {
            "begrip": "verleende vergunning",
            "definitie": "Het resultaat van de vergunningsprocedure",
        },
        {
            "begrip": "dit specifieke document",
            "definitie": "Deze concrete instantie van een document",
        },
    ]

    print(f"Classificeren van {len(items)} begrippen in batch...\n")

    results = classifier.classify_batch(items)

    for item, result in zip(items, results, strict=False):
        print(f"📝 {item['begrip']}")
        print(f"   → {result.level} ({result.confidence:.0%} confidence)")
        print()


def demo_validation_warnings():
    """Demo: Validatie waarschuwingen."""
    print_section("DEMO 4: Validatie Waarschuwingen")

    classifier = create_demo_classifier()

    # Force TYPE classificatie voor proces-achtig begrip
    def force_type_response(prompt, **kwargs):
        return json.dumps(
            {
                "level": "TYPE",
                "confidence": 0.65,
                "rationale": "Beschrijft een categorie (kunstmatige classificatie voor demo)",
                "linguistic_cues": ["algemeen begrip"],
            }
        )

    classifier.ai_service.generate_completion.side_effect = force_type_response

    print("Begrip: verificatieprocedure")
    print("Definitie: De handeling van het systematisch controleren van documenten")
    print("\nDit begrip klinkt als PROCES, maar wordt geclassificeerd als TYPE...\n")

    result = classifier.classify(
        begrip="verificatieprocedure",
        definitie="De handeling van het systematisch controleren van documenten",
    )
    print_result(result)

    if result.validation_warnings:
        print("✓ Validator heeft correcte waarschuwingen gegenereerd!")
    else:
        print("⚠️  Validator heeft geen waarschuwingen gegenereerd (onverwacht)")


def demo_all_categories():
    """Demo: Alle ontologische categorieën."""
    print_section("DEMO 5: Alle Ontologische Categorieën")

    classifier = create_demo_classifier()

    examples = [
        ("TYPE", "appel", "Een soort fruit"),
        ("PROCES", "verificatie", "Het controleren van juistheid"),
        ("RESULTAAT", "verleende vergunning", "Het resultaat van vergunningsprocedure"),
        ("EXEMPLAAR", "dit specifieke document", "Deze concrete instantie"),
    ]

    print("Overzicht van alle categorieën:\n")

    for expected_level, begrip, definitie in examples:
        result = classifier.classify(begrip, definitie)

        status = "✓" if result.level == expected_level else "✗"
        print(f"{status} {result.level:12s} | {begrip:30s} | {result.confidence:.0%}")

    print()


def main():
    """Run all demos."""
    print("\n" + "█" * 80)
    print("  ONTOLOGY CLASSIFICATION SYSTEM - DEMO")
    print("█" * 80)

    try:
        demo_basic_classification()
        demo_with_context()
        demo_batch_classification()
        demo_validation_warnings()
        demo_all_categories()

        print_section("DEMO VOLTOOID")
        print("✓ Alle demos succesvol uitgevoerd!")
        print("\nVoor meer informatie, zie:")
        print("  - docs/technisch/ontology_classification_integration.md")
        print("  - docs/architectuur/ontology_classification_implementation_roadmap.md")
        print()

    except Exception as e:
        print(f"\n❌ Demo gefaald: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
