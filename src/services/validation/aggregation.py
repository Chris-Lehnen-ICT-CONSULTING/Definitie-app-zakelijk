"""Aggregation helpers for modular validation results.

Implements weighted scoring, acceptability checks, and category minimums
as simple, deterministic utilities.
"""

from __future__ import annotations

from typing import Any


def _round2(x: float) -> float:
    return round(float(x), 2)


def calculate_weighted_score(
    scores: dict[str, float], weights: dict[str, float]
) -> float:
    """Σ(w*s) / Σ(w), excluding zero or missing weights. Rounded to 2 decimals."""
    total_w = 0.0
    total_ws = 0.0
    for code, score in (scores or {}).items():
        w = float(weights.get(code, 0.0) or 0.0)
        if w <= 0.0:
            continue
        total_w += w
        total_ws += w * float(score or 0.0)
    if total_w == 0.0:
        return 0.0
    return _round2(total_ws / total_w)


def aggregate_rule_results(rule_results: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate a list of rule results into an overall score and metadata.

    Excludes errored rules from the aggregation, collects their codes in
    `errored_rules`. Returns a dict with `overall_score` (rounded).
    """
    total_w = 0.0
    total_ws = 0.0
    errored: list[str] = []
    for rr in rule_results or []:
        if rr.get("errored"):
            code = rr.get("rule_code") or rr.get("code")
            if code:
                errored.append(code)
            continue
        w = float(rr.get("weight", 1.0) or 0.0)
        if w <= 0.0:
            continue
        s = float(rr.get("score", 0.0) or 0.0)
        total_w += w
        total_ws += w * s

    overall = 0.0 if total_w == 0.0 else _round2(total_ws / total_w)
    return {"overall_score": overall, "errored_rules": errored}


def determine_acceptability(score: float, threshold: float) -> bool:
    """Accept if score >= threshold."""
    return float(score) >= float(threshold)


def check_category_minimums(
    detailed_scores: dict[str, float], category_minimums: dict[str, float]
) -> bool:
    """All categories with a declared minimum must meet that minimum."""
    if not category_minimums:
        return True
    for cat, min_val in (category_minimums or {}).items():
        if cat in detailed_scores and float(detailed_scores[cat]) < float(min_val):
            return False
    return True
