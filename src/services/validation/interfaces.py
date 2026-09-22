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
from typing import Any, Final, Literal, NotRequired, Required
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
#
# 1.3.0 (DEF-622): additief uitgebreid met rule_results (gestructureerde
# deeluitkomsten van regels zonder cijfer, CON-01). overall_score en de
# categoriescores kunnen nu None zijn: de totaalscore is niet beschikbaar
# zolang een regel met score_policy no_score in de geevalueerde set zit
# (productbesluit: geen noemer zonder CON-01). Bestaande consumers moeten
# None aankunnen; geen enkel veld is verdwenen.
#
# 1.4.0 (DEF-743): additief uitgebreid met source_assessment — de volledige
# AI-bronbeoordeling (CON-02) die de async wrapper voor exact deze validatie
# heeft verkregen, of null wanneer er geen AI-beoordeling was (geen bronnen).
# Zo kan een aanroeper haar bewaren zonder tweede modelaanroep. SemVer-minor:
# geen veld is verdwenen of van betekenis veranderd.
#
# 2.0.0 (DEF-624): de betekenis van een AFWEZIGE validation_status is
# veranderd, en dat is een SemVer-major. Tot 1.4.0 declareerde het schema
# `default: validated`: een resultaat zonder status gold als uitgevoerde run.
# Vanaf 2.0.0 is validation_status verplicht in de canonieke uitvoervorm en
# geldt aan de invoergrens (dict, legacy object, fabriek): afwezig, null of
# ongeldig = validation_unknown met een concrete contractreden
# (contract_status_missing / contract_status_invalid). Legacy-invoer blijft
# leesbaar - zij wordt genormaliseerd, niet afgewezen - maar levert nooit
# meer een oordeel op. Een servicefout (degraded) is eveneens expliciet
# validation_unknown (validation_error). Geen veld is verdwenen; het vorige
# contract blijft gepind als validation_result_v1.4.0.schema.json. Dit
# nummer vervangt tevens de niet-canonieke "2.0.0" die services.validation.
# types eerder los van dit bestand voerde; types importeert de versie nu
# vanaf hier.
#
# 2.1.0 (DEF-766): additief uitgebreid met de resultaatstatus `not_applicable`
# (rule_statuses, rule_results, evaluation_coverage.not_applicable) — een
# afgeronde, gemotiveerde niet-toepasselijkheid (ESS-03: geen telbare eenheid
# bedoeld), geen pass en geen open punt — en met `ess03_assessment`: de
# volledige AI-telbaarheidsbeoordeling die de async wrapper voor exact deze
# validatie heeft verkregen (contract domain.ess03.contract), of null. Geen
# bestaande status of veld is van betekenis veranderd: SemVer-minor.
CONTRACT_VERSION = "2.1.0"

# DEF-621: de uitkomst van een validatie als geheel.
#
# "validated"          - er is werkelijk geevalueerd; overall_score en
#                        is_acceptable dragen een inhoudelijk oordeel. Alleen
#                        een producent die werkelijk een run uitvoerde zet
#                        deze waarde; een conversie verzint nooit een run.
# "validation_unknown" - er is geen betrouwbaar uitgevoerde run: de regelset
#                        dekt het contract niet, de status ontbreekt of is
#                        ongeldig, of de service faalde. Dit is technisch
#                        niet te bepalen, niet inhoudelijk invalid.
VALIDATION_STATUS_VALIDATED: Final = "validated"
VALIDATION_STATUS_UNKNOWN: Final = "validation_unknown"
ValidationStatus = Literal["validated", "validation_unknown"]

# Machineleesbare reden bij validation_unknown. Een consumer moet erop
# kunnen matchen; de onderliggende oorzaak (ontbrekende regelbestanden,
# onleesbare root-SSOT, mislukte lader, de exacte exceptie) hoort in het log.
#
# ruleset_incomplete       - de geladen regelset dekt het contract niet
#                            (DEF-621); validation_readiness is dan aanwezig.
# contract_status_missing  - het resultaat droeg geen (of null) status; er is
#                            geen run vastgelegd (DEF-624). Geen readiness:
#                            die is niet gemeten en wordt niet verzonnen.
# contract_status_invalid  - het resultaat droeg een waarde buiten het
#                            contract (DEF-624).
# validation_error         - de validatieservice faalde; degraded result.
UNKNOWN_REASON_RULESET_INCOMPLETE: Final = "ruleset_incomplete"
UNKNOWN_REASON_CONTRACT_STATUS_MISSING: Final = "contract_status_missing"
UNKNOWN_REASON_CONTRACT_STATUS_INVALID: Final = "contract_status_invalid"
UNKNOWN_REASON_VALIDATION_ERROR: Final = "validation_error"
UnknownReason = Literal[
    "ruleset_incomplete",
    "contract_status_missing",
    "contract_status_invalid",
    "validation_error",
]

# Uitkomst van één regelevaluatie. Alleen "pass" en "fail" zijn werkelijk
# uitgevoerde, betrouwbare beoordelingen; uitsluitend die twee beïnvloeden
# overall_score. "not_applicable" (DEF-766, contract 2.1.0) is een afgeronde,
# gemotiveerde niet-toepasselijkheid — geen pass, geen open punt. Spiegelt
# toetsregels.runtime_contract.ResultStatus.
RuleResultStatus = Literal[
    "pass", "fail", "review_required", "not_evaluated", "error", "not_applicable"
]


class ValidationResult(TypedDict, total=False):
    """ValidationResult contract gebonden aan JSON Schema.

    Alle verplichte velden conform validation_result.schema.json staan als
    `Required[...]` gemarkeerd (DEF-624): `ValidationResult.__required_keys__`
    is exact de `required`-lijst van het schema, zodat de binding geen
    ontbrekend verplicht veld accepteert dat het schema weigert. De overige
    velden zijn optioneel (`total=False`). Legacy-invoer zonder deze velden
    wordt niet hier maar aan de conversiegrens (mappers/types/adapter)
    genormaliseerd. Gebruikt TypedDict voor compile-time type safety zonder
    runtime overhead.
    """

    # Required fields
    version: Required[str]
    # 0.0-1.0, of None wanneer de totaalscore niet beschikbaar is (DEF-622).
    overall_score: Required[float | None]
    is_acceptable: Required[bool]
    violations: Required[list["RuleViolation"]]
    passed_rules: Required[list[str]]
    # category -> score (of None)
    detailed_scores: Required[dict[str, float | None]]
    system: Required["SystemMetadata"]
    # DEF-624 (2.0.0): verplicht in de canonieke uitvoervorm. Bij
    # validation_unknown is er niet (betrouwbaar) geevalueerd; overall_score
    # en is_acceptable zijn dan uitsluitend fail-closed placeholders (0.0 of
    # None respectievelijk False) en geen kwaliteitsoordeel. Aan de
    # invoergrens wordt een afwezige, null of ongeldige status door
    # services.validation.result_contract tot validation_unknown gemaakt.
    validation_status: Required[ValidationStatus]

    # Optional fields
    improvement_suggestions: NotRequired[list["ImprovementSuggestion"]]

    # Stond al in het JSON-schema maar niet in dit TypedDict; meegenomen
    # zodat schema en binding weer sluiten.
    acceptance_gate: NotRequired["AcceptanceGate"]

    # DEF-624: score en dekking zijn twee getallen, geen één.
    rule_statuses: NotRequired[dict[str, RuleResultStatus]]
    evaluation_coverage: NotRequired["EvaluationCoverage"]
    review_required: NotRequired[list["ReviewRequirement"]]

    # DEF-622: gestructureerde uitkomst per regel zonder cijfer (CON-01).
    rule_results: NotRequired[dict[str, "RuleResult"]]

    # DEF-743: de volledige AI-bronbeoordeling (CON-02) die de wrapper voor
    # deze validatie heeft verkregen (store-ready, zie
    # domain.sources.contract), of None zonder AI-beoordeling.
    source_assessment: NotRequired[dict[str, Any] | None]

    # DEF-766 (2.1.0): de volledige AI-telbaarheidsbeoordeling (ESS-03) die de
    # wrapper voor deze validatie heeft verkregen (store-ready, zie
    # domain.ess03.contract), of None zonder beoordeling (geen term/tekst).
    ess03_assessment: NotRequired[dict[str, Any] | None]

    # DEF-621/DEF-624: verplicht bij validation_unknown; validation_readiness
    # alleen bij unknown_reason ruleset_incomplete (de enige reden waarbij
    # werkelijk een readiness is gemeten).
    unknown_reason: NotRequired[UnknownReason]
    validation_readiness: NotRequired["ValidationReadinessDict"]


class ValidationReadinessDict(TypedDict):
    """Waarom de regelset het contract wel of niet dekt (DEF-621).

    `expected_total` is het aantal ID-s uit de contractuele set, niet het
    aantal bestanden op schijf: die twee liepen juist uiteen.

    Alle vijf velden zijn verplicht (`total=True`): het object is optioneel
    op het resultaat, maar zodra het aanwezig is, is het volledig. Een half
    ingevulde readiness zou dezelfde onduidelijkheid geven als de telling
    die deze uitbreiding juist vervangt.
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
    # DEF-766 (2.1.0, additief): afgeronde niet-toepasselijkheid, apart van
    # pass/fail, open en niet-uitgevoerd. Optioneel voor oudere resultaten.
    not_applicable: NotRequired[int]


class RuleResultPart(TypedDict):
    """Eén zichtbare deelcontrole van een regel zonder cijfer (DEF-622, B-08).

    `evidence` is de werkelijk gevonden tekst; `context_value` de geselecteerde
    contextwaarde, apart bewaard omdat de schrijfwijze kan verschillen.
    `reason` en `action` zijn de gebruikersuitleg: waarom dit niet voldoet of
    nog open staat, en wat de gebruiker kan doen.
    """

    id: str
    status: Literal["pass", "fail", "review_required", "error", "not_applicable"]
    evidence: str | None
    context_value: str | None
    field: str | None
    position: int | None
    reason: str
    action: str


class RuleResult(TypedDict):
    """Gestructureerde uitkomst van een regel zonder cijfer (DEF-622, B-06).

    `score` is bewust altijd None. `fingerprint` bindt een menselijke
    beoordeling aan term, exacte tekst, canonieke context en contractversie;
    verandert daar iets, dan geldt de eerdere beoordeling niet meer.
    """

    status: RuleResultStatus
    score: None
    contract_version: str | None
    fingerprint: str | None
    parts: list[RuleResultPart]
    review: dict[str, Any] | None


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

    correlation_id: Required[str]  # UUID format, required per schema
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
