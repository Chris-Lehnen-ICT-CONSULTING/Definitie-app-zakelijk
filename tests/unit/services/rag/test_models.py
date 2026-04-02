"""Tests voor RAG data models."""

import pytest

from services.rag.models import ChunkingResult, ChunkMetadata, DocumentChunk

pytestmark = [pytest.mark.unit]


class TestChunkMetadata:
    def test_required_fields(self):
        meta = ChunkMetadata(bronbestand="test.pdf", chunk_index=0)
        assert meta.bronbestand == "test.pdf"
        assert meta.chunk_index == 0

    def test_optional_fields_default_none(self):
        meta = ChunkMetadata(bronbestand="test.pdf", chunk_index=0)
        assert meta.pagina_nummer is None
        assert meta.sectie is None
        assert meta.rechtsgebied is None
        assert meta.wet_regeling is None
        assert meta.artikel_nummer is None
        assert meta.lid_nummer is None
        assert meta.structuur_type is None

    def test_juridische_metadata(self):
        meta = ChunkMetadata(
            bronbestand="wet.pdf",
            chunk_index=3,
            pagina_nummer=5,
            wet_regeling="Wet op de gemeentelijke basisadministratie",
            artikel_nummer="2",
            lid_nummer="1",
            structuur_type="lid",
        )
        assert meta.pagina_nummer == 5
        assert meta.artikel_nummer == "2"
        assert meta.structuur_type == "lid"

    def test_frozen_immutable(self):
        meta = ChunkMetadata(bronbestand="test.pdf", chunk_index=0)
        with pytest.raises(AttributeError):
            meta.chunk_index = 5  # type: ignore[misc]


class TestDocumentChunk:
    def test_creation(self):
        meta = ChunkMetadata(bronbestand="test.txt", chunk_index=0)
        chunk = DocumentChunk(
            tekst="Dit is test tekst.",
            metadata=meta,
            token_count=5,
        )
        assert chunk.tekst == "Dit is test tekst."
        assert chunk.token_count == 5
        assert chunk.overlap_tekst == ""

    def test_with_overlap(self):
        meta = ChunkMetadata(bronbestand="test.txt", chunk_index=1)
        chunk = DocumentChunk(
            tekst="Vervolg tekst.",
            metadata=meta,
            token_count=3,
            overlap_tekst="Vorige zin als context.",
        )
        assert chunk.overlap_tekst == "Vorige zin als context."

    def test_frozen_immutable(self):
        meta = ChunkMetadata(bronbestand="test.txt", chunk_index=0)
        chunk = DocumentChunk(tekst="Test.", metadata=meta, token_count=1)
        with pytest.raises(AttributeError):
            chunk.tekst = "Gewijzigd"  # type: ignore[misc]


class TestChunkingResult:
    def test_empty_result(self):
        result = ChunkingResult()
        assert result.chunks == ()
        assert result.totaal_tokens == 0
        assert result.fout_melding is None

    def test_error_result(self):
        result = ChunkingResult(
            bronbestand="corrupt.pdf",
            bestandstype="application/pdf",
            fout_melding="Kan bestand niet lezen",
        )
        assert result.fout_melding == "Kan bestand niet lezen"
        assert result.chunks == ()

    def test_successful_result(self):
        meta = ChunkMetadata(bronbestand="wet.pdf", chunk_index=0)
        chunk = DocumentChunk(tekst="Artikel 1 tekst", metadata=meta, token_count=4)
        result = ChunkingResult(
            chunks=(chunk,),
            bronbestand="wet.pdf",
            bestandstype="application/pdf",
            totaal_tokens=4,
            juridisch_document=True,
        )
        assert len(result.chunks) == 1
        assert result.juridisch_document is True

    def test_frozen_immutable(self):
        result = ChunkingResult()
        with pytest.raises(AttributeError):
            result.totaal_tokens = 100  # type: ignore[misc]
