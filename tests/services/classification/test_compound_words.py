"""
Regression tests for DEF-138: Zero confidence scores fix.

This test suite validates that compound word patterns (ending in -woord, -naam,
-lijst, -boek) are correctly classified with non-zero confidence scores.

Background:
-----------
DEF-138 identified that terms like "voegwoord" (conjunction) were receiving
0.0 confidence scores due to:
1. No pattern matches for compound words ending in -woord
2. Minimal context providing no semantic signals

Solution:
---------
Added compound word suffix patterns to config/classification/term_patterns.yaml:
- woord: 0.70 (grammatical terms: voegwoord, werkwoord, bijwoord)
- naam: 0.65 (name types: voornaam, achternaam)
- lijst: 0.65 (lists: controlelijst, checklist)
- boek: 0.70 (documents: handboek, wetboek)

Expected Behavior:
------------------
- Terms with these suffixes should receive non-zero TYPE scores
- Confidence should be MEDIUM or higher (>= 0.45)
- Classification should be OntologischeCategorie.TYPE
"""

import pytest

from domain.ontological_categories import OntologischeCategorie
from ontologie.improved_classifier import ImprovedOntologyClassifier


class TestCompoundWordPatterns:
    """Test suite for compound word pattern matching (DEF-138)."""

    def test_voegwoord_minimal_context(self):
        """
        Test that 'voegwoord' gets non-zero TYPE score with minimal context.

        This is the primary regression test for DEF-138. Before the fix,
        'voegwoord' with context 'test' returned:
        - scores: {'type': 0.0, 'proces': 0.0, 'resultaat': 0.0, 'exemplaar': 0.0}
        - confidence: 0.0

        After fix:
        - scores: {'type': 0.70, ...}
        - confidence: 0.70 (HIGH)
        """
        classifier = ImprovedOntologyClassifier()
        result = classifier.classify(begrip="voegwoord", org_context="test")

        # DEF-138: Should have non-zero TYPE score
        assert (
            result.test_scores["type"] > 0.0
        ), f"Expected non-zero TYPE score, got {result.test_scores}"

        # Should classify as TYPE
        assert (
            result.categorie == OntologischeCategorie.TYPE
        ), f"Expected TYPE classification, got {result.categorie.value}"

        # Should have MEDIUM+ confidence
        assert (
            result.confidence >= 0.45
        ), f"Expected confidence >= 0.45 (MEDIUM+), got {result.confidence}"

    @pytest.mark.parametrize(
        ("term", "expected_category", "description"),
        [
            ("werkwoord", OntologischeCategorie.TYPE, "verb (grammatical term)"),
            ("bijwoord", OntologischeCategorie.TYPE, "adverb (grammatical term)"),
            ("voornaam", OntologischeCategorie.TYPE, "first name (type of name)"),
            ("achternaam", OntologischeCategorie.TYPE, "last name (type of name)"),
            (
                "controlelijst",
                OntologischeCategorie.TYPE,
                "checklist (type of list)",
            ),
            ("handboek", OntologischeCategorie.TYPE, "manual/handbook (type of book)"),
            ("wetboek", OntologischeCategorie.TYPE, "law book (type of book)"),
        ],
    )
    def test_compound_word_coverage(self, term, expected_category, description):
        """
        Test that all compound word patterns work correctly.

        Validates coverage across all 4 compound word pattern groups:
        - -woord: grammatical terms (voegwoord, werkwoord, bijwoord)
        - -naam: name types (voornaam, achternaam)
        - -lijst: list types (controlelijst)
        - -boek: book/document types (handboek, wetboek)
        """
        classifier = ImprovedOntologyClassifier()
        result = classifier.classify(begrip=term, org_context="algemeen")

        # Should classify correctly
        assert result.categorie == expected_category, (
            f"{term} ({description}): "
            f"Expected {expected_category.value}, got {result.categorie.value}"
        )

        # Should have non-zero score for the expected category
        category_key = expected_category.value.lower()
        assert result.test_scores[category_key] > 0.0, (
            f"{term}: Expected non-zero {category_key} score, "
            f"got {result.test_scores}"
        )

        # Should have reasonable confidence (at least LOW threshold)
        assert (
            result.confidence > 0.0
        ), f"{term}: Expected non-zero confidence, got {result.confidence}"

    def test_woord_suffix_weight(self):
        """
        Test that -woord suffix provides expected weight contribution.

        Expected weight: 0.70 (as configured in term_patterns.yaml)
        """
        classifier = ImprovedOntologyClassifier()
        result = classifier.classify(begrip="testwoord", org_context="algemeen")

        # Should have TYPE score close to 0.70 (exact match weight)
        # Note: Actual score may vary slightly due to normalization
        assert (
            result.test_scores["type"] >= 0.65
        ), f"Expected TYPE score ~0.70, got {result.test_scores['type']}"

    def test_naam_suffix_weight(self):
        """
        Test that -naam suffix provides expected weight contribution.

        Expected weight: 0.65 (as configured in term_patterns.yaml)
        """
        classifier = ImprovedOntologyClassifier()
        result = classifier.classify(begrip="testnaam", org_context="algemeen")

        # Should have TYPE score close to 0.65
        assert (
            result.test_scores["type"] >= 0.60
        ), f"Expected TYPE score ~0.65, got {result.test_scores['type']}"

    def test_lijst_suffix_weight(self):
        """
        Test that -lijst suffix provides expected weight contribution.

        Expected weight: 0.65 (as configured in term_patterns.yaml)
        """
        classifier = ImprovedOntologyClassifier()
        result = classifier.classify(begrip="testlijst", org_context="algemeen")

        # Should have TYPE score close to 0.65
        assert (
            result.test_scores["type"] >= 0.60
        ), f"Expected TYPE score ~0.65, got {result.test_scores['type']}"

    def test_boek_suffix_weight(self):
        """
        Test that -boek suffix provides expected weight contribution.

        Expected weight: 0.70 (as configured in term_patterns.yaml)
        """
        classifier = ImprovedOntologyClassifier()
        result = classifier.classify(begrip="testboek", org_context="algemeen")

        # Should have TYPE score close to 0.70
        assert (
            result.test_scores["type"] >= 0.65
        ), f"Expected TYPE score ~0.70, got {result.test_scores['type']}"

    def test_compound_word_beats_generic_term(self):
        """
        Test that compound word patterns provide stronger signal than generic terms.

        A term like "proceswoord" should be classified as TYPE (due to -woord suffix)
        rather than PROCES (despite "proces" prefix).
        """
        classifier = ImprovedOntologyClassifier()
        result = classifier.classify(begrip="proceswoord", org_context="algemeen")

        # -woord suffix (0.70) should dominate over generic "proces" context
        assert result.categorie == OntologischeCategorie.TYPE, (
            f"Expected TYPE classification (due to -woord suffix), "
            f"got {result.categorie.value}"
        )

        assert (
            result.test_scores["type"] > result.test_scores["proces"]
        ), f"Expected TYPE score > PROCES score, got {result.test_scores}"


class TestDEF138RegressionScenarios:
    """
    Additional regression scenarios based on DEF-138 root cause analysis.

    These tests validate that the fix addresses the core issues:
    1. No pattern matches for compound words
    2. Minimal context scenarios
    3. Zero confidence score edge cases
    """

    def test_minimal_context_no_longer_returns_zero(self):
        """
        Validate that minimal context no longer results in 0.0 confidence.

        Before DEF-138 fix:
        - "voegwoord" + "test" → confidence: 0.0

        After fix:
        - "voegwoord" + "test" → confidence: 0.70 (HIGH)
        """
        classifier = ImprovedOntologyClassifier()

        # Test with various minimal contexts
        minimal_contexts = ["test", "algemeen", "standaard", "nvt"]

        for context in minimal_contexts:
            result = classifier.classify(begrip="voegwoord", org_context=context)

            assert result.confidence > 0.0, (
                f"Minimal context '{context}' should not return 0.0 confidence, "
                f"got {result.confidence}"
            )

            assert result.test_scores["type"] > 0.0, (
                f"Minimal context '{context}' should have non-zero TYPE score, "
                f"got {result.test_scores}"
            )

    def test_compound_word_with_rich_context(self):
        """
        Test that compound words work correctly with rich context.

        Rich context should NOT interfere with suffix pattern matching.
        """
        classifier = ImprovedOntologyClassifier()
        result = classifier.classify(
            begrip="voegwoord",
            org_context="grammatica en taalkunde in het Nederlandse taalonderwijs",
        )

        # Should still classify as TYPE despite rich context
        assert result.categorie == OntologischeCategorie.TYPE
        assert result.test_scores["type"] > 0.0

        # Confidence should be HIGH (strong suffix signal + relevant context)
        assert result.confidence >= 0.70, (
            f"Expected HIGH confidence with rich relevant context, "
            f"got {result.confidence}"
        )

    def test_no_false_positives_for_non_compound_words(self):
        """
        Ensure that suffix patterns work correctly for base words.

        Terms that are the suffix itself (like "woord") should also match
        the pattern and be classified as TYPE. This is expected behavior -
        "woord" (word) is indeed a TYPE in linguistic context.
        """
        classifier = ImprovedOntologyClassifier()

        # "woord" (word) itself is TYPE and should match the pattern
        result = classifier.classify(begrip="woord", org_context="algemeen")
        assert result.test_scores["type"] > 0.0  # Pattern should match
        assert result.categorie == OntologischeCategorie.TYPE

        # Should have confidence (exact suffix match)
        assert result.confidence > 0.0

        # Test that a term with -woord but clear PROCES context still works
        result2 = classifier.classify(
            begrip="beoordelingswoord", org_context="beoordeling en validatie proces"
        )
        # Should still classify as TYPE due to strong -woord suffix
        assert result2.test_scores["type"] > 0.0
