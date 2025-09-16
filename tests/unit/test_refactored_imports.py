"""
Test imports for refactored modules.
"""

import os
import sys

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_utils_imports():
    """Test utils module imports."""
    from utils.exceptions import APIError, DefinitieAgentError, ValidationError

    assert DefinitieAgentError
    assert APIError
    assert ValidationError


def test_ui_imports():
    """Test UI module imports."""
    from ui.components import UIComponents
    from ui.session_state import SessionStateManager

    assert SessionStateManager
    assert UIComponents


def test_services_imports():
    """Test services module imports (nieuwe architectuur)."""
    from services.service_factory import get_definition_service

    service = get_definition_service()
    assert service is not None


def test_session_state_defaults():
    """Test session state default values."""
    from ui.session_state import SessionStateManager

    defaults = SessionStateManager.DEFAULT_VALUES
    assert isinstance(defaults, dict)
    assert "gegenereerd" in defaults
    assert "beoordeling_gen" in defaults


def test_definition_service_creation():
    """Test dat service via factory kan worden verkregen."""
    from services.service_factory import get_definition_service

    service = get_definition_service()
    assert service is not None
    # Minimale interfacecontrole
    assert hasattr(service, "get_stats")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
