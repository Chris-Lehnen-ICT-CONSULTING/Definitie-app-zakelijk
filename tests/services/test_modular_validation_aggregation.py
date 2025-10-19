"""Tests for aggregation logic in ModularValidationService."""

import pytest


@pytest.mark.unit()
def test_weighted_sum_aggregation_formula():
    """Test the weighted sum aggregation: Σ(weight × score) / Σ(weights)."""
    m = pytest.importorskip(
        "services.validation.aggregation",
        reason="Aggregation module not implemented yet",
    )

    calculate_weighted_score = getattr(m, "calculate_weighted_score", None)
    if not calculate_weighted_score:
        pytest.skip("calculate_weighted_score function not found")

    # Test case 1: Simple equal weights
    scores = {"rule1": 0.8, "rule2": 0.6, "rule3": 1.0}
    weights = {"rule1": 1.0, "rule2": 1.0, "rule3": 1.0}

    result = calculate_weighted_score(scores, weights)
    (0.8 * 1.0 + 0.6 * 1.0 + 1.0 * 1.0) / (1.0 + 1.0 + 1.0)  # = 2.4 / 3.0 = 0.8
    assert result == pytest.approx(0.80, abs=0.01)

    # Test case 2: Different weights
    scores = {"rule1": 0.5, "rule2": 0.8, "rule3": 1.0}
    weights = {"rule1": 2.0, "rule2": 1.0, "rule3": 0.5}

    result = calculate_weighted_score(scores, weights)
    (0.5 * 2.0 + 0.8 * 1.0 + 1.0 * 0.5) / (2.0 + 1.0 + 0.5)  # = 2.3 / 3.5 = 0.657
    assert result == pytest.approx(0.66, abs=0.01)  # Rounded to 2 decimals

    # Test case 3: Some rules with zero weight (should be excluded)
    scores = {"rule1": 0.5, "rule2": 0.8, "rule3": 0.0}
    weights = {"rule1": 1.0, "rule2": 1.0, "rule3": 0.0}

    result = calculate_weighted_score(scores, weights)
    (0.5 * 1.0 + 0.8 * 1.0) / (1.0 + 1.0)  # = 1.3 / 2.0 = 0.65
    assert result == pytest.approx(0.65, abs=0.01)

    # Test case 4: All zero weights (edge case)
    scores = {"rule1": 0.5, "rule2": 0.8}
    weights = {"rule1": 0.0, "rule2": 0.0}

    result = calculate_weighted_score(scores, weights)
    assert result == 0.0  # Default when no weights


@pytest.mark.unit()
def test_aggregation_two_decimal_rounding():
    """Test that aggregated scores are rounded to exactly 2 decimal places."""
    m = pytest.importorskip(
        "services.validation.aggregation",
        reason="Aggregation module not implemented yet",
    )

    calculate_weighted_score = getattr(m, "calculate_weighted_score", None)
    if not calculate_weighted_score:
        pytest.skip("calculate_weighted_score function not found")

    # Test cases that produce many decimal places
    test_cases = [
        # (scores, weights, expected_rounded)
        ({"r1": 0.333, "r2": 0.666}, {"r1": 1.0, "r2": 1.0}, 0.50),  # 0.4995 -> 0.50
        (
            {"r1": 0.7, "r2": 0.8, "r3": 0.9},
            {"r1": 1.1, "r2": 1.2, "r3": 1.3},
            0.81,
        ),  # 0.8055... -> 0.81
        ({"r1": 0.123, "r2": 0.456}, {"r1": 2.5, "r2": 1.5}, 0.25),  # 0.2461 -> 0.25
        ({"r1": 0.999}, {"r1": 1.0}, 1.00),  # 0.999 -> 1.00
        ({"r1": 0.001}, {"r1": 1.0}, 0.00),  # 0.001 -> 0.00
    ]

    for scores, weights, expected in test_cases:
        result = calculate_weighted_score(scores, weights)
        # Check exact 2 decimal places
        assert result == expected, f"Expected {expected} but got {result}"
        # Verify it's actually rounded to 2 decimals
        assert result == round(result, 2)


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_category_aggregation():
    """Test aggregation per category (taal, juridisch, structuur, samenhang)."""
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
        text="Een definitie voor het testen van categorie aggregatie met verschillende scores.",
        ontologische_categorie=None,
        context=None,
    )

    # Check that all categories have scores
    assert "detailed_scores" in result
    for category in ["taal", "juridisch", "structuur", "samenhang"]:
        assert category in result["detailed_scores"], f"Missing category: {category}"
        score = result["detailed_scores"][category]
        assert 0.0 <= score <= 1.0, f"Category {category} score out of range: {score}"
        assert score == round(
            score, 2
        ), f"Category {category} not rounded to 2 decimals: {score}"


@pytest.mark.unit()
def test_aggregation_with_missing_rules():
    """Test aggregation when some rules are missing or errored."""
    m = pytest.importorskip(
        "services.validation.aggregation",
        reason="Aggregation module not implemented yet",
    )

    aggregate_rule_results = getattr(m, "aggregate_rule_results", None)
    if not aggregate_rule_results:
        pytest.skip("aggregate_rule_results function not found")

    # Mock rule results with some errored rules
    rule_results = [
        {"rule_code": "ESS-01", "score": 0.8, "weight": 1.0, "errored": False},
        {
            "rule_code": "CON-01",
            "score": 0.0,
            "weight": 1.0,
            "errored": True,
        },  # Errored rule
        {"rule_code": "STR-01", "score": 0.7, "weight": 2.0, "errored": False},
    ]

    result = aggregate_rule_results(rule_results)

    # Errored rule should be excluded from aggregation
    (0.8 * 1.0 + 0.7 * 2.0) / (1.0 + 2.0)  # = 2.2 / 3.0 = 0.733...
    assert result["overall_score"] == pytest.approx(0.73, abs=0.01)

    # Check that errored rules are tracked
    assert "errored_rules" in result
    assert "CON-01" in result["errored_rules"]


@pytest.mark.unit()
def test_aggregation_acceptability_threshold():
    """Test is_acceptable based on overall_score >= threshold (default 0.75)."""
    m = pytest.importorskip(
        "services.validation.aggregation",
        reason="Aggregation module not implemented yet",
    )

    determine_acceptability = getattr(m, "determine_acceptability", None)
    if not determine_acceptability:
        pytest.skip("determine_acceptability function not found")

    # Test cases: (score, threshold, expected_acceptable)
    test_cases = [
        (0.76, 0.75, True),  # Above threshold
        (0.75, 0.75, True),  # Exactly at threshold
        (0.74, 0.75, False),  # Just below threshold
        (0.50, 0.75, False),  # Well below threshold
        (0.90, 0.75, True),  # Well above threshold
        (0.80, 0.60, True),  # Custom lower threshold
        (0.50, 0.60, False),  # Below custom threshold
    ]

    for score, threshold, expected in test_cases:
        result = determine_acceptability(score, threshold)
        assert (
            result == expected
        ), f"Score {score} with threshold {threshold} should be acceptable={expected}"


@pytest.mark.unit()
def test_category_minimum_thresholds():
    """Test that category minimums can override overall acceptability."""
    m = pytest.importorskip(
        "services.validation.aggregation",
        reason="Aggregation module not implemented yet",
    )

    check_category_minimums = getattr(m, "check_category_minimums", None)
    if not check_category_minimums:
        pytest.skip("check_category_minimums function not found")

    # Even with high overall score, if a category is below minimum, not acceptable
    detailed_scores = {
        "taal": 0.80,
        "juridisch": 0.40,  # Below minimum
        "structuur": 0.85,
        "samenhang": 0.90,
    }

    category_minimums = {
        "taal": 0.50,
        "juridisch": 0.60,  # Minimum not met
        "structuur": 0.50,
        "samenhang": 0.50,
    }

    result = check_category_minimums(detailed_scores, category_minimums)
    assert result is False, "Should fail when juridisch is below minimum"

    # All categories meet minimum
    detailed_scores["juridisch"] = 0.65
    result = check_category_minimums(detailed_scores, category_minimums)
    assert result is True, "Should pass when all categories meet minimum"
