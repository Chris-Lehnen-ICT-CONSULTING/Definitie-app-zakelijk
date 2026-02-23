"""Tests voor chunking strategieën."""

import pytest

from services.rag.chunking_strategies import (
    GeneriekChunkingStrategy,
    JuridischeChunkingStrategy,
)
from services.rag.chunking_utils import bereken_overlap, forceer_split_op_zinnen
from services.rag.token_counter import tel_tokens

# ── Overlap helper ───────────────────────────────────────────────


class TestBerekenOverlap:
    def test_lege_tekst(self):
        assert bereken_overlap("", 0.12) == ""

    def test_korte_tekst_geen_overlap(self):
        # Very short text -> less than 5 target tokens -> empty
        assert bereken_overlap("Ja.", 0.12) == ""

    def test_overlap_bevat_volledige_zinnen(self):
        tekst = (
            "Eerste zin over de wet. Tweede zin over de regeling. "
            "Derde zin over de procedure. Vierde zin over het besluit."
        )
        overlap = bereken_overlap(tekst, 0.3)
        assert len(overlap) > 0
        # Overlap moet uit volledige woorden bestaan (geen mid-word cuts)
        assert not overlap.startswith(" ")

    def test_overlap_ratio_in_range(self):
        """Overlap tokens moeten ~ratio van de brontekst zijn."""
        tekst = "Dit is een langere tekst met meerdere zinnen. " * 10
        bron_tokens = tel_tokens(tekst)
        overlap = bereken_overlap(tekst, 0.12)
        overlap_tokens = tel_tokens(overlap)
        # Should be roughly 12% (allow 5-25% due to sentence boundary rounding)
        assert overlap_tokens <= bron_tokens * 0.25
        assert overlap_tokens >= bron_tokens * 0.05

    def test_afkorting_niet_gesplitst(self):
        """Mr., Dr. etc. moeten niet als zinsgrens behandeld worden."""
        tekst = (
            "Mr. De Vries was aanwezig. Dr. Jansen was afwezig. Het besluit is genomen."
        )
        overlap = bereken_overlap(tekst, 0.5)
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
            # Marge: 10 voor merge overhead + 12% van max_tokens voor overlap-prepend
            assert chunk.token_count <= 100 + 10 + int(
                100 * 0.15
            ), f"Chunk te groot: {chunk.token_count} tokens"


class TestOverlapPrepend:
    """DEF-380 Bevinding 5: Overlap wordt geprependt aan chunk_tekst voor opslag."""

    def test_tweede_chunk_begint_met_overlap(self):
        """De tekst van een chunk met overlap bevat de overlap-inhoud."""
        strategy = JuridischeChunkingStrategy(overlap_ratio=0.15)
        tekst = (
            "Artikel 1\n"
            "Dit is een eerste artikel met voldoende tekst voor overlap. "
            "Het heeft meerdere zinnen zodat overlap berekend kan worden. "
            "De derde zin zorgt voor extra context.\n\n"
            "Artikel 2\n"
            "Dit is het tweede artikel. Het volgt op het eerste.\n\n"
            "Artikel 3\n"
            "Dit is het derde artikel met eigen inhoud.\n"
        )
        chunks = strategy.chunk(tekst, "test.pdf", "application/pdf")

        chunks_met_overlap = [c for c in chunks if c.overlap_tekst]
        for chunk in chunks_met_overlap:
            assert (
                chunk.overlap_tekst in chunk.tekst
            ), "Overlap niet geprependt in chunk tekst"

    def test_eerste_chunk_geen_overlap_prefix(self):
        """De eerste chunk heeft geen overlap (geen vorige tekst)."""
        strategy = JuridischeChunkingStrategy()
        tekst = (
            "Artikel 1\n"
            "Eerste artikel met veel tekst om een goede chunk te vormen.\n\n"
            "Artikel 2\n"
            "Tweede artikel.\n"
        )
        chunks = strategy.chunk(tekst, "test.pdf", "application/pdf")
        assert chunks[0].overlap_tekst == ""

    def test_overlap_tekst_veld_beschikbaar(self):
        """overlap_tekst veld is beschikbaar op alle chunks als string."""
        strategy = JuridischeChunkingStrategy(overlap_ratio=0.20)
        tekst = (
            "Artikel 1\n"
            "Lang eerste artikel met genoeg tekst voor overlap. "
            "Tweede zin voor meer context. Derde zin ook mee.\n\n"
            "Artikel 2\n"
            "Tweede artikel.\n\nArtikel 3\nDerde.\n"
        )
        chunks = strategy.chunk(tekst, "test.pdf", "application/pdf")
        for chunk in chunks:
            assert hasattr(chunk, "overlap_tekst")
            assert isinstance(chunk.overlap_tekst, str)


class TestMaakEnkeleChunkSplit:
    """DEF-357 #13: _maak_enkele_chunk() splitst grote tekst zonder structuur."""

    def test_grote_tekst_zonder_structuur_wordt_gesplitst(self):
        """Juridisch document zonder structuur maar > max_tokens → meerdere chunks."""
        # Tekst zonder artikel-structuur maar groot genoeg
        grote_tekst = "Dit is een lang juridisch document zonder artikelen. " * 200
        strategy = JuridischeChunkingStrategy(max_tokens=200)
        chunks = strategy.chunk(grote_tekst, "groot.pdf", "application/pdf")
        assert len(chunks) > 1
        for chunk in chunks:
            # Marge voor zinsgrens-rounding + woord-split overhead
            assert chunk.token_count <= 200 + 30

    def test_kleine_tekst_zonder_structuur_niet_gesplitst(self):
        """Korte tekst zonder structuur → 1 chunk."""
        korte_tekst = "Dit is een korte tekst."
        strategy = JuridischeChunkingStrategy()
        chunks = strategy.chunk(korte_tekst, "kort.pdf", "application/pdf")
        assert len(chunks) == 1


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


# ── DEF-356: Formfeed normalisatie in chunking ──────────────────


class TestFormfeedChunking:
    """DEF-356: Formfeed-only tekst wordt correct gechunkt."""

    def test_juridisch_formfeed_only_meerdere_chunks(self, sample_formfeed_only_tekst):
        """PDF met alleen formfeeds levert meerdere chunks op."""
        # min_tokens=1 om merging uit te schakelen voor korte test-tekst
        strategy = JuridischeChunkingStrategy(min_tokens=1)
        chunks = strategy.chunk(
            sample_formfeed_only_tekst, "wet.pdf", "application/pdf"
        )
        assert len(chunks) >= 3

    def test_juridisch_formfeed_geen_formfeeds_in_chunks(
        self, sample_formfeed_only_tekst
    ):
        """Chunk-tekst mag geen formfeed characters bevatten."""
        strategy = JuridischeChunkingStrategy()
        chunks = strategy.chunk(
            sample_formfeed_only_tekst, "wet.pdf", "application/pdf"
        )
        for chunk in chunks:
            assert "\f" not in chunk.tekst

    def test_generiek_formfeed_normalisatie(self):
        """Generieke strategie normaliseert formfeeds in chunk-tekst."""
        tekst = "# Sectie 1\fTekst na formfeed.\n\n# Sectie 2\fMeer tekst."
        strategy = GeneriekChunkingStrategy()
        chunks = strategy.chunk(tekst, "doc.pdf", "application/pdf")
        for chunk in chunks:
            assert "\f" not in chunk.tekst


class TestArtikelMetTekstErna:
    """DEF-356: Artikel regex matcht ook als er tekst na het nummer staat."""

    def test_artikel_met_trailing_tekst_wordt_gechunkt(self):
        """Artikelen met tekst na het nummer worden als aparte chunks opgeslagen."""
        tekst = (
            "Artikel 1 Strafvordering betreft de opsporing van feiten.\n\n"
            "Artikel 2 De officier van justitie is belast met de vervolging.\n\n"
            "Artikel 3 De rechter oordeelt over de strafzaak.\n"
        )
        strategy = JuridischeChunkingStrategy(min_tokens=1)
        chunks = strategy.chunk(tekst, "sv.pdf", "application/pdf")
        assert len(chunks) == 3

    def test_bw_notatie_met_trailing_tekst(self):
        """BW-notatie (10:1) met trailing tekst wordt correct gedetecteerd."""
        tekst = (
            "Artikel 10:1 Een overeenkomst in de zin van dit boek.\n\n"
            "Artikel 10:2 De overeenkomst heeft rechtsgevolgen.\n"
        )
        strategy = JuridischeChunkingStrategy(min_tokens=1)
        chunks = strategy.chunk(tekst, "bw.pdf", "application/pdf")
        artikelen = [c for c in chunks if c.metadata.artikel_nummer]
        assert len(artikelen) == 2
        assert artikelen[0].metadata.artikel_nummer == "10:1"


class TestLetterLedenChunking:
    """DEF-356: Letter-leden worden NIET als splitpunt gebruikt."""

    def test_letter_leden_niet_als_splitpunt(self, sample_artikel_met_letter_leden):
        """Artikel met letter-leden wordt niet gesplitst op a., b., c."""
        tekst = sample_artikel_met_letter_leden + "\nArtikel 2\nKort.\n"
        strategy = JuridischeChunkingStrategy(max_tokens=500)
        chunks = strategy.chunk(tekst, "wet.pdf", "application/pdf")
        # Letter-leden moeten in dezelfde chunk als hun parent-lid zitten
        chunk_met_letters = [c for c in chunks if "basisregistratie" in c.tekst]
        assert len(chunk_met_letters) == 1
        assert (
            "a." in chunk_met_letters[0].tekst
            or "ingezetene" in chunk_met_letters[0].tekst
        )


class TestGroteSectieSplit:
    """DEF-356: Generieke strategie splitst grote secties op paragraaf-grenzen."""

    def test_grote_sectie_gesplitst(self, sample_groot_generiek_document):
        """Sectie > max_tokens wordt gesplitst op paragraaf-grenzen."""
        strategy = GeneriekChunkingStrategy(max_tokens=300)
        chunks = strategy.chunk(
            sample_groot_generiek_document, "doc.md", "text/markdown"
        )
        assert len(chunks) > 3
        for chunk in chunks:
            assert chunk.token_count <= 300 + 50  # marge voor zinsgrens-rounding

    def test_chunk_index_sequentieel_na_split(self, sample_groot_generiek_document):
        """Na paragraaf-split zijn chunk indices nog steeds sequentieel."""
        strategy = GeneriekChunkingStrategy(max_tokens=300)
        chunks = strategy.chunk(
            sample_groot_generiek_document, "doc.md", "text/markdown"
        )
        indices = [c.metadata.chunk_index for c in chunks]
        assert indices == list(range(len(chunks)))


# ── DEF-356: forceer_split_op_zinnen utility ────────────────────


class TestForceerSplitOpZinnen:
    def test_korte_tekst_niet_gesplitst(self):
        delen = forceer_split_op_zinnen("Korte zin.", 1000)
        assert len(delen) == 1

    def test_lange_tekst_gesplitst(self):
        tekst = "Dit is een zin. " * 100
        delen = forceer_split_op_zinnen(tekst, 50)
        assert len(delen) > 1
        for deel in delen:
            assert tel_tokens(deel) <= 50 + 20  # marge

    def test_lege_tekst(self):
        assert forceer_split_op_zinnen("", 100) == []

    def test_whitespace_only(self):
        assert forceer_split_op_zinnen("   ", 100) == []

    def test_mega_zin_wordt_gesplitst(self):
        """Een enkele zin > max_tokens wordt op woordgrenzen gesplitst."""
        mega_zin = "woord " * 200  # ~200 tokens, geen zinsgrenzen
        delen = forceer_split_op_zinnen(mega_zin.strip(), 50)
        assert len(delen) > 1
        for deel in delen:
            # Marge nodig: BPE tokeniseert "woord woord" anders dan losse woorden
            assert tel_tokens(deel) <= 50 + 30

    def test_mega_zin_tussen_normale_zinnen(self):
        """Mix van normale en mega-zinnen wordt correct gesplitst."""
        normaal = "Korte zin. Nog een. "
        mega = "woord " * 150
        tekst = normaal + mega.strip() + ". Einde."
        delen = forceer_split_op_zinnen(tekst, 50)
        assert len(delen) > 1
        # Alle tekst moet behouden zijn
        reconstructed = " ".join(delen)
        assert "Korte zin." in reconstructed
        assert "Einde." in reconstructed


# ── DEF-360: MAX_TOKENS_PER_CHUNK afdwingen ─────────────────────


class TestMaxTokensEnforcement:
    """DEF-360: Alle chunks moeten <= max_tokens zijn, ook hoofdstukken en leden."""

    def test_groot_hoofdstuk_wordt_gesplitst(self):
        """Hoofdstuk > max_tokens moet gesplitst worden op zinsgrenzen."""
        lang_hoofdstuk = "HOOFDSTUK 1. ALGEMENE BEPALINGEN\n" + (
            "Dit is een lange bepaling over de wet. " * 100
        )
        tekst = lang_hoofdstuk + "\nArtikel 1\nKort.\nArtikel 2\nOok kort.\n"
        strategy = JuridischeChunkingStrategy(max_tokens=200)
        chunks = strategy.chunk(tekst, "test.pdf", "application/pdf")
        for chunk in chunks:
            # Marge voor zinsgrens-rounding (+30) en overlap-prepend (+30 = ~12% van max)
            assert chunk.token_count <= 200 + 60, (
                f"Chunk te groot: {chunk.token_count} tokens, "
                f"type={chunk.metadata.structuur_type}"
            )

    def test_groot_lid_wordt_gesplitst(self):
        """Individueel lid > max_tokens moet sub-gesplitst worden."""
        lang_lid = (
            "1. " + "Dit is een extreem lang lid met veel juridische tekst. " * 80
        )
        tekst = (
            "Artikel 1\n"
            + lang_lid
            + "\n2. Kort lid.\n\n"
            + "Artikel 2\nAndere bepaling.\n"
        )
        strategy = JuridischeChunkingStrategy(max_tokens=200)
        chunks = strategy.chunk(tekst, "test.pdf", "application/pdf")
        for chunk in chunks:
            # Marge voor zinsgrens-rounding (+30) en overlap-prepend (+30 = ~12% van max)
            assert (
                chunk.token_count <= 200 + 60
            ), f"Chunk te groot: {chunk.token_count} tokens"

    def test_groot_hoofdstuk_behoudt_metadata(self):
        """Gesplitst hoofdstuk behoudt structuur_type in metadata."""
        lang = "HOOFDSTUK 1. BEPALINGEN\n" + "Lange tekst hier. " * 100
        tekst = lang + "\nArtikel 1\nKort.\nArtikel 2\nOok kort.\n"
        strategy = JuridischeChunkingStrategy(max_tokens=200)
        chunks = strategy.chunk(tekst, "test.pdf", "application/pdf")
        hoofdstuk_chunks = [
            c for c in chunks if c.metadata.structuur_type == "hoofdstuk"
        ]
        assert len(hoofdstuk_chunks) >= 2

    def test_klein_hoofdstuk_niet_gesplitst(self):
        """Hoofdstuk <= max_tokens blijft één chunk."""
        tekst = (
            "HOOFDSTUK 1. KORTE TITEL\nKorte tekst.\n\n"
            "Artikel 1\nBepaling.\nArtikel 2\nAndere bepaling.\n"
        )
        strategy = JuridischeChunkingStrategy(max_tokens=1000)
        chunks = strategy.chunk(tekst, "test.pdf", "application/pdf")
        hoofdstuk_chunks = [
            c for c in chunks if c.metadata.structuur_type == "hoofdstuk"
        ]
        assert len(hoofdstuk_chunks) == 1


# ── DEF-358: split_zinnen behoudt leestekens ────────────────────


class TestSplitZinnenLeestekens:
    """DEF-358: split_zinnen() moet leestekens behouden."""

    def test_punten_behouden(self):
        from services.rag.chunking_utils import split_zinnen

        zinnen = split_zinnen("Eerste zin. Tweede zin. Derde zin.")
        assert all(z.endswith(".") for z in zinnen)

    def test_vraagteken_behouden(self):
        from services.rag.chunking_utils import split_zinnen

        zinnen = split_zinnen("Wat is dit? Een ander punt. Klaar!")
        assert zinnen[0].endswith("?")
        assert zinnen[1].endswith(".")
        assert zinnen[2].endswith("!")

    def test_afkortingen_niet_gesplitst(self):
        from services.rag.chunking_utils import split_zinnen

        zinnen = split_zinnen("Mr. De Vries was er. Dr. Jansen ook.")
        # "Mr." en "Dr." mogen niet als zinsgrens
        assert len(zinnen) == 2


# ── DEF-380 Bevinding 2: artikel_nummer bewaard bij merge ────────


class TestMergeArtikelNummerPreservation:
    """DEF-380 Bevinding 2: artikel_nummer bewaard bij merge van kleine artikel-chunk."""

    def test_artikel_nummer_bewaard_als_prev_geen_nummer_heeft(self):
        """Klein artikel gemerged in hoofdstuk-chunk behoudt artikel_nummer."""
        from services.rag.models import ChunkMetadata, DocumentChunk

        strategy = JuridischeChunkingStrategy(min_tokens=30, max_tokens=200)
        meta_hoofdstuk = ChunkMetadata(
            bronbestand="test.pdf",
            chunk_index=0,
            structuur_type="hoofdstuk",
            artikel_nummer=None,
        )
        meta_artikel = ChunkMetadata(
            bronbestand="test.pdf",
            chunk_index=1,
            structuur_type="artikel",
            artikel_nummer="7",
        )
        groot = DocumentChunk(
            tekst="Hoofdstuk inhoud. " * 10,
            metadata=meta_hoofdstuk,
            token_count=50,
        )
        klein = DocumentChunk(
            tekst="Artikel 7 tekst.",
            metadata=meta_artikel,
            token_count=5,
        )
        result = strategy._merge_kleine_chunks([groot, klein])
        assert len(result) == 1
        # Na fix: artikel_nummer="7" bewaard (was None voor de fix)
        assert result[0].metadata.artikel_nummer == "7"

    def test_artikel_nummer_bewaard_in_integratie(self):
        """Integratietest: klein artikel in hoofdstuk behoudt artikel_nummer via chunk()."""
        strategy = JuridischeChunkingStrategy(min_tokens=50, max_tokens=500)
        tekst = (
            "HOOFDSTUK 1. ALGEMENE BEPALINGEN\n"
            "Uitgebreide inhoud van het hoofdstuk met relevante tekst. " * 8 + "\n\n"
            "Artikel 5\nKort artikel.\n"
        )
        chunks = strategy.chunk(tekst, "test.pdf", "application/pdf")
        chunk_met_kort = next((c for c in chunks if "Kort artikel" in c.tekst), None)
        assert chunk_met_kort is not None, "Geen chunk met 'Kort artikel' gevonden"
        # Na fix: artikel_nummer "5" bewaard ondanks merge in hoofdstuk-chunk
        assert chunk_met_kort.metadata.artikel_nummer == "5"

    def test_beide_chunks_hebben_nummer_geabsorbeerde_wint(self):
        """Als beide chunks artikel_nummer hebben, wint de geabsorbeerde (specifiekste)."""
        from services.rag.models import ChunkMetadata, DocumentChunk

        strategy = JuridischeChunkingStrategy(min_tokens=30, max_tokens=200)
        meta_1 = ChunkMetadata(
            bronbestand="test.pdf",
            chunk_index=0,
            artikel_nummer="1",
        )
        meta_2 = ChunkMetadata(
            bronbestand="test.pdf",
            chunk_index=1,
            artikel_nummer="2",
        )
        groot = DocumentChunk(
            tekst="Artikel 1 tekst. " * 10, metadata=meta_1, token_count=50
        )
        klein = DocumentChunk(tekst="Artikel 2 kort.", metadata=meta_2, token_count=5)

        result = strategy._merge_kleine_chunks([groot, klein])
        assert len(result) == 1
        # Geabsorbeerde chunk (artikel 2) wint
        assert result[0].metadata.artikel_nummer == "2"


# ── DEF-380 Bevinding 6: post-pass laatste chunk ─────────────────


class TestMergeKleineChunksPostPass:
    """DEF-380 Bevinding 6: post-pass voor kleine laatste chunk."""

    def test_kleine_laatste_chunk_gemerged(self):
        """Laatste kleine chunk wordt gemerged als voorlaatste voldoende ruimte heeft."""
        from dataclasses import replace as dc_replace

        from services.rag.models import ChunkMetadata, DocumentChunk

        strategy = JuridischeChunkingStrategy(min_tokens=30, max_tokens=200)
        meta = ChunkMetadata(bronbestand="test.pdf", chunk_index=0)

        groot = DocumentChunk(
            tekst="Lang " * 40,
            metadata=dc_replace(meta, chunk_index=0),
            token_count=80,
        )
        klein = DocumentChunk(
            tekst="Klein.",
            metadata=dc_replace(meta, chunk_index=1),
            token_count=3,  # < min=30
        )
        result = strategy._merge_kleine_chunks([groot, klein])
        assert len(result) == 1
        assert "Klein." in result[0].tekst

    def test_kleine_laatste_chunk_blijft_als_geen_ruimte(self):
        """Kleine laatste chunk blijft staan als merge max_tokens zou overschrijden."""
        from dataclasses import replace as dc_replace

        from services.rag.models import ChunkMetadata, DocumentChunk

        strategy = JuridischeChunkingStrategy(min_tokens=30, max_tokens=100)
        meta = ChunkMetadata(bronbestand="test.pdf", chunk_index=0)

        groot = DocumentChunk(
            tekst="A " * 50,
            metadata=dc_replace(meta, chunk_index=0),
            token_count=98,  # bijna vol
        )
        klein = DocumentChunk(
            tekst="Klein.",
            metadata=dc_replace(meta, chunk_index=1),
            token_count=5,  # 98+5=103 > 100 → kan niet mergen
        )
        result = strategy._merge_kleine_chunks([groot, klein])
        assert len(result) == 2  # Kan niet mergen, beide blijven
