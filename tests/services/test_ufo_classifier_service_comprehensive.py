"""
Comprehensive test suite voor UFO Classifier Service v3.0 met 100% coverage.

Deze test suite implementeert uitgebreide tests voor:
- Alle UFO categorieën (9 hoofdcategorieën)
- Pattern matching en disambiguation
- Edge cases en error handling
- Performance requirements (< 100ms per classificatie)
- Integration scenarios
- Nederlandse juridische termen
- Batch processing

Auteur: AI Assistant
Datum: 2025-09-23
Coverage Target: 100%
Performance Target: < 100ms per classificatie
"""

import json
import logging
import re
import time
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from unittest.mock import MagicMock, Mock, mock_open, patch

import pytest
import yaml

from src.services.ufo_classifier_service import (
    UFOCategory,
    UFOClassificationResult,
    UFOClassifierService,
    create_ufo_classifier_service,
    get_ufo_classifier,
)


class TestUFOCategory:
    """Test de UFOCategory enum."""

    def test_all_categories_defined(self):
        """Test dat alle 9 UFO categorieën gedefinieerd zijn."""
        expected_categories = [
            "KIND",
            "EVENT",
            "ROLE",
            "PHASE",
            "RELATOR",
            "MODE",
            "QUANTITY",
            "QUALITY",
            "COLLECTIVE",
        ]

        actual_categories = [cat.name for cat in UFOCategory]
        assert len(actual_categories) == 9

        for expected in expected_categories:
            assert expected in actual_categories, f"Categorie {expected} ontbreekt"

    def test_category_values(self):
        """Test dat category values correct zijn."""
        assert UFOCategory.KIND.value == "Kind"
        assert UFOCategory.EVENT.value == "Event"
        assert UFOCategory.ROLE.value == "Role"
        assert UFOCategory.COLLECTIVE.value == "Collective"


class TestUFOClassificationResult:
    """Test de UFOClassificationResult dataclass."""

    def test_result_creation(self):
        """Test dat results correct aangemaakt worden."""
        result = UFOClassificationResult(
            term="persoon",
            definition="Een mens van vlees en bloed",
            primary_category=UFOCategory.KIND,
            confidence=0.85,
            secondary_categories=[UFOCategory.ROLE],
            matched_patterns=["Kind: persoon", "Kind: mens"],
            explanation="Kind (85% zekerheid) - Basisentiteit of object",
            classification_time_ms=12.5,
        )

        assert result.term == "persoon"
        assert result.definition == "Een mens van vlees en bloed"
        assert result.primary_category == UFOCategory.KIND
        assert result.confidence == 0.85
        assert UFOCategory.ROLE in result.secondary_categories
        assert len(result.matched_patterns) == 2
        assert "85%" in result.explanation
        assert result.classification_time_ms == 12.5

    def test_default_values(self):
        """Test default waarden van result."""
        result = UFOClassificationResult(
            term="test", definition="test def", primary_category=UFOCategory.KIND
        )

        assert result.confidence == 0.0
        assert result.secondary_categories == []
        assert result.matched_patterns == []
        assert result.explanation == ""
        assert result.classification_time_ms == 0.0

    def test_json_serialization(self):
        """Test dat result JSON-serialiseerbaar is."""
        result = UFOClassificationResult(
            term="verdachte",
            definition="Persoon die wordt verdacht",
            primary_category=UFOCategory.ROLE,
            confidence=0.75,
            secondary_categories=[UFOCategory.KIND],
            matched_patterns=["Role: verdachte"],
            explanation="Test explanation",
            classification_time_ms=5.2,
        )

        # Converteer naar dict voor serialisatie
        result_dict = {
            "term": result.term,
            "definition": result.definition,
            "primary_category": result.primary_category.value,
            "confidence": result.confidence,
            "secondary_categories": [c.value for c in result.secondary_categories],
            "matched_patterns": result.matched_patterns,
            "explanation": result.explanation,
            "classification_time_ms": result.classification_time_ms,
        }

        json_str = json.dumps(result_dict)
        assert json_str

        # Deserialize en check
        loaded = json.loads(json_str)
        assert loaded["primary_category"] == "Role"
        assert loaded["confidence"] == 0.75


class TestUFOClassifierServiceInitialization:
    """Test initialisatie van UFOClassifierService."""

    def test_initialization_without_config(self):
        """Test initialisatie zonder config bestand."""
        classifier = UFOClassifierService()

        assert classifier is not None
        assert classifier.compiled_patterns is not None
        assert classifier.config is not None
        assert classifier.config["high_confidence"] == 0.8
        assert classifier.config["medium_confidence"] == 0.6
        assert classifier.config["max_time_ms"] == 500

    def test_initialization_with_config(self, tmp_path):
        """Test initialisatie met config bestand."""
        config_file = tmp_path / "test_config.yaml"
        config_data = {
            "high_confidence": 0.9,
            "medium_confidence": 0.7,
            "max_time_ms": 1000,
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        classifier = UFOClassifierService(config_path=config_file)

        assert classifier.config["high_confidence"] == 0.9
        assert classifier.config["medium_confidence"] == 0.7
        assert classifier.config["max_time_ms"] == 1000

    def test_initialization_with_invalid_config(self, tmp_path):
        """Test initialisatie met ongeldig config bestand."""
        config_file = tmp_path / "invalid_config.yaml"
        config_file.write_text("invalid: yaml: content:")

        with patch("src.services.ufo_classifier_service.logger") as mock_logger:
            classifier = UFOClassifierService(config_path=config_file)

            # Should use defaults
            assert classifier.config["high_confidence"] == 0.8
            mock_logger.warning.assert_called()

    def test_initialization_with_missing_config(self):
        """Test initialisatie met niet-bestaand config bestand."""
        classifier = UFOClassifierService(config_path=Path("non_existent.yaml"))

        # Should use defaults
        assert classifier.config["high_confidence"] == 0.8
        assert classifier.config["medium_confidence"] == 0.6

    def test_compile_patterns(self):
        """Test dat patterns correct gecompileerd worden."""
        classifier = UFOClassifierService()

        # Check dat alle categorieën gecompileerd zijn
        for category in UFOCategory:
            if category in classifier.PATTERNS:
                assert category in classifier.compiled_patterns
                assert all(
                    isinstance(p, re.Pattern)
                    for p in classifier.compiled_patterns[category]
                )

    def test_pattern_case_insensitivity(self):
        """Test dat patterns case-insensitive zijn."""
        classifier = UFOClassifierService()

        for _category, patterns in classifier.compiled_patterns.items():
            for pattern in patterns:
                assert pattern.flags & re.IGNORECASE


class TestClassification:
    """Test de classify methode."""

    @pytest.fixture
    def classifier(self):
        """Maak een UFOClassifierService instance."""
        return UFOClassifierService()

    def test_classify_kind(self, classifier):
        """Test classificatie van KIND entiteit."""
        result = classifier.classify(
            "persoon", "Een natuurlijk persoon is een mens van vlees en bloed"
        )

        assert result.primary_category == UFOCategory.KIND
        assert result.confidence > 0.5
        assert result.term == "persoon"
        assert len(result.matched_patterns) > 0
        assert "Kind" in result.explanation

    def test_classify_event(self, classifier):
        """Test classificatie van EVENT."""
        result = classifier.classify(
            "arrestatie",
            "Het proces waarbij iemand tijdens het onderzoek wordt aangehouden",
        )

        assert result.primary_category == UFOCategory.EVENT
        assert result.confidence > 0.5
        assert any("Event" in p for p in result.matched_patterns)

    def test_classify_role(self, classifier):
        """Test classificatie van ROLE."""
        result = classifier.classify(
            "verdachte", "Persoon in de hoedanigheid van mogelijke dader"
        )

        assert result.primary_category == UFOCategory.ROLE
        assert result.confidence > 0.3

    def test_classify_phase(self, classifier):
        """Test classificatie van PHASE."""
        result = classifier.classify(
            "voorlopige hechtenis", "De voorlopige fase van detentie"
        )

        assert result.primary_category == UFOCategory.PHASE
        assert result.confidence > 0.3

    def test_classify_relator(self, classifier):
        """Test classificatie van RELATOR."""
        result = classifier.classify(
            "koopovereenkomst", "Een overeenkomst tussen koper en verkoper"
        )

        assert result.primary_category == UFOCategory.RELATOR
        assert result.confidence > 0.5

    def test_classify_mode(self, classifier):
        """Test classificatie van MODE."""
        result = classifier.classify(
            "locatie", "De eigenschap die aangeeft waar iets zich bevindt"
        )

        assert result.primary_category == UFOCategory.MODE
        assert result.confidence > 0.3

    def test_classify_quantity(self, classifier):
        """Test classificatie van QUANTITY."""
        result = classifier.classify("schadevergoeding", "Een bedrag van 10.000 euro")

        assert result.primary_category == UFOCategory.QUANTITY
        assert result.confidence > 0.3

    def test_classify_quality(self, classifier):
        """Test classificatie van QUALITY."""
        result = classifier.classify(
            "betrouwbaarheid", "De mate van betrouwbaarheid van de getuige"
        )

        assert result.primary_category == UFOCategory.QUALITY
        assert result.confidence > 0.3

    def test_classify_collective(self, classifier):
        """Test classificatie van COLLECTIVE."""
        result = classifier.classify("commissie", "Een groep van deskundigen")

        assert result.primary_category == UFOCategory.COLLECTIVE
        assert result.confidence > 0.3

    def test_classify_with_empty_term(self, classifier):
        """Test met lege term."""
        with pytest.raises(ValueError, match="term.*niet-lege string"):
            classifier.classify("", "Een definitie")

    def test_classify_with_empty_definition(self, classifier):
        """Test met lege definitie."""
        with pytest.raises(ValueError, match="definition.*niet-lege string"):
            classifier.classify("term", "")

    def test_classify_with_whitespace_only(self, classifier):
        """Test met alleen whitespace."""
        with pytest.raises(ValueError, match="term.*niet leeg"):
            classifier.classify("   ", "definitie")

    def test_classify_with_none_input(self, classifier):
        """Test met None input."""
        with pytest.raises(ValueError, match="term.*niet-lege string"):
            classifier.classify(None, "definitie")

    def test_classify_with_very_long_text(self, classifier):
        """Test met zeer lange tekst (> 5000 karakters)."""
        long_text = "a" * 6000
        result = classifier.classify("test", long_text)

        # Text should be truncated to 5000 chars
        assert len(result.definition) == 5000
        assert result.primary_category is not None

    def test_classify_performance(self, classifier):
        """Test dat classificatie < 100ms duurt."""
        times = []
        for _ in range(10):
            start = time.perf_counter()
            classifier.classify("persoon", "Een natuurlijk persoon")
            duration = (time.perf_counter() - start) * 1000
            times.append(duration)

        avg_time = sum(times) / len(times)
        assert avg_time < 100, f"Gemiddelde tijd {avg_time:.1f}ms > 100ms"
        assert all(t < 500 for t in times), "Sommige classificaties > 500ms"


class TestDisambiguation:
    """Test disambiguation voor ambigue termen."""

    @pytest.fixture
    def classifier(self):
        return UFOClassifierService()

    def test_zaak_disambiguation(self, classifier):
        """Test disambiguatie van 'zaak'."""
        # Rechtszaak -> EVENT
        result1 = classifier.classify("zaak", "Een rechtszaak voor de rechter")
        assert result1.primary_category == UFOCategory.EVENT

        # Roerende zaak -> KIND
        result2 = classifier.classify("zaak", "Een roerende zaak zoals een auto")
        assert result2.primary_category == UFOCategory.KIND

    def test_huwelijk_disambiguation(self, classifier):
        """Test disambiguatie van 'huwelijk'."""
        # Sluiten van huwelijk -> EVENT
        result1 = classifier.classify("huwelijk", "Het sluiten van een huwelijk")
        assert result1.primary_category == UFOCategory.EVENT

        # Huwelijk als relatie -> RELATOR
        result2 = classifier.classify("huwelijk", "Een band tussen twee personen")
        assert result2.primary_category == UFOCategory.RELATOR

    def test_overeenkomst_disambiguation(self, classifier):
        """Test disambiguatie van 'overeenkomst'."""
        # Sluiten overeenkomst -> EVENT
        result1 = classifier.classify(
            "overeenkomst", "Het aangaan van een overeenkomst"
        )
        assert result1.primary_category == UFOCategory.EVENT

        # Overeenkomst tussen partijen -> RELATOR
        result2 = classifier.classify("overeenkomst", "Een contract tussen partijen")
        assert result2.primary_category == UFOCategory.RELATOR

    def test_procedure_disambiguation(self, classifier):
        """Test disambiguatie van 'procedure'."""
        # Start procedure -> EVENT
        result1 = classifier.classify("procedure", "Het begin van de procedure")
        assert result1.primary_category == UFOCategory.EVENT

        # Procedure volgens regels -> KIND
        result2 = classifier.classify(
            "procedure", "Een vastgestelde procedure volgens de wet"
        )
        assert result2.primary_category == UFOCategory.KIND

    def test_vergunning_disambiguation(self, classifier):
        """Test disambiguatie van 'vergunning'."""
        # Aanvragen vergunning -> EVENT
        result1 = classifier.classify("vergunning", "Het verlenen van een vergunning")
        assert result1.primary_category == UFOCategory.EVENT

        # Vergunning voor iets -> RELATOR
        result2 = classifier.classify(
            "vergunning", "Hij heeft een vergunning voor de bouw"
        )
        assert result2.primary_category == UFOCategory.RELATOR


class TestPatternMatching:
    """Test pattern matching functionaliteit."""

    @pytest.fixture
    def classifier(self):
        return UFOClassifierService()

    def test_calculate_pattern_scores(self, classifier):
        """Test score berekening."""
        scores = classifier._calculate_pattern_scores(
            "persoon", "Een natuurlijk persoon is een mens"
        )

        assert UFOCategory.KIND in scores
        assert scores[UFOCategory.KIND] > 0

    def test_get_matched_patterns(self, classifier):
        """Test ophalen van gematchte patterns."""
        patterns = classifier._get_matched_patterns(
            "verdachte", "De verdachte wordt verhoord"
        )

        assert len(patterns) > 0
        assert any("Role" in p for p in patterns)

    def test_matched_patterns_limit(self, classifier):
        """Test dat matched patterns gelimiteerd zijn tot 5."""
        # Create text met veel matches
        text = "persoon mens organisatie zaak ding object document gebouw voertuig"
        patterns = classifier._get_matched_patterns("multi", text)

        assert len(patterns) <= 5

    def test_pattern_scores_capped(self, classifier):
        """Test dat scores gecapped zijn op 1.0."""
        # Text met heel veel KIND patterns
        text = (
            "persoon mens organisatie zaak ding object document gebouw voertuig " * 10
        )
        scores = classifier._calculate_pattern_scores("test", text)

        assert all(score <= 1.0 for score in scores.values())

    def test_no_pattern_matches(self, classifier):
        """Test met tekst zonder pattern matches."""
        scores = classifier._calculate_pattern_scores("xyz", "abc def ghi")

        assert len(scores) == 0


class TestConfidenceCalculation:
    """Test confidence berekening."""

    @pytest.fixture
    def classifier(self):
        return UFOClassifierService()

    def test_calculate_confidence_no_scores(self, classifier):
        """Test confidence zonder scores."""
        confidence = classifier._calculate_confidence({}, UFOCategory.KIND)
        assert confidence == 0.3  # Default lage confidence

    def test_calculate_confidence_single_score(self, classifier):
        """Test confidence met één score."""
        scores = {UFOCategory.KIND: 0.8}
        confidence = classifier._calculate_confidence(scores, UFOCategory.KIND)
        assert confidence == 0.8

    def test_calculate_confidence_ambiguous(self, classifier):
        """Test confidence bij ambiguïteit."""
        scores = {UFOCategory.KIND: 0.6, UFOCategory.ROLE: 0.5}  # Dicht bij elkaar
        confidence = classifier._calculate_confidence(scores, UFOCategory.KIND)
        assert confidence < 0.6  # Verlaagd door ambiguïteit

    def test_calculate_confidence_clear_winner(self, classifier):
        """Test confidence met duidelijke winnaar."""
        scores = {UFOCategory.KIND: 0.9, UFOCategory.ROLE: 0.2}
        confidence = classifier._calculate_confidence(scores, UFOCategory.KIND)
        assert confidence >= 0.9

    def test_calculate_confidence_many_matches(self, classifier):
        """Test confidence boost bij veel matches."""
        scores = {
            UFOCategory.KIND: 0.7,
            UFOCategory.EVENT: 0.6,
            UFOCategory.ROLE: 0.5,
            UFOCategory.RELATOR: 0.4,
        }
        confidence = classifier._calculate_confidence(scores, UFOCategory.KIND)
        # Total score > 2.0, dus confidence boost
        assert confidence > 0.7

    def test_confidence_bounds(self, classifier):
        """Test dat confidence binnen bounds blijft."""
        # Test lower bound
        confidence1 = classifier._calculate_confidence({}, UFOCategory.KIND)
        assert 0.1 <= confidence1 <= 1.0

        # Test upper bound
        scores = {UFOCategory.KIND: 10.0}  # Zeer hoge score
        confidence2 = classifier._calculate_confidence(scores, UFOCategory.KIND)
        assert confidence2 <= 1.0


class TestSecondaryCategories:
    """Test bepaling van secundaire categorieën."""

    @pytest.fixture
    def classifier(self):
        return UFOClassifierService()

    def test_get_secondary_categories(self, classifier):
        """Test bepaling van secundaire categorieën."""
        scores = {
            UFOCategory.KIND: 0.8,
            UFOCategory.ROLE: 0.6,
            UFOCategory.EVENT: 0.4,
            UFOCategory.PHASE: 0.2,
        }

        secondary = classifier._get_secondary_categories(scores, UFOCategory.KIND)

        assert len(secondary) <= 2
        assert UFOCategory.KIND not in secondary
        assert UFOCategory.ROLE in secondary
        assert UFOCategory.EVENT in secondary

    def test_get_secondary_categories_threshold(self, classifier):
        """Test dat alleen categorieën >= 0.3 als secundair worden gekozen."""
        scores = {
            UFOCategory.KIND: 0.8,
            UFOCategory.ROLE: 0.25,  # Onder threshold
            UFOCategory.EVENT: 0.4,
        }

        secondary = classifier._get_secondary_categories(scores, UFOCategory.KIND)

        assert UFOCategory.EVENT in secondary
        assert UFOCategory.ROLE not in secondary

    def test_get_secondary_categories_sorted(self, classifier):
        """Test dat secundaire categorieën gesorteerd zijn op score."""
        scores = {
            UFOCategory.KIND: 0.8,
            UFOCategory.ROLE: 0.3,
            UFOCategory.EVENT: 0.6,
            UFOCategory.PHASE: 0.5,
        }

        secondary = classifier._get_secondary_categories(scores, UFOCategory.KIND)

        assert secondary[0] == UFOCategory.EVENT  # Hoogste score
        assert secondary[1] == UFOCategory.PHASE  # Tweede hoogste


class TestExplanationGeneration:
    """Test uitleg generatie."""

    @pytest.fixture
    def classifier(self):
        return UFOClassifierService()

    def test_generate_explanation_basic(self, classifier):
        """Test basis uitleg generatie."""
        explanation = classifier._generate_explanation(
            UFOCategory.KIND, 0.85, ["Kind: persoon", "Kind: mens"]
        )

        assert "Kind" in explanation
        assert "85%" in explanation
        assert "2 patronen" in explanation
        assert "Basisentiteit" in explanation

    def test_generate_explanation_no_patterns(self, classifier):
        """Test uitleg zonder patterns."""
        explanation = classifier._generate_explanation(UFOCategory.EVENT, 0.6, [])

        assert "Event" in explanation
        assert "60%" in explanation
        assert "patronen" not in explanation

    def test_generate_explanation_all_categories(self, classifier):
        """Test dat alle categorieën een uitleg hebben."""
        for category in UFOCategory:
            explanation = classifier._generate_explanation(category, 0.7, [])
            assert category.value in explanation


class TestNormalization:
    """Test tekst normalisatie."""

    @pytest.fixture
    def classifier(self):
        return UFOClassifierService()

    def test_normalize_text_basic(self, classifier):
        """Test basis normalisatie."""
        normalized = classifier._normalize_text("  test  ", "field")
        assert normalized == "test"

    def test_normalize_text_unicode(self, classifier):
        """Test Unicode normalisatie."""
        text_with_accents = "café naïef"
        normalized = classifier._normalize_text(text_with_accents, "field")
        assert normalized == unicodedata.normalize("NFC", text_with_accents)

    def test_normalize_text_very_long(self, classifier):
        """Test truncatie van zeer lange tekst."""
        long_text = "a" * 6000
        normalized = classifier._normalize_text(long_text, "field")
        assert len(normalized) == 5000

    def test_normalize_text_empty(self, classifier):
        """Test met lege string."""
        with pytest.raises(ValueError, match="niet-lege string"):
            classifier._normalize_text("", "field")

    def test_normalize_text_none(self, classifier):
        """Test met None."""
        with pytest.raises(ValueError, match="niet-lege string"):
            classifier._normalize_text(None, "field")

    def test_normalize_text_whitespace(self, classifier):
        """Test met alleen whitespace."""
        with pytest.raises(ValueError, match="niet leeg"):
            classifier._normalize_text("   ", "field")


class TestBatchClassification:
    """Test batch classificatie."""

    @pytest.fixture
    def classifier(self):
        return UFOClassifierService()

    def test_batch_classify_basic(self, classifier):
        """Test basis batch classificatie."""
        definitions = [
            ("persoon", "Een mens"),
            ("proces", "Een procedure"),
            ("verdachte", "Iemand die verdacht wordt"),
        ]

        results = classifier.batch_classify(definitions)

        assert len(results) == 3
        assert all(isinstance(r, UFOClassificationResult) for r in results)
        assert results[0].primary_category == UFOCategory.KIND
        assert results[1].primary_category == UFOCategory.EVENT
        assert results[2].primary_category == UFOCategory.ROLE

    def test_batch_classify_with_errors(self, classifier):
        """Test batch met fouten."""
        definitions = [
            ("valid", "Een geldige definitie"),
            ("", "Lege term"),  # Zal error geven
            ("another", "Nog een definitie"),
        ]

        with patch("src.services.ufo_classifier_service.logger") as mock_logger:
            results = classifier.batch_classify(definitions)

            assert len(results) == 3
            assert results[0].confidence > 0
            assert results[1].confidence == 0.0
            assert "Error" in results[1].explanation
            assert results[2].confidence > 0

            # Check dat error gelogd is
            mock_logger.error.assert_called()

    def test_batch_classify_progress_logging(self, classifier):
        """Test progress logging bij batch."""
        definitions = [(f"term_{i}", f"def_{i}") for i in range(25)]

        with patch("src.services.ufo_classifier_service.logger") as mock_logger:
            results = classifier.batch_classify(definitions)

            assert len(results) == 25
            # Progress wordt gelogd bij 10, 20
            assert mock_logger.info.call_count >= 2

    def test_batch_classify_empty(self, classifier):
        """Test met lege batch."""
        results = classifier.batch_classify([])
        assert results == []

    def test_batch_classify_performance(self, classifier):
        """Test batch performance."""
        definitions = [(f"term_{i}", f"definitie {i}") for i in range(50)]

        start = time.perf_counter()
        results = classifier.batch_classify(definitions)
        duration = time.perf_counter() - start

        assert len(results) == 50
        # Batch moet efficiënt zijn
        avg_time = (duration / 50) * 1000
        assert avg_time < 100, f"Batch avg {avg_time:.1f}ms per item"


class TestJuridicalDomain:
    """Test met Nederlandse juridische termen."""

    @pytest.fixture
    def classifier(self):
        return UFOClassifierService()

    def test_strafrechtelijke_termen(self, classifier):
        """Test strafrechtelijke termen."""
        test_cases = [
            ("verdachte", "Persoon die wordt verdacht", UFOCategory.ROLE),
            ("arrestatie", "Het aanhouden tijdens onderzoek", UFOCategory.EVENT),
            ("officier", "De officier van justitie", UFOCategory.ROLE),
            ("dagvaarding", "Oproep voor de rechter", UFOCategory.EVENT),
        ]

        for term, definition, expected in test_cases:
            result = classifier.classify(term, definition)
            assert (
                result.primary_category == expected
            ), f"{term} verwacht {expected}, kreeg {result.primary_category}"

    def test_bestuursrechtelijke_termen(self, classifier):
        """Test bestuursrechtelijke termen."""
        test_cases = [
            ("beschikking", "Besluit van bestuursorgaan", UFOCategory.KIND),
            ("bezwaarprocedure", "Procedure tegen besluit", UFOCategory.EVENT),
            ("vergunning", "Toestemming voor handeling", UFOCategory.RELATOR),
        ]

        for term, definition, expected in test_cases:
            result = classifier.classify(term, definition)
            # Flexibel voor ambigue termen
            if term == "vergunning":
                assert result.primary_category in [
                    UFOCategory.RELATOR,
                    UFOCategory.EVENT,
                ]
            else:
                assert result.primary_category == expected

    def test_civielrechtelijke_termen(self, classifier):
        """Test civielrechtelijke termen."""
        test_cases = [
            ("koopovereenkomst", "Contract tussen partijen", UFOCategory.RELATOR),
            ("eigenaar", "Persoon met eigendomsrecht", UFOCategory.ROLE),
            ("schadevergoeding", "Bedrag van 5000 euro", UFOCategory.QUANTITY),
        ]

        for term, definition, expected in test_cases:
            result = classifier.classify(term, definition)
            assert result.primary_category == expected


class TestFallbackBehavior:
    """Test fallback gedrag."""

    @pytest.fixture
    def classifier(self):
        return UFOClassifierService()

    def test_fallback_no_patterns(self, classifier):
        """Test fallback als geen patterns matchen."""
        result = classifier.classify("xyz", "abc def ghi")

        # Should fallback to KIND
        assert result.primary_category == UFOCategory.KIND
        assert result.confidence == 0.3  # Low confidence

    def test_fallback_event_keyword(self, classifier):
        """Test fallback met EVENT keywords."""
        result = classifier.classify("xyz", "Dit gebeurt tijdens het proces")

        assert result.primary_category == UFOCategory.EVENT

    def test_fallback_role_keyword(self, classifier):
        """Test fallback met ROLE keywords."""
        result = classifier.classify("xyz", "De eigenaar van het pand")

        assert result.primary_category == UFOCategory.ROLE

    def test_fallback_relator_keyword(self, classifier):
        """Test fallback met RELATOR keywords."""
        result = classifier.classify("xyz", "Het contract tussen partijen")

        assert result.primary_category == UFOCategory.RELATOR

    def test_fallback_quantity_pattern(self, classifier):
        """Test fallback met QUANTITY pattern."""
        result = classifier.classify("xyz", "Een bedrag van 100 euro")

        assert result.primary_category == UFOCategory.QUANTITY


class TestEdgeCases:
    """Test edge cases."""

    @pytest.fixture
    def classifier(self):
        return UFOClassifierService()

    def test_special_characters(self, classifier):
        """Test met speciale karakters."""
        test_cases = ["test-term", "test_term", "test.term", "test@term", "test#term"]

        for term in test_cases:
            result = classifier.classify(term, "Een test definitie")
            assert result is not None
            assert result.term == term

    def test_unicode_characters(self, classifier):
        """Test met Unicode karakters."""
        test_cases = [
            ("café", "Een établissement"),
            ("naïef", "Een eigenschap"),
            ("€100", "Een bedrag"),
            ("测试", "Chinese test"),
        ]

        for term, definition in test_cases:
            result = classifier.classify(term, definition)
            assert result is not None

    def test_numeric_terms(self, classifier):
        """Test met numerieke termen."""
        result = classifier.classify("123", "Een nummer")
        assert result is not None
        assert result.primary_category == UFOCategory.KIND  # Default

    def test_mixed_language(self, classifier):
        """Test met gemengde taal."""
        result = classifier.classify(
            "software", "Een computer programma voor processing"
        )
        assert result is not None

    def test_very_short_definition(self, classifier):
        """Test met zeer korte definitie."""
        result = classifier.classify("test", "X")
        assert result is not None


class TestIntegration:
    """Test integratie functies."""

    def test_singleton_pattern(self):
        """Test singleton pattern."""
        classifier1 = get_ufo_classifier()
        classifier2 = get_ufo_classifier()

        assert classifier1 is classifier2
        assert isinstance(classifier1, UFOClassifierService)

    @patch("src.services.ufo_classifier_service._classifier_instance", None)
    def test_singleton_initialization(self):
        """Test singleton initialisatie."""
        from src.services import ufo_classifier_service

        ufo_classifier_service._classifier_instance = None

        classifier = get_ufo_classifier()
        assert classifier is not None
        assert ufo_classifier_service._classifier_instance is classifier

    def test_create_ufo_classifier_service(self):
        """Test factory functie."""
        with patch("pathlib.Path.exists", return_value=False):
            classifier = create_ufo_classifier_service()
            assert isinstance(classifier, UFOClassifierService)

    def test_create_with_existing_config(self, tmp_path):
        """Test factory met bestaande config."""
        config_file = tmp_path / "ufo_classifier.yaml"
        config_file.write_text("high_confidence: 0.95")

        with patch("pathlib.Path", return_value=config_file):
            with patch("pathlib.Path.exists", return_value=True):
                classifier = create_ufo_classifier_service()
                assert classifier.config["high_confidence"] == 0.95


class TestCompleteWorkflow:
    """Test complete workflow scenarios."""

    @pytest.fixture
    def classifier(self):
        return UFOClassifierService()

    def test_juridical_workflow(self, classifier):
        """Test complete juridische classificatie workflow."""
        # Stap 1: Classificeer verschillende typen
        terms = [
            ("rechtspersoon", "Een juridische entiteit", UFOCategory.KIND),
            ("dagvaarding", "Oproep tijdens procedure", UFOCategory.EVENT),
            ("verdachte", "Persoon in hoedanigheid van", UFOCategory.ROLE),
            ("koopovereenkomst", "Contract tussen partijen", UFOCategory.RELATOR),
        ]

        for term, definition, expected in terms:
            result = classifier.classify(term, definition)

            # Verifieer correcte classificatie
            assert result.primary_category == expected
            assert result.confidence > 0.3
            assert result.explanation
            assert result.classification_time_ms < 500

    def test_ambiguous_terms_workflow(self, classifier):
        """Test workflow met ambigue termen."""
        # Test verschillende contexten voor "zaak"
        contexts = [
            ("Een rechtszaak voor de rechter", UFOCategory.EVENT),
            ("Een roerende zaak", UFOCategory.KIND),
        ]

        for definition, expected in contexts:
            result = classifier.classify("zaak", definition)
            assert result.primary_category == expected

    def test_batch_workflow(self, classifier):
        """Test batch processing workflow."""
        # Voorbereid diverse definities
        definitions = [
            ("persoon", "Een natuurlijk persoon"),
            ("proces", "Een juridisch proces"),
            ("contract", "Overeenkomst tussen partijen"),
            ("bedrag", "Som van 1000 euro"),
            ("commissie", "Groep van experts"),
        ]

        results = classifier.batch_classify(definitions)

        # Verifieer resultaten
        assert len(results) == 5
        assert results[0].primary_category == UFOCategory.KIND
        assert results[1].primary_category == UFOCategory.EVENT
        assert results[2].primary_category == UFOCategory.RELATOR
        assert results[3].primary_category == UFOCategory.QUANTITY
        assert results[4].primary_category == UFOCategory.COLLECTIVE

        # Check confidence distribution
        confidences = [r.confidence for r in results]
        assert all(0.0 <= c <= 1.0 for c in confidences)
        assert sum(c > 0.3 for c in confidences) >= 3


class TestPerformanceRequirements:
    """Test performance requirements."""

    @pytest.fixture
    def classifier(self):
        return UFOClassifierService()

    def test_single_classification_under_100ms(self, classifier):
        """Test dat enkele classificatie < 100ms duurt."""
        # Warmup
        classifier.classify("test", "test")

        times = []
        for _ in range(20):
            time.perf_counter()
            result = classifier.classify("persoon", "Een natuurlijk persoon")
            duration = result.classification_time_ms
            times.append(duration)

        avg_time = sum(times) / len(times)
        assert avg_time < 100, f"Avg {avg_time:.1f}ms > 100ms"
        assert max(times) < 500, f"Max {max(times):.1f}ms > 500ms"

    def test_batch_performance_scaling(self, classifier):
        """Test dat batch processing efficiënt schaalt."""
        sizes = [10, 50, 100]

        for size in sizes:
            definitions = [(f"term_{i}", f"def_{i}") for i in range(size)]

            start = time.perf_counter()
            classifier.batch_classify(definitions)
            duration = time.perf_counter() - start

            avg_per_item = (duration / size) * 1000
            assert avg_per_item < 100, f"Size {size}: {avg_per_item:.1f}ms per item"


if __name__ == "__main__":
    """Run tests met coverage report."""
    pytest.main(
        [
            __file__,
            "-v",
            "--tb=short",
            "--cov=src.services.ufo_classifier_service",
            "--cov-report=term-missing",
            "--cov-report=html:coverage_ufo_classifier",
        ]
    )
