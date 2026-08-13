"""SAM-04 — samenstelling start met het specialiserende component (DEF-606).

Overgenomen uit `ModularValidationService._evaluate_json_rule`. De huidige
heuristiek eist dat het eerste woord ná `':'` een substring van het begrip
is; die aanname wordt in DEF-623 vervangen door een conservatieve
compoundanalyse die alleen afkeurt wanneer het specialiserende component
betrouwbaar is vastgesteld.
"""

from __future__ import annotations

import logging

from services.validation.evaluators.base import (
    EvaluationDeps,
    EvaluationOutcome,
    falende_uitkomst,
)
from services.validation.types_internal import EvaluationContext
from toetsregels.runtime_contract import EvaluatorType, RuleRecord

logger = logging.getLogger(__name__)

__all__ = ["CompoundEvaluator"]


class CompoundEvaluator:
    """Een samengesteld begrip blijft een specialisatie van zijn genus."""

    evaluator_type = EvaluatorType.COMPOUND

    def evaluate(
        self, record: RuleRecord, ctx: EvaluationContext, deps: EvaluationDeps
    ) -> EvaluationOutcome:
        tekst = (ctx.cleaned_text or "").strip().lower()
        eerste_token = self._eerste_token_na_dubbelepunt(tekst)
        begrip = (ctx.begrip or "").strip().lower()

        if not eerste_token or not begrip or " " in begrip:
            return EvaluationOutcome.passed()
        if eerste_token in begrip:
            return EvaluationOutcome.passed()

        return falende_uitkomst(
            record,
            deps,
            melding=(
                "Samenstelling start niet met het specialiserende component (genus)"
            ),
            suggestie=(
                "Laat de definitie beginnen met het genus uit de samenstelling "
                "(bv. 'model …' bij 'procesmodel')."
            ),
        )

    @staticmethod
    def _eerste_token_na_dubbelepunt(tekst: str) -> str | None:
        if ":" not in tekst:
            return None
        try:
            romp = tekst.split(":", 1)[1].strip()
            return (romp.split() or [""])[0] or None
        except (AttributeError, IndexError) as exc:
            logger.debug(
                "SAM-04 tokenextractie gefaald: %s: %s",
                type(exc).__name__,
                exc,
                extra={"component": "evaluators.compound"},
            )
            return None
