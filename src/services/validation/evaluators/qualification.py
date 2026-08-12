"""SAM-02 — kwalificatie omvat geen herhaling van het hoofdbegrip (DEF-606).

Overgenomen uit `ModularValidationService._evaluate_json_rule`. De tweede
tak bevat een hardcoded basisfrase (`binnen de grenzen van`, `wettelijke
strafbepaling`) die letterlijk uit het goede voorbeeld van `SAM-02.json`
komt; die wordt in DEF-623 vervangen door een vergelijking met de
werkelijke hoofdbegripsdefinitie.
"""

from __future__ import annotations

import logging

from services.validation.evaluators.base import (
    EvaluationDeps,
    EvaluationOutcome,
)
from services.validation.types_internal import EvaluationContext
from services.validation.violation_builder import category_for_rule
from toetsregels.runtime_contract import EvaluatorType, ResultStatus, RuleRecord

logger = logging.getLogger(__name__)

__all__ = ["QualificationEvaluator"]

_BASISFRASEN = ("binnen de grenzen van", "wettelijke strafbepaling")


class QualificationEvaluator:
    """Een gekwalificeerd begrip herhaalt de hoofddefinitie niet."""

    evaluator_type = EvaluatorType.QUALIFICATION

    def evaluate(
        self, record: RuleRecord, ctx: EvaluationContext, deps: EvaluationDeps
    ) -> EvaluationOutcome:
        hoofdwoord = self._hoofdwoord(ctx)
        if not hoofdwoord:
            return EvaluationOutcome.passed()

        tekst = (ctx.cleaned_text or "").strip().lower()

        if tekst.startswith(f"{hoofdwoord}:"):
            return self._violation(
                record,
                ctx,
                deps,
                melding=(
                    "Kwalificatie definieert het hoofdbegrip in plaats van het "
                    "gekwalificeerde begrip"
                ),
                suggestie=(
                    "Begin met het gekwalificeerde begrip en gebruik "
                    "genus+differentia zonder de basisdefinitie te herhalen."
                ),
            )

        if hoofdwoord in tekst and any(frase in tekst for frase in _BASISFRASEN):
            return self._violation(
                record,
                ctx,
                deps,
                melding=(
                    "Kwalificatie bevat (gedeelten van) de basisdefinitie van "
                    "het hoofdbegrip"
                ),
                suggestie=(
                    "Gebruik genus+differentia: noem het hoofdbegrip kort (bv. "
                    "'delict') en voeg alleen het onderscheidende criterium toe."
                ),
            )

        return EvaluationOutcome.passed()

    @staticmethod
    def _hoofdwoord(ctx: EvaluationContext) -> str | None:
        try:
            delen = (ctx.begrip or "").strip().lower().split()
        except (AttributeError, IndexError) as exc:
            logger.debug(
                "SAM-02 hoofdwoord-extractie overgeslagen: %s: %s",
                type(exc).__name__,
                exc,
                extra={"component": "evaluators.qualification"},
            )
            return None
        return delen[-1] if len(delen) >= 2 else None

    @staticmethod
    def _violation(
        record: RuleRecord,
        ctx: EvaluationContext,
        deps: EvaluationDeps,
        *,
        melding: str,
        suggestie: str,
    ) -> EvaluationOutcome:
        code = record.rule_id.upper()
        return EvaluationOutcome(
            status=ResultStatus.FAIL,
            score=0.0,
            violation={
                "code": code,
                "severity": deps.support.severity_for(dict(record.data)),
                "message": melding,
                "description": melding,
                "rule_id": code,
                "category": category_for_rule(code),
                "suggestion": suggestie,
            },
        )
