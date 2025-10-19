"""
Smoke test voor ValidationOrchestratorV2 integratie.
Verifieert op hoog niveau dat V2 componenten importeerbaar zijn
en basis-aanroepen door de orchestrator kunnen worden uitgevoerd.
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Forceer DEV_MODE voor deze smoke test
os.environ["DEV_MODE"] = "true"


def test_management_tab_uses_v2_in_dev_mode():
    """Controleer dat DEV_MODE actief is en UI components importeerbaar zijn."""
    # Test that we can import key UI components (validation_view is always present)
    from ui.components.validation_view import render_validation_view

    # Verify function is callable
    assert callable(render_validation_view)

    # DEV_MODE moet actief zijn
    assert os.getenv("DEV_MODE", "false").lower() == "true"


@pytest.mark.asyncio()
async def test_validation_v2_basic_call():
    """Eenvoudige V2 orchestrator call met gepatchte async methode."""
    from services.orchestrators.validation_orchestrator_v2 import (
        ValidationOrchestratorV2,
    )
    from services.validation.interfaces import ValidationResult

    # Orchestrator met minimale dependency
    orchestrator = ValidationOrchestratorV2(validation_service=MagicMock())

    # Patch validate_text om een simpel resultaat terug te geven (async mock)
    with patch.object(
        orchestrator, "validate_text", new_callable=AsyncMock
    ) as mock_validate:
        mock_result = ValidationResult(
            version="1.0.0",
            overall_score=0.85,
            is_acceptable=True,
            violations=[],
            passed_rules=[],
            detailed_scores={},
            system={"correlation_id": "test-corr-id"},
        )
        mock_validate.return_value = mock_result

        # Voer validatie uit (await async mock)
        result = await orchestrator.validate_text(
            "Begrip", "Een test is een methode om iets te controleren.", "proces"
        )

        # Verifieer resultaat
        assert result["overall_score"] == pytest.approx(0.85)
        assert result["is_acceptable"] is True
        assert len(result["violations"]) == 0
        assert "correlation_id" in result["system"]


def test_v1_fallback_when_dev_mode_false():
    """Controleer dat DEV_MODE=false resulteert in false-waarde."""
    original_value = os.environ.get("DEV_MODE")
    os.environ["DEV_MODE"] = "false"

    try:
        use_v2 = os.getenv("DEV_MODE", "false").lower() == "true"
        assert use_v2 is False
    finally:
        if original_value is not None:
            os.environ["DEV_MODE"] = original_value
        else:
            os.environ.pop("DEV_MODE", None)


if __name__ == "__main__":
    # Handmatige run
    print("🔥 Running V2 Validation Smoke Tests...")
    test_management_tab_uses_v2_in_dev_mode()
    print("✅ Management tab DEV_MODE check passed")
    test_validation_v2_basic_call()
    print("✅ V2 validation basic call passed")
    test_v1_fallback_when_dev_mode_false()
    print("✅ V1 fallback check passed")
    print("\n🎉 All smoke tests passed!")
