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

from services.rag.chunking_utils import (
    MAX_TOKENS_PER_CHUNK,
    MIN_TOKENS_PER_CHUNK,
    OVERLAP_RATIO_GENERIEK,
    OVERLAP_RATIO_JURIDISCH,
    bereken_overlap,
    forceer_split_op_zinnen,
)
from services.rag.legal_structure_recognizer import (
    JuridischeStructuur,
    LegalStructureRecognizer,
)
from services.rag.models import ChunkMetadata, DocumentChunk
from services.rag.token_counter import tel_tokens

logger = logging.getLogger(__name__)


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

        # Recognizer eerst: detecteert pagina-grenzen via \f chars,
        # normaliseert daarna intern voor regex matching.
        structuur = self._recognizer.detecteer_structuur(tekst)
        wet_naam = self._recognizer.detecteer_wet_naam(tekst)

        # Normaliseer formfeeds NA detectie, zodat chunk-tekst
        # geen \f meer bevat (fallback paden).
        tekst = tekst.replace("\f", "\n")

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
        """Split een groot artikel op numerieke lid-grenzen.

        Letter-leden (a., b.) worden niet als splitpunt gebruikt:
        ze blijven onderdeel van hun parent-lid.
        """
        leden = self._recognizer.detecteer_leden(elem.tekst, include_letter_leden=False)

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
        delen = forceer_split_op_zinnen(tekst, self.max_tokens)
        chunks: list[DocumentChunk] = []
        vorige = vorige_tekst

        for i, deel in enumerate(delen):
            chunk = self._maak_chunk(
                deel,
                bronbestand,
                rechtsgebied,
                wet_naam,
                elem,
                tel_tokens(deel),
                vorige,
                i,
            )
            chunks.append(chunk)
            vorige = deel

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
        overlap = bereken_overlap(vorige_tekst, self.overlap_ratio)

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

        # Normaliseer formfeeds (PDF page breaks) naar newlines.
        tekst = tekst.replace("\f", "\n")

        secties = self._split_op_headings(tekst)
        secties = self._merge_kleine_secties(secties)

        chunks: list[DocumentChunk] = []
        vorige_tekst = ""
        chunk_index = 0

        for sectie_tekst in secties:
            token_count = tel_tokens(sectie_tekst)

            if token_count <= self.max_tokens:
                # Sectie past in één chunk
                overlap = bereken_overlap(vorige_tekst, self.overlap_ratio)
                heading = self._extract_heading(sectie_tekst)
                metadata = ChunkMetadata(
                    bronbestand=bronbestand,
                    chunk_index=chunk_index,
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
                chunk_index += 1
            else:
                # Sectie te groot: split op paragraaf-grenzen, daarna zinsgrenzen
                sub_chunks = self._split_grote_sectie(
                    sectie_tekst, bronbestand, rechtsgebied, vorige_tekst, chunk_index
                )
                chunks.extend(sub_chunks)
                if sub_chunks:
                    vorige_tekst = sub_chunks[-1].tekst
                    chunk_index += len(sub_chunks)

        return chunks

    def _split_grote_sectie(
        self,
        sectie_tekst: str,
        bronbestand: str,
        rechtsgebied: str | None,
        vorige_tekst: str,
        start_index: int,
    ) -> list[DocumentChunk]:
        """Split een te grote sectie op paragraaf-grenzen, dan zinsgrenzen."""
        heading = self._extract_heading(sectie_tekst)

        # Stap 1: split op paragraaf-grenzen (\n\n)
        paragrafen = [p.strip() for p in sectie_tekst.split("\n\n") if p.strip()]

        delen: list[str] = []
        for paragraaf in paragrafen:
            if tel_tokens(paragraaf) > self.max_tokens:
                # Paragraaf te groot: split op zinsgrenzen
                delen.extend(forceer_split_op_zinnen(paragraaf, self.max_tokens))
            else:
                delen.append(paragraaf)

        # Merge kleine delen terug samen (onder min_tokens)
        delen = self._merge_kleine_delen(delen)

        chunks: list[DocumentChunk] = []
        vorige = vorige_tekst
        for i, deel in enumerate(delen):
            overlap = bereken_overlap(vorige, self.overlap_ratio)
            metadata = ChunkMetadata(
                bronbestand=bronbestand,
                chunk_index=start_index + i,
                sectie=heading,
                rechtsgebied=rechtsgebied,
                structuur_type="generiek",
            )
            chunks.append(
                DocumentChunk(
                    tekst=deel,
                    metadata=metadata,
                    token_count=tel_tokens(deel),
                    overlap_tekst=overlap,
                )
            )
            vorige = deel

        return chunks

    def _merge_kleine_delen(self, delen: list[str]) -> list[str]:
        """Merge delen die onder min_tokens zitten."""
        if len(delen) <= 1:
            return delen

        merged: list[str] = []
        for deel in delen:
            tokens = tel_tokens(deel)
            if (
                merged
                and tokens < self.min_tokens
                and tel_tokens(merged[-1]) + tokens <= self.max_tokens
            ):
                merged[-1] = merged[-1] + "\n\n" + deel
            else:
                merged.append(deel)

        return merged

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
            if (
                merged
                and tokens < self.min_tokens
                and tel_tokens(merged[-1]) + tokens <= self.max_tokens
            ):
                merged[-1] = merged[-1] + "\n\n" + sectie
            else:
                merged.append(sectie)

        # Check of de laatste nog te klein is
        if (
            len(merged) > 1
            and tel_tokens(merged[-1]) < self.min_tokens
            and tel_tokens(merged[-2]) + tel_tokens(merged[-1]) <= self.max_tokens
        ):
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
