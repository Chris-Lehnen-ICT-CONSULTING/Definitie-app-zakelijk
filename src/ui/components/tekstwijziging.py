"""Tekstvergelijking na generatie (DEF-622, besluit Chris 14 september 2026).

Eén gedeelde renderer voor de generatie-, bewerk- en expertweergave: toon
uitsluitend wanneer de app de definitietekst ná generatie heeft gewijzigd de
melding *"De tekst is na generatie aangepast. Bekijk wijzigingen."*, met een
uitklapbare vergelijking van de gegenereerde definitiekern vóór nabewerking
en de uiteindelijke tekst, toevoegingen en verwijderingen herkenbaar.

Het bewijs komt van de generatie zelf (`definitie_kern_geextraheerd`,
`definitie_eindtekst`, `tekst_na_generatie_aangepast`) en reist mee in de
definitiemetadata en, per record, in `generation_prompt_data`. Zonder dat
bewijs (historisch record) wordt géén vóórtekst verzonnen — het al
opgeschoonde `definitie_origineel` is er geen. Is de actuele tekst niet meer
de generatie-eindtekst (na generatie handmatig gewijzigd), dan hoort de oude
vergelijking niet bij wat de gebruiker nu ziet en blijft de melding weg.

Modeltekst wordt letterlijk getoond (`st.text`): geen markdown- of
HTML-interpretatie van wat het model schreef.
"""

from __future__ import annotations

import difflib
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import streamlit as st

__all__ = [
    "MELDING_TEKST_AANGEPAST",
    "Tekstwijziging",
    "render_tekstwijziging",
    "tekstwijziging_uit_bewijs",
    "woordverschil",
]

MELDING_TEKST_AANGEPAST = "De tekst is na generatie aangepast. Bekijk wijzigingen."

VELD_KERN = "definitie_kern_geextraheerd"
VELD_EINDTEKST = "definitie_eindtekst"
VELD_AANGEPAST = "tekst_na_generatie_aangepast"


@dataclass(frozen=True)
class Tekstwijziging:
    """De twee echte tekststadia: kern vóór nabewerking en uiteindelijke tekst."""

    kern_voor: str
    tekst_na: str


def tekstwijziging_uit_bewijs(
    bewijs: Mapping[str, Any] | None, actuele_tekst: str | None
) -> Tekstwijziging | None:
    """De te tonen vergelijking, of None wanneer er niets (meer) te tonen is.

    None bij: geen bewijs of geen echte vóórtekst (historisch record), vlag
    niet gezet (ongewijzigd), of een actuele tekst die afwijkt van de
    generatie-eindtekst (stale: het record is daarna handmatig gewijzigd).
    """
    if not isinstance(bewijs, Mapping):
        return None
    kern = bewijs.get(VELD_KERN)
    eind = bewijs.get(VELD_EINDTEKST)
    if not isinstance(kern, str) or not isinstance(eind, str):
        return None
    if bewijs.get(VELD_AANGEPAST) is not True or kern == eind:
        return None
    if actuele_tekst is None or actuele_tekst.strip() != eind.strip():
        return None
    return Tekstwijziging(kern_voor=kern, tekst_na=eind)


def woordverschil(voor: str, na: str) -> list[tuple[str, str]]:
    """Woordniveau-verschil als (teken, woord): "=" gelijk, "-" weg, "+" erbij."""
    a, b = voor.split(), na.split()
    uit: list[tuple[str, str]] = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b).get_opcodes():
        if tag == "equal":
            uit.extend(("=", w) for w in a[i1:i2])
            continue
        if tag in ("delete", "replace"):
            uit.extend(("-", w) for w in a[i1:i2])
        if tag in ("insert", "replace"):
            uit.extend(("+", w) for w in b[j1:j2])
    return uit


def _inline(verschil: list[tuple[str, str]]) -> str:
    """Eén regel met [-verwijderd-] en {+toegevoegd+} (wdiff-stijl)."""
    delen = []
    for teken, woord in verschil:
        if teken == "-":
            delen.append(f"[-{woord}-]")
        elif teken == "+":
            delen.append(f"{{+{woord}+}}")
        else:
            delen.append(woord)
    return " ".join(delen)


def render_tekstwijziging(wijziging: Tekstwijziging | None, *, _st: Any = None) -> bool:
    """Toon melding en uitklapbare vergelijking; True wanneer er iets getoond is."""
    ui = _st if _st is not None else st
    if wijziging is None:
        return False
    ui.warning(MELDING_TEKST_AANGEPAST)
    verschil = woordverschil(wijziging.kern_voor, wijziging.tekst_na)
    with ui.expander("Bekijk wijzigingen", expanded=False):
        ui.caption("Gegenereerde definitiekern vóór nabewerking")
        ui.text(wijziging.kern_voor)
        ui.caption("Uiteindelijke definitietekst")
        ui.text(wijziging.tekst_na)
        ui.caption("Verschil per woord: [-verwijderd-] en {+toegevoegd+}")
        ui.text(_inline(verschil))
        ui.caption("Toegevoegd (+) en verwijderd (-)")
        ui.text(
            "\n".join(f"{teken} {woord}" for teken, woord in verschil if teken != "=")
            or "(geen woordverschil)"
        )
    return True
