"""
Tests voor DuplicateDetectionService.

Deze tests valideren alle business logic voor duplicate detection
zonder database dependencies.
"""

from datetime import datetime

import pytest

from services.duplicate_detection_service import (
    DuplicateDetectionService,
    DuplicateMatch,
)
from services.interfaces import Definition


class TestDuplicateDetectionService:
    """Test suite voor DuplicateDetectionService."""

    @pytest.fixture
    def service(self):
        """Create a service instance."""
        # V2: woord-Jaccard is conservatief; gebruik 0.3 drempel
        return DuplicateDetectionService(similarity_threshold=0.3)

    @pytest.fixture
    def sample_definitions(self):
        """Create sample definitions for testing."""
        return [
            Definition(
                id=1,
                begrip="Gemeente",
                definitie="Een lokaal bestuursorgaan",
                organisatorische_context=["Overheid"],
                metadata={"status": "established"},
            ),
            Definition(
                id=2,
                begrip="gemeente",  # lowercase variant
                definitie="Een gemeente is een lokaal bestuursorgaan",
                organisatorische_context=["overheid"],  # lowercase context
                metadata={"status": "draft"},
            ),
            Definition(
                id=3,
                begrip="Gemeentelijk orgaan",
                definitie="Orgaan van de gemeente",
                organisatorische_context=["Overheid"],
                metadata={"status": "established"},
            ),
            Definition(
                id=4,
                begrip="Provincie",
                definitie="Een regionaal bestuursorgaan",
                organisatorische_context=["Overheid"],
                metadata={"status": "established"},
            ),
            Definition(
                id=5,
                begrip="Gemeente",
                definitie="Archived definition",
                organisatorische_context=["Overheid"],
                metadata={"status": "archived"},  # Should be skipped
            ),
        ]

    def test_exact_match_detection(self, service, sample_definitions):
        """Test exact match detection (case insensitive)."""
        new_def = Definition(
            begrip="GEMEENTE",  # Different case
            definitie="Test definitie",
            organisatorische_context=["overheid"],  # Different case
        )

        matches = service.find_duplicates(new_def, sample_definitions)

        # Should find 2 exact matches (id=1 and id=2), but not archived (id=5)
        exact_matches = [m for m in matches if m.match_type == "exact"]
        assert len(exact_matches) == 2
        assert all(m.score == 1.0 for m in exact_matches)
        assert all("Exact match" in m.reason for m in exact_matches)

    def test_fuzzy_match_detection(self, service, sample_definitions):
        """Test fuzzy match detection."""
        new_def = Definition(
            begrip="Gemeentelijke instantie",
            definitie="Test definitie",
            organisatorische_context=["Overheid"],
        )

        matches = service.find_duplicates(new_def, sample_definitions)

        # Should find fuzzy match with "Gemeentelijk orgaan"
        fuzzy_matches = [m for m in matches if m.match_type == "fuzzy"]
        assert len(fuzzy_matches) >= 1
        # Met eenvoudige Jaccard op woorden is de score ~0.33; accepteer >= 0.3
        assert all(m.score >= 0.3 for m in fuzzy_matches)

    def test_no_duplicates(self, service, sample_definitions):
        """Test when no duplicates are found."""
        new_def = Definition(
            begrip="Waterschap",
            definitie="Waterbeheer organisatie",
            organisatorische_context=["Water"],
        )

        matches = service.find_duplicates(new_def, sample_definitions)
        assert len(matches) == 0

    def test_similarity_calculation(self, service):
        """Test Jaccard similarity calculation."""
        # Exact match
        assert service._calculate_similarity("test", "test") == 1.0

        # No overlap
        assert service._calculate_similarity("apple", "orange") == 0.0

        # Partial overlap
        score = service._calculate_similarity(
            "gemeentelijk orgaan", "gemeentelijk bestuur"
        )
        assert 0 < score < 1
        assert score == 1 / 3  # 1 common word out of 3 total unique words

        # Empty strings
        assert service._calculate_similarity("", "test") == 0.0
        assert service._calculate_similarity("test", "") == 0.0
        assert service._calculate_similarity("", "") == 0.0

    def test_threshold_filtering(self, service, sample_definitions):
        """Test that matches below threshold are filtered out."""
        # Set high threshold
        service.update_threshold(0.9)

        new_def = Definition(
            begrip="Gemeentelijk",  # Only one word from "Gemeentelijk orgaan"
            definitie="Test",
            organisatorische_context=["Overheid"],
        )

        matches = service.find_duplicates(new_def, sample_definitions)

        # Should not find fuzzy matches with low similarity
        fuzzy_matches = [m for m in matches if m.match_type == "fuzzy"]
        assert all(m.score > 0.9 for m in fuzzy_matches)

    def test_duplicate_risk_assessment(self, service, sample_definitions):
        """Test risk level determination."""
        # High risk - exact match
        exact_def = Definition(
            begrip="Gemeente", definitie="Test", organisatorische_context=["Overheid"]
        )
        assert service.check_duplicate_risk(exact_def, sample_definitions) == "high"

        # Medium/Low risk - fuzzy match
        fuzzy_def = Definition(
            begrip="Gemeentelijke dienst",
            definitie="Test",
            organisatorische_context=["Overheid"],
        )
        risk = service.check_duplicate_risk(fuzzy_def, sample_definitions)
        assert risk in ["medium", "low", "none"]

        # No risk - no matches
        unique_def = Definition(
            begrip="Uniek begrip", definitie="Test", organisatorische_context=["Uniek"]
        )
        assert service.check_duplicate_risk(unique_def, sample_definitions) == "none"

    def test_duplicate_summary(self, service):
        """Test summary generation."""
        # Empty matches
        summary = service.get_duplicate_summary([])
        assert summary["total"] == 0
        assert summary["risk_level"] == "none"

        # Mixed matches
        matches = [
            DuplicateMatch(
                definition=Definition(begrip="Test1"),
                score=1.0,
                reason="Exact match",
                match_type="exact",
            ),
            DuplicateMatch(
                definition=Definition(begrip="Test2"),
                score=0.85,
                reason="Fuzzy match",
                match_type="fuzzy",
            ),
        ]

        summary = service.get_duplicate_summary(matches)
        assert summary["total"] == 2
        assert summary["exact_matches"] == 1
        assert summary["fuzzy_matches"] == 1
        assert summary["highest_score"] == 1.0
        assert summary["risk_level"] == "high"

    def test_archived_definitions_skipped(self, service, sample_definitions):
        """Test that archived definitions are skipped."""
        new_def = Definition(
            begrip="Gemeente",
            definitie="Test definitie",
            organisatorische_context=["Overheid"],
        )

        matches = service.find_duplicates(new_def, sample_definitions)

        # Should not find the archived definition (id=5)
        matched_ids = [m.definition.id for m in matches]
        assert 5 not in matched_ids

    def test_sorting_by_score(self, service):
        """Test that results are sorted by score (highest first)."""
        definitions = [
            Definition(begrip="Test A", organisatorische_context=["ctx"]),
            Definition(begrip="Test B C", organisatorische_context=["ctx"]),
            Definition(begrip="Test B C D", organisatorische_context=["ctx"]),
        ]

        new_def = Definition(
            begrip="Test B C D",
            definitie="Test",
            organisatorische_context=[
                "different"
            ],  # Different context, so no exact match
        )

        matches = service.find_duplicates(new_def, definitions)

        # Verify sorting
        scores = [m.score for m in matches]
        assert scores == sorted(scores, reverse=True)

        # Highest score should be for "Test B C D"
        if matches:
            assert matches[0].definition.begrip == "Test B C D"

    def test_update_threshold(self, service):
        """Test threshold update."""
        # Valid updates
        service.update_threshold(0.8)
        assert service.threshold == 0.8

        service.update_threshold(0.0)
        assert service.threshold == 0.0

        service.update_threshold(1.0)
        assert service.threshold == 1.0

        # Invalid updates
        with pytest.raises(ValueError):
            service.update_threshold(-0.1)

        with pytest.raises(ValueError):
            service.update_threshold(1.1)


class TestDuplicateDetectionEdgeCases:
    """Edge case tests voor DuplicateDetectionService."""

    def test_definitions_without_context(self):
        """Test handling of definitions without context."""
        service = DuplicateDetectionService()

        def1 = Definition(begrip="Test", organisatorische_context=[])
        def2 = Definition(begrip="Test", organisatorische_context=None)
        def3 = Definition(begrip="Test", organisatorische_context=["Some context"])

        # Two definitions without context should match
        assert service._is_exact_match(def1, def2) is True

        # Definition without context vs with context should not match
        assert service._is_exact_match(def1, def3) is False

    def test_empty_existing_definitions(self):
        """Test with empty existing definitions list."""
        service = DuplicateDetectionService()
        new_def = Definition(begrip="Test")

        matches = service.find_duplicates(new_def, [])
        assert len(matches) == 0

    def test_special_characters_in_begrip(self):
        """Test handling of special characters."""
        service = DuplicateDetectionService()

        definitions = [
            Definition(begrip="Test-begrip", organisatorische_context=["ctx"]),
            Definition(begrip="Test/begrip", organisatorische_context=["ctx"]),
            Definition(begrip="Test.begrip", organisatorische_context=["ctx"]),
        ]

        new_def = Definition(begrip="Test begrip", organisatorische_context=["ctx"])

        # Should not find exact matches due to special chars
        matches = service.find_duplicates(new_def, definitions)
        exact_matches = [m for m in matches if m.match_type == "exact"]
        assert len(exact_matches) == 0

        # But should find fuzzy matches
        fuzzy_matches = [m for m in matches if m.match_type == "fuzzy"]
        assert len(fuzzy_matches) > 0
