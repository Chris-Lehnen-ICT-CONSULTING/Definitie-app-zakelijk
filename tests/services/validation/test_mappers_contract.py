import re

import pytest

from services.interfaces import ValidationResult as DCValidationResult, ValidationViolation, ValidationSeverity
from services.validation.interfaces import CONTRACT_VERSION
from services.validation.mappers import ensure_schema_compliance, dataclass_to_schema_dict, DEFAULT_PASSED_RULES


def test_dataclass_to_schema_minimal_maps_core_fields():
    dc = DCValidationResult(is_valid=True, definition_text="txt", score=0.8)
    mapped = dataclass_to_schema_dict(dc, correlation_id="00000000-0000-0000-0000-000000000000")

    assert isinstance(mapped, dict)
    assert mapped["version"] == CONTRACT_VERSION
    assert mapped["overall_score"] == 0.8
    assert mapped["is_acceptable"] is True
    assert mapped["system"]["correlation_id"]
    # No violations -> defaults to passed rules list
    assert mapped["passed_rules"] == DEFAULT_PASSED_RULES


def test_violation_mapping_and_defaults():
    v = ValidationViolation(rule_id="STR-01", severity=ValidationSeverity.HIGH, description="desc", suggestion="fix it")
    dc = DCValidationResult(is_valid=False, definition_text="x", score=0.2, violations=[v])
    mapped = dataclass_to_schema_dict(dc, correlation_id=None)

    assert mapped["version"] == CONTRACT_VERSION
    assert mapped["is_acceptable"] is False
    assert isinstance(mapped["violations"], list) and mapped["violations"]
    mv = mapped["violations"][0]
    assert mv["rule_id"] == "STR-01"
    # Code defaults when absent
    assert isinstance(mv.get("code"), str)
    # Message derived from description
    assert "desc" in mv["message"]


def test_ensure_schema_compliance_on_dict_adds_correlation_id():
    result = {
        "version": CONTRACT_VERSION,
        "overall_score": 0.5,
        "is_acceptable": True,
        "violations": [],
        "passed_rules": [],
        "detailed_scores": {"taal": 0.5},
        "system": {},
    }
    ensured = ensure_schema_compliance(result, correlation_id=None)
    assert ensured["system"].get("correlation_id")
    assert re.match(r"^[0-9a-f\-]{36}$", ensured["system"]["correlation_id"]) is not None


def test_ensure_schema_compliance_invalid_type_returns_degraded():
    ensured = ensure_schema_compliance(object(), correlation_id="00000000-0000-0000-0000-000000000000")
    assert ensured["is_acceptable"] is False
    assert any(v.get("code") == "SYS-SVC-001" for v in ensured.get("violations", []))

