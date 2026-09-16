"""Regels waarbij een signaal juist aanwézig moet zijn (DEF-606).

ESS-03 en ESS-05 gebruiken hun patronen als positief signaal: een treffer is
gewenst, het ontbreken van het kenmerk is de violation. Het gedrag is
één-op-één overgenomen uit `ModularValidationService._evaluate_json_rule`
(de `_has_*`-helpers), zodat het invoeren van het evaluatorcontract geen
regelbetekenis verschuift.

ESS-04 stond hier eerder ook. Die regel is bij de reparatiepas op DEF-624a
naar `judgment_review` verplaatst: "toetsbaarheid" is een inhoudelijk
oordeel, en de indicator vuurde op elk getal of elke tijdsaanduiding
terwijl hij het eigen foute voorbeeld miste. De bijbehorende indicator is
hier verwijderd in plaats van als dode mapping te blijven staan.

CON-02 stond hier tot DEF-743: een bronwoord (`volgens`, `conform`, `wet`)
bewees geen bron en het ontbreken ervan was geen gebrek. De regel loopt nu
via `source_evidence` (broninhoudelijke beoordeling op de aangeleverde
bronnen); de indicator is verwijderd.

Bekende beperking, belegd bij DEF-624: deze helpers gebruiken eigen
hardgecodeerde patronen in plaats van de `herkenbaar_patronen` uit het
record zelf. Daardoor keurt ESS-05 zijn eigen goede voorbeeld af.
"""

from __future__ import annotations

import re

from services.validation.evaluators.base import (
    EvaluationDeps,
    EvaluationOutcome,
    Finding,
)
from services.validation.evaluators.generic import (
    uitkomst_van,
    verzamel_generieke_bevindingen,
)
from services.validation.types_internal import EvaluationContext
from toetsregels.runtime_contract import EvaluatorType, RuleRecord

__all__ = ["PositiveIndicatorEvaluator"]

_UNIEKE_IDENTIFICATIE = re.compile(
    r"\b(uniek|specifiek|identificeer|registratie|nummer|code|id|vin|isbn|kenteken)\b",
    re.IGNORECASE,
)
_ONDERSCHEIDEND_KENMERK = re.compile(
    r"\b(onderscheidt|specifiek|bijzonder|kenmerk|eigenschap)\b", re.IGNORECASE
)

# rule-ID -> (patroon dat aanwezig moet zijn, melding, suggestiereden)
_INDICATOREN: dict[str, tuple[re.Pattern[str], str, str]] = {
    "ESS-03": (
        _UNIEKE_IDENTIFICATIE,
        "Ontbreekt uniek identificatiecriterium",
        "unique_id",
    ),
    "ESS-05": (
        _ONDERSCHEIDEND_KENMERK,
        "Ontbreekt onderscheidend kenmerk",
        "distinguishing",
    ),
}


class PositiveIndicatorEvaluator:
    """Patroontreffers zijn hier een gewenst signaal, geen overtreding."""

    evaluator_type = EvaluatorType.POSITIVE_INDICATOR

    def evaluate(
        self, record: RuleRecord, ctx: EvaluationContext, deps: EvaluationDeps
    ) -> EvaluationOutcome:
        verzameld = verzamel_generieke_bevindingen(
            record, ctx, deps, patronen_zijn_positief=True
        )
        indicator = _INDICATOREN.get(record.rule_id.upper())
        if indicator is not None:
            patroon, melding, reden = indicator
            if not patroon.search(ctx.cleaned_text or ""):
                verzameld = verzameld.met((Finding(message=melding, reason=reden),))
        return uitkomst_van(verzameld)
