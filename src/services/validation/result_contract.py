"""Runstatus van een validatieresultaat (DEF-624, contract 2.0.0).

Eén plek die bepaalt of een resultaat een uitgevoerde run vertegenwoordigt.
Tot 1.4.0 declareerde het schema `default: validated` en las elke consument
de discriminator zelf: de adapter kopieerde alleen een aanwezige status, de
gedeelde UI stopte alleen bij een expliciete `validation_unknown`, en de
opslag-, hertoets- en exportgrenzen keken alleen naar `is_acceptable`. Een
resultaat zónder status - een legacy object, een kale dict, een stub - gold
overal als geldig runbewijs, tot en met een hoge score en een groene gate.

Hier geldt de legacy-invoergrens: afwezig, null of ongeldig wordt
`validation_unknown` met een concrete contractreden. Een bestaande, geldige
status blijft wat hij is. Er wordt nooit een run verzonnen (`validated` komt
uitsluitend van een producent die werkelijk evalueerde) en er wordt nooit
een readiness verzonnen (die is bij een ontbrekend contract niet gemeten).

De helpers werken op een kopie en zijn idempotent: `met_expliciete_runstatus`
op zijn eigen uitvoer verandert niets meer.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from services.validation.interfaces import (
    UNKNOWN_REASON_CONTRACT_STATUS_INVALID,
    UNKNOWN_REASON_CONTRACT_STATUS_MISSING,
    UNKNOWN_REASON_RULESET_INCOMPLETE,
    UNKNOWN_REASON_VALIDATION_ERROR,
    VALIDATION_STATUS_UNKNOWN,
    VALIDATION_STATUS_VALIDATED,
)

__all__ = [
    "BEKENDE_REDENEN",
    "CONTRACTVELDEN",
    "READINESS_VELDEN",
    "Runstatus",
    "bepaal_runstatus",
    "is_geldige_readiness",
    "is_uitgevoerde_run",
    "lees_veld",
    "met_expliciete_runstatus",
    "neem_contractvelden_over",
]

#: Contractvelden die een conversie doordraagt wanneer de bron ze werkelijk
#: draagt (DEF-624, AC 2): (veld, geldig type of None voor "elke waarde",
#: nullable). `validation_status` reist ruw mee, ook als hij ongeldig is:
#: `met_expliciete_runstatus` bepaalt daarna zelf ontbrekend/ongeldig en
#: vervangt hem door de canonieke waarde. `source_assessment` is nullable:
#: een expliciete None is de vastlegging "geen bronbeoordeling" en mag niet
#: verdwijnen; ontbreekt het veld, dan wordt het niet verzonnen.
CONTRACTVELDEN: tuple[tuple[str, type | None, bool], ...] = (
    ("validation_status", None, False),
    ("unknown_reason", str, False),
    ("validation_readiness", dict, False),
    ("rule_statuses", dict, False),
    ("rule_results", dict, False),
    ("review_required", list, False),
    ("evaluation_coverage", dict, False),
    ("source_assessment", dict, True),
    ("acceptance_gate", dict, False),
)

#: De contractuele redenen; een andere waarde in `unknown_reason` telt niet
#: als reden (en wordt niet vervangen: de UI meldt hem generiek).
BEKENDE_REDENEN: frozenset[str] = frozenset(
    {
        UNKNOWN_REASON_RULESET_INCOMPLETE,
        UNKNOWN_REASON_CONTRACT_STATUS_MISSING,
        UNKNOWN_REASON_CONTRACT_STATUS_INVALID,
        UNKNOWN_REASON_VALIDATION_ERROR,
    }
)


#: De vijf verplichte readinessvelden (schema: `validation_readiness`,
#: additionalProperties false). Zodra het object aanwezig is, is het volledig.
READINESS_VELDEN: frozenset[str] = frozenset(
    {
        "ready",
        "expected_total",
        "loaded_total",
        "missing_rule_ids",
        "unexpected_rule_ids",
    }
)


def _is_heel_getal(waarde: Any) -> bool:
    """Een JSON-integer: int (geen bool) of een float zonder fractie."""
    if isinstance(waarde, bool):
        return False
    if isinstance(waarde, int):
        return True
    return isinstance(waarde, float) and waarde.is_integer()


def is_geldige_readiness(waarde: Any) -> bool:
    """Of `waarde` de readinessvorm van het schema heeft (DEF-624).

    Spiegelt uitsluitend het `validation_readiness`-subschema: precies de
    vijf velden, `ready` bool, beide totalen niet-negatieve gehele getallen,
    beide ID-lijsten lijsten van strings. Geen algemene validator; de check
    bestaat zodat een fabriek of geldigheidsclaim geen halve of verzonnen
    readiness kan goedkeuren die het schema weigert.
    """
    if not isinstance(waarde, Mapping) or set(waarde) != READINESS_VELDEN:
        return False
    if not isinstance(waarde["ready"], bool):
        return False
    for sleutel in ("expected_total", "loaded_total"):
        if not _is_heel_getal(waarde[sleutel]) or waarde[sleutel] < 0:
            return False
    for sleutel in ("missing_rule_ids", "unexpected_rule_ids"):
        ids = waarde[sleutel]
        if not isinstance(ids, list) or not all(isinstance(rid, str) for rid in ids):
            return False
    return True


@dataclass(frozen=True)
class Runstatus:
    """De uitkomst van de statusbepaling.

    `reason` is None bij `validated`, en bij een expliciete `validation_unknown`
    zonder (geldige) reden - dan wordt er geen reden verzonnen.
    """

    status: str
    reason: str | None

    @property
    def uitgevoerd(self) -> bool:
        return self.status == VALIDATION_STATUS_VALIDATED


def lees_veld(result: Any, veld: str) -> tuple[bool, Any]:
    """(aanwezig, waarde) van `veld` uit een mapping of een object.

    Aanwezigheid wordt bepaald vóór enige typecontrole, zodat een werkelijk
    aanwezige maar ongeldige waarde (True, 1, []) nooit als "afwezig" wordt
    gemeld en een expliciete None (nullable contractveld) niet verdwijnt.

    Op de objectkant telt alleen een werkelijk gedragen attribuut: een sleutel
    in de instantie-`__dict__`, een dataclassveld, een `__slots__`-slot of een
    op de klasse gedefinieerd attribuut/property. Een `Mock` verzint elk
    attribuut dat je opvraagt (en zet dat niet in `__dict__`); dat verzinsel
    telt niet. Een expliciet op een Mock gezette waarde staat wél in
    `__dict__` en telt dus wel.
    """
    if isinstance(result, Mapping):
        return (veld in result), result.get(veld)
    klasse = type(result)
    if (
        veld in getattr(result, "__dict__", {})
        or veld in getattr(klasse, "__dataclass_fields__", {})
        or hasattr(klasse, veld)
        or (veld in getattr(klasse, "__slots__", ()) and hasattr(result, veld))
    ):
        return True, getattr(result, veld, None)
    return False, None


def _lees(result: Any, veld: str) -> Any:
    """De waarde van `veld` (None als afwezig); alleen voor de statusvelden."""
    return lees_veld(result, veld)[1]


def neem_contractvelden_over(doel: dict[str, Any], bron: Any) -> None:
    """Kopieer de `CONTRACTVELDEN` die `bron` (mapping of object) werkelijk draagt.

    Een aanwezige waarde van het verwachte type reist mee; een aanwezige None
    alleen bij een nullable veld; een aanwezige waarde van een ander type wordt
    overgeslagen (behalve `validation_status`, die ruw meegaat zodat de
    statusbepaling "ongeldig" van "afwezig" kan onderscheiden). Een afwezig
    veld wordt nooit verzonnen.
    """
    for veld, verwacht_type, nullable in CONTRACTVELDEN:
        aanwezig, waarde = lees_veld(bron, veld)
        if not aanwezig:
            continue
        if (
            verwacht_type is None
            or isinstance(waarde, verwacht_type)
            or (nullable and waarde is None)
        ):
            doel[veld] = waarde


def bepaal_runstatus(result: Any) -> Runstatus:
    """Bepaal de runstatus van een resultaat (dict of object), fail-closed.

    - `validated`            -> (validated, None)
    - `validation_unknown`   -> (validation_unknown, de aanwezige reden of None)
    - afwezig of None        -> (validation_unknown, contract_status_missing)
    - iedere andere waarde   -> (validation_unknown, contract_status_invalid)

    Afwezig en null worden vóór elke typecontrole onderscheiden van een
    aanwezige ongeldige waarde (`lees_veld`), zodat dict-, object- en
    legacyconversie dezelfde reden opleveren.
    """
    status = _lees(result, "validation_status")
    if status is None:
        return Runstatus(
            VALIDATION_STATUS_UNKNOWN, UNKNOWN_REASON_CONTRACT_STATUS_MISSING
        )
    if status == VALIDATION_STATUS_VALIDATED:
        return Runstatus(VALIDATION_STATUS_VALIDATED, None)
    if status == VALIDATION_STATUS_UNKNOWN:
        reden = _lees(result, "unknown_reason")
        return Runstatus(
            VALIDATION_STATUS_UNKNOWN,
            reden if isinstance(reden, str) and reden else None,
        )
    return Runstatus(VALIDATION_STATUS_UNKNOWN, UNKNOWN_REASON_CONTRACT_STATUS_INVALID)


def is_uitgevoerde_run(result: Any) -> bool:
    """Alleen een expliciete `validated` is een uitgevoerde run."""
    return bepaal_runstatus(result).uitgevoerd


def met_expliciete_runstatus(result: Mapping[str, Any]) -> dict[str, Any]:
    """Een nieuw dict met een expliciete, contractuele runstatus.

    Bij `validated` verandert er niets aan de inhoud. Bij een onbekende run
    worden de fail-closed placeholders uit het contract afgedwongen:
    `is_acceptable` False en een aanwezige numerieke `overall_score` 0.0.
    Een `None`-score blijft None (niet beschikbaar is geen nul, DEF-622), een
    onleesbare score wordt None (niet beschikbaar, geen verzonnen nul) en een
    ontbrekende score wordt niet toegevoegd. Alle overige velden
    (regeluitkomsten, dekking, reviewplicht, bronbeoordeling, readiness)
    reizen ongewijzigd mee: zij blijven beschikbaar voor uitleg, maar het
    resultaat kan geen oordeel meer dragen. De bron wordt niet gemuteerd.
    """
    uit: dict[str, Any] = dict(result)
    runstatus = bepaal_runstatus(result)
    uit["validation_status"] = runstatus.status
    if runstatus.uitgevoerd:
        return uit
    if runstatus.reason is not None:
        uit["unknown_reason"] = runstatus.reason
    uit["is_acceptable"] = False
    score = uit.get("overall_score")
    if score is not None:
        try:
            float(score)
        except (TypeError, ValueError):
            uit["overall_score"] = None
        else:
            uit["overall_score"] = 0.0
    return uit
