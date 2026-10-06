"""Parser voor EU-verordeningen uit Cellar (publications.europa.eu) (DEF-620).

RAG fase 3: EU-verordeningen (AVG, eIDAS) worden in het Nederlands opgehaald
als XHTML uit de Cellar-repository van het Publicatiebureau, zowel het
oorspronkelijke Publicatieblad (``oj-*``-opmaak) als de geconsolideerde tekst
(CONVEX-opmaak). Beide markeren een artikel als ``<div id="art_N">``, een
hoofdstuk als ``cpt_X`` en een afdeling als ``cpt_X.sct_Y``.

Per artikel één chunk met een kopregel (verordening › hoofdstuk › afdeling ›
artikel en titel). Overwegingen, bijlagen, voetnoten en de wijzigingsmarkeringen
van de consolidatie (▼B, ▼M2) gaan niet mee. Definitieartikelen ("„term”:
omschrijving") leveren daarnaast één chunk per begrip.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from services.rag.models import ChunkingResult, ChunkMetadata, DocumentChunk
from services.rag.token_counter import tel_tokens

_NS = "{http://www.w3.org/1999/xhtml}"
_ARTIKEL_ID = re.compile(r"^art_[^.]+$")
_STRUCTUUR_ID = re.compile(r"^(cpt|tis|sct|sub)_[^.]+(\.(sct|sub)_[^.]+)*$")
_KOP_ARTIKEL = {"oj-ti-art", "title-article-norm"}
_SUBKOP_ARTIKEL = {"oj-sti-art", "stitle-article-norm"}
_KOP_STRUCTUUR = (
    "oj-ti-section-1", "oj-ti-section-2", "title-division-1", "title-division-2",
)  # fmt: skip
_OVERSLAAN_KLASSEN = {"modref", "footnote", "oj-note", "arrow", "oj-note-tag"}
_MARKERING = re.compile(r"▼\s*[A-Z]\d*")
_WITRUIMTE = re.compile(r"\s+")
_SPATIE_VOOR_LEESTEKEN = re.compile(r"\s+([,.;:)”])")
_ROMEINS = re.compile(r"^[IVXLCDM]+$")
_DEFINITIE = re.compile(
    r"(?:^|\s)(?P<nr>\d+\s?(?:bis|ter|quater|quinquies|sexies|septies|octies|nonies|"
    r"decies|[a-z])?)\s?[.)]\s*„(?P<term>[^”]{1,150})”(?P<rest>[^:„;.]{0,60}?)\s*:\s*"
)


def _klassen(element: ET.Element) -> set[str]:
    return set((element.get("class") or "").split())


#: Blokelementen krijgen een spatie eromheen; inline-opmaak (span, a, sup, …)
#: wordt aaneengesloten, zodat "hand<span>tekening</span>" één woord blijft.
_BLOK = {
    f"{_NS}{t}"
    for t in ("p", "div", "td", "th", "tr", "table", "li", "ul", "ol", "br", "dd", "dt")
}


def _verzamel(element: ET.Element, delen: list[str]) -> None:
    delen.append(element.text or "")
    for kind in element:
        if _klassen(kind) & _OVERSLAAN_KLASSEN:
            delen.append(kind.tail or "")
            continue
        blok = kind.tag in _BLOK
        if blok:
            delen.append(" ")
        _verzamel(kind, delen)
        if blok:
            delen.append(" ")
        delen.append(kind.tail or "")


def _tekst(element: ET.Element | None) -> str:
    if element is None:
        return ""
    delen: list[str] = []
    _verzamel(element, delen)
    tekst = _MARKERING.sub(" ", "".join(delen))
    tekst = _WITRUIMTE.sub(" ", tekst).strip()
    return _SPATIE_VOOR_LEESTEKEN.sub(r"\1", tekst)


def _kop_zin(tekst: str) -> str:
    """ "HOOFDSTUK III" → "Hoofdstuk III"; "VERTROUWENSDIENSTEN" → "Vertrouwensdiensten"."""
    woorden = tekst.split()
    if not woorden or not tekst.isupper():
        return tekst
    uit = [woorden[0].capitalize()]
    for woord in woorden[1:]:
        uit.append(woord if _ROMEINS.match(woord) else woord.lower())
    return " ".join(uit)


def _structuur_omschrijving(div: ET.Element) -> str | None:
    """Kop van een hoofdstuk of afdeling: "Hoofdstuk III Rechten van de betrokkene"."""
    delen: list[str] = []
    for kind in div:
        klassen = _klassen(kind)
        is_kop = kind.tag == f"{_NS}p" and bool(klassen & set(_KOP_STRUCTUUR))
        is_titel = kind.tag == f"{_NS}div" and "eli-title" in klassen
        if is_kop or is_titel:
            delen.append(_kop_zin(_tekst(kind)))
        elif kind.tag == f"{_NS}div" and kind.get("id"):
            break  # eerste onderliggende afdeling of artikel: kop is voorbij
    tekst = " ".join(d for d in delen if d)
    return tekst or None


def _artikel_delen(artikel: ET.Element) -> tuple[str, str, str]:
    """(nummer, titel, tekst) van een artikel-div."""
    kop = titel = ""
    tekstdelen: list[str] = []
    for kind in artikel:
        klassen = _klassen(kind)
        if klassen & _KOP_ARTIKEL and not kop:
            kop = _tekst(kind)
        elif not titel and ("eli-title" in klassen or klassen & _SUBKOP_ARTIKEL):
            titel = _tekst(kind)
        elif not klassen & _OVERSLAAN_KLASSEN:
            deel = _tekst(kind)
            if deel:
                tekstdelen.append(deel)
    nummer = re.sub(r"^Artikel\s+", "", kop).strip()
    return nummer, titel, " ".join(tekstdelen)


def _definities(tekst: str) -> list[tuple[str, str, str]]:
    """(onderdeel, term, omschrijving) uit "1) „term”: omschrijving; 2) …"."""
    treffers = list(_DEFINITIE.finditer(tekst))
    items = []
    for i, treffer in enumerate(treffers):
        einde = treffers[i + 1].start() if i + 1 < len(treffers) else len(tekst)
        omschrijving = tekst[treffer.end() : einde].strip()
        if omschrijving:
            term = f"{treffer.group('term')} {treffer.group('rest').strip()}".strip()
            items.append((treffer.group("nr").replace(" ", ""), term, omschrijving))
    return items


def parse_eu_xhtml(
    pad: str | Path,
    wet_regeling: str,
    rechtsgebied: str | None = None,
) -> ChunkingResult:
    """Lees een EU-verordening (Cellar-XHTML) en lever chunks per artikel."""
    bestand = Path(pad)
    try:
        wortel = ET.parse(bestand).getroot()
    except (ET.ParseError, OSError) as fout:
        return ChunkingResult(
            bronbestand=bestand.name,
            bestandstype="application/xhtml+xml",
            fout_melding=f"XHTML onleesbaar: {fout}",
        )
    ouder = {kind: element for element in wortel.iter() for kind in element}
    chunks: list[DocumentChunk] = []

    def _maak(tekst: str, nr: str, structuur: str, sectie: str) -> None:
        chunks.append(
            DocumentChunk(
                tekst=tekst,
                metadata=ChunkMetadata(
                    bronbestand=bestand.name,
                    chunk_index=len(chunks),
                    sectie=sectie or None,
                    rechtsgebied=rechtsgebied,
                    wet_regeling=wet_regeling,
                    artikel_nummer=nr,
                    structuur_type=structuur,
                ),
                token_count=tel_tokens(tekst),
            )
        )

    for artikel in wortel.iter(f"{_NS}div"):
        if not _ARTIKEL_ID.match(artikel.get("id") or ""):
            continue
        nummer, titel, inhoud = _artikel_delen(artikel)
        if not nummer or not inhoud:
            continue
        plaats: list[str] = []
        element = ouder.get(artikel)
        bijlage = False
        while element is not None:
            eid = element.get("id") or ""
            if eid.startswith("anx_"):
                bijlage = True
            if _STRUCTUUR_ID.match(eid):
                omschrijving = _structuur_omschrijving(element)
                if omschrijving:
                    plaats.append(omschrijving)
            element = ouder.get(element)
        if bijlage:
            continue
        sectie = " › ".join(reversed(plaats))
        kopregel = " — ".join(d for d in (wet_regeling, sectie) if d)
        artikelkop = " ".join(d for d in (f"Artikel {nummer}", titel) if d)
        _maak(f"{kopregel} › {artikelkop}\n{inhoud}", nummer, "artikel", sectie)
        if titel.lower().startswith("definities") or "verstaan onder" in inhoud:
            for onderdeel, term, omschrijving in _definities(inhoud):
                _maak(
                    f"{wet_regeling} — definitie (artikel {nummer}, punt {onderdeel})"
                    f"\n{term}: {omschrijving}",
                    nummer,
                    "definitie",
                    sectie,
                )

    return ChunkingResult(
        chunks=tuple(chunks),
        bronbestand=bestand.name,
        bestandstype="application/xhtml+xml",
        totaal_tokens=sum(c.token_count for c in chunks),
        juridisch_document=True,
    )
