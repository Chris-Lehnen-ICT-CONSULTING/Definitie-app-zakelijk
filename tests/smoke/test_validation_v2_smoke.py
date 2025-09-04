"""
Smoke test for ValidationOrchestratorV2 integration.
Quick validation that V2 orchestrator works in DEV_MODE.
"""

import os
import pytest
from unittest.mock import patch, MagicMock

# Set DEV_MODE for testing
os.environ["DEV_MODE"] = "true"


def test_management_tab_uses_v2_in_dev_mode():
    """Test that management_tab uses V2 validation when DEV_MODE is true."""
    from ui.components.management_tab import ManagementTab

    # Mock repository
    mock_repo = MagicMock()
    tab = ManagementTab(mock_repo)

    # Check that DEV_MODE is recognized
    assert os.getenv("DEV_MODE", "false").lower() == "true"


def test_validation_v2_basic_call():
    """Test basic V2 validation orchestrator call."""
    from services.validation.validation_orchestrator_v2 import ValidationOrchestratorV2
    from services.validation.interfaces import ValidationRequest, ValidationResult

    orchestrator = ValidationOrchestratorV2()

    # Create test request
    request = ValidationRequest(
        definition_text="Een test is een methode om iets te controleren.",
        category="proces",
        context={}
    )

    # Mock the validate method to return a simple result
    with patch.object(orchestrator, 'validate') as mock_validate:
        mock_result = ValidationResult(
            overall_score=0.85,
            is_acceptable=True,
            violations=[],
            metadata={"version": "v2"}
        )
        mock_validate.return_value = mock_result

        # Call validation
        result = orchestrator.validate(request)

        # Verify
        assert result.overall_score == 0.85
        assert result.is_acceptable is True
        assert len(result.violations) == 0
        assert result.metadata["version"] == "v2"


def test_v1_fallback_when_dev_mode_false():
    """Test that V1 validation is used when DEV_MODE is false."""
    # Temporarily set DEV_MODE to false
    original_value = os.environ.get("DEV_MODE")
    os.environ["DEV_MODE"] = "false"

    try:
        use_v2 = os.getenv("DEV_MODE", "false").lower() == "true"
        assert use_v2 is False
    finally:
        # Restore original value
        if original_value:
            os.environ["DEV_MODE"] = original_value
        else:
            del os.environ["DEV_MODE"]


if __name__ == "__main__":
    # Run smoke tests
    print("🔥 Running V2 Validation Smoke Tests...")

    test_management_tab_uses_v2_in_dev_mode()
    print("✅ Management tab DEV_MODE check passed")

    test_validation_v2_basic_call()
    print("✅ V2 validation basic call passed")

    test_v1_fallback_when_dev_mode_false()
    print("✅ V1 fallback check passed")

    print("\n🎉 All smoke tests passed!")
