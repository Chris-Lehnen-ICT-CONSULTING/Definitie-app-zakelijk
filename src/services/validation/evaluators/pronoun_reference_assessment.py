"""INT-03 — duidelijke voornaamwoord-verwijzing (DEF-772 WP3, K2 T-c).

De regel is niet langer een permanent open reviewpunt op een woordpatroon:
sinds DEF-772 beoordeelt de app zelf, via
`domain.int03.contract.beoordeel_verwijzingen`, of ieder verwijzend gebruikt
woord in de ongewijzigde definitie een eenduidig antecedent in de definitie
heeft. Deze evaluator is synchroon en zuiver; de AI-beoordeling wordt door de
async wrapper verkregen (`ValidationOrchestratorV2` →
`Int03AssessmentService`) en reist mee in `metadata["int03_assessment"]`
met de actuele binding in `metadata["int03_binding"]`.

- lege definitietekst → `not_evaluated` (geen toetsobject; de basisfout
  blijft bij VAL-EMP-001), zonder modelaanroep;
- geen (toepasbare) beoordeling → `review_required` met de reden — nooit
  pass: een directe service-aanroep zonder voorbereide beoordeling blijft
  expliciet niet beoordeeld, ook zonder enig signaalwoord (K7 ontstaat
  uitsluitend ná de inhoudelijke controle);
- gevalideerde beoordeling → `pass` (voldoet, of K7: geen verwijzend woord met
  exact de afgesproken motivering en de bevinding `no_referring_word`), `fail`
  (woord + plausibele kandidaten, of lege kandidatenlijst zonder antecedent)
  of `review_required` mét precies één gerichte vraag;
- technische fout in de beoordeling → `error` (nooit pass, nooit afkeur); dat
  geldt ook voor een beoordeling die bij replay structureel ongeldig is of een
  citaat draagt dat niet in de tekst staat (`invalid`), met een reden zonder
  modeltekst — alleen ontbrekend, niet beschikbaar of historisch blijft open;
- nooit een cijfer: `score` blijft `None`, de regel declareert
  `score_policy: excluded_from_score` en levert haar gestructureerde uitkomst
  (inclusief het volledige beoordelingsdocument) in `rule_results`.

De signaalpatronen uit het record (`herkenbaar_patronen`, K4) blijven
zoekhulp: zij reizen als `signals` mee in het detail, maar bepalen nooit de
status. Een negatieve uitkomst is zichtbaar (violation met de AI-onderbouwing)
maar geen blokkade: de ernst wordt, zoals bij ESS-03, expliciet op
`warning`/`medium` gezet en `metadata.advisory` markeert dat; toetsen wijzigt
de tekst niet en start geen herstel (K5: herstel alleen op verzoek).
"""

from __future__ import annotations

import re
from typing import Any

from domain.int03.contract import (
    STATUS_ERROR,
    STATUS_FAIL,
    STATUS_PASS,
    Beoordelingsbinding,
    Int03Uitkomst,
    beoordeel_verwijzingen,
    toelichting_uit_context,
)
from services.validation.evaluators.base import (
    EvaluationDeps,
    EvaluationOutcome,
    bouw_violation,
)
from services.validation.types_internal import EvaluationContext
from toetsregels.runtime_contract import EvaluatorType, ResultStatus, RuleRecord
from validation.additional_patterns import get_additional_patterns

__all__ = [
    "ADVISORY_SEVERITY",
    "ADVISORY_SEVERITY_LEVEL",
    "PronounReferenceAssessmentEvaluator",
]

#: De niet-blokkerende ernst van een negatieve INT-03-uitkomst (zoals ESS-03).
ADVISORY_SEVERITY = "warning"
ADVISORY_SEVERITY_LEVEL = "medium"


class PronounReferenceAssessmentEvaluator:
    """Verwijzingsduidelijkheid van INT-03: per woord antecedent en lezing, zonder cijfer."""

    evaluator_type = EvaluatorType.PRONOUN_REFERENCE_ASSESSMENT

    def evaluate(
        self, record: RuleRecord, ctx: EvaluationContext, deps: EvaluationDeps
    ) -> EvaluationOutcome:
        metadata = ctx.metadata or {}
        # Zelfde tekstbasis als CON-01/ESS-03: de exacte recordtekst, niet de
        # opgeschoonde variant, zodat de vingerafdruk bij het record hoort.
        recordtekst = metadata.get("record_text")
        tekst = recordtekst if isinstance(recordtekst, str) else (ctx.raw_text or "")
        if not tekst.strip():
            return EvaluationOutcome.not_evaluated(
                "vereiste invoer ontbreekt: definition_text (lege definitietekst, "
                "geen toetsobject voor INT-03)"
            )
        signalen = _signalen(record, tekst, deps)
        uitkomst = beoordeel_verwijzingen(
            ctx.begrip or "",
            tekst,
            metadata,
            toelichting_uit_context(metadata),
            assessment=metadata.get("int03_assessment"),
            binding=_binding_uit(metadata.get("int03_binding")),
        )
        return _naar_outcome(record, deps, uitkomst, signalen)


def _signalen(record: RuleRecord, tekst: str, deps: EvaluationDeps) -> tuple[str, ...]:
    """De recordpatronen die op de tekst vuren — zoekhulp, geen oordeel.

    Compileerbaarheid is bij het laden afgedwongen (`build_rule_record`); een
    fout hier loopt naar de ERROR-grens in plaats van de signalen stil weg te
    laten (DEF-667).
    """
    code = record.rule_id.upper()
    sleutel = f"__int03__{code}"
    gecompileerd = deps.pattern_cache.get(sleutel)
    if gecompileerd is None:
        patronen = list(record.get("herkenbaar_patronen", []) or [])
        extra = get_additional_patterns(code)
        if extra:
            patronen = list(dict.fromkeys([*patronen, *extra]))
        gecompileerd = [re.compile(p, re.IGNORECASE) for p in patronen]
        deps.pattern_cache[sleutel] = gecompileerd
    return tuple(patroon.pattern for patroon in gecompileerd if patroon.search(tekst))


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
    record: RuleRecord,
    deps: EvaluationDeps,
    uitkomst: Int03Uitkomst,
    signalen: tuple[str, ...],
) -> EvaluationOutcome:
    detail: dict[str, Any] = uitkomst.als_dict()
    detail["signals"] = list(signalen)
    (deel,) = uitkomst.parts
    samenvatting = uitkomst.review.get("assessment") or {}
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
                metadata={
                    "fingerprint": uitkomst.fingerprint,
                    "advisory": True,
                    "verdict": samenvatting.get("verdict"),
                    "finding": samenvatting.get("finding"),
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
        metadata={"signals": list(signalen), "rule_result": detail},
    )
