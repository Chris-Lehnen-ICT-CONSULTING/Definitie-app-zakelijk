"""ESS-03 — telbaarheid en onderscheidbaarheid van instanties (DEF-766).

De regel toetst niet langer een woordpatroon en is niet langer een
permanent open reviewpunt: sinds DEF-766 beoordeelt de app zelf, via
`domain.ess03.contract.beoordeel_telbaarheid`, of de kandidaat bij de
bedoelde betekenis duidelijk maakt wat als één, dezelfde of een andere
instantie geldt. Deze evaluator is synchroon en zuiver; de AI-beoordeling
wordt door de async wrapper verkregen (`ValidationOrchestratorV2` →
`Ess03AssessmentService`) en reist mee in `metadata["ess03_assessment"]`.

- lege definitietekst → `not_evaluated` (geen toetsobject; de basisfout
  blijft bij VAL-EMP-001);
- geen (toepasbare) beoordeling → `review_required` met de reden — nooit
  pass: een directe service-aanroep zonder voorbereide beoordeling blijft
  expliciet niet beoordeeld;
- gevalideerde beoordeling → `pass` / `fail` / `not_applicable`, of
  `review_required` mét precies één gerichte vraag (onvoldoende informatie);
- technische fout in de beoordeling → `error` (nooit pass, nooit afkeur);
- nooit een cijfer: `score` blijft `None`, de regel declareert
  `score_policy: no_score`.

Een negatieve uitkomst is zichtbaar (violation met de AI-onderbouwing) maar
geen blokkade: de ernst wordt expliciet op `warning`/`medium` gezet, zodat
noch de acceptatiegate (critical-telling) noch de vaststelgate (kritieke/hoge
issues) erdoor verandert, en `metadata.advisory` markeert dat. Toetsen
wijzigt de tekst niet en start geen herstel (besluit 21 september 2026).
"""

from __future__ import annotations

from typing import Any

from domain.ess03.contract import (
    STATUS_ERROR,
    STATUS_FAIL,
    STATUS_NOT_APPLICABLE,
    STATUS_PASS,
    Beoordelingsbinding,
    Ess03Uitkomst,
    beoordeel_telbaarheid,
    intentie_uit_context,
)
from services.validation.evaluators.base import (
    EvaluationDeps,
    EvaluationOutcome,
    bouw_violation,
)
from services.validation.types_internal import EvaluationContext
from toetsregels.runtime_contract import EvaluatorType, ResultStatus, RuleRecord

__all__ = [
    "ADVISORY_SEVERITY",
    "ADVISORY_SEVERITY_LEVEL",
    "CountabilityAssessmentEvaluator",
]

#: De niet-blokkerende ernst van een negatieve ESS-03-uitkomst (besluit 21-09-2026).
ADVISORY_SEVERITY = "warning"
ADVISORY_SEVERITY_LEVEL = "medium"


class CountabilityAssessmentEvaluator:
    """Telbaarheid van ESS-03: eenheid, onderscheid en toepasselijkheid, zonder cijfer."""

    evaluator_type = EvaluatorType.COUNTABILITY_ASSESSMENT

    def evaluate(
        self, record: RuleRecord, ctx: EvaluationContext, deps: EvaluationDeps
    ) -> EvaluationOutcome:
        metadata = ctx.metadata or {}
        # Zelfde tekstbasis als CON-01/CON-02: de exacte recordtekst, niet de
        # opgeschoonde variant, zodat de vingerafdruk bij het record hoort.
        recordtekst = metadata.get("record_text")
        tekst = recordtekst if isinstance(recordtekst, str) else (ctx.raw_text or "")
        if not tekst.strip():
            # DEF-766 (casus H-empty): zonder toetsobject is er niets te
            # beoordelen — geen open vraag over een lege kern en geen
            # inhoudelijke afkeur; de basisfout blijft bij VAL-EMP-001.
            return EvaluationOutcome.not_evaluated(
                "vereiste invoer ontbreekt: definition_text (lege definitietekst, "
                "geen toetsobject voor ESS-03)"
            )
        bronnen = metadata.get("provenance_sources")
        if bronnen is None:
            bronnen = metadata.get("sources")
        uitkomst = beoordeel_telbaarheid(
            ctx.begrip or "",
            tekst,
            metadata,
            bronnen,
            intentie=intentie_uit_context(metadata),
            assessment=metadata.get("ess03_assessment"),
            # R1: de actuele beoordelingsbinding zoals de wrapper haar van de
            # dienst kreeg; zonder binding is geen beoordeling actueel.
            binding=_binding_uit(metadata.get("ess03_binding")),
        )
        return _naar_outcome(record, deps, uitkomst)


def _binding_uit(waarde: Any) -> Beoordelingsbinding | None:
    """De door de wrapper meegegeven binding, of None (geen verzonnen binding)."""
    if not isinstance(waarde, dict):
        return None
    try:
        return Beoordelingsbinding(
            prompt_version=str(waarde["prompt_version"]),
            norm_sha256=str(waarde["norm_sha256"]),
            provider=waarde.get("provider"),
            model=waarde.get("model"),
        )
    except (KeyError, TypeError):
        return None


def _naar_outcome(
    record: RuleRecord, deps: EvaluationDeps, uitkomst: Ess03Uitkomst
) -> EvaluationOutcome:
    detail: dict[str, Any] = uitkomst.als_dict()
    (deel,) = uitkomst.parts
    if uitkomst.status == STATUS_PASS:
        return EvaluationOutcome(
            status=ResultStatus.PASS, score=None, metadata={"rule_result": detail}
        )
    if uitkomst.status == STATUS_NOT_APPLICABLE:
        return EvaluationOutcome(
            status=ResultStatus.NOT_APPLICABLE,
            score=None,
            reason=deel.reason,
            metadata={"rule_result": detail},
        )
    if uitkomst.status == STATUS_FAIL:
        return EvaluationOutcome(
            status=ResultStatus.FAIL,
            score=None,
            violation=bouw_violation(
                record,
                deps,
                melding=deel.reason,
                suggestie=deel.action,
                metadata={
                    "fingerprint": uitkomst.fingerprint,
                    "advisory": True,
                    "verdict": (uitkomst.review.get("assessment") or {}).get("verdict"),
                },
                severity=ADVISORY_SEVERITY,
                severity_level=ADVISORY_SEVERITY_LEVEL,
            ),
            metadata={"rule_result": detail},
        )
    if uitkomst.status == STATUS_ERROR:
        return EvaluationOutcome(
            status=ResultStatus.ERROR,
            score=None,
            reason=deel.reason,
            metadata={"rule_result": detail},
        )
    return EvaluationOutcome(
        status=ResultStatus.REVIEW_REQUIRED,
        score=None,
        reason=deel.reason,
        metadata={
            "signals": [deel.evidence] if deel.evidence else [],
            "rule_result": detail,
        },
    )
