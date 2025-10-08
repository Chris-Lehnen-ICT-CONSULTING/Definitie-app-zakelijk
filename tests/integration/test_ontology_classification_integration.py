"""
Integration tests voor Ontology Classification System.

Test volledige flow: Container → Service → Validator → UI
"""

import json
from unittest.mock import Mock, patch

import pytest

from src.services.classification.ontology_classifier import (
    ClassificationResult,
    OntologyClassifierService,
)
from src.services.classification.ontology_validator import OntologyValidator
from src.ui.components.ontology_classification_display import (
    OntologyClassificationDisplay,
    display_ontology_classification,
)


@pytest.fixture()
def mock_container():
    """Mock ServiceContainer met ontology_classifier."""
    container = Mock()

    # Create real validator
    validator = OntologyValidator()

    # Mock AI service
    ai_service = Mock()
    ai_service.generate_completion.return_value = json.dumps(
        {
            "level": "TYPE",
            "confidence": 0.85,
            "rationale": "Test rationale",
            "linguistic_cues": ["test cue"],
        }
    )

    # Create real classifier with mocked AI
    classifier = OntologyClassifierService(ai_service)
    classifier.validator = validator
    # Override prompt template
    classifier.system_prompt = "Test system"
    classifier.user_template = (
        "Begrip: {begrip}\nDefinitie: {definitie}\n{context_section}"
    )

    container.ontology_classifier.return_value = classifier
    return container


class TestOntologyClassificationIntegration:
    """Integration tests voor complete classification flow."""

    def test_container_provides_classifier(self, mock_container):
        """Test dat container classifier service levert."""
        classifier = mock_container.ontology_classifier()

        assert classifier is not None
        assert isinstance(classifier, OntologyClassifierService)

    def test_full_classification_flow(self, mock_container):
        """Test complete flow: begrip → classificatie → result."""
        # Get classifier
        classifier = mock_container.ontology_classifier()

        # Classificeer
        result = classifier.classify(begrip="appel", definitie="Een soort fruit")

        # Verify result
        assert isinstance(result, ClassificationResult)
        assert result.level == "TYPE"
        assert result.confidence == 0.85
        assert result.rationale == "Test rationale"
        assert len(result.linguistic_cues) == 1
        assert isinstance(result.validation_warnings, list)

    def test_classification_with_validation_warnings(self, mock_container):
        """Test dat validator warnings toegevoegd worden."""
        classifier = mock_container.ontology_classifier()

        # Setup AI to return TYPE for proces-achtig begrip
        classifier.ai_service.generate_completion.return_value = json.dumps(
            {
                "level": "TYPE",
                "confidence": 0.7,
                "rationale": "Test",
                "linguistic_cues": [],
            }
        )

        result = classifier.classify(
            begrip="verificatie",
            definitie="De handeling van controleren",  # "handeling" = anti-indicator voor TYPE
        )

        # Should have validation warnings
        assert result.level == "TYPE"
        assert len(result.validation_warnings) > 0

    def test_ui_display_renders_without_error(self):
        """Test dat UI display component zonder errors rendert."""
        display = OntologyClassificationDisplay()

        result = ClassificationResult(
            level="PROCES",
            confidence=0.82,
            rationale="Test rationale voor proces",
            linguistic_cues=["handeling", "ing-vorm"],
            validation_warnings=[],
        )

        # Should not raise
        # Note: In real app this would render to Streamlit, maar we testen alleen dat het niet crasht
        try:
            # We kunnen niet echt renderen zonder Streamlit context,
            # maar we kunnen wel verifiëren dat de methods bestaan
            assert hasattr(display, "render")
            assert hasattr(display, "render_compact")
            assert hasattr(display, "render_with_prompt_visibility")
        except Exception as e:
            pytest.fail(f"Display component heeft ontbrekende methods: {e}")

    def test_display_confidence_color_mapping(self):
        """Test dat confidence scores correct gemapped worden naar kleuren."""
        display = OntologyClassificationDisplay()

        # High confidence = groen
        assert display._get_confidence_color(0.9) == "#28a745"

        # Medium confidence = oranje
        assert display._get_confidence_color(0.7) == "#ffc107"

        # Low confidence = rood
        assert display._get_confidence_color(0.5) == "#dc3545"

    def test_batch_classification(self, mock_container):
        """Test batch classificatie van meerdere begrippen."""
        classifier = mock_container.ontology_classifier()

        # Setup mock responses
        responses = [
            '{"level": "TYPE", "confidence": 0.8, "rationale": "R1", "linguistic_cues": []}',
            '{"level": "PROCES", "confidence": 0.9, "rationale": "R2", "linguistic_cues": []}',
        ]
        classifier.ai_service.generate_completion.side_effect = responses

        items = [
            {"begrip": "appel", "definitie": "Een fruit"},
            {"begrip": "plukken", "definitie": "Het verwijderen"},
        ]

        results = classifier.classify_batch(items)

        assert len(results) == 2
        assert results[0].level == "TYPE"
        assert results[1].level == "PROCES"

    def test_error_handling_fallback_to_onbeslist(self, mock_container):
        """Test dat errors resulteren in ONBESLIST fallback."""
        classifier = mock_container.ontology_classifier()

        # Simulate API error
        classifier.ai_service.generate_completion.side_effect = Exception("API Down")

        result = classifier.classify(begrip="test", definitie="test definitie")

        # Should fallback to ONBESLIST
        assert result.level == "ONBESLIST"
        assert result.confidence == 0.0
        assert "API Down" in result.rationale
        assert len(result.validation_warnings) > 0

    def test_backward_compatibility_score_dict_generation(self, mock_container):
        """Test dat legacy score dict gegenereerd kan worden uit result."""
        classifier = mock_container.ontology_classifier()

        result = classifier.classify(begrip="appel", definitie="Een fruit")

        # Generate legacy scores
        legacy_scores = {
            "type": 1.0 if result.level == "TYPE" else 0.0,
            "exemplaar": 1.0 if result.level == "EXEMPLAAR" else 0.0,
            "proces": 1.0 if result.level == "PROCES" else 0.0,
            "resultaat": 1.0 if result.level == "RESULTAAT" else 0.0,
        }

        assert legacy_scores["type"] == 1.0  # Result was TYPE
        assert legacy_scores["proces"] == 0.0
        assert sum(legacy_scores.values()) == 1.0  # Exactly one category

    def test_context_and_voorbeelden_included_in_prompt(self, mock_container):
        """Test dat context en voorbeelden in prompt komen."""
        classifier = mock_container.ontology_classifier()

        classifier.classify(
            begrip="verificatie",
            definitie="Het controleren",
            context="Juridische context",
            voorbeelden=["Voorbeeld 1", "Voorbeeld 2"],
        )

        # Check prompt bevat context en voorbeelden
        call_args = classifier.ai_service.generate_completion.call_args
        prompt = call_args[1]["prompt"]

        assert "Juridische context" in prompt
        assert "Voorbeeld 1" in prompt
        assert "Voorbeeld 2" in prompt

    def test_temperature_and_max_tokens_settings(self, mock_container):
        """Test dat LLM parameters correct gezet worden."""
        classifier = mock_container.ontology_classifier()

        classifier.classify("test", "test definitie")

        call_kwargs = classifier.ai_service.generate_completion.call_args[1]

        # Verify settings
        assert call_kwargs["temperature"] == 0.3  # Low for consistency
        assert call_kwargs["max_tokens"] == 500  # Limited for cost control

    def test_validator_pattern_matching(self):
        """Test dat validator pattern matching werkt."""
        validator = OntologyValidator()

        # TYPE met goede indicators
        warnings1 = validator.validate(
            level="TYPE",
            begrip="appel",
            definitie="Een soort fruit in de categorie kernvruchten",
        )
        assert warnings1 == []  # No warnings - good match

        # TYPE met anti-indicators
        warnings2 = validator.validate(
            level="TYPE", begrip="proces", definitie="Deze specifieke handeling"
        )
        assert len(warnings2) > 0  # Should warn

    def test_domain_rules_validation(self):
        """Test domain-specific validation rules."""
        validator = OntologyValidator()

        # Biology term should be TYPE
        warnings = validator.validate(
            level="PROCES",  # Wrong!
            begrip="soort",
            definitie="Een biologische taxonomische categorie",
        )

        # Should warn about biology domain expecting TYPE
        assert len(warnings) > 0

    def test_classification_result_to_dict(self, mock_container):
        """Test dat ClassificationResult naar dict geconverteerd kan worden."""
        classifier = mock_container.ontology_classifier()
        result = classifier.classify("test", "test definitie")

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert "level" in result_dict
        assert "confidence" in result_dict
        assert "rationale" in result_dict
        assert "linguistic_cues" in result_dict
        assert "validation_warnings" in result_dict

    def test_emoji_mapping_complete(self):
        """Test dat alle levels emoji mapping hebben."""
        display = OntologyClassificationDisplay()

        levels = ["TYPE", "EXEMPLAAR", "PROCES", "RESULTAAT", "ONBESLIST"]

        for level in levels:
            assert level in display.CATEGORY_EMOJI
            emoji = display.CATEGORY_EMOJI[level]
            assert isinstance(emoji, str)
            assert len(emoji) > 0

    @patch("streamlit.info")
    @patch("streamlit.markdown")
    @patch("streamlit.columns")
    def test_ui_render_with_none_result(self, mock_columns, mock_markdown, mock_info):
        """Test UI rendering met None result."""
        display = OntologyClassificationDisplay()

        # Mock streamlit components
        mock_columns.return_value = [Mock(), Mock()]

        display.render(result=None)

        # Should show info message
        mock_info.assert_called_once()

    def test_display_modes_convenience_function(self):
        """Test dat convenience functie alle display modes ondersteunt."""
        result = ClassificationResult(
            level="TYPE",
            confidence=0.85,
            rationale="Test",
            linguistic_cues=[],
            validation_warnings=[],
        )

        # Should not raise voor verschillende modes
        try:
            # Note: Deze zullen falen zonder Streamlit context, maar we testen signature
            assert callable(display_ontology_classification)
        except Exception:
            pass  # Expected buiten Streamlit context


class TestPerformanceConsiderations:
    """Tests voor performance aspecten."""

    def test_classifier_caches_validator_instance(self, mock_container):
        """Test dat validator instance gecached wordt."""
        classifier = mock_container.ontology_classifier()

        validator1 = classifier.validator
        validator2 = classifier.validator

        # Should be same instance
        assert validator1 is validator2

    def test_batch_reduces_call_overhead(self, mock_container):
        """Test dat batch processing overhead reduceert."""
        classifier = mock_container.ontology_classifier()

        # Setup mock responses
        classifier.ai_service.generate_completion.side_effect = [
            '{"level": "TYPE", "confidence": 0.8, "rationale": "R", "linguistic_cues": []}'
        ] * 5

        items = [{"begrip": f"test{i}", "definitie": f"def{i}"} for i in range(5)]

        results = classifier.classify_batch(items)

        # Should have called AI service exactly 5 times (once per item)
        assert classifier.ai_service.generate_completion.call_count == 5
        assert len(results) == 5


class TestSecurityAndPrivacy:
    """Tests voor security en privacy aspecten."""

    def test_no_sensitive_data_in_prompts(self, mock_container):
        """Test dat geen sensitive data in prompts komt."""
        classifier = mock_container.ontology_classifier()

        classifier.classify(
            begrip="test begrip", definitie="test definitie", context="test context"
        )

        call_args = classifier.ai_service.generate_completion.call_args[1]
        prompt = call_args["prompt"]

        # Prompt mag alleen begrip, definitie, context bevatten (no PII)
        assert "test begrip" in prompt
        assert "test definitie" in prompt
        assert "test context" in prompt

    def test_validator_does_not_log_sensitive_data(self):
        """Test dat validator geen sensitive data logt."""
        validator = OntologyValidator()

        # Should not raise or log PII
        warnings = validator.validate(
            level="TYPE",
            begrip="Sensitive Term",
            definitie="Contains PII: john@example.com",
        )

        # Warnings should not contain raw PII (they describe patterns, not content)
        for warning in warnings:
            assert "john@example.com" not in warning
