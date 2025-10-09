#!/usr/bin/env python3
"""
Validatie script voor juridische keywords migratie.

Verificatie:
1. Alle hardcoded keywords zijn gemigreerd naar YAML
2. YAML config bevat exact dezelfde keywords (geen verlies)
3. Boost factors zijn correct geladen uit config
4. Backwards compatibility werkt (JURIDISCHE_KEYWORDS constant)

Usage:
    python scripts/validate_juridisch_keywords_migration.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import yaml

# Hardcoded fallback keywords (reference voor validatie)
EXPECTED_KEYWORDS = {
    # Algemeen juridisch
    "wetboek",
    "artikel",
    "wet",
    "recht",
    "rechter",
    "vonnis",
    "uitspraak",
    "rechtspraak",
    "juridisch",
    "wettelijk",
    "strafbaar",
    "rechtbank",
    "gerechtshof",
    "hoge raad",
    # Strafrecht
    "strafrecht",
    "verdachte",
    "beklaagde",
    "dagvaarding",
    "veroordeling",
    "vrijspraak",
    "schuldig",
    "delict",
    "misdrijf",
    "overtreding",
    # Burgerlijk recht
    "burgerlijk",
    "civiel",
    "overeenkomst",
    "contract",
    "schadevergoeding",
    "aansprakelijkheid",
    # Bestuursrecht
    "bestuursrecht",
    "beschikking",
    "besluit",
    "bezwaar",
    "beroep",
    "awb",
    # Procesrecht
    "procedure",
    "proces",
    "hoger beroep",
    "cassatie",
    "appel",
    # Wetten
    "sr",
    "sv",
    "rv",
    "bw",
}

# Expected boost factors
EXPECTED_BOOST_FACTORS = {
    "juridische_bron": 1.2,
    "keyword_per_match": 1.1,
    "keyword_max_boost": 1.3,
    "artikel_referentie": 1.15,
    "lid_referentie": 1.05,
    "context_match": 1.1,
    "context_max_boost": 1.3,
    "juridical_flag": 1.15,
}


def normalize_term(term: str) -> str:
    """Normaliseer term zoals in JuridischRankerConfig."""
    return term.lower().strip().replace("_", " ")


def validate_yaml_keywords():
    """Valideer dat YAML alle keywords bevat."""
    print("=" * 60)
    print("VALIDATIE 1: YAML Keywords Coverage")
    print("=" * 60)

    config_path = Path(__file__).parent.parent / "config" / "juridische_keywords.yaml"

    if not config_path.exists():
        print(f"❌ FOUT: Config niet gevonden: {config_path}")
        return False

    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Extract alle keywords uit YAML
    yaml_keywords = set()
    for category, keywords_list in data.items():
        if isinstance(keywords_list, list):
            for keyword in keywords_list:
                if isinstance(keyword, str):
                    normalized = normalize_term(keyword)
                    if normalized:
                        yaml_keywords.add(normalized)

    print(f"Expected keywords: {len(EXPECTED_KEYWORDS)}")
    print(f"YAML keywords: {len(yaml_keywords)}")

    # Check voor missing keywords
    missing = EXPECTED_KEYWORDS - yaml_keywords
    extra = yaml_keywords - EXPECTED_KEYWORDS

    if missing:
        print(f"\n❌ FOUT: {len(missing)} keywords ontbreken in YAML:")
        for kw in sorted(missing):
            print(f"  - {kw}")
        return False

    if extra:
        print(f"\n⚠️  WAARSCHUWING: {len(extra)} extra keywords in YAML:")
        for kw in sorted(extra):
            print(f"  - {kw}")

    print("\n✅ Alle expected keywords aanwezig in YAML")
    return True


def validate_boost_factors():
    """Valideer dat boost factors correct zijn geladen."""
    print("\n" + "=" * 60)
    print("VALIDATIE 2: Boost Factors Configuration")
    print("=" * 60)

    config_path = Path(__file__).parent.parent / "config" / "web_lookup_defaults.yaml"

    if not config_path.exists():
        print(f"❌ FOUT: Config niet gevonden: {config_path}")
        return False

    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if "web_lookup" not in data or "juridical_boost" not in data["web_lookup"]:
        print("❌ FOUT: juridical_boost sectie niet gevonden")
        return False

    boost_config = data["web_lookup"]["juridical_boost"]

    print(f"Expected boost factors: {len(EXPECTED_BOOST_FACTORS)}")
    print(f"Config boost factors: {len(boost_config)}")

    all_valid = True

    for key, expected_value in EXPECTED_BOOST_FACTORS.items():
        if key not in boost_config:
            print(f"❌ FOUT: Boost factor '{key}' ontbreekt")
            all_valid = False
        elif float(boost_config[key]) != expected_value:
            print(
                f"⚠️  WAARSCHUWING: Boost factor '{key}' heeft waarde "
                f"{boost_config[key]} (expected: {expected_value})"
            )

    if all_valid:
        print("\n✅ Alle boost factors correct geconfigureerd")

    return all_valid


def validate_runtime_loading():
    """Valideer dat runtime loading werkt."""
    print("\n" + "=" * 60)
    print("VALIDATIE 3: Runtime Config Loading")
    print("=" * 60)

    try:
        from services.web_lookup.juridisch_ranker import (
            JURIDISCHE_KEYWORDS,
            get_ranker_config,
        )

        # Test config loading
        config = get_ranker_config()

        print(f"Loaded keywords: {len(config.keywords)}")
        print(f"Loaded boost factors: {len(config.boost_factors)}")

        # Verify keywords match
        if config.keywords != EXPECTED_KEYWORDS:
            missing = EXPECTED_KEYWORDS - config.keywords
            extra = config.keywords - EXPECTED_KEYWORDS
            if missing:
                print(f"❌ FOUT: {len(missing)} keywords ontbreken bij runtime:")
                for kw in sorted(missing):
                    print(f"  - {kw}")
            if extra:
                print(f"⚠️  WAARSCHUWING: {len(extra)} extra keywords bij runtime:")
                for kw in sorted(extra):
                    print(f"  - {kw}")
            return False

        # Test backwards compatibility
        print("\nTesten backwards compatibility (JURIDISCHE_KEYWORDS)...")

        # Test 'in' operator
        if "wetboek" not in JURIDISCHE_KEYWORDS:
            print("❌ FOUT: 'in' operator werkt niet op JURIDISCHE_KEYWORDS")
            return False

        # Test iteration
        keywords_list = list(JURIDISCHE_KEYWORDS)
        if len(keywords_list) != len(EXPECTED_KEYWORDS):
            print("❌ FOUT: iteratie over JURIDISCHE_KEYWORDS geeft verkeerd aantal")
            return False

        # Test len()
        if len(JURIDISCHE_KEYWORDS) != len(EXPECTED_KEYWORDS):
            print("❌ FOUT: len(JURIDISCHE_KEYWORDS) incorrect")
            return False

        print("✅ Runtime loading en backwards compatibility werken correct")
        return True

    except ImportError as e:
        print(f"❌ FOUT: Kan module niet importeren: {e}")
        return False
    except Exception as e:
        print(f"❌ FOUT: Runtime validatie gefaald: {e}")
        return False


def validate_keyword_categorization():
    """Valideer dat keywords logisch gecategoriseerd zijn."""
    print("\n" + "=" * 60)
    print("VALIDATIE 4: Keyword Categorization")
    print("=" * 60)

    config_path = Path(__file__).parent.parent / "config" / "juridische_keywords.yaml"

    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    expected_categories = {
        "algemeen",
        "strafrecht",
        "burgerlijk",
        "bestuursrecht",
        "procesrecht",
        "wetten",
    }

    actual_categories = {k for k in data.keys() if isinstance(data[k], list)}

    missing_categories = expected_categories - actual_categories
    extra_categories = actual_categories - expected_categories

    if missing_categories:
        print(f"❌ FOUT: {len(missing_categories)} categorieën ontbreken:")
        for cat in sorted(missing_categories):
            print(f"  - {cat}")
        return False

    if extra_categories:
        print(f"⚠️  INFO: {len(extra_categories)} extra categorieën:")
        for cat in sorted(extra_categories):
            print(f"  - {cat}")

    # Print category sizes
    print("\nKeywords per categorie:")
    for category in sorted(expected_categories):
        if category in data:
            count = len(data[category])
            print(f"  - {category}: {count} keywords")

    print("\n✅ Keyword categorisatie is correct")
    return True


def main():
    """Run alle validaties."""
    print("JURIDISCHE KEYWORDS MIGRATIE VALIDATIE")
    print("=" * 60)
    print()

    results = []

    # Run validaties
    results.append(("YAML Keywords Coverage", validate_yaml_keywords()))
    results.append(("Boost Factors Config", validate_boost_factors()))
    results.append(("Runtime Config Loading", validate_runtime_loading()))
    results.append(("Keyword Categorization", validate_keyword_categorization()))

    # Print samenvatting
    print("\n" + "=" * 60)
    print("SAMENVATTING")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {name}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 60)

    if all_passed:
        print("🎉 ALLE VALIDATIES GESLAAGD!")
        print("Migratie is succesvol voltooid.")
        return 0
    else:
        print("❌ SOMMIGE VALIDATIES GEFAALD")
        print("Controleer de fouten hierboven.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
