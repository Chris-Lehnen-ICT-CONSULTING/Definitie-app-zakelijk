"""
Unified ValidationResult types for DEF-238.

This module provides factory and normalisation helpers for validation results.

Key Design Decisions:
- TypedDict-based for JSON serialization compatibility and compile-time type safety
- Schema-first approach aligned with validation_result.schema.json
- DEF-624: één contractdefinitie. `CONTRACT_VERSION`, `ValidationResult` en de
  gedeelde deel-TypedDicts komen uit `services.validation.interfaces`; dit
  bestand herexporteert ze (bestaande imports blijven werken) en voert geen
  eigen, afwijkend versienummer meer. Elke uitvoer draagt een expliciete
  runstatus; een conversie verzint nooit een run (`validated` komt alleen van
  een producent die werkelijk evalueerde), geen geslaagde regels en geen nul
  voor een niet-beschikbare score.
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
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any, Literal, NotRequired, cast

from typing_extensions import TypedDict

from services.validation.interfaces import (
    CONTRACT_VERSION,
    UNKNOWN_REASON_RULESET_INCOMPLETE,
    UNKNOWN_REASON_VALIDATION_ERROR,
    VALIDATION_STATUS_UNKNOWN,
    VALIDATION_STATUS_VALIDATED,
    AcceptanceGate,
    ProcessingTimings,
    TextSpan,
    UnknownReason,
    ValidationReadinessDict,
    ValidationResult,
    ValidationStatus,
    ViolationLocation,
)
from services.validation.result_contract import (
    BEKENDE_REDENEN,
    Runstatus,
    bepaal_runstatus,
    is_geldige_readiness,
    met_expliciete_runstatus,
    neem_contractvelden_over,
)

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
#
# TextSpan, ViolationLocation, ProcessingTimings, AcceptanceGate en
# ValidationResult zijn herexports van de canonieke binding in
# services.validation.interfaces. De typen hieronder bestaan alleen hier:
# strikter (verplichte sleutels) dan hun canonieke tegenhanger, voor de
# fabrieken in dit bestand.


class ViolationDict(TypedDict):
    """Single validation violation with full metadata.

    Schema requires: code, severity, message, rule_id, category.
    Strikte (total=True) variant van interfaces.RuleViolation.
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
    """Score breakdown by validation category (0.0-1.0 each, of None)."""

    taal: float | None  # Language quality score
    juridisch: float | None  # Legal compliance score
    structuur: float | None  # Structural quality score
    samenhang: float | None  # Coherence/consistency score


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


# ==============================================================================
# Factory Functions
# ==============================================================================


# Vereiste keys per ValidationResult JSON-schema. Wordt gebruikt door
# _assert_validation_result_keys() om externe data (bv. uit Case 1 in
# normalize_to_unified) lichtgewicht te valideren voordat we cast'en.
# `validation_status` staat hier bewust niet bij: dat is de invoergrens
# (afwezig -> validation_unknown), geen reden om de invoer te weigeren.
_VALIDATION_RESULT_REQUIRED_KEYS = frozenset(
    {
        "version",
        "overall_score",
        "is_acceptable",
        "violations",
        "passed_rules",
        "detailed_scores",
        "system",
    }
)


def _assert_validation_result_keys(data: dict[str, Any]) -> None:
    """Lichtgewicht runtime-validatie van ValidationResult-shape.

    Gebruikt voor externe data (Case 1 in `normalize_to_unified`): controleert
    dat alle required keys aanwezig zijn voordat `cast(ValidationResult, ...)`
    wordt toegepast. Voorkomt stille downstream KeyError/TypeError door een
    misvormde input vroeg te vangen met een duidelijke foutmelding.

    **Wat deze helper WEL checkt:**
    - Aanwezigheid van alle keys in `_VALIDATION_RESULT_REQUIRED_KEYS`.

    **Wat deze helper NIET checkt (bewuste trade-off):**
    - Value-types (bv. `overall_score` als string ipv float passeert).
    - Value-ranges (bv. score buiten [0.0, 1.0] passeert).
    - Geneste structuur (bv. `system` zonder `correlation_id` passeert).
    - Onverwachte extra keys (forward-compat — extra keys mogen).

    Bewust licht om de hot path niet te belasten. Voor strict schema-validatie
    met value-types: zie `docs/architectuur/contracts/schemas/validation_result.schema.json`
    of overweeg Pydantic `TypeAdapter` (DEF-408 review-bevinding HIGH-2).

    Raises:
        TypeError: als er required keys ontbreken.
    """
    missing = _VALIDATION_RESULT_REQUIRED_KEYS - data.keys()
    if missing:
        raise TypeError(
            f"ValidationResult ontbreekt vereiste keys: {sorted(missing)}. "
            f"Got keys: {sorted(data.keys())}"
        )


def _scores_per_categorie(overall_score: float | None) -> CategoryScores:
    """Afgeleide categoriescores; None blijft None (niet beschikbaar is geen nul)."""
    return {
        "taal": overall_score,
        "juridisch": overall_score,
        "structuur": overall_score,
        "samenhang": overall_score,
    }


def create_validation_result(
    overall_score: float | None,
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
    *,
    validation_status: ValidationStatus | None = None,
    unknown_reason: UnknownReason | None = None,
    validation_readiness: ValidationReadinessDict | None = None,
) -> ValidationResult:
    """Create a new schema-compliant ValidationResult.

    DEF-624: alleen een producent die werkelijk een run uitvoerde geeft
    `validation_status=VALIDATION_STATUS_VALIDATED` mee. Zonder status
    verzint de fabriek geen run: het resultaat is dan expliciet
    `validation_unknown` (contract_status_missing), met `is_acceptable`
    False en de fail-closed placeholder als score.

    De status gaat door de centrale statusbepaling (AC 1): None/afwezig wordt
    `validation_unknown` met `contract_status_missing`, een waarde buiten het
    contract ("ok", True, 1, []) wordt `validation_unknown` met
    `contract_status_invalid` - genormaliseerd, geen exception. Alleen
    expliciet meegegeven, tegenstrijdige metadata wordt geweigerd
    (ValueError): een reden bij `validated`, een expliciete
    `validation_unknown` zonder contractuele reden, `ruleset_incomplete`
    zonder (volledige) readiness, een readiness die niet de schemavorm heeft,
    of een reden die de afgeleide reden tegenspreekt. De fabriek verzint
    nooit een reden of een readiness.

    Args:
        overall_score: Overall validation score (0.0-1.0), of None (niet beschikbaar)
        is_acceptable: Whether the validation passed minimum requirements
        violations: List of validation violations (default: empty list)
        passed_rules: List of passed rule IDs (default: empty list)
        detailed_scores: Score breakdown by category (default: derived from overall)
        correlation_id: UUID for tracing (generated if not provided)
        engine_version: Validation engine version
        profile_used: Validation profile name
        duration_ms: Total processing time in milliseconds
        improvement_suggestions: AI-powered improvement suggestions
        acceptance_gate: Acceptance gate evaluation
        validation_status: De runstatus van de producent (validated of
            validation_unknown); None = geen run vastgelegd; een andere
            waarde = ongeldig, wordt genormaliseerd tot validation_unknown.
        unknown_reason: Verplicht bij een expliciete validation_unknown;
            verboden bij validated; moet bij een afgeleide status (None of
            ongeldig) gelijk zijn aan de afgeleide reden.
        validation_readiness: Verplicht bij unknown_reason ruleset_incomplete;
            als meegegeven altijd in de volledige schemavorm.

    Returns:
        Schema-compliant ValidationResult

    Raises:
        ValueError: bij expliciete metadata zonder schemageldige uitvoer.

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
            validation_status=VALIDATION_STATUS_VALIDATED,
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
        detailed_scores = _scores_per_categorie(overall_score)

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

    # Build result. Opbouw als dict[str, Any]; de shape voldoet aan het
    # canonieke TypedDict (strikte lokale deeltypen zijn subtypes daarvan).
    result: dict[str, Any] = {
        "version": CONTRACT_VERSION,
        "overall_score": overall_score,
        "is_acceptable": is_acceptable,
        "violations": violations,
        "passed_rules": passed_rules,
        "detailed_scores": detailed_scores,
        "system": system,
    }
    if validation_status is not None:
        # Ruw meegeven; de centrale statusbepaling (met_expliciete_runstatus)
        # maakt afwezig/ongeldig hierna expliciet validation_unknown.
        result["validation_status"] = validation_status
    _controleer_expliciete_metadata(
        validation_status,
        bepaal_runstatus(result),
        unknown_reason,
        validation_readiness,
    )
    if unknown_reason is not None:
        result["unknown_reason"] = unknown_reason
    if validation_readiness is not None:
        result["validation_readiness"] = validation_readiness

    # Add optional fields
    if improvement_suggestions:
        result["improvement_suggestions"] = improvement_suggestions
    if acceptance_gate:
        result["acceptance_gate"] = acceptance_gate

    return cast("ValidationResult", met_expliciete_runstatus(result))


def _controleer_expliciete_metadata(
    gegeven_status: Any,
    runstatus: Runstatus,
    unknown_reason: str | None,
    validation_readiness: Mapping[str, Any] | None,
) -> None:
    """Weiger expliciete metadata waarvoor het schema geen geldige uitvoer kent.

    De status zelf wordt nooit geweigerd (die is al centraal bepaald); alleen
    wat de aanroeper er tegenstrijdig bij meegeeft.
    """
    if validation_readiness is not None and not is_geldige_readiness(
        validation_readiness
    ):
        msg = (
            "validation_readiness voldoet niet aan het contract: precies de "
            "vijf velden ready, expected_total, loaded_total, missing_rule_ids, "
            "unexpected_rule_ids met de juiste typen"
        )
        raise ValueError(msg)
    if runstatus.uitgevoerd:
        if unknown_reason is not None:
            msg = "validated draagt geen unknown_reason"
            raise ValueError(msg)
        return
    if gegeven_status == VALIDATION_STATUS_UNKNOWN:
        # Expliciete unknown: de producent moet zelf een contractuele reden geven.
        if unknown_reason not in BEKENDE_REDENEN:
            msg = (
                "validation_unknown vereist een contractuele unknown_reason "
                f"({sorted(BEKENDE_REDENEN)}); kreeg {unknown_reason!r}"
            )
            raise ValueError(msg)
        if (
            unknown_reason == UNKNOWN_REASON_RULESET_INCOMPLETE
            and validation_readiness is None
        ):
            msg = "ruleset_incomplete vereist de gemeten validation_readiness"
            raise ValueError(msg)
        return
    # Afgeleide unknown (status None of ongeldig): de reden komt uit de
    # statusbepaling; een afwijkende expliciete reden is tegenstrijdig.
    if unknown_reason is not None and unknown_reason != runstatus.reason:
        msg = (
            f"unknown_reason {unknown_reason!r} spreekt de afgeleide reden "
            f"{runstatus.reason!r} voor validation_status {gegeven_status!r} tegen"
        )
        raise ValueError(msg)


def create_degraded_result(
    error: str,
    correlation_id: str | None = None,
    begrip: str | None = None,
    include_retry_suggestion: bool = True,
) -> ValidationResult:
    """Create a degraded mode result for service errors.

    Used when validation cannot complete normally due to service errors,
    timeouts, or other operational failures. The result is schema-compliant
    but indicates the error condition clearly: een servicefout is geen
    uitgevoerde run, dus `validation_unknown` met reden `validation_error`
    (DEF-624).

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

    result: dict[str, Any] = {
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
    }

    if suggestions:
        result["improvement_suggestions"] = suggestions

    return cast("ValidationResult", result)


def normalize_to_unified(
    result: Any,
    correlation_id: str | None = None,
) -> ValidationResult:
    """Normalize any validation result format to unified ValidationResult.

    This function handles conversion from:
    1. Dict with 'version' and 'system' keys (already schema-compliant)
    2. Dataclass ValidationResult (from services.interfaces)
    3. Legacy dicts without version/system structure

    In alle gevallen draagt de uitvoer een expliciete runstatus (DEF-624):
    zonder geldige `validation_status` in de bron is dat
    `validation_unknown` (contract_status_missing/invalid). De bron wordt
    niet gemuteerd.

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
        uit: dict[str, Any] = {**result}
        system = uit.get("system")
        if not isinstance(system, dict):
            system = {}
        # Ensure correlation_id is set (copy system dict too to avoid mutation)
        if not system.get("correlation_id"):
            uit["system"] = {
                **system,
                "correlation_id": correlation_id or str(uuid.uuid4()),
            }
        # Runtime validation: externe data — verifieer essentiële keys
        # voordat we cast'en, anders crasht downstream code laat.
        _assert_validation_result_keys(uit)
        return cast("ValidationResult", met_expliciete_runstatus(uit))

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


def _score_van(waarde: Any, *, aanwezig: bool) -> float | None:
    """None blijft None; ontbrekend wordt de oude default 0.0."""
    if not aanwezig:
        return 0.0
    if waarde is None:
        return None
    try:
        return float(waarde)
    except (TypeError, ValueError):
        return 0.0


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
            "message": str(message),
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

    # Extract scores: None blijft None (DEF-622)
    if hasattr(result, "score"):
        overall_score = _score_van(result.score, aanwezig=True)
    else:
        overall_score = _score_van(
            getattr(result, "overall_score", None),
            aanwezig=hasattr(result, "overall_score"),
        )

    # Detailed scores
    detailed_scores = getattr(result, "detailed_scores", None)
    if not detailed_scores:
        detailed_scores = _scores_per_categorie(overall_score)

    # Passed rules: alleen wat de bron meldt; geen verzonnen BASIC-00x.
    passed_rules = list(getattr(result, "passed_rules", None) or [])

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

    # Build final result. Zonder totaalscore is er geen drempel (fail-closed).
    if hasattr(result, "is_valid"):
        is_acceptable = bool(result.is_valid)
    elif hasattr(result, "is_acceptable"):
        is_acceptable = bool(result.is_acceptable)
    else:
        is_acceptable = overall_score is not None and overall_score >= 0.5

    unified: dict[str, Any] = {
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

    # DEF-624: contractvelden die de bron werkelijk draagt (ook een
    # ongeldige status of een expliciete lege bronbeoordeling) reizen mee.
    neem_contractvelden_over(unified, result)
    return cast("ValidationResult", met_expliciete_runstatus(unified))


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

    # Extract what we can from the dict; None blijft None (DEF-622)
    if "score" in result:
        overall_score = _score_van(result["score"], aanwezig=True)
    else:
        overall_score = _score_van(
            result.get("overall_score"), aanwezig="overall_score" in result
        )

    if "is_valid" in result:
        is_acceptable = bool(result["is_valid"])
    elif "is_acceptable" in result:
        is_acceptable = bool(result["is_acceptable"])
    else:
        is_acceptable = overall_score is not None and overall_score >= 0.5

    # Convert violations if present
    violations: list[ViolationDict] = []
    raw_violations = result.get("violations", [])
    for v in raw_violations or []:
        if isinstance(v, dict):
            violation: ViolationDict = {
                "code": v.get("code", "VAL-UNK-000"),
                "severity": v.get("severity", "warning"),
                "message": str(
                    v.get("message", v.get("description", "Unknown violation"))
                ),
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
        detailed_scores = _scores_per_categorie(overall_score)

    # Passed rules: alleen wat de bron meldt; geen verzonnen BASIC-00x.
    passed_rules = list(result.get("passed_rules") or [])

    # System metadata
    system: SystemMetadata = {
        "correlation_id": correlation_id,
        "timestamp": result.get("timestamp", datetime.now(UTC).isoformat()),
    }

    unified: dict[str, Any] = {
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

    # DEF-624: zie _convert_dataclass_to_unified.
    neem_contractvelden_over(unified, result)
    return cast("ValidationResult", met_expliciete_runstatus(unified))


# ==============================================================================
# Validation Helpers
# ==============================================================================


def is_valid_result(result: Any) -> bool:
    """Check if a result is a valid schema-compliant ValidationResult.

    Naast de verplichte sleutels en `system.correlation_id` eist de canonieke
    vorm (2.0.0) een geldige `validation_status`, en volgt zij de
    conditionele schema-eisen: `unknown_reason` verplicht (en contractueel)
    bij validation_unknown, verboden bij validated; bij validation_unknown de
    fail-closed placeholders (`is_acceptable` False, `overall_score` 0 of
    None); `validation_readiness` verplicht bij ruleset_incomplete en, zodra
    aanwezig, in de volledige schemavorm. Zo kan deze check niet True zeggen
    waar het schema de status-/unknown-/readinessuitkomst weigert (DEF-624,
    reviewbevinding 2 en deltareview). Lichtgewicht: overige value-types en
    geneste structuren (violations, scores per categorie) blijven buiten scope.

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

    status = result.get("validation_status")
    if status not in (VALIDATION_STATUS_VALIDATED, VALIDATION_STATUS_UNKNOWN):
        return False
    # Dezelfde conditionele eisen als het schema (allOf): een reden alleen
    # en verplicht bij unknown, de fail-closed placeholders bij unknown
    # (is_acceptable false, overall_score 0 of null), readiness verplicht
    # bij ruleset_incomplete en - zodra aanwezig - altijd in de schemavorm.
    reden = result.get("unknown_reason")
    if status == VALIDATION_STATUS_VALIDATED and "unknown_reason" in result:
        return False
    if status == VALIDATION_STATUS_UNKNOWN:
        if reden not in BEKENDE_REDENEN:
            return False
        if result.get("is_acceptable") is not False:
            return False
        if not _is_unknown_placeholder(result.get("overall_score")):
            return False
        if (
            reden == UNKNOWN_REASON_RULESET_INCOMPLETE
            and "validation_readiness" not in result
        ):
            return False
    if "validation_readiness" in result and not is_geldige_readiness(
        result["validation_readiness"]
    ):
        return False

    # Check system has correlation_id
    system = result.get("system", {})
    return isinstance(system, dict) and "correlation_id" in system


def _is_unknown_placeholder(score: Any) -> bool:
    """Schema bij validation_unknown: overall_score is 0 (geen bool) of null."""
    if score is None:
        return True
    return isinstance(score, int | float) and not isinstance(score, bool) and score == 0


def get_blocking_violations(result: ValidationResult) -> list[ViolationDict]:
    """Get violations that block acceptance (severity: error).

    Args:
        result: ValidationResult to inspect

    Returns:
        List of error-severity violations
    """
    return [
        cast("ViolationDict", v)
        for v in result.get("violations", [])
        if v.get("severity") == "error"
    ]


def get_category_score(
    result: ValidationResult, category: CategoryType
) -> float | None:
    """Get the score for a specific category.

    Args:
        result: ValidationResult to inspect
        category: Category to get score for

    Returns:
        Score for the category (0.0-1.0), of None wanneer niet beschikbaar;
        defaults to overall_score if the category is not found.
    """
    scores = result.get("detailed_scores", {})
    if category in scores:
        return scores[category]
    return result.get("overall_score", 0.0)


def is_uitgevoerde_run(result: Any) -> bool:
    """Alleen een expliciete `validated` is een uitgevoerde run (DEF-624)."""
    return bepaal_runstatus(result).uitgevoerd


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
    "is_uitgevoerde_run",
    "is_valid_result",
    "normalize_to_unified",
]
