"""DUP_01 — duplicaatdetectie op begrip plus genormaliseerde context (DEF-674).

Deze evaluator draagt wat eerder in `context_metadata` (CON-01) zat. Dat was
een pragmatische plek — DEF-672 moest de controle snel bedraden — maar niet de
contractuele. De records wijzen ondubbelzinnig naar DUP_01:

| | CON-01 | DUP_01 |
| --- | --- | --- |
| toetsvraag | Is de betekenis contextspecifiek geformuleerd, zonder de context letterlijk te noemen? | Bestaat deze definitie nog niet in de database? |
| evaluator | `context_metadata` | `duplicate_detection` |
| required_inputs | `definition_text`, `term` | + `definition_repository` |
| executability | `deterministic` | `repository` |

CON-01 toetst de formulering, DUP_01 de database. Door de controle hierheen te
verplaatsen kan CON-01 `deterministic` en `scored` blijven — zijn patroontoets
blijft dus meetellen in de score, precies wat DEF-672 wilde behouden — terwijl
DUP_01 zijn eigen `fail` draagt in plaats van een waarschuwing die buiten de
statusboekhouding om reisde.

De uitkomst is een echte `EvaluationOutcome`. De vorige route stashte de
bevinding in `ctx.metadata` en liet de service haar in een `try/except` met het
commentaar `(best-effort)` oppikken; `rule_statuses["CON-01"]` bleef daardoor
`pass` terwijl er een violation in de lijst stond.
"""

from __future__ import annotations

import logging
from typing import Any

from domain.context.normalisatie import contextsleutel
from services.validation.evaluators.base import (
    EvaluationDeps,
    EvaluationOutcome,
    falende_uitkomst,
)
from services.validation.types_internal import EvaluationContext
from toetsregels.runtime_contract import EvaluatorType, RuleRecord

logger = logging.getLogger(__name__)

__all__ = [
    "CONTEXT_VELDEN",
    "DUPLICATE_LOOKUP_METHODE",
    "DuplicateDetectionEvaluator",
]

# De publieke repository-capability die de duplicaatcontrole nodig heeft. Eén
# constante, zodat de guard en de test niet elk hun eigen naam dragen. Was een
# privémethode die in DEF-176 als dode code is verwijderd, waardoor de controle
# in productie nooit liep (DEF-672).
DUPLICATE_LOOKUP_METHODE = "find_duplicate_candidates"

CONTEXT_VELDEN: tuple[str, str, str] = (
    "organisatorische_context",
    "juridische_context",
    "wettelijke_basis",
)

_MELDING = "Bestaande definitie met dezelfde context gevonden"
_SUGGESTIE = (
    "Overweeg de bestaande definitie te hergebruiken of pas de context/lemma "
    "aan om duplicatie te voorkomen."
)


class DuplicateDetectionEvaluator:
    """Bestaat deze definitie nog niet in de database?"""

    evaluator_type = EvaluatorType.DUPLICATE_DETECTION

    def evaluate(
        self, record: RuleRecord, ctx: EvaluationContext, deps: EvaluationDeps
    ) -> EvaluationOutcome:
        """Zoek een duplicaat op begrip plus genormaliseerde context.

        Bewust zonder foutafhandeling (DEF-667): een aanwezige repository die
        faalt levert een míslukte controle op, geen geslaagde. De uitzondering
        loopt door naar de ERROR-grens in
        `ModularValidationService._evaluate_via_registry`.

        Zonder begrip of zonder enige context is er geen duplicaatidentiteit om
        op te matchen. Die gevallen leveren `not_evaluated`, niet `pass`: deze
        regel beantwoordt letterlijk "Bestaat deze definitie nog niet in de
        database?", en dat met `pass` beantwoorden zonder de database te
        bevragen is een default-pass — precies wat DEF-624 sluit.

        Op CON-01 was dezelfde vroege return onschadelijk, want daar ging de
        `pass` over de patroontoets. Bij de verhuizing verandert de betekenis
        van die uitkomst, dus verandert hier ook het antwoord.
        """
        begrip = ctx.begrip or None
        if not begrip:
            return EvaluationOutcome.not_evaluated(
                "geen begrip om duplicaatidentiteit op te bepalen"
            )

        metadata = ctx.metadata or {}
        contexten = [metadata.get(veld) or [] for veld in CONTEXT_VELDEN]
        if not any(contexten):
            # Term plus genormaliseerde context bepaalt duplicaatidentiteit
            # (ADR-001). Zonder enige context is die identiteit onvolledig; het
            # afdwingen van verplichte context is DEF-622.
            return EvaluationOutcome.not_evaluated(
                "geen contextwaarden; duplicaatidentiteit is term plus context"
            )

        if not hasattr(deps.repository, DUPLICATE_LOOKUP_METHODE):
            # Een repository zonder de publieke capability is een
            # bedradingsdefect. `not_evaluated` in plaats van `pass`: de
            # controle heeft niet gelopen, dus zij is niet geslaagd. Dat kan
            # hier veilig, anders dan bij CON-01, omdat DUP_01 buiten de score
            # valt en de invoergate deze regel al bewaakt.
            logger.error(
                "Duplicaatcontrole overgeslagen: repository %s biedt geen %s() "
                "(DEF-672/DEF-674)",
                type(deps.repository).__name__,
                DUPLICATE_LOOKUP_METHODE,
                extra={
                    "component": "evaluators.duplicate_detection",
                    "rule_id": record.rule_id,
                    "repository_type": type(deps.repository).__name__,
                    "ontbrekende_methode": DUPLICATE_LOOKUP_METHODE,
                },
            )
            return EvaluationOutcome.not_evaluated(
                f"repository biedt geen {DUPLICATE_LOOKUP_METHODE}()"
            )

        gevonden = self._zoek_duplicaat(deps.repository, begrip, contexten, metadata)
        if gevonden is None:
            return EvaluationOutcome.passed()

        # De ernst volgt hier niet uit het record maar uit de invoer: een
        # bewust geforceerd duplicaat is een expliciete schending en weegt
        # zwaarder dan een gesignaleerd duplicaat dat de gebruiker nog kan
        # herstellen. Die nuance bestond al in DEF-672 en blijft behouden.
        geforceerd = _is_geforceerd(metadata)
        return falende_uitkomst(
            record,
            deps,
            melding=_MELDING,
            suggestie=_SUGGESTIE,
            metadata={
                "existing_definition_id": gevonden["id"],
                "status": gevonden["status"],
                "force_duplicate": geforceerd,
            },
            severity="error" if geforceerd else "warning",
            severity_level="high" if geforceerd else "medium",
        )

    @staticmethod
    def _zoek_duplicaat(
        repository: Any,
        begrip: str,
        contexten: list[Any],
        metadata: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Match op begrip plus de drie genormaliseerde contextlijsten (DEF-672).

        De repository begrenst de kandidaten op begrip en status; hier beslist
        de genormaliseerde gestructureerde context. Beide zijden gaan door
        dezelfde `contextsleutel`, dus volgorde, hoofdletters, whitespace en
        duplicaten maken geen verschil — en een bestaand record met een
        niet-canonieke schrijfwijze wordt gewoon herkend.
        """
        gezocht = tuple(contextsleutel(lijst) for lijst in contexten)
        categorie = metadata.get("categorie") or metadata.get("ontologische_categorie")

        for kandidaat in repository.find_duplicate_candidates(begrip):
            kandidaat_context = (
                kandidaat.organisatorische_context,
                kandidaat.juridische_context,
                kandidaat.wettelijke_basis,
            )
            if kandidaat_context != gezocht:
                continue
            kandidaat_categorie = getattr(kandidaat, "categorie", None)
            if categorie and kandidaat_categorie:
                if str(kandidaat_categorie).casefold() != str(categorie).casefold():
                    continue
            return {
                "id": getattr(kandidaat, "id", None),
                "status": getattr(kandidaat, "status", None),
            }
        return None


def _is_geforceerd(metadata: dict[str, Any]) -> bool:
    try:
        opties = metadata.get("options")
        return bool(
            metadata.get("force_duplicate")
            or (isinstance(opties, dict) and opties.get("force_duplicate"))
        )
    except (TypeError, AttributeError) as exc:
        logger.debug("force_duplicate check gefaald, default False: %s", exc)
        return False
