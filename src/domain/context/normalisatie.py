"""Gedeelde contextnormalisatie (DEF-672, vervroegd uit DEF-622).

Context is gestructureerde metadata náást de definitie: drie gelijkwaardige
lijsten (`organisatorische_context`, `juridische_context`, `wettelijke_basis`)
die als gegeven bij een definitie en bij een validatie worden meegeleverd. Zij
wordt nooit aan de definitietekst toegevoegd — niet aan `definitie`, niet aan
`cleaned_text`, niet aan enig ander tekstveld.

Deze module bepaalt wanneer twee contextverzamelingen *dezelfde* context zijn.
Eén regelset, twee vormen:

- `canoniseer_contextlijst` — de vorm die wordt **opgeslagen**: getrimd, zonder
  lege waarden, hoofdletteronafhankelijk ontdubbeld en deterministisch
  gesorteerd. De oorspronkelijke schrijfwijze blijft staan; `DJI`, `OM` en
  `KMAR` zijn eigennamen die in de UI leesbaar moeten blijven.
- `contextsleutel` — de **vergelijkingssleutel**: dezelfde vorm, Unicode
  gecasefold. Hiermee is de vergelijking hoofdletter-, whitespace-, volgorde- en
  duplicaat-onafhankelijk zonder dat de opslag onleesbaar wordt.

Waarom twee vormen en niet één gecasefolde: de identiteitsregels zijn identiek,
maar casefolden bij het opslaan zou `DJI` als `dji` in de database zetten en dus
in de UI. Dat is gegevensverlies zonder functioneel doel — de herkenning van
bestaande, niet-canoniek opgeslagen waarden komt van de normalisatie bij het
*lezen*, niet van de vorm op disk. Daarom is er geen datamigratie nodig.

Bewust géén aliasmapping in deze wijziging: `DJI` en `Dienst Justitiële
Inrichtingen` blijven verschillende contextwaarden (besluit DEF-622).
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

__all__ = [
    "canoniseer_contextlijst",
    "contextsleutel",
]


def _losse_waarden(waarden: Any) -> Iterable[Any]:
    """Maak van de invoer een itereerbare reeks losse waarden.

    Een string is bewust géén reeks tekens hier: `list("DJI")` zou
    `['D', 'J', 'I']` opleveren en dat is precies het defect waardoor de
    duplicaatvergelijking nooit matchte (DEF-672).
    """
    if waarden is None:
        return ()
    if isinstance(waarden, str):
        return (waarden,)
    if isinstance(waarden, Iterable):
        return waarden
    return (waarden,)


def canoniseer_contextlijst(waarden: Any) -> list[str]:
    """De op te slaan vorm van één contextlijst.

    Trimt whitespace, laat lege waarden vallen, ontdubbelt
    hoofdletteronafhankelijk (de eerst gevonden schrijfwijze blijft staan) en
    sorteert deterministisch op de gecasefolde waarde. Idempotent.
    """
    gezien: dict[str, str] = {}
    for waarde in _losse_waarden(waarden):
        tekst = str(waarde if waarde is not None else "").strip()
        if not tekst:
            continue
        gezien.setdefault(tekst.casefold(), tekst)
    return [gezien[sleutel] for sleutel in sorted(gezien)]


def contextsleutel(waarden: Any) -> tuple[str, ...]:
    """De vergelijkingssleutel van één contextlijst.

    Gelijk voor elke schrijfwijze, volgorde, whitespace-variant en herhaling
    die dezelfde context betekent. Hashbaar, zodat de sleutel als dict- of
    set-lid kan dienen.
    """
    return tuple(waarde.casefold() for waarde in canoniseer_contextlijst(waarden))
