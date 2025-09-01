"""Mappers voor ValidationResult conversies tussen dataclass en TypedDict.

Deze module handelt de conversie af tussen:
- services.interfaces.ValidationResult (dataclass) - gebruikt door legacy services
- services.validation.interfaces.ValidationResult (TypedDict) - JSON Schema conform
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from services.interfaces import ValidationResult as DataclassResult
from services.validation.interfaces import (
    CONTRACT_VERSION,
    ImprovementSuggestion,
    RuleViolation,
    SystemMetadata,
    ValidationResult as TypedDictResult,
    ViolationLocation,
)

# Default passed rules configuration
DEFAULT_PASSED_RULES = ["BASIC-001", "BASIC-002", "BASIC-003"]


def dataclass_to_schema_dict(
    result: DataclassResult, correlation_id: str | None = None
) -> TypedDictResult:
    """Converteer ValidationResult dataclass naar schema-conform TypedDict.

    Args:
        result: De dataclass ValidationResult van legacy services
        correlation_id: Optionele correlation ID (genereert nieuwe indien None)

    Returns:
        TypedDictResult conform JSON Schema validation_result.schema.json
    """
    # Generate correlation ID if not provided
    if not correlation_id:
        correlation_id = str(uuid.uuid4())

    # Map violations naar schema format
    violations: list[RuleViolation] = []
    for v in getattr(result, "violations", []):
        # Handle severity enum vs string
        severity = getattr(v, "severity", "warning")
        if hasattr(severity, "value"):  # It's an enum
            severity = str(severity.value)

        # Map description to message (legacy field name)
        message = getattr(v, "message", None)
        if not message:
            message = getattr(v, "description", str(v))

        violation: RuleViolation = {
            "code": getattr(v, "code", "VAL-UNK-000"),
            "severity": severity,
            "message": message,
            "rule_id": getattr(v, "rule_id", "unknown"),
            "category": getattr(v, "category", "system"),
        }

        # Add optional location if present
        if hasattr(v, "location") and v.location:
            location: ViolationLocation = {}
            # Handle dict or object location
            if isinstance(v.location, dict):
                if "line" in v.location:
                    location["line"] = v.location["line"]
                if "column" in v.location:
                    location["column"] = v.location["column"]
            else:
                if hasattr(v.location, "line"):
                    location["line"] = v.location.line
                if hasattr(v.location, "column"):
                    location["column"] = v.location.column
            if location:  # Only add if not empty
                violation["location"] = location

        # Add suggestions if present (handle both singular and plural)
        suggestions_list = None
        if hasattr(v, "suggestions") and v.suggestions:
            suggestions_list = list(v.suggestions)
        elif hasattr(v, "suggestion") and v.suggestion:
            # Handle singular form
            suggestions_list = [str(v.suggestion)]

        if suggestions_list:
            violation["suggestions"] = suggestions_list

        violations.append(violation)

    # Map improvement suggestions
    suggestions: list[ImprovementSuggestion] = []
    suggestions_raw = getattr(result, "suggestions", [])
    if suggestions_raw:  # Only iterate if not None
        for s in suggestions_raw:
            suggestion: ImprovementSuggestion = {
                "type": getattr(s, "type", "improvement"),
                "description": getattr(s, "description", str(s)),
            }
            if hasattr(s, "example"):
                suggestion["example"] = s.example
            if hasattr(s, "impact"):
                suggestion["impact"] = s.impact
            suggestions.append(suggestion)

    # Calculate scores
    overall_score = getattr(result, "score", 0.0)
    if hasattr(result, "overall_score"):
        overall_score = result.overall_score

    # Map detailed scores - gebruik defaults als niet aanwezig
    detailed_scores = getattr(result, "detailed_scores", {})
    if not detailed_scores:
        # Generate default scores based on overall
        detailed_scores = {
            "taal": overall_score,
            "juridisch": overall_score,
            "structuur": overall_score,
            "samenhang": overall_score,
        }

    # Build system metadata
    system: SystemMetadata = {
        "correlation_id": correlation_id,
    }

    # Add optional system fields
    if hasattr(result, "engine_version"):
        system["engine_version"] = result.engine_version
    if hasattr(result, "profile_used"):
        system["profile_used"] = result.profile_used
    if hasattr(result, "timestamp"):
        system["timestamp"] = result.timestamp
    else:
        system["timestamp"] = datetime.now(timezone.utc).isoformat()

    # Add processing time if available
    if hasattr(result, "processing_time_ms"):
        system["duration_ms"] = result.processing_time_ms

    # Check for errors (degraded mode)
    if hasattr(result, "error") and result.error:
        system["error"] = str(result.error)

    # Get passed rules
    passed_rules = getattr(result, "passed_rules", [])
    if not passed_rules and not violations:
        # If no violations and no explicit passed rules, use defaults
        passed_rules = DEFAULT_PASSED_RULES

    # Build final TypedDict result
    schema_result: TypedDictResult = {
        "version": CONTRACT_VERSION,
        "overall_score": overall_score,
        "is_acceptable": getattr(result, "is_valid", overall_score >= 0.5),
        "violations": violations,
        "passed_rules": passed_rules,
        "detailed_scores": detailed_scores,
        "system": system,
    }

    # Add optional improvement suggestions
    if suggestions:
        schema_result["improvement_suggestions"] = suggestions

    return schema_result


def ensure_schema_compliance(
    result: Any, correlation_id: str | None = None
) -> TypedDictResult:
    """Ensure any result is schema-compliant.

    Args:
        result: Either a dataclass ValidationResult or dict-like result
        correlation_id: Optional correlation ID

    Returns:
        Schema-compliant TypedDictResult
    """
    # If already a dict with correct structure, validate and return
    if isinstance(result, dict) and "version" in result and "system" in result:
        # Ensure correlation_id is set
        if not result.get("system", {}).get("correlation_id"):
            if "system" not in result:
                result["system"] = {}
            result["system"]["correlation_id"] = correlation_id or str(uuid.uuid4())
        return result

    # If it's a dataclass, convert it
    if hasattr(result, "__dataclass_fields__"):
        return dataclass_to_schema_dict(result, correlation_id)

    # Fallback: create minimal valid result
    return create_degraded_result(
        error="Invalid result type", correlation_id=correlation_id
    )


def create_degraded_result(
    error: str, correlation_id: str | None = None, begrip: str | None = None
) -> TypedDictResult:
    """Create a degraded mode result for errors.

    Args:
        error: Error message
        correlation_id: Optional correlation ID
        begrip: Optional begrip for context

    Returns:
        Schema-compliant degraded TypedDictResult
    """
    if not correlation_id:
        correlation_id = str(uuid.uuid4())

    violation: RuleViolation = {
        "code": "SYS-SVC-001",
        "severity": "error",
        "message": f"Service error: {error}",
        "rule_id": "system-error",
        "category": "system",
    }

    suggestion: ImprovementSuggestion = {
        "type": "retry",
        "description": "The validation service encountered an error. Please try again.",
        "impact": "high",
    }

    system: SystemMetadata = {
        "correlation_id": correlation_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "error": error,
    }

    result: TypedDictResult = {
        "version": CONTRACT_VERSION,
        "overall_score": 0.0,
        "is_acceptable": False,
        "violations": [violation],
        "passed_rules": [],
        "detailed_scores": {
            "taal": 0.0,
            "juridisch": 0.0,
            "structuur": 0.0,
            "samenhang": 0.0,
        },
        "system": system,
        "improvement_suggestions": [suggestion],
    }

    return result
