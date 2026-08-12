"""Nog niet geïmplementeerde evaluatorstrategieën (DEF-606).

Deze strategieën hebben een gevalideerd contract maar nog geen werkende
implementatie: hun regels vragen repositorydata of een voorkeursterm-
contract dat pas in DEF-623/DEF-624 landt.

Het alternatief — de regel voorlopig laten passeren — is precies de stille
default-pass die ADR-001 verbiedt: die 1,0 zou de kwaliteitsscore optillen
zonder dat er iets is gemeten. Daarom levert deze evaluator expliciet
`not_evaluated` met een reden en het eigenaar-issue. De regelrecords
declareren dat ook zo (`automation_status: not_evaluated`,
`score_policy: excluded_from_score`), zodat contract en runtime hetzelfde
zeggen en de evaluatiedekking het gat zichtbaar maakt.

Zodra de echte evaluator er is, vervangt die de registratie hier en gaat
het record terug naar `automated`/`scored`.
"""

from __future__ import annotations

from dataclasses import dataclass

from services.validation.evaluators.base import (
    EvaluationDeps,
    EvaluationOutcome,
)
from services.validation.types_internal import EvaluationContext
from toetsregels.runtime_contract import EvaluatorType, RuleRecord

__all__ = ["DEFERRED_EVALUATORS", "DeferredEvaluator"]


@dataclass(frozen=True)
class DeferredEvaluator:
    """Levert altijd `not_evaluated` met een traceerbare reden."""

    evaluator_type: EvaluatorType
    issue: str
    toelichting: str

    def evaluate(
        self, record: RuleRecord, ctx: EvaluationContext, deps: EvaluationDeps
    ) -> EvaluationOutcome:
        return EvaluationOutcome.not_evaluated(
            f"{self.toelichting} — implementatie belegd bij {self.issue}"
        )


DEFERRED_EVALUATORS: tuple[DeferredEvaluator, ...] = (
    DeferredEvaluator(
        EvaluatorType.DEFINITION_OVERLAP,
        "DEF-623",
        "Overlap met andere definitieteksten vereist de begrippenverzameling",
    ),
    DeferredEvaluator(
        EvaluatorType.DEFINITION_GRAPH,
        "DEF-623",
        "Cyclusdetectie vereist de begrippenverzameling",
    ),
    DeferredEvaluator(
        EvaluatorType.PREFERRED_TERM,
        "DEF-623",
        "Voorkeurstermcontrole vereist het synoniemen-/voorkeurstermcontract",
    ),
    DeferredEvaluator(
        EvaluatorType.SYNONYM_CONSISTENCY,
        "DEF-624",
        "Één definitie per synoniemenpaar vereist de begrippenverzameling",
    ),
    DeferredEvaluator(
        EvaluatorType.DUPLICATE_DETECTION,
        "DEF-624",
        "Duplicaatdetectie vereist de begrippenverzameling",
    ),
)
