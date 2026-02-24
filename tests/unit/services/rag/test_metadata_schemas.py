"""Tests voor metadata Pydantic schema-validatie (DEF-374)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from services.rag.metadata_schemas import (
    METADATA_SCHEMAS,
    PDFMetadata,
    WebsiteMetadata,
    WetgevingMetadata,
    valideer_chunk_metadata,
)


class TestWetgevingMetadata:
    def test_alle_velden_optioneel(self):
        m = WetgevingMetadata()
        assert m.artikel_nummer is None
        assert m.sectie is None

    def test_valide_metadata(self):
        m = WetgevingMetadata(
            artikel_nummer="1",
            lid_nummer="2",
            structuur_type="lid",
            bronbestand="wvs.xml",
            pagina_nummer=42,
            sectie="Hoofdstuk 1",
        )
        assert m.artikel_nummer == "1"
        assert m.pagina_nummer == 42

    def test_verkeerd_type_pagina_nummer_geeft_fout(self):
        with pytest.raises(ValidationError):
            WetgevingMetadata(pagina_nummer="veertien")

    def test_sectie_veld_aanwezig(self):
        """sectie moet expliciet in WetgevingMetadata staan (DEF-374 AC)."""
        m = WetgevingMetadata(sectie="Afdeling 3")
        assert m.sectie == "Afdeling 3"


class TestWebsiteMetadata:
    def test_url_optioneel_totdat_chunker_het_levert(self):
        """url is optioneel: ChunkMetadata levert dit veld nog niet (DEF-374)."""
        m = WebsiteMetadata()
        assert m.url is None

    def test_valide_website_metadata_met_url(self):
        m = WebsiteMetadata(url="https://example.com", domein="example.com")
        assert m.url == "https://example.com"

    def test_optionele_velden_zijn_none(self):
        m = WebsiteMetadata(url="https://x.nl")
        assert m.domein is None
        assert m.sectie is None


class TestPDFMetadata:
    def test_alle_velden_optioneel(self):
        m = PDFMetadata()
        assert m.pagina_nummer is None

    def test_valide_pdf_metadata(self):
        m = PDFMetadata(pagina_nummer=3, auteur="J. Smit", bronbestand="wet.pdf")
        assert m.pagina_nummer == 3


class TestMetadataSchemasRegistry:
    def test_bekende_bron_types_aanwezig(self):
        assert "wetgeving" in METADATA_SCHEMAS
        assert "website" in METADATA_SCHEMAS
        assert "pdf" in METADATA_SCHEMAS

    def test_registry_wijst_naar_correcte_klassen(self):
        assert METADATA_SCHEMAS["wetgeving"] is WetgevingMetadata
        assert METADATA_SCHEMAS["website"] is WebsiteMetadata
        assert METADATA_SCHEMAS["pdf"] is PDFMetadata


class TestValideerChunkMetadata:
    def test_valide_wetgeving_metadata(self):
        result = valideer_chunk_metadata(
            "wetgeving",
            {"artikel_nummer": "1", "lid_nummer": "2", "bronbestand": "wvs.xml"},
        )
        assert result["artikel_nummer"] == "1"
        assert result["lid_nummer"] == "2"

    def test_invalide_type_geeft_validation_error(self):
        with pytest.raises(ValidationError):
            valideer_chunk_metadata("wetgeving", {"pagina_nummer": "veertien"})

    def test_onbekend_bron_type_accepteert_als_vrije_json(self):
        """Onbekende bron_type → geen validatie, raw dict terug."""
        data = {"willekeurig_veld": "waarde"}
        result = valideer_chunk_metadata("onbekend_type", data)
        assert result == data

    def test_bron_type_none_accepteert_als_vrije_json(self):
        """bron_type=None → geen validatie, raw dict terug."""
        data = {"veld": "x"}
        result = valideer_chunk_metadata(None, data)
        assert result == data

    def test_exclude_none_in_output(self):
        """None-waarden worden uitgesloten van het resultaat."""
        result = valideer_chunk_metadata("wetgeving", {"artikel_nummer": "1"})
        assert "lid_nummer" not in result
        assert result["artikel_nummer"] == "1"

    def test_lege_metadata_dict(self):
        """Lege dict voor bekende bron_type → lege dict (alle velden optioneel)."""
        result = valideer_chunk_metadata("wetgeving", {})
        assert result == {}

    def test_roundtrip_wetgeving(self):
        """Serialisatie → deserialisatie behoudt waarden."""
        original = {"artikel_nummer": "42", "sectie": "Hoofdstuk 3"}
        result = valideer_chunk_metadata("wetgeving", original)
        assert result["artikel_nummer"] == "42"
        assert result["sectie"] == "Hoofdstuk 3"
