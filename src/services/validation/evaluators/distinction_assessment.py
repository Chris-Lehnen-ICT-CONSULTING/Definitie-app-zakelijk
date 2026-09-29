"""ESS-05 — voldoende onderscheidend van verwante begrippen (DEF-768).

De regel toetst geen woordindicator meer (die keurde het eigen en het
ASTRA-goede voorbeeld af en liet lege trefwoordzinnen slagen): de app
beoordeelt via `domain.ess05.contract.beoordeel_onderscheid` of de kern het
begrip in deze context kenbaar onderscheidt van zijn verwante begrippen.
Deze evaluator is synchroon en zuiver; de AI-beoordeling en de actieve
burenlijst worden door de async wrapper (`ValidationOrchestratorV2` →
`Ess05BewijsregelService`, sinds DEF-768 stap 2) voorbereid en reizen mee in
de metadata:

- `ess05_assessment` — het beoordelingsdocument (of None);
- `ess05_binding` — de actuele beoordelingsbinding van de dienst (de
  bewijsregelbinding; een ess05/2-binding blijft leesbaar);
- `ess05_actieve_buren` — de actieve burenlijst (gebruiker, bron,
  repository, model); zonder die sleutel de opgeslagen `ess05_buren`;
- `ess05_uitgesloten_termen` — afgewezen buurtermen;
- `ess05_lege_ruimte` — een deskundige bevestiging van een lege
  vergelijkingsruimte.

Lege tekst → `not_evaluated`; geen beoordeling → `review_required` (nooit
pass); technische fout → `error`; een negatieve uitkomst is zichtbaar maar
geen blokkade (`warning`/`medium`, `advisory`); nooit een cijfer.
"""

from __future__ import annotations

from typing import Any

from domain.ess03.contract import intentie_uit_context
from domain.ess05.contract import (
    STATUS_ERROR,
    STATUS_FAIL,
    STATUS_NOT_EVALUATED,
    STATUS_PASS,
    Ess05Uitkomst,
    beoordeel_onderscheid,
    binding_uit_dict,
)
from services.validation.evaluators.base import (
    EvaluationDeps,
    EvaluationOutcome,
    bouw_violation,
)
from services.validation.evaluators.countability_assessment import (
    ADVISORY_SEVERITY,
    ADVISORY_SEVERITY_LEVEL,
)
from services.validation.types_internal import EvaluationContext
from toetsregels.runtime_contract import EvaluatorType, ResultStatus, RuleRecord

__all__ = ["DistinctionAssessmentEvaluator"]


class DistinctionAssessmentEvaluator:
    """Onderscheid van ESS-05 per verwant begrip, zonder cijfer."""

    evaluator_type = EvaluatorType.DISTINCTION_ASSESSMENT
    #: Bij ontbrekende vereiste invoer (context) levert het contract zelf de
    #: gemotiveerde `not_evaluated` (reden + vervolgstap), zonder modelaanroep;
    #: de service accepteert van deze route uitsluitend `not_evaluated`.
    motiveert_ontbrekende_invoer = True

    def evaluate(
        self, record: RuleRecord, ctx: EvaluationContext, deps: EvaluationDeps
    ) -> EvaluationOutcome:
        metadata = ctx.metadata or {}
        recordtekst = metadata.get("record_text")
        tekst = recordtekst if isinstance(recordtekst, str) else (ctx.raw_text or "")
        if not tekst.strip():
            return EvaluationOutcome.not_evaluated(
                "vereiste invoer ontbreekt: definition_text (lege definitietekst, "
                "geen toetsobject voor ESS-05)"
            )
        bronnen = metadata.get("provenance_sources")
        if bronnen is None:
            bronnen = metadata.get("sources")
        buren = (
            metadata["ess05_actieve_buren"]
            if "ess05_actieve_buren" in metadata
            else metadata.get("ess05_buren")
        )
        uitkomst = beoordeel_onderscheid(
            ctx.begrip or "",
            tekst,
            metadata,
            bronnen,
            intentie=intentie_uit_context(metadata),
            buren=buren,
            lege_ruimte=metadata.get("ess05_lege_ruimte"),
            assessment=metadata.get("ess05_assessment"),
            # ESS-05-eigen binding, fail-closed: exact de velden van een van
            # beide routes; de ESS-03-parser zou velden stil laten wegvallen.
            binding=binding_uit_dict(metadata.get("ess05_binding")),
            uitgesloten_termen=metadata.get("ess05_uitgesloten_termen") or (),
        )
        return _naar_outcome(record, deps, uitkomst)


def _naar_outcome(
    record: RuleRecord, deps: EvaluationDeps, uitkomst: Ess05Uitkomst
) -> EvaluationOutcome:
    detail: dict[str, Any] = uitkomst.als_dict()
    deel = uitkomst.parts[0]
    if uitkomst.status == STATUS_PASS:
        return EvaluationOutcome(
            status=ResultStatus.PASS, score=None, metadata={"rule_result": detail}
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
                metadata={"fingerprint": uitkomst.fingerprint, "advisory": True},
                severity=ADVISORY_SEVERITY,
                severity_level=ADVISORY_SEVERITY_LEVEL,
            ),
            metadata={"rule_result": detail},
        )
    status = {
        STATUS_ERROR: ResultStatus.ERROR,
        STATUS_NOT_EVALUATED: ResultStatus.NOT_EVALUATED,
    }.get(uitkomst.status, ResultStatus.REVIEW_REQUIRED)
    return EvaluationOutcome(
        status=status,
        score=None,
        reason=deel.reason,
        metadata={"rule_result": detail},
    )
