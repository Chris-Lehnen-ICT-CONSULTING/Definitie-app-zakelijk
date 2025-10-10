"""
Comprehensive Edge Case Test Suite for UFO Classifier
======================================================
Tests for all identified bugs and edge cases to ensure 95% precision target
"""

import gc
import os
import sys
import time

import psutil
import pytest

# Import the classifier (adjust path as needed)
from src.services.ufo_classifier_service import (DutchLegalLexicon,
                                                 UFOCategory,
                                                 UFOClassifierService)


class TestEdgeCasesEmptyAndWhitespace:
    """Test edge cases with empty strings and whitespace."""

    @pytest.fixture()
    def classifier(self):
        return UFOClassifierService()

    def test_empty_strings(self, classifier):
        """Test that empty strings are properly rejected."""
        with pytest.raises(ValueError, match="verplicht"):
            classifier.classify("", "")

    def test_whitespace_only(self, classifier):
        """Test that whitespace-only strings are rejected."""
        with pytest.raises(ValueError, match="verplicht"):
            classifier.classify("   ", "\t\n")

    def test_mixed_whitespace(self, classifier):
        """Test various whitespace combinations."""
        test_cases = [
            ("", "valid"),
            ("valid", ""),
            ("\n", "valid"),
            ("valid", "\t"),
            (" \n\t ", " \n\t "),
        ]

        for term, definition in test_cases:
            with pytest.raises(ValueError):
                classifier.classify(term, definition)

    def test_whitespace_normalization(self, classifier):
        """Test that leading/trailing whitespace is handled."""
        result = classifier.classify("  verdachte  ", "  Persoon die wordt verdacht  ")
        assert result.term == "verdachte"  # Should be trimmed
        assert result.confidence > 0


class TestEdgeCasesUnicode:
    """Test Unicode edge cases specific to Dutch text."""

    @pytest.fixture()
    def classifier(self):
        return UFOClassifierService()

    def test_dutch_diacritics(self, classifier):
        """Test Dutch words with diacritics."""
        test_cases = [
            ("café", "Een établissement voor consumpties"),
            ("coöperatie", "Een samenwerkingsverband"),
            ("reünie", "Een bijeenkomst van oud-leden"),
            ("naïef", "Onschuldig en goedgelovig"),
        ]

        for term, definition in test_cases:
            result = classifier.classify(term, definition)
            assert result.primary_category is not None
            assert result.confidence > 0

    def test_unicode_normalization_nfc_nfd(self, classifier):
        """Test that different Unicode forms are handled consistently."""
        # Same word in NFC (composed) and NFD (decomposed) forms
        term_nfc = "café"  # é as single character
        term_nfd = "cafe\u0301"  # e + combining acute accent

        result_nfc = classifier.classify(term_nfc, "Een drinkgelegenheid")
        result_nfd = classifier.classify(term_nfd, "Een drinkgelegenheid")

        # Should classify the same regardless of Unicode form
        assert result_nfc.primary_category == result_nfd.primary_category

    def test_dutch_ij_ligature(self, classifier):
        """Test Dutch IJ ligature handling."""
        # Different representations of IJ
        test_cases = [
            ("Ĳssel", "Een rivier in Nederland"),  # Ligature
            ("IJssel", "Een rivier in Nederland"),  # Two characters
            ("ijssel", "Een rivier in Nederland"),  # Lowercase
        ]

        results = []
        for term, definition in test_cases:
            result = classifier.classify(term, definition)
            results.append(result.primary_category)

        # All should classify consistently
        assert len(set(results)) == 1, "IJ variants classified differently"

    def test_unicode_edge_characters(self, classifier):
        """Test edge Unicode characters that might break regex."""
        problematic_chars = [
            ("test\u200b", "Zero-width space"),  # Zero-width space
            ("test\ufeff", "BOM character"),  # Byte order mark
            ("test\u00a0", "Non-breaking space"),  # Non-breaking space
            ("test\u2028", "Line separator"),  # Line separator
            ("test\u2029", "Paragraph separator"),  # Paragraph separator
        ]

        for term, definition in problematic_chars:
            # Should not crash
            try:
                result = classifier.classify(term, f"Test met {definition}")
                assert result is not None
            except ValueError:
                # Acceptable to reject these
                pass


class TestEdgeCasesSpecialCharacters:
    """Test special characters and potential injection attempts."""

    @pytest.fixture()
    def classifier(self):
        return UFOClassifierService()

    def test_regex_special_characters(self, classifier):
        """Test that regex special characters don't break pattern matching."""
        special_terms = [
            ("test()", "Een functie in programmeren"),
            ("test[]", "Een array notatie"),
            ("test{}", "Een object notatie"),
            ("test.*", "Een wildcard pattern"),
            ("test|or", "Een OR operatie"),
            ("test\\n", "Met een newline"),
            ("test$", "Met een dollar teken"),
            ("test^", "Met een caret"),
        ]

        for term, definition in special_terms:
            # Should not crash or cause regex errors
            result = classifier.classify(term, definition)
            assert result is not None
            assert result.primary_category is not None

    def test_sql_injection_patterns(self, classifier):
        """Test that SQL injection patterns are handled safely."""
        injection_attempts = [
            ("'; DROP TABLE users; --", "Malicious input"),
            ("1=1", "Always true condition"),
            ("admin' OR '1'='1", "Auth bypass attempt"),
            ("SELECT * FROM", "SQL query"),
        ]

        for term, definition in injection_attempts:
            # Should either reject or handle safely
            try:
                result = classifier.classify(term, definition)
                # If it doesn't reject, should at least classify safely
                assert result.primary_category is not None
            except ValueError:
                # Rejection is acceptable
                pass

    def test_html_javascript_injection(self, classifier):
        """Test HTML/JavaScript injection patterns."""
        injection_attempts = [
            ("<script>alert('xss')</script>", "XSS attempt"),
            ("javascript:void(0)", "JavaScript protocol"),
            ("<img src=x onerror=alert(1)>", "Image XSS"),
            ("${alert(1)}", "Template injection"),
        ]

        for term, definition in injection_attempts:
            try:
                result = classifier.classify(term, definition)
                assert result.primary_category is not None
            except ValueError:
                pass


class TestEdgeCasesPerformance:
    """Test performance edge cases."""

    @pytest.fixture()
    def classifier(self):
        return UFOClassifierService()

    def test_very_long_strings(self, classifier):
        """Test with extremely long input strings."""
        # Create very long strings
        long_term = "verdachte" * 100  # ~900 characters
        long_definition = "Persoon die wordt verdacht " * 500  # ~15000 characters

        start = time.time()
        result = classifier.classify(long_term[:1000], long_definition[:5000])
        elapsed = time.time() - start

        assert result is not None
        assert elapsed < 1.0, f"Classification took {elapsed:.2f}s, too slow"

    def test_many_pattern_matches(self, classifier):
        """Test performance with text that matches many patterns."""
        # Text with many legal terms
        complex_definition = """
        De verdachte persoon, in de hoedanigheid van eigenaar van het gebouw,
        heeft tijdens de procedure een overeenkomst gesloten met de verhuurder,
        waarbij de officier van justitie een dagvaarding heeft uitgebracht voor
        de rechtbank, waar het onderzoek in de voorlopige fase zich bevindt.
        Het betreft een bedrag van 10.000 euro met een complexiteit die de
        betrouwbaarheid van de zaak beïnvloedt.
        """

        start = time.time()
        result = classifier.classify("complexe zaak", complex_definition)
        elapsed = time.time() - start

        assert elapsed < 0.5, f"Complex classification took {elapsed:.2f}s"
        assert len(result.matched_patterns) > 10  # Should find many patterns

    @pytest.mark.slow()
    def test_batch_memory_usage(self, classifier):
        """Test memory usage with large batches."""
        # Create large batch
        large_batch = [(f"term_{i}", f"Definitie nummer {i}") for i in range(1000)]

        # Measure memory before
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / 1024 / 1024  # MB

        # Process batch
        results = classifier.batch_classify(large_batch)

        # Force garbage collection
        gc.collect()

        # Measure memory after
        mem_after = process.memory_info().rss / 1024 / 1024  # MB
        mem_increase = mem_after - mem_before

        assert len(results) == 1000
        assert mem_increase < 100, f"Memory increased by {mem_increase:.1f}MB"


class TestEdgeCasesNumericAndMeasurements:
    """Test edge cases with numbers and measurements."""

    @pytest.fixture()
    def classifier(self):
        return UFOClassifierService()

    def test_extreme_numbers(self, classifier):
        """Test with very large and very small numbers."""
        test_cases = [
            ("grote boete", f"Een boete van {10**12} euro"),
            ("kleine boete", "Een boete van 0.00001 euro"),
            ("negatief bedrag", "Een schuld van -1000 euro"),
            ("infinity", "Een bedrag van inf euro"),
        ]

        for term, definition in test_cases:
            result = classifier.classify(term, definition)
            # Should handle numeric extremes
            assert result.primary_category in [UFOCategory.QUANTITY, UFOCategory.KIND]

    def test_mixed_units(self, classifier):
        """Test with mixed measurement units."""
        test_cases = [
            ("afstand", "Een afstand van 5 km, 300 meter en 50 cm"),
            ("tijd", "Een periode van 2 jaar, 3 maanden en 15 dagen"),
            ("complex bedrag", "EUR 1.000,50 of $1,234.56"),
        ]

        for term, definition in test_cases:
            result = classifier.classify(term, definition)
            assert result.primary_category is not None

    def test_percentage_edge_cases(self, classifier):
        """Test percentage edge cases."""
        test_cases = [
            ("percentage", "Een aandeel van 0%"),
            ("percentage", "Een aandeel van 100%"),
            ("percentage", "Een aandeel van 150%"),  # Over 100%
            ("percentage", "Een aandeel van -10%"),  # Negative
        ]

        for term, definition in test_cases:
            result = classifier.classify(term, definition)
            assert result.primary_category in [
                UFOCategory.QUANTITY,
                UFOCategory.QUALITY,
            ]


class TestEdgeCasesDisambiguation:
    """Test disambiguation edge cases."""

    @pytest.fixture()
    def classifier(self):
        return UFOClassifierService()

    def test_recursive_disambiguation(self, classifier):
        """Test that recursive disambiguation doesn't cause infinite loops."""
        # Create a definition that could trigger recursive disambiguation
        tricky_definition = """
        Een zaak betreffende een zaak over de zaak van de zaak waarbij
        de procedure voor de procedure tijdens de procedure plaatsvindt.
        """

        start = time.time()
        result = classifier.classify("zaak", tricky_definition)
        elapsed = time.time() - start

        assert elapsed < 1.0, "Possible infinite loop in disambiguation"
        assert result.primary_category is not None

    def test_conflicting_disambiguation_rules(self, classifier):
        """Test when multiple disambiguation rules apply."""
        # Definition that matches multiple disambiguation patterns
        ambiguous = """
        Het sluiten van een huwelijk tussen twee personen waarbij het huwelijk
        als juridische band wordt vastgelegd tijdens de huwelijksvoltrekking.
        """

        result = classifier.classify("huwelijk", ambiguous)

        # Should pick one category decisively
        assert result.primary_category in [UFOCategory.EVENT, UFOCategory.RELATOR]
        # Should document the disambiguation
        assert len(result.disambiguation_notes) > 0 or len(result.decision_path) > 5


class TestEdgeCasesConfidenceCalculation:
    """Test confidence calculation edge cases."""

    @pytest.fixture()
    def classifier(self):
        return UFOClassifierService()

    def test_zero_matches_confidence(self, classifier):
        """Test confidence when no patterns match."""
        # Nonsense that matches nothing
        result = classifier.classify("xyzabc", "qwerty uiop asdfg")

        # Should still classify (default to KIND) but with low confidence
        assert result.primary_category == UFOCategory.KIND
        assert result.confidence < 0.3

    def test_all_categories_match_equally(self, classifier):
        """Test when all categories have equal scores."""
        # Very generic definition
        generic = "Het is wat het is en doet wat het doet"

        result = classifier.classify("iets", generic)

        # Should pick something but with low confidence
        assert result.primary_category is not None
        assert result.confidence < 0.5

    def test_single_strong_match(self, classifier):
        """Test high confidence with clear match."""
        result = classifier.classify(
            "arrestatie",
            "Het aanhouden van een persoon door de politie tijdens het onderzoek",
        )

        assert result.primary_category == UFOCategory.EVENT
        assert result.confidence > 0.7


class TestEdgeCasesErrorHandling:
    """Test error handling and recovery."""

    @pytest.fixture()
    def classifier(self):
        return UFOClassifierService()

    def test_none_input(self, classifier):
        """Test that None input is handled properly."""
        with pytest.raises((ValueError, TypeError)):
            classifier.classify(None, None)

        with pytest.raises((ValueError, TypeError)):
            classifier.classify("term", None)

        with pytest.raises((ValueError, TypeError)):
            classifier.classify(None, "definition")

    def test_non_string_input(self, classifier):
        """Test non-string input handling."""
        test_cases = [
            (123, 456),
            ([], {}),
            (True, False),
            (object(), object()),
        ]

        for term, definition in test_cases:
            with pytest.raises((ValueError, TypeError, AttributeError)):
                classifier.classify(term, definition)

    def test_batch_with_errors(self, classifier):
        """Test batch processing with some invalid items."""
        batch = [
            ("valid1", "Een geldige definitie"),
            ("", ""),  # Invalid
            ("valid2", "Nog een geldige definitie"),
            (None, None),  # Invalid
            ("valid3", "Laatste geldige definitie"),
        ]

        results = classifier.batch_classify(batch)

        # Should process all items, creating error results for invalid ones
        assert len(results) == 5

        # Valid items should have positive confidence
        assert results[0].confidence > 0
        assert results[2].confidence > 0
        assert results[4].confidence > 0

        # Invalid items should have zero confidence
        assert results[1].confidence == 0
        assert results[3].confidence == 0


class TestEdgeCasesSecondaryCategories:
    """Test secondary category identification edge cases."""

    @pytest.fixture()
    def classifier(self):
        return UFOClassifierService()

    def test_no_secondary_categories(self, classifier):
        """Test when only one category matches."""
        result = classifier.classify("gebouw", "Een onroerend goed")

        assert result.primary_category == UFOCategory.KIND
        assert len(result.secondary_categories) == 0 or all(
            s != result.primary_category for s in result.secondary_categories
        )

    def test_many_secondary_categories(self, classifier):
        """Test limiting secondary categories to 3."""
        complex_def = """
        Een persoon in de rol van verdachte tijdens het proces van arrestatie
        waarbij een bedrag van 1000 euro als borg wordt gevraagd met een
        complexiteit die de betrouwbaarheid beïnvloedt in de voorlopige fase.
        """

        result = classifier.classify("complexe zaak", complex_def)

        # Should have at most 3 secondary categories
        assert len(result.secondary_categories) <= 3

        # Primary should not be in secondary
        assert result.primary_category not in result.secondary_categories


class TestEdgeCasesDecisionPath:
    """Test decision path edge cases."""

    @pytest.fixture()
    def classifier(self):
        return UFOClassifierService()

    def test_all_steps_executed(self, classifier):
        """Verify all 9 steps are always executed."""
        test_cases = [
            ("persoon", "Een mens"),
            ("proces", "Een gebeurtenis"),
            ("verdachte", "Een rol"),
        ]

        for term, definition in test_cases:
            result = classifier.classify(term, definition)

            # Check all 9 steps are present
            step_numbers = []
            for step in result.decision_path:
                if "Stap" in step and ":" in step:
                    try:
                        num = int(step.split("Stap")[1].split(":")[0].strip())
                        step_numbers.append(num)
                    except:
                        pass

            # Should have steps 1-9
            assert set(range(1, 10)).issubset(
                set(step_numbers)
            ), f"Missing steps in decision path for {term}"


class TestEdgeCasesLexiconMemory:
    """Test lexicon memory usage edge cases."""

    def test_lexicon_size(self):
        """Test that lexicon has 500+ terms as claimed."""
        lexicon = DutchLegalLexicon()
        all_terms = lexicon.get_all_terms()

        assert len(all_terms) >= 500, f"Only {len(all_terms)} terms loaded"

    def test_lexicon_duplicates(self):
        """Test that lexicon doesn't have duplicates."""
        lexicon = DutchLegalLexicon()
        all_terms = list(lexicon.get_all_terms())

        assert len(all_terms) == len(set(all_terms)), "Lexicon contains duplicates"

    def test_lexicon_memory_efficiency(self):
        """Test lexicon memory usage is reasonable."""

        lexicon = DutchLegalLexicon()

        # Estimate memory usage (rough)
        total_size = 0
        for domain, terms in lexicon.lexicons.items():
            total_size += sys.getsizeof(domain)
            total_size += sys.getsizeof(terms)
            for term in terms:
                total_size += sys.getsizeof(term)

        # Should be under 1MB for 500+ terms
        assert total_size < 1024 * 1024, f"Lexicon uses {total_size} bytes"


# Performance benchmark suite
@pytest.mark.benchmark()
class TestPerformanceBenchmarks:
    """Performance benchmarks to ensure 500ms target."""

    @pytest.fixture()
    def classifier(self):
        return UFOClassifierService()

    def test_average_classification_time(self, classifier, benchmark):
        """Benchmark average classification time."""

        def classify():
            return classifier.classify(
                "verdachte", "Persoon die wordt verdacht van een strafbaar feit"
            )

        result = benchmark(classify)
        assert result.primary_category == UFOCategory.ROLE

    def test_worst_case_classification_time(self, classifier, benchmark):
        """Benchmark worst-case with complex input."""

        complex_def = " ".join(["verdachte eigenaar arrestatie koopovereenkomst"] * 50)

        def classify():
            return classifier.classify("complex", complex_def)

        result = benchmark(classify)
        assert result is not None


if __name__ == "__main__":
    # Run with: python -m pytest UFO_EDGE_CASE_TESTS.py -v
    pytest.main([__file__, "-v", "--tb=short"])
