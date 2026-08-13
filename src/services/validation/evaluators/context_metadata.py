"""CON-01 — contextspecifieke formulering en duplicaatsignaal (DEF-606).

Overgenomen uit `ModularValidationService`: het duplicaatsignaal op
begrip + genormaliseerde context, plus de declaratieve patroontoets.

DEF-622 vervangt de vaste patroonlijst uit `CON-01.json` (24 patronen,
waaronder `\\bDJI\\b`, `\\bstrafrecht\\b` en `\\bjuridisch(e)?\\b`) door
detectie van de wérkelijk geselecteerde contextwaarden, en maakt van
"geen enkele context" een expliciete violation in plaats van een pass.
"""

from __future__ import annotations

import logging
from typing import Any

from services.validation.evaluators.base import (
    EvaluationDeps,
    EvaluationOutcome,
)
from services.validation.evaluators.generic import (
    uitkomst_van,
    verzamel_generieke_bevindingen,
)
from services.validation.types_internal import EvaluationContext
from services.validation.violation_builder import category_for_rule
from toetsregels.runtime_contract import EvaluatorType, RuleRecord

logger = logging.getLogger(__name__)

__all__ = [
    "CONTEXT_VELDEN",
    "DUPLICATE_LOOKUP_METHODE",
    "DUPLICATE_STASH_KEY",
    "ContextMetadataEvaluator",
    "normaliseer_contextlijst",
]

# De repository-capability die de duplicaatcontrole nodig heeft. Eén constante,
# zodat de guard en de test niet elk hun eigen naam dragen (DEF-672).
DUPLICATE_LOOKUP_METHODE = "_get_all_definitions"

CONTEXT_VELDEN: tuple[str, str, str] = (
    "organisatorische_context",
    "juridische_context",
    "wettelijke_basis",
)
DUPLICATE_STASH_KEY = "__con01_dup_warnings__"


def normaliseer_contextlijst(waarden: Any) -> list[str]:
    """Trim, casefold, dedupliceer en sorteer een contextlijst.

    Volgorde-onafhankelijk en Unicode-correct; dit is de enige
    normalisatiefunctie die de contextinvariant, CON-01 en de
    duplicaatcontrole delen (besluit DEF-622).

    Geen foutafhandeling (DEF-667): een niet-itereerbare contextwaarde leverde
    eerder een lege lijst op, en dan vergelijkt een kandidaat met échte
    context ongelijk — het duplicaat verdwijnt en de regel slaagt. De
    `TypeError` loopt nu door naar de ERROR-grens.
    """
    return sorted({str(item or "").strip().casefold() for item in list(waarden or [])})


class ContextMetadataEvaluator:
    """Contextspecifieke formulering plus duplicaatsignaal op term+context."""

    evaluator_type = EvaluatorType.CONTEXT_METADATA

    def evaluate(
        self, record: RuleRecord, ctx: EvaluationContext, deps: EvaluationDeps
    ) -> EvaluationOutcome:
        self._signaleer_duplicaat(ctx, deps)
        return uitkomst_van(verzamel_generieke_bevindingen(record, ctx, deps))

    def _signaleer_duplicaat(
        self, ctx: EvaluationContext, deps: EvaluationDeps
    ) -> None:
        """Stash een duplicaatwaarschuwing die de service later oppikt.

        Bewust zonder foutafhandeling (DEF-667). Een aanwezige repository die
        faalt levert een míslukte controle op, geen geslaagde; de oude
        `except Exception` + warning liet CON-01 daarna gewoon op `pass`
        eindigen, waardoor een duplicaat ongemerkt kon worden vastgesteld.
        De uitzondering loopt nu door naar de ERROR-grens in
        `ModularValidationService._evaluate_via_registry`.

        De drie vroege returns hieronder zijn géén foutafhandeling maar
        expliciete niet-van-toepassing-gevallen: zonder repository, zonder
        begrip of zonder enige context is er niets te vergelijken. Dat gedrag
        blijft ongewijzigd — de UI valideert standaard zonder repository.
        """
        begrip = ctx.begrip or None
        if deps.repository is None or not begrip:
            return
        metadata = ctx.metadata or {}
        contexten = [metadata.get(veld) or [] for veld in CONTEXT_VELDEN]
        if not any(contexten):
            return
        if not hasattr(deps.repository, DUPLICATE_LOOKUP_METHODE):
            # DEF-672: dit is géén niet-van-toepassing-geval maar een
            # bedradingsdefect. De caller heeft om een duplicaat-bewuste
            # validatie gevraagd en krijgt die niet, terwijl CON-01 daarna een
            # gemeten `pass` meldt. Gemeten op de productieketen: de
            # geïnjecteerde `DefinitionRepository` heeft deze methode niet
            # (verwijderd in DEF-176), dus deze tak wordt élke aanroep genomen.
            #
            # Nog niet fail-closed op status: `error` zou met de errorblokkade
            # elke productievalidatie afkeuren, en `not_evaluated` zou CON-01
            # uit de automatische set halen. De echte bedrading vraagt een
            # genormaliseerde duplicaatquery over de persistentiegrens
            # (specificatiebesluit 2) en is belegd bij DEF-672/DEF-622. Tot dan
            # is de fout minstens niet meer stil.
            logger.error(
                "Duplicaatcontrole overgeslagen: repository %s biedt geen "
                "%s(); CON-01 rapporteert daardoor een patroontoets zonder "
                "duplicaatsignaal (DEF-672)",
                type(deps.repository).__name__,
                DUPLICATE_LOOKUP_METHODE,
                extra={
                    "component": "evaluators.context_metadata",
                    "rule_id": "CON-01",
                    "repository_type": type(deps.repository).__name__,
                    "ontbrekende_methode": DUPLICATE_LOOKUP_METHODE,
                    "issue": "DEF-672",
                },
            )
            return

        gevonden = self._zoek_duplicaat(deps.repository, begrip, contexten, metadata)
        if gevonden is None:
            return
        self._voeg_waarschuwing_toe(metadata, gevonden["id"], gevonden["status"])

    @staticmethod
    def _zoek_duplicaat(
        repository: Any,
        begrip: str,
        contexten: list[Any],
        metadata: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Exacte match op begrip plus de drie genormaliseerde contextlijsten."""
        genormaliseerd = [normaliseer_contextlijst(lijst) for lijst in contexten]
        categorie = metadata.get("categorie") or metadata.get("ontologische_categorie")
        begrip_norm = str(begrip).strip().casefold()

        for kandidaat in repository._get_all_definitions():
            if (
                getattr(kandidaat, "begrip", "") or ""
            ).strip().casefold() != begrip_norm:
                continue
            if any(
                normaliseer_contextlijst(getattr(kandidaat, veld, []))
                != genormaliseerd[index]
                for index, veld in enumerate(CONTEXT_VELDEN)
            ):
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

    @staticmethod
    def _voeg_waarschuwing_toe(
        metadata: dict[str, Any], gevonden_id: Any, gevonden_status: Any
    ) -> None:
        waarschuwingen = metadata.setdefault(DUPLICATE_STASH_KEY, [])
        geforceerd = _is_geforceerd(metadata)
        waarschuwingen.append(
            {
                "code": "CON-01",
                "severity": "error" if geforceerd else "warning",
                "severity_level": "high" if geforceerd else "medium",
                "message": "Bestaande definitie met dezelfde context gevonden",
                "description": "Bestaande definitie met dezelfde context gevonden",
                "rule_id": "CON-01",
                "category": category_for_rule("CON-01"),
                "metadata": {
                    "existing_definition_id": gevonden_id,
                    "status": gevonden_status,
                },
                "suggestion": (
                    "Overweeg de bestaande definitie te hergebruiken of pas de "
                    "context/lemma aan om duplicatie te voorkomen."
                ),
            }
        )


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
