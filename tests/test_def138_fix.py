"""
Test voor DEF-138 fix: Handelingsnaamwoorden vs ARAI-01.

Dit test bestand verifieert dat:
1. Handelingsnaamwoorden (observatie, verzameling) worden geaccepteerd
2. Vervoegde werkwoorden (is, wordt, heeft) worden afgewezen
3. De contradictie tussen ARAI-01 en PROCES categorie is opgelost
"""

import json
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import validator using the correct file name (with hyphen)
import importlib.util

spec = importlib.util.spec_from_file_location(
    "ARAI_01", Path(__file__).parent.parent / "src/toetsregels/regels/ARAI-01.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
ARAI01Validator = module.ARAI01Validator


def test_arai01_allows_handelingsnaamwoorden():
    """Test dat handelingsnaamwoorden (action nouns) worden toegestaan."""
    # Load config
    config_path = Path(__file__).parent.parent / "src/toetsregels/regels/ARAI-01.json"
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    validator = ARAI01Validator(config)

    # Test cases met handelingsnaamwoorden die MOETEN slagen
    valid_definitions = [
        "observatie van gedrag in natuurlijke omgeving",
        "verzameling van relevante documenten door systematische selectie",
        "registratie waarbij gegevens formeel worden vastgelegd",
        "activiteit waarbij data wordt verzameld",
        "proces dat beslissers identificeert",
        "handeling die resulteert in een besluit",
        "beoordeling van prestaties volgens criteria",
        "analyse waarbij documenten worden vergeleken",
    ]

    print("\n✅ Testing VALID definitions with handelingsnaamwoorden:")
    for definition in valid_definitions:
        success, message, score = validator.validate(definition, "test_begrip")
        print(f"  {'✓' if success else '✗'} {definition[:50]}...")
        if not success:
            print(f"    ERROR: {message}")
        assert success, f"Handelingsnaamwoord definition should pass: {definition}"
        assert score >= 0.5, f"Score should be at least 0.5, got {score}"


def test_arai01_blocks_conjugated_verbs():
    """Test dat vervoegde werkwoorden aan het begin worden geblokkeerd."""
    config_path = Path(__file__).parent.parent / "src/toetsregels/regels/ARAI-01.json"
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    validator = ARAI01Validator(config)

    # Test cases met vervoegde werkwoorden die MOETEN falen
    invalid_definitions = [
        "is een observatie van gedrag",
        "wordt gebruikt voor het verzamelen van data",
        "heeft als doel het registreren van gegevens",
        "kan worden omschreven als een proces",
        "moet worden gezien als een activiteit",
        "zijn handelingen die leiden tot",
        "doet aan analyse van documenten",
        "creëert een overzicht van resultaten",
    ]

    print("\n❌ Testing INVALID definitions with conjugated verbs:")
    for definition in invalid_definitions:
        success, message, score = validator.validate(definition, "test_begrip")
        print(f"  {'✗' if not success else '✓'} {definition[:50]}...")
        if success:
            print("    ERROR: Should have failed but passed!")
        assert not success, f"Conjugated verb definition should fail: {definition}"
        assert score < 0.5, f"Score should be less than 0.5, got {score}"


def test_proces_category_compatibility():
    """Test dat PROCES categorie definities compatible zijn met ARAI-01."""
    config_path = Path(__file__).parent.parent / "src/toetsregels/regels/ARAI-01.json"
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    validator = ARAI01Validator(config)

    # PROCES definities uit semantic_categorisation_module voorbeelden
    proces_definitions = [
        "activiteit waarbij gegevens worden verzameld door directe waarneming",
        "handeling waarin door middel van vraaggesprekken informatie wordt verzameld",
        "proces waarin documenten systematisch worden geanalyseerd",
    ]

    print("\n🔄 Testing PROCES category definitions:")
    for definition in proces_definitions:
        success, message, score = validator.validate(definition, "test_proces")
        print(f"  {'✓' if success else '✗'} {definition[:50]}...")
        if not success:
            print(f"    ERROR: {message}")
        assert success, f"PROCES definition should pass ARAI-01: {definition}"


def test_edge_cases():
    """Test edge cases zoals gerundiums en complexe constructies."""
    config_path = Path(__file__).parent.parent / "src/toetsregels/regels/ARAI-01.json"
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    validator = ARAI01Validator(config)

    test_cases = [
        # (definition, should_pass, description)
        (
            "het verzamelen van gegevens door middel van observatie",
            True,
            "Gerundium (het + infinitief)",
        ),
        ("het observeren gebeurt in natuurlijke setting", True, "Gerundium as subject"),
        (
            "Een observatie is een gestructureerde waarneming",
            True,
            "Noun followed by 'is' is OK",
        ),
        (
            "observatie wordt gedefinieerd als systematische waarneming",
            True,
            "Noun first, verb later",
        ),
        ("  is een proces waarbij", False, "Leading whitespace + verb"),
        ("Wordt gedefinieerd als", False, "Starts with passive verb"),
    ]

    print("\n🔍 Testing edge cases:")
    for definition, should_pass, description in test_cases:
        success, message, score = validator.validate(definition, "test_edge")
        result = "✓" if success == should_pass else "✗"
        print(f"  {result} {description}: {definition[:40]}...")
        if success != should_pass:
            print(
                f"    ERROR: Expected {'pass' if should_pass else 'fail'}, got {'pass' if success else 'fail'}"
            )
            print(f"    Message: {message}")
        assert success == should_pass, f"Edge case failed: {description}"


if __name__ == "__main__":
    print("=" * 60)
    print("DEF-138 FIX VALIDATION TESTS")
    print("Testing handelingsnaamwoorden vs ARAI-01 compatibility")
    print("=" * 60)

    test_arai01_allows_handelingsnaamwoorden()
    test_arai01_blocks_conjugated_verbs()
    test_proces_category_compatibility()
    test_edge_cases()

    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("The DEF-138 fix successfully resolves the contradiction.")
    print("=" * 60)
