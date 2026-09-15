"""Canonieke bronidentiteit voor CON-02 (DEF-743).

Een aangeleverde bron (upload, RAG-chunk, webtreffer) is een aanvoerroute met
gegevens, geen gezag. Deze module maakt daar één vergelijkbare identiteit van:

- een **stabiel id** dat uitsluitend uit aangeleverde velden wordt afgeleid
  (`doc_id`, `chunk_id`, `url`) of — als die ontbreken — uit de inhoud;
- een **lokaal berekende inhoudshash** over de passage die werkelijk als
  bewijs geldt: `prompt_content` (wat het model bij de generatie zag, na
  sanitisatie/afkapping) als dat er is, anders de aangeleverde tekst;
- alleen **werkelijk aangeleverde** coördinaten (url, vindplaats, versie,
  profiel): niets wordt verzonnen, `None` betekent onbekend;
- de overige **feitelijke** metadata als `identity` (deep copy), zodat een
  wijziging in bijvoorbeeld uitgever, vaststellingsstatus of rechtsgebied de
  vingerafdruk raakt (`domain.sources.contract`).

Zoekscore, confidence, `used_in_prompt`, `is_authoritative` en routelabels
horen bewust niet bij de identiteit: zij zeggen iets over hoe een bron is
gevonden of getoond, niet over wat zij is.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

__all__ = [
    "KWITANTIE_KANALEN",
    "NIET_SUBSTANTIEVE_VELDEN",
    "PROFIELEN",
    "PROFIEL_BELEID",
    "PROFIEL_CONVENANT",
    "PROFIEL_NORM",
    "PROFIEL_OVERIG",
    "PROFIEL_VAKPUBLICATIE",
    "PROFIEL_WET",
    "Bronidentiteit",
    "bereken_inhoudshash",
    "bron_op_id",
    "canoniseer_bronnen",
    "koppel_kwitantie",
    "kwitantie_koppelrapport",
    "kwitantiefout",
]

# De zes goedgekeurde bronprofielen (DEF-743). Profiel en bewijsstatus blijven
# apart: onvastgesteld beleid houdt profiel 'beleid' met een onbekende status.
PROFIEL_WET = "wet_regelgeving"
PROFIEL_BELEID = "beleid"
PROFIEL_CONVENANT = "convenant"
PROFIEL_NORM = "norm_standaard"
PROFIEL_VAKPUBLICATIE = "vakpublicatie"
PROFIEL_OVERIG = "overig"
PROFIELEN: tuple[str, ...] = (
    PROFIEL_WET,
    PROFIEL_BELEID,
    PROFIEL_CONVENANT,
    PROFIEL_NORM,
    PROFIEL_VAKPUBLICATIE,
    PROFIEL_OVERIG,
)

# Alleen een expliciet aangeleverd `bron_type` wordt naar een profiel vertaald.
_BRON_TYPE_NAAR_PROFIEL: dict[str, str] = {
    "wet": PROFIEL_WET,
    "wetgeving": PROFIEL_WET,
    "regelgeving": PROFIEL_WET,
    "wet_regelgeving": PROFIEL_WET,
    "verdrag": PROFIEL_WET,
    "beleid": PROFIEL_BELEID,
    "beleidsregel": PROFIEL_BELEID,
    "convenant": PROFIEL_CONVENANT,
    "overeenkomst": PROFIEL_CONVENANT,
    "norm": PROFIEL_NORM,
    "standaard": PROFIEL_NORM,
    "norm_standaard": PROFIEL_NORM,
    "vakpublicatie": PROFIEL_VAKPUBLICATIE,
    "begrippenregister": PROFIEL_VAKPUBLICATIE,
    "register": PROFIEL_VAKPUBLICATIE,
    "overig": PROFIEL_OVERIG,
    "onbekend": PROFIEL_OVERIG,
}

# Velden die géén bronidentiteit zijn: hoe een bron is gevonden, getoond of in
# de prompt is beland. Zij tellen nergens als gezag en zitten niet in de
# vingerafdruk. De passagevelden staan er ook: de passage wordt apart gehasht.
NIET_SUBSTANTIEVE_VELDEN: frozenset[str] = frozenset(
    {
        "score",
        "confidence",
        "level",
        "used_in_prompt",
        "is_authoritative",
        "source_label",
        "selection_basis",
        "retrieval_score",
        "snippet",
        "chunk_text",
        "content",
        "prompt_content",
        "prompt_content_hash",
        "xml",
        "sanitized",
        "truncated",
        "nr",
        "receipt_nr",
        "omitted_reason",
        # Correlatievelden van de kwitantie v2 (pakket E): positie en hash van
        # de oorspronkelijke passage — koppeladministratie, geen identiteit.
        "input_index",
        "original_content_hash",
        "receipt_correlation",
        # De afgeleide/canonieke velden zelf; die staan al apart op de identiteit.
        "source_id",
        "provider",
        "title",
        "url",
        "version",
        "source_version",
        "locator",
        "legal",
        "metadata",
        "citation_label",
        "artikel_lid",
        "bron_type",
    }
)

_PASSAGEVELDEN: tuple[str, ...] = ("prompt_content", "snippet", "chunk_text", "content")
# Alleen een expliciet aangeleverde bronversie/-editie is een versie. Een
# `created_at`/`retrieved_at` zegt wanneer de app de passage zag — dat is een
# observatie (blijft in `identity`), geen normatieve editie of geldigheid.
_VERSIEVELDEN: tuple[str, ...] = ("source_version", "version")


def bereken_inhoudshash(passage: str) -> str:
    """sha256 over de exacte passage; één teken verschil is een andere inhoud."""
    return hashlib.sha256(str(passage or "").encode("utf-8")).hexdigest()


def _tekst(waarde: Any) -> str | None:
    """Een getrimde, niet-lege tekst of None (nooit de tekst 'None')."""
    if waarde is None or isinstance(waarde, bool):
        return None
    tekst = str(waarde).strip()
    return tekst or None


def _json_normaal(waarde: Any) -> Any:
    """Diep gekopieerde, JSON-vriendelijke waarde (sleutels als tekst)."""
    if isinstance(waarde, Mapping):
        return {str(k): _json_normaal(v) for k, v in waarde.items()}
    if isinstance(waarde, list | tuple | set | frozenset):
        return [_json_normaal(v) for v in waarde]
    if isinstance(waarde, str | int | float | bool) or waarde is None:
        return waarde
    return str(waarde)


def _metadata_locatordelen(metadata: Any) -> list[str]:
    """Vindplaatsdelen uit `metadata`: paginanummer, dan `locator` (dict of tekst)."""
    if not isinstance(metadata, Mapping):
        return []
    delen: list[str] = []
    pagina = _tekst(metadata.get("pagina_nummer"))
    if pagina:
        delen.append(f"p. {pagina}")
    locator = metadata.get("locator")
    if isinstance(locator, Mapping):
        for sleutel in sorted(locator):
            waarde = _tekst(locator[sleutel])
            if waarde:
                delen.append(f"{sleutel}={waarde}")
    else:
        waarde = _tekst(locator)
        if waarde:
            delen.append(waarde)
    return delen


def _locator(bron: Mapping[str, Any]) -> str | None:
    """Alle aangeleverde vindplaatsdelen, in vaste volgorde; None als er niets is."""
    delen: list[str] = []
    legal = bron.get("legal")
    if isinstance(legal, Mapping):
        citaat = _tekst(legal.get("citation_text"))
        if citaat:
            delen.append(citaat)
    for veld in ("citation_label", "artikel_lid"):
        waarde = _tekst(bron.get(veld))
        if waarde and waarde not in delen:
            delen.append(waarde)
    delen.extend(_metadata_locatordelen(bron.get("metadata")))
    if not delen:
        return _tekst(bron.get("locator"))
    return " · ".join(delen)


def _versie(bron: Mapping[str, Any]) -> str | None:
    for veld in _VERSIEVELDEN:
        waarde = _tekst(bron.get(veld))
        if waarde:
            return waarde
    return None


def _passage(bron: Mapping[str, Any]) -> str:
    """De passage die als bewijs geldt: wat het model zag gaat vóór de ruwe tekst."""
    for veld in _PASSAGEVELDEN:
        waarde = bron.get(veld)
        if isinstance(waarde, str) and waarde != "":
            return waarde
    return ""


def _gedeclareerd_profiel(bron: Mapping[str, Any]) -> str | None:
    bron_type = _tekst(bron.get("bron_type"))
    if bron_type is None:
        return None
    return _BRON_TYPE_NAAR_PROFIEL.get(bron_type.casefold(), PROFIEL_OVERIG)


def _provider_id(
    bron: Mapping[str, Any], doc_id: str | None, chunk_id: str | None
) -> str | None:
    """Het id dat de aanvoerroute zelf voorschrijft (documents → doc, rag → rag)."""
    provider = (_tekst(bron.get("provider")) or "").casefold()
    if provider in ("documents", "document") and doc_id:
        return f"doc:{doc_id}"
    if provider == "rag" and chunk_id:
        document_id = _tekst(bron.get("document_id"))
        return f"rag:{document_id}:{chunk_id}" if document_id else f"rag:{chunk_id}"
    return None


def _basis_id(bron: Mapping[str, Any], content_hash: str) -> str:
    """Basis-id: expliciet → per aanvoerroute → url → doc → rag → inhoudshash."""
    expliciet = _tekst(bron.get("source_id"))
    if expliciet:
        return expliciet
    doc_id = _tekst(bron.get("doc_id"))
    chunk_id = _tekst(bron.get("chunk_id"))
    per_route = _provider_id(bron, doc_id, chunk_id)
    if per_route:
        return per_route
    kandidaten = (
        ("url", _tekst(bron.get("url"))),
        ("doc", doc_id),
        ("rag", chunk_id),
    )
    for voorvoegsel, waarde in kandidaten:
        if waarde:
            return f"{voorvoegsel}:{waarde}"
    return f"hash:{content_hash[:16]}"


def _identity(bron: Mapping[str, Any]) -> dict[str, Any]:
    """De feitelijke, niet-canonieke metadata van de bron (deep copy)."""
    identity: dict[str, Any] = {}
    for sleutel, waarde in bron.items():
        naam = str(sleutel)
        if naam in NIET_SUBSTANTIEVE_VELDEN or waarde is None:
            continue
        identity[naam] = _json_normaal(waarde)
    # Geneste feitelijke coördinaten blijven in de identiteit — maar als kopie.
    for sleutel in ("legal", "metadata"):
        waarde = bron.get(sleutel)
        if isinstance(waarde, Mapping) and waarde:
            identity[sleutel] = _json_normaal(waarde)
    return dict(sorted(identity.items()))


@dataclass(frozen=True)
class Bronidentiteit:
    """Eén canonieke aangeleverde bron: identiteit, passage en inhoudshash."""

    source_id: str
    provider: str | None
    title: str | None
    url: str | None
    locator: str | None
    version: str | None
    passage: str
    content_hash: str
    declared_profile: str | None
    identity: dict[str, Any]
    used_in_prompt: bool | None = None

    def als_dict(self) -> dict[str, Any]:
        """JSON-vriendelijke identiteit; de passage reist met de bronlijst mee."""
        return {
            "source_id": self.source_id,
            "provider": self.provider,
            "title": self.title,
            "url": self.url,
            "locator": self.locator,
            "version": self.version,
            "content_hash": self.content_hash,
            "declared_profile": self.declared_profile,
            "identity": deepcopy(self.identity),
            "used_in_prompt": self.used_in_prompt,
        }

    def vingerafdrukdeel(self) -> dict[str, Any]:
        """Wat van deze bron in de vingerafdruk gaat: alles wat het oordeel raakt.

        Bewust niet `used_in_prompt`: dat is administratie over de prompt, geen
        eigenschap van de bron.
        """
        return {
            "source_id": self.source_id,
            "content_hash": self.content_hash,
            "version": self.version,
            "url": self.url,
            "locator": self.locator,
            "title": self.title,
            "declared_profile": self.declared_profile,
            "identity": self.identity,
        }


def _canoniseer_een(bron: Mapping[str, Any]) -> tuple[str, Bronidentiteit]:
    """(basis-id, identiteit) voor één bron; de definitieve id volgt na botsingscontrole."""
    kopie = deepcopy(dict(bron))
    passage = _passage(kopie)
    content_hash = bereken_inhoudshash(passage)
    used = kopie.get("used_in_prompt")
    return _basis_id(kopie, content_hash), Bronidentiteit(
        source_id="",
        provider=_tekst(kopie.get("provider")),
        title=_tekst(kopie.get("title")) or _tekst(kopie.get("filename")),
        url=_tekst(kopie.get("url")),
        locator=_locator(kopie),
        version=_versie(kopie),
        passage=passage,
        content_hash=content_hash,
        declared_profile=_gedeclareerd_profiel(kopie),
        identity=_identity(kopie),
        used_in_prompt=used if isinstance(used, bool) else None,
    )


def _variantsleutel(bron: Bronidentiteit) -> str:
    """Wat een bron onderscheidt van een andere met hetzelfde basis-id.

    Inhoud én identiteitsmetadata (versie, url, vindplaats, titel, profiel,
    feitelijke velden) tellen mee: twee bronnen met dezelfde passage maar een
    andere versie of vindplaats zijn twee bronnen, en de invoervolgorde mag
    nooit bepalen welke van de twee 'de echte' is.
    """
    deel = {k: v for k, v in bron.vingerafdrukdeel().items() if k != "source_id"}
    return hashlib.sha256(
        json.dumps(deel, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def canoniseer_bronnen(ruw: Any) -> tuple[Bronidentiteit, ...]:
    """Alle bruikbare bronnen uit een aangeleverde lijst, canoniek en gesorteerd.

    Niet-dicts worden overgeslagen; de invoer wordt nooit gemuteerd (deep copy
    per bron). Botst een basis-id op verschillende inhoud óf verschillende
    identiteitsmetadata, dan krijgen alle betrokken varianten een suffix over
    hun variantsleutel, zodat elke variant een eigen, stabiel id houdt en
    `bron_op_id` nooit een andere passage of versie teruggeeft dan gevraagd.
    Alleen volledig identieke bronnen tellen één keer.
    """
    if not isinstance(ruw, list | tuple):
        return ()
    voorlopig: list[tuple[str, Bronidentiteit]] = [
        _canoniseer_een(bron) for bron in ruw if isinstance(bron, Mapping)
    ]
    varianten_per_basis: dict[str, set[str]] = {}
    for basis, bron in voorlopig:
        varianten_per_basis.setdefault(basis, set()).add(_variantsleutel(bron))

    gezien: set[str] = set()
    resultaat: list[Bronidentiteit] = []
    for basis, bron in voorlopig:
        variant = _variantsleutel(bron)
        source_id = (
            f"{basis}#{variant[:8]}" if len(varianten_per_basis[basis]) > 1 else basis
        )
        if source_id in gezien:
            continue
        gezien.add(source_id)
        resultaat.append(
            Bronidentiteit(
                source_id=source_id,
                provider=bron.provider,
                title=bron.title,
                url=bron.url,
                locator=bron.locator,
                version=bron.version,
                passage=bron.passage,
                content_hash=bron.content_hash,
                declared_profile=bron.declared_profile,
                identity=bron.identity,
                used_in_prompt=bron.used_in_prompt,
            )
        )
    resultaat.sort(key=lambda b: (b.source_id, b.content_hash))
    return tuple(resultaat)


def bron_op_id(bronnen: Any, source_id: Any) -> Bronidentiteit | None:
    """De canonieke bron met exact dit id, of None."""
    if not isinstance(source_id, str):
        return None
    for bron in bronnen or ():
        if isinstance(bron, Bronidentiteit) and bron.source_id == source_id:
            return bron
    return None


# --- Kwitantie van de promptservice (pakket E) --------------------------------

_KWITANTIE_TYPE_NAAR_PROVIDER: dict[str, str] = {
    "rag": "rag",
    "document": "documents",
    "web": "web",
}


#: De drie aanvoerkanalen van de kwitantie (E): `document` ≙ provider
#: `documents`, `rag` ≙ provider `rag`, `web` ≙ alle overige providers.
KWITANTIE_KANALEN: tuple[str, str, str] = ("rag", "web", "document")

#: Waarden van `receipt_correlation` op een gekoppelde bron.
_CORRELATIE_GEVERIFIEERD = "verified"  # positie + oorspronkelijke hash kloppen
_CORRELATIE_NIET_IN_KWITANTIE = "not_in_receipt"  # geen record wijst naar deze bron
_CORRELATIE_ONGEKOPPELD = "unmatched"  # record wijst naar niets (index/hash/id fout)
_CORRELATIE_AMBIGU = "ambiguous"  # v1-kwitantie zonder uniek id in het kanaal


def _kanaal_van(bron: Mapping[str, Any]) -> str:
    provider = (_tekst(bron.get("provider")) or "").casefold()
    if provider == "rag":
        return "rag"
    if provider in ("documents", "document"):
        return "document"
    return "web"


def _kanaal_id(bron: Mapping[str, Any], kanaal: str) -> str | None:
    """Het ruwe kanaal-id zoals de kwitantie het noemt (chunk_id/doc_id/url)."""
    veld = {"rag": "chunk_id", "document": "doc_id", "web": "url"}[kanaal]
    return _tekst(bron.get(veld))


def _oorspronkelijke_hash(bron: Mapping[str, Any], kanaal: str) -> str:
    """`sha256:<hex>` over de aangeleverde passage, exact zoals E die berekent."""
    tekst = bron.get("snippet")
    if not isinstance(tekst, str) and kanaal == "rag":
        tekst = bron.get("chunk_text")
    if not isinstance(tekst, str):
        tekst = ""
    return "sha256:" + bereken_inhoudshash(tekst)


def _kanaallijsten(
    bronnen_ruw: list[Mapping[str, Any]],
    kanalen: Mapping[str, Any] | None,
) -> dict[str, list[int]]:
    """Per kanaal de posities in `bronnen_ruw`, in de aangeleverde kanaalvolgorde.

    Met expliciete `kanalen` (de lijsten die de orchestrator werkelijk aan de
    promptservice gaf) worden de objecten op identiteit teruggevonden — geen
    gok na filteren of sorteren. Zonder `kanalen` geldt de providergroepering
    van de bronlijst zelf, in bronlijstvolgorde; de hashverificatie vangt
    daarna elke afwijking op.
    """
    if isinstance(kanalen, Mapping):
        positie = {id(b): i for i, b in enumerate(bronnen_ruw)}
        return {
            kanaal: [
                positie[id(item)]
                for item in (kanalen.get(kanaal) or [])
                if id(item) in positie
            ]
            for kanaal in KWITANTIE_KANALEN
        }
    lijsten: dict[str, list[int]] = {kanaal: [] for kanaal in KWITANTIE_KANALEN}
    for i, bron in enumerate(bronnen_ruw):
        lijsten[_kanaal_van(bron)].append(i)
    return lijsten


def _kandidaat_v2(
    record: Mapping[str, Any],
    bronnen_ruw: list[Mapping[str, Any]],
    lijsten: Mapping[str, list[int]],
) -> int | None:
    """De bronpositie waar dit v2-record aantoonbaar bij hoort, of None.

    Drie onafhankelijke controles: kanaal + positie bestaan, de hash van de
    oorspronkelijke passage is gelijk, en een genoemd `source_id` is gelijk aan
    het kanaal-id van de kandidaat. Faalt er één, dan is er geen koppeling —
    nooit een positionele gok.
    """
    kanaal = (_tekst(record.get("source_type")) or "").casefold()
    index = record.get("input_index")
    if kanaal not in lijsten or not isinstance(index, int) or isinstance(index, bool):
        return None
    posities = lijsten[kanaal]
    if not 0 <= index < len(posities):
        return None
    kandidaat = bronnen_ruw[posities[index]]
    if _tekst(record.get("original_content_hash")) != _oorspronkelijke_hash(
        kandidaat, kanaal
    ):
        return None
    genoemd = _tekst(record.get("source_id"))
    if genoemd is not None and genoemd != _kanaal_id(kandidaat, kanaal):
        return None
    return posities[index]


def _kandidaat_v1(
    record: Mapping[str, Any],
    bronnen_ruw: list[Mapping[str, Any]],
    lijsten: Mapping[str, list[int]],
) -> tuple[int | None, bool]:
    """(positie, ambigu) voor een v1-record: alleen een uniek kanaal-id koppelt."""
    kanaal = (_tekst(record.get("source_type")) or "").casefold()
    genoemd = _tekst(record.get("source_id"))
    if kanaal not in lijsten or genoemd is None:
        return None, False
    treffers = [
        i for i in lijsten[kanaal] if _kanaal_id(bronnen_ruw[i], kanaal) == genoemd
    ]
    if len(treffers) == 1:
        return treffers[0], False
    return None, len(treffers) > 1


def koppel_kwitantie(
    bronnen_ruw: Any,
    receipt: Any,
    *,
    kanalen: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Koppel de aangeleverde bronnen aan de kwitantie van de prompt (E, v2).

    Per record in `sources` + `omitted` wordt de bron gezocht op
    `(source_type, input_index)` in de aangeleverde kanaallijst en
    **geverifieerd** met `original_content_hash` (en, indien genoemd, het
    kanaal-id). Gekoppelde gebruikte bronnen krijgen de exacte promptinhoud
    (`prompt_content`, gesanitiseerd/afgekapt) en `used_in_prompt=True`;
    gekoppelde weggelaten bronnen `used_in_prompt=False` + `omitted_reason`.
    Elke bron draagt `receipt_correlation`: `verified`, `not_in_receipt` (geen
    record wijst ernaar) — en records zonder aantoonbare tegenhanger worden
    als losse bron toegevoegd met `unmatched` (v2) of `ambiguous` (v1 zonder
    uniek id): zichtbaar, nooit stil positioneel geplakt. Een v1-kwitantie
    koppelt uitsluitend op een binnen het kanaal uniek `source_id`.

    `kanalen` zijn de lijsten die de orchestrator werkelijk aan de
    promptservice gaf (`rag`/`web`/`document`); de bronobjecten daarin worden
    op identiteit in `bronnen_ruw` teruggevonden. Zonder bruikbare kwitantie
    komt de lijst ongewijzigd (als kopie) terug. De invoer wordt niet
    gemuteerd; de correlatievelden zijn geen bronidentiteit.
    """
    origineel: list[Mapping[str, Any]] = [
        b for b in (bronnen_ruw or []) if isinstance(b, Mapping)
    ]
    bronnen: list[dict[str, Any]] = [deepcopy(dict(b)) for b in origineel]
    if not isinstance(receipt, Mapping):
        return bronnen

    v2 = str(receipt.get("version") or "") != "1"
    lijsten = _kanaallijsten(origineel, kanalen)
    records = [
        (r, True) for r in receipt.get("sources") or [] if isinstance(r, Mapping)
    ] + [(r, False) for r in receipt.get("omitted") or [] if isinstance(r, Mapping)]

    gekoppeld: set[int] = set()
    los: list[dict[str, Any]] = []
    for record, gebruikt in records:
        if v2:
            positie, ambigu = _kandidaat_v2(record, origineel, lijsten), False
        else:
            positie, ambigu = _kandidaat_v1(record, origineel, lijsten)
        if positie is None or positie in gekoppeld:
            extra = _bron_uit_kwitantie(record, gebruikt)
            extra["receipt_correlation"] = (
                _CORRELATIE_AMBIGU if ambigu else _CORRELATIE_ONGEKOPPELD
            )
            los.append(extra)
            continue
        gekoppeld.add(positie)
        bron = bronnen[positie]
        bron["receipt_correlation"] = _CORRELATIE_GEVERIFIEERD
        if gebruikt:
            _markeer_gebruikt(bron, record)
        else:
            _markeer_weggelaten(bron, record)

    for i, bron in enumerate(bronnen):
        if i in gekoppeld:
            continue
        bron["used_in_prompt"] = False
        bron["omitted_reason"] = _CORRELATIE_NIET_IN_KWITANTIE
        bron["receipt_correlation"] = _CORRELATIE_NIET_IN_KWITANTIE
        bron.pop("prompt_content", None)
        bron.pop("prompt_content_hash", None)
    return bronnen + los


def kwitantiefout(receipt: Any) -> str | None:
    """De verzamelfout die een kwitantie meldt, of None.

    Eén gedeelde lezer voor de async wrappers en de beoordelingsservice, zodat
    een `status: error` of niet-lege `errors`-lijst op beide grenzen dezelfde
    technische fout oplevert — ook zonder aangeleverde bronnen.
    """
    if not isinstance(receipt, Mapping):
        return None
    fouten = [f for f in receipt.get("errors") or [] if isinstance(f, Mapping)]
    if receipt.get("status") == "error" or fouten:
        beschrijving = (
            ", ".join(f"{f.get('stage', '?')}: {f.get('type', '?')}" for f in fouten)
            or "kwitantiestatus error"
        )
        return f"verzamelfout bij het aanleveren van bronnen ({beschrijving})"
    return None


def kwitantie_koppelrapport(gekoppeld: Any) -> dict[str, int]:
    """Telling van `receipt_correlation` over een gekoppelde bronlijst."""
    telling = {
        _CORRELATIE_GEVERIFIEERD: 0,
        _CORRELATIE_NIET_IN_KWITANTIE: 0,
        _CORRELATIE_ONGEKOPPELD: 0,
        _CORRELATIE_AMBIGU: 0,
    }
    for bron in gekoppeld or []:
        if isinstance(bron, Mapping):
            status = bron.get("receipt_correlation")
            if status in telling:
                telling[status] += 1
    return telling


def _correlatievelden(bron: dict[str, Any], record: Mapping[str, Any]) -> None:
    for veld in ("input_index", "original_content_hash"):
        if record.get(veld) is not None:
            bron[veld] = record[veld]


def _markeer_gebruikt(bron: dict[str, Any], record: Mapping[str, Any]) -> None:
    inhoud = record.get("content")
    bron["used_in_prompt"] = True
    if isinstance(inhoud, str):
        bron["prompt_content"] = inhoud
        bron["prompt_content_hash"] = bereken_inhoudshash(inhoud)
    nr = record.get("nr")
    if isinstance(nr, int) and not isinstance(nr, bool):
        bron["receipt_nr"] = nr
    for vlag in ("sanitized", "truncated"):
        if isinstance(record.get(vlag), bool):
            bron[vlag] = record[vlag]
    _correlatievelden(bron, record)
    bron.pop("omitted_reason", None)


def _markeer_weggelaten(bron: dict[str, Any], record: Mapping[str, Any]) -> None:
    bron["used_in_prompt"] = False
    bron["omitted_reason"] = _tekst(record.get("reason")) or "omitted"
    _correlatievelden(bron, record)
    bron.pop("prompt_content", None)
    bron.pop("prompt_content_hash", None)
    bron.pop("receipt_nr", None)


def _bron_uit_kwitantie(
    record: Mapping[str, Any], gebruikt: bool = True
) -> dict[str, Any]:
    """Een record zonder aantoonbare tegenhanger, met zijn identiteit intact.

    Nooit weggegooid: wat het model zag (of wat de kwitantie wegliet) blijft
    zichtbaar, maar zonder de rijke aangeleverde velden — die zijn er niet.
    """
    identity = record.get("identity")
    bron: dict[str, Any] = (
        deepcopy({str(k): v for k, v in identity.items()})
        if isinstance(identity, Mapping)
        else {}
    )
    soort = (_tekst(record.get("source_type")) or "").casefold()
    bron.setdefault("provider", _KWITANTIE_TYPE_NAAR_PROVIDER.get(soort, soort or None))
    ident = record.get("source_id")
    if ident is not None:
        if soort == "rag":
            bron.setdefault("chunk_id", ident)
        elif soort == "document":
            bron.setdefault("doc_id", ident)
        elif soort == "web":
            bron.setdefault("url", ident)
    if isinstance(record.get("content"), str):
        bron["snippet"] = record["content"]
    score = record.get("retrieval_score")
    if isinstance(score, int | float) and not isinstance(score, bool):
        bron["score"] = float(score)
    if gebruikt:
        _markeer_gebruikt(bron, record)
    else:
        _markeer_weggelaten(bron, record)
    return bron
