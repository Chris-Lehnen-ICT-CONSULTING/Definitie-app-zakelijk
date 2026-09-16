"""CON-02 — bronbewijs (DEF-743).

De regel toetst niet langer een woordpatroon in de definitiezin (`volgens`,
`conform`, `wet`): een bronwoord bewijst geen bron, en het ontbreken ervan is
geen gebrek wanneer de bron in de brongegevens staat. Sinds DEF-743 loopt de
beoordeling via `domain.sources.contract.beoordeel_bronbasis`:

- geen bronnen aangeleverd → drie onderdelen `review_required` (expliciet
  open, geen violation, geen not_evaluated) — zonder AI-aanroep;
- bronnen mét een gevalideerde AI-beoordeling → per onderdeel pass/fail/open
  uit het oordeel, nadat de code het bewijs (citaat in dié passage) en de
  binding (vingerafdruk over tekst, term, context, peildatum, bronidentiteit)
  opnieuw heeft gecontroleerd; een pass/fail zonder aantoonbaar bewijs is open;
- technische fout in de beoordeling → `error` (nooit pass);
- deskundige uitzonderingen blijven zichtbaar als uitzondering
  (`review_required`, `field=source_review`), nooit als gewoon 'voldoet';
- nooit een cijfer: `score` blijft `None`, de regel declareert
  `score_policy: no_score`.

De AI-beoordeling zelf wordt niet hier maar door de async wrapper verkregen
(`ValidationOrchestratorV2` → `SourceAssessmentService`) en reist mee in
`metadata["source_assessment"]`; deze evaluator is synchroon en zuiver.
De gestructureerde deeluitkomsten reizen in `metadata["rule_result"]` naar de
service, die ze onder `rule_results["CON-02"]` publiceert.
"""

from __future__ import annotations

from typing import Any

from domain.sources.contract import (
    STATUS_ERROR,
    STATUS_FAIL,
    STATUS_PASS,
    BronUitkomst,
    beoordeel_bronbasis,
)
from services.validation.evaluators.base import (
    EvaluationDeps,
    EvaluationOutcome,
    bouw_violation,
)
from services.validation.types_internal import EvaluationContext
from toetsregels.runtime_contract import EvaluatorType, ResultStatus, RuleRecord

__all__ = ["SourceEvidenceEvaluator"]


class SourceEvidenceEvaluator:
    """Bronbasis van CON-02: gezag, betekenissteun en verwijzing, zonder cijfer."""

    evaluator_type = EvaluatorType.SOURCE_EVIDENCE

    def evaluate(
        self, record: RuleRecord, ctx: EvaluationContext, deps: EvaluationDeps
    ) -> EvaluationOutcome:
        metadata = ctx.metadata or {}
        # Zelfde tekstbasis als CON-01: de exacte recordtekst, niet de
        # opgeschoonde variant, zodat de vingerafdruk bij het record hoort.
        recordtekst = metadata.get("record_text")
        tekst = recordtekst if isinstance(recordtekst, str) else (ctx.raw_text or "")
        bronnen = metadata.get("provenance_sources")
        if bronnen is None:
            bronnen = metadata.get("sources")
        uitkomst = beoordeel_bronbasis(
            ctx.begrip or "",
            tekst,
            metadata,
            bronnen,
            assessment=metadata.get("source_assessment"),
            review=metadata.get("source_review"),
            definitie_versie=metadata.get("definition_version"),
            peildatum=metadata.get("peildatum"),
            # De werkelijke afkapgrens van de beoordelingsdienst (door de
            # wrapper meegegeven); bindt de beoordelingskwitantie aan de echte
            # dienstgrens i.p.v. alleen aan interne consistentie.
            max_passage_chars=_grens(metadata.get("assessment_max_passage_chars")),
        )
        return _naar_outcome(record, deps, uitkomst)


def _grens(waarde: Any) -> int | None:
    """Een positieve gehele afkapgrens, of None (geen verzonnen grens)."""
    if isinstance(waarde, int) and not isinstance(waarde, bool) and waarde > 0:
        return waarde
    return None


def _naar_outcome(
    record: RuleRecord, deps: EvaluationDeps, uitkomst: BronUitkomst
) -> EvaluationOutcome:
    detail: dict[str, Any] = uitkomst.als_dict()
    if uitkomst.status == STATUS_PASS:
        return EvaluationOutcome(
            status=ResultStatus.PASS,
            score=None,
            metadata={"rule_result": detail},
        )

    open_delen = [
        p for p in uitkomst.parts if p.status not in (STATUS_FAIL, STATUS_PASS)
    ]
    if uitkomst.status == STATUS_FAIL:
        falend = [p for p in uitkomst.parts if p.status == STATUS_FAIL]
        melding = "; ".join(dict.fromkeys(p.reason for p in falend))
        acties = list(dict.fromkeys(p.action for p in falend))
        if open_delen:
            acties.append(
                "Daarnaast staat nog open: " + ", ".join(p.id for p in open_delen) + "."
            )
        return EvaluationOutcome(
            status=ResultStatus.FAIL,
            score=None,
            violation=bouw_violation(
                record,
                deps,
                melding=melding,
                suggestie=" ".join(acties) or None,
                metadata={
                    "fingerprint": uitkomst.fingerprint,
                    "failing_parts": [p.id for p in falend],
                    "open_parts": [p.id for p in open_delen],
                },
            ),
            metadata={"rule_result": detail},
        )

    if uitkomst.status == STATUS_ERROR:
        mislukt = [p for p in uitkomst.parts if p.status == STATUS_ERROR]
        return EvaluationOutcome(
            status=ResultStatus.ERROR,
            score=None,
            reason="bronbeoordeling mislukt voor: " + ", ".join(p.id for p in mislukt),
            metadata={"rule_result": detail},
        )

    reden = "; ".join(dict.fromkeys(p.reason for p in open_delen)) or (
        "De bronbasis van de definitie is nog niet beoordeeld."
    )
    return EvaluationOutcome(
        status=ResultStatus.REVIEW_REQUIRED,
        score=None,
        reason=reden,
        metadata={
            "signals": [p.evidence for p in open_delen if p.evidence],
            "rule_result": detail,
        },
    )
