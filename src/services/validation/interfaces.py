"""ValidationOrchestratorV2 Interface Definition

Definieert het contract voor alle ValidationOrchestrator implementaties met:
- Async-first design met expliciete domeinvelden
- Schema-first approach met TypedDict binding
- Privacy-bewuste context handling zonder PII
- Degraded error handling (geen exceptions, wel ValidationResult)
"""

from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any, Literal, NotRequired
from uuid import UUID

from typing_extensions import TypedDict

from services.interfaces import Definition

# Contract version voor schema compliance.
#
# 1.1.0 (DEF-624): additief uitgebreid met rule_statuses,
# evaluation_coverage en review_required. SemVer-minor, want bestaande
# consumers blijven werken: er is geen veld verdwenen of van betekenis
# veranderd. De pinned validation_result_v1.0.0.schema.json blijft als
# historisch schema staan.
#
# 1.2.0 (DEF-621): additief uitgebreid met validation_status, unknown_reason
# en validation_readiness. Ook dit is een SemVer-minor: geen veld is
# verdwenen of van betekenis veranderd. Zie de conditionele constraint in
# het JSON-schema - bij validation_unknown zijn overall_score en
# is_acceptable uitsluitend fail-closed placeholders.
CONTRACT_VERSION = "1.2.0"

# DEF-621: de uitkomst van een validatie als geheel.
#
# "validated"          - er is werkelijk geevalueerd; overall_score en
#                        is_acceptable dragen een inhoudelijk oordeel.
# "validation_unknown" - de regelset dekt het contract niet, dus er is niet
#                        geevalueerd. Dit is technisch niet betrouwbaar te
#                        bepalen, niet inhoudelijk invalid.
VALIDATION_STATUS_VALIDATED = "validated"
VALIDATION_STATUS_UNKNOWN = "validation_unknown"
ValidationStatus = Literal["validated", "validation_unknown"]

# Machineleesbare reden bij validation_unknown. Bewust een enkele waarde:
# een consumer moet erop kunnen matchen. De onderliggende oorzaak
# (ontbrekende regelbestanden, onleesbare root-SSOT, mislukte lader) hoort
# in het log.
UNKNOWN_REASON_RULESET_INCOMPLETE = "ruleset_incomplete"
UnknownReason = Literal["ruleset_incomplete"]

# Uitkomst van één regelevaluatie. Alleen "pass" en "fail" zijn werkelijk
# uitgevoerde, betrouwbare beoordelingen; uitsluitend die twee beïnvloeden
# overall_score. Spiegelt toetsregels.runtime_contract.ResultStatus.
RuleResultStatus = Literal["pass", "fail", "review_required", "not_evaluated", "error"]


class ValidationResult(TypedDict, total=False):
    """ValidationResult contract gebonden aan JSON Schema.

    Alle verplichte velden conform validation_result.schema.json.
    Gebruikt TypedDict voor compile-time type safety zonder runtime overhead.
    """

    # Required fields
    version: str
    overall_score: float  # 0.0-1.0
    is_acceptable: bool
    violations: list["RuleViolation"]
    passed_rules: list[str]
    detailed_scores: dict[str, float]  # category -> score
    system: "SystemMetadata"

    # Optional fields
    improvement_suggestions: NotRequired[list["ImprovementSuggestion"]]

    # Stond al in het JSON-schema maar niet in dit TypedDict; meegenomen
    # zodat schema en binding weer sluiten.
    acceptance_gate: NotRequired["AcceptanceGate"]

    # DEF-624: score en dekking zijn twee getallen, geen één.
    rule_statuses: NotRequired[dict[str, RuleResultStatus]]
    evaluation_coverage: NotRequired["EvaluationCoverage"]
    review_required: NotRequired[list["ReviewRequirement"]]

    # DEF-621: bij validation_unknown is er niet geevalueerd.
    # overall_score en is_acceptable blijven aanwezig voor
    # compatibiliteit, maar zijn dan uitsluitend fail-closed
    # placeholders (0.0 respectievelijk False) en geen kwaliteitsoordeel.
    validation_status: NotRequired[ValidationStatus]
    unknown_reason: NotRequired[UnknownReason]
    validation_readiness: NotRequired["ValidationReadinessDict"]


class ValidationReadinessDict(TypedDict, total=False):
    """Waarom de regelset het contract wel of niet dekt (DEF-621).

    `expected_total` is het aantal ID-s uit de contractuele set, niet het
    aantal bestanden op schijf: die twee liepen juist uiteen.
    """

    ready: bool
    expected_total: int
    loaded_total: int
    missing_rule_ids: list[str]
    unexpected_rule_ids: list[str]


class AcceptanceGate(TypedDict, total=False):
    """Uitkomst van de vaststelgate."""

    status: NotRequired[str]  # "pass" | "blocked" | "override_required"
    acceptable: NotRequired[bool]
    gates_passed: NotRequired[list[str]]
    gates_failed: NotRequired[list[str]]
    reasons: NotRequired[list[str]]
    thresholds: NotRequired[dict[str, float]]


class EvaluationCoverage(TypedDict):
    """Hoeveel regels werkelijk zijn beoordeeld, naast de kwaliteitsscore.

    Zonder dit blok kan een lagere dekking als hogere kwaliteit verschijnen:
    regels die niet zijn uitgevoerd vallen uit de scoreberekening en zouden
    anders onzichtbaar blijven.
    """

    evaluated: int  # pass + fail
    passed: int
    failed: int
    review_required: int
    not_evaluated: int
    error: int
    total: int
    coverage_ratio: float  # evaluated / total


class ReviewRequirement(TypedDict):
    """Een regel die menselijk oordeel vraagt.

    Bewust geen violation: reviewplicht is geen kwaliteitsprobleem en telt
    ook niet als pass. De signalen wijzen de reviewer waar te kijken; het
    zijn aanwijzingen, geen bewijs.
    """

    rule_id: str
    category: str
    reason: str
    signals: list[str]


class RuleViolation(TypedDict, total=False):
    """Validation rule violation met standaard error codes."""

    code: str  # Pattern: ^[A-Z]{3}-[A-Z]{3}-\d{3}$
    severity: str  # "info" | "warning" | "error"
    message: str
    rule_id: str
    category: str  # "taal" | "juridisch" | "structuur" | "samenhang" | "system"
    location: NotRequired["ViolationLocation"]
    suggestions: NotRequired[list[str]]
    metadata: NotRequired[dict[str, Any]]


class ViolationLocation(TypedDict, total=False):
    """Locatie van violation in tekst."""

    text_span: NotRequired["TextSpan"]
    indices: NotRequired[list[int]]
    line: NotRequired[int]  # 1-based
    column: NotRequired[int]  # 1-based


class TextSpan(TypedDict):
    """Text span met start/end indices."""

    start: int  # 0-based character index
    end: int  # 0-based character index


class ImprovementSuggestion(TypedDict, total=False):
    """AI-powered improvement suggestion."""

    type: str  # "rewrite" | "addition" | "removal" | "restructure"
    description: str
    example: NotRequired[str]
    impact: NotRequired[str]  # "low" | "medium" | "high"


class SystemMetadata(TypedDict, total=False):
    """System metadata met verplichte correlation_id."""

    correlation_id: str  # UUID format, required per schema
    engine_version: NotRequired[str]
    profile_used: NotRequired[str]
    timestamp: NotRequired[str]  # ISO 8601
    duration_ms: NotRequired[int]
    timings: NotRequired["ProcessingTimings"]
    error: NotRequired[str]  # Voor degraded results


class ProcessingTimings(TypedDict, total=False):
    """Gedetailleerde timing breakdown."""

    cleaning_ms: NotRequired[int]
    validation_ms: NotRequired[int]
    enhancement_ms: NotRequired[int]


@dataclass(frozen=True)
class ValidationContext:
    """Validation context zonder PII.

    Privacy-bewust: geen user_id/email. Extra metadata via feature_flags
    of gecontroleerde metadata mapping indien noodzakelijk.
    """

    correlation_id: UUID | None = None
    profile: str | None = None
    locale: str | None = None
    trace_parent: str | None = None
    feature_flags: Mapping[str, bool] | None = None
    metadata: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class ValidationRequest:
    """Immutable validation request met expliciete domeinvelden."""

    begrip: str
    text: str
    ontologische_categorie: str | None = None
    context: ValidationContext | None = None


class ValidationOrchestratorInterface(ABC):
    """Interface voor alle ValidationOrchestrator implementaties.

    Error Handling Policy:
    - Operationele fouten (timeout, service down) → ValidationResult met SYS-* code
    - GEEN exceptions voor business logic failures
    - Input validation failures → VAL-* codes in violations
    - System errors → system.error field gevuld

    Contract Garanties:
    - Alle responses 100% conform validation_result.schema.json
    - system.correlation_id altijd UUID (gegenereerd indien ontbreekt)
    - version altijd CONTRACT_VERSION
    """

    @abstractmethod
    async def validate_text(
        self,
        begrip: str,
        text: str,
        ontologische_categorie: str | None = None,
        context: ValidationContext | None = None,
    ) -> ValidationResult:
        """Valideer tekst tegen validatieregels.

        Args:
            begrip: Het begrip waarvoor de tekst wordt gevalideerd
            text: Te valideren tekst (mag leeg zijn)
            ontologische_categorie: Optionele categorie voor contextuele regels
            context: Optionele validatiecontext

        Returns:
            ValidationResult: Schema-conform resultaat

        Note:
            - Lege tekst resulteert in is_acceptable=False met passende violation
            - Bij ontbrekende context wordt correlation_id gegenereerd
            - Operationele fouten → degraded result, GEEN exception
        """
        ...

    @abstractmethod
    async def validate_definition(
        self,
        definition: Definition,
        context: ValidationContext | None = None,
    ) -> ValidationResult:
        """Valideer volledige definitie.

        Args:
            definition: Te valideren Definition object
            context: Optionele validatiecontext

        Returns:
            ValidationResult: Schema-conform resultaat met detailed_scores

        Note:
            - Alle categorie scores (taal, juridisch, structuur, samenhang) ingevuld
            - improvement_suggestions toegevoegd indien beschikbaar
        """
        ...

    @abstractmethod
    async def batch_validate(
        self,
        items: Iterable[ValidationRequest],
        max_concurrency: int = 1,
    ) -> list[ValidationResult]:
        """Batch validatie van meerdere items.

        Args:
            items: Itereerbare van ValidationRequest objects
            max_concurrency: Maximum parallelle validaties (default: sequentieel)

        Returns:
            List[ValidationResult]: Resultaten in zelfde volgorde als input

        Note:
            - Lengte output == lengte input
            - Individuele failures → degraded result, niet hele batch failure
            - max_concurrency=1 voor sequentiële verwerking
        """
        ...
