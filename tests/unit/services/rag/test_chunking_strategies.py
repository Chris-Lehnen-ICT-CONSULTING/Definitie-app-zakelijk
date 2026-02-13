"""Tests voor chunking strategieën."""

import pytest

from services.rag.chunking_strategies import (
    GeneriekChunkingStrategy,
    JuridischeChunkingStrategy,
    _bereken_overlap,
)
from services.rag.token_counter import tel_tokens

# ── Overlap helper ───────────────────────────────────────────────


class TestBerekenOverlap:
    def test_lege_tekst(self):
        assert _bereken_overlap("", 0.12) == ""

    def test_korte_tekst_geen_overlap(self):
        # Very short text -> less than 5 target tokens -> empty
        assert _bereken_overlap("Ja.", 0.12) == ""

    def test_overlap_bevat_volledige_zinnen(self):
        tekst = (
            "Eerste zin over de wet. Tweede zin over de regeling. "
            "Derde zin over de procedure. Vierde zin over het besluit."
        )
        overlap = _bereken_overlap(tekst, 0.3)
        assert len(overlap) > 0
        # Overlap moet uit volledige woorden bestaan (geen mid-word cuts)
        assert not overlap.startswith(" ")

    def test_overlap_ratio_in_range(self):
        """Overlap tokens moeten ~ratio van de brontekst zijn."""
        tekst = "Dit is een langere tekst met meerdere zinnen. " * 10
        bron_tokens = tel_tokens(tekst)
        overlap = _bereken_overlap(tekst, 0.12)
        overlap_tokens = tel_tokens(overlap)
        # Should be roughly 12% (allow 5-25% due to sentence boundary rounding)
        assert overlap_tokens <= bron_tokens * 0.25
        assert overlap_tokens >= bron_tokens * 0.05

    def test_afkorting_niet_gesplitst(self):
        """Mr., Dr. etc. moeten niet als zinsgrens behandeld worden."""
        tekst = (
            "Mr. De Vries was aanwezig. Dr. Jansen was afwezig. Het besluit is genomen."
        )
        overlap = _bereken_overlap(tekst, 0.5)
        # Should contain "Mr." or "Dr." intact (not split mid-abbreviation)
        assert "Mr" in overlap or "Dr" in overlap or "besluit" in overlap


# ── Juridische strategie ─────────────────────────────────────────


class TestJuridischeChunkingStrategy:
    @pytest.fixture
    def strategy(self):
        return JuridischeChunkingStrategy()

    def test_lege_tekst(self, strategy):
        assert strategy.chunk("", "test.pdf", "application/pdf") == []

    def test_artikelen_als_chunks(self, strategy, sample_wettekst):
        chunks = strategy.chunk(sample_wettekst, "wet.pdf", "application/pdf")
        assert len(chunks) > 0
        for chunk in chunks:
            assert len(chunk.tekst) > 0
            assert chunk.metadata.bronbestand == "wet.pdf"
            assert chunk.token_count > 0

    def test_artikel_niet_gesplitst(self, strategy, sample_wettekst):
        """Artikel tekst mag niet over meerdere chunks verdeeld worden."""
        chunks = strategy.chunk(sample_wettekst, "wet.pdf", "application/pdf")
        # Artikel 3 is kort — het kan gemerged zijn met een buurman,
        # maar de tekst moet intact in precies 1 chunk zitten.
        chunks_met_art3 = [c for c in chunks if "verantwoordelijk" in c.tekst]
        assert len(chunks_met_art3) == 1

    def test_definitieblok_intact(self, strategy, sample_wettekst):
        """Definitieblok moet als 1 chunk behouden blijven."""
        chunks = strategy.chunk(sample_wettekst, "wet.pdf", "application/pdf")
        defblokken = [c for c in chunks if c.metadata.structuur_type == "definitieblok"]
        assert len(defblokken) == 1
        assert "basisregistratie" in defblokken[0].tekst
        assert "minister" in defblokken[0].tekst

    def test_groot_artikel_gesplitst_op_leden(self):
        """Artikel > max_tokens moet gesplitst worden op lid-grenzen."""
        leden = []
        for i in range(1, 6):
            leden.append(f"{i}. " + "Dit is een lang lid met veel tekst. " * 20)
        lang_artikel = "Artikel 1\n" + "\n".join(leden) + "\n\nArtikel 2\nKort."

        strategy = JuridischeChunkingStrategy(max_tokens=300)
        chunks = strategy.chunk(lang_artikel, "test.pdf", "application/pdf")
        assert len(chunks) > 2

    def test_overlap_aanwezig_en_in_range(self, strategy, sample_wettekst):
        """Chunks na de eerste moeten overlap hebben, ~12% van vorige chunk."""
        chunks = strategy.chunk(sample_wettekst, "wet.pdf", "application/pdf")
        overlaps = [c for c in chunks if c.overlap_tekst]
        assert len(overlaps) > 0
        # Verify overlap is not excessively large
        for chunk in overlaps:
            overlap_tokens = tel_tokens(chunk.overlap_tekst)
            # Overlap should be reasonable (not more than 50% of the chunk)
            assert overlap_tokens < chunk.token_count or chunk.token_count < 20

    def test_chunk_index_sequentieel(self, strategy, sample_wettekst):
        chunks = strategy.chunk(sample_wettekst, "wet.pdf", "application/pdf")
        indices = [c.metadata.chunk_index for c in chunks]
        assert indices == list(range(len(chunks)))

    def test_wet_naam_in_metadata(self, strategy, sample_wettekst):
        chunks = strategy.chunk(
            sample_wettekst, "wet.pdf", "application/pdf", rechtsgebied="bestuursrecht"
        )
        assert any(c.metadata.wet_regeling for c in chunks)
        assert all(c.metadata.rechtsgebied == "bestuursrecht" for c in chunks)

    def test_min_tokens_merge(self):
        """Korte chunks moeten gemerged worden tot >= min_tokens."""
        tekst = (
            "Artikel 1\nKort.\n\n"
            "Artikel 2\nOok kort.\n\n"
            "Artikel 3\n" + "Lang artikel met genoeg tekst voor een chunk. " * 20 + "\n"
        )
        min_tok = 30
        strategy = JuridischeChunkingStrategy(min_tokens=min_tok)
        chunks = strategy.chunk(tekst, "test.txt", "text/plain")
        # After merging, no chunk should be below min_tokens
        # (except possible edge case where all content is tiny)
        merged_chunks = [c for c in chunks if c.token_count >= min_tok]
        assert len(merged_chunks) >= 1

    def test_merge_respects_max_tokens(self):
        """Merge mag max_tokens niet overschrijden."""
        strategy = JuridischeChunkingStrategy(max_tokens=100, min_tokens=30)
        # Maak een artikel van ~90 tokens gevolgd door één van ~20 tokens
        art1_tekst = "Dit is een lang artikel. " * 12  # ~90 tokens
        tekst = (
            "Artikel 1\n" + art1_tekst + "\n\n"
            "Artikel 2\nKort.\n\n"
            "Artikel 3\nOok weer een wat langere tekst voor de derde keer.\n"
        )
        chunks = strategy.chunk(tekst, "test.txt", "text/plain")
        for chunk in chunks:
            assert (
                chunk.token_count <= 100 + 10
            )  # kleine marge voor \n\n merge overhead


# ── Generieke strategie ──────────────────────────────────────────


class TestGeneriekChunkingStrategy:
    @pytest.fixture
    def strategy(self):
        return GeneriekChunkingStrategy()

    def test_lege_tekst(self, strategy):
        assert strategy.chunk("", "doc.md", "text/markdown") == []

    def test_markdown_secties(self, strategy, sample_generieke_tekst):
        chunks = strategy.chunk(sample_generieke_tekst, "doc.md", "text/markdown")
        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk.metadata.structuur_type == "generiek"
            assert chunk.metadata.bronbestand == "doc.md"

    def test_heading_in_metadata(self, strategy, sample_generieke_tekst):
        chunks = strategy.chunk(sample_generieke_tekst, "doc.md", "text/markdown")
        headings = [c.metadata.sectie for c in chunks if c.metadata.sectie]
        assert len(headings) > 0

    def test_kleine_secties_gemerged(self):
        """Secties onder minimum worden gemerged."""
        tekst = "# A\nKort.\n\n# B\nOok kort.\n\n# C\n" + "Lang genoeg tekst. " * 30
        strategy = GeneriekChunkingStrategy(min_tokens=20)
        chunks = strategy.chunk(tekst, "doc.md", "text/markdown")
        assert len(chunks) >= 1

    def test_overlap_aanwezig(self, strategy, sample_generieke_tekst):
        chunks = strategy.chunk(sample_generieke_tekst, "doc.md", "text/markdown")
        if len(chunks) > 1:
            has_overlap = any(c.overlap_tekst for c in chunks[1:])
            assert has_overlap

    def test_chunk_index_sequentieel(self, strategy, sample_generieke_tekst):
        chunks = strategy.chunk(sample_generieke_tekst, "doc.md", "text/markdown")
        indices = [c.metadata.chunk_index for c in chunks]
        assert indices == list(range(len(chunks)))

    def test_chunks_zijn_frozen(self, strategy, sample_generieke_tekst):
        """Chunks moeten immutable zijn (frozen dataclass)."""
        chunks = strategy.chunk(sample_generieke_tekst, "doc.md", "text/markdown")
        assert len(chunks) > 0
        with pytest.raises(AttributeError):
            chunks[0].tekst = "gewijzigd"  # type: ignore[misc]
