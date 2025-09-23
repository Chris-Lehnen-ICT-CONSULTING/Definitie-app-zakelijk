"""
Unit tests voor UFO Classifier Service.

Test de automatische classificatie van begrippen volgens UFO/OntoUML categorieën.
"""

import pytest
from unittest.mock import MagicMock, patch

from src.services.ufo_classifier_service import (
    UFOCategory,
    UFOClassificationResult,
    UFOClassifierService,
    PatternMatcher,
    get_ufo_classifier
)


class TestPatternMatcher:
    """Test de PatternMatcher class."""

    def test_pattern_initialization(self):
        """Test dat patterns correct worden geïnitialiseerd."""
        matcher = PatternMatcher()

        assert UFOCategory.KIND in matcher.patterns
        assert UFOCategory.EVENT in matcher.patterns
        assert UFOCategory.ROLE in matcher.patterns

        # Check dat er daadwerkelijk patterns zijn
        kind_patterns = matcher.patterns[UFOCategory.KIND]
        assert 'core_nouns' in kind_patterns
        assert 'persoon' in kind_patterns['core_nouns']

    def test_pattern_compilation(self):
        """Test dat regex patterns correct worden gecompileerd."""
        matcher = PatternMatcher()

        assert UFOCategory.KIND in matcher.compiled_patterns
        assert hasattr(matcher.compiled_patterns[UFOCategory.KIND], 'findall')

    def test_find_matches_simple(self):
        """Test pattern matching met simpele tekst."""
        matcher = PatternMatcher()
        text = "Een persoon is een natuurlijk mens"

        matches = matcher.find_matches(text)

        assert UFOCategory.KIND in matches
        assert 'persoon' in matches[UFOCategory.KIND]
        assert 'mens' in matches[UFOCategory.KIND]

    def test_find_matches_event(self):
        """Test pattern matching voor events."""
        matcher = PatternMatcher()
        text = "Het proces van arrestatie tijdens het onderzoek"

        matches = matcher.find_matches(text)

        assert UFOCategory.EVENT in matches
        assert 'proces' in matches[UFOCategory.EVENT]
        assert 'tijdens' in matches[UFOCategory.EVENT]
        assert 'onderzoek' in matches[UFOCategory.EVENT]

    def test_find_matches_role(self):
        """Test pattern matching voor rollen."""
        matcher = PatternMatcher()
        text = "De verdachte in de rol van getuige"

        matches = matcher.find_matches(text)

        assert UFOCategory.ROLE in matches
        assert 'verdachte' in matches[UFOCategory.ROLE]
        assert 'in de rol van' in matches[UFOCategory.ROLE]
        assert 'getuige' in matches[UFOCategory.ROLE]

    def test_find_matches_case_insensitive(self):
        """Test dat matching case-insensitive is."""
        matcher = PatternMatcher()
        text = "Een PERSOON is een Natuurlijk MENS"

        matches = matcher.find_matches(text)

        assert UFOCategory.KIND in matches
        assert 'persoon' in matches[UFOCategory.KIND]
        assert 'mens' in matches[UFOCategory.KIND]

    def test_find_matches_caching(self):
        """Test dat resultaten gecached worden."""
        matcher = PatternMatcher()
        text = "Een persoon is een mens"

        # Eerste call
        matches1 = matcher.find_matches(text)
        # Tweede call (zou uit cache moeten komen)
        matches2 = matcher.find_matches(text)

        assert matches1 == matches2


class TestUFOClassifierService:
    """Test de UFOClassifierService class."""

    @pytest.fixture
    def classifier(self):
        """Maak een classifier instance voor tests."""
        return UFOClassifierService()

    def test_initialization(self, classifier):
        """Test dat de service correct wordt geïnitialiseerd."""
        assert classifier.pattern_matcher is not None
        assert classifier.decision_weights is not None
        assert UFOCategory.KIND in classifier.decision_weights

    def test_classify_kind(self, classifier):
        """Test classificatie van KIND categorie."""
        term = "Persoon"
        definition = "Een persoon is een natuurlijk mens met rechtspersoonlijkheid"

        result = classifier.classify(term, definition)

        assert result.primary_category == UFOCategory.KIND
        assert result.confidence > 0.5
        assert len(result.explanation) > 0
        assert 'persoon' in str(result.matched_patterns).lower()

    def test_classify_event(self, classifier):
        """Test classificatie van EVENT categorie."""
        term = "Arrestatie"
        definition = "Het proces waarbij een verdachte tijdens het onderzoek wordt aangehouden"

        result = classifier.classify(term, definition)

        assert result.primary_category == UFOCategory.EVENT
        assert result.confidence > 0.5
        assert 'proces' in str(result.explanation).lower() or 'gebeurtenis' in str(result.explanation).lower()

    def test_classify_role(self, classifier):
        """Test classificatie van ROLE categorie."""
        term = "Verdachte"
        definition = "Een persoon in de hoedanigheid van mogelijke dader van een strafbaar feit"

        result = classifier.classify(term, definition)

        assert result.primary_category == UFOCategory.ROLE
        assert result.confidence > 0.4
        assert any('rol' in exp.lower() or 'hoedanigheid' in exp.lower() for exp in result.explanation)

    def test_classify_relator(self, classifier):
        """Test classificatie van RELATOR categorie."""
        term = "Huwelijk"
        definition = "Een overeenkomst tussen twee personen voor het aangaan van een levensgemeenschap"

        result = classifier.classify(term, definition)

        assert result.primary_category == UFOCategory.RELATOR
        assert result.confidence > 0.4
        assert 'huwelijk' in str(result.matched_patterns).lower() or 'overeenkomst' in str(result.matched_patterns).lower()

    def test_classify_mode(self, classifier):
        """Test classificatie van MODE categorie."""
        term = "Gezondheid"
        definition = "De toestand van fysiek en mentaal welzijn van een persoon"

        result = classifier.classify(term, definition)

        assert result.primary_category == UFOCategory.MODE
        assert result.confidence > 0.3
        assert 'toestand' in str(result.matched_patterns).lower()

    def test_classify_quantity(self, classifier):
        """Test classificatie van QUANTITY categorie."""
        term = "Bedrag"
        definition = "Het aantal euro's dat betaald moet worden"

        result = classifier.classify(term, definition)

        assert result.primary_category in [UFOCategory.QUANTITY, UFOCategory.MODE]
        if result.primary_category == UFOCategory.QUANTITY:
            assert 'euro' in str(result.matched_patterns).lower() or 'aantal' in str(result.matched_patterns).lower()

    def test_classify_quality(self, classifier):
        """Test classificatie van QUALITY categorie."""
        term = "Betrouwbaarheid"
        definition = "De mate waarin iets of iemand te vertrouwen is"

        result = classifier.classify(term, definition)

        assert result.primary_category == UFOCategory.QUALITY
        assert result.confidence > 0.3
        assert 'mate' in str(result.matched_patterns).lower() or 'betrouwbaarheid' in str(result.matched_patterns).lower()

    def test_classify_with_context(self, classifier):
        """Test classificatie met context informatie."""
        term = "Zaak"
        definition = "Een juridische aangelegenheid"
        context = {'domain': 'legal'}

        result = classifier.classify(term, definition, context)

        assert result.primary_category in [UFOCategory.KIND, UFOCategory.EVENT]
        assert result.confidence > 0.2

    def test_classify_unknown(self, classifier):
        """Test classificatie van onbekende termen."""
        term = "XYZ123"
        definition = "Een compleet onbekend begrip zonder herkenbare patronen qwerty"

        result = classifier.classify(term, definition)

        assert result.primary_category == UFOCategory.UNKNOWN
        assert result.confidence < 0.3

    def test_secondary_tags(self, classifier):
        """Test detectie van secundaire tags."""
        term = "Type persoon"
        definition = "Een abstract type dat verschillende soorten personen beschrijft"

        result = classifier.classify(term, definition)

        assert len(result.secondary_tags) > 0
        assert UFOCategory.ABSTRACT in result.secondary_tags or UFOCategory.SUBKIND in result.secondary_tags

    def test_confidence_levels(self, classifier):
        """Test verschillende confidence niveaus."""
        # Hoge confidence
        result1 = classifier.classify(
            "Rechtspersoon",
            "Een juridische entiteit met rechtspersoonlijkheid"
        )
        assert result1.confidence > 0.6

        # Lage confidence
        result2 = classifier.classify(
            "Iets",
            "Een vage omschrijving"
        )
        assert result2.confidence < 0.5

    def test_explanation_generation(self, classifier):
        """Test dat uitleg correct wordt gegenereerd."""
        term = "Contract"
        definition = "Een overeenkomst tussen partijen"

        result = classifier.classify(term, definition)

        assert len(result.explanation) >= 2
        assert any('zekerheid' in exp.lower() for exp in result.explanation)
        assert any('overeenkomst' in exp.lower() or 'contract' in exp.lower() or 'relatie' in exp.lower()
                   for exp in result.explanation)

    def test_batch_classify(self, classifier):
        """Test batch classificatie."""
        items = [
            ("Persoon", "Een natuurlijk mens", None),
            ("Proces", "Een gebeurtenis die plaatsvindt", None),
            ("Verdachte", "Iemand in de rol van mogelijke dader", {'domain': 'legal'})
        ]

        results = classifier.batch_classify(items)

        assert len(results) == 3
        assert results[0].primary_category == UFOCategory.KIND
        assert results[1].primary_category == UFOCategory.EVENT
        assert results[2].primary_category == UFOCategory.ROLE

    def test_batch_classify_with_error(self, classifier):
        """Test batch classificatie met fout handling."""
        items = [
            ("Persoon", "Een natuurlijk mens", None),
            (None, None, None),  # Dit zou een error moeten geven
            ("Proces", "Een gebeurtenis", None)
        ]

        results = classifier.batch_classify(items)

        assert len(results) == 3
        assert results[0].primary_category == UFOCategory.KIND
        assert results[1].primary_category == UFOCategory.UNKNOWN
        assert results[1].confidence == 0.0
        assert results[2].primary_category == UFOCategory.EVENT

    def test_get_category_examples(self, classifier):
        """Test ophalen van voorbeelden per categorie."""
        examples = classifier.get_category_examples(UFOCategory.KIND)

        assert isinstance(examples, dict)
        assert 'core_nouns' in examples
        assert 'legal_entities' in examples
        assert len(examples['core_nouns']) <= 5  # Max 5 voorbeelden

    def test_explain_classification(self, classifier):
        """Test uitgebreide uitleg generatie."""
        term = "Contract"
        definition = "Een overeenkomst tussen twee partijen"

        result = classifier.classify(term, definition)
        explanation = classifier.explain_classification(result)

        assert isinstance(explanation, str)
        assert 'UFO Categorie:' in explanation
        assert 'Zekerheid:' in explanation
        assert str(result.primary_category.value) in explanation

    def test_to_dict_serialization(self, classifier):
        """Test serialisatie naar dictionary."""
        term = "Persoon"
        definition = "Een natuurlijk mens"

        result = classifier.classify(term, definition)
        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert 'primary_category' in result_dict
        assert 'confidence' in result_dict
        assert 'explanation' in result_dict
        assert 'secondary_tags' in result_dict
        assert 'matched_patterns' in result_dict

        assert isinstance(result_dict['primary_category'], str)
        assert isinstance(result_dict['confidence'], float)
        assert isinstance(result_dict['explanation'], list)


class TestSingletonPattern:
    """Test de singleton pattern voor de classifier."""

    def test_get_ufo_classifier_singleton(self):
        """Test dat get_ufo_classifier een singleton retourneert."""
        classifier1 = get_ufo_classifier()
        classifier2 = get_ufo_classifier()

        assert classifier1 is classifier2

    def test_singleton_initialization(self):
        """Test dat de singleton correct wordt geïnitialiseerd."""
        # Reset de global instance
        import src.services.ufo_classifier_service as module
        module._classifier_instance = None

        classifier = get_ufo_classifier()

        assert classifier is not None
        assert isinstance(classifier, UFOClassifierService)


class TestPerformance:
    """Performance tests voor de classifier."""

    def test_classification_speed(self):
        """Test dat classificatie snel genoeg is."""
        import time

        classifier = UFOClassifierService()
        term = "Persoon"
        definition = "Een natuurlijk mens met rechtspersoonlijkheid"

        # Warm up (eerste call kan trager zijn)
        classifier.classify(term, definition)

        # Measure
        start = time.time()
        for _ in range(100):
            classifier.classify(term, definition)
        duration = time.time() - start

        # Should be less than 1 second for 100 classifications
        assert duration < 1.0, f"100 classificaties duurde {duration:.2f} seconden"

    def test_batch_performance(self):
        """Test batch processing performance."""
        import time

        classifier = UFOClassifierService()
        items = [
            (f"Term{i}", f"Definitie {i} met wat tekst", None)
            for i in range(100)
        ]

        start = time.time()
        results = classifier.batch_classify(items)
        duration = time.time() - start

        assert len(results) == 100
        assert duration < 2.0, f"100 batch classificaties duurde {duration:.2f} seconden"

    def test_caching_effectiveness(self):
        """Test dat caching werkt voor herhaalde calls."""
        import time

        classifier = UFOClassifierService()
        text = "Een persoon is een natuurlijk mens"

        # Eerste call
        start1 = time.time()
        classifier.pattern_matcher.find_matches(text)
        duration1 = time.time() - start1

        # Tweede call (cached)
        start2 = time.time()
        classifier.pattern_matcher.find_matches(text)
        duration2 = time.time() - start2

        # Cached call zou sneller moeten zijn
        assert duration2 <= duration1


class TestEdgeCases:
    """Test edge cases en speciale situaties."""

    def test_empty_input(self):
        """Test met lege input."""
        classifier = UFOClassifierService()

        result = classifier.classify("", "")

        assert result.primary_category == UFOCategory.UNKNOWN
        assert result.confidence < 0.3

    def test_very_long_input(self):
        """Test met zeer lange input."""
        classifier = UFOClassifierService()
        long_text = " ".join(["Een persoon is een natuurlijk mens"] * 100)

        result = classifier.classify("Persoon", long_text)

        assert result.primary_category == UFOCategory.KIND
        assert result.confidence > 0.5

    def test_special_characters(self):
        """Test met speciale karakters."""
        classifier = UFOClassifierService()

        result = classifier.classify(
            "Test@#$%",
            "Een definitie met speciale !@#$%^&*() karakters"
        )

        assert result.primary_category in [UFOCategory.UNKNOWN, UFOCategory.KIND]

    def test_mixed_languages(self):
        """Test met gemixte talen."""
        classifier = UFOClassifierService()

        result = classifier.classify(
            "Person",
            "A person is een natuurlijk mens with rights"
        )

        # Zou nog steeds moeten werken op Nederlandse termen
        assert result.primary_category == UFOCategory.KIND

    def test_numeric_input(self):
        """Test met numerieke input."""
        classifier = UFOClassifierService()

        result = classifier.classify(
            "100",
            "Het aantal van 100 euro"
        )

        assert result.primary_category in [UFOCategory.QUANTITY, UFOCategory.MODE]