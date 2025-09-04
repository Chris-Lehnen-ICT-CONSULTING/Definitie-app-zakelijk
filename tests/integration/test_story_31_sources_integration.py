"""
Integration tests for Story 3.1: End-to-end source metadata flow.

Tests the complete flow from web lookup through prompt generation to UI display.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from services.service_factory import ServiceAdapter
from services.web_lookup.provenance import build_provenance


@pytest.mark.integration
class TestSourceMetadataE2E:
    """Test end-to-end flow of source metadata through the system."""

    def test_sources_flow_from_response_to_ui(self):
        """Test that sources from orchestrator response are accessible in result."""
        # Arrange - Create adapter with mocked container
        container = Mock()
        adapter = ServiceAdapter(container)

        # Mock web lookup results that should flow through
        web_lookup_results = [
            {
                "provider": "wikipedia",
                "title": "Rechtspersoon - Wikipedia",
                "url": "https://nl.wikipedia.org/wiki/Rechtspersoon",
                "snippet": "Een rechtspersoon is een juridische entiteit...",
                "score": 0.95,
                "used_in_prompt": True,
                "source_label": "Wikipedia NL"
            },
            {
                "provider": "overheid",
                "title": "Artikel 2:3 BW",
                "url": "https://wetten.overheid.nl/test",
                "snippet": "Rechtspersonen zijn...",
                "score": 0.85,
                "used_in_prompt": True,
                "source_label": "Overheid.nl"
            }
        ]

        # Mock the orchestrator response
        mock_response = Mock()
        mock_response.success = True
        mock_response.definition = Mock()
        mock_response.definition.definitie = "Een rechtspersoon is een juridische entiteit met rechtsbevoegdheid."
        mock_response.definition.metadata = {
            "sources": web_lookup_results,
            "processing_time": 2.5
        }
        mock_response.metadata = {"voorbeelden": {}}
        mock_response.validation_result = None
        mock_response.error = None

        # Setup orchestrator mock
        adapter.orchestrator = Mock()
        adapter.orchestrator.create_definition = AsyncMock(return_value=mock_response)

        # Act - Generate definition
        result = adapter.generate_definition(
            begrip="rechtspersoon",
            context_dict={}
        )

        # Assert - Sources should be accessible in result
        assert hasattr(result, 'sources'), "Result should have sources attribute"
        assert len(result.sources) == 2
        assert result.sources[0]["provider"] == "wikipedia"
        assert result.sources[0]["used_in_prompt"] is True
        assert result.sources[1]["provider"] == "overheid"

        # Sources should also be in metadata
        assert hasattr(result, 'metadata')
        assert "sources" in result.metadata
        assert result.metadata["sources"] == web_lookup_results

    def test_sources_with_juridical_metadata(self):
        """Test that juridical sources include legal metadata."""
        # Arrange
        container = Mock()
        adapter = ServiceAdapter(container)

        # Mock response with juridical sources including legal metadata
        juridical_sources = [
            {
                "provider": "rechtspraak",
                "title": "ECLI:NL:HR:2023:1234",
                "url": "https://uitspraken.rechtspraak.nl/test",
                "snippet": "Het Hof oordeelt dat...",
                "score": 0.98,
                "used_in_prompt": True,
                "legal": {
                    "ecli": "ECLI:NL:HR:2023:1234",
                    "citation_text": "ECLI:NL:HR:2023:1234"
                },
                "is_authoritative": True,
                "source_label": "Rechtspraak.nl"
            }
        ]

        # Mock response
        mock_response = Mock()
        mock_response.success = True
        mock_response.definition = Mock()
        mock_response.definition.definitie = "Nietigheid van rechtshandelingen..."
        mock_response.definition.metadata = {
            "sources": juridical_sources
        }
        mock_response.metadata = {}
        mock_response.validation_result = None
        mock_response.error = None

        adapter.orchestrator = Mock()
        adapter.orchestrator.create_definition = AsyncMock(return_value=mock_response)

        # Act
        result = adapter.generate_definition(
            begrip="nietigheid",
            context_dict={}
        )

        # Assert - Legal metadata should be preserved
        assert result.sources[0]["legal"]["ecli"] == "ECLI:NL:HR:2023:1234"
        assert result.sources[0]["is_authoritative"] is True

    def test_no_sources_scenario(self):
        """Test behavior when no web lookup sources are available."""
        # Arrange
        container = Mock()
        adapter = ServiceAdapter(container)

        # Mock response with no sources
        mock_response = Mock()
        mock_response.success = True
        mock_response.definition = Mock()
        mock_response.definition.definitie = "Test definitie zonder bronnen"
        mock_response.definition.metadata = {
            "processing_time": 1.0
            # No sources key
        }
        mock_response.metadata = None
        mock_response.validation_result = None
        mock_response.error = None

        adapter.orchestrator = Mock()
        adapter.orchestrator.create_definition = AsyncMock(return_value=mock_response)

        # Act
        result = adapter.generate_definition(
            begrip="test",
            context_dict={}
        )

        # Assert - Should have empty sources list
        assert hasattr(result, 'sources')
        assert result.sources == []
        # UI should be able to detect this and show appropriate message


@pytest.mark.integration
class TestProvenanceBuilding:
    """Test provenance building with all enhancements."""

    def test_build_provenance_with_legal_extraction(self):
        """Test that build_provenance extracts legal metadata when requested."""
        # Arrange
        results = [
            {
                "provider": "rechtspraak",
                "title": "ECLI:NL:HR:2023:1234 - Hoge Raad",
                "url": "https://rechtspraak.nl/test",
                "snippet": "Test content",
                "score": 0.95,
                "metadata": {
                    "dc_identifier": "ECLI:NL:HR:2023:1234"
                }
            },
            {
                "provider": "overheid",
                "title": "Artikel 3:40 Burgerlijk Wetboek",
                "url": "https://wetten.overheid.nl/test",
                "snippet": "Wetsartikel content",
                "score": 0.85
            }
        ]

        # Act
        provenance = build_provenance(results, extract_legal=True)

        # Assert
        assert len(provenance) == 2

        # First source (rechtspraak) should have legal metadata
        assert provenance[0]["provider"] == "rechtspraak"
        assert "legal" in provenance[0]
        assert provenance[0]["legal"]["ecli"] == "ECLI:NL:HR:2023:1234"
        assert provenance[0]["is_authoritative"] is True

        # Second source (overheid) should have article extraction
        assert provenance[1]["provider"] == "overheid"
        assert "legal" in provenance[1]
        assert provenance[1]["legal"]["article"] == "3:40"
        assert provenance[1]["legal"]["law"] in ["Burgerlijk Wetboek", "BW"]
        assert provenance[1]["is_authoritative"] is True

    def test_provider_labels_and_sorting(self):
        """Test that provenance adds provider labels and sorts by score."""
        # Arrange
        results = [
            {"provider": "wikipedia", "score": 0.7, "title": "Test 1"},
            {"provider": "overheid", "score": 0.9, "title": "Test 2"},
            {"provider": "rechtspraak", "score": 0.95, "title": "Test 3"}
        ]

        # Act
        provenance = build_provenance(results)

        # Assert - Should be sorted by score descending
        assert provenance[0]["score"] == 0.95
        assert provenance[0]["source_label"] == "Rechtspraak.nl"
        assert provenance[1]["score"] == 0.9
        assert provenance[1]["source_label"] == "Overheid.nl"
        assert provenance[2]["score"] == 0.7
        assert provenance[2]["source_label"] == "Wikipedia NL"


@pytest.mark.integration
class TestUISourceAccess:
    """Test UI access patterns for sources."""

    def test_ui_can_access_sources_multiple_ways(self):
        """Test that UI can access sources through different patterns."""
        from services.service_factory import LegacyGenerationResult

        # Arrange - Create result with sources
        sources = [
            {"provider": "wikipedia", "title": "Test", "score": 0.9}
        ]

        result = LegacyGenerationResult(
            success=True,
            definitie="Test",
            sources=sources,
            metadata={"sources": sources}
        )

        # Act & Assert - All access patterns should work
        # Direct attribute access
        assert hasattr(result, 'sources')
        assert result.sources == sources

        # Via metadata
        assert result.metadata["sources"] == sources

        # Via getattr with default
        assert getattr(result, 'sources', []) == sources

        # Check that both point to same data
        assert result.sources is result.metadata["sources"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
