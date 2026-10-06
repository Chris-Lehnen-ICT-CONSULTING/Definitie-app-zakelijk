"""Parser voor geldende wetteksten uit het Basiswettenbestand (BWB) (DEF-620).

RAG fase 3: wetten worden ingelezen uit de XML van een BWB-toestand
(wetten.overheid.nl, schema ``toestand_2016-1``, wortel ``toestand``). De
opbouw is vrijwel gelijk aan die van de officiële publicatie (boek, titeldeel,
hoofdstuk, afdeling, paragraaf, artikel, lid, lijst); de tekstextractie wordt
gedeeld met ``officiele_publicatie_parser``.

Per geldend artikel één chunk met een kopregel die de plaats in de wet noemt
(en de artikeltitel, als die er is); vervallen en nog niet in werking getreden
artikelen (``status="vervallen"``/``"nogniet"``), artikelen die alleen een
redactionele noot hebben ("Vervallen.", "Wijzigt de …") en metagegevens gaan
niet mee.
Begripsbepalingen ("... wordt verstaan onder: a. term: omschrijving") leveren
daarnaast één chunk per begrip.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from itertools import pairwise
from pathlib import Path

from services.rag.models import ChunkingResult, ChunkMetadata, DocumentChunk
from services.rag.officiele_publicatie_parser import (
    _OVERSLAAN,
    _artikel_inhoud,
    _tekst,
    _zin,
)
from services.rag.token_counter import tel_tokens

#: Structuurelementen met een kop; de tag bepaalt het niveau, het label de tekst.
_STRUCTUUR_TAGS = {
    "boek", "titeldeel", "hoofdstuk", "afdeling", "paragraaf", "divisie", "bijlage",
}  # fmt: skip
_STANDAARD_LABEL = {
    "boek": "Boek", "titeldeel": "Titel", "hoofdstuk": "Hoofdstuk",
    "afdeling": "Afdeling", "paragraaf": "Paragraaf", "divisie": "", "bijlage": "Bijlage",
}  # fmt: skip
#: Artikelen die (nog) niet gelden: vervallen of nog niet in werking getreden.
_NIET_GELDEND = {"vervallen", "nogniet"}
_VERSTAAN_ONDER = re.compile(r"verstaan\s+onder\s*:?\s*$", re.IGNORECASE)
_TERM_DEFINITIE = re.compile(
    r"^(?P<term>[^:;]{1,120}?)\s*:\s*(?P<def>\S.*)$", re.DOTALL
)


def _structuur_omschrijving(element: ET.Element) -> str | None:
    """ "Boek 1 Personen- en familierecht" voor een structuurelement met kop."""
    if element.tag not in _STRUCTUUR_TAGS:
        return None
    kop = element.find("kop")
    if kop is None:
        return None
    label = _tekst(kop.find("label")) or _STANDAARD_LABEL[element.tag]
    if label.isupper() or label.islower():
        label = label.capitalize()
    nr = _tekst(kop.find("nr"))
    titel = _zin(_tekst(kop.find("titel")))
    tekst = " ".join(d for d in (label, nr, titel) if d)
    return tekst or None


def _begripsbepalingen(artikel: ET.Element) -> list[tuple[str, str, str]]:
    """(onderdeel, term, omschrijving) uit lijsten na "wordt verstaan onder:"."""
    items: list[tuple[str, str, str]] = []
    for ouder in artikel.iter():
        kinderen = [k for k in ouder if k.tag not in _OVERSLAAN]
        for vorige, lijst in pairwise(kinderen):
            if lijst.tag != "lijst" or vorige.tag != "al":
                continue
            if not _VERSTAAN_ONDER.search(_tekst(vorige)):
                continue
            for li in lijst.findall("li"):
                onderdeel = _tekst(li.find("li.nr")).rstrip(".")
                if not any(t.isalnum() for t in onderdeel):
                    onderdeel = ""
                inhoud = " ".join(
                    _tekst(k) for k in li if k.tag not in ("li.nr", *_OVERSLAAN)
                ).strip()
                gevonden = _TERM_DEFINITIE.match(inhoud)
                if not gevonden:
                    continue
                term = gevonden.group("term").strip()
                omschrijving = gevonden.group("def").strip()
                if term and omschrijving:
                    items.append((onderdeel, term, omschrijving))
    return items


def parse_bwb_toestand(
    pad: str | Path,
    wet_regeling: str,
    rechtsgebied: str | None = None,
) -> ChunkingResult:
    """Lees een BWB-toestand (XML) en lever chunks per geldend artikel.

    Args:
        pad: XML-bestand van de toestand (repository.officiele-overheidspublicaties.nl).
        wet_regeling: naam zoals in de bron getoond, bijv.
            "Wetboek van Strafvordering (geldend, versie 1-7-2026)".
        rechtsgebied: genormaliseerd rechtsgebied (bijv. "strafrecht").
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
    if wortel.tag != "toestand":
        return ChunkingResult(
            bronbestand=bestand.name,
            bestandstype="application/xml",
            fout_melding=f"geen BWB-toestand (wortel {wortel.tag!r})",
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

    for artikel in wortel.iter("artikel"):
        if artikel.get("status") in _NIET_GELDEND:
            continue
        nr = _tekst(artikel.find("kop/nr"))
        titel = _tekst(artikel.find("kop/titel"))
        inhoud = _artikel_inhoud(artikel)
        if not nr or not inhoud:
            continue
        plaats: list[str] = []
        element = ouder.get(artikel)
        while element is not None:
            omschrijving = _structuur_omschrijving(element)
            if omschrijving:
                plaats.append(omschrijving)
            element = ouder.get(element)
        sectie = " › ".join(reversed(plaats))
        kopregel = " — ".join(d for d in (wet_regeling, sectie) if d)
        artikelkop = " ".join(d for d in (f"Artikel {nr}", titel) if d)
        _maak(f"{kopregel} › {artikelkop}\n{inhoud}", nr, "artikel", sectie)
        for onderdeel, term, omschrijving in _begripsbepalingen(artikel):
            verwijzing = f"artikel {nr}" + (f", onder {onderdeel}" if onderdeel else "")
            _maak(
                f"{wet_regeling} — definitie ({verwijzing})\n{term}: {omschrijving}",
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
