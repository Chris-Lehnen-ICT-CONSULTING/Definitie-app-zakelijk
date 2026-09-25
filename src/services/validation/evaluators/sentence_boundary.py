"""INT-01-evaluator: zinsgrenzen als deelbevinding (DEF-770).

De segmentatie en de gestructureerde deeluitkomst staan in
`domain.int01.zinsgrenzen`; zie daar de norm en de uitzonderingen. Eén
vastgestelde zin is een deelbevinding: de regel wordt nooit stil `pass`
maar `fail` (zekere tweede zin) of `review_required` (één zin of onzekere
grens), met de onderdelen in `metadata["rule_result"]`. Geen cijfer en geen
automatische tekstwijziging.
"""

from __future__ import annotations

from domain.int01.opslag import tekstvingerafdruk
from domain.int01.zinsgrenzen import (
    CONTRACTVERSIE,
    REDEN_MEERDERE_ZINNEN,
    SUGGESTIE_MEERDERE_ZINNEN,
    Segmentatie,
    Zinsgrens,
    melding_meerdere_zinnen,
    open_melding,
    regeluitkomst,
    segmenteer,
)
from services.validation.evaluators.base import (
    EvaluationDeps,
    EvaluationOutcome,
    Finding,
)
from services.validation.types_internal import EvaluationContext
from toetsregels.runtime_contract import EvaluatorType, ResultStatus, RuleRecord

__all__ = [
    "CONTRACTVERSIE",
    "REDEN_MEERDERE_ZINNEN",
    "SUGGESTIE_MEERDERE_ZINNEN",
    "Segmentatie",
    "SentenceBoundaryEvaluator",
    "Zinsgrens",
    "segmenteer",
]


class SentenceBoundaryEvaluator:
    """INT-01: zinsgrenzen als deelbevinding; compactheid en begrijpelijkheid open."""

    evaluator_type = EvaluatorType.SENTENCE_BOUNDARY

    def evaluate(
        self, record: RuleRecord, ctx: EvaluationContext, deps: EvaluationDeps
    ) -> EvaluationOutcome:
        seg = segmenteer(ctx.cleaned_text or "")
        if seg is None:
            return EvaluationOutcome.not_evaluated(
                "geen definitietekst; INT-01 niet beoordeelbaar"
            )
        # DEF-770: de uitkomst draagt de vingerafdruk van exact de getoetste
        # tekst (contractveld `fingerprint`); een weergave bij een andere
        # tekst kan haar zo nooit stil als actueel tonen.
        detail = dict(
            regeluitkomst(seg),
            fingerprint=tekstvingerafdruk((ctx.raw_text or "").strip()),
        )
        if seg.zekere_grenzen:
            eerste = seg.zekere_grenzen[0]
            return EvaluationOutcome(
                status=ResultStatus.FAIL,
                findings=(
                    Finding(
                        message=melding_meerdere_zinnen(seg),
                        reason=REDEN_MEERDERE_ZINNEN,
                        details=eerste.passage,
                    ),
                ),
                first_hit_pos=eerste.positie,
                metadata={"rule_result": detail},
            )
        return EvaluationOutcome(
            status=ResultStatus.REVIEW_REQUIRED,
            reason=open_melding(seg),
            metadata={"rule_result": detail},
        )
