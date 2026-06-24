"""AI-call-contract test voor OntologicalClassifier (DEF-439).

De classifier riep `self.ai_service.generate_text(...)` aan, een methode die
niet op AIServiceV2 bestaat. Het brede `except Exception` in `classify`
verpakte de AttributeError als RuntimeError → classificatie faalde altijd
(live aangeroepen vanuit global_context_renderer.py). Een `Mock(spec=AIServiceV2)`
dwingt het echte contract af: alleen `generate_definition` bestaat.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from services.ai_service_v2 import AIServiceV2
from services.classification.ontological_classifier import (
    OntologicalClassifier,
    OntologicalLevel,
)

pytestmark = [pytest.mark.unit]


async def test_classify_uses_generate_definition():
    """classify() haalt tekst via generate_definition().text, niet generate_text()."""
    ai = Mock(spec=AIServiceV2)
    ai.generate_definition = AsyncMock(
        return_value=SimpleNamespace(
            text=(
                '{"level": "F", "confidence": 0.82, "rationale": "functioneel begrip",'
                ' "scores": {"U": 0.1, "F": 0.8, "O": 0.1}}'
            )
        )
    )

    classifier = OntologicalClassifier(ai)
    result = await classifier.classify("Overeenkomst")

    ai.generate_definition.assert_called_once()
    assert result.level == OntologicalLevel.FUNCTIONEEL
    assert result.confidence == 0.82
