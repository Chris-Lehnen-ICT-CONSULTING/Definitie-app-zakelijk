import pytest


def test_calculate_weighted_score_basic():
    from services.validation.aggregation import calculate_weighted_score

    scores = {"A": 1.0, "B": 0.5, "C": 0.0}
    weights = {"A": 1.0, "B": 2.0, "C": 1.0}
    # (1.0*1 + 0.5*2 + 0*1) / (1+2+1) = (1 + 1 + 0) / 4 = 0.5 → round2 0.5
    assert calculate_weighted_score(scores, weights) == 0.5


def test_calculate_weighted_score_ignores_zero_weights():
    from services.validation.aggregation import calculate_weighted_score

    scores = {"A": 1.0, "B": 0.0}
    weights = {"A": 0.0, "B": 0.0}
    assert calculate_weighted_score(scores, weights) == 0.0


def test_aggregate_rule_results_ignores_errored():
    from services.validation.aggregation import aggregate_rule_results

    rule_results = [
        {"rule_code": "X", "score": 0.8, "weight": 1.0},
        {"rule_code": "Y", "errored": True},
        {"rule_code": "Z", "score": 0.6, "weight": 2.0},
    ]
    agg = aggregate_rule_results(rule_results)
    # (0.8*1 + 0.6*2) / (1+2) = 2.0/3 ≈ 0.67 → round2 0.67
    assert agg["overall_score"] == 0.67
    assert agg["errored_rules"] == ["Y"]


def test_determine_acceptability_boundary():
    from services.validation.aggregation import determine_acceptability

    assert determine_acceptability(0.75, 0.75) is True
    assert determine_acceptability(0.749, 0.75) is False


def test_check_category_minimums():
    from services.validation.aggregation import check_category_minimums

    detailed = {"taal": 0.8, "juridisch": 0.75, "structuur": 0.7, "samenhang": 0.9}
    minimums = {"juridisch": 0.7, "structuur": 0.7}
    assert check_category_minimums(detailed, minimums) is True

    minimums_fail = {"juridisch": 0.76}
    assert check_category_minimums(detailed, minimums_fail) is False
