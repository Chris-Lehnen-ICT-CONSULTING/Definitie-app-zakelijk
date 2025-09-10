"""
Schema tests voor het canonieke VoorbeeldenDict contract.

Test dat voorbeelden altijd de juiste structuur hebben en geen legacy keys bevatten.
"""

import pytest
from typing import Any

from services.interfaces import VoorbeeldenDict
from voorbeelden import genereer_alle_voorbeelden


def test_voorbeelden_canonical_keys():
    """Test dat voorbeelden altijd canonieke keys hebben."""
    # Test data
    begrip = "testbegrip"
    definitie = "Een test definitie voor het begrip."
    context_dict = {
        "organisatorisch": ["Test Organisatie"],
        "juridisch": ["Test Domein"],  # Let op: dit is CONTEXT, niet voorbeelden type
        "wettelijk": ["Test Wetgeving"],
    }

    # Generate voorbeelden
    voorbeelden = genereer_alle_voorbeelden(begrip, definitie, context_dict)

    # Verplichte keys moeten aanwezig zijn
    assert "voorbeeldzinnen" in voorbeelden, "voorbeeldzinnen key ontbreekt"
    assert "praktijkvoorbeelden" in voorbeelden, "praktijkvoorbeelden key ontbreekt"
    assert "tegenvoorbeelden" in voorbeelden, "tegenvoorbeelden key ontbreekt"

    # Optionele keys mogen aanwezig zijn
    # Deze worden altijd gegenereerd volgens de code
    assert "synoniemen" in voorbeelden, "synoniemen key verwacht"
    assert "antoniemen" in voorbeelden, "antoniemen key verwacht"
    assert "toelichting" in voorbeelden, "toelichting key verwacht"

    # GEEN legacy keys
    assert "juridisch" not in voorbeelden, "Legacy key 'juridisch' gevonden - moet voorbeeldzinnen zijn"
    assert "praktijk" not in voorbeelden, "Legacy key 'praktijk' gevonden - moet praktijkvoorbeelden zijn"

    # Type checking - verplichte velden zijn lijsten
    assert isinstance(voorbeelden["voorbeeldzinnen"], list), "voorbeeldzinnen moet een lijst zijn"
    assert isinstance(voorbeelden["praktijkvoorbeelden"], list), "praktijkvoorbeelden moet een lijst zijn"
    assert isinstance(voorbeelden["tegenvoorbeelden"], list), "tegenvoorbeelden moet een lijst zijn"

    # Optionele velden
    assert isinstance(voorbeelden["synoniemen"], list), "synoniemen moet een lijst zijn"
    assert isinstance(voorbeelden["antoniemen"], list), "antoniemen moet een lijst zijn"
    assert isinstance(voorbeelden["toelichting"], str), "toelichting moet een string zijn"


def test_voorbeelden_businesslogica_aantallen():
    """Test dat de businesslogica voor aantallen voorbeelden behouden blijft."""
    from voorbeelden.unified_voorbeelden import DEFAULT_EXAMPLE_COUNTS

    # Businesslogica: default aantallen per type
    assert DEFAULT_EXAMPLE_COUNTS["voorbeeldzinnen"] == 3, "Default voorbeeldzinnen moet 3 zijn"
    assert DEFAULT_EXAMPLE_COUNTS["praktijkvoorbeelden"] == 3, "Default praktijkvoorbeelden moet 3 zijn"
    assert DEFAULT_EXAMPLE_COUNTS["tegenvoorbeelden"] == 3, "Default tegenvoorbeelden moet 3 zijn"
    assert DEFAULT_EXAMPLE_COUNTS["synoniemen"] == 5, "Default synoniemen moet 5 zijn"
    assert DEFAULT_EXAMPLE_COUNTS["antoniemen"] == 5, "Default antoniemen moet 5 zijn"
    assert DEFAULT_EXAMPLE_COUNTS["toelichting"] == 1, "Default toelichting moet 1 zijn"


def test_voorbeelden_contract_matches_typedef():
    """Test dat gegenereerde voorbeelden matchen met VoorbeeldenDict TypedDict."""
    # Test data
    begrip = "contracttest"
    definitie = "Test voor contract matching."
    context_dict = {
        "organisatorisch": ["Test"],
        "juridisch": [],
        "wettelijk": [],
    }

    # Generate voorbeelden
    voorbeelden = genereer_alle_voorbeelden(begrip, definitie, context_dict)

    # Check dat structuur overeenkomt met VoorbeeldenDict
    # We kunnen niet direct type-checken tijdens runtime, maar we kunnen
    # wel de structuur valideren

    required_keys = {"voorbeeldzinnen", "praktijkvoorbeelden", "tegenvoorbeelden"}
    optional_keys = {"synoniemen", "antoniemen", "toelichting"}

    # Check dat alle keys geldig zijn
    all_valid_keys = required_keys | optional_keys
    actual_keys = set(voorbeelden.keys())

    invalid_keys = actual_keys - all_valid_keys
    assert not invalid_keys, f"Ongeldige keys gevonden: {invalid_keys}"

    # Check dat verplichte keys aanwezig zijn
    missing_required = required_keys - actual_keys
    assert not missing_required, f"Verplichte keys ontbreken: {missing_required}"


def test_orchestrator_metadata_voorbeelden():
    """Test dat orchestrator voorbeelden correct in metadata zet."""
    # Dit test de integratie maar we kunnen het contract testen
    # door te checken dat de structuur klopt

    example_metadata = {
        "voorbeelden": {
            "voorbeeldzinnen": ["Voorbeeld 1", "Voorbeeld 2"],
            "praktijkvoorbeelden": ["Praktijk 1"],
            "tegenvoorbeelden": ["Tegen 1"],
            "synoniemen": ["Synoniem 1"],
            "antoniemen": ["Antoniem 1"],
            "toelichting": "Dit is een toelichting",
        }
    }

    voorbeelden = example_metadata["voorbeelden"]

    # Validate structure
    assert "voorbeeldzinnen" in voorbeelden
    assert "praktijkvoorbeelden" in voorbeelden
    assert "tegenvoorbeelden" in voorbeelden

    # No legacy keys
    assert "juridisch" not in voorbeelden
    assert "praktijk" not in voorbeelden


def test_ui_response_voorbeelden_type():
    """Test dat UIResponseDict voorbeelden van juiste type zijn."""
    from services.interfaces import UIResponseDict

    # Create example UI response
    ui_response: UIResponseDict = {
        "success": True,
        "definitie_origineel": "origineel",
        "definitie_gecorrigeerd": "gecorrigeerd",
        "final_score": 0.9,
        "validation_details": {
            "overall_score": 0.9,
            "is_acceptable": True,
            "violations": [],
            "passed_rules": ["RULE1", "RULE2"],
        },
        "voorbeelden": {
            "voorbeeldzinnen": ["Voorbeeld 1"],
            "praktijkvoorbeelden": ["Praktijk 1"],
            "tegenvoorbeelden": ["Tegen 1"],
            "synoniemen": ["Synoniem 1"],
            "antoniemen": ["Antoniem 1"],
            "toelichting": "Toelichting",
        },
        "metadata": {
            "prompt_text": "test prompt",
            "model": "gpt-4",
        },
        "sources": [],
    }

    # Check voorbeelden structure
    voorbeelden = ui_response["voorbeelden"]

    # Verplichte velden
    assert isinstance(voorbeelden["voorbeeldzinnen"], list)
    assert isinstance(voorbeelden["praktijkvoorbeelden"], list)
    assert isinstance(voorbeelden["tegenvoorbeelden"], list)

    # Optionele velden
    if "synoniemen" in voorbeelden:
        assert isinstance(voorbeelden["synoniemen"], list | type(None))
    if "antoniemen" in voorbeelden:
        assert isinstance(voorbeelden["antoniemen"], list | type(None))
    if "toelichting" in voorbeelden:
        assert isinstance(voorbeelden["toelichting"], str | type(None))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
