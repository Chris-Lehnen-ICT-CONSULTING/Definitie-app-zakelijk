"""CON-01 — contextspecifieke formulering (DEF-606).

Overgenomen uit `ModularValidationService`: de declaratieve patroontoets op
de contextspecifieke formulering.

De duplicaatcontrole die hier in DEF-672 bij is gezet, is in DEF-674 verhuisd
naar `duplicate_detection` (DUP_01). Dat is de regel die "Bestaat deze
definitie nog niet in de database?" toetst en die `definition_repository` als
vereiste invoer declareert. CON-01 toetst de formulering en blijft daardoor
`deterministic` en `scored`.

DEF-622 vervangt de vaste patroonlijst uit `CON-01.json` (24 patronen,
waaronder `\\bDJI\\b`, `\\bstrafrecht\\b` en `\\bjuridisch(e)?\\b`) door
detectie van de wérkelijk geselecteerde contextwaarden, en maakt van
"geen enkele context" een expliciete violation in plaats van een pass.
"""

from __future__ import annotations

from typing import Any

from domain.context.normalisatie import contextsleutel
from services.validation.evaluators.base import (
    EvaluationDeps,
    EvaluationOutcome,
)
from services.validation.evaluators.generic import (
    uitkomst_van,
    verzamel_generieke_bevindingen,
)
from services.validation.types_internal import EvaluationContext
from toetsregels.runtime_contract import EvaluatorType, RuleRecord

__all__ = [
    "CONTEXT_VELDEN",
    "ContextMetadataEvaluator",
    "normaliseer_contextlijst",
]

CONTEXT_VELDEN: tuple[str, str, str] = (
    "organisatorische_context",
    "juridische_context",
    "wettelijke_basis",
)


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
    """Contextspecifieke formulering — de patroontoets van CON-01.

    De duplicaatcontrole die hier eerder bij inzat is in DEF-674 verhuisd naar
    `duplicate_detection` (DUP_01). CON-01 toetst de formulering, DUP_01 de
    database; dat is ook wat beide records declareren. Daardoor kan CON-01
    `deterministic` en `scored` blijven en raakt hij de repository niet meer.
    """

    evaluator_type = EvaluatorType.CONTEXT_METADATA

    def evaluate(
        self, record: RuleRecord, ctx: EvaluationContext, deps: EvaluationDeps
    ) -> EvaluationOutcome:
        return uitkomst_van(verzamel_generieke_bevindingen(record, ctx, deps))
