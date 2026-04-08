"""
Quick UI smoke test voor beide modes.
"""

import os
import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.smoke]

# Voeg src toe aan path
sys.path.insert(0, str(Path(__file__).parent / "src"))


@pytest.mark.parametrize("use_new_services", [False, True], ids=["legacy", "new"])
def test_ui_mode(use_new_services):
    """Test UI in een specifieke mode."""
    os.environ["USE_NEW_SERVICES"] = str(use_new_services).lower()

    # Import UI components
    # Check service factory
    from services.service_factory import get_definition_service
    from ui.tabbed_interface import TabbedInterface

    service = get_definition_service()
    assert service is not None

    # Test basic operations
    assert hasattr(service, "generate_definition") or hasattr(
        service, "genereer_definitie"
    )

    # Check UI initialization
    interface = TabbedInterface()
    assert interface is not None
