"""Tests voor ValidationResult mappers.

DEF-624: een legacy dataclass draagt geen runbewijs. De conversie levert
daarom `validation_unknown` (contract_status_missing) met de fail-closed
placeholders 0.0/False; wat het object wél draagt (violations, locaties,
metadata) reist ongewijzigd mee. Alleen een object met een werkelijk
aanwezige, geldige `validation_status` blijft `validated`.
"""

import uuid
from dataclasses import dataclass

import pytest

from services.validation.interfaces import (
    CONTRACT_VERSION,
    UNKNOWN_REASON_CONTRACT_STATUS_MISSING,
    VALIDATION_STATUS_UNKNOWN,
    VALIDATION_STATUS_VALIDATED,
)
from services.validation.mappers import (
    create_degraded_result,
    dataclass_to_schema_dict,
    ensure_schema_compliance,
)

pytestmark = [pytest.mark.unit]


@dataclass
class MockValidationResult:
    """Mock dataclass voor testing (legacy vorm: geen runstatus)."""

    is_valid: bool
    score: float
    violations: list = None
    suggestions: list = None
    passed_rules: list = None
    detailed_scores: dict = None
    error: str = None


@dataclass
class MockProducentResult(MockValidationResult):
    """Een object dat wél een werkelijk uitgevoerde run meldt."""

    validation_status: str = VALIDATION_STATUS_VALIDATED


@dataclass
class MockViolation:
    """Mock violation voor testing."""

    code: str
    severity: str
    message: str
    rule_id: str
    category: str
    location: dict = None
    suggestions: list[str] = None


class TestMappers:
    """Test suite voor ValidationResult mappers."""

    def test_dataclass_to_schema_dict_basic(self):
        """Test basic dataclass to TypedDict conversion.

        DEF-624: de legacy dataclass draagt geen runbewijs, dus ondanks
        `is_valid=True, score=0.95` is de uitkomst `validation_unknown` met
        de fail-closed placeholders. De regels die het object meldt reizen mee.
        """
        result = MockValidationResult(
            is_valid=True,
            score=0.95,
            violations=[],
            passed_rules=["RULE-001", "RULE-002"],
            detailed_scores={
                "taal": 0.9,
                "juridisch": 1.0,
                "structuur": 0.95,
                "samenhang": 0.9,
            },
        )

        schema_dict = dataclass_to_schema_dict(result)

        assert schema_dict["version"] == CONTRACT_VERSION
        assert schema_dict["validation_status"] == VALIDATION_STATUS_UNKNOWN
        assert schema_dict["unknown_reason"] == UNKNOWN_REASON_CONTRACT_STATUS_MISSING
        assert schema_dict["overall_score"] == 0.0
        assert schema_dict["is_acceptable"] is False
        assert len(schema_dict["violations"]) == 0
        assert len(schema_dict["passed_rules"]) == 2
        assert "system" in schema_dict
        assert "correlation_id" in schema_dict["system"]
        # Verify it's a valid UUID
        uuid.UUID(schema_dict["system"]["correlation_id"])

    def test_dataclass_met_runstatus_blijft_validated(self):
        """Een producent die zijn run meldt behoudt score en oordeel."""
        result = MockProducentResult(
            is_valid=True, score=0.95, violations=[], passed_rules=["RULE-001"]
        )

        schema_dict = dataclass_to_schema_dict(result)

        assert schema_dict["validation_status"] == VALIDATION_STATUS_VALIDATED
        assert "unknown_reason" not in schema_dict
        assert schema_dict["overall_score"] == 0.95
        assert schema_dict["is_acceptable"] is True

    def test_dataclass_to_schema_dict_with_violations(self):
        """Test conversion with violations."""
        violations = [
            MockViolation(
                code="VAL-LEN-001",
                severity="error",
                message="Text too short",
                rule_id="length-check",
                category="structuur",
                location={"line": 1, "column": 5},
            )
        ]

        result = MockValidationResult(
            is_valid=False,
            score=0.3,
            violations=violations,
            detailed_scores={
                "taal": 0.5,
                "juridisch": 0.3,
                "structuur": 0.2,
                "samenhang": 0.2,
            },
        )

        schema_dict = dataclass_to_schema_dict(result, "test-correlation-id")

        assert schema_dict["is_acceptable"] is False
        # DEF-624: zonder runbewijs is de score de fail-closed placeholder.
        assert schema_dict["validation_status"] == VALIDATION_STATUS_UNKNOWN
        assert schema_dict["overall_score"] == 0.0
        assert len(schema_dict["violations"]) == 1

        violation = schema_dict["violations"][0]
        assert violation["code"] == "VAL-LEN-001"
        assert violation["severity"] == "error"
        assert violation["message"] == "Text too short"
        assert violation["category"] == "structuur"
        assert "location" in violation
        assert violation["location"]["line"] == 1

        assert schema_dict["system"]["correlation_id"] == "test-correlation-id"

    def test_ensure_schema_compliance_with_dict(self):
        """Test that valid dict passes through.

        DEF-624: een schema-conform dict draagt zijn runstatus expliciet
        (`validated`, gezet door de producent); dan is de doorgifte
        inhoudelijk een pass-through.
        """
        valid_dict = {
            "version": CONTRACT_VERSION,
            "validation_status": VALIDATION_STATUS_VALIDATED,
            "overall_score": 0.8,
            "is_acceptable": True,
            "violations": [],
            "passed_rules": ["TEST-001"],
            "detailed_scores": {
                "taal": 0.8,
                "juridisch": 0.8,
                "structuur": 0.8,
                "samenhang": 0.8,
            },
            "system": {"correlation_id": "existing-id"},
        }

        result = ensure_schema_compliance(valid_dict)

        assert result == valid_dict
        assert result is not valid_dict
        assert result["system"]["correlation_id"] == "existing-id"

    def test_ensure_schema_compliance_dict_zonder_status_is_geen_run(self):
        """Hetzelfde dict zonder status: geen oordeel, wel dezelfde inhoud."""
        zonder_status = {
            "version": CONTRACT_VERSION,
            "overall_score": 0.8,
            "is_acceptable": True,
            "violations": [],
            "passed_rules": ["TEST-001"],
            "detailed_scores": {"taal": 0.8},
            "system": {"correlation_id": "existing-id"},
        }

        result = ensure_schema_compliance(zonder_status)

        assert result["validation_status"] == VALIDATION_STATUS_UNKNOWN
        assert result["unknown_reason"] == UNKNOWN_REASON_CONTRACT_STATUS_MISSING
        assert result["is_acceptable"] is False
        assert result["overall_score"] == 0.0
        assert result["passed_rules"] == ["TEST-001"]
        assert "validation_status" not in zonder_status, "invoer gemuteerd"

    def test_ensure_schema_compliance_adds_correlation_id(self):
        """Test that missing correlation_id is added."""
        dict_without_id = {
            "version": CONTRACT_VERSION,
            "overall_score": 0.8,
            "is_acceptable": True,
            "violations": [],
            "passed_rules": ["TEST-001"],
            "detailed_scores": {
                "taal": 0.8,
                "juridisch": 0.8,
                "structuur": 0.8,
                "samenhang": 0.8,
            },
            "system": {},
        }

        result = ensure_schema_compliance(dict_without_id, "new-correlation-id")

        assert result["system"]["correlation_id"] == "new-correlation-id"

    def test_ensure_schema_compliance_with_dataclass(self):
        """Test that dataclass is converted."""
        dataclass_result = MockValidationResult(
            is_valid=True, score=0.75, violations=[], passed_rules=["CHECK-001"]
        )

        result = ensure_schema_compliance(dataclass_result, "test-id")

        assert result["version"] == CONTRACT_VERSION
        # DEF-624: de dataclass draagt geen runbewijs.
        assert result["validation_status"] == VALIDATION_STATUS_UNKNOWN
        assert result["overall_score"] == 0.0
        assert result["is_acceptable"] is False
        assert result["passed_rules"] == ["CHECK-001"]
        assert result["system"]["correlation_id"] == "test-id"

    def test_create_degraded_result(self):
        """Test degraded result creation."""
        result = create_degraded_result(
            error="Service unavailable",
            correlation_id="degraded-id",
            begrip="test_begrip",
        )

        assert result["version"] == CONTRACT_VERSION
        assert result["overall_score"] == 0.0
        assert result["is_acceptable"] is False
        assert len(result["violations"]) == 1

        violation = result["violations"][0]
        assert violation["code"] == "SYS-SVC-001"
        assert violation["severity"] == "error"
        assert "Service unavailable" in violation["message"]

        assert result["system"]["correlation_id"] == "degraded-id"
        assert result["system"]["error"] == "Service unavailable"

        assert "improvement_suggestions" in result
        assert len(result["improvement_suggestions"]) == 1
        assert result["improvement_suggestions"][0]["type"] == "restructure"

    def test_degraded_result_generates_correlation_id(self):
        """Test that degraded result generates correlation_id if not provided."""
        result = create_degraded_result(error="Test error")

        assert "correlation_id" in result["system"]
        # Verify it's a valid UUID
        uuid.UUID(result["system"]["correlation_id"])

    def test_dataclass_without_detailed_scores(self):
        """Test that missing detailed_scores are generated."""
        result = MockValidationResult(is_valid=True, score=0.6, violations=[])

        schema_dict = dataclass_to_schema_dict(result)

        assert "detailed_scores" in schema_dict
        assert schema_dict["detailed_scores"]["taal"] == 0.6
        assert schema_dict["detailed_scores"]["juridisch"] == 0.6
        assert schema_dict["detailed_scores"]["structuur"] == 0.6
        assert schema_dict["detailed_scores"]["samenhang"] == 0.6

    def test_dataclass_without_passed_rules(self):
        """DEF-624: geen verzonnen geslaagde regels bij "geen violations".

        De oude default (`BASIC-001..003`) presenteerde bewijs van regels die
        nooit zijn gedraaid; ook een producent die zijn run meldt krijgt ze
        niet toebedeeld.
        """
        for result in (
            MockValidationResult(is_valid=True, score=1.0, violations=[]),
            MockProducentResult(is_valid=True, score=1.0, violations=[]),
        ):
            schema_dict = dataclass_to_schema_dict(result)

            assert schema_dict["passed_rules"] == [], result
            assert "BASIC-001" not in schema_dict["passed_rules"]
