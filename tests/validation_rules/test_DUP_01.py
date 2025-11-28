"""
Unit tests voor DUP_01 toetsregel (Database Duplicate Detection).

DEF-183: Toegevoegd na multiagent analyse die ontbrekende test coverage identificeerde.

Deze tests instantiëren DUP_01 direct en mocken de repository,
waardoor complexe import chains worden vermeden.
"""

from unittest.mock import Mock

import pytest


class TestDUP01:
    """Test suite voor DUP_01 duplicate detection rule."""

    @pytest.fixture
    def mock_repository(self):
        """Create mock repository with default empty response."""
        repo = Mock()
        repo.search_definitions = Mock(return_value=[])
        return repo

    @pytest.fixture
    def dup_instance(self, mock_repository):
        """Create DUP01 instance with mocked repository.

        We import DUP01 and manually set the repository to avoid
        the complex container initialization chain.
        """
        from toetsregels.regels.DUP_01 import DUP01

        instance = DUP01()
        instance.repository = mock_repository
        return instance

    # ==================== Initialization Tests ====================

    def test_dup01_has_repository_attribute(self):
        """Test that DUP01 has a repository attribute."""
        from toetsregels.regels.DUP_01 import DUP01

        instance = DUP01()
        # Should have repository attribute (even if None)
        assert hasattr(instance, "repository")

    # ==================== Check Method - Edge Cases ====================

    def test_check_without_repository_returns_skipped(self):
        """Test graceful handling when repository unavailable."""
        from toetsregels.regels.DUP_01 import DUP01

        dup = DUP01()
        dup.repository = None  # Explicitly set to None

        result = dup.check("test definitie", "test begrip")

        assert result["voldoet"] is True
        assert "overgeslagen" in result["toelichting"]

    def test_check_without_begrip_returns_skipped(self, dup_instance):
        """Test that missing begrip skips the check."""
        result = dup_instance.check("test definitie", begrip="")

        assert result["voldoet"] is True
        assert "begrip ontbreekt" in result["toelichting"]

    def test_check_no_existing_definitions(self, dup_instance, mock_repository):
        """Test when no existing definitions found."""
        mock_repository.search_definitions.return_value = []

        result = dup_instance.check("Een nieuwe definitie", begrip="nieuw_begrip")

        assert result["voldoet"] is True
        assert "Geen bestaande definities" in result["toelichting"]

    # ==================== Check Method - Duplicate Detection ====================

    def test_check_finds_exact_duplicate(self, dup_instance, mock_repository):
        """Test detection of exact duplicate definitions."""
        mock_repository.search_definitions.return_value = [
            {"id": 123, "begrip": "test", "definitie": "Dit is een test definitie"}
        ]

        result = dup_instance.check("Dit is een test definitie", begrip="test")

        assert result["voldoet"] is False
        assert "Exacte duplicate" in result["toelichting"]
        assert "123" in result["toelichting"]
        assert "suggestie" in result

    def test_check_uses_gecorrigeerd_if_available(self, dup_instance, mock_repository):
        """Test that definitie_gecorrigeerd is preferred over definitie."""
        mock_repository.search_definitions.return_value = [
            {
                "id": 456,
                "begrip": "test",
                "definitie": "oude versie",
                "definitie_gecorrigeerd": "gecorrigeerde versie",
            }
        ]

        result = dup_instance.check("gecorrigeerde versie", begrip="test")

        assert result["voldoet"] is False
        assert "Exacte duplicate" in result["toelichting"]

    def test_check_finds_similar_definition_above_threshold(
        self, dup_instance, mock_repository
    ):
        """Test detection of highly similar definitions (>90% overlap).

        DUP_01 uses `> 0.9` threshold.
        With 22 words and 1 different: 21/23 = 91.3% (above 90% threshold)
        """
        # 22 word sentence for >90% similarity with 1 word change
        mock_repository.search_definitions.return_value = [
            {
                "id": 789,
                "begrip": "test",
                "definitie": "Een formele beschrijving van een begrip dat wordt gebruikt binnen een specifiek domein om eenduidige communicatie te waarborgen en misverstanden te voorkomen in de praktijk",
            }
        ]

        # Change just one word (beschrijving -> omschrijving): 21 common / 23 total = 91.3%
        result = dup_instance.check(
            "Een formele omschrijving van een begrip dat wordt gebruikt binnen een specifiek domein om eenduidige communicatie te waarborgen en misverstanden te voorkomen in de praktijk",
            begrip="test",
        )

        assert result["voldoet"] is False
        assert "vergelijkbare" in result["toelichting"].lower()

    def test_check_allows_sufficiently_different_definition(
        self, dup_instance, mock_repository
    ):
        """Test that sufficiently different definitions pass."""
        mock_repository.search_definitions.return_value = [
            {
                "id": 101,
                "begrip": "test",
                "definitie": "Een heel andere definitie met andere woorden",
            }
        ]

        result = dup_instance.check(
            "Volledig nieuwe tekst zonder overlap met bestaande content",
            begrip="test",
        )

        assert result["voldoet"] is True
        assert "Geen duplicates" in result["toelichting"]

    def test_check_case_insensitive_begrip_match(self, dup_instance, mock_repository):
        """Test that begrip matching is case-insensitive."""
        mock_repository.search_definitions.return_value = [
            {"id": 111, "begrip": "TEST", "definitie": "Exacte tekst hier"}
        ]

        result = dup_instance.check("Exacte tekst hier", begrip="test")

        assert result["voldoet"] is False
        assert "Exacte duplicate" in result["toelichting"]

    def test_check_handles_search_exception(self, dup_instance, mock_repository):
        """Test handling of exceptions during search."""
        mock_repository.search_definitions.side_effect = Exception("Database error")

        result = dup_instance.check("Een definitie", begrip="test")

        assert result["voldoet"] is True
        assert "technische fout" in result["toelichting"]

    # ==================== Normalize Text Helper ====================

    def test_normalize_lowercase(self, dup_instance):
        """Test that text is lowercased."""
        result = dup_instance._normalize_text("TEST Definitie HIER")
        assert result == "test definitie hier"

    def test_normalize_strips_whitespace(self, dup_instance):
        """Test that leading/trailing whitespace is removed."""
        result = dup_instance._normalize_text("  tekst met spaties  ")
        assert result == "tekst met spaties"

    def test_normalize_removes_trailing_punctuation(self, dup_instance):
        """Test that trailing punctuation is removed."""
        assert dup_instance._normalize_text("definitie.") == "definitie"
        assert dup_instance._normalize_text("definitie...") == "definitie"
        assert dup_instance._normalize_text("definitie!") == "definitie"
        assert dup_instance._normalize_text("definitie?") == "definitie"
        assert dup_instance._normalize_text("definitie;") == "definitie"
        assert dup_instance._normalize_text("definitie:") == "definitie"

    def test_normalize_collapses_whitespace(self, dup_instance):
        """Test that multiple spaces are collapsed to single space."""
        result = dup_instance._normalize_text("woord1    woord2")
        assert result == "woord1 woord2"

    def test_normalize_empty_string(self, dup_instance):
        """Test handling of empty string."""
        assert dup_instance._normalize_text("") == ""

    def test_normalize_none_returns_empty(self, dup_instance):
        """Test handling of None input."""
        assert dup_instance._normalize_text(None) == ""

    # ==================== Calculate Similarity Helper ====================

    def test_similarity_identical_texts(self, dup_instance):
        """Test that identical texts have similarity 1.0."""
        result = dup_instance._calculate_similarity("a b c", "a b c")
        assert result == 1.0

    def test_similarity_completely_different_texts(self, dup_instance):
        """Test that completely different texts have similarity 0.0."""
        result = dup_instance._calculate_similarity("a b c", "d e f")
        assert result == 0.0

    def test_similarity_partial_overlap(self, dup_instance):
        """Test partial overlap calculation."""
        # Words: {a, b, c, d} and {a, b, e, f}
        # Intersection: {a, b} = 2
        # Union: {a, b, c, d, e, f} = 6
        # Jaccard: 2/6 = 0.333...
        result = dup_instance._calculate_similarity("a b c d", "a b e f")
        assert 0.3 < result < 0.4

    def test_similarity_empty_first_text(self, dup_instance):
        """Test that empty first text returns 0."""
        result = dup_instance._calculate_similarity("", "a b c")
        assert result == 0.0

    def test_similarity_empty_second_text(self, dup_instance):
        """Test that empty second text returns 0."""
        result = dup_instance._calculate_similarity("a b c", "")
        assert result == 0.0

    def test_similarity_both_empty(self, dup_instance):
        """Test that two empty texts return 0."""
        result = dup_instance._calculate_similarity("", "")
        assert result == 0.0

    def test_similarity_high_overlap(self, dup_instance):
        """Test high similarity detection."""
        # 9 matching words, 1 different
        text1 = "een twee drie vier vijf zes zeven acht negen tien"
        text2 = "een twee drie vier vijf zes zeven acht negen elf"
        # Intersection: 9, Union: 11, Jaccard: 9/11 ≈ 0.818

        result = dup_instance._calculate_similarity(text1, text2)
        assert result > 0.8
