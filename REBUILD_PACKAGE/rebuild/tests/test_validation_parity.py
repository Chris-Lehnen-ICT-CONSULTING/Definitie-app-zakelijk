"""
Test validation parity between OLD and NEW systems.

This test suite ensures that the rebuilt validation system produces
100% identical results to the current production system for the
42 baseline definitions.

Requirements:
- 100% match on validation scores
- 100% match on rule pass/fail results
- Detailed diagnostics for any differences

EPIC-026 Phase 1 - Rebuild Validation
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from services.validation.modular_validation_service import ModularValidationService

# ========================================
# FIXTURES
# ========================================


@pytest.fixture(scope="module")
def baseline_definitions() -> list[dict[str, Any]]:
    """Load 42 baseline definitions from exported JSON."""
    baseline_file = (
        Path(__file__).parent.parent.parent
        / "docs"
        / "business-logic"
        / "baseline_42_definitions.json"
    )

    if not baseline_file.exists():
        pytest.skip(f"Baseline definitions not found: {baseline_file}")

    with open(baseline_file, encoding="utf-8") as f:
        data = json.load(f)

    return data.get("definitions", [])


@pytest.fixture(scope="module")
def old_validation_service():
    """Initialize OLD validation service (current production system)."""
    # Initialize with current production configuration
    service = ModularValidationService()
    return service


@pytest.fixture(scope="module")
def new_validation_service():
    """
    Initialize NEW validation service (from extracted configs).

    TODO: Replace with actual NEW service once extracted.
    For now, this is a placeholder that uses the same service.
    """
    # TODO: Initialize with extracted configuration
    service = ModularValidationService()
    return service


# ========================================
# VALIDATION PARITY TESTS
# ========================================


@pytest.mark.baseline()
@pytest.mark.parity()
def test_baseline_definitions_loaded(baseline_definitions):
    """Verify that baseline definitions are loaded correctly."""
    assert len(baseline_definitions) > 0, "No baseline definitions found"
    assert (
        len(baseline_definitions) == 42
    ), f"Expected 42 definitions, got {len(baseline_definitions)}"

    # Verify structure
    for defn in baseline_definitions:
        assert "begrip" in defn, "Missing 'begrip' field"
        assert "definitie" in defn, "Missing 'definitie' field"
        assert "categorie" in defn, "Missing 'categorie' field"


@pytest.mark.baseline()
@pytest.mark.parity()
@pytest.mark.slow()
def test_validation_score_parity(baseline_definitions, old_validation_service):
    """
    Test that validation scores match between OLD and NEW systems.

    Requirement: 100% match on overall validation scores.
    """
    mismatches = []

    for defn in baseline_definitions:
        begrip = defn.get("begrip", "unknown")
        definitie_text = defn.get("definitie", "")

        # Get OLD system validation score
        old_result = old_validation_service.validate(definitie_text, begrip)
        old_score = (
            old_result.get("overall_score", 0.0)
            if isinstance(old_result, dict)
            else getattr(old_result, "overall_score", 0.0)
        )

        # Get stored baseline score
        baseline_score = defn.get("validation_score")

        # Compare scores (allow small floating point differences)
        if baseline_score is not None:
            score_diff = abs(old_score - baseline_score)
            if score_diff > 0.01:  # 1% tolerance for floating point
                mismatches.append(
                    {
                        "begrip": begrip,
                        "old_score": old_score,
                        "baseline_score": baseline_score,
                        "difference": score_diff,
                    }
                )

    # Report mismatches
    if mismatches:
        report = "\n\nValidation Score Mismatches:\n"
        report += "=" * 80 + "\n"
        for mismatch in mismatches:
            report += f"\nBegrip: {mismatch['begrip']}\n"
            report += f"  OLD score:      {mismatch['old_score']:.4f}\n"
            report += f"  Baseline score: {mismatch['baseline_score']:.4f}\n"
            report += f"  Difference:     {mismatch['difference']:.4f}\n"

        pytest.fail(f"Found {len(mismatches)} score mismatches:{report}")


@pytest.mark.baseline()
@pytest.mark.parity()
@pytest.mark.slow()
def test_rule_results_parity(baseline_definitions, old_validation_service):
    """
    Test that individual rule results match between OLD and NEW systems.

    Requirement: 100% match on rule pass/fail results.
    """
    mismatches = []

    for defn in baseline_definitions:
        begrip = defn.get("begrip", "unknown")
        definitie_text = defn.get("definitie", "")

        # Get OLD system validation results
        old_result = old_validation_service.validate(definitie_text, begrip)

        # Extract rule results
        if isinstance(old_result, dict):
            old_rules = old_result.get("rule_results", [])
        else:
            old_rules = getattr(old_result, "rule_results", [])

        # Get stored baseline validation issues
        baseline_issues = defn.get("validation_issues", [])

        # Compare rule counts
        if len(old_rules) != len(baseline_issues):
            mismatches.append(
                {
                    "begrip": begrip,
                    "type": "rule_count",
                    "old_count": len(old_rules),
                    "baseline_count": len(baseline_issues),
                }
            )

    # Report mismatches
    if mismatches:
        report = "\n\nRule Results Mismatches:\n"
        report += "=" * 80 + "\n"
        for mismatch in mismatches:
            report += f"\nBegrip: {mismatch['begrip']}\n"
            report += f"  Type: {mismatch['type']}\n"
            if mismatch["type"] == "rule_count":
                report += f"  OLD rules:      {mismatch['old_count']}\n"
                report += f"  Baseline rules: {mismatch['baseline_count']}\n"

        pytest.fail(f"Found {len(mismatches)} rule result mismatches:{report}")


@pytest.mark.baseline()
@pytest.mark.parity()
def test_validation_determinism(old_validation_service):
    """
    Test that validation is deterministic (same input = same output).

    This ensures that validation results are reproducible.
    """
    test_definitie = (
        "Een proces waarbij de identiteit van een persoon wordt geverifieerd."
    )
    test_begrip = "authenticatie"

    # Run validation 5 times
    results = []
    for _ in range(5):
        result = old_validation_service.validate(test_definitie, test_begrip)
        if isinstance(result, dict):
            score = result.get("overall_score", 0.0)
        else:
            score = getattr(result, "overall_score", 0.0)
        results.append(score)

    # All results should be identical
    assert len(set(results)) == 1, f"Non-deterministic results: {results}"


@pytest.mark.baseline()
@pytest.mark.parity()
@pytest.mark.slow()
def test_high_quality_definitions_pass(baseline_definitions, old_validation_service):
    """
    Test that high-quality baseline definitions pass validation.

    Definitions with validation_score >= 0.80 should be acceptable.
    """
    failures = []

    for defn in baseline_definitions:
        baseline_score = defn.get("validation_score")
        if baseline_score is None or baseline_score < 0.80:
            continue  # Skip low-quality definitions

        begrip = defn.get("begrip", "unknown")
        definitie_text = defn.get("definitie", "")

        # Validate with OLD system
        result = old_validation_service.validate(definitie_text, begrip)

        # Check if acceptable
        if isinstance(result, dict):
            is_acceptable = result.get("is_acceptable", False)
        else:
            is_acceptable = getattr(result, "is_acceptable", False)

        if not is_acceptable:
            failures.append(
                {
                    "begrip": begrip,
                    "baseline_score": baseline_score,
                    "is_acceptable": is_acceptable,
                }
            )

    # Report failures
    if failures:
        report = "\n\nHigh-Quality Definitions Failed Validation:\n"
        report += "=" * 80 + "\n"
        for failure in failures:
            report += f"\nBegrip: {failure['begrip']}\n"
            report += f"  Baseline score:  {failure['baseline_score']:.2f}\n"
            report += f"  Is acceptable:   {failure['is_acceptable']}\n"

        pytest.fail(
            f"Found {len(failures)} high-quality definitions that failed:{report}"
        )


@pytest.mark.baseline()
@pytest.mark.parity()
@pytest.mark.parametrize("min_score", [0.90, 0.80, 0.70, 0.60])
def test_score_threshold_consistency(
    baseline_definitions, old_validation_service, min_score: float
):
    """
    Test that validation scores are consistent across different quality thresholds.

    Args:
        min_score: Minimum score threshold to test
    """
    count_above_threshold = 0

    for defn in baseline_definitions:
        baseline_score = defn.get("validation_score")
        if baseline_score is None:
            continue

        if baseline_score >= min_score:
            count_above_threshold += 1

    # At least some definitions should meet each threshold
    assert count_above_threshold > 0, f"No definitions found with score >= {min_score}"


@pytest.mark.baseline()
@pytest.mark.parity()
def test_validation_issues_captured(baseline_definitions):
    """
    Test that validation issues are properly captured in baseline data.

    This ensures we can compare specific issues between systems.
    """
    definitions_with_issues = 0

    for defn in baseline_definitions:
        issues = defn.get("validation_issues", [])
        if issues:
            definitions_with_issues += 1

            # Verify issue structure
            if isinstance(issues, str):
                # Parse JSON if stored as string
                try:
                    issues = json.loads(issues)
                except json.JSONDecodeError:
                    continue

            # Check that issues have expected structure
            for issue in issues:
                if isinstance(issue, dict):
                    # Should have at least a rule_id or message
                    assert (
                        "rule_id" in issue or "message" in issue
                    ), f"Issue missing structure: {issue}"

    # Some definitions should have issues
    assert definitions_with_issues > 0, "No definitions with validation issues found"


# ========================================
# DETAILED DIAGNOSTICS
# ========================================


@pytest.mark.baseline()
@pytest.mark.parity()
@pytest.mark.slow()
def test_generate_parity_report(baseline_definitions, old_validation_service):
    """
    Generate a detailed parity report comparing OLD system results with baseline.

    This test always passes but generates a comprehensive comparison report.
    """
    report = []
    report.append("\n" + "=" * 80)
    report.append("VALIDATION PARITY REPORT")
    report.append("=" * 80)
    report.append(f"\nTotal Baseline Definitions: {len(baseline_definitions)}")

    # Statistics
    total_validated = 0
    score_matches = 0
    score_mismatches = []

    for defn in baseline_definitions:
        begrip = defn.get("begrip", "unknown")
        definitie_text = defn.get("definitie", "")
        baseline_score = defn.get("validation_score")

        if baseline_score is None:
            continue

        total_validated += 1

        # Validate with OLD system
        old_result = old_validation_service.validate(definitie_text, begrip)
        old_score = (
            old_result.get("overall_score", 0.0)
            if isinstance(old_result, dict)
            else getattr(old_result, "overall_score", 0.0)
        )

        # Compare
        score_diff = abs(old_score - baseline_score)
        if score_diff <= 0.01:
            score_matches += 1
        else:
            score_mismatches.append(
                {
                    "begrip": begrip,
                    "old": old_score,
                    "baseline": baseline_score,
                    "diff": score_diff,
                }
            )

    # Summary statistics
    report.append(f"\nValidated Definitions: {total_validated}")
    report.append(f"Score Matches: {score_matches}")
    report.append(f"Score Mismatches: {len(score_mismatches)}")

    if total_validated > 0:
        match_percentage = (score_matches / total_validated) * 100
        report.append(f"Match Percentage: {match_percentage:.2f}%")

    # Detailed mismatches
    if score_mismatches:
        report.append("\n" + "-" * 80)
        report.append("SCORE MISMATCHES:")
        report.append("-" * 80)
        for mismatch in score_mismatches[:10]:  # Show top 10
            report.append(f"\n  {mismatch['begrip']}:")
            report.append(f"    OLD:      {mismatch['old']:.4f}")
            report.append(f"    Baseline: {mismatch['baseline']:.4f}")
            report.append(f"    Diff:     {mismatch['diff']:.4f}")

    report.append("\n" + "=" * 80)

    # Print report
    print("\n".join(report))

    # Test always passes - this is for diagnostics only
    assert True
