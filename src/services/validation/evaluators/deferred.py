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
    # DEF-667/DEF-669: `abbreviation` en `definition_grammar` stonden in
    # `EvaluatorType` en in de root-SSOT zonder registratie. Vandaag declareert
    # geen enkel record ze, maar "toegestaan zonder registratie" is precies het
    # gat dat het register moet dichten: een record dat er één noemt passeert
    # alle contractvalidatie en klapt pas per evaluatie om in ERROR, waarna de
    # regel via de dekking uit de noemer valt. Ze staan hier expliciet als
    # uitgesteld, met eigenaar-issue, in plaats van als stille leegte.
    DeferredEvaluator(
        EvaluatorType.ABBREVIATION,
        "DEF-624",
        "INT-07 vraagt een afkortingstoets die de correcte uitschrijving niet "
        "meer afkeurt",
    ),
    DeferredEvaluator(
        EvaluatorType.DEFINITION_GRAMMAR,
        "DEF-624",
        "De STR-01-body-check op de tekst ná de dubbele punt is nog niet "
        "geïmplementeerd",
    ),
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
    # DEF-674: `DUPLICATE_DETECTION` stond hier als uitgesteld terwijl de
    # controle in werkelijkheid al draaide — in `context_metadata` (CON-01).
    # Zij is nu verhuisd naar `DuplicateDetectionEvaluator`, de plek die de
    # records zelf aanwijzen, en dus geen uitgestelde evaluator meer.
)
