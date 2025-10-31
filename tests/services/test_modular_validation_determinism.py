"""Tests for deterministic behavior of ModularValidationService."""

import pytest


@pytest.mark.unit
@pytest.mark.asyncio
async def test_deterministic_results_identical_inputs():
    """Two identical runs must produce identical results."""
    m = pytest.importorskip(
        "services.validation.modular_validation_service",
        reason="ModularValidationService not implemented yet",
    )

    svc = m.ModularValidationService
    try:
        service = svc(toetsregel_manager=None, cleaning_service=None, config=None)
    except TypeError:
        service = svc()

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
    try:
        service = svc(toetsregel_manager=None, cleaning_service=None, config=None)
    except TypeError:
        service = svc()

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
    try:
        service = svc(toetsregel_manager=None, cleaning_service=None, config=None)
    except TypeError:
        service = svc()

    # Use a definition that will trigger multiple violations
    result = await service.validate_definition(
        begrip="test",
        text="Test.",  # Too short, will trigger multiple violations
        ontologische_categorie=None,
        context=None,
    )

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
    try:
        service = svc(toetsregel_manager=None, cleaning_service=None, config=None)
    except TypeError:
        service = svc()

    result = await service.validate_definition(
        begrip="test",
        text="Een test definitie die een score oplevert met veel decimalen door gewogen aggregatie.",
        ontologische_categorie=None,
        context=None,
    )

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
