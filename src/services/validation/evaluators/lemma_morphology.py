"""Morfologie van de term zelf: VER-01 en VER-03 (DEF-606).

Overgenomen uit `ModularValidationService`: de plurale-tantumcontrole van
VER-01 (`_lemma_is_singular`, sinds DEF-605 aangesloten op de gecureerde
domeinlijst) en de infinitiefcontrole van VER-03.

Twee bekende gaten, belegd bij DEF-623:

- VER-01 keurt zijn eigen goede voorbeeld `gegeven` af, omdat de heuristiek
  elke uitgang `-en` als meervoud leest;
- VER-03 keurt élk lemma op `-t`/`-d` af en raakt daarmee zelfstandige
  naamwoorden als `besluit`, `gebied` en `beleid`.

Beide worden hier bewust ongewijzigd overgenomen; het contract eerst, de
semantiek in DEF-623.
"""

from __future__ import annotations

import re

from domain.linguistisch.pluralia_tantum import PluraliatantumChecker
from services.validation.evaluators.base import (
    EvaluationDeps,
    EvaluationOutcome,
    Finding,
    falende_uitkomst,
)
from services.validation.evaluators.generic import (
    uitkomst_van,
    verzamel_generieke_bevindingen,
)
from services.validation.types_internal import EvaluationContext
from toetsregels.runtime_contract import EvaluatorType, RuleRecord

__all__ = ["LemmaMorphologyEvaluator", "lemma_is_enkelvoud"]


def lemma_is_enkelvoud(begrip: str | None) -> bool:
    """Is het lemma enkelvoud, of een erkend plurale tantum?"""
    lemma = (begrip or "").strip().lower()
    if PluraliatantumChecker.is_plurale_tantum_of_samenstelling(lemma):
        return True
    if re.search(r"\w+ens$", lemma):
        return False
    return not bool(re.search(r"\w+en$", lemma))


class LemmaMorphologyEvaluator:
    """VER-01 (enkelvoud) en VER-03 (infinitief) op het lemma."""

    evaluator_type = EvaluatorType.LEMMA_MORPHOLOGY

    def evaluate(
        self, record: RuleRecord, ctx: EvaluationContext, deps: EvaluationDeps
    ) -> EvaluationOutcome:
        code = record.rule_id.upper()
        if code == "VER-03":
            return self._infinitief(record, ctx, deps)
        return self._enkelvoud(record, ctx, deps)

    @staticmethod
    def _infinitief(
        record: RuleRecord, ctx: EvaluationContext, deps: EvaluationDeps
    ) -> EvaluationOutcome:
        lemma = str(ctx.begrip or "").strip()
        if lemma and re.search(r".+[td]$", lemma.lower()):
            return falende_uitkomst(
                record,
                deps,
                melding="Werkwoord-term niet in infinitief (eindigt op -t/-d)",
                suggestie=(
                    "Gebruik de onbepaalde wijs (infinitief), bijv. "
                    "'beoordelen' i.p.v. 'beoordeelt'."
                ),
            )
        return EvaluationOutcome.passed()

    @staticmethod
    def _enkelvoud(
        record: RuleRecord, ctx: EvaluationContext, deps: EvaluationDeps
    ) -> EvaluationOutcome:
        verzameld = verzamel_generieke_bevindingen(record, ctx, deps)
        if not lemma_is_enkelvoud(ctx.begrip or ""):
            verzameld = verzameld.met(
                (
                    Finding(
                        message="Term (lemma) lijkt meervoud (geen plurale tantum)",
                        reason="singular",
                        details=str(ctx.begrip or ""),
                    ),
                )
            )
        return uitkomst_van(verzameld)
