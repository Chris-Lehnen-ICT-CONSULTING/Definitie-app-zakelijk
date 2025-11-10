"""
DEF-138 Edge Case Tests
Testing compound word classification and zero-score scenarios.
"""

import pytest

from domain.ontological_categories import OntologischeCategorie
from ontologie.improved_classifier import ImprovedOntologyClassifier


class TestCompoundWordEdgeCases:
    """Test edge cases for compound word classification."""

    @pytest.fixture
    def classifier(self):
        """Create classifier instance."""
        return ImprovedOntologyClassifier()

    def test_voegwoord_minimal_context(self, classifier):
        """Test original bug case: voegwoord with minimal context."""
        result = classifier.classify("voegwoord", "Een verbindend element in zinnen.")

        # Should classify as something, not fail with zero scores
        assert result is not None
        assert result.categorie is not None
        assert result.confidence > 0.0
        print(
            f"voegwoord classified as: {result.categorie} (confidence: {result.confidence})"
        )

    def test_bijwoord_common_compound(self, classifier):
        """Test common compound word: bijwoord."""
        result = classifier.classify(
            "bijwoord",
            "Een woord dat een werkwoord, bijvoeglijk naamwoord of ander bijwoord nader bepaalt.",
        )

        assert result is not None
        assert result.categorie is not None
        assert result.confidence > 0.0
        print(
            f"bijwoord classified as: {result.categorie} (confidence: {result.confidence})"
        )

    def test_werkwoord_verb_type(self, classifier):
        """Test compound word representing verb type."""
        result = classifier.classify(
            "werkwoord",
            "Een woord dat een handeling, toestand of gebeurtenis uitdrukt.",
        )

        assert result is not None
        assert result.categorie is not None
        assert result.confidence > 0.0
        print(
            f"werkwoord classified as: {result.categorie} (confidence: {result.confidence})"
        )

    def test_onbekendwoord_unknown_compound(self, classifier):
        """Test unknown/made-up compound word."""
        result = classifier.classify(
            "onbekendwoord", "Dit is een test van een onbekend woord."
        )

        # Should still return valid classification even if word is unknown
        assert result is not None
        assert result.categorie is not None
        # Confidence may be low but should not be zero
        print(
            f"onbekendwoord classified as: {result.categorie} (confidence: {result.confidence})"
        )

    def test_simple_woord_baseline(self, classifier):
        """Test simple case without compound."""
        result = classifier.classify("woord", "Een betekeniseenheid in taal.")

        assert result is not None
        assert result.categorie is not None
        assert result.confidence > 0.0
        print(
            f"woord classified as: {result.categorie} (confidence: {result.confidence})"
        )


class TestZeroScoreScenarios:
    """Test scenarios that previously caused zero confidence scores."""

    @pytest.fixture
    def classifier(self):
        """Create classifier instance."""
        return ImprovedOntologyClassifier()

    def test_empty_context(self, classifier):
        """Test classification with empty context."""
        result = classifier.classify("test", "")

        # Should handle gracefully, not crash
        assert result is not None
        assert result.categorie is not None
        print(
            f"Empty context result: {result.categorie} (confidence: {result.confidence})"
        )

    def test_single_word_context(self, classifier):
        """Test classification with minimal single-word context."""
        result = classifier.classify("begrip", "test")

        assert result is not None
        assert result.categorie is not None
        # May have low confidence but should not be zero
        print(
            f"Single word context: {result.categorie} (confidence: {result.confidence})"
        )

    def test_no_pattern_matches(self, classifier):
        """Test term with context that matches no patterns."""
        result = classifier.classify(
            "xyzabc", "This is completely random text with no meaning."
        )

        assert result is not None
        assert result.categorie is not None
        # Should fall back to default category
        print(
            f"No pattern matches: {result.categorie} (confidence: {result.confidence})"
        )

    def test_all_scores_equal(self, classifier):
        """Test term where all category scores would be equal."""
        # Generic term with generic description
        result = classifier.classify("ding", "Een object of iets.")

        assert result is not None
        assert result.categorie is not None
        assert result.confidence >= 0.0
        print(
            f"Equal scores scenario: {result.categorie} (confidence: {result.confidence})"
        )


class TestPerformanceEdgeCases:
    """Test performance-related edge cases."""

    @pytest.fixture
    def classifier(self):
        """Create classifier instance."""
        return ImprovedOntologyClassifier()

    def test_very_long_context(self, classifier):
        """Test classification with very long context."""
        long_context = " ".join(["Dit is een zeer lange context"] * 100)

        import time

        start = time.time()
        result = classifier.classify("test", long_context)
        elapsed = time.time() - start

        assert result is not None
        assert elapsed < 1.0, f"Classification took too long: {elapsed:.2f}s"
        print(f"Long context classification: {elapsed:.3f}s")

    def test_many_classifications(self, classifier):
        """Test 100 classifications for performance."""
        terms = [
            ("voegwoord", "Verbindend element"),
            ("bijwoord", "Nader bepalend woord"),
            ("werkwoord", "Actie of toestand"),
            ("zelfstandig naamwoord", "Persoon, plaats of ding"),
            ("bijvoeglijk naamwoord", "Eigenschap"),
        ]

        import time

        start = time.time()

        for _i in range(20):  # 20 cycles * 5 terms = 100 classifications
            for term, context in terms:
                result = classifier.classify(term, context)
                assert result is not None
                assert result.confidence > 0.0

        elapsed = time.time() - start
        avg_time = elapsed / 100

        assert avg_time < 0.1, f"Average classification too slow: {avg_time:.3f}s"
        print(
            f"100 classifications in {elapsed:.2f}s (avg: {avg_time:.4f}s per classification)"
        )


class TestClassificationConsistency:
    """Test that classifications are consistent and reproducible."""

    @pytest.fixture
    def classifier(self):
        """Create classifier instance."""
        return ImprovedOntologyClassifier()

    def test_same_input_same_output(self, classifier):
        """Test that same input produces same output."""
        term = "voegwoord"
        context = "Een verbindend element in zinnen."

        result1 = classifier.classify(term, context)
        result2 = classifier.classify(term, context)
        result3 = classifier.classify(term, context)

        # All results should be identical
        assert result1.categorie == result2.categorie == result3.categorie
        assert result1.confidence == result2.confidence == result3.confidence
        print(f"Consistent results: {result1.categorie} @ {result1.confidence}")

    def test_similar_terms_similar_results(self, classifier):
        """Test that similar terms get similar classifications."""
        # All are linguistic/grammatical terms
        voegwoord = classifier.classify("voegwoord", "Verbindt zinsdelen.")
        bijwoord = classifier.classify("bijwoord", "Bepaalt werkwoord nader.")
        werkwoord = classifier.classify("werkwoord", "Drukt handeling uit.")

        # All should be TYPE (grammatical categories are types)
        print(f"voegwoord: {voegwoord.categorie}")
        print(f"bijwoord: {bijwoord.categorie}")
        print(f"werkwoord: {werkwoord.categorie}")

        # All linguistic terms should be classified as TYPE
        assert voegwoord.categorie == OntologischeCategorie.TYPE
        assert bijwoord.categorie == OntologischeCategorie.TYPE
        assert werkwoord.categorie == OntologischeCategorie.TYPE
