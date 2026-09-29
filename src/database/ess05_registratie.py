"""De ESS-05-registratie in `generation_prompt_data` (DEF-768 WP5).

Zuivere functies voor de persistentielaag: vormcontrole van de structurele
invoer (vóór de transactie; een ValueError laat de hele opslag falen, niets
geschreven) en het samenvoegen ónder de lock met append-only historie. Geen
schema, geen kolom. Of een opgeslagen beoordeling nog bij het record hoort,
beslist de replay van het contract bij het lezen, niet deze module.

Invoersleutels (in `updates` of `Definition.metadata`):

- `ess05_assessment` — het beoordelingsdocument; gelijk = geen wijziging,
  anders gaat het vorige document naar `ess05_assessment_history`;
- `ess05_buren` — de volledige burenlijst met expertbesluiten; een gewijzigde
  lijst bewaart de vorige in `ess05_buren_history`;
- `ess05_lege_ruimte` — de deskundige bevestiging; `{}` wist haar bewust.

Afwezig of None = onaangeraakt.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from database.models import (
    ESS05_ASSESSMENT_HISTORY_KEY,
    ESS05_ASSESSMENT_KEY,
    ESS05_BUREN_HISTORIE_VELD,
    ESS05_BUREN_VELD,
    ESS05_LEGE_RUIMTE_IMPORT_VELD,
    ESS05_LEGE_RUIMTE_VELD,
)
from domain.ess05.contract import normaliseer_buren

__all__ = [
    "ESS05_INVOERSLEUTELS",
    "ess05_invoer_uit",
    "neutraliseer_geimporteerde_ess05",
    "valideer_ess05_invoer",
    "voeg_ess05_samen",
]

ESS05_INVOERSLEUTELS: tuple[str, ...] = (
    ESS05_ASSESSMENT_KEY,
    ESS05_BUREN_VELD,
    ESS05_LEGE_RUIMTE_VELD,
)
_TECHNISCHE_STATUSSEN = ("assessed", "error", "unavailable")
_LEGE_RUIMTE_VERPLICHT = ("fingerprint", "contract_version", "grond", "actor")


def _tekst(waarde: Any) -> str:
    return waarde.strip() if isinstance(waarde, str) else ""


def _valideer_beoordeling(invoer: Any) -> dict[str, Any]:
    if not isinstance(invoer, Mapping) or not _tekst(invoer.get("fingerprint")):
        msg = "ess05_assessment moet een dict met een niet-lege fingerprint zijn"
        raise ValueError(msg)
    if invoer.get("status") not in _TECHNISCHE_STATUSSEN:
        msg = f"ess05_assessment heeft een onbekende status {invoer.get('status')!r}"
        raise ValueError(msg)
    return deepcopy(dict(invoer))


def _valideer_buren(invoer: Any) -> list[dict[str, Any]]:
    """Elke buur, ook een afgewezen, moet een geldige buur zijn (fail-closed)."""
    if not isinstance(invoer, list):
        msg = "ess05_buren moet een lijst zijn"
        raise ValueError(msg)
    for index, item in enumerate(invoer):
        if not isinstance(item, Mapping):
            msg = f"ess05_buren[{index}] is geen object"
            raise ValueError(msg)
        if "afgewezen" in item and not isinstance(item["afgewezen"], bool):
            msg = f"ess05_buren[{index}]: afgewezen moet waar of onwaar zijn"
            raise ValueError(msg)
    # Een OngeldigeBurenlijstError is een ValueError.
    normaliseer_buren([{**item, "afgewezen": False} for item in invoer])
    return [deepcopy(dict(item)) for item in invoer]


def _valideer_lege_ruimte(invoer: Any) -> dict[str, Any]:
    if not isinstance(invoer, Mapping):
        msg = "ess05_lege_ruimte moet een dict zijn ({} = bewust gewist)"
        raise ValueError(msg)
    if not invoer:
        return {}
    ontbrekend = [v for v in _LEGE_RUIMTE_VERPLICHT if not _tekst(invoer.get(v))]
    if ontbrekend:
        msg = f"ess05_lege_ruimte mist {', '.join(ontbrekend)}"
        raise ValueError(msg)
    return deepcopy(dict(invoer))


_VALIDATOREN = {
    ESS05_ASSESSMENT_KEY: _valideer_beoordeling,
    ESS05_BUREN_VELD: _valideer_buren,
    ESS05_LEGE_RUIMTE_VELD: _valideer_lege_ruimte,
}


def valideer_ess05_invoer(invoer: Mapping[str, Any] | None) -> dict[str, Any]:
    """De gevalideerde ESS-05-invoer; sleutels met None/afwezig vallen weg."""
    return {
        sleutel: _VALIDATOREN[sleutel](invoer[sleutel])
        for sleutel in ESS05_INVOERSLEUTELS
        if invoer and invoer.get(sleutel) is not None
    }


def ess05_invoer_uit(updates: dict[str, Any]) -> dict[str, Any]:
    """Neem de structurele ESS-05-sleutels uit `updates` (geen kolommen) en valideer."""
    return valideer_ess05_invoer(
        {sleutel: updates.pop(sleutel, None) for sleutel in ESS05_INVOERSLEUTELS}
    )


def _vervang_met_historie(
    registratie: dict[str, Any],
    sleutel: str,
    historiesleutel: str,
    nieuw: Any,
    veld: str,
    *,
    versie: int,
    nu: str,
) -> bool:
    vorige = registratie.get(sleutel)
    if vorige == nieuw:
        return False
    historie = registratie.get(historiesleutel)
    historie = list(historie) if isinstance(historie, list) else []
    if vorige is not None:
        historie.append(
            {
                veld: deepcopy(vorige),
                "superseded_at": nu,
                "superseded_on_version": versie,
            }
        )
    registratie[sleutel] = nieuw
    registratie[historiesleutel] = historie
    return True


def voeg_ess05_samen(
    registratie: dict[str, Any], invoer: Mapping[str, Any], *, versie: int, nu: str
) -> bool:
    """Voeg gevalideerde invoer samen in `registratie` (muteert); geeft 'gewijzigd'."""
    gewijzigd = False
    if ESS05_ASSESSMENT_KEY in invoer:
        gewijzigd |= _vervang_met_historie(
            registratie,
            ESS05_ASSESSMENT_KEY,
            ESS05_ASSESSMENT_HISTORY_KEY,
            invoer[ESS05_ASSESSMENT_KEY],
            "assessment",
            versie=versie,
            nu=nu,
        )
    if ESS05_BUREN_VELD in invoer:
        gewijzigd |= _vervang_met_historie(
            registratie,
            ESS05_BUREN_VELD,
            ESS05_BUREN_HISTORIE_VELD,
            invoer[ESS05_BUREN_VELD],
            "neighbours",
            versie=versie,
            nu=nu,
        )
    if ESS05_LEGE_RUIMTE_VELD in invoer:
        lege = invoer[ESS05_LEGE_RUIMTE_VELD]
        if not lege:
            gewijzigd |= registratie.pop(ESS05_LEGE_RUIMTE_VELD, None) is not None
        elif registratie.get(ESS05_LEGE_RUIMTE_VELD) != lege:
            registratie[ESS05_LEGE_RUIMTE_VELD] = lege
            gewijzigd = True
    return gewijzigd


def neutraliseer_geimporteerde_ess05(
    registratie: dict[str, Any], *, versie: int, nu: str
) -> None:
    """Maak ESS-05-bewijs uit een import niet-actueel (muteert; BC-01).

    De replay toetst consistentie, geen herkomst: een samenhangend herschreven
    document zou als actuele pass afspelen. Een aangeleverde beoordeling gaat
    daarom als herkenbare historie (`herkomst: import`, `actueel: False`) naar
    `ess05_assessment_history`, een lege-ruimtebevestiging als historie-item
    naar de lijst `ess05_lege_ruimte_imported` (eerder bewaarde blijven staan,
    een gelijk document wordt niet opnieuw toegevoegd). Niets gaat verloren;
    de burenlijst blijft invoer. Pas een lokaal nieuw berekende beoordeling of
    lokale bevestiging is weer actueel.
    """
    beoordeling = registratie.pop(ESS05_ASSESSMENT_KEY, None)
    if beoordeling is not None:
        historie = registratie.get(ESS05_ASSESSMENT_HISTORY_KEY)
        historie = list(historie) if isinstance(historie, list) else []
        historie.append(
            {
                "assessment": deepcopy(beoordeling),
                "herkomst": "import",
                "actueel": False,
                "reden": "extern geïmporteerd; geen lokaal verkregen beoordeling",
                "superseded_at": nu,
                "superseded_on_version": versie,
            }
        )
        registratie[ESS05_ASSESSMENT_HISTORY_KEY] = historie
    lege = registratie.pop(ESS05_LEGE_RUIMTE_VELD, None)
    bewaard = _importhistorie_lege_ruimte(
        registratie.get(ESS05_LEGE_RUIMTE_IMPORT_VELD)
    )
    if lege and all(item.get("lege_ruimte") != lege for item in bewaard):
        bewaard.append(
            {
                "lege_ruimte": deepcopy(lege),
                "herkomst": "import",
                "actueel": False,
                "reden": "extern geïmporteerd; geen lokale bevestiging",
                "superseded_at": nu,
                "superseded_on_version": versie,
            }
        )
    if bewaard:
        registratie[ESS05_LEGE_RUIMTE_IMPORT_VELD] = bewaard


def _importhistorie_lege_ruimte(waarde: Any) -> list[dict[str, Any]]:
    """De bewaarde geïmporteerde lege-ruimtebevestigingen als lijst (BC-01-H).

    Een eerdere herimport overschreef het bewaarde document. Een enkel document
    (vorm van vóór de lijst) wordt een historie-item zonder verzonnen tijdstip;
    een onverwachte waarde gaat evenmin verloren.
    """
    if waarde is None:
        return []
    items = waarde if isinstance(waarde, list) else [waarde]
    return [
        (
            # dict(...) is voor een dict (de JSON-vorm) dezelfde waarde en houdt
            # het item bij het gedeclareerde `dict`-type.
            dict(deepcopy(item))
            if isinstance(item, Mapping) and "lege_ruimte" in item
            else {"lege_ruimte": deepcopy(item), "herkomst": "import", "actueel": False}
        )
        for item in items
    ]
