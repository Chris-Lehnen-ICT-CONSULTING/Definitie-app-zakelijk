"""De expertacties op de ESS-05-burenlijst (DEF-768 WP4, besluiten K-1/K-2).

Zuivere functies: ze krijgen de opgeslagen burenlijst (met besluiten) en
geven een nieuwe lijst terug; de invoer wordt nooit gemuteerd. De UI roept
ze aan en slaat het resultaat op via `ess05_buren`; de persistentielaag
valideert en bewaart de vorige lijst in de historie.

- Elk besluit draagt `actor` en `at`; afwijzen en een lege ruimte vereisen
  een `grond`.
- Een repository-buur die nog niet in de opgeslagen lijst staat, krijgt bij
  een besluit een eigen regel (`id` = `repository:<db-id>`); zijn term en
  definitie worden bij elke toetsing opnieuw uit de database gelezen.
- De bevestigingsstatus telt niet in de vingerafdruk: een besluit vraagt
  geen nieuwe modelaanroep, wel een nieuwe (lokale) samenvoeging.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from copy import deepcopy
from typing import Any

from domain.ess05.contract import (
    CONTRACTVERSIE,
    OngeldigeBurenlijstError,
    bronverwijzing,
    buur_id,
    normaliseer_buren,
)

__all__ = [
    "bevestig_buur",
    "bevestig_lege_ruimte",
    "neem_voorstel_over",
    "voeg_buur_toe",
    "wijs_buur_af",
]


def _tekst(waarde: Any) -> str:
    return waarde.strip() if isinstance(waarde, str) else ""


def _kopie(opgeslagen: Iterable[Mapping[str, Any]] | None) -> list[dict[str, Any]]:
    return [deepcopy(dict(item)) for item in (opgeslagen or ())]


def _vereis(waarde: Any, naam: str) -> str:
    schoon = _tekst(waarde)
    if not schoon:
        msg = f"een ESS-05-besluit vereist een {naam}"
        raise ValueError(msg)
    return schoon


def _besluit(
    opgeslagen: Iterable[Mapping[str, Any]] | None,
    actief: Iterable[Mapping[str, Any]],
    id_: str,
    wijziging: Mapping[str, Any],
) -> list[dict[str, Any]]:
    lijst = _kopie(opgeslagen)
    for item in lijst:
        if _tekst(item.get("id")) == id_:
            item.update(wijziging)
            return lijst
    for buur in actief:
        if _tekst(buur.get("id")) == id_:
            nieuw = {
                "id": id_,
                "term": buur.get("term"),
                "definitie": buur.get("definitie"),
                "herkomst": buur.get("herkomst"),
                "bevestigd": bool(buur.get("bevestigd")),
            }
            nieuw.update(wijziging)
            lijst.append(nieuw)
            return lijst
    msg = f"buur {id_!r} staat niet in de burenlijst"
    raise OngeldigeBurenlijstError(msg)


def bevestig_buur(
    opgeslagen: Iterable[Mapping[str, Any]] | None,
    actief: Iterable[Mapping[str, Any]],
    id_: str,
    *,
    actor: str,
    at: str,
) -> list[dict[str, Any]]:
    """Bevestig dat deze buur een verwant begrip is dat de definitie moet uitsluiten."""
    return _besluit(
        opgeslagen,
        actief,
        id_,
        {
            "bevestigd": True,
            "afgewezen": False,
            "actor": _vereis(actor, "actor"),
            "at": _vereis(at, "tijdstip"),
        },
    )


def wijs_buur_af(
    opgeslagen: Iterable[Mapping[str, Any]] | None,
    actief: Iterable[Mapping[str, Any]],
    id_: str,
    *,
    actor: str,
    at: str,
    grond: str,
) -> list[dict[str, Any]]:
    """Wijs een buur gemotiveerd af: hij gaat niet meer mee en keert niet terug."""
    return _besluit(
        opgeslagen,
        actief,
        id_,
        {
            "bevestigd": False,
            "afgewezen": True,
            "actor": _vereis(actor, "actor"),
            "at": _vereis(at, "tijdstip"),
            "grond": _vereis(grond, "grond"),
        },
    )


def _voeg_toe(
    opgeslagen: Iterable[Mapping[str, Any]] | None, nieuw: dict[str, Any]
) -> list[dict[str, Any]]:
    lijst = _kopie(opgeslagen)
    sleutel = _tekst(nieuw.get("term")).casefold()
    if not sleutel:
        msg = "een buur heeft een term nodig"
        raise OngeldigeBurenlijstError(msg)
    if any(_tekst(item.get("term")).casefold() == sleutel for item in lijst):
        msg = f"{nieuw['term']!r} staat al in de burenlijst"
        raise OngeldigeBurenlijstError(msg)
    lijst.append(nieuw)
    normaliseer_buren([{**item, "afgewezen": False} for item in lijst])
    return lijst


def voeg_buur_toe(
    opgeslagen: Iterable[Mapping[str, Any]] | None,
    term: str,
    definitie: str | None,
    *,
    actor: str,
    at: str,
) -> list[dict[str, Any]]:
    """Een door de gebruiker genoemd verwant begrip: herkomst `gebruiker`, bevestigd."""
    schoon = _tekst(term)
    return _voeg_toe(
        opgeslagen,
        {
            "id": buur_id("gebruiker", schoon),
            "term": schoon,
            "definitie": _tekst(definitie) or None,
            "herkomst": "gebruiker",
            "bevestigd": True,
            "actor": _vereis(actor, "actor"),
            "at": _vereis(at, "tijdstip"),
        },
    )


def neem_voorstel_over(
    opgeslagen: Iterable[Mapping[str, Any]] | None,
    voorstel: Mapping[str, Any],
    *,
    actor: str,
    at: str,
    bevestigd: bool = False,
) -> list[dict[str, Any]]:
    """Neem een bron- of modelvoorstel over; standaard als onbevestigde buur (K-1).

    De herkomst blijft die van het voorstel (een modelvoorstel blijft `model`);
    een bronverwijzing (`source_id` + letterlijk `quote`) gaat apart mee. Een
    halve verwijzing wordt fail-closed geweigerd door `normaliseer_buren`.
    """
    herkomst = voorstel.get("herkomst")
    if herkomst not in ("bron", "model"):
        msg = f"alleen bron- of modelvoorstellen kunnen worden overgenomen, niet {herkomst!r}"
        raise OngeldigeBurenlijstError(msg)
    term = _tekst(voorstel.get("term"))
    nieuw: dict[str, Any] = {
        "id": _tekst(voorstel.get("id")) or buur_id(herkomst, term),
        "term": term,
        "definitie": _tekst(voorstel.get("definitie")) or None,
        "herkomst": herkomst,
        "bevestigd": bool(bevestigd),
        "actor": _vereis(actor, "actor"),
        "at": _vereis(at, "tijdstip"),
    }
    verwijzing = bronverwijzing(voorstel)
    if verwijzing:
        nieuw.update(verwijzing)
    elif voorstel.get("source_id") is not None or voorstel.get("quote") is not None:
        nieuw.update(source_id=voorstel.get("source_id"), quote=voorstel.get("quote"))
    return _voeg_toe(opgeslagen, nieuw)


def bevestig_lege_ruimte(
    fingerprint: str, *, grond: str, actor: str, at: str
) -> dict[str, Any]:
    """De deskundige bevestiging dat er in deze context geen verwante begrippen zijn (K-2).

    Gebonden aan de vingerafdruk van term, tekst, context, bedoelde betekenis,
    bronnen en de lege burenlijst; vervalt vanzelf bij elke wijziging daarvan.
    """
    return {
        "fingerprint": _vereis(fingerprint, "vingerafdruk"),
        "contract_version": CONTRACTVERSIE,
        "grond": _vereis(grond, "grond"),
        "actor": _vereis(actor, "actor"),
        "at": _vereis(at, "tijdstip"),
    }
