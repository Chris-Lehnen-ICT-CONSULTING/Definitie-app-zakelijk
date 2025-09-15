"""Tests voor ServiceFactory caching: dezelfde instance bij herhaalde calls.

TDD RED-test voor Fix 3: `get_definition_service(config)` moet voor identieke
configuraties dezelfde objectinstantie retourneren binnen hetzelfde proces,
zodat Streamlit-reruns geen herhaalde zware initialisatie veroorzaken.
"""

import sys
from pathlib import Path

# Voeg src toe aan sys.path voor directe imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import os
from services.service_factory import get_definition_service  # noqa: E402


def test_service_factory_returns_same_instance():
    """Herhaalde aanroepen met dezelfde config moeten dezelfde instance geven."""
    # Zorg voor geldige API key zodat initialisatie niet faalt in tests
    os.environ.setdefault("OPENAI_API_KEY", "test")
    config = {"db_path": ":memory:"}

    # Zorg dat caching niet wordt uitgeschakeld door pytest detectie
    os.environ.pop("PYTEST_CURRENT_TEST", None)
    service1 = get_definition_service(config)
    service2 = get_definition_service(config)

    assert service1 is service2
