"""
Comprehensive tests for services.validation.types module.

Tests cover:
1. Factory functions: create_validation_result, create_degraded_result
2. Normalization: normalize_to_unified (dict, dataclass, legacy formats)
3. Validators: is_valid_result, get_blocking_violations, get_category_score
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from typing import Any
from unittest.mock import patch

import pytest

from services.validation.types import (
    CONTRACT_VERSION,
    AcceptanceGate,
    CategoryScores,
    ImprovementSuggestion,
    ValidationResult,
    ViolationDict,
    create_degraded_result,
    create_validation_result,
    get_blocking_violations,
    get_category_score,
    is_valid_result,
    normalize_to_unified,
)

# ==============================================================================
# Test Fixtures
# ==============================================================================


@pytest.fixture
def minimal_violation() -> ViolationDict:
    """Create a minimal valid violation for testing."""
    return {
        "code": "VAL-TST-001",
        "severity": "warning",
        "message": "Test violation message",
        "rule_id": "TEST-001",
        "category": "taal",
    }


@pytest.fixture
def error_violation() -> ViolationDict:
    """Create an error-severity violation for testing."""
    return {
        "code": "VAL-ERR-001",
        "severity": "error",
        "message": "Blocking error violation",
        "rule_id": "ERROR-001",
        "category": "structuur",
    }


@pytest.fixture
def valid_result() -> ValidationResult:
    """Create a valid ValidationResult for testing."""
    return create_validation_result(
        overall_score=0.85,
        is_acceptable=True,
        violations=[],
        passed_rules=["RULE-001", "RULE-002"],
    )


@pytest.fixture
def custom_detailed_scores() -> CategoryScores:
    """Create custom detailed scores for testing."""
    return {
        "taal": 0.9,
        "juridisch": 0.8,
        "structuur": 0.75,
        "samenhang": 0.85,
    }


# ==============================================================================
# Factory Function Tests: create_validation_result
# ==============================================================================


class TestCreateValidationResult:
    """Tests for create_validation_result factory function."""

    def test_minimal_args_creates_valid_result(self) -> None:
        """Create result with only required args produces valid schema."""
        result = create_validation_result(
            overall_score=0.75,
            is_acceptable=True,
        )

        assert result["version"] == CONTRACT_VERSION
        assert result["overall_score"] == 0.75
        assert result["is_acceptable"] is True
        assert result["violations"] == []
        assert result["passed_rules"] == []
        assert "system" in result
        assert "correlation_id" in result["system"]
        assert "detailed_scores" in result

    def test_auto_generated_correlation_id_is_valid_uuid(self) -> None:
        """Auto-generated correlation_id should be a valid UUID string."""
        result = create_validation_result(
            overall_score=0.5,
            is_acceptable=True,
        )

        correlation_id = result["system"]["correlation_id"]
        # Should not raise ValueError if valid UUID
        parsed = uuid.UUID(correlation_id)
        assert str(parsed) == correlation_id

    def test_explicit_correlation_id_used(self) -> None:
        """Explicit correlation_id should be used when provided."""
        explicit_id = "test-correlation-id-12345"
        result = create_validation_result(
            overall_score=0.5,
            is_acceptable=True,
            correlation_id=explicit_id,
        )

        assert result["system"]["correlation_id"] == explicit_id

    def test_default_detailed_scores_match_overall(self) -> None:
        """Default detailed_scores should match overall_score for all categories."""
        result = create_validation_result(
            overall_score=0.8,
            is_acceptable=True,
        )

        scores = result["detailed_scores"]
        assert scores["taal"] == 0.8
        assert scores["juridisch"] == 0.8
        assert scores["structuur"] == 0.8
        assert scores["samenhang"] == 0.8

    def test_custom_detailed_scores_preserved(
        self, custom_detailed_scores: CategoryScores
    ) -> None:
        """Custom detailed_scores should be preserved exactly."""
        result = create_validation_result(
            overall_score=0.8,
            is_acceptable=True,
            detailed_scores=custom_detailed_scores,
        )

        assert result["detailed_scores"] == custom_detailed_scores

    def test_violations_included(self, minimal_violation: ViolationDict) -> None:
        """Violations should be included in result."""
        result = create_validation_result(
            overall_score=0.6,
            is_acceptable=False,
            violations=[minimal_violation],
        )

        assert len(result["violations"]) == 1
        assert result["violations"][0] == minimal_violation

    def test_passed_rules_included(self) -> None:
        """Passed rules should be included in result."""
        rules = ["RULE-001", "RULE-002", "RULE-003"]
        result = create_validation_result(
            overall_score=0.9,
            is_acceptable=True,
            passed_rules=rules,
        )

        assert result["passed_rules"] == rules

    def test_all_optional_args(
        self,
        minimal_violation: ViolationDict,
        custom_detailed_scores: CategoryScores,
    ) -> None:
        """Create result with all optional args included."""
        improvement: ImprovementSuggestion = {
            "type": "rewrite",
            "description": "Consider rephrasing",
            "impact": "medium",
        }
        acceptance_gate: AcceptanceGate = {
            "status": "pass",
            "acceptable": True,
            "gates_passed": ["threshold", "errors"],
            "gates_failed": [],
            "reasons": ["All criteria met"],
            "thresholds": {"min_score": 0.7},
        }

        result = create_validation_result(
            overall_score=0.85,
            is_acceptable=True,
            violations=[minimal_violation],
            passed_rules=["RULE-001"],
            detailed_scores=custom_detailed_scores,
            correlation_id="test-123",
            engine_version="1.2.3",
            profile_used="strict",
            duration_ms=150,
            improvement_suggestions=[improvement],
            acceptance_gate=acceptance_gate,
        )

        # Required fields
        assert result["version"] == CONTRACT_VERSION
        assert result["overall_score"] == 0.85
        assert result["is_acceptable"] is True
        assert len(result["violations"]) == 1
        assert result["passed_rules"] == ["RULE-001"]
        assert result["detailed_scores"] == custom_detailed_scores

        # System metadata
        system = result["system"]
        assert system["correlation_id"] == "test-123"
        assert system["engine_version"] == "1.2.3"
        assert system["profile_used"] == "strict"
        assert system["duration_ms"] == 150
        assert "timestamp" in system

        # Optional fields
        assert result["improvement_suggestions"] == [improvement]
        assert result["acceptance_gate"] == acceptance_gate

    def test_timestamp_is_iso_format(self) -> None:
        """System timestamp should be in ISO 8601 format."""
        result = create_validation_result(
            overall_score=0.5,
            is_acceptable=True,
        )

        timestamp = result["system"]["timestamp"]
        # ISO format pattern: YYYY-MM-DDTHH:MM:SS.ffffff+00:00
        assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", timestamp)

    @pytest.mark.parametrize(
        ("score", "acceptable"),
        [
            (0.0, False),
            (0.5, True),
            (1.0, True),
            (0.33, False),
            (0.99, True),
        ],
    )
    def test_various_score_acceptable_combinations(
        self, score: float, acceptable: bool
    ) -> None:
        """Test various score and acceptable value combinations."""
        result = create_validation_result(
            overall_score=score,
            is_acceptable=acceptable,
        )

        assert result["overall_score"] == score
        assert result["is_acceptable"] is acceptable


# ==============================================================================
# Factory Function Tests: create_degraded_result
# ==============================================================================


class TestCreateDegradedResult:
    """Tests for create_degraded_result factory function."""

    def test_creates_error_state_with_zero_score(self) -> None:
        """Degraded result should have zero score and not acceptable."""
        result = create_degraded_result(error="Test error")

        assert result["overall_score"] == 0.0
        assert result["is_acceptable"] is False

    def test_error_message_in_violation(self) -> None:
        """Error message should appear in system violation."""
        error_msg = "AI service timeout"
        result = create_degraded_result(error=error_msg)

        assert len(result["violations"]) == 1
        violation = result["violations"][0]
        assert violation["code"] == "SYS-SVC-001"
        assert violation["severity"] == "error"
        assert error_msg in violation["message"]
        assert violation["category"] == "system"

    def test_error_in_system_metadata(self) -> None:
        """Error should be stored in system metadata."""
        error_msg = "Database connection failed"
        result = create_degraded_result(error=error_msg)

        assert result["system"]["error"] == error_msg

    def test_auto_generated_correlation_id(self) -> None:
        """Degraded result should auto-generate correlation_id."""
        result = create_degraded_result(error="Test")

        correlation_id = result["system"]["correlation_id"]
        # Should be valid UUID
        uuid.UUID(correlation_id)

    def test_explicit_correlation_id(self) -> None:
        """Explicit correlation_id should be used."""
        explicit_id = "degraded-test-id"
        result = create_degraded_result(
            error="Test",
            correlation_id=explicit_id,
        )

        assert result["system"]["correlation_id"] == explicit_id

    def test_includes_retry_suggestion_by_default(self) -> None:
        """Default behavior includes retry suggestion."""
        result = create_degraded_result(error="Test")

        assert "improvement_suggestions" in result
        suggestions = result["improvement_suggestions"]
        assert len(suggestions) == 1
        assert suggestions[0]["type"] == "restructure"
        assert "try again" in suggestions[0]["description"].lower()

    def test_no_retry_suggestion_when_disabled(self) -> None:
        """Retry suggestion can be disabled."""
        result = create_degraded_result(
            error="Test",
            include_retry_suggestion=False,
        )

        assert "improvement_suggestions" not in result

    def test_all_category_scores_zero(self) -> None:
        """All category scores should be zero in degraded state."""
        result = create_degraded_result(error="Test")

        scores = result["detailed_scores"]
        assert scores["taal"] == 0.0
        assert scores["juridisch"] == 0.0
        assert scores["structuur"] == 0.0
        assert scores["samenhang"] == 0.0

    def test_passed_rules_empty(self) -> None:
        """Passed rules should be empty in degraded state."""
        result = create_degraded_result(error="Test")

        assert result["passed_rules"] == []

    def test_logs_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """Creating degraded result should log warning."""
        with caplog.at_level("WARNING"):
            create_degraded_result(
                error="Test error",
                begrip="TestBegrip",
            )

        assert "degraded" in caplog.text.lower()
        assert "TestBegrip" in caplog.text

    def test_schema_compliant(self) -> None:
        """Degraded result should pass is_valid_result check."""
        result = create_degraded_result(error="Test")

        assert is_valid_result(result)


# ==============================================================================
# Normalization Tests: normalize_to_unified
# ==============================================================================


class TestNormalizeToUnified:
    """Tests for normalize_to_unified function."""

    def test_passthrough_compliant_dict(self, valid_result: ValidationResult) -> None:
        """Already-compliant dict should pass through unchanged."""
        original_id = valid_result["system"]["correlation_id"]
        normalized = normalize_to_unified(valid_result)

        assert normalized["version"] == valid_result["version"]
        assert normalized["overall_score"] == valid_result["overall_score"]
        assert normalized["system"]["correlation_id"] == original_id

    def test_compliant_dict_preserves_all_fields(self) -> None:
        """All fields in compliant dict should be preserved."""
        original: ValidationResult = {
            "version": "2.0.0",
            "overall_score": 0.8,
            "is_acceptable": True,
            "violations": [],
            "passed_rules": ["R1", "R2"],
            "detailed_scores": {
                "taal": 0.9,
                "juridisch": 0.8,
                "structuur": 0.75,
                "samenhang": 0.85,
            },
            "system": {"correlation_id": "test-id", "timestamp": "2024-01-01T00:00:00"},
        }

        normalized = normalize_to_unified(original)

        assert normalized["passed_rules"] == ["R1", "R2"]
        assert normalized["detailed_scores"]["taal"] == 0.9

    def test_adds_correlation_id_if_missing(self) -> None:
        """Should add correlation_id if missing from compliant dict."""
        incomplete: dict[str, Any] = {
            "version": "2.0.0",
            "overall_score": 0.5,
            "is_acceptable": True,
            "violations": [],
            "passed_rules": [],
            "detailed_scores": {},
            "system": {},  # Missing correlation_id
        }

        normalized = normalize_to_unified(incomplete)
        assert "correlation_id" in normalized["system"]

    def test_uses_provided_correlation_id(self) -> None:
        """Should use provided correlation_id parameter."""
        incomplete: dict[str, Any] = {
            "version": "2.0.0",
            "overall_score": 0.5,
            "is_acceptable": True,
            "violations": [],
            "passed_rules": [],
            "detailed_scores": {},
            "system": {},
        }

        normalized = normalize_to_unified(incomplete, correlation_id="provided-id")
        assert normalized["system"]["correlation_id"] == "provided-id"

    def test_dataclass_conversion(self) -> None:
        """Should convert dataclass to unified format."""

        @dataclass
        class MockViolation:
            code: str = "VAL-TST-001"
            severity: str = "warning"
            message: str = "Test violation"
            rule_id: str = "TEST-001"
            category: str = "taal"

        @dataclass
        class MockDataclassResult:
            is_valid: bool = True
            score: float = 0.8
            violations: list[MockViolation] = field(default_factory=list)
            passed_rules: list[str] = field(default_factory=list)
            suggestions: list[str] = field(default_factory=list)
            engine_version: str = "1.0.0"

        mock_result = MockDataclassResult(
            is_valid=True,
            score=0.8,
            violations=[MockViolation()],
            passed_rules=["RULE-001"],
            suggestions=["Improve clarity"],
            engine_version="1.0.0",
        )

        normalized = normalize_to_unified(mock_result, correlation_id="dc-test-id")

        assert normalized["version"] == CONTRACT_VERSION
        assert normalized["overall_score"] == 0.8
        assert normalized["is_acceptable"] is True
        assert len(normalized["violations"]) == 1
        assert normalized["violations"][0]["code"] == "VAL-TST-001"
        assert normalized["passed_rules"] == ["RULE-001"]
        assert normalized["system"]["correlation_id"] == "dc-test-id"
        assert normalized["system"]["engine_version"] == "1.0.0"

    def test_dataclass_with_enum_severity(self) -> None:
        """Should handle dataclass with enum severity."""
        from enum import Enum

        class Severity(Enum):
            WARNING = "warning"
            ERROR = "error"

        @dataclass
        class ViolationWithEnum:
            code: str = "VAL-TST-001"
            severity: Severity = Severity.WARNING
            message: str = "Test"
            rule_id: str = "TEST-001"
            category: str = "taal"

        @dataclass
        class ResultWithEnumViolation:
            is_valid: bool = True
            score: float = 0.7
            violations: list[ViolationWithEnum] = field(default_factory=list)

        mock_result = ResultWithEnumViolation(
            violations=[ViolationWithEnum(severity=Severity.ERROR)]
        )

        normalized = normalize_to_unified(mock_result)

        assert normalized["violations"][0]["severity"] == "error"

    def test_legacy_dict_without_version_system(self) -> None:
        """Should convert legacy dict without version/system structure."""
        legacy: dict[str, Any] = {
            "score": 0.75,
            "is_valid": True,
            "violations": [
                {
                    "code": "VAL-LEG-001",
                    "severity": "warning",
                    "message": "Legacy violation",
                    "rule_id": "LEGACY-001",
                    "category": "taal",
                }
            ],
        }

        normalized = normalize_to_unified(legacy, correlation_id="legacy-id")

        assert normalized["version"] == CONTRACT_VERSION
        assert normalized["overall_score"] == 0.75
        assert normalized["is_acceptable"] is True
        assert len(normalized["violations"]) == 1
        assert "system" in normalized
        assert normalized["system"]["correlation_id"] == "legacy-id"

    def test_legacy_dict_with_errors_warnings(self) -> None:
        """Should convert legacy errors/warnings to violations."""
        legacy: dict[str, Any] = {
            "score": 0.5,
            "errors": ["Error 1", "Error 2"],
            "warnings": ["Warning 1"],
        }

        normalized = normalize_to_unified(legacy)

        # Should have 3 violations: 2 errors + 1 warning
        assert len(normalized["violations"]) == 3

        error_violations = [
            v for v in normalized["violations"] if v["severity"] == "error"
        ]
        warning_violations = [
            v for v in normalized["violations"] if v["severity"] == "warning"
        ]

        assert len(error_violations) == 2
        assert len(warning_violations) == 1

    def test_legacy_dict_infers_acceptable_from_score(self) -> None:
        """Should infer is_acceptable from score when not provided."""
        # Score >= 0.5 -> acceptable
        legacy_high: dict[str, Any] = {"score": 0.6}
        normalized_high = normalize_to_unified(legacy_high)
        assert normalized_high["is_acceptable"] is True

        # Score < 0.5 -> not acceptable
        legacy_low: dict[str, Any] = {"score": 0.4}
        normalized_low = normalize_to_unified(legacy_low)
        assert normalized_low["is_acceptable"] is False

    def test_legacy_dict_with_suggestions(self) -> None:
        """Should convert legacy suggestions to improvement_suggestions."""
        legacy: dict[str, Any] = {
            "score": 0.7,
            "suggestions": ["Suggestion 1", "Suggestion 2"],
        }

        normalized = normalize_to_unified(legacy)

        assert "improvement_suggestions" in normalized
        assert len(normalized["improvement_suggestions"]) == 2
        assert normalized["improvement_suggestions"][0]["type"] == "rewrite"
        assert normalized["improvement_suggestions"][0]["description"] == "Suggestion 1"

    def test_unknown_type_creates_degraded_result(self) -> None:
        """Unknown types should create degraded result."""
        unknown_obj = ["not", "a", "valid", "result"]

        normalized = normalize_to_unified(unknown_obj, correlation_id="unknown-id")

        assert normalized["overall_score"] == 0.0
        assert normalized["is_acceptable"] is False
        assert normalized["system"]["correlation_id"] == "unknown-id"
        assert "error" in normalized["system"]
        assert "list" in normalized["system"]["error"]

    def test_unknown_type_logs_error(self, caplog: pytest.LogCaptureFixture) -> None:
        """Unknown type should log error."""
        with caplog.at_level("ERROR"):
            normalize_to_unified(12345)

        assert "cannot normalize" in caplog.text.lower()
        assert "int" in caplog.text

    def test_none_violations_handled(self) -> None:
        """Should handle None violations gracefully."""
        legacy: dict[str, Any] = {
            "score": 0.8,
            "violations": None,
        }

        normalized = normalize_to_unified(legacy)
        assert normalized["violations"] == []

    def test_overall_score_from_different_keys(self) -> None:
        """Should extract score from 'score' or 'overall_score' key."""
        with_score: dict[str, Any] = {"score": 0.7}
        with_overall: dict[str, Any] = {"overall_score": 0.8}

        assert normalize_to_unified(with_score)["overall_score"] == 0.7
        assert normalize_to_unified(with_overall)["overall_score"] == 0.8


# ==============================================================================
# Validator Tests: is_valid_result
# ==============================================================================


class TestIsValidResult:
    """Tests for is_valid_result validator function."""

    def test_valid_result_returns_true(self, valid_result: ValidationResult) -> None:
        """Valid ValidationResult should return True."""
        assert is_valid_result(valid_result) is True

    def test_factory_created_result_is_valid(self) -> None:
        """Result from factory function should be valid."""
        result = create_validation_result(overall_score=0.5, is_acceptable=True)
        assert is_valid_result(result) is True

    def test_non_dict_returns_false(self) -> None:
        """Non-dict types should return False."""
        assert is_valid_result(None) is False
        assert is_valid_result("string") is False
        assert is_valid_result(123) is False
        assert is_valid_result([1, 2, 3]) is False

    @pytest.mark.parametrize(
        "missing_field",
        [
            "version",
            "overall_score",
            "is_acceptable",
            "violations",
            "passed_rules",
            "detailed_scores",
            "system",
        ],
    )
    def test_missing_required_field_returns_false(self, missing_field: str) -> None:
        """Missing any required field should return False."""
        result = create_validation_result(overall_score=0.5, is_acceptable=True)
        del result[missing_field]  # type: ignore[misc]

        assert is_valid_result(result) is False

    def test_missing_correlation_id_returns_false(self) -> None:
        """System without correlation_id should return False."""
        result: dict[str, Any] = {
            "version": "2.0.0",
            "overall_score": 0.5,
            "is_acceptable": True,
            "violations": [],
            "passed_rules": [],
            "detailed_scores": {},
            "system": {},  # Missing correlation_id
        }

        assert is_valid_result(result) is False

    def test_system_not_dict_returns_false(self) -> None:
        """Non-dict system should return False."""
        result: dict[str, Any] = {
            "version": "2.0.0",
            "overall_score": 0.5,
            "is_acceptable": True,
            "violations": [],
            "passed_rules": [],
            "detailed_scores": {},
            "system": "not-a-dict",
        }

        assert is_valid_result(result) is False


# ==============================================================================
# Validator Tests: get_blocking_violations
# ==============================================================================


class TestGetBlockingViolations:
    """Tests for get_blocking_violations function."""

    def test_returns_only_error_severity(
        self, minimal_violation: ViolationDict, error_violation: ViolationDict
    ) -> None:
        """Should return only violations with error severity."""
        result = create_validation_result(
            overall_score=0.5,
            is_acceptable=False,
            violations=[minimal_violation, error_violation],
        )

        blocking = get_blocking_violations(result)

        assert len(blocking) == 1
        assert blocking[0]["severity"] == "error"
        assert blocking[0]["code"] == "VAL-ERR-001"

    def test_empty_when_no_errors(self, minimal_violation: ViolationDict) -> None:
        """Should return empty list when no error violations."""
        result = create_validation_result(
            overall_score=0.7,
            is_acceptable=True,
            violations=[minimal_violation],  # warning severity
        )

        blocking = get_blocking_violations(result)

        assert blocking == []

    def test_multiple_errors_all_returned(self) -> None:
        """Should return all error-severity violations."""
        errors: list[ViolationDict] = [
            {
                "code": "VAL-ERR-001",
                "severity": "error",
                "message": "Error 1",
                "rule_id": "ERR-001",
                "category": "taal",
            },
            {
                "code": "VAL-ERR-002",
                "severity": "error",
                "message": "Error 2",
                "rule_id": "ERR-002",
                "category": "structuur",
            },
        ]
        result = create_validation_result(
            overall_score=0.3,
            is_acceptable=False,
            violations=errors,
        )

        blocking = get_blocking_violations(result)

        assert len(blocking) == 2

    def test_handles_empty_violations(self) -> None:
        """Should handle result with no violations."""
        result = create_validation_result(
            overall_score=0.9,
            is_acceptable=True,
            violations=[],
        )

        blocking = get_blocking_violations(result)

        assert blocking == []

    def test_handles_missing_violations_key(self) -> None:
        """Should handle result without violations key gracefully."""
        result: ValidationResult = {  # type: ignore[typeddict-item]
            "version": "2.0.0",
            "overall_score": 0.5,
            "is_acceptable": True,
            "passed_rules": [],
            "detailed_scores": {},
            "system": {"correlation_id": "test"},
            # No violations key
        }

        blocking = get_blocking_violations(result)

        assert blocking == []


# ==============================================================================
# Validator Tests: get_category_score
# ==============================================================================


class TestGetCategoryScore:
    """Tests for get_category_score function."""

    def test_returns_correct_category_score(
        self, custom_detailed_scores: CategoryScores
    ) -> None:
        """Should return correct score for each category."""
        result = create_validation_result(
            overall_score=0.8,
            is_acceptable=True,
            detailed_scores=custom_detailed_scores,
        )

        assert get_category_score(result, "taal") == 0.9
        assert get_category_score(result, "juridisch") == 0.8
        assert get_category_score(result, "structuur") == 0.75
        assert get_category_score(result, "samenhang") == 0.85

    def test_returns_overall_score_when_category_missing(self) -> None:
        """Should return overall_score when category not in detailed_scores."""
        result = create_validation_result(
            overall_score=0.7,
            is_acceptable=True,
            detailed_scores={"taal": 0.8},  # Only taal present
        )

        # Existing category
        assert get_category_score(result, "taal") == 0.8
        # Missing category - falls back to overall
        assert get_category_score(result, "juridisch") == 0.7

    def test_returns_overall_for_system_category(self) -> None:
        """System category should fall back to overall_score."""
        result = create_validation_result(
            overall_score=0.75,
            is_acceptable=True,
        )

        # 'system' is not in standard detailed_scores
        assert get_category_score(result, "system") == 0.75

    def test_handles_missing_detailed_scores(self) -> None:
        """Should handle result without detailed_scores gracefully."""
        result: ValidationResult = {  # type: ignore[typeddict-item]
            "version": "2.0.0",
            "overall_score": 0.6,
            "is_acceptable": True,
            "violations": [],
            "passed_rules": [],
            "system": {"correlation_id": "test"},
            # No detailed_scores key
        }

        assert get_category_score(result, "taal") == 0.6

    def test_handles_missing_overall_score(self) -> None:
        """Should return 0.0 when both category and overall_score missing."""
        result: ValidationResult = {  # type: ignore[typeddict-item]
            "version": "2.0.0",
            "is_acceptable": False,
            "violations": [],
            "passed_rules": [],
            "detailed_scores": {},
            "system": {"correlation_id": "test"},
            # No overall_score key
        }

        assert get_category_score(result, "taal") == 0.0

    @pytest.mark.parametrize(
        "category",
        ["taal", "juridisch", "structuur", "samenhang"],
    )
    def test_all_standard_categories(self, category: str) -> None:
        """Should work for all standard category types."""
        result = create_validation_result(
            overall_score=0.5,
            is_acceptable=True,
        )

        # Default detailed_scores should have all categories
        score = get_category_score(result, category)  # type: ignore[arg-type]
        assert score == 0.5


# ==============================================================================
# Integration / Edge Case Tests
# ==============================================================================


class TestEdgeCases:
    """Tests for edge cases and integration scenarios."""

    def test_degraded_result_is_schema_compliant(self) -> None:
        """Degraded result should pass validation."""
        result = create_degraded_result(error="Test error")

        assert is_valid_result(result)
        assert result["version"] == CONTRACT_VERSION

    def test_normalize_then_validate(self) -> None:
        """Normalized results should pass validation."""
        legacy: dict[str, Any] = {"score": 0.7}
        normalized = normalize_to_unified(legacy)

        assert is_valid_result(normalized)

    def test_round_trip_normalization(self, valid_result: ValidationResult) -> None:
        """Normalizing an already-valid result should preserve it."""
        first_pass = normalize_to_unified(valid_result)
        second_pass = normalize_to_unified(first_pass)

        assert first_pass["overall_score"] == second_pass["overall_score"]
        assert (
            first_pass["system"]["correlation_id"]
            == second_pass["system"]["correlation_id"]
        )

    def test_contract_version_constant(self) -> None:
        """CONTRACT_VERSION should follow semver pattern."""
        assert re.match(r"^\d+\.\d+\.\d+$", CONTRACT_VERSION)

    def test_boundary_scores(self) -> None:
        """Test boundary score values."""
        # Minimum score
        result_min = create_validation_result(overall_score=0.0, is_acceptable=False)
        assert result_min["overall_score"] == 0.0

        # Maximum score
        result_max = create_validation_result(overall_score=1.0, is_acceptable=True)
        assert result_max["overall_score"] == 1.0

    def test_large_violations_list(self) -> None:
        """Should handle large number of violations."""
        violations: list[ViolationDict] = [
            {
                "code": f"VAL-TST-{i:03d}",
                "severity": "warning",
                "message": f"Violation {i}",
                "rule_id": f"RULE-{i:03d}",
                "category": "taal",
            }
            for i in range(100)
        ]

        result = create_validation_result(
            overall_score=0.3,
            is_acceptable=False,
            violations=violations,
        )

        assert len(result["violations"]) == 100
        assert is_valid_result(result)

    def test_unicode_in_messages(self) -> None:
        """Should handle unicode characters in messages."""
        violation: ViolationDict = {
            "code": "VAL-UNI-001",
            "severity": "warning",
            "message": "Definitie bevat ongeldige tekens: \u00e9\u00e0\u00fc\u00f1",
            "rule_id": "UNICODE-001",
            "category": "taal",
        }

        result = create_validation_result(
            overall_score=0.7,
            is_acceptable=True,
            violations=[violation],
        )

        assert "\u00e9" in result["violations"][0]["message"]


# ==============================================================================
# Extended Coverage Tests: Dataclass Conversion Edge Cases
# ==============================================================================


class TestDataclassConversionEdgeCases:
    """Tests for edge cases in dataclass to unified conversion."""

    def test_dataclass_with_location_dict(self) -> None:
        """Should convert violation with dict location."""

        @dataclass
        class ViolationWithLocation:
            code: str = "VAL-LOC-001"
            severity: str = "warning"
            message: str = "Test"
            rule_id: str = "LOC-001"
            category: str = "structuur"
            location: dict[str, Any] = field(
                default_factory=lambda: {"line": 10, "column": 5}
            )

        @dataclass
        class ResultWithLocation:
            score: float = 0.7
            violations: list[ViolationWithLocation] = field(default_factory=list)

        mock_result = ResultWithLocation(violations=[ViolationWithLocation()])
        normalized = normalize_to_unified(mock_result)

        assert len(normalized["violations"]) == 1
        assert "location" in normalized["violations"][0]
        assert normalized["violations"][0]["location"]["line"] == 10
        assert normalized["violations"][0]["location"]["column"] == 5

    def test_dataclass_with_location_text_span(self) -> None:
        """Should convert violation with text_span in location."""

        @dataclass
        class ViolationWithTextSpan:
            code: str = "VAL-TSP-001"
            severity: str = "warning"
            message: str = "Test"
            rule_id: str = "TSP-001"
            category: str = "taal"
            location: dict[str, Any] = field(
                default_factory=lambda: {"text_span": {"start": 0, "end": 10}}
            )

        @dataclass
        class ResultWithTextSpan:
            score: float = 0.7
            violations: list[ViolationWithTextSpan] = field(default_factory=list)

        mock_result = ResultWithTextSpan(violations=[ViolationWithTextSpan()])
        normalized = normalize_to_unified(mock_result)

        location = normalized["violations"][0].get("location", {})
        assert location.get("text_span") == {"start": 0, "end": 10}

    def test_dataclass_with_location_object(self) -> None:
        """Should convert violation with location as dataclass object."""

        @dataclass
        class LocationObject:
            line: int = 15
            column: int = 20

        @dataclass
        class ViolationWithLocationObj:
            code: str = "VAL-LOC-002"
            severity: str = "warning"
            message: str = "Test"
            rule_id: str = "LOC-002"
            category: str = "taal"
            location: LocationObject = field(default_factory=LocationObject)

        @dataclass
        class ResultWithLocationObj:
            score: float = 0.7
            violations: list[ViolationWithLocationObj] = field(default_factory=list)

        mock_result = ResultWithLocationObj(violations=[ViolationWithLocationObj()])
        normalized = normalize_to_unified(mock_result)

        location = normalized["violations"][0].get("location", {})
        assert location.get("line") == 15
        assert location.get("column") == 20

    def test_dataclass_violation_with_suggestions_list(self) -> None:
        """Should convert violation with suggestions list."""

        @dataclass
        class ViolationWithSuggestions:
            code: str = "VAL-SUG-001"
            severity: str = "warning"
            message: str = "Test"
            rule_id: str = "SUG-001"
            category: str = "taal"
            suggestions: list[str] = field(
                default_factory=lambda: ["Fix option 1", "Fix option 2"]
            )

        @dataclass
        class ResultWithSuggestions:
            score: float = 0.7
            violations: list[ViolationWithSuggestions] = field(default_factory=list)

        mock_result = ResultWithSuggestions(violations=[ViolationWithSuggestions()])
        normalized = normalize_to_unified(mock_result)

        violation = normalized["violations"][0]
        assert "suggestions" in violation
        assert violation["suggestions"] == ["Fix option 1", "Fix option 2"]

    def test_dataclass_violation_with_single_suggestion(self) -> None:
        """Should convert violation with single suggestion attribute."""

        @dataclass
        class ViolationWithSingleSuggestion:
            code: str = "VAL-SNG-001"
            severity: str = "warning"
            message: str = "Test"
            rule_id: str = "SNG-001"
            category: str = "taal"
            suggestion: str = "Single fix"

        @dataclass
        class ResultWithSingleSuggestion:
            score: float = 0.7
            violations: list[ViolationWithSingleSuggestion] = field(
                default_factory=list
            )

        mock_result = ResultWithSingleSuggestion(
            violations=[ViolationWithSingleSuggestion()]
        )
        normalized = normalize_to_unified(mock_result)

        violation = normalized["violations"][0]
        assert "suggestions" in violation
        assert violation["suggestions"] == ["Single fix"]

    def test_dataclass_with_description_instead_of_message(self) -> None:
        """Should extract message from description attribute if message missing."""

        @dataclass
        class ViolationWithDescription:
            code: str = "VAL-DESC-001"
            severity: str = "warning"
            description: str = "Description text"
            rule_id: str = "DESC-001"
            category: str = "taal"

        @dataclass
        class ResultWithDescription:
            score: float = 0.7
            violations: list[ViolationWithDescription] = field(default_factory=list)

        mock_result = ResultWithDescription(violations=[ViolationWithDescription()])
        normalized = normalize_to_unified(mock_result)

        assert normalized["violations"][0]["message"] == "Description text"

    def test_dataclass_with_improvement_suggestion_objects(self) -> None:
        """Should convert improvement suggestions as objects."""

        @dataclass
        class ImprovementSuggestionObj:
            type: str = "rewrite"
            description: str = "Rewrite the definition"
            example: str = "Example improvement"
            impact: str = "high"

        @dataclass
        class ResultWithImprovementObj:
            score: float = 0.7
            suggestions: list[ImprovementSuggestionObj] = field(default_factory=list)

        mock_result = ResultWithImprovementObj(suggestions=[ImprovementSuggestionObj()])
        normalized = normalize_to_unified(mock_result)

        assert "improvement_suggestions" in normalized
        suggestion = normalized["improvement_suggestions"][0]
        assert suggestion["type"] == "rewrite"
        assert suggestion["description"] == "Rewrite the definition"
        assert suggestion["example"] == "Example improvement"
        assert suggestion["impact"] == "high"

    def test_dataclass_with_invalid_severity_mapped(self) -> None:
        """Should map invalid severity values to warning."""

        @dataclass
        class ViolationWithInvalidSeverity:
            code: str = "VAL-INV-001"
            severity: str = "critical"  # Not a valid SeverityType
            message: str = "Test"
            rule_id: str = "INV-001"
            category: str = "taal"

        @dataclass
        class ResultWithInvalidSeverity:
            score: float = 0.7
            violations: list[ViolationWithInvalidSeverity] = field(default_factory=list)

        mock_result = ResultWithInvalidSeverity(
            violations=[ViolationWithInvalidSeverity()]
        )
        normalized = normalize_to_unified(mock_result)

        # Invalid severity should be mapped to "warning"
        assert normalized["violations"][0]["severity"] == "warning"

    def test_dataclass_with_none_score(self) -> None:
        """Should handle None score by defaulting to 0.0."""

        @dataclass
        class ResultWithNoneScore:
            score: float | None = None

        mock_result = ResultWithNoneScore(score=None)
        normalized = normalize_to_unified(mock_result)

        assert normalized["overall_score"] == 0.0

    def test_dataclass_with_profile_and_timestamp(self) -> None:
        """Should convert profile_used and timestamp metadata."""

        @dataclass
        class ResultWithMetadata:
            score: float = 0.8
            profile_used: str = "strict-profile"
            timestamp: str = "2024-01-15T10:30:00Z"
            processing_time_ms: int = 250

        mock_result = ResultWithMetadata()
        normalized = normalize_to_unified(mock_result)

        system = normalized["system"]
        assert system["profile_used"] == "strict-profile"
        assert system["timestamp"] == "2024-01-15T10:30:00Z"
        assert system["duration_ms"] == 250

    def test_dataclass_with_error_attribute(self) -> None:
        """Should convert error attribute to system metadata."""

        @dataclass
        class ResultWithError:
            score: float = 0.0
            error: str = "Service unavailable"

        mock_result = ResultWithError()
        normalized = normalize_to_unified(mock_result)

        assert normalized["system"]["error"] == "Service unavailable"

    def test_dataclass_with_default_passed_rules(self) -> None:
        """Should add default passed rules when none provided and no violations."""

        @dataclass
        class ResultNoViolations:
            score: float = 0.9
            is_valid: bool = True

        mock_result = ResultNoViolations()
        normalized = normalize_to_unified(mock_result)

        # Should have default passed rules
        assert "BASIC-001" in normalized["passed_rules"]
        assert "BASIC-002" in normalized["passed_rules"]
        assert "BASIC-003" in normalized["passed_rules"]


# ==============================================================================
# Extended Coverage Tests: Legacy Dict Conversion Edge Cases
# ==============================================================================


class TestLegacyDictConversionEdgeCases:
    """Tests for edge cases in legacy dict to unified conversion."""

    def test_legacy_dict_with_violation_location(self) -> None:
        """Should preserve location in legacy dict violations."""
        legacy: dict[str, Any] = {
            "score": 0.7,
            "violations": [
                {
                    "code": "VAL-LOC-001",
                    "severity": "warning",
                    "message": "Test",
                    "rule_id": "LOC-001",
                    "category": "taal",
                    "location": {"line": 5, "column": 10},
                }
            ],
        }

        normalized = normalize_to_unified(legacy)

        assert normalized["violations"][0]["location"] == {"line": 5, "column": 10}

    def test_legacy_dict_with_violation_suggestions(self) -> None:
        """Should preserve suggestions in legacy dict violations."""
        legacy: dict[str, Any] = {
            "score": 0.7,
            "violations": [
                {
                    "code": "VAL-SUG-001",
                    "severity": "warning",
                    "message": "Test",
                    "rule_id": "SUG-001",
                    "category": "taal",
                    "suggestions": ["Fix A", "Fix B"],
                }
            ],
        }

        normalized = normalize_to_unified(legacy)

        assert normalized["violations"][0]["suggestions"] == ["Fix A", "Fix B"]

    def test_legacy_dict_with_dict_suggestions(self) -> None:
        """Should convert dict-format suggestions in legacy dict."""
        legacy: dict[str, Any] = {
            "score": 0.7,
            "suggestions": [
                {"type": "addition", "description": "Add clarification"},
                {"type": "removal", "description": "Remove redundancy"},
            ],
        }

        normalized = normalize_to_unified(legacy)

        assert len(normalized["improvement_suggestions"]) == 2
        assert normalized["improvement_suggestions"][0]["type"] == "addition"
        assert normalized["improvement_suggestions"][1]["type"] == "removal"

    def test_legacy_dict_with_empty_errors_warnings(self) -> None:
        """Should handle empty errors and warnings lists."""
        legacy: dict[str, Any] = {
            "score": 0.8,
            "errors": [],
            "warnings": [],
        }

        normalized = normalize_to_unified(legacy)

        assert normalized["violations"] == []

    def test_legacy_dict_auto_generates_correlation_id(self) -> None:
        """Should auto-generate correlation_id when not provided."""
        legacy: dict[str, Any] = {"score": 0.7}

        normalized = normalize_to_unified(legacy)

        # Should have a valid UUID
        uuid.UUID(normalized["system"]["correlation_id"])

    def test_legacy_dict_with_detailed_scores(self) -> None:
        """Should preserve detailed_scores from legacy dict."""
        legacy: dict[str, Any] = {
            "score": 0.7,
            "detailed_scores": {
                "taal": 0.8,
                "juridisch": 0.7,
                "structuur": 0.6,
                "samenhang": 0.7,
            },
        }

        normalized = normalize_to_unified(legacy)

        assert normalized["detailed_scores"]["taal"] == 0.8
        assert normalized["detailed_scores"]["structuur"] == 0.6

    def test_legacy_dict_defaults_passed_rules(self) -> None:
        """Should add default passed rules when none and no violations."""
        legacy: dict[str, Any] = {
            "score": 0.9,
            "is_valid": True,
        }

        normalized = normalize_to_unified(legacy)

        assert "BASIC-001" in normalized["passed_rules"]

    def test_legacy_dict_violation_missing_fields_default(self) -> None:
        """Should provide defaults for missing violation fields."""
        legacy: dict[str, Any] = {
            "score": 0.6,
            "violations": [{"description": "Partial violation"}],  # Missing most fields
        }

        normalized = normalize_to_unified(legacy)

        violation = normalized["violations"][0]
        assert violation["code"] == "VAL-UNK-000"
        assert violation["severity"] == "warning"
        assert violation["message"] == "Partial violation"
        assert violation["rule_id"] == "unknown"
        assert violation["category"] == "system"

    def test_legacy_dict_preserves_timestamp(self) -> None:
        """Should preserve existing timestamp in legacy dict."""
        legacy: dict[str, Any] = {
            "score": 0.7,
            "timestamp": "2024-06-01T12:00:00Z",
        }

        normalized = normalize_to_unified(legacy)

        assert normalized["system"]["timestamp"] == "2024-06-01T12:00:00Z"

    def test_legacy_dict_with_none_score(self) -> None:
        """Should handle explicit None score by defaulting to 0.0."""
        legacy: dict[str, Any] = {
            "score": None,
        }

        normalized = normalize_to_unified(legacy)

        assert normalized["overall_score"] == 0.0
        # None score < 0.5, so not acceptable
        assert normalized["is_acceptable"] is False
