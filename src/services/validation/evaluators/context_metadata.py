"""CON-01 — contextcontract (DEF-606 / DEF-622).

De regel toetst niet langer een vaste patroonlijst (`\\bDJI\\b`,
`\\bstrafrecht\\b`, `\\bjuridisch(e)?\\b`, …): die keurde gewone woorden af
zonder dat zij iets met de geselecteerde context te maken hadden, en liet
"geen enkele context" als `pass` door. Sinds DEF-622 loopt de beoordeling via
`domain.context.contract.beoordeel_context`:

- geen betekenisvolle context bij het record → `fail` (B-01);
- een geselecteerde contextwaarde letterlijk (case-insensitief) in de zin →
  `review_required` totdat een expert de functie van die treffer heeft
  beoordeeld (B-04); na die beoordeling `fail` (registratiecontext) of `pass`
  (noodzakelijke naam, of — R1 — geen contextvermelding: een gewoon woord
  dat samenvalt met de contextwaarde);
- nooit een cijfer (B-06): `score` blijft `None`, de regel declareert
  `score_policy: no_score`.

De gestructureerde deeluitkomsten reizen in `metadata["rule_result"]` mee naar
de service, die ze onder `rule_results["CON-01"]` publiceert.

De duplicaatcontrole die hier in DEF-672 bij zat, is in DEF-674 verhuisd naar
`duplicate_detection` (DUP_01).
"""

from __future__ import annotations

from typing import Any

from domain.context.contract import (
    CONTEXT_VELDEN,
    STATUS_ERROR,
    STATUS_FAIL,
    STATUS_PASS,
    ContextUitkomst,
    beoordeel_context,
)
from domain.context.normalisatie import contextsleutel
from services.validation.evaluators.base import (
    EvaluationDeps,
    EvaluationOutcome,
    bouw_violation,
)
from services.validation.types_internal import EvaluationContext
from toetsregels.runtime_contract import EvaluatorType, ResultStatus, RuleRecord

__all__ = [
    "CONTEXT_VELDEN",
    "ContextMetadataEvaluator",
    "normaliseer_contextlijst",
]


def normaliseer_contextlijst(waarden: Any) -> list[str]:
    """Vergelijkingssleutel van één contextlijst, als lijst.

    Dunne laag over `domain.context.normalisatie.contextsleutel` — dé gedeelde
    normalisatie die de opslag, de contextinvariant en de duplicaatcontrole
    delen (DEF-672, vervroegd uit DEF-622). Blijft bestaan omdat bestaande
    aanroepers een `list` verwachten.

    Geen foutafhandeling (DEF-667): een niet-itereerbare contextwaarde leverde
    eerder een lege lijst op, en dan vergelijkt een kandidaat met échte
    context ongelijk — het duplicaat verdwijnt en de regel slaagt.
    """
    return list(contextsleutel(waarden))


class ContextMetadataEvaluator:
    """Contextcontract van CON-01: aanwezigheid en naamfunctie, zonder cijfer."""

    evaluator_type = EvaluatorType.CONTEXT_METADATA

    def evaluate(
        self, record: RuleRecord, ctx: EvaluationContext, deps: EvaluationDeps
    ) -> EvaluationOutcome:
        metadata = ctx.metadata or {}
        # Bewijs en vingerafdruk binden aan de exacte recordtekst, niet aan
        # een opgeschoonde variant: de expert beoordeelt wat op het record
        # staat, en een gewijzigde recordtekst moet een eerdere beoordeling
        # laten vervallen — ook wanneer cleaning het verschil wegpoetst.
        # `record_text` komt van de orchestrator (die vóór de service kan
        # cleanen); anders is de ongeschoonde invoer van de service de tekst.
        recordtekst = metadata.get("record_text")
        tekst = recordtekst if isinstance(recordtekst, str) else (ctx.raw_text or "")
        uitkomst = beoordeel_context(
            ctx.begrip or "",
            tekst,
            metadata,
            review=metadata.get("context_review"),
            definitie_versie=metadata.get("definition_version"),
        )
        return _naar_outcome(record, deps, uitkomst)


def _naar_outcome(
    record: RuleRecord, deps: EvaluationDeps, uitkomst: ContextUitkomst
) -> EvaluationOutcome:
    detail = uitkomst.als_dict()
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
            # B-08: bij falen én open (of mislukt) blijven beide zichtbaar,
            # ook in de violation die de bestaande UI toont.
            acties.append(
                "Daarnaast is nog niet elk naamsignaal beoordeeld: "
                + ", ".join(f"'{p.evidence}'" for p in open_delen if p.evidence)
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
        # Een mislukt onderdeel zonder bewezen overtreding: de regel als
        # geheel is een technische fout (fail-closed op de acceptatie), met de
        # afgeronde onderdelen zichtbaar in `rule_result`.
        mislukt = [p for p in uitkomst.parts if p.status == STATUS_ERROR]
        return EvaluationOutcome(
            status=ResultStatus.ERROR,
            score=None,
            reason="deelcontrole mislukt voor: " + ", ".join(p.id for p in mislukt),
            metadata={"rule_result": detail},
        )

    reden = "; ".join(dict.fromkeys(p.reason for p in open_delen)) or (
        "De functie van een naam in de definitiezin is nog niet beoordeeld."
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
