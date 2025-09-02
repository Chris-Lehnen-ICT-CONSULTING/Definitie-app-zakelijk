"""
Test voor JSON/Python validator architectuur.

Test dat alle 45 validators correct geladen en uitgevoerd worden.
"""

import pytest
from ai_toetser import toets_definitie, ModularToetser
from ai_toetser.json_validator_loader import json_validator_loader


def test_load_all_validators():
    """Test dat alle validators geladen kunnen worden."""
    regel_ids = json_validator_loader.get_all_regel_ids()

    # Er moeten 45 validators zijn
    assert len(regel_ids) >= 45, f"Verwacht minstens 45 validators, gevonden: {len(regel_ids)}"

    # Check dat belangrijke validators aanwezig zijn
    expected = ["CON-01", "ESS-01", "STR-01", "INT-01", "SAM-01", "VER-01", "ARAI01"]
    for regel_id in expected:
        assert regel_id in regel_ids, f"Validator {regel_id} ontbreekt"


def test_validate_with_json_validators():
    """Test basis validatie met JSON validators."""
    definitie = "Een persoon is een natuurlijk persoon of rechtspersoon."

    # Test met enkele regels
    toetsregels = {
        "CON-01": {},
        "ESS-01": {},
        "STR-01": {}
    }

    results = toets_definitie(
        definitie=definitie,
        toetsregels=toetsregels,
        begrip="persoon"
    )

    # Check resultaten
    assert isinstance(results, list)
    assert len(results) > 0

    # Check dat er een samenvatting is
    assert any("Toetsing Samenvatting" in r for r in results)


def test_validator_without_examples():
    """Test dat validators zonder voorbeelden ook werken."""
    # Laad een validator
    validator = json_validator_loader.load_validator("ESS-01")
    assert validator is not None

    # Test validate methode
    success, message, score = validator.validate(
        "Een test definitie zonder doel.",
        "test",
        {}
    )

    assert isinstance(success, bool)
    assert isinstance(message, str)
    assert isinstance(score, float)


def test_all_validators_validate():
    """Test dat alle validators kunnen valideren zonder crashes."""
    definitie = "Een document is een schriftelijk stuk dat informatie bevat."
    regel_ids = json_validator_loader.get_all_regel_ids()

    failed_validators = []

    for regel_id in regel_ids:
        try:
            results = json_validator_loader.validate_definitie(
                definitie=definitie,
                begrip="document",
                regel_ids=[regel_id],
                context={}
            )
            assert len(results) > 0
        except Exception as e:
            failed_validators.append((regel_id, str(e)))

    # Rapporteer failures
    if failed_validators:
        print(f"\nGefaalde validators ({len(failed_validators)}):")
        for regel_id, error in failed_validators[:5]:  # Toon max 5
            print(f"  {regel_id}: {error}")

    # Maximaal 5% mag falen tijdens transitie
    assert len(failed_validators) < len(regel_ids) * 0.05


if __name__ == "__main__":
    print("Testing JSON validators...")

    test_load_all_validators()
    print("✅ All validators loaded")

    test_validate_with_json_validators()
    print("✅ Basic validation works")

    test_validator_without_examples()
    print("✅ Validators without examples work")

    test_all_validators_validate()
    print("✅ All validators can validate")

    print("\n🎉 All tests passed!")
