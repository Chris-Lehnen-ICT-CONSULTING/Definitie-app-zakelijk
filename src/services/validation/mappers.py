"""Mappers voor ValidationResult conversies tussen dataclass en TypedDict.

Deze module handelt de conversie af tussen:
- services.interfaces.ValidationResult (dataclass) - gebruikt door legacy services
- services.validation.interfaces.ValidationResult (TypedDict) - JSON Schema conform

DEF-624 (contract 2.0.0): elke uitvoer draagt een expliciete runstatus. Een
conversie verzint nooit een run: een legacy object of dict zonder geldige
`validation_status` wordt `validation_unknown` (contract_status_missing/
invalid), een degraded result is `validation_unknown` (validation_error).
Alleen wat de bron werkelijk draagt reist mee; er worden geen geslaagde
regels of nullen voor een niet-beschikbare score verzonnen, en de invoer
wordt niet gemuteerd.
"""

import logging
import uuid
from datetime import UTC, datetime

UTC = UTC  # Python 3.10 compatibility
from typing import Any, cast

from services.interfaces import ValidationResult as DataclassResult
from services.validation.interfaces import (
    CONTRACT_VERSION,
    UNKNOWN_REASON_VALIDATION_ERROR,
    VALIDATION_STATUS_UNKNOWN,
    ImprovementSuggestion,
    RuleViolation,
    SystemMetadata,
    ValidationResult as TypedDictResult,
    ViolationLocation,
)
from services.validation.result_contract import (
    met_expliciete_runstatus,
    neem_contractvelden_over,
)

# Module logger
logger = logging.getLogger(__name__)

# Historische default (tot 1.4.0): drie verzonnen `BASIC-00x`-regels wanneer
# een legacy resultaat geen violations en geen passed_rules droeg. Sinds
# DEF-624 wordt deze lijst nergens meer ingevuld - een conversie verzint geen
# geslaagde regels. De naam blijft geëxporteerd voor bestaande imports.
DEFAULT_PASSED_RULES = ["BASIC-001", "BASIC-002", "BASIC-003"]


def _score_uit_object(result: Any) -> float | None:
    """`overall_score`, anders het legacy `score`; een expliciete None blijft None.

    Ontbreekt elk scoreattribuut, dan geldt de oude default 0.0.
    """
    if hasattr(result, "overall_score"):
        waarde = result.overall_score
    elif hasattr(result, "score"):
        waarde = result.score
    else:
        return 0.0
    if waarde is None:
        return None
    try:
        return float(waarde)
    except (TypeError, ValueError):
        return 0.0


def dataclass_to_schema_dict(
    result: DataclassResult, correlation_id: str | None = None
) -> TypedDictResult:
    """Converteer ValidationResult dataclass naar schema-conform TypedDict.

    De dataclass draagt geen runbewijs: zonder een werkelijk aanwezig,
    geldig `validation_status`-attribuut is de uitkomst `validation_unknown`
    (contract_status_missing), ook bij `is_valid=True` (DEF-624).

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
    for v in getattr(result, "violations", None) or []:
        # Handle severity enum vs string
        severity = getattr(v, "severity", "warning")
        if hasattr(severity, "value"):  # It's an enum
            severity = str(severity.value)

        # Map description to message (legacy field name)
        # DEF-439: garandeer een str (description kan None zijn → TypedDict eist str)
        message = (
            getattr(v, "message", None) or getattr(v, "description", None) or str(v)
        )

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

    # Scores: `overall_score` gaat vóór het legacy `score`; None blijft None
    # (niet beschikbaar is geen nul, DEF-622).
    overall_score = _score_uit_object(result)

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
        system["timestamp"] = datetime.now(UTC).isoformat()

    # Add processing time if available
    if hasattr(result, "processing_time_ms"):
        system["duration_ms"] = result.processing_time_ms

    # Check for errors (degraded mode)
    if hasattr(result, "error") and result.error:
        system["error"] = str(result.error)

    # Geslaagde regels: alleen wat de bron zelf meldt. De oude default
    # (DEFAULT_PASSED_RULES bij "geen violations") verzon bewijs.
    passed_rules = list(getattr(result, "passed_rules", None) or [])

    # Oordeel: het expliciete veld, anders de oude scoredrempel. Zonder
    # totaalscore is er geen drempel te toetsen (fail-closed).
    if hasattr(result, "is_acceptable"):
        is_acceptable = bool(result.is_acceptable)
    elif hasattr(result, "is_valid"):
        is_acceptable = bool(result.is_valid)
    else:
        is_acceptable = overall_score is not None and overall_score >= 0.5

    # Build final TypedDict result
    schema_result: dict[str, Any] = {
        "version": CONTRACT_VERSION,
        "overall_score": overall_score,
        "is_acceptable": is_acceptable,
        "violations": violations,
        "passed_rules": passed_rules,
        "detailed_scores": detailed_scores,
        "system": system,
    }

    # Add optional improvement suggestions
    if suggestions:
        schema_result["improvement_suggestions"] = suggestions

    # DEF-624: de contractvelden die het object werkelijk draagt reizen mee
    # (aanwezigheid vóór typecontrole: een ongeldige status blijft "ongeldig",
    # een expliciete lege bronbeoordeling blijft None); daarna maakt de
    # runstatus zichzelf expliciet (afwezig -> unknown).
    neem_contractvelden_over(schema_result, result)
    return cast(TypedDictResult, met_expliciete_runstatus(schema_result))


def ensure_schema_compliance(
    result: Any, correlation_id: str | None = None
) -> TypedDictResult:
    """Ensure any result is schema-compliant.

    Geeft altijd een nieuw dict terug met een expliciete runstatus; de
    invoer wordt niet gemuteerd (DEF-624). Een dict zonder geldige
    `validation_status` wordt `validation_unknown`.

    Args:
        result: Either a dataclass ValidationResult or dict-like result
        correlation_id: Optional correlation ID

    Returns:
        Schema-compliant TypedDictResult
    """
    # If already a dict with correct structure, validate and return
    if isinstance(result, dict) and "version" in result and "system" in result:
        uit: dict[str, Any] = dict(result)
        system = uit.get("system")
        if not isinstance(system, dict):
            system = {}
        # Ensure correlation_id is set (op een kopie van `system`)
        if not system.get("correlation_id"):
            uit["system"] = {
                **system,
                "correlation_id": correlation_id or str(uuid.uuid4()),
            }
        # DEF-439: runtime-gevalideerde shape (version+system aanwezig) → TypedDict
        return cast(TypedDictResult, met_expliciete_runstatus(uit))

    # If it's a dataclass, convert it
    if hasattr(result, "__dataclass_fields__"):
        return dataclass_to_schema_dict(result, correlation_id)

    # Fallback: create minimal valid result
    logger.error(
        f"Context validation failed: Invalid result type {type(result).__name__}. "
        f"Expected dataclass or dict with 'version' and 'system' keys. "
        f"correlation_id={correlation_id or 'N/A'}",
        exc_info=True,
    )
    return create_degraded_result(
        error="Invalid result type", correlation_id=correlation_id
    )


def create_degraded_result(
    error: str, correlation_id: str | None = None, begrip: str | None = None
) -> TypedDictResult:
    """Create a degraded mode result for errors.

    Een servicefout is geen uitgevoerde run: het resultaat is expliciet
    `validation_unknown` met reden `validation_error` (DEF-624). De
    placeholders 0.0/False zijn geen kwaliteitsoordeel.

    Args:
        error: Error message
        correlation_id: Optional correlation ID
        begrip: Optional begrip for context

    Returns:
        Schema-compliant degraded TypedDictResult
    """
    if not correlation_id:
        correlation_id = str(uuid.uuid4())

    # Log degraded result creation
    logger.error(
        f"Creating degraded validation result: {error}. "
        f"begrip={begrip or 'N/A'}, correlation_id={correlation_id}",
        exc_info=True,
    )

    violation: RuleViolation = {
        "code": "SYS-SVC-001",
        "severity": "error",
        "message": f"Service error: {error}",
        "rule_id": "system-error",
        "category": "system",
    }

    # Align with schema enum: use a permitted type (e.g., 'restructure')
    suggestion: ImprovementSuggestion = {
        "type": "restructure",
        "description": "The validation service encountered an error. Please try again.",
        "impact": "high",
    }

    system: SystemMetadata = {
        "correlation_id": correlation_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "error": error,
    }

    result: TypedDictResult = {
        "version": CONTRACT_VERSION,
        "validation_status": VALIDATION_STATUS_UNKNOWN,
        "unknown_reason": UNKNOWN_REASON_VALIDATION_ERROR,
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
