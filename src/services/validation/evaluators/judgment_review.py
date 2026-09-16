"""Oordeelregels: expliciet reviewplichtig, nooit stil geslaagd (DEF-624).

Twaalf regels hebben geen betrouwbare automatische toets:

- besluit DEF-624 (acht regels): ARAI-03, ESS-01, ESS-04, INT-02, INT-06,
  STR-03, STR-05 en STR-06;
- SAM-01, dat naast een oordeel ook de begrippenverzameling nodig heeft en
  daarom `definition_repository` als vereiste invoer declareert;
- projectuitbreiding: INT-03, STR-08 en STR-09.

Hun patronen blijven bruikbaar als *signaal* — ze wijzen de reviewer waar
te kijken — maar ze zijn geen *bewijs*: bij alle twaalf vuren de eigen
patronen ook op het gedocumenteerde goede voorbeeld, of missen ze het
gedocumenteerde foute voorbeeld volledig.

Dát het er twaalf zijn wordt bewaakt door
`tests/unit/validation/test_rule_runtime_matrix.py::TestAfgeleideTelling`:
die klasse leidt de klasseverdeling uit de records af en faalt zodra het
aantal `review_required`-regels verschuift. Zij legt alleen die telling
vast — niet de identiteit van de twaalf regels hierboven. Een canonieke,
hardgecodeerde lijst en de bijbehorende semantische dekking komen met
Batch 2 via DEF-623; die tests staan tot dan geparkeerd buiten `main`.

Daarom levert deze evaluator altijd `review_required`. Die uitkomst telt
niet mee in de kwaliteitsscore en wordt nooit als pass genormaliseerd; hij
verschijnt apart in de evaluatiedekking. Een gecontroleerde AI-jury is
bewust níet ingevoerd: dat vraagt een afzonderlijk besluit over prompt- en
modelversie, goldset, privacy, kosten en foutbeleid (ADR-001).
"""

from __future__ import annotations

import re

from services.validation.evaluators.base import (
    EvaluationDeps,
    EvaluationOutcome,
)
from services.validation.types_internal import EvaluationContext
from toetsregels.runtime_contract import EvaluatorType, RuleRecord
from validation.additional_patterns import get_additional_patterns

__all__ = ["JudgmentReviewEvaluator"]


class JudgmentReviewEvaluator:
    """Menselijk oordeel vereist; patronen zijn hooguit een aanwijzing."""

    evaluator_type = EvaluatorType.JUDGMENT_REVIEW

    def evaluate(
        self, record: RuleRecord, ctx: EvaluationContext, deps: EvaluationDeps
    ) -> EvaluationOutcome:
        signalen = self._signalen(record, ctx, deps)
        toetsvraag = str(record.get("toetsvraag") or record.get("naam") or "").strip()
        reden = toetsvraag or "Deze regel vereist een inhoudelijk oordeel."
        if record.rule_id.upper() == "ESS-01":
            reden = self._ess01_reden(ctx, signalen)
        return EvaluationOutcome.review_required(reden, signals=signalen)

    @staticmethod
    def _ess01_reden(ctx: EvaluationContext, signalen: tuple[str, ...]) -> str:
        """A: citeer passages in het bestaande redenveld; geen inhoudelijk oordeel."""
        reden = (
            "ESS-01 — Nog te beoordelen: welke kenmerken bepalen de betekenis van "
            "dit begrip? Beoordeel eventuele functie- of doelkenmerken en leg de grond vast."
        )
        treffers = sorted(
            (hit.start(), hit.group())
            for patroon in signalen
            for hit in re.finditer(patroon, ctx.cleaned_text, re.IGNORECASE)
        )
        passages = dict.fromkeys(fragment for _, fragment in treffers)
        if not passages:
            return (
                reden
                + " Geen patroonsignaal gevonden; inhoudelijke beoordeling blijft nodig."
            )
        return (
            reden
            + " "
            + " ".join(
                f"Te beoordelen passage: {fragment}. Bepaalt deze passage het begrip of "
                "beschrijft zij een doel, gebruik of verband? Dit signaal geeft nog geen "
                "inhoudelijk oordeel."
                for fragment in passages
            )
        )

    @staticmethod
    def _signalen(
        record: RuleRecord, ctx: EvaluationContext, deps: EvaluationDeps
    ) -> tuple[str, ...]:
        code = record.rule_id.upper()
        sleutel = f"__judgment__{code}"
        gecompileerd = deps.pattern_cache.get(sleutel)
        if gecompileerd is None:
            patronen = list(record.get("herkenbaar_patronen", []) or [])
            extra = get_additional_patterns(code)
            if extra:
                patronen = list(dict.fromkeys([*patronen, *extra]))
            # Zie generic.py: compileerbaarheid is bij het laden afgedwongen;
            # een fout hier is een contractbreuk die naar de ERROR-grens moet
            # doorlopen in plaats van de signalen stil weg te laten (DEF-667).
            gecompileerd = [re.compile(p, re.IGNORECASE) for p in patronen]
            deps.pattern_cache[sleutel] = gecompileerd

        tekst = ctx.cleaned_text or ""
        return tuple(
            patroon.pattern for patroon in gecompileerd if patroon.search(tekst)
        )
