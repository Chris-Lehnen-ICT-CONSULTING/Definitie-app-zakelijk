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

DEF-821 (ESS-04 G2-2) voegt een tweede, even strikte uitzondering toe: kan
het model een begripsbepalend criterium niet formuleren zonder een gegeven
te verzinnen, omdat de noodzakelijke betekenisgrond ontbreekt of strijdig
is, dan levert het géén definitie maar::

    BETEKENISGROND ONTBREEKT: {"ontbrekende_grond": "...", "vraag": "..."}

Geen lezingen en geen bronverwijzingen: de melding benoemt juist wat níét is
aangeleverd, dus er valt geen grond te verifiëren en er hoeft geen conflict
te worden verzonnen. Beide sentinels in één antwoord is ``gemengde_melding``
(ongeldig); verder gelden dezelfde structuurregels.

Correctieronde 1 (Codex-review): een beschadigde gereserveerde kop aan het
begin van een regel (zonder of met losse dubbele punt, underscore, opmaak)
is ``sentinel_beschadigd`` en een meldingspayload zonder kop (de
gereserveerde sleutels ``"ontbrekende_grond"``/``"lezingen"``) is
``payload_zonder_sentinel`` — beide ongeldig, nooit een kandidaat. Dezelfde
woorden midden in een definitiezin blijven gewoon een definitie.
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
    "ONTBREKENDE_GROND_SENTINEL",
    "SOORT_CONFLICT",
    "SOORT_DEFINITIE",
    "SOORT_ONGELDIG",
    "SOORT_ONTBREKENDE_GROND",
    "Conflictmelding",
    "Lezing",
    "Modelantwoord",
    "OntbrekendeGrondmelding",
    "bron_nrs_uit_kwitantie",
    "contextwaarden_uit",
    "lees_modelantwoord",
    "verifieer_gronden",
]

#: De vaste eerste regel van een conflictmelding (kastongevoelig gelezen).
CONFLICT_SENTINEL = "VERDUIDELIJKING NODIG:"
#: DEF-821: de vaste eerste regel van een melding van ontbrekende betekenisgrond.
ONTBREKENDE_GROND_SENTINEL = "BETEKENISGROND ONTBREEKT:"

SOORT_DEFINITIE = "definitie"
SOORT_CONFLICT = "conflict"
SOORT_ONTBREKENDE_GROND = "ontbrekende_grond"
SOORT_ONGELDIG = "ongeldig"

_VERPLICHTE_MELDINGSSLEUTELS = frozenset({"vraag", "lezingen"})
_VERPLICHTE_GRONDSLEUTELS = frozenset({"ontbrekende_grond", "vraag"})
_VERPLICHTE_LEZINGSSLEUTELS = frozenset({"lezing", "bron", "grond"})
_MIN_LEZINGEN = 2

_BRON_NR = re.compile(r"^bron\s+(\d+)$", re.IGNORECASE)
_CONTEXTWAARDE = re.compile(r"^context\s*:\s*(.+)$", re.IGNORECASE)
_MARKDOWN_FENCE = re.compile(r"^```[a-zA-Z0-9_-]*\s*\n(.*?)\n?```\s*$", re.DOTALL)
#: DEF-821 correctieronde 1: een gereserveerde meldingskop die aan het begin
#: van een regel staat maar niet exact is (geen of losse dubbele punt,
#: underscore, opmaak eromheen). Structureel, geen semantische detector:
#: alleen de twee kopwoordparen, aan het regelbegin, als geheel woord.
_BESCHADIGDE_KOP = re.compile(
    r"^(?:<[^>\n]*>|[\s\-*•#>`_])*"
    r"(?:betekenisgrond[\s_-]+ontbreekt|verduidelijking[\s_-]+nodig)(?!\w)",
    re.IGNORECASE | re.MULTILINE,
)
#: Een meldingspayload zonder kop: de gereserveerde contractsleutels.
_GERESERVEERDE_SLEUTEL = re.compile(r'"(?:ontbrekende_grond|lezingen)"\s*:')


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
class OntbrekendeGrondmelding:
    """DEF-821: welke noodzakelijke betekenisgrond ontbreekt + één gerichte vraag."""

    ontbrekende_grond: str
    vraag: str

    def to_dict(self) -> dict[str, str]:
        return {"ontbrekende_grond": self.ontbrekende_grond, "vraag": self.vraag}


#: Vaste foutcodes → vaste technische omschrijvingen (reviewcorrectie 3).
#: Een reden is altijd exact een van deze teksten: nooit een sleutelnaam,
#: bronwaarde of ander fragment uit de modelpayload, zodat een afgewezen
#: melding geen modelinhoud verspreidt via response, log of UI. Veldnamen
#: die hieronder staan zijn ons eigen contractvocabulaire.
FOUTCODES: dict[str, str] = {
    "dubbele_melding": "dubbele melding in één antwoord",
    "gemengde_melding": (
        "conflictmelding en melding van ontbrekende betekenisgrond in één antwoord"
    ),
    "grond_ontbreekt": "veld 'ontbrekende_grond' ontbreekt of is leeg",
    "sentinel_beschadigd": (
        "gereserveerde meldingskop niet exact (bijv. zonder dubbele punt)"
    ),
    "payload_zonder_sentinel": "meldingspayload zonder gereserveerde meldingskop",
    "sentinel_niet_eerst": (
        "melding staat niet op de eerste regel (vermengd met andere tekst)"
    ),
    "payload_ontbreekt": "melding zonder JSON-payload",
    "payload_geen_json": "meldingspayload is geen geldige JSON",
    "tekst_na_payload": "tekst na de meldingspayload (vermengd antwoord)",
    "payload_geen_object": "meldingspayload is geen JSON-object",
    "vraag_ontbreekt": "veld 'vraag' ontbreekt of is leeg",
    "lezingen_ontbreken": "veld 'lezingen' ontbreekt",
    "onbekende_sleutel": "meldingspayload bevat een onbekende sleutel",
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
    `SOORT_CONFLICT`, `ontbrekende_grond` alleen bij `SOORT_ONTBREKENDE_GROND`;
    `code` en `reden` alleen bij `SOORT_ONGELDIG` — een vaste foutcode uit
    `FOUTCODES` met haar vaste omschrijving, zonder modeltekst (geschikt voor
    logs, response en UI).
    """

    soort: str
    tekst: str
    conflict: Conflictmelding | None = None
    code: str | None = None
    reden: str | None = None
    ontbrekende_grond: OntbrekendeGrondmelding | None = None


def _ongeldig(raw: str, code: str) -> Modelantwoord:
    return Modelantwoord(
        soort=SOORT_ONGELDIG, tekst=raw, code=code, reden=FOUTCODES[code]
    )


def _payload_na_sentinel(raw: str, sentinel: str) -> str:
    """De tekst ná de (enige) sentinel, zonder eventuele markdown-fence."""
    index = raw.lower().index(sentinel.lower())
    payload = raw[index + len(sentinel) :].strip()
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
    """Lees het ruwe modelantwoord structureel.

    Uitkomst: definitie, conflict, ontbrekende grond of ongeldig. Zonder
    sentinel is het antwoord een definitie (tekst ongewijzigd). Met precies
    één sentinel moet die op de eerste niet-lege regel staan en gevolgd
    worden door precies één JSON-object; elke afwijking — ook beide soorten
    melding in één antwoord — is veilig ongeldig.
    """
    tekst = raw if isinstance(raw, str) else str(raw)
    laag = tekst.lower()
    aantal_conflict = laag.count(CONFLICT_SENTINEL.lower())
    aantal_grond = laag.count(ONTBREKENDE_GROND_SENTINEL.lower())
    if aantal_conflict == 0 and aantal_grond == 0:
        # Correctieronde 1: een beschadigde kop of kale payload is een
        # misvormde melding, nooit een kandidaat.
        if _BESCHADIGDE_KOP.search(tekst):
            return _ongeldig(raw, "sentinel_beschadigd")
        if _GERESERVEERDE_SLEUTEL.search(tekst):
            return _ongeldig(raw, "payload_zonder_sentinel")
        return Modelantwoord(soort=SOORT_DEFINITIE, tekst=raw)
    if aantal_conflict and aantal_grond:
        return _ongeldig(raw, "gemengde_melding")
    if aantal_conflict > 1 or aantal_grond > 1:
        return _ongeldig(raw, "dubbele_melding")
    sentinel = CONFLICT_SENTINEL if aantal_conflict else ONTBREKENDE_GROND_SENTINEL

    regels = [r for r in tekst.splitlines() if r.strip()]
    eerste = regels[0].strip().lstrip("-*• ").strip() if regels else ""
    if not eerste.lower().startswith(sentinel.lower()):
        return _ongeldig(raw, "sentinel_niet_eerst")

    payload = _payload_na_sentinel(tekst, sentinel)
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

    if sentinel == ONTBREKENDE_GROND_SENTINEL:
        return _lees_grondpayload(raw, obj)
    return _lees_conflictpayload(raw, obj)


def _lees_grondpayload(raw: str, obj: dict[str, Any]) -> Modelantwoord:
    """DEF-821: precies `ontbrekende_grond` en `vraag`, beide niet-lege tekst."""
    if set(obj) - _VERPLICHTE_GRONDSLEUTELS:
        return _ongeldig(raw, "onbekende_sleutel")
    grond = _niet_lege_tekst(obj.get("ontbrekende_grond"))
    if grond is None:
        return _ongeldig(raw, "grond_ontbreekt")
    vraag = _niet_lege_tekst(obj.get("vraag"))
    if vraag is None:
        return _ongeldig(raw, "vraag_ontbreekt")
    return Modelantwoord(
        soort=SOORT_ONTBREKENDE_GROND,
        tekst=raw,
        ontbrekende_grond=OntbrekendeGrondmelding(ontbrekende_grond=grond, vraag=vraag),
    )


def _lees_conflictpayload(raw: str, obj: dict[str, Any]) -> Modelantwoord:
    """DEF-751: `vraag` plus minstens twee verschillende lezingen met grond."""
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
