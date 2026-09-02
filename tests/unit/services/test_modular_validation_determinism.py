"""Tests for deterministic behavior of ModularValidationService."""

import pytest

from services.validation.interfaces import VALIDATION_STATUS_VALIDATED
from toetsregels.manager import get_toetsregel_manager

pytestmark = [pytest.mark.unit]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_deterministic_results_identical_inputs():
    """Two identical runs must produce identical results."""
    m = pytest.importorskip(
        "services.validation.modular_validation_service",
        reason="ModularValidationService not implemented yet",
    )

    svc = m.ModularValidationService
    # DEF-621: de echte contractmanager. Zonder manager levert de guard twee
    # identieke `validation_unknown`-resultaten - dan is determinisme
    # triviaal waar en bewijst deze suite niets over de evaluator.
    service = svc(get_toetsregel_manager(), None, None)

    # Run validation twice with identical inputs
    begrip = "test_begrip"
    text = "Dit is een test definitie met voldoende inhoud om gevalideerd te worden."
    context = {"correlation_id": "test-determinism-123"}

    result1 = await service.validate_definition(
        begrip=begrip,
        text=text,
        ontologische_categorie=None,
        context=context,
    )

    result2 = await service.validate_definition(
        begrip=begrip,
        text=text,
        ontologische_categorie=None,
        context=context,
    )

    # Results must be identical
    # Zonder deze regel zouden twee lege validation_unknown-resultaten de
    # determinisme-assertie ook waarmaken.
    assert result1["validation_status"] == VALIDATION_STATUS_VALIDATED, result1
    assert result2["validation_status"] == VALIDATION_STATUS_VALIDATED, result2

    assert (
        result1["overall_score"] == result2["overall_score"]
    ), "Scores must be identical"
    assert (
        result1["is_acceptable"] == result2["is_acceptable"]
    ), "Acceptability must be identical"

    # Violations must be identical (same codes in same order)
    violations1 = [v["code"] for v in result1.get("violations", [])]
    violations2 = [v["code"] for v in result2.get("violations", [])]
    assert (
        violations1 == violations2
    ), f"Violations must be identical: {violations1} != {violations2}"

    # Passed rules must be identical
    assert result1.get("passed_rules", []) == result2.get(
        "passed_rules", []
    ), "Passed rules must be identical"

    # Detailed scores must be identical
    for category in ["taal", "juridisch", "structuur", "samenhang"]:
        score1 = result1["detailed_scores"].get(category, 0.0)
        score2 = result2["detailed_scores"].get(category, 0.0)
        assert (
            score1 == score2
        ), f"Category {category} scores must be identical: {score1} != {score2}"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_deterministic_results_different_correlation_ids():
    """Different correlation IDs should not affect determinism of scores."""
    m = pytest.importorskip(
        "services.validation.modular_validation_service",
        reason="ModularValidationService not implemented yet",
    )

    svc = m.ModularValidationService
    # DEF-621: de echte contractmanager. Zonder manager levert de guard twee
    # identieke `validation_unknown`-resultaten - dan is determinisme
    # triviaal waar en bewijst deze suite niets over de evaluator.
    service = svc(get_toetsregel_manager(), None, None)

    begrip = "test_begrip"
    text = "Dit is een test definitie met voldoende inhoud om gevalideerd te worden."

    result1 = await service.validate_definition(
        begrip=begrip,
        text=text,
        ontologische_categorie=None,
        context={"correlation_id": "id-1"},
    )

    result2 = await service.validate_definition(
        begrip=begrip,
        text=text,
        ontologische_categorie=None,
        context={"correlation_id": "id-2"},
    )

    # Scores and violations must still be identical
    assert result1["validation_status"] == VALIDATION_STATUS_VALIDATED, result1
    assert result2["validation_status"] == VALIDATION_STATUS_VALIDATED, result2
    assert result1["overall_score"] == result2["overall_score"]
    assert result1["is_acceptable"] == result2["is_acceptable"]

    violations1 = [v["code"] for v in result1.get("violations", [])]
    violations2 = [v["code"] for v in result2.get("violations", [])]
    assert violations1 == violations2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_deterministic_violation_order():
    """Violations must always be returned in sorted order by code."""
    m = pytest.importorskip(
        "services.validation.modular_validation_service",
        reason="ModularValidationService not implemented yet",
    )

    svc = m.ModularValidationService
    # DEF-621: de echte contractmanager. Zonder manager levert de guard twee
    # identieke `validation_unknown`-resultaten - dan is determinisme
    # triviaal waar en bewijst deze suite niets over de evaluator.
    service = svc(get_toetsregel_manager(), None, None)

    # Use a definition that will trigger multiple violations
    result = await service.validate_definition(
        begrip="test",
        text="Test.",  # Too short, will trigger multiple violations
        ontologische_categorie=None,
        context=None,
    )

    # Zonder deze regel is de test triviaal groen bij validation_unknown: een
    # lege violationslijst is per definitie gesorteerd.
    assert result["validation_status"] == VALIDATION_STATUS_VALIDATED, result

    violation_codes = [v["code"] for v in result.get("violations", [])]

    # Check that codes are sorted
    sorted_codes = sorted(violation_codes)
    assert (
        violation_codes == sorted_codes
    ), f"Violations must be sorted: {violation_codes} != {sorted_codes}"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_deterministic_floating_point_rounding():
    """Scores must be consistently rounded to 2 decimal places."""
    m = pytest.importorskip(
        "services.validation.modular_validation_service",
        reason="ModularValidationService not implemented yet",
    )

    svc = m.ModularValidationService
    # DEF-621: de echte contractmanager. Zonder manager levert de guard twee
    # identieke `validation_unknown`-resultaten - dan is determinisme
    # triviaal waar en bewijst deze suite niets over de evaluator.
    service = svc(get_toetsregel_manager(), None, None)

    result = await service.validate_definition(
        begrip="test",
        text="Een test definitie die een score oplevert met veel decimalen door gewogen aggregatie.",
        ontologische_categorie=None,
        context=None,
    )

    # Zonder deze regel is de test triviaal groen bij validation_unknown:
    # score 0.0 is al afgerond en `detailed_scores` is leeg, dus de lus
    # hieronder draait geen enkele keer.
    assert result["validation_status"] == VALIDATION_STATUS_VALIDATED, result

    # Check overall score has at most 2 decimal places
    score = result["overall_score"]
    assert score == round(score, 2), f"Score must be rounded to 2 decimals: {score}"

    # Check all detailed scores have at most 2 decimal places
    for category, cat_score in result["detailed_scores"].items():
        assert cat_score == round(
            cat_score, 2
        ), f"Category {category} score must be rounded to 2 decimals: {cat_score}"


@pytest.mark.unit
def test_deterministic_rule_evaluation_order():
    """Rules must be evaluated in sorted order by code for determinism."""
    m = pytest.importorskip(
        "services.validation.modular_validation_service",
        reason="ModularValidationService not implemented yet",
    )

    # This test checks the implementation detail that rules are sorted
    # We can inspect the service's internal rule ordering if exposed
    svc_cls = m.ModularValidationService

    # Check if the service has a method or property that exposes rule order
    if hasattr(svc_cls, "_get_rule_evaluation_order"):
        service = svc_cls()
        order = service._get_rule_evaluation_order()
        sorted_order = sorted(order)
        assert order == sorted_order, "Rules must be evaluated in sorted order"
    else:
        # If not exposed, we skip this implementation detail test
        pytest.skip("Rule evaluation order not exposed in API")
