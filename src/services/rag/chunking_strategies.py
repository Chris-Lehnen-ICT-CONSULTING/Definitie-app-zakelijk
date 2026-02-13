"""
Chunking strategieën voor juridische en generieke documenten.

JuridischeChunkingStrategy: split op artikel-grenzen, sub-split op leden.
GeneriekChunkingStrategy: split op headings/paragrafen, merge kleine secties.
"""

from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from dataclasses import replace

from services.rag.legal_structure_recognizer import (
    JuridischeStructuur,
    LegalStructureRecognizer,
)
from services.rag.models import ChunkMetadata, DocumentChunk
from services.rag.token_counter import tel_tokens

logger = logging.getLogger(__name__)

# Defaults
MAX_TOKENS_PER_CHUNK = 1000
MIN_TOKENS_PER_CHUNK = 50
OVERLAP_RATIO_JURIDISCH = 0.12
OVERLAP_RATIO_GENERIEK = 0.10

# Abbreviation-safe sentence boundary: split on . ! ? followed by whitespace,
# but NOT after common Dutch/legal abbreviations.
_ZINSGRENS_RE = re.compile(
    r"(?<![Mm]r)(?<![Dd]r)(?<![Dd]rs)(?<![Ii]ng)(?<![Ii]r)"
    r"(?<![Aa]rt)(?<![Nn]r)(?<![Rr]esp)(?<![Bb]ijv)"
    r"(?<![Ee]vt)(?<![Zz]gn)"
    r"[.!?]\s+",
)


def _split_zinnen(tekst: str) -> list[str]:
    """Split tekst op zinsgrenzen, veilig voor Nederlandse afkortingen."""
    delen = _ZINSGRENS_RE.split(tekst.strip())
    return [d for d in delen if d]


# ── Overlap helper ───────────────────────────────────────────────


def _bereken_overlap(tekst: str, ratio: float) -> str:
    """
    Bereken overlap-tekst: neem ~ratio van de tekst, afgekapt op zinsgrens.

    Returns de laatste paar zinnen die samen ~ratio van de token count vormen.
    """
    if not tekst:
        return ""

    tokens_totaal = tel_tokens(tekst)
    doel_tokens = int(tokens_totaal * ratio)
    if doel_tokens < 5:
        return ""

    zinnen = _split_zinnen(tekst)
    if not zinnen:
        return ""

    # Neem zinnen van achteren tot we doel bereiken
    overlap_zinnen: list[str] = []
    token_count = 0
    for zin in reversed(zinnen):
        zin_tokens = tel_tokens(zin)
        if token_count + zin_tokens > doel_tokens and overlap_zinnen:
            break
        overlap_zinnen.insert(0, zin)
        token_count += zin_tokens

    return " ".join(overlap_zinnen)


# ── Abstract Strategy ────────────────────────────────────────────


class ChunkingStrategy(ABC):
    """Abstracte base class voor chunking strategieën."""

    @abstractmethod
    def chunk(
        self,
        tekst: str,
        bronbestand: str,
        bestandstype: str,
        rechtsgebied: str | None = None,
    ) -> list[DocumentChunk]:
        """Split tekst in chunks."""


# ── Juridische strategie ─────────────────────────────────────────


class JuridischeChunkingStrategy(ChunkingStrategy):
    """Split juridische teksten op artikel-grenzen."""

    def __init__(
        self,
        max_tokens: int = MAX_TOKENS_PER_CHUNK,
        min_tokens: int = MIN_TOKENS_PER_CHUNK,
        overlap_ratio: float = OVERLAP_RATIO_JURIDISCH,
    ):
        self.max_tokens = max_tokens
        self.min_tokens = min_tokens
        self.overlap_ratio = overlap_ratio
        self._recognizer = LegalStructureRecognizer()

    def chunk(
        self,
        tekst: str,
        bronbestand: str,
        bestandstype: str,
        rechtsgebied: str | None = None,
    ) -> list[DocumentChunk]:
        if not tekst or not tekst.strip():
            return []

        structuur = self._recognizer.detecteer_structuur(tekst)
        wet_naam = self._recognizer.detecteer_wet_naam(tekst)

        if not structuur:
            # Fallback: hele tekst als 1 chunk
            return self._maak_enkele_chunk(tekst, bronbestand, rechtsgebied, wet_naam)

        chunks: list[DocumentChunk] = []
        vorige_tekst = ""

        for elem in structuur:
            elem_chunks = self._chunk_element(
                elem, bronbestand, rechtsgebied, wet_naam, vorige_tekst
            )
            chunks.extend(elem_chunks)
            vorige_tekst = elem.tekst

        # Verwijder chunks onder minimum
        chunks = self._merge_kleine_chunks(chunks)

        # Hernummer chunk indices (frozen: create new instances)
        return [
            DocumentChunk(
                tekst=c.tekst,
                metadata=replace(c.metadata, chunk_index=i),
                token_count=c.token_count,
                overlap_tekst=c.overlap_tekst,
            )
            for i, c in enumerate(chunks)
        ]

    def _chunk_element(
        self,
        elem: JuridischeStructuur,
        bronbestand: str,
        rechtsgebied: str | None,
        wet_naam: str | None,
        vorige_tekst: str,
    ) -> list[DocumentChunk]:
        """Chunk een enkel structuur-element."""
        token_count = tel_tokens(elem.tekst)

        # Definitieblokken: altijd atomic
        if elem.type == "definitieblok":
            return [
                self._maak_chunk(
                    elem.tekst,
                    bronbestand,
                    rechtsgebied,
                    wet_naam,
                    elem,
                    token_count,
                    vorige_tekst,
                    0,
                )
            ]

        # Hoofdstukken/afdelingen/paragrafen/bijlagen/titels/boeken: als label
        if elem.type in (
            "hoofdstuk",
            "afdeling",
            "paragraaf",
            "bijlage",
            "titel",
            "boek",
        ):
            return [
                self._maak_chunk(
                    elem.tekst,
                    bronbestand,
                    rechtsgebied,
                    wet_naam,
                    elem,
                    token_count,
                    vorige_tekst,
                    0,
                )
            ]

        # Artikel <= max_tokens: 1 chunk
        if token_count <= self.max_tokens:
            return [
                self._maak_chunk(
                    elem.tekst,
                    bronbestand,
                    rechtsgebied,
                    wet_naam,
                    elem,
                    token_count,
                    vorige_tekst,
                    0,
                )
            ]

        # Artikel > max_tokens: split op leden
        return self._split_op_leden(
            elem, bronbestand, rechtsgebied, wet_naam, vorige_tekst
        )

    def _split_op_leden(
        self,
        elem: JuridischeStructuur,
        bronbestand: str,
        rechtsgebied: str | None,
        wet_naam: str | None,
        vorige_tekst: str,
    ) -> list[DocumentChunk]:
        """Split een groot artikel op lid-grenzen."""
        leden = self._recognizer.detecteer_leden(elem.tekst)

        if not leden:
            # Geen leden gevonden, forceer split op zinsgrenzen
            return self._forceer_split(
                elem.tekst,
                bronbestand,
                rechtsgebied,
                wet_naam,
                elem,
                vorige_tekst,
            )

        chunks: list[DocumentChunk] = []
        vorige = vorige_tekst

        for i, lid in enumerate(leden):
            lid_tokens = tel_tokens(lid.tekst)
            chunk = self._maak_chunk(
                lid.tekst,
                bronbestand,
                rechtsgebied,
                wet_naam,
                elem,
                lid_tokens,
                vorige,
                i,
                lid_nummer=lid.nummer,
                structuur_type="lid",
            )
            chunks.append(chunk)
            vorige = lid.tekst

        return chunks

    def _forceer_split(
        self,
        tekst: str,
        bronbestand: str,
        rechtsgebied: str | None,
        wet_naam: str | None,
        elem: JuridischeStructuur,
        vorige_tekst: str,
    ) -> list[DocumentChunk]:
        """Forceer split op zinsgrenzen wanneer geen leden beschikbaar zijn."""
        zinnen = _split_zinnen(tekst)
        chunks: list[DocumentChunk] = []
        huidige_tekst_delen: list[str] = []
        huidige_tokens = 0
        vorige = vorige_tekst
        sub_index = 0

        for zin in zinnen:
            zin_tokens = tel_tokens(zin)
            if huidige_tokens + zin_tokens > self.max_tokens and huidige_tekst_delen:
                chunk_tekst = " ".join(huidige_tekst_delen)
                chunk = self._maak_chunk(
                    chunk_tekst,
                    bronbestand,
                    rechtsgebied,
                    wet_naam,
                    elem,
                    huidige_tokens,
                    vorige,
                    sub_index,
                )
                chunks.append(chunk)
                vorige = chunk_tekst
                huidige_tekst_delen = []
                huidige_tokens = 0
                sub_index += 1

            huidige_tekst_delen.append(zin)
            huidige_tokens += zin_tokens

        # Laatste rest
        if huidige_tekst_delen:
            chunk_tekst = " ".join(huidige_tekst_delen)
            chunk = self._maak_chunk(
                chunk_tekst,
                bronbestand,
                rechtsgebied,
                wet_naam,
                elem,
                tel_tokens(chunk_tekst),
                vorige,
                sub_index,
            )
            chunks.append(chunk)

        return chunks

    def _maak_chunk(
        self,
        tekst: str,
        bronbestand: str,
        rechtsgebied: str | None,
        wet_naam: str | None,
        elem: JuridischeStructuur,
        token_count: int,
        vorige_tekst: str,
        sub_index: int,
        lid_nummer: str | None = None,
        structuur_type: str | None = None,
    ) -> DocumentChunk:
        """Maak een DocumentChunk aan met metadata en overlap."""
        overlap = _bereken_overlap(vorige_tekst, self.overlap_ratio)

        metadata = ChunkMetadata(
            bronbestand=bronbestand,
            chunk_index=sub_index,
            pagina_nummer=elem.pagina_nummer,
            rechtsgebied=rechtsgebied,
            wet_regeling=wet_naam,
            artikel_nummer=(
                elem.nummer if elem.type in ("artikel", "definitieblok") else None
            ),
            lid_nummer=lid_nummer,
            structuur_type=structuur_type or elem.type,
        )

        return DocumentChunk(
            tekst=tekst,
            metadata=metadata,
            token_count=token_count,
            overlap_tekst=overlap,
        )

    def _maak_enkele_chunk(
        self,
        tekst: str,
        bronbestand: str,
        rechtsgebied: str | None,
        wet_naam: str | None,
    ) -> list[DocumentChunk]:
        """Fallback: hele tekst als 1 chunk."""
        metadata = ChunkMetadata(
            bronbestand=bronbestand,
            chunk_index=0,
            rechtsgebied=rechtsgebied,
            wet_regeling=wet_naam,
            structuur_type="generiek",
        )
        return [
            DocumentChunk(
                tekst=tekst.strip(),
                metadata=metadata,
                token_count=tel_tokens(tekst),
            )
        ]

    def _merge_kleine_chunks(self, chunks: list[DocumentChunk]) -> list[DocumentChunk]:
        """Merge chunks die onder het minimum token count zitten."""
        if len(chunks) <= 1:
            return chunks

        merged: list[DocumentChunk] = []
        for chunk in chunks:
            if (
                merged
                and chunk.token_count < self.min_tokens
                and merged[-1].token_count + chunk.token_count <= self.max_tokens
            ):
                # Merge met vorige chunk (frozen: create new instance)
                prev = merged[-1]
                combined = prev.tekst + "\n\n" + chunk.tekst
                combined_tokens = tel_tokens(combined)
                merged[-1] = DocumentChunk(
                    tekst=combined,
                    metadata=prev.metadata,
                    token_count=combined_tokens,
                    overlap_tekst=prev.overlap_tekst,
                )
            else:
                merged.append(chunk)

        return merged


# ── Generieke strategie ──────────────────────────────────────────


class GeneriekChunkingStrategy(ChunkingStrategy):
    """Split niet-juridische teksten op headings en paragrafen."""

    def __init__(
        self,
        max_tokens: int = MAX_TOKENS_PER_CHUNK,
        min_tokens: int = MIN_TOKENS_PER_CHUNK,
        overlap_ratio: float = OVERLAP_RATIO_GENERIEK,
    ):
        self.max_tokens = max_tokens
        self.min_tokens = min_tokens
        self.overlap_ratio = overlap_ratio

    def chunk(
        self,
        tekst: str,
        bronbestand: str,
        bestandstype: str,
        rechtsgebied: str | None = None,
    ) -> list[DocumentChunk]:
        if not tekst or not tekst.strip():
            return []

        secties = self._split_op_headings(tekst)
        secties = self._merge_kleine_secties(secties)

        chunks: list[DocumentChunk] = []
        vorige_tekst = ""

        for i, sectie_tekst in enumerate(secties):
            token_count = tel_tokens(sectie_tekst)
            overlap = _bereken_overlap(vorige_tekst, self.overlap_ratio)

            # Detecteer sectie heading
            heading = self._extract_heading(sectie_tekst)

            metadata = ChunkMetadata(
                bronbestand=bronbestand,
                chunk_index=i,
                sectie=heading,
                rechtsgebied=rechtsgebied,
                structuur_type="generiek",
            )

            chunks.append(
                DocumentChunk(
                    tekst=sectie_tekst.strip(),
                    metadata=metadata,
                    token_count=token_count,
                    overlap_tekst=overlap,
                )
            )
            vorige_tekst = sectie_tekst

        return chunks

    def _split_op_headings(self, tekst: str) -> list[str]:
        """Split tekst op heading-grenzen (Markdown #, blank+CAPS)."""
        pattern = re.compile(
            r"(?:^|\n)(?=#{1,6}\s|\n[A-Z][A-Z\s]{3,}\n)",
        )

        delen = pattern.split(tekst)
        return [d.strip() for d in delen if d.strip()]

    def _merge_kleine_secties(self, secties: list[str]) -> list[str]:
        """Merge secties die onder het minimum token count zitten."""
        if len(secties) <= 1:
            return secties

        merged: list[str] = []
        for sectie in secties:
            tokens = tel_tokens(sectie)
            if merged and tokens < self.min_tokens:
                merged[-1] = merged[-1] + "\n\n" + sectie
            else:
                merged.append(sectie)

        # Check of de laatste nog te klein is
        if len(merged) > 1 and tel_tokens(merged[-1]) < self.min_tokens:
            merged[-2] = merged[-2] + "\n\n" + merged[-1]
            merged.pop()

        return merged

    @staticmethod
    def _extract_heading(tekst: str) -> str | None:
        """Extraheer heading uit begin van sectie tekst."""
        eerste_regel = tekst.strip().split("\n")[0].strip()
        # Markdown heading
        if eerste_regel.startswith("#"):
            return eerste_regel.lstrip("#").strip()
        # ALL-CAPS heading
        if eerste_regel.isupper() and len(eerste_regel) > 3:
            return eerste_regel
        return None
