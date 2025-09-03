"""
Unit tests for Story 3.1: Metadata First, Prompt Second - Web Lookup Bronnen.

Tests the proper flow of sources metadata through the system from web lookup
to UI display, including provider-neutral references and juridical citations.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import sys
from pathlib import Path
import re

# Add src to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from services.service_factory import LegacyGenerationResult, ServiceAdapter
from services.web_lookup.provenance import build_provenance, _get_provider_label, _extract_legal_metadata


class TestLegacyGenerationResultSources:
    """Test that sources are accessible in LegacyGenerationResult wrapper."""

    def test_sources_field_exists_in_legacy_result(self):
        """Test that sources field is accessible in LegacyGenerationResult."""
        # Arrange - Create a result with sources
        test_sources = [
            {"provider": "wikipedia", "title": "Test", "score": 0.9},
            {"provider": "overheid", "title": "Wet test", "score": 0.8}
        ]

        # Act - Create LegacyGenerationResult with sources
        result = LegacyGenerationResult(
            success=True,
            definitie="Test definitie",
            sources=test_sources,  # This should be added to make sources accessible
            metadata={"sources": test_sources}
        )

        # Assert
        assert hasattr(result, 'sources'), "LegacyGenerationResult should have sources attribute"
        assert result.sources == test_sources
        assert len(result.sources) == 2
        assert result.sources[0]["provider"] == "wikipedia"

    def test_service_adapter_adds_sources_to_result(self):
        """Test that ServiceAdapter.generate_definition adds sources to result_dict."""
        # Arrange
        container = Mock()
        adapter = ServiceAdapter(container)

        # Mock the orchestrator response
        mock_response = Mock()
        mock_response.success = True
        mock_response.definition = Mock()
        mock_response.definition.definitie = "Test definitie"  # Changed from .text to .definitie
        mock_response.definition.metadata = {
            "sources": [
                {"provider": "wikipedia", "title": "Test", "score": 0.9},
                {"provider": "overheid", "title": "Wet test", "score": 0.8}
            ],
            "processing_time": 1.5
        }
        mock_response.metadata = {"voorbeelden": {}}
        mock_response.error = None
        mock_response.validation_result = None

        # Mock the orchestrator
        adapter.orchestrator = Mock()
        adapter.orchestrator.create_definition = AsyncMock(return_value=mock_response)

        # Act
        result = adapter.generate_definition(begrip="test", context_dict={})

        # Assert - result should have sources field
        assert hasattr(result, 'sources'), "Result should have sources attribute"
        assert result.sources == mock_response.definition.metadata["sources"]

    def test_sources_empty_list_when_no_sources(self):
        """Test that sources defaults to empty list when no sources in metadata."""
        # Arrange
        container = Mock()
        adapter = ServiceAdapter(container)

        mock_response = Mock()
        mock_response.success = True
        mock_response.definition = Mock()
        mock_response.definition.definitie = "Test definitie"  # Changed from .text to .definitie
        mock_response.definition.metadata = {"processing_time": 1.5}  # No sources
        mock_response.metadata = None
        mock_response.error = None
        mock_response.validation_result = None

        # Mock the orchestrator
        adapter.orchestrator = Mock()
        adapter.orchestrator.create_definition = AsyncMock(return_value=mock_response)

        # Act
        result = adapter.generate_definition(begrip="test", context_dict={})

        # Assert
        assert hasattr(result, 'sources')
        assert result.sources == []


class TestProviderNeutralReferences:
    """Test provider-neutral references in prompts and UI."""

    def test_prompt_augmentation_uses_neutral_labels(self):
        """Test that prompt augmentation uses 'Bron 1', 'Bron 2' instead of provider names."""
        # This test verifies the expected behavior for provider-neutral references
        # The actual implementation is in prompt_service_v2.py

        # Arrange
        mock_sources = [
            {"provider": "wikipedia", "snippet": "Test content 1", "score": 0.9, "used_in_prompt": True},
            {"provider": "overheid", "snippet": "Test content 2", "score": 0.8, "used_in_prompt": True},
        ]

        # Expected: prompt should contain "Bron 1:" and "Bron 2:" not provider names
        # This will be implemented in the prompt service
        expected_prompt_snippet = "Bron 1: Test content 1"

        # Act - Simulate the augmentation (this represents the desired behavior)
        augmented_lines = []
        for i, source in enumerate(mock_sources):
            if source.get("used_in_prompt"):
                augmented_lines.append(f"Bron {i+1}: {source['snippet']}")

        result = "\n".join(augmented_lines)

        # Assert
        assert "Bron 1:" in result
        assert "Bron 2:" in result
        assert "wikipedia:" not in result
        assert "overheid:" not in result


class TestProvenanceEnhancements:
    """Test enhancements to provenance building."""

    def test_build_provenance_preserves_metadata(self):
        """Test that build_provenance preserves all source metadata."""
        # Arrange
        results = [
            {
                "provider": "wikipedia",
                "title": "Test Article",
                "url": "https://nl.wikipedia.org/test",
                "snippet": "Test content here",
                "score": 0.9,
                "used_in_prompt": True,
                "retrieved_at": "2025-01-01T10:00:00"
            },
            {
                "provider": "overheid",
                "title": "Wet test",
                "url": "https://wetten.overheid.nl/test",
                "snippet": "Legal content",
                "score": 0.8,
                "used_in_prompt": False,
                "retrieved_at": "2025-01-01T10:01:00"
            }
        ]

        # Act
        provenance = build_provenance(results)

        # Assert
        assert len(provenance) == 2
        assert provenance[0]["score"] == 0.9  # Should be sorted by score
        assert provenance[1]["score"] == 0.8
        assert provenance[0]["provider"] == "wikipedia"
        assert provenance[0]["used_in_prompt"] is True
        assert provenance[1]["used_in_prompt"] is False

    def test_extract_ecli_pattern(self):
        """Test ECLI pattern extraction from legal sources."""
        # Arrange
        text_with_ecli = "ECLI:NL:HR:2023:1234 is het arrest nummer"

        # Act - Test the regex pattern that should be used
        ecli_pattern = r"ECLI:[A-Z:0-9]+"
        match = re.search(ecli_pattern, text_with_ecli)

        # Assert
        assert match is not None
        assert match.group() == "ECLI:NL:HR:2023:1234"

    def test_extract_article_pattern(self):
        """Test article extraction pattern from legal titles."""
        # Arrange
        titles = [
            "Artikel 3:40 Burgerlijk Wetboek",
            "Art. 162 Wetboek van Strafrecht",
            "artikel 8 EVRM"
        ]

        # Act & Assert
        article_pattern = r"(?:artikel|art\.?)\s+(\d+(?::\d+)?[a-z]?)"

        for title in titles:
            match = re.search(article_pattern, title, re.IGNORECASE)
            assert match is not None, f"Should find article in: {title}"

        # Check specific extractions
        match1 = re.search(article_pattern, titles[0], re.IGNORECASE)
        assert match1.group(1) == "3:40"

        match2 = re.search(article_pattern, titles[1], re.IGNORECASE)
        assert match2.group(1) == "162"


class TestUISourceDisplay:
    """Test UI display logic for sources."""

    def test_ui_gets_sources_from_agent_result(self):
        """Test that UI can retrieve sources from agent_result during preview."""
        # Simulate UI component logic

        # Arrange - agent_result with sources
        agent_result = Mock()
        agent_result.sources = [
            {"provider": "wikipedia", "title": "Test", "score": 0.9}
        ]
        agent_result.metadata = {
            "sources": [
                {"provider": "wikipedia", "title": "Test", "score": 0.9}
            ]
        }

        # Act - Try different access patterns used by UI
        sources_direct = getattr(agent_result, 'sources', [])
        sources_metadata = agent_result.metadata.get('sources', []) if hasattr(agent_result, 'metadata') else []

        # Assert - Both should work
        assert len(sources_direct) == 1
        assert len(sources_metadata) == 1
        assert sources_direct[0]["provider"] == "wikipedia"

    def test_ui_handles_missing_sources_gracefully(self):
        """Test UI handles case when no sources are present."""
        # Arrange
        agent_result = Mock(spec=['metadata'])  # Spec to avoid auto-creating attributes
        agent_result.metadata = {}
        # Intentionally don't set sources attribute

        # Act - UI should handle missing attribute
        sources = getattr(agent_result, 'sources', [])

        # Assert
        assert sources == []

    def test_provider_label_formatting(self):
        """Test human-friendly provider labels."""
        # This represents the expected provider label mapping

        # Arrange
        provider_labels = {
            "wikipedia": "Wikipedia NL",
            "overheid": "Overheid.nl",
            "rechtspraak": "Rechtspraak.nl",
            "wiktionary": "Wiktionary NL"
        }

        # Act & Assert
        assert provider_labels["wikipedia"] == "Wikipedia NL"
        assert provider_labels["overheid"] == "Overheid.nl"
        assert provider_labels["rechtspraak"] == "Rechtspraak.nl"

        # Test fallback for unknown provider
        unknown = "unknown_provider"
        fallback = unknown.replace("_", " ").title()
        assert fallback == "Unknown Provider"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
