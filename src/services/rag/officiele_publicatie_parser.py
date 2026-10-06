"""Parser voor wetteksten in het formaat van de officiële publicaties (DEF-620).

RAG fase 2: wetten worden niet meer uit een pdf geknipt, maar per artikel uit
de XML van de officiële publicatie (Staatsblad, OP-schema
``op-xsd-2014-05-15``, wortel ``officiele-publicatie``). Elk artikel wordt één
chunk met een kopregel die de plaats in de wet noemt (wet › boek › hoofdstuk
› … › artikel). Definitielijsten ("In dit wetboek wordt verstaan onder:")
leveren daarnaast één chunk per definitie.

Formele artikelen van een vaststellingswet (Romeins genummerd, bv. "ARTIKEL
IV: Deze wet treedt in werking …") horen niet bij de wettekst zelf en worden
overgeslagen.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from services.rag.models import ChunkingResult, ChunkMetadata, DocumentChunk
from services.rag.token_counter import tel_tokens

_STRUCTUUR_LABELS = ("boek", "hoofdstuk", "titel", "afdeling", "paragraaf")
# Formele artikelen van een vaststellingswet: "IV", "V", ook met lettersuffix ("IIIA").
_ROMEINS = re.compile(r"^[IVXLCDM]+[A-Z]?$", re.IGNORECASE)
_BOEK_IN_WAT = re.compile(r"\bBoek (\d+)\b")
_WITRUIMTE = re.compile(r"\s+")


# Blokelementen krijgen een spatie eromheen; inline-elementen (nadruk, extref,
# sup, …) worden zonder extra spatie aan de lopende tekst geplakt.
_BLOK = {
    "al", "lid", "lidnr", "lijst", "li", "li.nr", "definitielijst",
    "definitie-item", "term", "definitie", "kop", "label", "nr", "titel",
    "tussenkop", "table", "row", "entry",
}  # fmt: skip
_SPATIE_VOOR_LEESTEKEN = re.compile(r"\s+([,.;:)])")


def _verzamel(element: ET.Element, delen: list[str]) -> None:
    delen.append(element.text or "")
    for kind in element:
        blok = kind.tag in _BLOK
        if blok:
            delen.append(" ")
        _verzamel(kind, delen)
        if blok:
            delen.append(" ")
        delen.append(kind.tail or "")


def _tekst(element: ET.Element | None) -> str:
    """Alle tekst van een element: blokken gescheiden door één spatie, inline
    opmaak zonder extra spatie, geen spatie vóór leestekens."""
    if element is None:
        return ""
    delen: list[str] = []
    _verzamel(element, delen)
    tekst = _WITRUIMTE.sub(" ", "".join(delen)).strip()
    return _SPATIE_VOOR_LEESTEKEN.sub(r"\1", tekst)


def _zin(tekst: str) -> str:
    """Kopteksten in hoofdletters ("STRAFVORDERING IN HET ALGEMEEN") naar zinsvorm."""
    if tekst.isupper():
        return tekst[:1] + tekst[1:].lower()
    return tekst


def _kop_omschrijving(element: ET.Element) -> str | None:
    """ "Boek 1 Strafvordering in het algemeen" voor een structuurelement."""
    kop = element.find("kop")
    if kop is None:
        return None
    label = _tekst(kop.find("label")).lower()
    if label not in _STRUCTUUR_LABELS:
        return None
    nr = _tekst(kop.find("nr"))
    titel = _zin(_tekst(kop.find("titel")))
    return " ".join(d for d in (label.capitalize(), nr, titel) if d)


def _artikel_inhoud(artikel: ET.Element) -> str:
    """Artikeltekst zonder de kop (label/nummer), lid- en onderdeelnummers behouden."""
    delen = [_tekst(kind) for kind in artikel if kind.tag != "kop"]
    return " ".join(d for d in delen if d)


def _definities(artikel: ET.Element) -> list[tuple[str, str, str]]:
    """(onderdeel, term, definitie) per definitie-item in het artikel."""
    items = []
    for item in artikel.iter("definitie-item"):
        onderdeel = _tekst(item.find("li.nr")).rstrip(".")
        if not any(teken.isalnum() for teken in onderdeel):
            onderdeel = ""  # ongemarkeerde lijst ("–")
        term = _tekst(item.find("term")).rstrip(":").strip()
        definitie = _tekst(item.find("definitie"))
        if term and definitie:
            items.append((onderdeel, term, definitie))
    return items


def parse_officiele_publicatie(
    pad: str | Path,
    wet_regeling: str,
    rechtsgebied: str | None = None,
) -> ChunkingResult:
    """Lees een officiële publicatie (XML) en lever chunks per artikel.

    Args:
        pad: XML-bestand van de officiële publicatie.
        wet_regeling: naam van de wet zoals die in de bron getoond wordt,
            bijv. "Wetboek van Strafvordering (nieuw, i.w.t. 1-4-2029)".
        rechtsgebied: genormaliseerd rechtsgebied (bijv. "strafrecht").

    Returns:
        ChunkingResult met per artikel één chunk (``structuur_type="artikel"``)
        en per definitie-item één chunk (``structuur_type="definitie"``). Bij een
        onleesbaar bestand: lege chunks en ``fout_melding``.
    """
    bestand = Path(pad)
    try:
        wortel = ET.parse(bestand).getroot()
    except (ET.ParseError, OSError) as fout:
        return ChunkingResult(
            bronbestand=bestand.name,
            bestandstype="application/xml",
            fout_melding=f"XML onleesbaar: {fout}",
        )

    ouder = {kind: element for element in wortel.iter() for kind in element}
    chunks: list[DocumentChunk] = []

    def _maak(tekst: str, artikel_nr: str, structuur: str, sectie: str) -> None:
        chunks.append(
            DocumentChunk(
                tekst=tekst,
                metadata=ChunkMetadata(
                    bronbestand=bestand.name,
                    chunk_index=len(chunks),
                    sectie=sectie or None,
                    rechtsgebied=rechtsgebied,
                    wet_regeling=wet_regeling,
                    artikel_nummer=artikel_nr,
                    structuur_type=structuur,
                ),
                token_count=tel_tokens(tekst),
            )
        )

    for artikel in wortel.iter("artikel"):
        nr = _tekst(artikel.find("kop/nr"))
        if not nr or _ROMEINS.match(nr):
            continue  # formeel artikel van de vaststellingswet
        inhoud = _artikel_inhoud(artikel)
        if not inhoud:
            continue

        plaats: list[str] = []
        boek_uit_wat: str | None = None
        element = ouder.get(artikel)
        while element is not None:
            omschrijving = _kop_omschrijving(element)
            if omschrijving:
                plaats.append(omschrijving)
            if element.tag == "wijzig-artikel" and boek_uit_wat is None:
                # Vaststellingswet: "Boek 1, Hoofdstuk 10, van het Wetboek …
                # komt te luiden:" — de boekcontext staat alleen in <wat>.
                gevonden = _BOEK_IN_WAT.search(_tekst(element.find("wat")))
                boek_uit_wat = f"Boek {gevonden.group(1)}" if gevonden else None
            element = ouder.get(element)
        plaats.reverse()
        if boek_uit_wat and not any(d.startswith("Boek ") for d in plaats):
            plaats.insert(0, boek_uit_wat)
        sectie = " › ".join(plaats)
        kopregel = " — ".join(d for d in (wet_regeling, sectie) if d)

        _maak(f"{kopregel} › Artikel {nr}\n{inhoud}", nr, "artikel", sectie)
        for onderdeel, term, definitie in _definities(artikel):
            verwijzing = f"artikel {nr}" + (f", onder {onderdeel}" if onderdeel else "")
            _maak(
                f"{wet_regeling} — definitie ({verwijzing})\n{term}: {definitie}",
                nr,
                "definitie",
                sectie,
            )

    return ChunkingResult(
        chunks=tuple(chunks),
        bronbestand=bestand.name,
        bestandstype="application/xml",
        totaal_tokens=sum(c.token_count for c in chunks),
        juridisch_document=True,
    )
