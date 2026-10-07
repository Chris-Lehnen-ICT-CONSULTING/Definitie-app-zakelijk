"""INT-02 — geen beslisregel, O2-toepassing van een beoordeling (DEF-835 WP3).

Deze evaluator is synchroon en zuiver: hij doet geen modelaanroep en beslist
zelf niets over de norm. Hij past een getypeerd beoordelingsdocument
(`domain.int02.contract.Beoordelingsdocument`, contract
def835-int02-assessment/4; een bewaard /1–/3-document is historisch) toe op
de *actuele* invoer en de *expliciete actuele* configuratie, uitsluitend via
de bestaande WP1-controle
`toets_actualiteit` (NE → nog niet beoordeeld → fout/niet herleidbaar →
historisch → bewaard oordeel). Het oordeel zelf komt van de beoordelaar
(model of mens); de async verkrijging hoort bij de integratie (WP5).

Metadata-aansluiting (`EvaluationContext.metadata`):

- `record_text` (str): de exacte kern; zonder `record_text` de aangeleverde
  tekst (`raw_text`), zoals INT-03, zodat de binding bij het record hoort;
  een aanwezige waarde die geen tekst is, is ongeldige metadata (`error`);
- `organisatorische_context`, `juridische_context`, `wettelijke_basis`:
  lijst/tuple van teksten; afwezig of None is leeg;
- `int02_bedoeling`: tekst, of None/afwezig (expliciet onbekend);
- `int02_bronnen`: lijst van `{"id", "tekst"}`; afwezig of None is geen;
- `int02_configuratie`: `domain.int02.contract.Configuratie`;
- `int02_document`: `Beoordelingsdocument` of None/afwezig.

De actuele invoer wordt uitsluitend via `maak_invoer` gebouwd, nooit uit het
document afgeleid. Ongeldige metadata (verkeerd type, ongeldige invoer, een
ander documenttype) geeft `error` — nooit een positieve uitkomst en geen
exceptie. Zonder actuele configuratie is er geen actueel oordeel: nog niet
beoordeeld (of NE bij ontbrekende kern/context). Er wordt niets gelogd.

Uitkomst (contract 2.3.0): score altijd None; `metadata["rule_result"]` met
de exacte WP1-melding, `review.actuality` (`current`, `historical`,
`not_assessed`; None bij NE en fout), `assessment` (het document alleen als
`toets_actualiteit` het heeft aanvaard, anders None) en `signals` (de
recordpatronen die op de actuele kern vuren; leeshulp, nooit een oordeel).
Een fail is een zichtbare, adviserende violation (`warning`/`medium`, zoals
INT-03 en ESS-03), geen poort en geen herstel (besluiten B5/B6).

Grens: evaluator, register en schema zijn gereed; de container, orchestrator,
`ModularValidationService`-boekhouding, UI en opslag zijn het niet (WP5). Het
actieve INT-02-record kiest deze evaluator nog niet.
"""

from __future__ import annotations

import re
from typing import Any

from domain.int02.contract import (
    CONTRACTVERSIE,
    MELDING_E,
    MELDING_NE,
    MELDING_NIET_BEOORDEELD,
    Actualiteit,
    Beoordelingsdocument,
    Configuratie,
    Int02ContractError,
    Int02Invoer,
    maak_invoer,
    ontbrekende_invoer,
    toets_actualiteit,
)
from services.validation.evaluators.base import (
    EvaluationDeps,
    EvaluationOutcome,
    bouw_violation,
)
from services.validation.evaluators.pronoun_reference_assessment import (
    ADVISORY_SEVERITY,
    ADVISORY_SEVERITY_LEVEL,
)
from services.validation.types_internal import EvaluationContext
from toetsregels.runtime_contract import EvaluatorType, ResultStatus, RuleRecord
from validation.additional_patterns import get_additional_patterns

__all__ = [
    "METADATA_BEDOELING",
    "METADATA_BRONNEN",
    "METADATA_CONFIGURATIE",
    "METADATA_DOCUMENT",
    "DecisionRuleAssessmentEvaluator",
]

METADATA_BEDOELING = "int02_bedoeling"
METADATA_BRONNEN = "int02_bronnen"
METADATA_CONFIGURATIE = "int02_configuratie"
METADATA_DOCUMENT = "int02_document"
_CONTEXTVELDEN = ("organisatorische_context", "juridische_context", "wettelijke_basis")

# Uitvoeringsteksten voor `parts[].action`: geen sjabloon uit synthese §4 en
# nooit een herschrijfopdracht (B6: geen INT-02-herstel).
_ACTIE = {
    "pass": "Geen INT-02-actie nodig; andere toetsregels zijn hiermee niet beoordeeld.",
    "fail": "Weeg de passage mee in de integrale expertbeoordeling; de tekst is niet gewijzigd.",
    "insufficient_information": "Beantwoord de vraag en laat INT-02 opnieuw beoordelen.",
    "not_assessed": "Laat INT-02 beoordelen.",
    "historical": "Laat INT-02 opnieuw beoordelen voor de actuele versie.",
    "not_applicable": "Geen INT-02-actie; er is geen oordeel over de definitiekern.",
    "error": "Toets opnieuw; er is geen inhoudelijk oordeel.",
}


class DecisionRuleAssessmentEvaluator:
    """INT-02 (O2): een bewaard oordeel toepassen op de actuele invoer, zonder cijfer."""

    evaluator_type = EvaluatorType.DECISION_RULE_ASSESSMENT

    def evaluate(
        self, record: RuleRecord, ctx: EvaluationContext, deps: EvaluationDeps
    ) -> EvaluationOutcome:
        metadata = ctx.metadata if isinstance(ctx.metadata, dict) else {}
        # Terugval op raw_text alleen bij een ontbrekende sleutel; een aanwezige
        # niet-tekst gaat naar de WP1-validatie en wordt `error` (WP3-R1).
        kern = metadata.get("record_text", ctx.raw_text)
        signalen = _signalen(record, kern if isinstance(kern, str) else "", deps)
        try:
            invoer = _huidige_invoer(ctx, metadata, kern)
        except Int02ContractError:
            return _naar_outcome(record, deps, _fout(), None, signalen, None)
        document = metadata.get(METADATA_DOCUMENT)
        configuratie = metadata.get(METADATA_CONFIGURATIE)
        if configuratie is None:
            ontbreekt = ontbrekende_invoer(invoer)
            if ontbreekt:
                actualiteit = Actualiteit(
                    "not_evaluated",
                    None,
                    MELDING_NE.replace("{kern/context}", ontbreekt),
                )
            else:
                actualiteit = Actualiteit(
                    "review_required", "not_assessed", MELDING_NIET_BEOORDEELD
                )
            return _naar_outcome(record, deps, actualiteit, None, signalen, ontbreekt)
        if not isinstance(configuratie, Configuratie):
            return _naar_outcome(record, deps, _fout(), None, signalen, None)
        try:
            actualiteit = toets_actualiteit(document, invoer, configuratie)
        except Int02ContractError:
            return _naar_outcome(record, deps, _fout(), None, signalen, None)
        aanvaard = (
            document
            if isinstance(document, Beoordelingsdocument)
            and actualiteit.status not in ("not_evaluated", "error")
            else None
        )
        return _naar_outcome(
            record, deps, actualiteit, aanvaard, signalen, ontbrekende_invoer(invoer)
        )


def _fout() -> Actualiteit:
    return Actualiteit("error", None, MELDING_E)


def _lijst_of_leeg(waarde: Any) -> Any:
    """None is leeg; elk ander type gaat ongewijzigd naar de WP1-validatie."""
    return [] if waarde is None else waarde


def _huidige_invoer(
    ctx: EvaluationContext, metadata: dict[str, Any], kern: Any
) -> Int02Invoer:
    """De exacte actuele invoer; WP1 weigert elk ongeldig veld."""
    return maak_invoer(
        begrip=ctx.begrip,
        kern=kern,
        bedoeling=metadata.get(METADATA_BEDOELING),
        bronnen=_lijst_of_leeg(metadata.get(METADATA_BRONNEN)),
        **{veld: _lijst_of_leeg(metadata.get(veld)) for veld in _CONTEXTVELDEN},
    )


def _signalen(record: RuleRecord, kern: str, deps: EvaluationDeps) -> tuple[str, ...]:
    """Recordpatronen die op de actuele kern vuren — leeshulp, geen oordeel.

    Compileerbaarheid is bij het laden afgedwongen (`build_rule_record`); een
    fout hier loopt naar de ERROR-grens van de service (DEF-667).
    """
    code = record.rule_id.upper()
    sleutel = f"__int02o2__{code}"
    gecompileerd = deps.pattern_cache.get(sleutel)
    if gecompileerd is None:
        patronen = list(record.get("herkenbaar_patronen", []) or [])
        extra = get_additional_patterns(code)
        if extra:
            patronen = list(dict.fromkeys([*patronen, *extra]))
        gecompileerd = [re.compile(p, re.IGNORECASE) for p in patronen]
        deps.pattern_cache[sleutel] = gecompileerd
    return tuple(patroon.pattern for patroon in gecompileerd if patroon.search(kern))


def _actualiteit_label(actualiteit: Actualiteit) -> str | None:
    if actualiteit.status in ("not_evaluated", "error"):
        return None
    if actualiteit.reden in ("historical", "not_assessed"):
        return actualiteit.reden
    return "current"


def _actie(actualiteit: Actualiteit, ontbreekt: str | None) -> str:
    if actualiteit.status == "not_evaluated":
        return f"Lever de ontbrekende {ontbreekt or 'invoer'} aan en toets opnieuw."
    return _ACTIE[actualiteit.reden or actualiteit.status]


def _naar_outcome(
    record: RuleRecord,
    deps: EvaluationDeps,
    actualiteit: Actualiteit,
    document: Beoordelingsdocument | None,
    signalen: tuple[str, ...],
    ontbreekt: str | None,
) -> EvaluationOutcome:
    actie = _actie(actualiteit, ontbreekt)
    detail: dict[str, Any] = {
        "status": actualiteit.status,
        "score": None,
        "contract_version": CONTRACTVERSIE,
        "fingerprint": None,
        "parts": [
            {
                "id": "beoordeling",
                "status": actualiteit.status,
                "evidence": None,
                "context_value": None,
                "field": None,
                "position": None,
                "reason": actualiteit.melding,
                "action": actie,
            }
        ],
        "review": {"actuality": _actualiteit_label(actualiteit)},
        "assessment": document.als_dict() if document is not None else None,
        "signals": list(signalen),
    }
    status = ResultStatus(actualiteit.status)
    if status is ResultStatus.PASS:
        return EvaluationOutcome(
            status=status, score=None, metadata={"rule_result": detail}
        )
    if status is ResultStatus.FAIL:
        return EvaluationOutcome(
            status=status,
            score=None,
            violation=bouw_violation(
                record,
                deps,
                melding=actualiteit.melding,
                suggestie=actie,
                metadata={"advisory": True, "contract_version": CONTRACTVERSIE},
                severity=ADVISORY_SEVERITY,
                severity_level=ADVISORY_SEVERITY_LEVEL,
            ),
            metadata={"rule_result": detail},
        )
    metadata: dict[str, Any] = {"rule_result": detail}
    if status is ResultStatus.REVIEW_REQUIRED:
        metadata["signals"] = list(signalen)
    return EvaluationOutcome(
        status=status, score=None, reason=actualiteit.melding, metadata=metadata
    )
