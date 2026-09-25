"""Regels waarbij een signaal juist aanwézig moet zijn (DEF-606).

Een record met deze evaluator gebruikt zijn `herkenbaar_patronen` als
positief signaal: een treffer is gewenst. Aanvullende hardgecodeerde
indicatoren (`_INDICATOREN`) zijn er sinds DEF-768 niet meer; de strategie
blijft geregistreerd als contractwaarde, maar geen actief regelrecord
gebruikt haar nog.

ESS-05 stond hier tot DEF-768. De indicator (`onderscheidt`, `specifiek`,
`bijzonder`, `kenmerk`, `eigenschap`) keurde het eigen goede voorbeeld en
het ASTRA-goede voorbeeld af en liet lege trefwoordzinnen ("heeft een
onderscheidend kenmerk") slagen: een trefwoord bewijst geen onderscheid en
het ontbreken ervan is geen gebrek. De regel loopt nu via
`distinction_assessment` (AI-beoordeling per verwant begrip, `no_score`);
de indicator is verwijderd, geen alternatief levend pad.

ESS-04 stond hier eerder ook. Die regel is bij de reparatiepas op DEF-624a
naar `judgment_review` verplaatst: "toetsbaarheid" is een inhoudelijk
oordeel, en de indicator vuurde op elk getal of elke tijdsaanduiding
terwijl hij het eigen foute voorbeeld miste. De bijbehorende indicator is
hier verwijderd in plaats van als dode mapping te blijven staan.

CON-02 stond hier tot DEF-743: een bronwoord (`volgens`, `conform`, `wet`)
bewees geen bron en het ontbreken ervan was geen gebrek. De regel loopt nu
via `source_evidence` (broninhoudelijke beoordeling op de aangeleverde
bronnen); de indicator is verwijderd.

ESS-03 stond hier tot DEF-766. De woordindicator (`uniek`, `nummer`,
`code`, `id`, `isbn`, …) liet "Object met een nummer", een ontkende
uniciteitsclaim ("de code is niet uniek") en een ISBN-boekexemplaar slagen
en keurde een natuurlijke grens, een stoflezing en "registratienummer" af —
een woordtreffer bewijst geen individuatie en het ontbreken ervan is geen
gebrek (servicemeting 13×2 in het ESS-03-onderzoek van 18 september 2026).
De regel loopt nu via `judgment_review` met `no_score`; de indicator is
verwijderd, ook hier: geen alternatief levend pad.
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

# rule-ID -> (patroon dat aanwezig moet zijn, melding, suggestiereden).
# Bewust leeg sinds DEF-768 (zie de moduledocstring).
_INDICATOREN: dict[str, tuple[re.Pattern[str], str, str]] = {}


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
