"""
DocumentChunker — orchestrator voor juridisch-aware document chunking.

Entry points:
- chunk_tekst(): voor al geëxtraheerde tekst
- chunk_bestand(): voor raw bytes (delegeert extractie naar DocumentExtractor)
"""

from __future__ import annotations

import logging

from document_processing.document_extractor import extract_text_from_file
from services.rag.chunking_strategies import (
    GeneriekChunkingStrategy,
    JuridischeChunkingStrategy,
)
from services.rag.legal_structure_recognizer import LegalStructureRecognizer
from services.rag.models import ChunkingResult

logger = logging.getLogger(__name__)


class DocumentChunker:
    """Orchestreert juridisch-aware document chunking."""

    def __init__(
        self,
        max_tokens: int = 1000,
        min_tokens: int = 50,
    ):
        self._recognizer = LegalStructureRecognizer()
        self._juridisch_strategy = JuridischeChunkingStrategy(
            max_tokens=max_tokens,
            min_tokens=min_tokens,
        )
        self._generiek_strategy = GeneriekChunkingStrategy(
            max_tokens=max_tokens,
            min_tokens=min_tokens,
        )

    def chunk_tekst(
        self,
        tekst: str,
        bronbestand: str,
        bestandstype: str = "text/plain",
        rechtsgebied: str | None = None,
    ) -> ChunkingResult:
        """
        Chunk al geëxtraheerde tekst.

        Args:
            tekst: De tekst om te chunken.
            bronbestand: Oorspronkelijke bestandsnaam.
            bestandstype: MIME type van het bronbestand.
            rechtsgebied: Optioneel rechtsgebied voor metadata.

        Returns:
            ChunkingResult met chunks en metadata.
        """
        if not tekst or not tekst.strip():
            return ChunkingResult(
                bronbestand=bronbestand,
                bestandstype=bestandstype,
                fout_melding="Lege of geen tekst ontvangen",
            )

        try:
            is_juridisch = self._recognizer.is_juridisch_document(tekst)

            if is_juridisch:
                strategy = self._juridisch_strategy
                logger.info(
                    "Juridisch document gedetecteerd: %s — gebruik juridische chunking",
                    bronbestand,
                )
            else:
                strategy = self._generiek_strategy
                logger.info(
                    "Generiek document: %s — gebruik generieke chunking",
                    bronbestand,
                )

            chunks = strategy.chunk(tekst, bronbestand, bestandstype, rechtsgebied)
            totaal_tokens = sum(c.token_count for c in chunks)

            return ChunkingResult(
                chunks=tuple(chunks),
                bronbestand=bronbestand,
                bestandstype=bestandstype,
                totaal_tokens=totaal_tokens,
                juridisch_document=is_juridisch,
            )

        except Exception as e:
            logger.error("Fout bij chunking van %s: %s", bronbestand, e)
            return ChunkingResult(
                bronbestand=bronbestand,
                bestandstype=bestandstype,
                fout_melding=f"Chunking fout: {e}",
            )

    def chunk_bestand(
        self,
        file_content: bytes,
        filename: str,
        mime_type: str | None = None,
        rechtsgebied: str | None = None,
    ) -> ChunkingResult:
        """
        Chunk een bestand: extractie + chunking in één stap.

        Args:
            file_content: Binaire inhoud van het bestand.
            filename: Originele bestandsnaam.
            mime_type: MIME type (optioneel, wordt afgeleid).
            rechtsgebied: Optioneel rechtsgebied voor metadata.

        Returns:
            ChunkingResult met chunks en metadata.
        """
        bestandstype = mime_type or "application/octet-stream"

        if not file_content:
            return ChunkingResult(
                bronbestand=filename,
                bestandstype=bestandstype,
                fout_melding="Leeg bestand ontvangen",
            )

        try:
            tekst = extract_text_from_file(file_content, filename, mime_type)
        except Exception as e:
            logger.error("Tekst extractie mislukt voor %s: %s", filename, e)
            return ChunkingResult(
                bronbestand=filename,
                bestandstype=bestandstype,
                fout_melding=f"Extractie fout: {e}",
            )

        if not tekst:
            return ChunkingResult(
                bronbestand=filename,
                bestandstype=bestandstype,
                fout_melding=f"Geen tekst geëxtraheerd uit {filename}",
            )

        return self.chunk_tekst(tekst, filename, bestandstype, rechtsgebied)
