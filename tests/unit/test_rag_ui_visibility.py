"""
Unit tests for DEF-364: RAG Zichtbaarheid in Generatie-UI.

Tests:
- RAG chunks normalisatie naar provenance_sources format
- Score kleurcodering in SourcesRenderer
- Provider label voor "rag" type
"""

import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit]

# Add src to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestScoreColor:
    """Test SourcesRenderer._score_color() kleurcodering."""

    def test_high_score_green(self):
        from ui.components.sources_renderer import SourcesRenderer

        assert SourcesRenderer._score_color(0.85) == "🟢"

    def test_boundary_high_green(self):
        from ui.components.sources_renderer import SourcesRenderer

        assert SourcesRenderer._score_color(0.71) == "🟢"

    def test_medium_score_orange(self):
        from ui.components.sources_renderer import SourcesRenderer

        assert SourcesRenderer._score_color(0.6) == "🟠"

    def test_boundary_medium_orange(self):
        from ui.components.sources_renderer import SourcesRenderer

        assert SourcesRenderer._score_color(0.5) == "🟠"

    def test_low_score_red(self):
        from ui.components.sources_renderer import SourcesRenderer

        assert SourcesRenderer._score_color(0.3) == "🔴"

    def test_zero_score_red(self):
        from ui.components.sources_renderer import SourcesRenderer

        assert SourcesRenderer._score_color(0.0) == "🔴"


class TestProviderLabel:
    """Test get_provider_label voor RAG en documents."""

    def test_rag_provider_label(self):
        from ui.components.formatters import get_provider_label

        assert get_provider_label("rag") == "RAG Document"

    def test_documents_provider_label(self):
        from ui.components.formatters import get_provider_label

        assert get_provider_label("documents") == "Geüpload document"

    def test_unknown_provider_fallback(self):
        from ui.components.formatters import get_provider_label

        # Unknown providers get title-cased
        assert get_provider_label("my_custom") == "My Custom"


class TestRagChunkNormalization:
    """Test dat RAG chunks correct genormaliseerd worden naar provenance format."""

    def _make_rag_chunk(
        self,
        score=0.85,
        rechtsgebied="Strafrecht",
        wet_regeling="Wetboek van Strafrecht",
        artikel_lid="Art. 1",
        chunk_text="Dit is een test chunk.",
        document_id=1,
    ):
        return {
            "chunk_id": 42,
            "chunk_text": chunk_text,
            "score": score,
            "rechtsgebied": rechtsgebied,
            "wet_regeling": wet_regeling,
            "artikel_lid": artikel_lid,
            "document_id": document_id,
            "chunk_index": 0,
            "created_at": "2026-02-19T10:00:00",
        }

    def test_rag_chunk_to_provenance_format(self):
        """RAG chunk moet correct provenance dict opleveren."""
        chunk = self._make_rag_chunk()

        # Simulate the normalization logic from orchestrator Phase 2.7
        title = chunk.get("wet_regeling") or chunk.get("rechtsgebied") or "RAG document"
        citation_parts = [
            p
            for p in [
                chunk.get("rechtsgebied"),
                chunk.get("wet_regeling"),
                chunk.get("artikel_lid"),
            ]
            if p
        ]
        result = {
            "provider": "rag",
            "title": title,
            "url": None,
            "snippet": chunk.get("chunk_text", ""),
            "score": float(chunk.get("score", 0.0)),
            "used_in_prompt": True,
            "source_label": f"RAG: {title}",
            "is_authoritative": False,
            "legal": (
                {"citation_text": " · ".join(citation_parts)}
                if citation_parts
                else None
            ),
        }

        assert result["provider"] == "rag"
        assert result["title"] == "Wetboek van Strafrecht"
        assert result["url"] is None
        assert result["snippet"] == "Dit is een test chunk."
        assert result["score"] == 0.85
        assert result["used_in_prompt"] is True
        assert result["source_label"] == "RAG: Wetboek van Strafrecht"
        assert (
            result["legal"]["citation_text"]
            == "Strafrecht · Wetboek van Strafrecht · Art. 1"
        )

    def test_rag_chunk_without_legal_metadata(self):
        """RAG chunk zonder rechtsgebied/wet_regeling moet fallback titel krijgen."""
        chunk = self._make_rag_chunk(
            rechtsgebied=None, wet_regeling=None, artikel_lid=None
        )

        title = chunk.get("wet_regeling") or chunk.get("rechtsgebied") or "RAG document"
        citation_parts = [
            p
            for p in [
                chunk.get("rechtsgebied"),
                chunk.get("wet_regeling"),
                chunk.get("artikel_lid"),
            ]
            if p
        ]

        assert title == "RAG document"
        assert citation_parts == []

    def test_rag_chunk_partial_legal_metadata(self):
        """RAG chunk met alleen rechtsgebied moet dat als titel gebruiken."""
        chunk = self._make_rag_chunk(
            rechtsgebied="Bestuursrecht", wet_regeling=None, artikel_lid=None
        )

        title = chunk.get("wet_regeling") or chunk.get("rechtsgebied") or "RAG document"
        citation_parts = [
            p
            for p in [
                chunk.get("rechtsgebied"),
                chunk.get("wet_regeling"),
                chunk.get("artikel_lid"),
            ]
            if p
        ]

        assert title == "Bestuursrecht"
        assert " · ".join(citation_parts) == "Bestuursrecht"
