"""
Tests voor GPT4SynonymSuggester service.

Test coverage:
- JSON parsing en validation
- Confidence filtering
- Context building
- Retry logic
- Integration met AIServiceV2
"""

from unittest.mock import AsyncMock, Mock

import pytest

from services.ai_service_v2 import AIServiceV2
from services.interfaces import AIGenerationResult, AIServiceError
from services.synonym_automation.gpt4_suggester import (
    GPT4SynonymSuggester,
    SynonymSuggestion,
)


class TestSynonymSuggestion:
    """Tests voor SynonymSuggestion dataclass."""

    def test_synonym_suggestion_creation(self):
        """Test basis synonym suggestion creation."""
        suggestion = SynonymSuggestion(
            hoofdterm="voorlopige hechtenis",
            synoniem="voorarrest",
            confidence=0.95,
            rationale="Juridisch synoniem voor tijdelijke vrijheidsbeneming",
        )

        assert suggestion.hoofdterm == "voorlopige hechtenis"
        assert suggestion.synoniem == "voorarrest"
        assert suggestion.confidence == 0.95
        assert "vrijheidsbeneming" in suggestion.rationale

    def test_synonym_suggestion_to_dict(self):
        """Test conversion to dictionary."""
        suggestion = SynonymSuggestion(
            hoofdterm="verdachte",
            synoniem="beklaagde",
            confidence=0.90,
            rationale="Procesfase-specifiek synoniem",
            context_used={"model": "gpt-4-turbo"},
        )

        result = suggestion.to_dict()

        assert result["hoofdterm"] == "verdachte"
        assert result["synoniem"] == "beklaagde"
        assert result["confidence"] == 0.90
        assert "model" in result["context"]


class TestGPT4SynonymSuggester:
    """Tests voor GPT4SynonymSuggester service."""

    @pytest.fixture()
    def mock_ai_service(self):
        """Create mock AIServiceV2."""
        mock = Mock(spec=AIServiceV2)
        # Make generate_definition an async mock
        mock.generate_definition = AsyncMock()
        return mock

    @pytest.fixture()
    def suggester(self, mock_ai_service):
        """Create GPT4SynonymSuggester with mock AI service."""
        return GPT4SynonymSuggester(
            ai_service=mock_ai_service,
            model="gpt-4-turbo",
            temperature=0.3,
            min_confidence=0.6,
        )

    def test_build_context_section_with_definitie(self, suggester):
        """Test context building met definitie."""
        context = suggester._build_context_section(
            definitie="Tijdelijke vrijheidsbeneming van een verdachte",
            context=None,
        )

        assert "DEFINITIE:" in context
        assert "vrijheidsbeneming" in context

    def test_build_context_section_with_context_list(self, suggester):
        """Test context building met context lijst."""
        context = suggester._build_context_section(
            definitie=None, context=["Sv", "strafrecht", "artikel 63"]
        )

        assert "CONTEXT:" in context
        assert "Sv" in context
        assert "strafrecht" in context

    def test_build_context_section_complete(self, suggester):
        """Test context building met beide parameters."""
        context = suggester._build_context_section(
            definitie="Juridische term voor X",
            context=["Sv", "strafrecht"],
        )

        assert "DEFINITIE:" in context
        assert "CONTEXT:" in context
        assert "Juridische term voor X" in context
        assert "Sv" in context

    def test_parse_json_response_valid(self, suggester):
        """Test JSON parsing met valide response."""
        response = """{
            "synoniemen": [
                {
                    "term": "voorarrest",
                    "confidence": 0.95,
                    "rationale": "Direct juridisch synoniem"
                }
            ]
        }"""

        result = suggester._parse_json_response(response)

        assert "synoniemen" in result
        assert len(result["synoniemen"]) == 1
        assert result["synoniemen"][0]["term"] == "voorarrest"

    def test_parse_json_response_with_markdown(self, suggester):
        """Test JSON parsing met markdown code fences."""
        response = """```json
        {
            "synoniemen": [{"term": "test", "confidence": 0.8, "rationale": "test"}]
        }
        ```"""

        result = suggester._parse_json_response(response)

        assert "synoniemen" in result
        assert len(result["synoniemen"]) == 1

    def test_parse_json_response_invalid(self, suggester):
        """Test JSON parsing met invalide response."""
        response = "This is not valid JSON"

        with pytest.raises(ValueError, match="Invalid JSON"):
            suggester._parse_json_response(response)

    def test_validate_suggestion_valid(self, suggester):
        """Test suggestion validation met valide data."""
        suggestion_data = {
            "term": "voorarrest",
            "confidence": 0.95,
            "rationale": "Direct synoniem",
        }

        assert suggester._validate_suggestion(suggestion_data)

    def test_validate_suggestion_missing_keys(self, suggester):
        """Test suggestion validation met missende keys."""
        suggestion_data = {
            "term": "voorarrest",
            "confidence": 0.95,
            # Missing 'rationale'
        }

        assert not suggester._validate_suggestion(suggestion_data)

    def test_validate_suggestion_invalid_confidence(self, suggester):
        """Test suggestion validation met invalide confidence."""
        suggestion_data = {
            "term": "voorarrest",
            "confidence": 1.5,  # Out of range
            "rationale": "Test",
        }

        assert not suggester._validate_suggestion(suggestion_data)

    def test_validate_suggestion_invalid_types(self, suggester):
        """Test suggestion validation met invalide types."""
        suggestion_data = {
            "term": 123,  # Should be string
            "confidence": 0.95,
            "rationale": "Test",
        }

        assert not suggester._validate_suggestion(suggestion_data)

    @pytest.mark.asyncio()
    async def test_suggest_synonyms_success(self, suggester, mock_ai_service):
        """Test successful synonym generation."""
        # Mock AI response
        mock_response = AIGenerationResult(
            text="""{
                "synoniemen": [
                    {
                        "term": "voorarrest",
                        "confidence": 0.95,
                        "rationale": "Juridisch correct synoniem voor voorlopige hechtenis"
                    },
                    {
                        "term": "bewaring",
                        "confidence": 0.90,
                        "rationale": "Veelgebruikt synoniem in strafrecht"
                    }
                ]
            }""",
            model="gpt-4-turbo",
            tokens_used=250,
            generation_time=1.5,
            cached=False,
            retry_count=0,
        )
        mock_ai_service.generate_definition.return_value = mock_response

        # Test suggest_synonyms
        suggestions = await suggester.suggest_synonyms(
            term="voorlopige hechtenis",
            definitie="Tijdelijke vrijheidsbeneming",
            context=["Sv", "strafrecht"],
        )

        # Verify results
        assert len(suggestions) == 2
        assert all(isinstance(s, SynonymSuggestion) for s in suggestions)
        assert suggestions[0].synoniem == "voorarrest"
        assert suggestions[0].confidence == 0.95
        assert suggestions[1].synoniem == "bewaring"
        assert suggestions[1].confidence == 0.90

        # Verify AI service was called correctly
        mock_ai_service.generate_definition.assert_called_once()
        call_kwargs = mock_ai_service.generate_definition.call_args.kwargs
        assert "voorlopige hechtenis" in call_kwargs["prompt"]
        assert call_kwargs["model"] == "gpt-4-turbo"
        assert call_kwargs["temperature"] == 0.3

    @pytest.mark.asyncio()
    async def test_suggest_synonyms_filters_low_confidence(
        self, suggester, mock_ai_service
    ):
        """Test dat lage confidence suggesties gefilterd worden."""
        mock_response = AIGenerationResult(
            text="""{
                "synoniemen": [
                    {
                        "term": "voorarrest",
                        "confidence": 0.95,
                        "rationale": "Hoge confidence"
                    },
                    {
                        "term": "opsluiting",
                        "confidence": 0.50,
                        "rationale": "Lage confidence - te algemeen"
                    }
                ]
            }""",
            model="gpt-4-turbo",
            tokens_used=200,
            generation_time=1.0,
            cached=False,
            retry_count=0,
        )
        mock_ai_service.generate_definition.return_value = mock_response

        # min_confidence = 0.6, dus 0.50 moet gefilterd worden
        suggestions = await suggester.suggest_synonyms("voorlopige hechtenis")

        assert len(suggestions) == 1
        assert suggestions[0].synoniem == "voorarrest"

    @pytest.mark.asyncio()
    async def test_suggest_synonyms_respects_max_synonyms(
        self, suggester, mock_ai_service
    ):
        """Test dat max_synonyms limit gerespecteerd wordt."""
        # Generate 10 synonyms
        synoniemen_list = [
            {
                "term": f"synoniem_{i}",
                "confidence": 0.90,
                "rationale": f"Rationale {i}",
            }
            for i in range(10)
        ]

        mock_response = AIGenerationResult(
            text='{"synoniemen": ' + str(synoniemen_list).replace("'", '"') + "}",
            model="gpt-4-turbo",
            tokens_used=500,
            generation_time=2.0,
            cached=False,
            retry_count=0,
        )
        mock_ai_service.generate_definition.return_value = mock_response

        # max_synonyms = 8 (default)
        suggestions = await suggester.suggest_synonyms("test term")

        assert len(suggestions) <= 8

    @pytest.mark.asyncio()
    async def test_suggest_synonyms_retry_on_malformed_json(
        self, suggester, mock_ai_service
    ):
        """Test retry logic bij malformed JSON."""
        # First attempt: invalid JSON
        # Second attempt: valid JSON
        mock_ai_service.generate_definition.side_effect = [
            AIGenerationResult(
                text="This is not JSON",
                model="gpt-4-turbo",
                tokens_used=50,
                generation_time=0.5,
                cached=False,
                retry_count=0,
            ),
            AIGenerationResult(
                text="""{
                    "synoniemen": [
                        {
                            "term": "voorarrest",
                            "confidence": 0.95,
                            "rationale": "Success on retry"
                        }
                    ]
                }""",
                model="gpt-4-turbo",
                tokens_used=200,
                generation_time=1.0,
                cached=False,
                retry_count=0,
            ),
        ]

        suggestions = await suggester.suggest_synonyms("voorlopige hechtenis")

        # Should succeed on second attempt
        assert len(suggestions) == 1
        assert suggestions[0].synoniem == "voorarrest"
        assert mock_ai_service.generate_definition.call_count == 2

    @pytest.mark.asyncio()
    async def test_suggest_synonyms_fails_after_max_retries(
        self, suggester, mock_ai_service
    ):
        """Test dat service faalt na max_retries."""
        # All attempts return invalid JSON
        mock_ai_service.generate_definition.return_value = AIGenerationResult(
            text="Not JSON",
            model="gpt-4-turbo",
            tokens_used=50,
            generation_time=0.5,
            cached=False,
            retry_count=0,
        )

        with pytest.raises(ValueError, match="Failed to get valid JSON response"):
            await suggester.suggest_synonyms("test term")

        # Should have tried max_retries times (default: 3)
        assert mock_ai_service.generate_definition.call_count == 3

    @pytest.mark.asyncio()
    async def test_suggest_synonyms_propagates_ai_errors(
        self, suggester, mock_ai_service
    ):
        """Test dat AI service errors correct gepropageerd worden."""
        mock_ai_service.generate_definition.side_effect = AIServiceError(
            "Rate limit exceeded"
        )

        with pytest.raises(AIServiceError, match="Rate limit"):
            await suggester.suggest_synonyms("test term")

    @pytest.mark.asyncio()
    async def test_suggest_synonyms_skips_invalid_suggestions(
        self, suggester, mock_ai_service
    ):
        """Test dat invalide suggesties geskipped worden."""
        mock_response = AIGenerationResult(
            text="""{
                "synoniemen": [
                    {
                        "term": "valid synoniem",
                        "confidence": 0.90,
                        "rationale": "Correct"
                    },
                    {
                        "term": "invalid",
                        "confidence": "not a number",
                        "rationale": "Invalid confidence type"
                    },
                    {
                        "term": "another valid",
                        "confidence": 0.85,
                        "rationale": "Also correct"
                    }
                ]
            }""",
            model="gpt-4-turbo",
            tokens_used=300,
            generation_time=1.5,
            cached=False,
            retry_count=0,
        )
        mock_ai_service.generate_definition.return_value = mock_response

        suggestions = await suggester.suggest_synonyms("test term")

        # Should only return the 2 valid suggestions
        assert len(suggestions) == 2
        assert suggestions[0].synoniem == "valid synoniem"
        assert suggestions[1].synoniem == "another valid"


class TestIntegration:
    """Integration tests (require actual API key)."""

    @pytest.mark.integration()
    @pytest.mark.asyncio()
    async def test_real_gpt4_suggestion(self):
        """Test met echte GPT-4 API call (requires OPENAI_API_KEY)."""
        import os

        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set")

        suggester = GPT4SynonymSuggester(
            model="gpt-4-turbo", temperature=0.3, min_confidence=0.6
        )

        suggestions = await suggester.suggest_synonyms(
            term="voorlopige hechtenis",
            definitie="Tijdelijke vrijheidsbeneming van een verdachte voorafgaand aan het vonnis",
            context=["Sv", "strafrecht", "artikel 63"],
        )

        # Verify reasonable output
        assert len(suggestions) > 0
        assert len(suggestions) <= 8
        assert all(s.confidence >= 0.6 for s in suggestions)
        assert all(s.confidence <= 1.0 for s in suggestions)
        assert all(len(s.rationale) > 10 for s in suggestions)

        # Log results for manual inspection
        print("\n=== GPT-4 Synonym Suggestions ===")
        for s in suggestions:
            print(f"  - {s.synoniem} ({s.confidence:.2f}): {s.rationale}")
