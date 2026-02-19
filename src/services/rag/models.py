"""
Data models voor de RAG chunking pipeline.

Definieert de structuren voor chunks, metadata en resultaten.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChunkMetadata:
    """Metadata per chunk — beschrijft locatie en juridische context."""

    bronbestand: str
    chunk_index: int
    pagina_nummer: int | None = None
    sectie: str | None = None
    rechtsgebied: str | None = None
    wet_regeling: str | None = None
    artikel_nummer: str | None = None
    lid_nummer: str | None = None
    structuur_type: str | None = None  # hoofdstuk|artikel|lid|bijlage|generiek
    truncated: bool = False  # Vangnet: True als embedding-tekst afgekapt moest worden


@dataclass(frozen=True)
class DocumentChunk:
    """Een enkel stuk tekst met metadata en overlap."""

    tekst: str
    metadata: ChunkMetadata
    token_count: int
    overlap_tekst: str = ""


@dataclass(frozen=True)
class ChunkingResult:
    """Resultaat van een volledige chunking operatie."""

    chunks: tuple[DocumentChunk, ...] = ()
    bronbestand: str = ""
    bestandstype: str = ""
    totaal_tokens: int = 0
    juridisch_document: bool = False
    fout_melding: str | None = None
