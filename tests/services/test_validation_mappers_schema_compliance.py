import uuid

import pytest


def test_ensure_schema_compliance_adds_correlation_id_when_missing():
    from services.validation.mappers import ensure_schema_compliance

    raw = {
        "version": "1.0.0",
        "overall_score": 0.8,
        "is_acceptable": True,
        "violations": [],
        "passed_rules": [],
        "detailed_scores": {"taal": 0.8, "juridisch": 0.8, "structuur": 0.8, "samenhang": 0.8},
        "system": {},
    }

    out = ensure_schema_compliance(raw, correlation_id="00000000-0000-0000-0000-000000000000")
    assert out["system"]["correlation_id"] == "00000000-0000-0000-0000-000000000000"


def test_ensure_schema_compliance_converts_dataclass_result():
    from services.validation.mappers import ensure_schema_compliance
    from services.interfaces import ValidationResult

    # Dataclass result (legacy shape)
    dc = ValidationResult(is_valid=True, definition_text="Def.", score=0.8)

    out = ensure_schema_compliance(dc, correlation_id=str(uuid.uuid4()))
    assert isinstance(out, dict)
    assert "version" in out
    assert "system" in out and "correlation_id" in out["system"]


def test_create_degraded_result_schema_conform():
    from services.validation.mappers import create_degraded_result

    d = create_degraded_result(error="boom", correlation_id="00000000-0000-0000-0000-000000000001")
    assert d["version"]
    assert d["is_acceptable"] is False
    assert d["system"]["correlation_id"] == "00000000-0000-0000-0000-000000000001"
    # Improvement suggestion type should follow schema enum (e.g., 'restructure')
    assert d.get("improvement_suggestions"), "Expected improvement_suggestions"
    assert d["improvement_suggestions"][0]["type"] in {"restructure", "rewrite", "addition", "removal"}


def test_ensure_schema_compliance_on_invalid_type_yields_degraded():
    from services.validation.mappers import ensure_schema_compliance

    out = ensure_schema_compliance(object(), correlation_id="00000000-0000-0000-0000-000000000002")
    assert out["is_acceptable"] is False
    assert out["system"]["correlation_id"] == "00000000-0000-0000-0000-000000000002"
