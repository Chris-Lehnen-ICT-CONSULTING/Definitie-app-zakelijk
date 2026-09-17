"""Categoriekeuze en -weergave zonder verlies of stille omzetting (DEF-751 B1).

Het schema staat elf opslagwaarden toe (CHECK op `definities.categorie`); de
app biedt er vier als keuze en de generatie kent alleen die vier. Deze pure
helper zorgt dat:

* de editor een geladen waarde exact terugtoont — ook ENT/ACT/… of een
  waarde die het schema niet (meer) kent — zonder `ValueError` en zonder
  hem naar type/proces om te zetten;
* een ontbrekende waarde als "geen categorie" zichtbaar is, niet als proces;
* de generatiehandler een keuze of modelvoorstel alleen accepteert als het
  één van de vier generatiecategorieën is — geen stille PROCES;
* de import kan zeggen of een waarde opgeslagen kan worden (technische
  schemagrens), zonder een tweede lijst van de elf waarden bij te houden.

Herkomst (handmatig/model/default) wordt hier niet vastgelegd; dat is B2.
"""

from __future__ import annotations

from typing import Any

from domain.ontological_categories import OntologischeCategorie
from ui.components.formatters.definition_formatter_utils import (
    CATEGORY_DISPLAY_NAMES,
    get_category_display_name,
)

# De vier keuzes die de app aanbiedt en die de generatie kent.
STANDAARD_CATEGORIEEN: list[str] = [c.value for c in OntologischeCategorie]

# Lege widgetwaarde voor een record zonder categorie; de opslaglaag slaat een
# lege keuze over (`_definition_to_updates` schrijft alleen niet-None).
GEEN_CATEGORIE = ""

_ONGEWIJZIGD = "bestaande waarde — ongewijzigd"


def is_opslagcategorie(waarde: str | None) -> bool:
    """True als `waarde` exact (hoofdlettergevoelig) een schemawaarde is."""
    return isinstance(waarde, str) and waarde in CATEGORY_DISPLAY_NAMES


def bouw_categorie_opties(bestaand: str | None) -> tuple[list[str], int]:
    """Opties en startindex voor de categorie-selectbox in de editor.

    De geladen waarde komt altijd exact in de lijst terug: als standaardkeuze
    op zijn eigen plek, anders als extra optie achteraan. Ontbrekend → lege
    optie vooraan, zodat openen/opslaan geen proces verzint.
    """
    if not bestaand:
        return [GEEN_CATEGORIE, *STANDAARD_CATEGORIEEN], 0
    if bestaand in STANDAARD_CATEGORIEEN:
        return list(STANDAARD_CATEGORIEEN), STANDAARD_CATEGORIEEN.index(bestaand)
    opties = [*STANDAARD_CATEGORIEEN, bestaand]
    return opties, len(opties) - 1


def categorie_label(waarde: str) -> str:
    """Weergavetekst voor een optie; niet-standaardwaarden zonder herkomstclaim."""
    if waarde == GEEN_CATEGORIE:
        return "— geen categorie —"
    naam = get_category_display_name(waarde)
    if waarde in STANDAARD_CATEGORIEEN:
        return naam
    return f"{naam} ({waarde}; {_ONGEWIJZIGD})"


def generatiecategorie_van(waarde: str | None) -> OntologischeCategorie | None:
    """De generatiecategorie voor een keuze/voorstel, of None als die er niet is.

    Alleen de vier enumwaarden (kastongevoelig, geen trimming) tellen; alles
    anders geeft None zodat de caller kan weigeren i.p.v. stil PROCES kiezen.
    """
    if not isinstance(waarde, str):
        return None
    try:
        return OntologischeCategorie(waarde.lower())
    except ValueError:
        return None


# DEF-751 B2: leesbare weergave van de keuzestatus (`domain.categorie_herkomst`).
_STATUSTEKST: dict[str, str] = {
    "absent": "Herkomst categorie: geen categorie en geen keuze vastgelegd.",
    "unknown_origin": (
        "Herkomst categorie: herkomst onbekend (bestaand record zonder keuze-event)."
    ),
    "invalid": "Herkomst categorie: keuze-event onleesbaar.",
    "manual_confirmed": "Herkomst categorie: handmatig gekozen",
    "manual_unattributed": (
        "Herkomst categorie: handmatige keuze volgens de aanvraag, door niemand "
        "bevestigd."
    ),
    "model_suggestion": "Herkomst categorie: voorstel van het model, niet bevestigd.",
    "imported": "Herkomst categorie: overgenomen uit import.",
    "imported_missing": "Herkomst categorie: importbron had geen categorie.",
    "default": "Herkomst categorie: door de code toegepaste default, geen keuze.",
}


def beschrijf_keuzestatus(status: Any, keuze: Any) -> str:
    """Eén regel over de herkomst van de opgeslagen categorie; geen oordeel."""
    if not isinstance(status, dict):
        return _STATUSTEKST["unknown_origin"]
    code = status.get("status")
    if code == "stale":
        onderliggend = _STATUSTEKST.get(str(status.get("underlying")), "")
        return (
            "Herkomst categorie: verouderd — "
            f"{status.get('reason')}. Eerder: "
            f"{onderliggend.removeprefix('Herkomst categorie: ')} "
            "Alleen een nieuwe keuze maakt de categorie weer bevestigd."
        )
    tekst = _STATUSTEKST.get(str(code), _STATUSTEKST["unknown_origin"])
    if code == "manual_confirmed" and isinstance(keuze, dict):
        tekst += (
            f" door {keuze.get('actor')} (opgegeven naam, niet geverifieerd) "
            f"op {keuze.get('recorded_at')}."
        )
    if status.get("text_unchanged") is False:
        # Reviewbevinding 5: de beperkte binding (term/context, niet de
        # gewijzigde tekst) expliciet — geen herbevestiging van de nieuwe tekst.
        versie = status.get("text_changed_on_version")
        tekst += (
            " Let op: de tekst is sindsdien gewijzigd"
            + (f" (versie {versie})" if versie is not None else "")
            + "; de keuze gold voor de tekst van toen en bevestigt de huidige "
            "tekst niet."
        )
    return tekst
