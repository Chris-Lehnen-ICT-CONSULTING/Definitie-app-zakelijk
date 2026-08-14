"""Evaluatorcontract voor de JSON-toetsregels (DEF-606 / ADR-001).

Eén protocol, één uitkomsttype. Iedere evaluator krijgt een gevalideerd
`RuleRecord` plus de `EvaluationContext` en geeft een `EvaluationOutcome`
terug die zonder adapterverlies in het bestaande `RuleResult`/violation-
formaat past.

De uitkomst draagt expliciet een `ResultStatus`. Alleen `PASS` en `FAIL`
zijn werkelijk uitgevoerde beoordelingen; `REVIEW_REQUIRED`,
`NOT_EVALUATED` en `ERROR` mogen nooit als pass worden genormaliseerd.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from services.validation.types_internal import EvaluationContext
from services.validation.violation_builder import category_for_rule
from toetsregels.runtime_contract import (
    EvaluatorType,
    RequiredInput,
    ResultStatus,
    RuleRecord,
)

__all__ = [
    "EvaluationDeps",
    "EvaluationOutcome",
    "EvaluationSupport",
    "Finding",
    "RuleEvaluator",
    "bouw_violation",
    "falende_uitkomst",
]


@dataclass(frozen=True)
class Finding:
    """Eén geconstateerd probleem binnen een regelevaluatie.

    `reason` is de sleutel waarmee de service een concrete NL-suggestie
    opbouwt; `details` levert de variabele invulling daarvan.
    """

    message: str
    reason: str
    details: str | None = None


@dataclass(frozen=True)
class EvaluationOutcome:
    """Uitkomst van één regelevaluatie."""

    status: ResultStatus
    score: float | None = None
    findings: tuple[Finding, ...] = ()
    pattern_hits: tuple[str, ...] = ()
    first_hit_pattern: str | None = None
    first_hit_pos: int | None = None
    violation: dict[str, Any] | None = None
    reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def passed(cls) -> EvaluationOutcome:
        return cls(status=ResultStatus.PASS, score=1.0)

    @classmethod
    def not_evaluated(cls, reason: str) -> EvaluationOutcome:
        return cls(status=ResultStatus.NOT_EVALUATED, reason=reason)

    @classmethod
    def review_required(
        cls, reason: str, *, signals: tuple[str, ...] = ()
    ) -> EvaluationOutcome:
        return cls(
            status=ResultStatus.REVIEW_REQUIRED,
            reason=reason,
            metadata={"signals": list(signals)} if signals else {},
        )


@runtime_checkable
class EvaluationSupport(Protocol):
    """De weinige diensten die evaluators van de orchestrator lenen.

    Bewust smal gehouden: severity-afleiding en suggestieopbouw blijven bij
    de service, zodat het violation-formaat op één plek wordt bepaald en er
    geen brede god-objectrefactor (DEF-424) nodig is om dit contract te
    kunnen invoeren.
    """

    def severity_for(self, rule: dict[str, Any]) -> str: ...

    def severity_level_for(self, rule: dict[str, Any]) -> str: ...

    def build_suggestion(
        self,
        code: str,
        rule: dict[str, Any] | None,
        text: str,
        ctx: EvaluationContext,
        *,
        reason: str,
        details: str | None = None,
    ) -> str: ...


@dataclass(frozen=True)
class EvaluationDeps:
    """Runtime-invoer die niet uit het regelrecord of de tekst komt."""

    support: EvaluationSupport
    available_inputs: frozenset[RequiredInput]
    repository: Any | None = None
    pattern_cache: dict[str, Any] = field(default_factory=dict)

    def has(self, vereist: RequiredInput) -> bool:
        return vereist in self.available_inputs


class RuleEvaluator(Protocol):
    """Iedere evaluatorstrategie implementeert precies dit contract.

    Structureel, niet nominaal: evaluators erven van niets en hoeven alleen
    `evaluator_type` en `evaluate` te bieden. Het register controleert bij
    registratie of `evaluator_type` werkelijk een `EvaluatorType` is, zodat
    een verkeerd gevormde evaluator niet stil geregistreerd raakt.
    """

    @property
    def evaluator_type(self) -> EvaluatorType: ...

    def evaluate(
        self, record: RuleRecord, ctx: EvaluationContext, deps: EvaluationDeps
    ) -> EvaluationOutcome: ...


def bouw_violation(
    record: RuleRecord,
    deps: EvaluationDeps,
    *,
    melding: str,
    suggestie: str | None,
    beschrijving: str | None = None,
    metadata: dict[str, Any] | None = None,
    severity: str | None = None,
    severity_level: str | None = None,
) -> dict[str, Any]:
    """De enige plek waar een evaluator zijn eigen violation-dict vormt.

    Vier evaluators bouwden die dict eerder met de hand, en dus verschillend:
    `compound` en `qualification` leverden géén `severity_level`,
    `ontological_category` hardcodeerde `"high"` en `lemma_morphology` leidde
    hem af uit het record. Een consumer die op `severity_level` filtert kreeg
    voor SAM-02 en SAM-04 niets terug (DEF-669).

    Severity en severity_level komen standaard uit het regelrecord, via
    dezelfde afleiding die de service voor de bevindingen-route gebruikt. Zo
    is de vorm van een violation onafhankelijk van welke evaluator hem maakte.

    `severity`/`severity_level` zijn een expliciete override voor het enige
    geval waarin de ernst niet uit het record volgt maar uit de invoer: een
    duplicaat weegt zwaarder wanneer de gebruiker het bewust forceert
    (DEF-674). De override is opzettelijk zichtbaar in de aanroep, zodat een
    afwijking niet stil in een evaluator kan ontstaan.
    """
    rule = dict(record.data)
    code = record.rule_id.upper()
    violation: dict[str, Any] = {
        "code": code,
        "severity": severity or deps.support.severity_for(rule),
        "severity_level": severity_level or deps.support.severity_level_for(rule),
        "message": melding,
        "description": beschrijving or melding,
        "rule_id": code,
        "category": category_for_rule(code),
        "suggestion": suggestie,
    }
    if metadata:
        violation["metadata"] = dict(metadata)
    return violation


def falende_uitkomst(
    record: RuleRecord,
    deps: EvaluationDeps,
    *,
    melding: str,
    suggestie: str | None,
    beschrijving: str | None = None,
    metadata: dict[str, Any] | None = None,
    severity: str | None = None,
    severity_level: str | None = None,
) -> EvaluationOutcome:
    """Eén FAIL-uitkomst met violation, in één vorm (DEF-669)."""
    return EvaluationOutcome(
        status=ResultStatus.FAIL,
        score=0.0,
        violation=bouw_violation(
            record,
            deps,
            melding=melding,
            suggestie=suggestie,
            beschrijving=beschrijving,
            metadata=metadata,
            severity=severity,
            severity_level=severity_level,
        ),
    )
