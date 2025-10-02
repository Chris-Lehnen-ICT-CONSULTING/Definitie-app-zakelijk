"""
Parametrized tests for ServiceAdapter overall_score handling.
Covers various input types and edge cases concisely.
"""

from unittest.mock import AsyncMock, Mock

import pytest

from src.services.interfaces import Definition, DefinitionResponse
from src.services.service_factory import ServiceAdapter


@pytest.fixture()
def adapter_with_orchestrator():
    container = Mock()
    orchestrator = AsyncMock()
    orchestrator.get_stats = Mock(return_value={})
    container.orchestrator.return_value = orchestrator
    return ServiceAdapter(container), orchestrator


def _def_response(score_present: bool, score_value):
    mock_validation = Mock()
    # Build dict similar to production contract
    vd = {
        "is_acceptable": True,
        "violations": [],
        "passed_rules": ["rule1"],
    }
    if score_present:
        vd["overall_score"] = score_value

    mock_validation.to_dict.return_value = vd
    mock_validation.violations = vd["violations"]
    mock_validation.is_valid = vd["is_acceptable"]
    mock_validation.score = vd.get("overall_score", 0.0)
    mock_validation.errors = []
    mock_validation.suggestions = []

    return DefinitionResponse(
        success=True,
        definition=Definition(
            begrip="Test",
            definitie="Def",
            metadata={"origineel": "orig", "voorbeelden": {}},
        ),
        validation=mock_validation,
        message="Success",
    )


@pytest.mark.asyncio()
@pytest.mark.unit()
@pytest.mark.parametrize(
    "score_present, score_value, expected",
    [
        (True, 85.5, 85.5),  # float
        (True, 90, 90.0),  # int
        (True, "75.5", 75.5),  # numeric string
        (True, "", 0.0),  # empty string → default
        (True, None, 0.0),  # None → default
        (True, True, 1.0),  # bool True → 1.0
        (True, False, 0.0),  # bool False → 0.0
        (True, 0, 0.0),  # zero preserved
        (True, -10, -10.0),  # negative preserved
        (True, 1e308, 1e308),  # very large
        (False, None, 0.0),  # missing key → default
    ],
)
async def test_overall_score_param(
    adapter_with_orchestrator, score_present, score_value, expected
):
    adapter, orchestrator = adapter_with_orchestrator
    orchestrator.create_definition.return_value = _def_response(
        score_present, score_value
    )

    result = await adapter.generate_definition("Test", {})

    assert result["final_score"] == expected
    assert result["validation_details"]["overall_score"] == expected
