"""Tests voor ServiceContainer: legacy 'validator' mapping verwijderd.

TDD RED-test voor Fix 1: `get_service('validator')` mag niet crashen en
moet netjes `None` teruggeven omdat de legacy validator is verwijderd.
"""

import sys
from pathlib import Path

# Voeg src toe aan sys.path voor directe imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from services.container import ServiceContainer


def test_get_service_validator_returns_none():
    """Legacy 'validator' service mag niet meer bestaan en moet None geven."""
    container = ServiceContainer()
    assert (  # Geen AttributeError; voorspelbaar None
        container.get_service("validator") is None
    )
