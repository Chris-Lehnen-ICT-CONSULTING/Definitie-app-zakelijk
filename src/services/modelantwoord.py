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
  ``ongeldig``: veilig falen, nooit een kandidaat.
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


@dataclass(frozen=True)
class Modelantwoord:
    """Uitkomst van het lezen van het ruwe modelantwoord.

    `tekst` is altijd het ongewijzigde ruwe antwoord (identiteit), zodat het
    definitiepad byte-identiek blijft. `conflict` is alleen gevuld bij
    `SOORT_CONFLICT`; `reden` alleen bij `SOORT_ONGELDIG` (technisch, zonder
    modeltekst — geschikt voor logs en de UI).
    """

    soort: str
    tekst: str
    conflict: Conflictmelding | None = None
    reden: str | None = None


def _ongeldig(raw: str, reden: str) -> Modelantwoord:
    return Modelantwoord(soort=SOORT_ONGELDIG, tekst=raw, reden=reden)


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


def _lees_lezing(index: int, item: Any) -> Lezing | str:
    """Eén lezing lezen; geeft de `Lezing` of een technische reden terug."""
    if not isinstance(item, dict):
        return f"lezing {index} is geen object"
    sleutels = set(item)
    ontbrekend = _VERPLICHTE_LEZINGSSLEUTELS - sleutels
    if ontbrekend:
        return f"lezing {index} mist sleutel(s) {sorted(ontbrekend)}"
    onbekend = sleutels - _VERPLICHTE_LEZINGSSLEUTELS
    if onbekend:
        return f"lezing {index} bevat onbekende sleutel(s) {sorted(onbekend)}"
    waarden: dict[str, str] = {}
    for sleutel in ("lezing", "bron", "grond"):
        tekst = _niet_lege_tekst(item[sleutel])
        if tekst is None:
            return f"lezing {index}: veld '{sleutel}' ontbreekt of is leeg"
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
        return _ongeldig(raw, "dubbele conflictmelding in één antwoord")

    regels = [r for r in tekst.splitlines() if r.strip()]
    eerste = regels[0].strip().lstrip("-*• ").strip() if regels else ""
    if not eerste.lower().startswith(CONFLICT_SENTINEL.lower()):
        return _ongeldig(
            raw,
            "conflictmelding staat niet op de eerste regel "
            "(vermengd met andere tekst)",
        )

    payload = _payload_na_sentinel(tekst)
    if not payload:
        return _ongeldig(raw, "conflictmelding zonder JSON-payload")
    try:
        obj, einde = json.JSONDecoder().raw_decode(payload)
    except ValueError:
        return _ongeldig(raw, "conflictpayload is geen geldige JSON")
    if payload[einde:].strip():
        return _ongeldig(raw, "tekst na de conflictpayload (vermengd antwoord)")
    if not isinstance(obj, dict):
        return _ongeldig(raw, "conflictpayload is geen JSON-object")

    sleutels = set(obj)
    ontbrekend = _VERPLICHTE_MELDINGSSLEUTELS - sleutels
    if ontbrekend:
        return _ongeldig(raw, f"conflictpayload mist sleutel(s) {sorted(ontbrekend)}")
    onbekend = sleutels - _VERPLICHTE_MELDINGSSLEUTELS
    if onbekend:
        return _ongeldig(
            raw, f"conflictpayload bevat onbekende sleutel(s) {sorted(onbekend)}"
        )
    vraag = _niet_lege_tekst(obj["vraag"])
    if vraag is None:
        return _ongeldig(raw, "veld 'vraag' ontbreekt of is leeg")
    ruwe_lezingen = obj["lezingen"]
    if not isinstance(ruwe_lezingen, list):
        return _ongeldig(raw, "veld 'lezingen' is geen lijst")
    if len(ruwe_lezingen) < _MIN_LEZINGEN:
        return _ongeldig(
            raw, f"minstens twee lezingen vereist, {len(ruwe_lezingen)} gegeven"
        )
    lezingen: list[Lezing] = []
    for index, item in enumerate(ruwe_lezingen, start=1):
        gelezen = _lees_lezing(index, item)
        if isinstance(gelezen, str):
            return _ongeldig(raw, gelezen)
        lezingen.append(gelezen)
    if len({lz.lezing.casefold() for lz in lezingen}) < len(lezingen):
        return _ongeldig(raw, "lezingen moeten van elkaar verschillen")

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
) -> str | None:
    """Technische toets: elke `bron` wijst een aangeleverde bron of contextwaarde aan.

    Geen semantische jury: alleen "bron <nr>" met een nummer uit de kwitantie
    of "context: <waarde>" met een letterlijk opgegeven contextwaarde
    (kastongevoelig) is verifieerbaar. Geeft de reden terug, of None.
    """
    nummers = {int(nr) for nr in bron_nrs}
    waarden = {w.strip().casefold() for w in contextwaarden if w and w.strip()}
    for index, lezing in enumerate(conflict.lezingen, start=1):
        verwijzing = lezing.bron.strip()
        nr = _BRON_NR.match(verwijzing)
        if nr and int(nr.group(1)) in nummers:
            continue
        ctx = _CONTEXTWAARDE.match(verwijzing)
        if ctx and ctx.group(1).strip().casefold() in waarden:
            continue
        return (
            f"lezing {index} verwijst naar '{verwijzing}', maar dat is geen "
            "aangeleverde bron (bron <nr> uit het bronnenblok) of opgegeven "
            "contextwaarde (context: <waarde>)"
        )
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
