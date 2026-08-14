"""ESS-02 — ontologische categorie eenduidig expliciteren (DEF-606).

Overgenomen uit `ModularValidationService._eval_ess02`. De regel is de
lokale uitbreiding van ASTRA's binaire "type of instantie" naar vier
UFO-categorieën (type/particulier/proces/resultaat); die uitbreiding wordt
via DEF-625 als bewuste projectafwijking vastgelegd.
"""

from __future__ import annotations

import logging
import re

from services.validation.evaluators.base import (
    EvaluationDeps,
    EvaluationOutcome,
    falende_uitkomst,
)
from services.validation.types_internal import EvaluationContext
from toetsregels.runtime_contract import EvaluatorType, RuleRecord

logger = logging.getLogger(__name__)

__all__ = ["OntologicalCategoryEvaluator"]

_GELDIGE_MARKERS = frozenset(
    {
        "soort",
        "type",
        "exemplaar",
        "particulier",
        "proces",
        "activiteit",
        "resultaat",
        "uitkomst",
    }
)

_CATEGORIEVELDEN: tuple[tuple[str, str], ...] = (
    ("type", "herkenbaar_patronen_type"),
    ("particulier", "herkenbaar_patronen_particulier"),
    ("proces", "herkenbaar_patronen_proces"),
    ("resultaat", "herkenbaar_patronen_resultaat"),
)


class OntologicalCategoryEvaluator:
    """Precies één ontologische categorie moet herkenbaar zijn."""

    evaluator_type = EvaluatorType.ONTOLOGICAL_CATEGORY

    def evaluate(
        self, record: RuleRecord, ctx: EvaluationContext, deps: EvaluationDeps
    ) -> EvaluationOutcome:
        code = record.rule_id.upper()
        text = ctx.cleaned_text or ""

        if self._marker_is_expliciet(ctx):
            return EvaluationOutcome.passed()

        treffers = self._categorietreffers(record, deps, text)
        if len(treffers) == 1:
            return EvaluationOutcome.passed()

        if len(treffers) > 1:
            melding = (
                f"Ambigu: meerdere categorieën herkend ({', '.join(sorted(treffers))})"
            )
            reden = "ambigu"
        else:
            melding = (
                "Geen duidelijke ontologische marker "
                "(type/particulier/proces/resultaat)"
            )
            reden = "missing"

        # DEF-669: severity en severity_level kwamen hier uit een hardcoded
        # "error"/"high" in plaats van uit het regelrecord. ESS-02 is
        # verplicht+hoog en hoort dus severity_level "critical" te dragen,
        # net als elke andere verplichte regel met hoge prioriteit.
        return falende_uitkomst(
            record,
            deps,
            melding=melding,
            suggestie=deps.support.build_suggestion(
                code, dict(record.data), text, ctx, reason=reden
            ),
        )

    @staticmethod
    def _marker_is_expliciet(ctx: EvaluationContext) -> bool:
        try:
            marker = (ctx.metadata or {}).get("marker")
        except (TypeError, AttributeError) as exc:
            logger.debug(
                "ESS-02 marker extractie overgeslagen: %s: %s",
                type(exc).__name__,
                exc,
                extra={"component": "evaluators.ontological_category"},
            )
            return False
        return bool(marker) and str(marker).strip().lower() in _GELDIGE_MARKERS

    @staticmethod
    def _categorietreffers(
        record: RuleRecord, deps: EvaluationDeps, text: str
    ) -> set[str]:
        sleutel = f"__ess02__{record.rule_id}"
        gecompileerd = deps.pattern_cache.get(sleutel)
        if gecompileerd is None:
            # Zie generic.py: geen `except re.error` die de categorie stil op
            # een lege patroonlijst zet. Een categorie zonder patronen kan dan
            # nooit meer treffen, waardoor de regel van "ambigu" naar
            # "eenduidig" verschuift zonder dat er iets is gemeten (DEF-667).
            gecompileerd = {
                categorie: [
                    re.compile(p, re.IGNORECASE) for p in (record.get(veld, []) or [])
                ]
                for categorie, veld in _CATEGORIEVELDEN
            }
            deps.pattern_cache[sleutel] = gecompileerd

        return {
            categorie
            for categorie, patronen in gecompileerd.items()
            if any(p.search(text) for p in patronen)
        }
