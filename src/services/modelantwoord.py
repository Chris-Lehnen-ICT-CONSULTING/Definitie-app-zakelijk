"""Het additieve modelconflictcontract (DEF-751 stap 2, ESS-02 besluit C3).

Het uitvoercontract van de generatie blijft "één zin, uitsluitend de
definitiekern". Deze module voegt daar één strikt herkenbare uitzondering aan
toe: bij een werkelijke tegenspraak tussen aangeleverde bronnen of
contextwaarden over de bedoelde betekenislaag levert het model géén
definitie, maar één melding::

    VERDUIDELIJKING NODIG: {"vraag": "...", "lezingen": [
        {"lezing": "...", "bron": "bron 2", "grond": "..."},
        {"lezing": "...", "bron": "context: DJI", "grond": "..."}]}

Wat hier wél en niet gebeurt:

* `lees_modelantwoord` leest uitsluitend structuur: staat de sentinel op de
  eerste niet-lege regel, is de rest precies één JSON-object met de verplichte
  velden, en volgt er niets meer. Er is geen regex- of semantiekdetector: een
  gewoon definitieantwoord (zonder sentinel) gaat byte-identiek door naar het
  bestaande pad, ook met een oude ``Ontologische categorie:``-regel.
* Alles wat afwijkt — definitie én melding, tekst na de payload, dubbele
  melding, ontbrekende/lege/onbekende velden, twee gelijke lezingen — is
  ``ongeldig``: veilig falen, nooit een kandidaat. De reden is altijd een
  vaste foutcode met vaste omschrijving (`FOUTCODES`), nooit modeltekst.
* `verifieer_gronden` toetst technisch (niet inhoudelijk) dat elke lezing
  naar een werkelijk aangeleverde bron (nummer uit de bronkwitantie) of een
  letterlijk opgegeven contextwaarde verwijst. Verzonnen bewijs of
  bronidentiteit maakt de melding ongeldig.
* Een gemeld conflict is een melding van het model, geen vastgesteld feit en
  geen ESS-02-oordeel; de verwerking daarvan (niet opslaan, niet valideren,
  verduidelijking vragen) ligt in de orchestrator en de UI.
"""

from __future__ import annotations

import json
import re
from collections.abc import Collection
from dataclasses import dataclass
from typing import Any

__all__ = [
    "CONFLICT_SENTINEL",
    "FOUTCODES",
    "SOORT_CONFLICT",
    "SOORT_DEFINITIE",
    "SOORT_ONGELDIG",
    "Conflictmelding",
    "Lezing",
    "Modelantwoord",
    "bron_nrs_uit_kwitantie",
    "contextwaarden_uit",
    "lees_modelantwoord",
    "verifieer_gronden",
]

#: De vaste eerste regel van een conflictmelding (kastongevoelig gelezen).
CONFLICT_SENTINEL = "VERDUIDELIJKING NODIG:"

SOORT_DEFINITIE = "definitie"
SOORT_CONFLICT = "conflict"
SOORT_ONGELDIG = "ongeldig"

_VERPLICHTE_MELDINGSSLEUTELS = frozenset({"vraag", "lezingen"})
_VERPLICHTE_LEZINGSSLEUTELS = frozenset({"lezing", "bron", "grond"})
_MIN_LEZINGEN = 2

_BRON_NR = re.compile(r"^bron\s+(\d+)$", re.IGNORECASE)
_CONTEXTWAARDE = re.compile(r"^context\s*:\s*(.+)$", re.IGNORECASE)
_MARKDOWN_FENCE = re.compile(r"^```[a-zA-Z0-9_-]*\s*\n(.*?)\n?```\s*$", re.DOTALL)


@dataclass(frozen=True)
class Lezing:
    """Eén door het model onderscheiden lezing met haar opgegeven grond."""

    lezing: str
    bron: str
    grond: str

    def to_dict(self) -> dict[str, str]:
        return {"lezing": self.lezing, "bron": self.bron, "grond": self.grond}


@dataclass(frozen=True)
class Conflictmelding:
    """Een structureel geldige conflictmelding: gerichte vraag + ≥2 lezingen."""

    vraag: str
    lezingen: tuple[Lezing, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "vraag": self.vraag,
            "lezingen": [lz.to_dict() for lz in self.lezingen],
        }


#: Vaste foutcodes → vaste technische omschrijvingen (reviewcorrectie 3).
#: Een reden is altijd exact een van deze teksten: nooit een sleutelnaam,
#: bronwaarde of ander fragment uit de modelpayload, zodat een afgewezen
#: melding geen modelinhoud verspreidt via response, log of UI. Veldnamen
#: die hieronder staan zijn ons eigen contractvocabulaire.
FOUTCODES: dict[str, str] = {
    "dubbele_melding": "dubbele conflictmelding in één antwoord",
    "sentinel_niet_eerst": (
        "conflictmelding staat niet op de eerste regel (vermengd met andere tekst)"
    ),
    "payload_ontbreekt": "conflictmelding zonder JSON-payload",
    "payload_geen_json": "conflictpayload is geen geldige JSON",
    "tekst_na_payload": "tekst na de conflictpayload (vermengd antwoord)",
    "payload_geen_object": "conflictpayload is geen JSON-object",
    "vraag_ontbreekt": "veld 'vraag' ontbreekt of is leeg",
    "lezingen_ontbreken": "veld 'lezingen' ontbreekt",
    "onbekende_sleutel": "conflictpayload bevat een onbekende sleutel",
    "lezingen_geen_lijst": "veld 'lezingen' is geen lijst",
    "te_weinig_lezingen": "minstens twee lezingen vereist",
    "lezing_geen_object": "een lezing is geen JSON-object",
    "lezing_onbekende_sleutel": "een lezing bevat een onbekende sleutel",
    "lezing_veld_lezing_ontbreekt": "een lezing mist het veld 'lezing' of het is leeg",
    "lezing_veld_bron_ontbreekt": "een lezing mist het veld 'bron' of het is leeg",
    "lezing_veld_grond_ontbreekt": "een lezing mist het veld 'grond' of het is leeg",
    "lezingen_gelijk": "lezingen moeten van elkaar verschillen",
    "grond_niet_aangeleverd": (
        "een lezing verwijst niet naar een aangeleverde bron (bron <nr> uit het "
        "bronnenblok) of opgegeven contextwaarde (context: <waarde>)"
    ),
}


@dataclass(frozen=True)
class Modelantwoord:
    """Uitkomst van het lezen van het ruwe modelantwoord.

    `tekst` is altijd het ongewijzigde ruwe antwoord (identiteit), zodat het
    definitiepad byte-identiek blijft. `conflict` is alleen gevuld bij
    `SOORT_CONFLICT`; `code` en `reden` alleen bij `SOORT_ONGELDIG` — een
    vaste foutcode uit `FOUTCODES` met haar vaste omschrijving, zonder
    modeltekst (geschikt voor logs, response en UI).
    """

    soort: str
    tekst: str
    conflict: Conflictmelding | None = None
    code: str | None = None
    reden: str | None = None


def _ongeldig(raw: str, code: str) -> Modelantwoord:
    return Modelantwoord(
        soort=SOORT_ONGELDIG, tekst=raw, code=code, reden=FOUTCODES[code]
    )


def _payload_na_sentinel(raw: str) -> str:
    """De tekst ná de (enige) sentinel, zonder eventuele markdown-fence."""
    index = raw.lower().index(CONFLICT_SENTINEL.lower())
    payload = raw[index + len(CONFLICT_SENTINEL) :].strip()
    fence = _MARKDOWN_FENCE.match(payload)
    if fence:
        payload = fence.group(1).strip()
    return payload


def _niet_lege_tekst(waarde: Any) -> str | None:
    if not isinstance(waarde, str):
        return None
    tekst = " ".join(waarde.split())
    return tekst or None


def _lees_lezing(item: Any) -> Lezing | str:
    """Eén lezing lezen; geeft de `Lezing` of een vaste foutcode terug.

    Onbekende sleutels worden niet benoemd (dat zou modeltekst zijn); welk
    verplicht veld ontbreekt wel — dat is ons eigen contractvocabulaire.
    """
    if not isinstance(item, dict):
        return "lezing_geen_object"
    sleutels = set(item)
    if sleutels - _VERPLICHTE_LEZINGSSLEUTELS:
        return "lezing_onbekende_sleutel"
    waarden: dict[str, str] = {}
    for sleutel in ("lezing", "bron", "grond"):
        tekst = _niet_lege_tekst(item.get(sleutel))
        if tekst is None:
            return f"lezing_veld_{sleutel}_ontbreekt"
        waarden[sleutel] = tekst
    return Lezing(**waarden)


def lees_modelantwoord(raw: str) -> Modelantwoord:
    """Lees het ruwe modelantwoord structureel: definitie, conflict of ongeldig.

    Zonder sentinel is het antwoord een definitie (tekst ongewijzigd). Met
    sentinel moet die op de eerste niet-lege regel staan en gevolgd worden
    door precies één JSON-object; elke afwijking is veilig ongeldig.
    """
    tekst = raw if isinstance(raw, str) else str(raw)
    aantal = tekst.lower().count(CONFLICT_SENTINEL.lower())
    if aantal == 0:
        return Modelantwoord(soort=SOORT_DEFINITIE, tekst=raw)
    if aantal > 1:
        return _ongeldig(raw, "dubbele_melding")

    regels = [r for r in tekst.splitlines() if r.strip()]
    eerste = regels[0].strip().lstrip("-*• ").strip() if regels else ""
    if not eerste.lower().startswith(CONFLICT_SENTINEL.lower()):
        return _ongeldig(raw, "sentinel_niet_eerst")

    payload = _payload_na_sentinel(tekst)
    if not payload:
        return _ongeldig(raw, "payload_ontbreekt")
    try:
        obj, einde = json.JSONDecoder().raw_decode(payload)
    except ValueError:
        return _ongeldig(raw, "payload_geen_json")
    if payload[einde:].strip():
        return _ongeldig(raw, "tekst_na_payload")
    if not isinstance(obj, dict):
        return _ongeldig(raw, "payload_geen_object")

    sleutels = set(obj)
    if sleutels - _VERPLICHTE_MELDINGSSLEUTELS:
        return _ongeldig(raw, "onbekende_sleutel")
    vraag = _niet_lege_tekst(obj.get("vraag"))
    if vraag is None:
        return _ongeldig(raw, "vraag_ontbreekt")
    if "lezingen" not in obj:
        return _ongeldig(raw, "lezingen_ontbreken")
    ruwe_lezingen = obj["lezingen"]
    if not isinstance(ruwe_lezingen, list):
        return _ongeldig(raw, "lezingen_geen_lijst")
    if len(ruwe_lezingen) < _MIN_LEZINGEN:
        return _ongeldig(raw, "te_weinig_lezingen")
    lezingen: list[Lezing] = []
    for item in ruwe_lezingen:
        gelezen = _lees_lezing(item)
        if isinstance(gelezen, str):
            return _ongeldig(raw, gelezen)
        lezingen.append(gelezen)
    if len({lz.lezing.casefold() for lz in lezingen}) < len(lezingen):
        return _ongeldig(raw, "lezingen_gelijk")

    return Modelantwoord(
        soort=SOORT_CONFLICT,
        tekst=raw,
        conflict=Conflictmelding(vraag=vraag, lezingen=tuple(lezingen)),
    )


def verifieer_gronden(
    conflict: Conflictmelding,
    *,
    bron_nrs: Collection[int],
    contextwaarden: Collection[str],
) -> tuple[str, str] | None:
    """Technische toets: elke `bron` wijst een aangeleverde bron of contextwaarde aan.

    Geen semantische jury: alleen "bron <nr>" met een nummer uit de kwitantie
    of "context: <waarde>" met een letterlijk opgegeven contextwaarde
    (kastongevoelig) is verifieerbaar. Geeft `(code, vaste omschrijving)`
    terug — nooit de opgegeven bronwaarde zelf — of None.
    """
    nummers = {int(nr) for nr in bron_nrs}
    waarden = {w.strip().casefold() for w in contextwaarden if w and w.strip()}
    for lezing in conflict.lezingen:
        verwijzing = lezing.bron.strip()
        nr = _BRON_NR.match(verwijzing)
        if nr and int(nr.group(1)) in nummers:
            continue
        ctx = _CONTEXTWAARDE.match(verwijzing)
        if ctx and ctx.group(1).strip().casefold() in waarden:
            continue
        return "grond_niet_aangeleverd", FOUTCODES["grond_niet_aangeleverd"]
    return None


def bron_nrs_uit_kwitantie(receipt: Any) -> set[int]:
    """De bronnummers die werkelijk in de prompt stonden (DEF-743-kwitantie)."""
    if not isinstance(receipt, dict):
        return set()
    sources = receipt.get("sources")
    if not isinstance(sources, list):
        return set()
    nummers: set[int] = set()
    for bron in sources:
        if isinstance(bron, dict) and isinstance(bron.get("nr"), int):
            nummers.add(bron["nr"])
    return nummers


def contextwaarden_uit(request: Any) -> set[str]:
    """Alle letterlijk opgegeven contextwaarden van een `GenerationRequest`."""
    waarden: set[str] = set()
    for veld in ("organisatorische_context", "juridische_context", "wettelijke_basis"):
        for waarde in getattr(request, veld, None) or []:
            if isinstance(waarde, str) and waarde.strip():
                waarden.add(waarde.strip())
    organisatie = getattr(request, "organisatie", None)
    if isinstance(organisatie, str) and organisatie.strip():
        waarden.add(organisatie.strip())
    return waarden
