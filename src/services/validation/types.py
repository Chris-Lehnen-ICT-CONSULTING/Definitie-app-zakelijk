"""
Unified ValidationResult types for DEF-238.

This module provides the single source of truth for validation result types,
replacing the multiple inconsistent representations across the codebase.

Key Design Decisions:
- TypedDict-based for JSON serialization compatibility and compile-time type safety
- Schema-first approach aligned with validation_result.schema.json
- VERSION 2.0.0 introduces acceptance_gate for establishment decision support
- All factory functions guarantee schema compliance

Migration Path:
- Legacy dataclass ValidationResult (services.interfaces) -> use normalize_to_unified()
- Legacy TypedDict ValidationResult (services.validation.interfaces) -> compatible, use as-is
- Dict from external sources -> use normalize_to_unified()

Usage:
    from services.validation.types import (
        ValidationResult,
        create_validation_result,
        create_degraded_result,
        normalize_to_unified,
    )
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any, Literal, NotRequired

from typing_extensions import TypedDict

# Contract version - bump on breaking changes to schema
CONTRACT_VERSION = "2.0.0"

# Module logger
logger = logging.getLogger(__name__)

# ==============================================================================
# Type Literals
# ==============================================================================

# Severity for violations (schema: "info" | "warning" | "error")
SeverityType = Literal["error", "warning", "info"]

# Impact/priority levels for suggestions (aligned with JSON schema)
# Note: JSON schema uses "low", "medium", "high" - NO "critical"
ImpactLevel = Literal["low", "medium", "high"]

# Legacy alias for internal priority tracking (includes critical)
SeverityLevel = Literal["critical", "high", "medium", "low"]

# Improvement suggestion types (schema enum)
ImprovementType = Literal["rewrite", "addition", "removal", "restructure"]

# Category types for violations and scores
CategoryType = Literal["taal", "juridisch", "structuur", "samenhang", "system"]

# Acceptance gate status
GateStatus = Literal["pass", "blocked", "override_required"]

# ==============================================================================
# Supporting TypedDicts
# ==============================================================================


class TextSpan(TypedDict):
    """Text span with start/end indices for locating violations."""

    start: int  # 0-based character index
    end: int  # 0-based character index (exclusive)


class ViolationLocation(TypedDict, total=False):
    """Location of a violation in text - all fields optional."""

    text_span: NotRequired[TextSpan]
    indices: NotRequired[list[int]]  # Alternative: list of character positions
    line: NotRequired[int]  # 1-based line number
    column: NotRequired[int]  # 1-based column number


class ViolationDict(TypedDict):
    """Single validation violation with full metadata.

    Schema requires: code, severity, message, rule_id, category
    """

    # Required fields (per schema)
    code: str  # Pattern: ^[A-Z]{3}-[A-Z]{3}-\d{3}$ (e.g., VAL-STR-001)
    severity: SeverityType  # "info" | "warning" | "error"
    message: str  # User-friendly error message (i18n ready)
    rule_id: str  # Specific rule identifier (e.g., ARAI04SUB1)
    category: CategoryType  # Violation category

    # Optional fields
    location: NotRequired[ViolationLocation]
    suggestions: NotRequired[list[str]]  # Possible fixes
    metadata: NotRequired[dict[str, Any]]  # Additional context


class ProcessingTimings(TypedDict, total=False):
    """Detailed timing breakdown for performance monitoring."""

    cleaning_ms: NotRequired[int]
    validation_ms: NotRequired[int]
    enhancement_ms: NotRequired[int]


class SystemMetadata(TypedDict):
    """System metadata with required correlation_id for tracing.

    Schema requires: correlation_id
    """

    # Required field
    correlation_id: str  # UUID format

    # Optional fields
    engine_version: NotRequired[str]
    profile_used: NotRequired[str]
    timestamp: NotRequired[str]  # ISO 8601 format
    duration_ms: NotRequired[int]
    timings: NotRequired[ProcessingTimings]
    error: NotRequired[str]  # Present when degraded result


class CategoryScores(TypedDict, total=False):
    """Score breakdown by validation category (0.0-1.0 each)."""

    taal: float  # Language quality score
    juridisch: float  # Legal compliance score
    structuur: float  # Structural quality score
    samenhang: float  # Coherence/consistency score


class ImprovementSuggestion(TypedDict):
    """AI-powered improvement suggestion.

    Schema requires: type, description
    """

    # Required fields
    type: ImprovementType  # "rewrite" | "addition" | "removal" | "restructure"
    description: str

    # Optional fields
    example: NotRequired[str]  # Example of improved text
    impact: NotRequired[
        ImpactLevel
    ]  # Expected impact on score (schema: low/medium/high)


class AcceptanceGate(TypedDict, total=False):
    """Acceptance gate evaluation for establishment decision.

    New in VERSION 2.0.0 - supports establishment workflow.
    """

    status: GateStatus  # "pass" | "blocked" | "override_required"
    acceptable: bool  # Whether definition meets minimum thresholds
    gates_passed: list[str]  # List of passed gate identifiers
    gates_failed: list[str]  # List of failed gate identifiers
    reasons: list[str]  # Human-readable reasons for decision
    thresholds: dict[str, float]  # Thresholds used for decision


# ==============================================================================
# Main ValidationResult Type
# ==============================================================================


class ValidationResult(TypedDict, total=False):
    """Unified ValidationResult contract aligned with JSON Schema.

    This is the single source of truth for validation results.
    All required fields per validation_result.schema.json:
    - version, overall_score, is_acceptable, violations,
    - passed_rules, detailed_scores, system

    VERSION 2.0.0 adds optional acceptance_gate for establishment support.
    """

    # Required fields (per schema)
    version: str  # Contract version (SemVer pattern: \d+.\d+.\d+)
    overall_score: float  # 0.0-1.0
    is_acceptable: bool  # Whether validation passed minimum requirements
    violations: list[ViolationDict]  # All validation violations
    passed_rules: list[str]  # Rule IDs that passed
    detailed_scores: CategoryScores  # Score breakdown by category
    system: SystemMetadata  # System metadata

    # Optional fields
    improvement_suggestions: NotRequired[list[ImprovementSuggestion]]
    acceptance_gate: NotRequired[AcceptanceGate]  # New in 2.0.0


# ==============================================================================
# Factory Functions
# ==============================================================================


def create_validation_result(
    overall_score: float,
    is_acceptable: bool,
    violations: list[ViolationDict] | None = None,
    passed_rules: list[str] | None = None,
    detailed_scores: CategoryScores | None = None,
    correlation_id: str | None = None,
    engine_version: str | None = None,
    profile_used: str | None = None,
    duration_ms: int | None = None,
    improvement_suggestions: list[ImprovementSuggestion] | None = None,
    acceptance_gate: AcceptanceGate | None = None,
) -> ValidationResult:
    """Create a new schema-compliant ValidationResult.

    Args:
        overall_score: Overall validation score (0.0-1.0)
        is_acceptable: Whether the validation passed minimum requirements
        violations: List of validation violations (default: empty list)
        passed_rules: List of passed rule IDs (default: empty list)
        detailed_scores: Score breakdown by category (default: derived from overall)
        correlation_id: UUID for tracing (generated if not provided)
        engine_version: Validation engine version
        profile_used: Validation profile name
        duration_ms: Total processing time in milliseconds
        improvement_suggestions: AI-powered improvement suggestions
        acceptance_gate: Acceptance gate evaluation (VERSION 2.0.0)

    Returns:
        Schema-compliant ValidationResult

    Example:
        result = create_validation_result(
            overall_score=0.85,
            is_acceptable=True,
            violations=[{
                "code": "VAL-STR-001",
                "severity": "warning",
                "message": "Definition too long",
                "rule_id": "ARAI04SUB1",
                "category": "structuur",
            }],
            passed_rules=["BASIC-001", "BASIC-002"],
        )
    """
    # Generate correlation_id if not provided
    if not correlation_id:
        correlation_id = str(uuid.uuid4())

    # Default violations and passed_rules to empty lists
    if violations is None:
        violations = []
    if passed_rules is None:
        passed_rules = []

    # Default detailed_scores based on overall_score
    if detailed_scores is None:
        detailed_scores = {
            "taal": overall_score,
            "juridisch": overall_score,
            "structuur": overall_score,
            "samenhang": overall_score,
        }

    # Build system metadata
    system: SystemMetadata = {
        "correlation_id": correlation_id,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    if engine_version:
        system["engine_version"] = engine_version
    if profile_used:
        system["profile_used"] = profile_used
    if duration_ms is not None:
        system["duration_ms"] = duration_ms

    # Build result
    result: ValidationResult = {
        "version": CONTRACT_VERSION,
        "overall_score": overall_score,
        "is_acceptable": is_acceptable,
        "violations": violations,
        "passed_rules": passed_rules,
        "detailed_scores": detailed_scores,
        "system": system,
    }

    # Add optional fields
    if improvement_suggestions:
        result["improvement_suggestions"] = improvement_suggestions
    if acceptance_gate:
        result["acceptance_gate"] = acceptance_gate

    return result


def create_degraded_result(
    error: str,
    correlation_id: str | None = None,
    begrip: str | None = None,
    include_retry_suggestion: bool = True,
) -> ValidationResult:
    """Create a degraded mode result for service errors.

    Used when validation cannot complete normally due to service errors,
    timeouts, or other operational failures. The result is schema-compliant
    but indicates the error condition clearly.

    Args:
        error: Error message describing the failure
        correlation_id: UUID for tracing (generated if not provided)
        begrip: Optional begrip for context in logging
        include_retry_suggestion: Whether to add retry suggestion (default: True)

    Returns:
        Schema-compliant ValidationResult with error state

    Example:
        result = create_degraded_result(
            error="AI service timeout",
            correlation_id="abc-123",
            begrip="Test begrip",
        )
    """
    if not correlation_id:
        correlation_id = str(uuid.uuid4())

    # Log degraded result creation
    logger.warning(
        f"Creating degraded validation result: {error}. "
        f"begrip={begrip or 'N/A'}, correlation_id={correlation_id}"
    )

    # Build system violation
    violation: ViolationDict = {
        "code": "SYS-SVC-001",
        "severity": "error",
        "message": f"Service error: {error}",
        "rule_id": "system-error",
        "category": "system",
    }

    # Optional retry suggestion
    suggestions: list[ImprovementSuggestion] = []
    if include_retry_suggestion:
        suggestions.append(
            {
                "type": "restructure",
                "description": "The validation service encountered an error. Please try again.",
                "impact": "high",
            }
        )

    # Build system metadata with error
    system: SystemMetadata = {
        "correlation_id": correlation_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "error": error,
    }

    result: ValidationResult = {
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
    }

    if suggestions:
        result["improvement_suggestions"] = suggestions

    return result


def normalize_to_unified(
    result: Any,
    correlation_id: str | None = None,
) -> ValidationResult:
    """Normalize any validation result format to unified ValidationResult.

    This function handles conversion from:
    1. Dict with 'version' and 'system' keys (already schema-compliant)
    2. Dataclass ValidationResult (from services.interfaces)
    3. Legacy dicts without version/system structure

    Args:
        result: Any validation result format
        correlation_id: Optional correlation ID (used if not present in result)

    Returns:
        Schema-compliant ValidationResult

    Example:
        # From legacy dataclass
        legacy = DataclassValidationResult(is_valid=True, score=0.8)
        unified = normalize_to_unified(legacy)

        # From dict
        data = {"is_valid": True, "score": 0.75}
        unified = normalize_to_unified(data, correlation_id="abc-123")
    """
    # Case 1: Already a schema-compliant dict
    if isinstance(result, dict) and "version" in result and "system" in result:
        # Make shallow copy to avoid mutating input
        result = {**result}
        # Ensure correlation_id is set (copy system dict too to avoid mutation)
        if not result.get("system", {}).get("correlation_id"):
            result["system"] = {**result.get("system", {})}
            result["system"]["correlation_id"] = correlation_id or str(uuid.uuid4())
        return result

    # Case 2: Dataclass with __dataclass_fields__
    if hasattr(result, "__dataclass_fields__"):
        return _convert_dataclass_to_unified(result, correlation_id)

    # Case 3: Legacy dict without version/system
    if isinstance(result, dict):
        return _convert_legacy_dict_to_unified(result, correlation_id)

    # Case 4: Unknown type - create degraded result
    logger.error(
        f"Cannot normalize result of type {type(result).__name__}. "
        f"correlation_id={correlation_id or 'N/A'}"
    )
    return create_degraded_result(
        error=f"Invalid result type: {type(result).__name__}",
        correlation_id=correlation_id,
    )


# ==============================================================================
# Internal Conversion Helpers
# ==============================================================================


def _convert_dataclass_to_unified(
    result: Any,
    correlation_id: str | None = None,
) -> ValidationResult:
    """Convert a dataclass ValidationResult to unified format.

    Internal helper for normalize_to_unified().
    """
    if not correlation_id:
        correlation_id = str(uuid.uuid4())

    # Extract violations from dataclass
    violations: list[ViolationDict] = []
    for v in getattr(result, "violations", []) or []:
        # Handle severity enum vs string
        severity = getattr(v, "severity", "warning")
        if hasattr(severity, "value"):
            severity = str(severity.value)
        # Map to allowed values
        if severity not in ("info", "warning", "error"):
            severity = "warning"

        # Get message from description or message attribute
        message = getattr(v, "message", None)
        if not message:
            message = getattr(v, "description", str(v))

        violation: ViolationDict = {
            "code": getattr(v, "code", "VAL-UNK-000"),
            "severity": severity,  # type: ignore[typeddict-item]
            "message": message,
            "rule_id": getattr(v, "rule_id", "unknown"),
            "category": getattr(v, "category", "system"),
        }

        # Add optional location
        if hasattr(v, "location") and v.location:
            location: ViolationLocation = {}
            loc = v.location
            if isinstance(loc, dict):
                if "line" in loc:
                    location["line"] = loc["line"]
                if "column" in loc:
                    location["column"] = loc["column"]
                if "text_span" in loc:
                    location["text_span"] = loc["text_span"]
            else:
                if hasattr(loc, "line") and loc.line:
                    location["line"] = loc.line
                if hasattr(loc, "column") and loc.column:
                    location["column"] = loc.column
            if location:
                violation["location"] = location

        # Add suggestions
        suggestions_list: list[str] = []
        if hasattr(v, "suggestions") and v.suggestions:
            suggestions_list = list(v.suggestions)
        elif hasattr(v, "suggestion") and v.suggestion:
            suggestions_list = [str(v.suggestion)]
        if suggestions_list:
            violation["suggestions"] = suggestions_list

        violations.append(violation)

    # Extract improvement suggestions
    improvement_suggestions: list[ImprovementSuggestion] = []
    for s in getattr(result, "suggestions", []) or []:
        if isinstance(s, str):
            improvement_suggestions.append({"type": "rewrite", "description": s})
        else:
            suggestion: ImprovementSuggestion = {
                "type": getattr(s, "type", "rewrite"),
                "description": getattr(s, "description", str(s)),
            }
            if hasattr(s, "example") and s.example:
                suggestion["example"] = s.example
            if hasattr(s, "impact") and s.impact:
                suggestion["impact"] = s.impact
            improvement_suggestions.append(suggestion)

    # Extract scores
    overall_score = getattr(result, "score", 0.0)
    if overall_score is None:
        overall_score = 0.0

    # Detailed scores
    detailed_scores = getattr(result, "detailed_scores", None)
    if not detailed_scores:
        detailed_scores = {
            "taal": overall_score,
            "juridisch": overall_score,
            "structuur": overall_score,
            "samenhang": overall_score,
        }

    # Passed rules
    passed_rules = getattr(result, "passed_rules", [])
    if not passed_rules and not violations:
        passed_rules = ["BASIC-001", "BASIC-002", "BASIC-003"]

    # Build system metadata
    system: SystemMetadata = {"correlation_id": correlation_id}

    if hasattr(result, "engine_version") and result.engine_version:
        system["engine_version"] = result.engine_version
    if hasattr(result, "profile_used") and result.profile_used:
        system["profile_used"] = result.profile_used
    if hasattr(result, "timestamp") and result.timestamp:
        system["timestamp"] = result.timestamp
    else:
        system["timestamp"] = datetime.now(UTC).isoformat()
    if hasattr(result, "processing_time_ms") and result.processing_time_ms:
        system["duration_ms"] = result.processing_time_ms
    if hasattr(result, "error") and result.error:
        system["error"] = str(result.error)

    # Build final result
    is_acceptable = getattr(result, "is_valid", overall_score >= 0.5)

    unified: ValidationResult = {
        "version": CONTRACT_VERSION,
        "overall_score": overall_score,
        "is_acceptable": is_acceptable,
        "violations": violations,
        "passed_rules": passed_rules,
        "detailed_scores": detailed_scores,
        "system": system,
    }

    if improvement_suggestions:
        unified["improvement_suggestions"] = improvement_suggestions

    return unified


def _convert_legacy_dict_to_unified(
    result: dict[str, Any],
    correlation_id: str | None = None,
) -> ValidationResult:
    """Convert a legacy dict format to unified ValidationResult.

    Internal helper for normalize_to_unified().
    Handles dicts that lack the version/system structure.
    """
    if not correlation_id:
        correlation_id = str(uuid.uuid4())

    # Extract what we can from the dict
    overall_score = result.get("score", result.get("overall_score", 0.0))
    if overall_score is None:
        overall_score = 0.0

    is_acceptable = result.get(
        "is_valid", result.get("is_acceptable", overall_score >= 0.5)
    )

    # Convert violations if present
    violations: list[ViolationDict] = []
    raw_violations = result.get("violations", [])
    for v in raw_violations or []:
        if isinstance(v, dict):
            violation: ViolationDict = {
                "code": v.get("code", "VAL-UNK-000"),
                "severity": v.get("severity", "warning"),
                "message": v.get("message", v.get("description", "Unknown violation")),
                "rule_id": v.get("rule_id", "unknown"),
                "category": v.get("category", "system"),
            }
            if "location" in v:
                violation["location"] = v["location"]
            if "suggestions" in v:
                violation["suggestions"] = v["suggestions"]
            violations.append(violation)

    # Handle legacy errors/warnings as violations
    for error in result.get("errors", []) or []:
        violations.append(
            {
                "code": "VAL-ERR-001",
                "severity": "error",
                "message": str(error),
                "rule_id": "legacy-error",
                "category": "system",
            }
        )
    for warning in result.get("warnings", []) or []:
        violations.append(
            {
                "code": "VAL-WRN-001",
                "severity": "warning",
                "message": str(warning),
                "rule_id": "legacy-warning",
                "category": "system",
            }
        )

    # Detailed scores
    detailed_scores = result.get("detailed_scores")
    if not detailed_scores:
        detailed_scores = {
            "taal": overall_score,
            "juridisch": overall_score,
            "structuur": overall_score,
            "samenhang": overall_score,
        }

    # Passed rules
    passed_rules = result.get("passed_rules", [])
    if not passed_rules and not violations:
        passed_rules = ["BASIC-001", "BASIC-002", "BASIC-003"]

    # System metadata
    system: SystemMetadata = {
        "correlation_id": correlation_id,
        "timestamp": result.get("timestamp", datetime.now(UTC).isoformat()),
    }

    unified: ValidationResult = {
        "version": CONTRACT_VERSION,
        "overall_score": overall_score,
        "is_acceptable": is_acceptable,
        "violations": violations,
        "passed_rules": passed_rules,
        "detailed_scores": detailed_scores,
        "system": system,
    }

    # Convert suggestions if present
    raw_suggestions = result.get("suggestions", [])
    if raw_suggestions:
        improvement_suggestions: list[ImprovementSuggestion] = []
        for s in raw_suggestions:
            if isinstance(s, str):
                improvement_suggestions.append({"type": "rewrite", "description": s})
            elif isinstance(s, dict):
                improvement_suggestions.append(
                    {
                        "type": s.get("type", "rewrite"),
                        "description": s.get("description", str(s)),
                    }
                )
        if improvement_suggestions:
            unified["improvement_suggestions"] = improvement_suggestions

    return unified


# ==============================================================================
# Validation Helpers
# ==============================================================================


def is_valid_result(result: Any) -> bool:
    """Check if a result is a valid schema-compliant ValidationResult.

    Args:
        result: Any object to check

    Returns:
        True if result is a valid ValidationResult dict with all required fields
    """
    if not isinstance(result, dict):
        return False

    required_fields = {
        "version",
        "overall_score",
        "is_acceptable",
        "violations",
        "passed_rules",
        "detailed_scores",
        "system",
    }

    if not required_fields.issubset(result.keys()):
        return False

    # Check system has correlation_id
    system = result.get("system", {})
    return isinstance(system, dict) and "correlation_id" in system


def get_blocking_violations(result: ValidationResult) -> list[ViolationDict]:
    """Get violations that block acceptance (severity: error).

    Args:
        result: ValidationResult to inspect

    Returns:
        List of error-severity violations
    """
    return [v for v in result.get("violations", []) if v.get("severity") == "error"]


def get_category_score(result: ValidationResult, category: CategoryType) -> float:
    """Get the score for a specific category.

    Args:
        result: ValidationResult to inspect
        category: Category to get score for

    Returns:
        Score for the category (0.0-1.0), defaults to overall_score if not found
    """
    scores = result.get("detailed_scores", {})
    return scores.get(category, result.get("overall_score", 0.0))


# ==============================================================================
# Type Exports
# ==============================================================================

__all__ = [
    "CONTRACT_VERSION",
    "AcceptanceGate",
    "CategoryScores",
    "CategoryType",
    "GateStatus",
    "ImpactLevel",
    "ImprovementSuggestion",
    "ImprovementType",
    "ProcessingTimings",
    "SeverityLevel",
    "SeverityType",
    "SystemMetadata",
    "TextSpan",
    "ValidationResult",
    "ViolationDict",
    "ViolationLocation",
    "create_degraded_result",
    "create_validation_result",
    "get_blocking_violations",
    "get_category_score",
    "is_valid_result",
    "normalize_to_unified",
]
