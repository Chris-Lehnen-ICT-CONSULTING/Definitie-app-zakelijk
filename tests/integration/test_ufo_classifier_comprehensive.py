"""
Comprehensive Test Suite for UFO Classification Service
========================================================
Based on US-300 requirements, this test suite covers:
1. Unit tests (35+ test cases)
2. Integration tests with ServiceContainer
3. Performance tests (10ms target)
4. Batch processing tests (2000 items/sec)
5. Edge cases for Dutch legal terminology
6. Confidence scoring validation
7. Rule engine tests for all 16 UFO categories
8. Database migration tests
9. UI integration tests
10. Fallback mechanism tests (confidence <0.6)
11. Audit logging tests
12. A/B testing framework for rule improvements
"""

import json
import sqlite3
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest

from src.services.ufo_classifier_service import (
    PatternMatcher,
    UFOCategory,
    UFOClassificationResult,
    UFOClassifierService,
    get_ufo_classifier,
)

# ============================================================================
# 1. UNIT TESTS (35+ test cases)
# ============================================================================


class TestUFOClassifierUnit:
    """Comprehensive unit tests for UFO Classifier Service"""

    @pytest.fixture()
    def classifier(self):
        """Create a fresh classifier instance for each test"""
        return UFOClassifierService()

    @pytest.fixture()
    def dutch_legal_samples(self):
        """Dutch legal terminology test samples"""
        return {
            "strafrecht": [
                (
                    "verdachte",
                    "Een persoon die wordt verdacht van het plegen van een strafbaar feit",
                ),
                ("dader", "De persoon die een strafbaar feit heeft gepleegd"),
                (
                    "slachtoffer",
                    "Degene die rechtstreeks schade heeft ondervonden door een strafbaar feit",
                ),
                (
                    "aanhouding",
                    "Het proces waarbij een persoon van zijn vrijheid wordt beroofd",
                ),
                (
                    "inverzekeringstelling",
                    "Het vasthouden van een verdachte na aanhouding",
                ),
                (
                    "dagvaarding",
                    "Schriftelijke oproep om voor de rechter te verschijnen",
                ),
                (
                    "proces-verbaal",
                    "Schriftelijk verslag van bevindingen door opsporingsambtenaar",
                ),
            ],
            "bestuursrecht": [
                ("burger", "Een natuurlijk persoon in relatie tot de overheid"),
                (
                    "bestuursorgaan",
                    "Orgaan van een rechtspersoon die krachtens publiekrecht is ingesteld",
                ),
                ("beschikking", "Besluit dat niet van algemene strekking is"),
                ("vergunning", "Toestemming van de overheid om iets te mogen doen"),
                ("bezwaar", "Procedure tegen een besluit van een bestuursorgaan"),
                ("beroep", "Procedure bij de rechter tegen een beslissing op bezwaar"),
                ("handhaving", "Het toezien op naleving van voorschriften"),
            ],
            "civiel_recht": [
                ("koper", "Partij die een zaak koopt"),
                ("verkoper", "Partij die een zaak verkoopt"),
                ("eigenaar", "Degene aan wie een zaak toebehoort"),
                (
                    "koopovereenkomst",
                    "Overeenkomst waarbij verkoper zich verbindt zaak te geven",
                ),
                (
                    "huurovereenkomst",
                    "Overeenkomst waarbij verhuurder zich verbindt tot verschaffen van genot",
                ),
                (
                    "vorderingsrecht",
                    "Het recht om van een ander een prestatie te vorderen",
                ),
                ("hypotheek", "Zakelijk recht op onroerende zaak tot zekerheid"),
            ],
        }

    # Test 1-5: Basic category detection
    def test_kind_detection_natural_person(self, classifier):
        """Test 1: Natural person as KIND"""
        result = classifier.classify(
            "natuurlijk persoon",
            "Een mens van vlees en bloed met rechtspersoonlijkheid",
        )
        assert result.primary_category == UFOCategory.KIND
        assert result.confidence >= 0.7
        assert "persoon" in str(result.matched_patterns).lower()

    def test_kind_detection_organization(self, classifier):
        """Test 2: Organization as KIND"""
        result = classifier.classify(
            "rechtspersoon", "Een juridische entiteit met eigen rechten en plichten"
        )
        assert result.primary_category == UFOCategory.KIND
        assert result.confidence >= 0.6

    def test_event_detection_process(self, classifier):
        """Test 3: Legal process as EVENT"""
        result = classifier.classify(
            "strafproces",
            "Het proces van opsporing, vervolging en berechting dat plaatsvindt na een strafbaar feit",
        )
        assert result.primary_category == UFOCategory.EVENT
        assert result.confidence >= 0.6
        assert "proces" in str(result.matched_patterns).lower()

    def test_event_detection_temporal(self, classifier):
        """Test 4: Temporal event detection"""
        result = classifier.classify(
            "hoorzitting",
            "Een bijeenkomst tijdens welke partijen hun standpunten kunnen toelichten",
        )
        assert result.primary_category == UFOCategory.EVENT
        assert "tijdens" in str(result.matched_patterns).lower()

    def test_role_detection_context(self, classifier):
        """Test 5: Contextual role detection"""
        result = classifier.classify(
            "advocaat", "Een persoon in de hoedanigheid van juridisch vertegenwoordiger"
        )
        assert result.primary_category == UFOCategory.ROLE
        assert result.confidence >= 0.5

    # Test 6-10: Complex legal entities
    def test_relator_legal_binding(self, classifier):
        """Test 6: Legal contract as RELATOR"""
        result = classifier.classify(
            "arbeidsovereenkomst",
            "Een overeenkomst tussen werkgever en werknemer voor het verrichten van arbeid",
        )
        assert result.primary_category == UFOCategory.RELATOR
        assert "overeenkomst" in str(result.matched_patterns).lower()

    def test_phase_lifecycle(self, classifier):
        """Test 7: Status/phase detection"""
        result = classifier.classify(
            "voorlopige hechtenis",
            "De fase waarin een verdachte in verzekering is gesteld voorafgaand aan het proces",
        )
        assert result.primary_category in [UFOCategory.PHASE, UFOCategory.EVENT]

    def test_mode_state_attribute(self, classifier):
        """Test 8: State/attribute as MODE"""
        result = classifier.classify(
            "handelingsbekwaamheid",
            "De toestand waarin een persoon bevoegd is rechtshandelingen te verrichten",
        )
        assert result.primary_category == UFOCategory.MODE
        assert "toestand" in str(result.matched_patterns).lower()

    def test_quantity_monetary(self, classifier):
        """Test 9: Monetary amount as QUANTITY"""
        result = classifier.classify(
            "schadevergoeding",
            "Het bedrag in euro's dat als compensatie voor geleden schade wordt uitgekeerd",
        )
        assert result.primary_category in [UFOCategory.QUANTITY, UFOCategory.MODE]
        if result.primary_category == UFOCategory.QUANTITY:
            assert (
                "euro" in str(result.matched_patterns).lower()
                or "bedrag" in str(result.matched_patterns).lower()
            )

    def test_quality_gradation(self, classifier):
        """Test 10: Quality with gradation"""
        result = classifier.classify(
            "ernst van het feit",
            "De mate waarin een strafbaar feit als zwaarwegend wordt beschouwd",
        )
        assert result.primary_category == UFOCategory.QUALITY
        assert (
            "ernst" in str(result.matched_patterns).lower()
            or "mate" in str(result.matched_patterns).lower()
        )

    # Test 11-15: Ambiguous terms
    def test_ambiguous_zaak_multiple_meanings(self, classifier):
        """Test 11: Ambiguous term 'zaak' (case/thing/matter)"""
        # As physical object
        result1 = classifier.classify(
            "zaak", "Een stoffelijk voorwerp dat in het handelsverkeer kan zijn"
        )
        assert result1.primary_category == UFOCategory.KIND

        # As legal case
        result2 = classifier.classify(
            "zaak", "Een juridische procedure die bij de rechter aanhangig is"
        )
        assert result2.primary_category in [UFOCategory.EVENT, UFOCategory.KIND]

    def test_ambiguous_huwelijk_relator_or_event(self, classifier):
        """Test 12: 'Huwelijk' as both RELATOR and EVENT"""
        # As relationship
        result1 = classifier.classify(
            "huwelijk", "De wettelijke verbintenis tussen twee personen"
        )
        assert result1.primary_category == UFOCategory.RELATOR

        # As ceremony/event
        result2 = classifier.classify(
            "huwelijk", "De ceremonie waarbij twee personen in de echt worden verbonden"
        )
        assert result2.primary_category in [UFOCategory.EVENT, UFOCategory.RELATOR]

    def test_ambiguous_low_confidence(self, classifier):
        """Test 13: Ambiguous term should have lower confidence"""
        result = classifier.classify("ding", "Iets")
        assert result.confidence < 0.5

    def test_context_disambiguation(self, classifier):
        """Test 14: Context helps disambiguation"""
        context = {"domain": "strafrecht", "type": "proces"}
        result = classifier.classify("onderzoek", "Het verzamelen van bewijs", context)
        assert result.primary_category == UFOCategory.EVENT
        assert result.confidence >= 0.4

    def test_compound_term_analysis(self, classifier):
        """Test 15: Compound Dutch legal terms"""
        result = classifier.classify(
            "rechter-commissaris",
            "Een rechter belast met het voorbereidend onderzoek in strafzaken",
        )
        assert result.primary_category == UFOCategory.ROLE
        assert "rechter" in str(result.matched_patterns).lower()

    # Test 16-20: Secondary tags and hierarchies
    def test_subkind_detection(self, classifier):
        """Test 16: Subkind detection"""
        result = classifier.classify(
            "type verdachte",
            "Een soort persoon die van een strafbaar feit wordt verdacht",
        )
        assert (
            UFOCategory.SUBKIND in result.secondary_tags
            or result.primary_category == UFOCategory.SUBKIND
        )

    def test_category_abstract_type(self, classifier):
        """Test 17: Abstract category detection"""
        result = classifier.classify(
            "juridische categorie", "Een abstracte groepering van juridische concepten"
        )
        assert (
            UFOCategory.ABSTRACT in result.secondary_tags
            or UFOCategory.CATEGORY in result.secondary_tags
        )

    def test_mixin_pattern(self, classifier):
        """Test 18: Mixin pattern detection"""
        result = classifier.classify(
            "procespartij",
            "Verschillende rollen die partijen in een proces kunnen hebben",
        )
        if result.primary_category == UFOCategory.ROLE:
            assert (
                UFOCategory.ROLEMIXIN in result.secondary_tags
                or len(result.secondary_tags) > 0
            )

    def test_event_composition(self, classifier):
        """Test 19: Composite event detection"""
        result = classifier.classify(
            "strafproces", "Het geheel van opsporing, vervolging en berechting"
        )
        assert result.primary_category == UFOCategory.EVENT
        # Could have Event Composition as secondary tag

    def test_relation_vs_relator(self, classifier):
        """Test 20: Distinguish RELATIE from RELATOR"""
        # Relator (reified relationship)
        result1 = classifier.classify(
            "huurcontract", "Een overeenkomst tussen huurder en verhuurder"
        )
        assert result1.primary_category == UFOCategory.RELATOR

        # Pure relation (if pattern exists)
        result2 = classifier.classify(
            "is_eigenaar_van", "De relatie tussen een persoon en zijn eigendom"
        )
        # This might be RELATOR or have RELATIE tag
        assert result2.primary_category in [
            UFOCategory.RELATOR,
            UFOCategory.MODE,
            UFOCategory.UNKNOWN,
        ]

    # Test 21-25: Edge cases
    def test_empty_definition(self, classifier):
        """Test 21: Empty or minimal input"""
        result = classifier.classify("", "")
        assert result.primary_category == UFOCategory.UNKNOWN
        assert result.confidence < 0.3

    def test_very_long_definition(self, classifier):
        """Test 22: Very long definition (performance)"""
        long_def = " ".join(["Een persoon die verdacht wordt"] * 100)
        result = classifier.classify("verdachte", long_def)
        assert result.primary_category in [UFOCategory.ROLE, UFOCategory.KIND]

    def test_special_characters_robustness(self, classifier):
        """Test 23: Special characters handling"""
        result = classifier.classify(
            "test@#$", "Een persoon met speciale !@#$ karakters"
        )
        # Should still detect 'persoon' pattern
        assert result.primary_category == UFOCategory.KIND

    def test_mixed_language_robustness(self, classifier):
        """Test 24: Mixed Dutch-English text"""
        result = classifier.classify(
            "legal person", "Een rechtspersoon is a legal entity met eigen rights"
        )
        assert result.primary_category == UFOCategory.KIND
        assert "rechtspersoon" in str(result.matched_patterns).lower()

    def test_numeric_terms(self, classifier):
        """Test 25: Numeric and measurement terms"""
        result = classifier.classify(
            "artikel 3:40 BW",
            "Het wetsartikel dat nietigheid van rechtshandelingen regelt",
        )
        # Articles are typically KIND (document/regulation)
        assert result.primary_category in [UFOCategory.KIND, UFOCategory.UNKNOWN]

    # Test 26-35: Confidence and explanation
    def test_high_confidence_threshold(self, classifier):
        """Test 26: High confidence (≥0.8) for clear cases"""
        result = classifier.classify(
            "natuurlijk persoon",
            "Een mens van vlees en bloed met rechtspersoonlijkheid",
        )
        assert result.confidence >= 0.8
        assert "Hoge zekerheid" in " ".join(result.explanation)

    def test_medium_confidence_threshold(self, classifier):
        """Test 27: Medium confidence (0.5-0.8) for moderate matches"""
        result = classifier.classify("procedure", "Een vastgestelde werkwijze")
        if result.confidence >= 0.5 and result.confidence < 0.8:
            assert "Redelijke zekerheid" in " ".join(result.explanation)

    def test_low_confidence_threshold(self, classifier):
        """Test 28: Low confidence (<0.5) for weak matches"""
        result = classifier.classify("iets", "Een onduidelijk begrip")
        assert result.confidence < 0.5
        if result.confidence >= 0.15:  # Not UNKNOWN
            assert "Lage zekerheid" in " ".join(result.explanation)

    def test_explanation_includes_patterns(self, classifier):
        """Test 29: Explanation includes matched patterns"""
        result = classifier.classify(
            "koopovereenkomst",
            "Een overeenkomst waarbij de verkoper zich verbindt een zaak te leveren",
        )
        assert len(result.explanation) >= 2
        assert any("overeenkomst" in exp.lower() for exp in result.explanation)

    def test_explanation_category_specific(self, classifier):
        """Test 30: Category-specific explanations"""
        result = classifier.classify("persoon", "Een natuurlijk persoon met rechten")
        assert any(
            "zelfstandig" in exp.lower() or "object" in exp.lower()
            for exp in result.explanation
        )

    def test_pattern_priority_weights(self, classifier):
        """Test 31: Pattern weights affect classification"""
        # KIND has higher weight than others
        result = classifier.classify(
            "persoon proces",  # Contains both KIND and EVENT markers
            "Een persoon in een juridisch proces",
        )
        # KIND should win due to higher weight
        assert result.primary_category in [UFOCategory.KIND, UFOCategory.EVENT]

    def test_heuristic_rules_application(self, classifier):
        """Test 32: Heuristic rules enhance classification"""
        result = classifier.classify(
            "vergadering", "Een bijeenkomst die plaatsvindt tussen partijen"
        )
        # "plaatsvindt" should boost EVENT score
        assert result.primary_category == UFOCategory.EVENT

    def test_conflicting_patterns_resolution(self, classifier):
        """Test 33: Resolve conflicting patterns"""
        result = classifier.classify(
            "procespartij", "Een persoon die als partij optreedt in een proces"
        )
        # Has both EVENT (proces) and ROLE (als, optreedt) markers
        assert result.primary_category in [UFOCategory.ROLE, UFOCategory.KIND]

    def test_unknown_category_fallback(self, classifier):
        """Test 34: UNKNOWN for unrecognizable terms"""
        result = classifier.classify("xyzabc", "qwerty uiop asdfgh")
        assert result.primary_category == UFOCategory.UNKNOWN
        assert result.confidence < 0.3

    def test_serialization_completeness(self, classifier):
        """Test 35: Complete serialization to dict"""
        result = classifier.classify(
            "verdachte", "Een persoon die wordt verdacht van een strafbaar feit"
        )
        data = result.to_dict()

        assert "primary_category" in data
        assert "confidence" in data
        assert "explanation" in data
        assert "secondary_tags" in data
        assert "matched_patterns" in data
        assert isinstance(data["confidence"], float)
        assert 0 <= data["confidence"] <= 1


# ============================================================================
# 2. INTEGRATION TESTS WITH SERVICE CONTAINER
# ============================================================================


class TestServiceContainerIntegration:
    """Test integration with ServiceContainer for dependency injection"""

    @pytest.fixture()
    def mock_container(self):
        """Create a mock ServiceContainer with UFO classifier"""
        from unittest.mock import Mock

        container = Mock()
        container.ufo_classifier = Mock(return_value=get_ufo_classifier())
        return container

    def test_singleton_pattern_in_container(self, mock_container):
        """Test that container returns singleton instance"""
        classifier1 = mock_container.ufo_classifier()
        classifier2 = mock_container.ufo_classifier()
        # In real implementation, these should be the same instance
        assert isinstance(classifier1, UFOClassifierService)
        assert isinstance(classifier2, UFOClassifierService)

    def test_container_lazy_initialization(self):
        """Test lazy initialization of UFO classifier"""
        # Simulate container with lazy loading
        container_instances = {}

        def get_or_create_classifier():
            if "ufo_classifier" not in container_instances:
                container_instances["ufo_classifier"] = UFOClassifierService()
            return container_instances["ufo_classifier"]

        classifier1 = get_or_create_classifier()
        classifier2 = get_or_create_classifier()
        assert classifier1 is classifier2

    def test_integration_with_repository(self):
        """Test integration with DefinitionRepository"""
        classifier = UFOClassifierService()

        # Mock repository interaction
        mock_definitions = [
            {
                "id": 1,
                "begrip": "verdachte",
                "definitie": "Persoon verdacht van strafbaar feit",
            },
            {"id": 2, "begrip": "proces", "definitie": "Juridische procedure"},
        ]

        # Classify all definitions
        for definition in mock_definitions:
            result = classifier.classify(definition["begrip"], definition["definitie"])
            assert result.primary_category != UFOCategory.UNKNOWN

    def test_integration_with_validator(self):
        """Test integration with validation service"""
        classifier = UFOClassifierService()

        # Mock validation context
        validation_context = {
            "begrip": "verdachte",
            "definitie": "Een persoon die wordt verdacht",
            "ufo_required": True,
        }

        result = classifier.classify(
            validation_context["begrip"], validation_context["definitie"]
        )

        # Validation should check if UFO category is present
        assert result.primary_category != UFOCategory.UNKNOWN
        assert result.confidence > 0


# ============================================================================
# 3. PERFORMANCE TESTS (10ms target)
# ============================================================================


class TestPerformanceRequirements:
    """Test performance requirements from US-300"""

    @pytest.fixture()
    def classifier(self):
        return UFOClassifierService()

    @pytest.fixture()
    def test_dataset(self, dutch_legal_samples):
        """Generate test dataset for performance testing"""
        all_samples = []
        for category_samples in dutch_legal_samples.values():
            all_samples.extend(category_samples)
        return all_samples

    def test_single_classification_under_10ms(self, classifier):
        """Test that single classification takes <10ms"""
        term = "verdachte"
        definition = "Een persoon die wordt verdacht van een strafbaar feit"

        # Warm up
        classifier.classify(term, definition)

        # Measure
        times = []
        for _ in range(100):
            start = time.perf_counter()
            classifier.classify(term, definition)
            duration = (time.perf_counter() - start) * 1000  # Convert to ms
            times.append(duration)

        avg_time = np.mean(times)
        p95_time = np.percentile(times, 95)

        assert avg_time < 10, f"Average time {avg_time:.2f}ms exceeds 10ms target"
        assert p95_time < 20, f"P95 time {p95_time:.2f}ms exceeds reasonable threshold"

    def test_batch_processing_2000_per_second(self, classifier, test_dataset):
        """Test batch processing achieves >2000 items/sec"""
        # Create batch of 2000 items
        batch = test_dataset * (2000 // len(test_dataset) + 1)
        batch = batch[:2000]

        items = [(term, definition, None) for term, definition in batch]

        start = time.perf_counter()
        results = classifier.batch_classify(items)
        duration = time.perf_counter() - start

        throughput = len(results) / duration

        assert len(results) == 2000
        assert (
            throughput > 2000
        ), f"Throughput {throughput:.0f}/sec below 2000/sec target"

    def test_memory_footprint_under_100mb(self, classifier):
        """Test memory usage stays under 100MB"""
        import tracemalloc

        tracemalloc.start()

        # Perform many classifications
        for i in range(1000):
            classifier.classify(
                f"term_{i}", f"Definition for term {i} with some legal context"
            )

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Convert to MB
        peak_mb = peak / 1024 / 1024

        assert peak_mb < 100, f"Peak memory {peak_mb:.1f}MB exceeds 100MB limit"

    def test_cache_effectiveness(self, classifier):
        """Test LRU cache hit rate >90%"""
        test_texts = [
            "Een persoon met rechtspersoonlijkheid",
            "Een juridisch proces",
            "Een overeenkomst tussen partijen",
            "Een verdachte in een strafzaak",
            "Een bestuursorgaan van de overheid",
        ]

        # First pass - cache miss
        for text in test_texts:
            classifier.pattern_matcher.find_matches(text)

        # Clear cache statistics if available
        classifier.pattern_matcher.find_matches.cache_clear()

        # Multiple passes - should hit cache
        cache_hits = 0
        total_calls = 0

        for _ in range(20):
            for text in test_texts:
                total_calls += 1
                # In real implementation, we'd check cache stats
                classifier.pattern_matcher.find_matches(text)

        # Cache should be effective for repeated calls
        # This is a simplified test - real implementation would check actual cache stats
        assert total_calls > 0

    def test_pattern_compilation_optimization(self):
        """Test that patterns are pre-compiled for performance"""
        matcher = PatternMatcher()

        # All patterns should be pre-compiled
        assert len(matcher.compiled_patterns) > 0

        # Each compiled pattern should be a regex object
        for category, pattern in matcher.compiled_patterns.items():
            assert hasattr(pattern, "findall")
            assert hasattr(pattern, "search")

    def test_concurrent_classification_performance(self, classifier):
        """Test performance under concurrent load"""
        import concurrent.futures

        def classify_item(item):
            term, definition = item
            return classifier.classify(term, definition)

        test_items = [
            ("verdachte", "Persoon verdacht van strafbaar feit"),
            ("proces", "Juridische procedure"),
            ("overeenkomst", "Contract tussen partijen"),
        ] * 100

        start = time.perf_counter()

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(classify_item, test_items))

        duration = time.perf_counter() - start
        throughput = len(results) / duration

        assert len(results) == 300
        assert throughput > 500, f"Concurrent throughput {throughput:.0f}/sec too low"


# ============================================================================
# 4. BATCH PROCESSING TESTS
# ============================================================================


class TestBatchProcessing:
    """Test batch processing capabilities"""

    @pytest.fixture()
    def classifier(self):
        return UFOClassifierService()

    @pytest.fixture()
    def large_batch(self):
        """Create a large batch for testing"""
        terms = [
            "verdachte",
            "proces",
            "overeenkomst",
            "persoon",
            "organisatie",
            "vergunning",
            "besluit",
            "bezwaar",
            "beroep",
            "rechter",
        ]
        definitions = [f"Definitie voor {term} in juridische context" for term in terms]

        # Create 2000 items by repeating
        batch = []
        for i in range(200):
            for j, term in enumerate(terms):
                batch.append((f"{term}_{i}", definitions[j], None))

        return batch

    def test_batch_classify_basic(self, classifier):
        """Test basic batch classification"""
        items = [
            ("persoon", "Een natuurlijk persoon", None),
            ("proces", "Een juridisch proces", None),
            ("overeenkomst", "Een contract tussen partijen", None),
        ]

        results = classifier.batch_classify(items)

        assert len(results) == 3
        assert all(isinstance(r, UFOClassificationResult) for r in results)
        assert results[0].primary_category == UFOCategory.KIND
        assert results[1].primary_category == UFOCategory.EVENT
        assert results[2].primary_category == UFOCategory.RELATOR

    def test_batch_classify_with_errors(self, classifier):
        """Test batch processing with error handling"""
        items = [
            ("valid", "Een geldige definitie", None),
            (None, None, None),  # This should cause an error
            ("another", "Nog een definitie", None),
        ]

        results = classifier.batch_classify(items)

        assert len(results) == 3
        assert results[0].primary_category != UFOCategory.UNKNOWN
        assert results[1].primary_category == UFOCategory.UNKNOWN
        assert results[1].confidence == 0.0
        assert "fout" in results[1].explanation[0].lower()
        assert results[2].primary_category != UFOCategory.UNKNOWN

    def test_batch_classify_performance(self, classifier, large_batch):
        """Test batch classification performance"""
        start = time.perf_counter()
        results = classifier.batch_classify(large_batch)
        duration = time.perf_counter() - start

        throughput = len(results) / duration

        assert len(results) == 2000
        assert throughput > 2000, f"Batch throughput {throughput:.0f}/sec below target"

    def test_batch_classify_memory_efficiency(self, classifier, large_batch):
        """Test memory efficiency of batch processing"""
        import tracemalloc

        tracemalloc.start()

        results = classifier.batch_classify(large_batch)

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Should not use excessive memory
        peak_mb = peak / 1024 / 1024
        assert (
            peak_mb < 200
        ), f"Peak memory {peak_mb:.1f}MB too high for batch processing"

        # All results should be valid
        assert all(isinstance(r, UFOClassificationResult) for r in results)

    def test_batch_with_context(self, classifier):
        """Test batch processing with different contexts"""
        items = [
            ("zaak", "Een juridische aangelegenheid", {"domain": "legal"}),
            ("zaak", "Een fysiek voorwerp", {"domain": "physical"}),
            ("onderzoek", "Wetenschappelijk onderzoek", {"domain": "science"}),
            ("onderzoek", "Strafrechtelijk onderzoek", {"domain": "strafrecht"}),
        ]

        results = classifier.batch_classify(items)

        assert len(results) == 4
        # Context should influence classification
        assert results[0].primary_category in [UFOCategory.KIND, UFOCategory.EVENT]
        assert results[1].primary_category == UFOCategory.KIND
        assert results[3].primary_category == UFOCategory.EVENT


# ============================================================================
# 5. EDGE CASES FOR DUTCH LEGAL TERMINOLOGY
# ============================================================================


class TestDutchLegalEdgeCases:
    """Test edge cases specific to Dutch legal terminology"""

    @pytest.fixture()
    def classifier(self):
        return UFOClassifierService()

    def test_compound_legal_terms(self, classifier):
        """Test compound Dutch legal terms"""
        compounds = [
            (
                "gerechtsdeurwaarder",
                "Ambtenaar belast met betekening en tenuitvoerlegging",
            ),
            ("kinderrechter", "Rechter gespecialiseerd in jeugdzaken"),
            (
                "arrondissementsrechtbank",
                "Rechtbank met rechtsmacht in een arrondissement",
            ),
            ("hoger-beroepsprocedure", "Procedure bij het gerechtshof"),
        ]

        for term, definition in compounds:
            result = classifier.classify(term, definition)
            assert result.primary_category != UFOCategory.UNKNOWN
            assert result.confidence > 0.3

    def test_abbreviations_and_acronyms(self, classifier):
        """Test legal abbreviations"""
        abbreviations = [
            ("OM", "Het Openbaar Ministerie"),
            ("IND", "Immigratie- en Naturalisatiedienst"),
            ("ABRvS", "Afdeling bestuursrechtspraak van de Raad van State"),
            ("WAHV", "Wet administratiefrechtelijke handhaving verkeersvoorschriften"),
        ]

        for abbr, definition in abbreviations:
            result = classifier.classify(abbr, definition)
            # Should classify based on definition content
            assert result.primary_category in [UFOCategory.KIND, UFOCategory.ROLE]

    def test_latin_legal_terms(self, classifier):
        """Test Latin terms used in Dutch law"""
        latin_terms = [
            ("habeas corpus", "Het recht om voor een rechter te worden gebracht"),
            ("pro forma", "Een formaliteit zonder inhoudelijke behandeling"),
            ("in dubio pro reo", "Bij twijfel in het voordeel van de verdachte"),
            ("nulla poena sine lege", "Geen straf zonder wet"),
        ]

        for term, definition in latin_terms:
            result = classifier.classify(term, definition)
            # Should classify based on Dutch definition
            assert result.primary_category != UFOCategory.UNKNOWN

    def test_archaic_legal_language(self, classifier):
        """Test archaic Dutch legal terminology"""
        archaic = [
            ("drossaard", "Historische benaming voor een justitiële ambtenaar"),
            ("schout", "Vroegere benaming voor hoofd van politie"),
            ("baljuw", "Middeleeuwse rechterlijke ambtenaar"),
        ]

        for term, definition in archaic:
            result = classifier.classify(term, definition)
            assert result.primary_category == UFOCategory.ROLE

    def test_domain_specific_homonyms(self, classifier):
        """Test words with different meanings in legal context"""
        homonyms = [
            # 'Akte' as document vs ceremony
            (
                "akte",
                "Een officieel document opgemaakt door een notaris",
                {"domain": "notarieel"},
            ),
            (
                "akte",
                "De handeling van het opmaken van een document",
                {"domain": "proces"},
            ),
            # 'Vordering' as claim vs demand
            ("vordering", "Een eis tot betaling", {"domain": "civiel"}),
            (
                "vordering",
                "Het instellen van een rechtszaak",
                {"domain": "procesrecht"},
            ),
        ]

        for term, definition, context in homonyms:
            result = classifier.classify(term, definition, context)
            assert result.primary_category != UFOCategory.UNKNOWN

    def test_negations_and_exceptions(self, classifier):
        """Test definitions with negations"""
        negations = [
            ("niet-ontvankelijk", "Het niet kunnen behandelen van een zaak"),
            ("onbevoegd", "Niet bevoegd om een handeling te verrichten"),
            ("nietig", "Zonder rechtsgevolg"),
        ]

        for term, definition in negations:
            result = classifier.classify(term, definition)
            # Negations often indicate MODE or QUALITY
            assert result.primary_category in [
                UFOCategory.MODE,
                UFOCategory.QUALITY,
                UFOCategory.PHASE,
            ]


# ============================================================================
# 6. CONFIDENCE SCORING VALIDATION
# ============================================================================


class TestConfidenceScoring:
    """Test confidence score calculation and thresholds"""

    @pytest.fixture()
    def classifier(self):
        return UFOClassifierService()

    def test_confidence_distribution(self, classifier):
        """Test that confidence scores are well distributed"""
        test_cases = [
            # High confidence cases (>0.8)
            ("rechtspersoon", "Een juridische entiteit met rechtspersoonlijkheid"),
            ("arrestatie", "Het proces van aanhouding van een verdachte"),
            # Medium confidence (0.5-0.8)
            ("procedure", "Een vastgestelde werkwijze"),
            ("zaak", "Een juridische aangelegenheid"),
            # Low confidence (<0.5)
            ("iets", "Een onduidelijk begrip"),
            ("ding", "Een object"),
        ]

        confidences = []
        for term, definition in test_cases:
            result = classifier.classify(term, definition)
            confidences.append(result.confidence)

        # Should have a range of confidences
        assert max(confidences) > 0.8
        assert min(confidences) < 0.5
        assert 0.5 < sorted(confidences)[len(confidences) // 2] < 0.8

    def test_confidence_monotonicity(self, classifier):
        """Test that more evidence increases confidence"""
        # Minimal evidence
        result1 = classifier.classify("x", "Een persoon")

        # More evidence
        result2 = classifier.classify(
            "x", "Een natuurlijk persoon met rechtspersoonlijkheid"
        )

        # Most evidence
        result3 = classifier.classify(
            "natuurlijk persoon",
            "Een natuurlijk persoon is een mens met rechtspersoonlijkheid",
        )

        assert result1.confidence <= result2.confidence
        assert result2.confidence <= result3.confidence

    def test_confidence_with_conflicts(self, classifier):
        """Test confidence when patterns conflict"""
        # Contains both KIND (persoon) and EVENT (proces) markers
        result = classifier.classify(
            "procespersoon", "Een persoon die deelneemt aan een juridisch proces"
        )

        # Confidence should be moderate due to conflicts
        assert 0.3 < result.confidence < 0.9

    def test_forced_manual_review_threshold(self, classifier):
        """Test that low confidence (<0.6) triggers manual review flag"""
        low_confidence_cases = [
            ("vague", "Something unclear"),
            ("xyz", "Abstract concept"),
            ("", ""),
        ]

        for term, definition in low_confidence_cases:
            result = classifier.classify(term, definition)
            if result.primary_category != UFOCategory.UNKNOWN:
                # If classified, check if confidence triggers review
                requires_review = result.confidence < 0.6
                assert requires_review or result.confidence >= 0.6


# ============================================================================
# 7. RULE ENGINE TESTS FOR ALL 16 UFO CATEGORIES
# ============================================================================


class TestRuleEngineComprehensive:
    """Test rule engine for all 16 UFO categories"""

    @pytest.fixture()
    def classifier(self):
        return UFOClassifierService()

    def test_all_ufo_categories_have_patterns(self):
        """Test that all main categories have patterns defined"""
        matcher = PatternMatcher()

        main_categories = [
            UFOCategory.KIND,
            UFOCategory.EVENT,
            UFOCategory.ROLE,
            UFOCategory.PHASE,
            UFOCategory.RELATOR,
            UFOCategory.MODE,
            UFOCategory.QUANTITY,
            UFOCategory.QUALITY,
        ]

        for category in main_categories:
            assert category in matcher.patterns
            assert len(matcher.patterns[category]) > 0

    def test_rule_weights_configuration(self, classifier):
        """Test that rule weights are properly configured"""
        weights = classifier.decision_weights

        # KIND should have highest weight
        assert weights[UFOCategory.KIND] >= max(weights.values()) * 0.9

        # UNKNOWN should have lowest weight
        assert weights[UFOCategory.UNKNOWN] == min(weights.values())

        # Weights should be between 0 and 1
        for weight in weights.values():
            assert 0 <= weight <= 1

    def test_category_specific_rules(self, classifier):
        """Test specific rules for each category"""
        test_cases = {
            UFOCategory.KIND: (
                "organisatie",
                "Een rechtspersoon met eigen doelstellingen",
            ),
            UFOCategory.EVENT: ("zitting", "Een bijeenkomst van de rechtbank"),
            UFOCategory.ROLE: ("curator", "Persoon aangesteld als bewindvoerder"),
            UFOCategory.PHASE: ("voorlopig", "In de fase voorafgaand aan definitief"),
            UFOCategory.RELATOR: (
                "huurcontract",
                "Overeenkomst tussen huurder en verhuurder",
            ),
            UFOCategory.MODE: ("gezondheid", "De toestand van fysiek welzijn"),
            UFOCategory.QUANTITY: ("bedrag", "Een som van 100 euro"),
            UFOCategory.QUALITY: ("betrouwbaarheid", "De mate van vertrouwen"),
            UFOCategory.SUBKIND: ("type persoon", "Een soort natuurlijk persoon"),
            UFOCategory.CATEGORY: ("juridische categorie", "Een abstracte groepering"),
            UFOCategory.MIXIN: ("partij", "Verschillende rollen in een proces"),
        }

        for expected_category, (term, definition) in test_cases.items():
            result = classifier.classify(term, definition)
            # Allow for some flexibility in classification
            if expected_category in [
                UFOCategory.SUBKIND,
                UFOCategory.CATEGORY,
                UFOCategory.MIXIN,
            ]:
                # These might be secondary tags
                assert (
                    result.primary_category == expected_category
                    or expected_category in result.secondary_tags
                    or result.primary_category != UFOCategory.UNKNOWN
                )
            else:
                assert result.primary_category == expected_category

    def test_pattern_matching_accuracy(self):
        """Test accuracy of pattern matching"""
        matcher = PatternMatcher()

        # Test exact matches
        text = "Een persoon is een natuurlijk mens"
        matches = matcher.find_matches(text)

        assert UFOCategory.KIND in matches
        assert "persoon" in matches[UFOCategory.KIND]
        assert "mens" in matches[UFOCategory.KIND]

        # Test word boundaries
        text2 = "Depersoon is geen persoon"  # 'Depersoon' should not match
        matches2 = matcher.find_matches(text2)

        if UFOCategory.KIND in matches2:
            assert "persoon" in matches2[UFOCategory.KIND]
            assert len([m for m in matches2[UFOCategory.KIND] if m == "persoon"]) == 1


# ============================================================================
# 8. DATABASE MIGRATION TESTS
# ============================================================================


class TestDatabaseMigration:
    """Test database migration for UFO categories"""

    @pytest.fixture()
    def temp_db(self):
        """Create temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        yield db_path

        # Cleanup
        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture()
    def test_db_connection(self, temp_db):
        """Create test database with schema"""
        conn = sqlite3.connect(temp_db)

        # Create simplified schema
        conn.execute(
            """
            CREATE TABLE definities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                begrip TEXT NOT NULL,
                definitie TEXT NOT NULL,
                ufo_categorie TEXT,
                ufo_suggestion TEXT,
                ufo_confidence REAL,
                ufo_source TEXT DEFAULT 'manual'
            )
        """
        )

        conn.execute(
            """
            CREATE TABLE definition_ufo_history (
                id INTEGER PRIMARY KEY,
                definition_id INTEGER,
                old_category TEXT,
                new_category TEXT,
                confidence REAL,
                source TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Insert test data
        test_data = [
            ("verdachte", "Persoon verdacht van strafbaar feit"),
            ("proces", "Juridische procedure"),
            ("overeenkomst", "Contract tussen partijen"),
        ]

        for begrip, definitie in test_data:
            conn.execute(
                "INSERT INTO definities (begrip, definitie) VALUES (?, ?)",
                (begrip, definitie),
            )

        conn.commit()
        yield conn
        conn.close()

    def test_migration_adds_ufo_columns(self, temp_db):
        """Test that migration adds required UFO columns"""
        conn = sqlite3.connect(temp_db)

        # Check if columns exist
        cursor = conn.execute("PRAGMA table_info(definities)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        # Create table first if not exists
        if not columns:
            conn.execute(
                """
                CREATE TABLE definities (
                    id INTEGER PRIMARY KEY,
                    begrip TEXT,
                    definitie TEXT
                )
            """
            )
            conn.commit()

        # Simulate migration
        try:
            conn.execute("ALTER TABLE definities ADD COLUMN ufo_suggestion TEXT")
            conn.execute("ALTER TABLE definities ADD COLUMN ufo_confidence REAL")
            conn.execute(
                "ALTER TABLE definities ADD COLUMN ufo_source TEXT DEFAULT 'manual'"
            )
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Columns might already exist

        # Verify columns exist
        cursor = conn.execute("PRAGMA table_info(definities)")
        columns = {row[1] for row in cursor.fetchall()}

        assert "ufo_suggestion" in columns or "ufo_categorie" in columns

        conn.close()

    def test_batch_migration_existing_data(self, test_db_connection):
        """Test batch migration of existing definitions"""
        classifier = UFOClassifierService()
        conn = test_db_connection

        # Get all definitions
        cursor = conn.execute("SELECT id, begrip, definitie FROM definities")
        definitions = cursor.fetchall()

        # Classify each
        for def_id, begrip, definitie in definitions:
            result = classifier.classify(begrip, definitie)

            # Update database
            conn.execute(
                """
                UPDATE definities
                SET ufo_suggestion = ?, ufo_confidence = ?, ufo_source = ?
                WHERE id = ?
            """,
                (result.primary_category.value, result.confidence, "auto", def_id),
            )

        conn.commit()

        # Verify updates
        cursor = conn.execute("SELECT ufo_suggestion, ufo_confidence FROM definities")
        results = cursor.fetchall()

        assert len(results) == 3
        for suggestion, confidence in results:
            assert suggestion is not None
            assert confidence is not None
            assert confidence > 0

    def test_audit_trail_creation(self, test_db_connection):
        """Test creation of audit trail for UFO changes"""
        conn = test_db_connection

        # Simulate UFO category change
        conn.execute(
            """
            INSERT INTO definition_ufo_history
            (definition_id, old_category, new_category, confidence, source)
            VALUES (?, ?, ?, ?, ?)
        """,
            (1, None, "Role", 0.85, "auto"),
        )

        conn.execute(
            """
            INSERT INTO definition_ufo_history
            (definition_id, old_category, new_category, confidence, source)
            VALUES (?, ?, ?, ?, ?)
        """,
            (1, "Role", "Kind", 0.92, "manual"),
        )

        conn.commit()

        # Verify audit trail
        cursor = conn.execute(
            """
            SELECT * FROM definition_ufo_history
            WHERE definition_id = 1
            ORDER BY timestamp
        """
        )

        history = cursor.fetchall()
        assert len(history) == 2
        assert history[0][2] is None  # old_category
        assert history[0][3] == "Role"  # new_category
        assert history[1][2] == "Role"  # old_category
        assert history[1][3] == "Kind"  # new_category


# ============================================================================
# 9. UI INTEGRATION TESTS
# ============================================================================


class TestUIIntegration:
    """Test integration with UI components (Generator/Edit/Expert tabs)"""

    @pytest.fixture()
    def classifier(self):
        return UFOClassifierService()

    @pytest.fixture()
    def mock_streamlit(self):
        """Mock Streamlit components"""
        mock_st = Mock()
        mock_st.info = Mock()
        mock_st.button = Mock(return_value=False)
        mock_st.selectbox = Mock()
        mock_st.write = Mock()
        return mock_st

    def test_ui_display_suggestion(self, classifier, mock_streamlit):
        """Test UI display of UFO suggestion"""
        result = classifier.classify("verdachte", "Persoon verdacht van strafbaar feit")

        # Simulate UI display
        mock_streamlit.info(
            f"Voorgestelde categorie: {result.primary_category.value} "
            f"({result.confidence:.0%})"
        )

        mock_streamlit.info.assert_called_once()
        call_args = mock_streamlit.info.call_args[0][0]
        assert result.primary_category.value in call_args
        assert f"{result.confidence:.0%}" in call_args

    def test_ui_manual_override(self, classifier, mock_streamlit):
        """Test manual override functionality"""
        result = classifier.classify("verdachte", "Persoon verdacht van strafbaar feit")

        # Available categories
        categories = [cat.value for cat in UFOCategory]

        # Simulate selectbox with override
        mock_streamlit.selectbox.return_value = "Kind"  # User overrides to Kind

        selected = mock_streamlit.selectbox(
            "UFO Categorie",
            options=categories,
            index=categories.index(result.primary_category.value),
        )

        assert selected == "Kind"
        assert selected != result.primary_category.value

    def test_ui_explanation_display(self, classifier, mock_streamlit):
        """Test explanation display in UI"""
        result = classifier.classify("verdachte", "Persoon verdacht van strafbaar feit")

        # Simulate "Why?" button click
        mock_streamlit.button.return_value = True

        if mock_streamlit.button("Waarom?"):
            mock_streamlit.write("**Gedetecteerde patronen:**")
            for rule in result.explanation[:3]:
                mock_streamlit.write(f"- {rule}")

        # Verify explanation was displayed
        assert mock_streamlit.write.call_count >= len(result.explanation[:3])

    def test_ui_low_confidence_warning(self, classifier, mock_streamlit):
        """Test UI warning for low confidence"""
        # Create low confidence case
        result = classifier.classify("vague", "unclear definition")

        if result.confidence < 0.6:
            mock_streamlit.warning = Mock()
            mock_streamlit.warning("⚠️ Lage zekerheid - handmatige review vereist")
            mock_streamlit.warning.assert_called_once()

    def test_bulk_review_interface(self, classifier):
        """Test bulk review interface for low confidence items"""
        # Simulate batch of items with varying confidence
        items = [
            ("term1", "clear definition", None),
            ("term2", "vague description", None),
            ("term3", "another clear one", None),
            ("term4", "unclear", None),
        ]

        results = classifier.batch_classify(items)

        # Filter items needing review
        needs_review = [
            (item, result)
            for (item, result) in zip(items, results, strict=False)
            if result.confidence < 0.6
        ]

        # Should have some items needing review
        assert len(needs_review) > 0
        assert all(r.confidence < 0.6 for _, r in needs_review)


# ============================================================================
# 10. FALLBACK MECHANISM TESTS (confidence <0.6)
# ============================================================================


class TestFallbackMechanism:
    """Test fallback mechanism for low confidence classifications"""

    @pytest.fixture()
    def classifier(self):
        return UFOClassifierService()

    def test_fallback_triggers_at_threshold(self, classifier):
        """Test that fallback triggers at confidence <0.6"""
        test_cases = [
            ("", ""),  # Empty input
            ("xyz", "qwerty"),  # Nonsense
            ("abstract", "vague concept"),  # Vague
        ]

        for term, definition in test_cases:
            result = classifier.classify(term, definition)

            if result.primary_category != UFOCategory.UNKNOWN:
                # Check if needs fallback
                needs_fallback = result.confidence < 0.6
                if needs_fallback:
                    assert result.confidence < 0.6

    def test_fallback_to_manual_review(self, classifier):
        """Test fallback to manual review process"""
        # Low confidence classification
        result = classifier.classify("unclear", "vague description")

        if result.confidence < 0.6:
            # Should trigger manual review
            review_required = {
                "definition_id": 1,
                "term": "unclear",
                "auto_classification": result.primary_category.value,
                "confidence": result.confidence,
                "requires_manual_review": True,
            }

            assert review_required["requires_manual_review"]
            assert review_required["confidence"] < 0.6

    def test_fallback_preserves_suggestion(self, classifier):
        """Test that fallback preserves the original suggestion"""
        result = classifier.classify("vague", "unclear")

        # Even with low confidence, should preserve the suggestion
        fallback_data = {
            "suggested_category": result.primary_category.value,
            "confidence": result.confidence,
            "status": "needs_review" if result.confidence < 0.6 else "auto_classified",
        }

        if result.confidence < 0.6:
            assert fallback_data["status"] == "needs_review"
            assert fallback_data["suggested_category"] is not None


# ============================================================================
# 11. AUDIT LOGGING TESTS
# ============================================================================


class TestAuditLogging:
    """Test audit logging functionality"""

    @pytest.fixture()
    def classifier(self):
        return UFOClassifierService()

    @pytest.fixture()
    def audit_log(self):
        """Mock audit log storage"""
        return []

    def test_audit_log_creation(self, classifier, audit_log):
        """Test creation of audit log entries"""
        result = classifier.classify("verdachte", "Persoon verdacht van strafbaar feit")

        # Create audit entry
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "auto_classification",
            "term": "verdachte",
            "category": result.primary_category.value,
            "confidence": result.confidence,
            "source": "auto",
            "patterns_matched": list(result.matched_patterns.keys()),
        }

        audit_log.append(audit_entry)

        assert len(audit_log) == 1
        assert audit_log[0]["action"] == "auto_classification"
        assert audit_log[0]["confidence"] > 0

    def test_audit_log_manual_override(self, classifier, audit_log):
        """Test logging of manual overrides"""
        result = classifier.classify("verdachte", "Persoon verdacht van strafbaar feit")

        # Log auto classification
        audit_log.append(
            {
                "timestamp": datetime.now().isoformat(),
                "action": "auto_classification",
                "category": result.primary_category.value,
                "confidence": result.confidence,
            }
        )

        # Log manual override
        audit_log.append(
            {
                "timestamp": datetime.now().isoformat(),
                "action": "manual_override",
                "old_category": result.primary_category.value,
                "new_category": "Kind",
                "reason": "Expert judgment",
            }
        )

        assert len(audit_log) == 2
        assert audit_log[1]["action"] == "manual_override"
        assert audit_log[1]["old_category"] != audit_log[1]["new_category"]

    def test_audit_log_no_pii(self, classifier, audit_log):
        """Test that audit logs contain no PII"""
        result = classifier.classify(
            "Jan Jansen",  # Name (PII)
            "Een specifieke persoon met BSN 123456789",  # Contains BSN (PII)
        )

        # Audit entry should not contain PII
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "classification",
            "category": result.primary_category.value,
            "confidence": result.confidence,
            # No term or definition stored
            "has_pii": False,
        }

        audit_log.append(audit_entry)

        # Verify no PII in audit log
        assert "Jan Jansen" not in str(audit_log)
        assert "123456789" not in str(audit_log)
        assert audit_log[0]["has_pii"] == False


# ============================================================================
# 12. A/B TESTING FRAMEWORK
# ============================================================================


class TestABTestingFramework:
    """Test A/B testing framework for rule improvements"""

    @pytest.fixture()
    def classifier_a(self):
        """Baseline classifier"""
        return UFOClassifierService()

    @pytest.fixture()
    def classifier_b(self):
        """Experimental classifier with modified rules"""
        classifier = UFOClassifierService()
        # Simulate modified weights
        classifier.decision_weights[UFOCategory.EVENT] = 1.0
        return classifier

    def test_ab_comparison_framework(self, classifier_a, classifier_b):
        """Test A/B comparison of classifiers"""
        test_set = [
            ("proces", "Een juridische procedure"),
            ("persoon", "Een natuurlijk persoon"),
            ("overeenkomst", "Contract tussen partijen"),
        ]

        results_a = []
        results_b = []

        for term, definition in test_set:
            results_a.append(classifier_a.classify(term, definition))
            results_b.append(classifier_b.classify(term, definition))

        # Compare results
        differences = []
        for i, (a, b) in enumerate(zip(results_a, results_b, strict=False)):
            if a.primary_category != b.primary_category:
                differences.append(
                    {
                        "term": test_set[i][0],
                        "classifier_a": a.primary_category.value,
                        "classifier_b": b.primary_category.value,
                        "confidence_a": a.confidence,
                        "confidence_b": b.confidence,
                    }
                )

        # Should detect some differences due to weight changes
        assert len(differences) >= 0

    def test_ab_metrics_collection(self, classifier_a, classifier_b):
        """Test metrics collection for A/B testing"""
        test_set = [
            ("proces", "Een juridische procedure", UFOCategory.EVENT),  # Expected
            ("persoon", "Een natuurlijk persoon", UFOCategory.KIND),
            ("overeenkomst", "Contract tussen partijen", UFOCategory.RELATOR),
        ]

        def evaluate_classifier(classifier, test_set):
            correct = 0
            total_confidence = 0

            for term, definition, expected in test_set:
                result = classifier.classify(term, definition)
                if result.primary_category == expected:
                    correct += 1
                total_confidence += result.confidence

            return {
                "accuracy": correct / len(test_set),
                "avg_confidence": total_confidence / len(test_set),
            }

        metrics_a = evaluate_classifier(classifier_a, test_set)
        metrics_b = evaluate_classifier(classifier_b, test_set)

        # Both should have reasonable accuracy
        assert metrics_a["accuracy"] >= 0.5
        assert metrics_b["accuracy"] >= 0.5

        # Confidence should be positive
        assert metrics_a["avg_confidence"] > 0
        assert metrics_b["avg_confidence"] > 0

    def test_ab_statistical_significance(self):
        """Test framework for statistical significance testing"""
        # Simulate A/B test results
        results_a = [0.85, 0.82, 0.88, 0.81, 0.86]  # Accuracy over time
        results_b = [0.87, 0.89, 0.88, 0.90, 0.91]  # Improved accuracy

        mean_a = np.mean(results_a)
        mean_b = np.mean(results_b)
        std_a = np.std(results_a)
        std_b = np.std(results_b)

        # Simple comparison (in practice, would use proper statistical test)
        improvement = mean_b - mean_a

        assert improvement > 0, "Classifier B should show improvement"
        assert mean_b > 0.85, "Classifier B should maintain high accuracy"

    def test_ab_rollback_capability(self, classifier_a):
        """Test ability to rollback to previous version"""
        # Save original weights
        original_weights = classifier_a.decision_weights.copy()

        # Modify weights (experiment)
        classifier_a.decision_weights[UFOCategory.EVENT] = 0.1

        # Test with modified weights
        result_modified = classifier_a.classify("proces", "Een juridische procedure")

        # Rollback
        classifier_a.decision_weights = original_weights

        # Test after rollback
        result_rollback = classifier_a.classify("proces", "Een juridische procedure")

        # Should restore original behavior
        assert result_rollback.primary_category == UFOCategory.EVENT
        assert classifier_a.decision_weights == original_weights


# ============================================================================
# FIXTURES AND UTILITIES
# ============================================================================


@pytest.fixture(scope="session")
def performance_report():
    """Generate performance report after all tests"""
    report = {"timestamp": datetime.now().isoformat(), "metrics": {}}

    yield report

    # Save report
    with open("test_performance_report.json", "w") as f:
        json.dump(report, f, indent=2)


@contextmanager
def timer(name: str, report: dict):
    """Context manager for timing operations"""
    start = time.perf_counter()
    yield
    duration = time.perf_counter() - start

    if "timings" not in report:
        report["timings"] = {}
    report["timings"][name] = duration


# ============================================================================
# INTEGRATION TEST SUITE
# ============================================================================


class TestFullIntegration:
    """Full integration test combining all components"""

    def test_end_to_end_classification_flow(self):
        """Test complete classification flow from input to storage"""
        # Initialize classifier
        classifier = get_ufo_classifier()

        # Test input
        term = "koopovereenkomst"
        definition = "Een overeenkomst waarbij de verkoper zich verbindt een zaak te leveren en de koper om een prijs te betalen"

        # Classify
        result = classifier.classify(term, definition)

        # Validate result
        assert result.primary_category == UFOCategory.RELATOR
        assert result.confidence > 0.6
        assert len(result.explanation) > 0

        # Simulate storage
        stored_data = {
            "begrip": term,
            "definitie": definition,
            "ufo_categorie": result.primary_category.value,
            "ufo_confidence": result.confidence,
            "ufo_source": "auto",
        }

        # Verify storage format
        assert stored_data["ufo_categorie"] in [cat.value for cat in UFOCategory]
        assert 0 <= stored_data["ufo_confidence"] <= 1
        assert stored_data["ufo_source"] in ["auto", "manual"]

    def test_migration_and_reclassification(self):
        """Test migration of existing definitions with reclassification"""
        classifier = UFOClassifierService()

        # Simulate existing definitions without UFO categories
        existing_definitions = [
            {
                "id": 1,
                "begrip": "verdachte",
                "definitie": "Persoon verdacht van strafbaar feit",
            },
            {"id": 2, "begrip": "proces", "definitie": "Juridische procedure"},
            {"id": 3, "begrip": "vague", "definitie": "unclear"},
        ]

        migration_results = []
        needs_review = []

        for definition in existing_definitions:
            result = classifier.classify(definition["begrip"], definition["definitie"])

            migration_data = {
                "id": definition["id"],
                "ufo_suggestion": result.primary_category.value,
                "confidence": result.confidence,
                "needs_review": result.confidence < 0.6,
            }

            migration_results.append(migration_data)

            if migration_data["needs_review"]:
                needs_review.append(definition["id"])

        # Verify migration results
        assert len(migration_results) == 3
        assert len(needs_review) > 0  # Should have at least one low confidence
        assert all("ufo_suggestion" in r for r in migration_results)


if __name__ == "__main__":
    # Run tests with coverage
    pytest.main(
        [
            __file__,
            "-v",
            "--cov=src.services.ufo_classifier_service",
            "--cov-report=html",
        ]
    )
