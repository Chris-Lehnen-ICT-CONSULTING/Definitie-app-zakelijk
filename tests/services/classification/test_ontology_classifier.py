"""
Unit tests voor OntologyClassifierService.

Test LLM-based classificatie met mocking van AI service.
"""

import json
from unittest.mock import MagicMock, Mock

import pytest

from src.services.ai_service_v2 import AIServiceV2
from src.services.classification.ontology_classifier import (
    ClassificationResult,
    OntologyClassifierService,
    OntologyLevel,
)


@pytest.fixture()
def mock_ai_service():
    """Mock AI service die JSON responses teruggeeft."""
    # Geen spec zodat we attributes kunnen toevoegen
    service = Mock()
    return service


@pytest.fixture()
def classifier(mock_ai_service):
    """Classifier instance met mocked AI service."""
    classifier = OntologyClassifierService(mock_ai_service)
    # Override prompt loading voor tests
    classifier.system_prompt = "Test system prompt"
    classifier.user_template = (
        "Begrip: {begrip}\nDefinitie: {definitie}\n{context_section}"
    )
    return classifier


class TestOntologyClassifierService:
    """Tests voor OntologyClassifierService."""

    def test_init_loads_prompt_template(self, mock_ai_service, tmp_path):
        """Test dat initialisatie prompt template laadt."""
        # Create temp prompt file
        prompt_file = tmp_path / "test_prompt.yaml"
        prompt_file.write_text(
            """
system: "Test system"
user_template: "Test template {begrip}"
"""
        )

        # Mock prompt path
        original_path = OntologyClassifierService.PROMPT_PATH
        OntologyClassifierService.PROMPT_PATH = prompt_file

        try:
            classifier = OntologyClassifierService(mock_ai_service)
            assert classifier.system_prompt == "Test system"
            assert "Test template" in classifier.user_template
        finally:
            OntologyClassifierService.PROMPT_PATH = original_path

    def test_classify_type_successful(self, classifier, mock_ai_service):
        """Test succesvolle TYPE classificatie."""
        # Setup mock response
        mock_response = {
            "level": "TYPE",
            "confidence": 0.85,
            "rationale": "Dit begrip beschrijft een algemene categorie",
            "linguistic_cues": ["algemene categorie", "soort"],
        }
        mock_ai_service.generate_completion.return_value = json.dumps(mock_response)

        # Execute
        result = classifier.classify(begrip="appel", definitie="Een soort fruit")

        # Assert
        assert isinstance(result, ClassificationResult)
        assert result.level == "TYPE"
        assert result.confidence == 0.85
        assert "algemene categorie" in result.rationale
        assert len(result.linguistic_cues) == 2
        assert result.validation_warnings == []  # No validation warnings

    def test_classify_proces_with_context(self, classifier, mock_ai_service):
        """Test PROCES classificatie met context."""
        mock_response = {
            "level": "PROCES",
            "confidence": 0.92,
            "rationale": "Beschrijft een handeling of activiteit",
            "linguistic_cues": ["handeling", "ing-vorm", "werkwoord"],
        }
        mock_ai_service.generate_completion.return_value = json.dumps(mock_response)

        result = classifier.classify(
            begrip="verifiëren",
            definitie="Het controleren van de juistheid",
            context="Juridische procedures",
            voorbeelden=["Het verifiëren van identiteit"],
        )

        assert result.level == "PROCES"
        assert result.confidence == 0.92
        # Verify context was included in prompt
        call_args = mock_ai_service.generate_completion.call_args
        assert "Juridische procedures" in call_args[1]["prompt"]
        assert "verifiëren van identiteit" in call_args[1]["prompt"]

    def test_classify_onbeslist_low_confidence(self, classifier, mock_ai_service):
        """Test ONBESLIST classificatie bij lage confidence."""
        mock_response = {
            "level": "ONBESLIST",
            "confidence": 0.3,
            "rationale": "Begrip is niet eenduidig te classificeren",
            "linguistic_cues": ["ambigue", "meerdere interpretaties"],
        }
        mock_ai_service.generate_completion.return_value = json.dumps(mock_response)

        result = classifier.classify(
            begrip="systeem", definitie="Een geheel van onderdelen"
        )

        assert result.level == "ONBESLIST"
        assert result.confidence == 0.3

    def test_classify_with_validation_warnings(self, classifier, mock_ai_service):
        """Test classificatie die validatie warnings triggert."""
        # Mock LLM response: TYPE classificatie voor proces-achtig begrip
        mock_response = {
            "level": "TYPE",
            "confidence": 0.7,
            "rationale": "Beschrijft een categorie",
            "linguistic_cues": ["algemeen"],
        }
        mock_ai_service.generate_completion.return_value = json.dumps(mock_response)

        result = classifier.classify(
            begrip="verificatie",  # Klinkt als PROCES
            definitie="Het proces van controleren",
        )

        # Validator should detect anti-indicator "proces"
        assert result.level == "TYPE"
        assert len(result.validation_warnings) > 0
        assert any("proces" in w.lower() for w in result.validation_warnings)

    def test_parse_llm_response_valid_json(self, classifier):
        """Test parsing van valide JSON response."""
        response = """
        {
            "level": "EXEMPLAAR",
            "confidence": 0.75,
            "rationale": "Test",
            "linguistic_cues": ["cue1"]
        }
        """

        result = classifier._parse_llm_response(response)
        assert result["level"] == "EXEMPLAAR"
        assert result["confidence"] == 0.75

    def test_parse_llm_response_with_markdown_wrapper(self, classifier):
        """Test parsing van JSON in markdown code block."""
        response = """```json
        {
            "level": "RESULTAAT",
            "confidence": 0.88,
            "rationale": "Test",
            "linguistic_cues": []
        }
        ```"""

        result = classifier._parse_llm_response(response)
        assert result["level"] == "RESULTAAT"
        assert result["confidence"] == 0.88

    def test_parse_llm_response_invalid_json_raises_error(self, classifier):
        """Test dat ongeldige JSON een error geeft."""
        response = "Not valid JSON at all"

        with pytest.raises(ValueError, match="Ongeldige JSON"):
            classifier._parse_llm_response(response)

    def test_parse_llm_response_missing_required_field(self, classifier):
        """Test dat missende vereiste velden gedetecteerd worden."""
        response = '{"level": "TYPE", "confidence": 0.8}'  # Missing 'rationale'

        with pytest.raises(ValueError, match="Ontbrekend veld"):
            classifier._parse_llm_response(response)

    def test_parse_llm_response_invalid_level_value(self, classifier):
        """Test dat ongeldige level waarde rejected wordt."""
        response = """
        {
            "level": "INVALID_LEVEL",
            "confidence": 0.8,
            "rationale": "Test"
        }
        """

        with pytest.raises(ValueError, match="Ongeldige level"):
            classifier._parse_llm_response(response)

    def test_parse_llm_response_confidence_out_of_range(self, classifier):
        """Test dat confidence buiten range rejected wordt."""
        response = """
        {
            "level": "TYPE",
            "confidence": 1.5,
            "rationale": "Test"
        }
        """

        with pytest.raises(ValueError, match="Confidence buiten range"):
            classifier._parse_llm_response(response)

    def test_classify_api_error_returns_onbeslist(self, classifier, mock_ai_service):
        """Test dat API errors resulteren in ONBESLIST fallback."""
        mock_ai_service.generate_completion.side_effect = Exception("API Error")

        result = classifier.classify(begrip="test", definitie="test definitie")

        assert result.level == "ONBESLIST"
        assert result.confidence == 0.0
        assert "API Error" in result.rationale
        assert len(result.validation_warnings) > 0

    def test_classify_batch(self, classifier, mock_ai_service):
        """Test batch classificatie van meerdere begrippen."""
        # Setup mock responses
        responses = [
            '{"level": "TYPE", "confidence": 0.8, "rationale": "Type 1", "linguistic_cues": []}',
            '{"level": "PROCES", "confidence": 0.9, "rationale": "Proces 1", "linguistic_cues": []}',
            '{"level": "RESULTAAT", "confidence": 0.7, "rationale": "Resultaat 1", "linguistic_cues": []}',
        ]
        mock_ai_service.generate_completion.side_effect = responses

        items = [
            {"begrip": "appel", "definitie": "Een fruit"},
            {"begrip": "plukken", "definitie": "Het verwijderen"},
            {"begrip": "geplukte appel", "definitie": "Resultaat van plukken"},
        ]

        results = classifier.classify_batch(items)

        assert len(results) == 3
        assert results[0].level == "TYPE"
        assert results[1].level == "PROCES"
        assert results[2].level == "RESULTAAT"

    def test_temperature_setting(self, classifier, mock_ai_service):
        """Test dat temperatuur op 0.3 gezet wordt voor consistentie."""
        mock_response = {
            "level": "TYPE",
            "confidence": 0.8,
            "rationale": "Test",
            "linguistic_cues": [],
        }
        mock_ai_service.generate_completion.return_value = json.dumps(mock_response)

        classifier.classify("test", "test definitie")

        # Verify temperature parameter
        call_kwargs = mock_ai_service.generate_completion.call_args[1]
        assert call_kwargs["temperature"] == 0.3

    def test_max_tokens_setting(self, classifier, mock_ai_service):
        """Test dat max_tokens gelimiteerd is."""
        mock_response = {
            "level": "TYPE",
            "confidence": 0.8,
            "rationale": "Test",
            "linguistic_cues": [],
        }
        mock_ai_service.generate_completion.return_value = json.dumps(mock_response)

        classifier.classify("test", "test definitie")

        # Verify max_tokens parameter
        call_kwargs = mock_ai_service.generate_completion.call_args[1]
        assert call_kwargs["max_tokens"] == 500
