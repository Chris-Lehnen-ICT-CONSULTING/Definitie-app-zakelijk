"""
Comprehensive Edge Case and Regression Test Suite for UFO Classifier
=====================================================================
This test suite ensures the UFO Classifier handles all edge cases correctly
and prevents regression of previously identified bugs.

Coverage Areas:
- Input validation (empty, whitespace, None, special chars)
- Unicode normalization (Dutch diacritics)
- Memory management (cache, leaks)
- Thread safety and concurrency
- Performance boundaries
- Error handling
"""

import gc
import queue
import re
import threading
import time
import unicodedata
from unittest.mock import MagicMock, patch

import pytest

from src.services.ufo_classifier_service import (
    UFOCategory,
    UFOClassificationResult,
    UFOClassifierService,
    create_ufo_classifier_service,
    get_ufo_classifier,
)


class TestInputValidation:
    """Test input validation and sanitization."""

    @pytest.fixture
    def classifier(self):
        return UFOClassifierService()

    def test_empty_string_validation(self, classifier):
        """Test that empty strings are properly rejected."""
        # Empty term
        with pytest.raises(ValueError, match=r"term.*niet-lege"):
            classifier.classify("", "valid definition")

        # Empty definition
        with pytest.raises(ValueError, match=r"definition.*niet-lege"):
            classifier.classify("valid term", "")

        # Both empty
        with pytest.raises(ValueError, match=r"term.*niet-lege"):
            classifier.classify("", "")

    def test_whitespace_only_validation(self, classifier):
        """Test that whitespace-only strings are rejected."""
        # Whitespace term
        with pytest.raises(ValueError, match="mag niet leeg"):
            classifier.classify("   ", "valid definition")

        with pytest.raises(ValueError, match="mag niet leeg"):
            classifier.classify("\t\n", "valid definition")

        # Whitespace definition
        with pytest.raises(ValueError, match="mag niet leeg"):
            classifier.classify("valid term", "   ")

        with pytest.raises(ValueError, match="mag niet leeg"):
            classifier.classify("valid term", "\r\n\t")

    def test_none_input_handling(self, classifier):
        """Test None input handling."""
        with pytest.raises(ValueError, match="niet-lege string"):
            classifier.classify(None, "definition")

        with pytest.raises(ValueError, match="niet-lege string"):
            classifier.classify("term", None)

        with pytest.raises(ValueError, match="niet-lege string"):
            classifier.classify(None, None)

    def test_non_string_input(self, classifier):
        """Test non-string input handling."""
        # Numbers
        with pytest.raises(ValueError, match="string"):
            classifier.classify(123, "definition")

        with pytest.raises(ValueError, match="string"):
            classifier.classify("term", 456)

        # Lists
        with pytest.raises(ValueError, match="string"):
            classifier.classify(["term"], "definition")

        # Dicts
        with pytest.raises(ValueError, match="string"):
            classifier.classify({"term": "value"}, "definition")

    def test_extremely_long_input(self, classifier):
        """Test handling of very long inputs."""
        # Test truncation at 5000 chars
        long_term = "x" * 6000
        long_def = "y" * 6000

        result = classifier.classify(long_term, long_def)
        assert result is not None
        assert len(result.term) <= 5000
        assert len(result.definition) <= 5000

    def test_special_characters(self, classifier):
        """Test handling of special characters."""
        test_cases = [
            ("test()", "definitie met haakjes()"),
            ("test[brackets]", "definitie met [brackets]"),
            ("test{braces}", "definitie met {braces}"),
            ("€100", "bedrag van 100 euro"),
            ("50%", "percentage van vijftig"),
            ("test@email.com", "e-mail adres"),
            ("test/slash", "definitie met/slash"),
            ("test\\backslash", "definitie met\\backslash"),
            ("test'quote", "definitie met 'quotes'"),
            ('test"doublequote', 'definitie met "quotes"'),
        ]

        for term, definition in test_cases:
            result = classifier.classify(term, definition)
            assert result is not None
            assert result.primary_category in UFOCategory
            assert 0 <= result.confidence <= 1

    def test_sql_injection_attempts(self, classifier):
        """Test SQL injection protection."""
        dangerous_inputs = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin'--",
            "1; DELETE FROM definitions WHERE 1=1",
            "UNION SELECT * FROM users",
        ]

        for dangerous in dangerous_inputs:
            # Should handle safely without executing
            result = classifier.classify(dangerous, "safe definition")
            assert result is not None

            result = classifier.classify("safe term", dangerous)
            assert result is not None

    def test_command_injection_attempts(self, classifier):
        """Test command injection protection."""
        dangerous_inputs = [
            "$(rm -rf /)",
            "`cat /etc/passwd`",
            "| ls -la",
            "; shutdown -h now",
            "&& echo hacked",
        ]

        for dangerous in dangerous_inputs:
            result = classifier.classify(dangerous, "safe definition")
            assert result is not None
            assert result.primary_category in UFOCategory

    def test_path_traversal_attempts(self, classifier):
        """Test path traversal protection."""
        dangerous_inputs = [
            "../../etc/passwd",
            "../../../windows/system32",
            "..\\..\\..\\windows\\system32",
            "/etc/passwd",
            "C:\\Windows\\System32",
        ]

        for dangerous in dangerous_inputs:
            result = classifier.classify(dangerous, "safe definition")
            assert result is not None

class TestUnicodeHandling:
    """Test Unicode normalization and Dutch diacritics."""

    @pytest.fixture
    def classifier(self):
        return UFOClassifierService()

    def test_dutch_diacritics_normalization(self, classifier):
        """Test normalization of Dutch diacritics."""
        # Test composed vs decomposed forms
        test_pairs = [
            ("café", "cafe\u0301"),  # é vs e+combining acute
            ("coöperatie", "coo\u0308peratie"),  # ö vs o+combining diaeresis
            ("geïnformeerd", "gei\u0308nformeerd"),  # ï vs i+combining diaeresis
            ("reünie", "reu\u0308nie"),  # ü vs u+combining diaeresis
        ]

        for composed, decomposed in test_pairs:
            result1 = classifier.classify(composed, "een definitie")
            result2 = classifier.classify(decomposed, "een definitie")

            # Both should normalize to same form
            assert result1.term == result2.term

    def test_unicode_edge_cases(self, classifier):
        """Test various Unicode edge cases."""
        test_cases = [
            ("test\u200b", "zero-width space"),  # Zero-width space
            ("test\ufeff", "BOM character"),  # Byte order mark
            ("test\u00a0", "non-breaking space"),  # Non-breaking space
            ("🏛️", "emoji rechtbank"),  # Emoji
            ("test™", "trademark symbol"),  # Special symbols
            ("Α", "Greek alpha"),  # Non-Latin scripts
            ("א", "Hebrew aleph"),  # Right-to-left script
            ("中", "Chinese character"),  # Ideographic script
        ]

        for term, definition in test_cases:
            result = classifier.classify(term, definition)
            assert result is not None

    def test_unicode_normalization_forms(self, classifier):
        """Test different Unicode normalization forms."""
        test_text = "café coöperatie"

        # Different normalization forms
        nfc = unicodedata.normalize("NFC", test_text)
        nfd = unicodedata.normalize("NFD", test_text)
        nfkc = unicodedata.normalize("NFKC", test_text)
        nfkd = unicodedata.normalize("NFKD", test_text)

        results = []
        for form in [nfc, nfd, nfkc, nfkd]:
            result = classifier.classify(form, "een definitie")
            results.append(result)

        # All should produce consistent classification
        categories = [r.primary_category for r in results]
        assert (
            len(set(categories)) == 1
        ), "Inconsistent classification across Unicode forms"

class TestPerformanceAndMemory:
    """Test performance boundaries and memory management."""

    @pytest.fixture
    def classifier(self):
        return UFOClassifierService()

    def test_classification_performance(self, classifier):
        """Test that classification meets performance targets."""
        test_cases = [
            ("rechtspersoon", "Een juridische entiteit"),
            ("overeenkomst", "Contract tussen partijen"),
            ("verdachte", "Persoon in de hoedanigheid van verdachte"),
        ]

        times = []
        for term, definition in test_cases * 10:  # Run multiple times
            start = time.perf_counter()
            result = classifier.classify(term, definition)
            elapsed = (time.perf_counter() - start) * 1000  # ms

            times.append(elapsed)
            assert (
                result.classification_time_ms < 500
            ), f"Classification too slow: {elapsed}ms"

        avg_time = sum(times) / len(times)
        assert avg_time < 100, f"Average time {avg_time}ms exceeds target"

    def test_batch_processing_memory(self, classifier):
        """Test memory usage in batch processing."""
        # Generate large batch
        definitions = [(f"term_{i}", f"definition_{i}") for i in range(1000)]

        # Measure initial memory
        gc.collect()
        initial_objects = len(gc.get_objects())

        # Process batch
        results = classifier.batch_classify(definitions)

        # Force garbage collection
        gc.collect()
        final_objects = len(gc.get_objects())

        # Check results
        assert len(results) == len(definitions)

        # Memory should not grow unbounded
        growth = final_objects - initial_objects
        assert growth < 5000, f"Memory growth {growth} objects exceeds threshold"

    def test_memory_leak_prevention(self, classifier):
        """Test that repeated classifications don't leak memory."""
        gc.collect()
        initial = len(gc.get_objects())

        # Many classifications
        for i in range(500):
            classifier.classify(f"term_{i}", f"definition_{i}")

            # Periodic GC
            if i % 100 == 0:
                gc.collect()

        gc.collect()
        final = len(gc.get_objects())

        growth_rate = (final - initial) / 500
        assert (
            growth_rate < 10
        ), f"Memory growing at {growth_rate} objects per classification"

class TestConcurrency:
    """Test thread safety and concurrent operations."""

    @pytest.fixture
    def classifier(self):
        return UFOClassifierService()

    def test_concurrent_classifications(self, classifier):
        """Test thread safety of classifier."""
        results = queue.Queue()
        errors = queue.Queue()

        def worker(worker_id, num_classifications):
            for i in range(num_classifications):
                try:
                    result = classifier.classify(
                        f"term_{worker_id}_{i}",
                        f"definition for worker {worker_id} item {i}",
                    )
                    results.put((worker_id, result))
                except Exception as e:
                    errors.put((worker_id, str(e)))

        # Launch threads
        threads = []
        num_workers = 10
        classifications_per_worker = 20

        for i in range(num_workers):
            t = threading.Thread(target=worker, args=(i, classifications_per_worker))
            threads.append(t)
            t.start()

        # Wait for completion
        for t in threads:
            t.join(timeout=10)

        # Check results
        assert errors.empty(), f"Errors in concurrent execution: {list(errors.queue)}"
        assert results.qsize() == num_workers * classifications_per_worker

        # Verify results are valid
        while not results.empty():
            worker_id, result = results.get()
            assert isinstance(result, UFOClassificationResult)
            assert result.primary_category in UFOCategory
            assert 0 <= result.confidence <= 1

    def test_singleton_thread_safety(self):
        """Test thread-safe singleton pattern."""
        instances = queue.Queue()

        def get_instance():
            instance = get_ufo_classifier()
            instances.put(id(instance))

        threads = []
        for _ in range(20):
            t = threading.Thread(target=get_instance)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # All instances should be the same
        instance_ids = list(instances.queue)
        assert len(set(instance_ids)) == 1, "Multiple instances created"

class TestErrorHandling:
    """Test error handling and recovery."""

    @pytest.fixture
    def classifier(self):
        return UFOClassifierService()

    def test_pattern_compilation_errors(self):
        """Test handling of invalid regex patterns."""
        # Mock invalid patterns
        with patch.object(
            UFOClassifierService,
            "PATTERNS",
            {UFOCategory.KIND: [r"[invalid(regex"]},  # Invalid regex
        ):
            # Should handle compilation error gracefully
            classifier = UFOClassifierService()
            result = classifier.classify("test", "definition")
            assert result is not None

    def test_batch_error_recovery(self, classifier):
        """Test batch processing continues after errors."""
        definitions = [
            ("valid1", "definition 1"),
            ("", ""),  # Will cause error
            ("valid2", "definition 2"),
            (None, None),  # Will cause error
            ("valid3", "definition 3"),
        ]

        results = classifier.batch_classify(definitions)

        # Should get results for all items
        assert len(results) == 5

        # Check valid results
        assert results[0].confidence > 0
        assert results[2].confidence > 0
        assert results[4].confidence > 0

        # Check error results
        assert results[1].confidence == 0
        assert "Error" in results[1].explanation
        assert results[3].confidence == 0
        assert "Error" in results[3].explanation

    def test_config_loading_errors(self):
        """Test handling of config loading errors."""
        from pathlib import Path

        # Non-existent config
        classifier = UFOClassifierService(Path("/nonexistent/config.yaml"))
        assert classifier is not None
        assert classifier.config is not None  # Should use defaults

        # Invalid YAML
        with patch("builtins.open", MagicMock(side_effect=OSError("File error"))):
            classifier = UFOClassifierService(Path("dummy.yaml"))
            assert classifier.config is not None  # Should use defaults

class TestCategoryClassification:
    """Test correct classification of each UFO category."""

    @pytest.fixture
    def classifier(self):
        return UFOClassifierService()

    def test_kind_classification(self, classifier):
        """Test KIND category classification."""
        test_cases = [
            ("persoon", "Een natuurlijk persoon is een mens"),
            ("organisatie", "Een bedrijf of instelling"),
            ("document", "Een schriftelijk stuk"),
            ("gebouw", "Een onroerend goed"),
        ]

        for term, definition in test_cases:
            result = classifier.classify(term, definition)
            assert result.primary_category == UFOCategory.KIND

    def test_event_classification(self, classifier):
        """Test EVENT category classification."""
        test_cases = [
            ("procedure", "Een proces dat wordt uitgevoerd"),
            ("zitting", "Een gebeurtenis tijdens de rechtszaak"),
            ("arrestatie", "Het aanhouden van een verdachte"),
        ]

        for term, definition in test_cases:
            result = classifier.classify(term, definition)
            assert result.primary_category == UFOCategory.EVENT

    def test_role_classification(self, classifier):
        """Test ROLE category classification."""
        test_cases = [
            ("verdachte", "Persoon in de hoedanigheid van verdachte"),
            ("eigenaar", "Iemand die eigendom heeft"),
            ("koper", "Partij die als koper optreedt"),
        ]

        for term, definition in test_cases:
            result = classifier.classify(term, definition)
            assert result.primary_category == UFOCategory.ROLE

    def test_relator_classification(self, classifier):
        """Test RELATOR category classification."""
        test_cases = [
            ("overeenkomst", "Contract tussen twee partijen"),
            ("huwelijk", "Verbintenis tussen twee personen"),
            ("vergunning", "Toestemming verleend aan houder"),
        ]

        for term, definition in test_cases:
            result = classifier.classify(term, definition)
            assert result.primary_category == UFOCategory.RELATOR

    def test_quantity_classification(self, classifier):
        """Test QUANTITY category classification."""
        test_cases = [
            ("bedrag", "Een som van 1000 euro"),
            ("percentage", "Het deel uitgedrukt in procenten"),
            ("koopsom", "Het bedrag van €250.000"),
        ]

        for term, definition in test_cases:
            result = classifier.classify(term, definition)
            assert result.primary_category == UFOCategory.QUANTITY

class TestDisambiguation:
    """Test disambiguation of ambiguous terms."""

    @pytest.fixture
    def classifier(self):
        return UFOClassifierService()

    def test_zaak_disambiguation(self, classifier):
        """Test disambiguation of 'zaak'."""
        # As legal case (EVENT)
        result = classifier.classify("rechtszaak", "Een rechtszaak voor de rechter")
        assert result.primary_category == UFOCategory.EVENT

        # As object (KIND)
        result = classifier.classify("zaak", "Een roerende zaak zoals een auto")
        assert result.primary_category == UFOCategory.KIND

    def test_huwelijk_disambiguation(self, classifier):
        """Test disambiguation of 'huwelijk'."""
        # As ceremony (EVENT)
        result = classifier.classify(
            "huwelijksvoltrekking", "Het sluiten van een huwelijk"
        )
        assert result.primary_category == UFOCategory.EVENT

        # As relationship (RELATOR)
        result = classifier.classify("huwelijk", "De band tussen twee gehuwde personen")
        assert result.primary_category == UFOCategory.RELATOR

    def test_procedure_disambiguation(self, classifier):
        """Test disambiguation of 'procedure'."""
        # As process (EVENT)
        result = classifier.classify(
            "bezwaarprocedure", "De procedure start met indienen bezwaar"
        )
        assert result.primary_category == UFOCategory.EVENT

        # As document (KIND)
        result = classifier.classify("procedure", "Het document volgens de procedure")
        assert result.primary_category == UFOCategory.KIND

class TestIntegration:
    """Integration tests with ServiceContainer."""

    def test_factory_function(self):
        """Test factory function for ServiceContainer."""
        service = create_ufo_classifier_service()
        assert isinstance(service, UFOClassifierService)

        result = service.classify("test", "een test definitie")
        assert isinstance(result, UFOClassificationResult)

    def test_singleton_persistence(self):
        """Test singleton persists across calls."""
        instance1 = get_ufo_classifier()
        instance2 = get_ufo_classifier()

        assert instance1 is instance2

        # Test persistence of state
        result1 = instance1.classify("test", "definition")
        result2 = instance2.classify("test", "definition")

        assert result1.primary_category == result2.primary_category

class TestRegressionPrevention:
    """Tests to prevent regression of previously fixed bugs."""

    @pytest.fixture
    def classifier(self):
        return UFOClassifierService()

    def test_no_division_by_zero(self, classifier):
        """Test that division by zero is prevented."""
        # Create scenario with no matches
        with patch.object(classifier, "_calculate_pattern_scores", return_value={}):
            result = classifier.classify("test", "definition")
            assert result is not None
            assert result.confidence >= 0
            assert result.confidence <= 1

    def test_confidence_boundaries(self, classifier):
        """Test confidence stays within 0-1 bounds."""
        test_cases = [
            ("", ""),  # Edge case
            ("x", "y"),  # Minimal
            (
                "rechtspersoon",
                "Een rechtspersoon is een juridische entiteit",
            ),  # Clear match
            ("ambiguous", "Could be many things"),  # Ambiguous
        ]

        for term, definition in test_cases:
            try:
                result = classifier.classify(term, definition)
                assert (
                    0 <= result.confidence <= 1
                ), f"Confidence {result.confidence} out of bounds for {term}"
            except ValueError:
                pass  # Expected for empty inputs

    def test_abstract_category_removed(self, classifier):
        """Test that ABSTRACT category is no longer in enum."""
        # Check enum doesn't have ABSTRACT
        categories = list(UFOCategory)
        category_names = [c.name for c in categories]

        assert "ABSTRACT" not in category_names, "ABSTRACT should not be in enum"

    def test_pattern_compilation_cached(self, classifier):
        """Test patterns are compiled once, not per classification."""
        # Patterns should already be compiled
        assert hasattr(classifier, "compiled_patterns")
        assert len(classifier.compiled_patterns) > 0

        # Check they're compiled regex objects
        for _category, patterns in classifier.compiled_patterns.items():
            assert isinstance(patterns, list)
            for pattern in patterns:
                assert isinstance(pattern, re.Pattern)

if __name__ == "__main__":
    # Run tests with coverage
    pytest.main([__file__, "-v", "--cov=src.services.ufo_classifier_service"])
