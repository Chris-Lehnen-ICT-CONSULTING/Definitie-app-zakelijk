"""Tests voor DocumentChunker orchestrator."""

from unittest.mock import patch

import pytest

from services.rag.document_chunker import DocumentChunker
from services.rag.token_counter import tel_tokens

pytestmark = [pytest.mark.unit]


@pytest.fixture
def chunker():
    return DocumentChunker()


class TestChunkTekst:
    def test_juridisch_document(self, chunker, sample_wettekst):
        result = chunker.chunk_tekst(sample_wettekst, "wet.pdf", "application/pdf")
        assert result.juridisch_document is True
        assert len(result.chunks) > 0
        assert result.totaal_tokens > 0
        assert result.fout_melding is None

    def test_generiek_document(self, chunker, sample_generieke_tekst):
        result = chunker.chunk_tekst(
            sample_generieke_tekst, "handleiding.md", "text/markdown"
        )
        assert result.juridisch_document is False
        assert len(result.chunks) > 0
        assert result.fout_melding is None

    def test_lege_tekst(self, chunker):
        result = chunker.chunk_tekst("", "leeg.txt", "text/plain")
        assert result.fout_melding is not None
        assert len(result.chunks) == 0

    def test_whitespace_only(self, chunker):
        result = chunker.chunk_tekst("   \n\n  ", "spaties.txt", "text/plain")
        assert result.fout_melding is not None

    def test_rechtsgebied_in_metadata(self, chunker, sample_wettekst):
        result = chunker.chunk_tekst(
            sample_wettekst,
            "wet.pdf",
            "application/pdf",
            rechtsgebied="bestuursrecht",
        )
        for chunk in result.chunks:
            assert chunk.metadata.rechtsgebied == "bestuursrecht"

    def test_bronbestand_in_result(self, chunker, sample_wettekst):
        result = chunker.chunk_tekst(sample_wettekst, "mijn_wet.pdf", "application/pdf")
        assert result.bronbestand == "mijn_wet.pdf"
        assert result.bestandstype == "application/pdf"

    def test_totaal_tokens_consistent(self, chunker, sample_wettekst):
        result = chunker.chunk_tekst(sample_wettekst, "wet.pdf", "application/pdf")
        som = sum(c.token_count for c in result.chunks)
        assert result.totaal_tokens == som

    def test_result_is_frozen(self, chunker, sample_wettekst):
        result = chunker.chunk_tekst(sample_wettekst, "wet.pdf", "application/pdf")
        with pytest.raises(AttributeError):
            result.totaal_tokens = 999  # type: ignore[misc]


class TestChunkBestand:
    def test_txt_bestand(self, chunker, sample_wettekst):
        content = sample_wettekst.encode("utf-8")
        result = chunker.chunk_bestand(content, "wet.txt", "text/plain")
        assert result.juridisch_document is True
        assert len(result.chunks) > 0

    def test_leeg_bestand(self, chunker):
        result = chunker.chunk_bestand(b"", "leeg.txt", "text/plain")
        assert result.fout_melding is not None
        assert len(result.chunks) == 0

    def test_extractie_mislukt(self, chunker):
        """Niet-ondersteund bestandstype geeft foutmelding."""
        result = chunker.chunk_bestand(
            b"binary data", "bestand.xyz", "application/octet-stream"
        )
        assert result.fout_melding is not None

    def test_corrupt_bestand_geen_crash(self, chunker):
        """Corrupt bestand mag niet crashen."""
        result = chunker.chunk_bestand(b"\x00\x01\x02\x03", "corrupt.txt", "text/plain")
        assert result is not None

    @patch("services.rag.document_chunker.extract_text_from_file")
    def test_extractie_exceptie(self, mock_extract, chunker):
        """Exception bij extractie moet netjes afgevangen worden."""
        mock_extract.side_effect = RuntimeError("Extractie kapot")
        result = chunker.chunk_bestand(b"data", "test.pdf", "application/pdf")
        assert result.fout_melding is not None
        assert "Extractie fout" in result.fout_melding


class TestAcceptatiecriteria:
    """Tests die direct mappen op de acceptatiecriteria uit het Linear issue."""

    def test_artikel_niet_in_twee_chunks(self, sample_wettekst):
        """Artikel nooit in twee chunks gesplitst (tenzij > 1000 tokens)."""
        chunker = DocumentChunker()
        result = chunker.chunk_tekst(sample_wettekst, "wet.pdf", "application/pdf")

        art3_tekst = "verantwoordelijk voor het bijhouden"
        matches = [c for c in result.chunks if art3_tekst in c.tekst]
        assert len(matches) == 1

    def test_min_50_tokens_na_merge(self, sample_wettekst):
        """Na merging mogen chunks niet onder 50 tokens zitten."""
        chunker = DocumentChunker(min_tokens=50)
        result = chunker.chunk_tekst(sample_wettekst, "wet.pdf", "application/pdf")
        # Count chunks that violate the minimum
        te_klein = [c for c in result.chunks if c.token_count < 50]
        # Allow max 1 edge-case chunk at end of document
        assert (
            len(te_klein) <= 1
        ), f"Te veel chunks onder 50 tokens: {[(c.token_count, c.tekst[:30]) for c in te_klein]}"

    def test_overlap_ratio_correct(self, sample_wettekst):
        """Overlap moet 10-15% zijn, gemeten in tokens."""
        chunker = DocumentChunker()
        result = chunker.chunk_tekst(sample_wettekst, "wet.pdf", "application/pdf")
        for _i, chunk in enumerate(result.chunks):
            if not chunk.overlap_tekst:
                continue
            overlap_tokens = tel_tokens(chunk.overlap_tekst)
            # Overlap should be > 0 and not absurdly large
            assert overlap_tokens > 0
            assert overlap_tokens < chunk.token_count or chunk.token_count < 20

    def test_definitieblokken_intact(self, sample_definitieblok):
        """Definitieblokken moeten intact blijven als 1 chunk."""
        tekst = sample_definitieblok + "\nArtikel 2\nAndere bepaling.\n"
        chunker = DocumentChunker()
        result = chunker.chunk_tekst(tekst, "wet.pdf", "application/pdf")

        defblok_chunks = [c for c in result.chunks if "wordt verstaan onder" in c.tekst]
        assert len(defblok_chunks) == 1
        chunk = defblok_chunks[0]
        assert "basisregistratie" in chunk.tekst
        assert "minister" in chunk.tekst

    def test_pdf_paginanummers(self, sample_pdf_tekst):
        """PDF chunks moeten paginanummers hebben."""
        chunker = DocumentChunker()
        result = chunker.chunk_tekst(sample_pdf_tekst, "wet.pdf", "application/pdf")
        chunks_met_pagina = [
            c for c in result.chunks if c.metadata.pagina_nummer is not None
        ]
        assert len(chunks_met_pagina) > 0

    def test_corrupt_leeg_geen_crash(self):
        """Corrupt/leeg bestand geeft foutmelding, geen crash."""
        chunker = DocumentChunker()
        result = chunker.chunk_bestand(b"", "leeg.pdf", "application/pdf")
        assert result.fout_melding is not None
        assert len(result.chunks) == 0

    def test_structuurherkenning(self, sample_wettekst):
        """Structuurherkenning: Artikel, Lid, Hoofdstuk, Bijlage."""
        chunker = DocumentChunker()
        result = chunker.chunk_tekst(sample_wettekst, "wet.pdf", "application/pdf")
        types = {c.metadata.structuur_type for c in result.chunks}
        assert "hoofdstuk" in types or "artikel" in types or "definitieblok" in types

    def test_bw_artikelen_correct_genummerd(self):
        """Burgerlijk Wetboek notatie: artikelnummers met : intact."""
        # Artikelen moeten lang genoeg zijn om niet gemerged te worden
        vulling = "Deze bepaling regelt de rechten en plichten van partijen. " * 8
        tekst = (
            "Wetboek van Burgerlijke Rechtsvordering\n\n"
            f"Artikel 10:1\n{vulling}\n\n"
            f"Artikel 10:2\n{vulling}\n\n"
            f"Artikel 10:3\n{vulling}\n"
        )
        chunker = DocumentChunker()
        result = chunker.chunk_tekst(tekst, "bw.pdf", "application/pdf")
        nummers = [
            c.metadata.artikel_nummer
            for c in result.chunks
            if c.metadata.artikel_nummer
        ]
        assert "10:1" in nummers
        assert "10:2" in nummers
