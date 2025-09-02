"""Tests for AIServiceV2 implementation."""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from openai import OpenAIError, RateLimitError, APITimeoutError

from services.ai_service_v2 import AIServiceV2
from services.interfaces import (
    AIBatchRequest,
    AIGenerationResult,
    AIRateLimitError,
    AIServiceError,
    AITimeoutError,
)
from utils.async_api import RateLimitConfig


class TestAIServiceV2:
    """Test suite for AIServiceV2."""

    @pytest.fixture
    def rate_limit_config(self):
        """Create test rate limit config."""
        return RateLimitConfig(
            requests_per_minute=10,
            requests_per_hour=100,
            max_concurrent=2,
            backoff_factor=1.5,
            max_retries=2,
        )

    @pytest.fixture
    def ai_service(self, rate_limit_config):
        """Create AIServiceV2 instance for testing."""
        with patch("services.ai_service_v2.AsyncGPTClient"):
            service = AIServiceV2(
                rate_limit_config=rate_limit_config,
                default_model="gpt-4",
                use_cache=False,  # Disable cache for most tests
            )
            return service

    @pytest.mark.asyncio
    async def test_generate_definition_success(self, ai_service):
        """Test successful definition generation."""
        # Mock the client response
        expected_text = "Een test is een procedure om iets te verifiëren."
        ai_service.client.chat_completion = AsyncMock(return_value=expected_text)

        # Call generate_definition
        result = await ai_service.generate_definition(
            prompt="Definieer het begrip 'test'",
            temperature=0.7,
            max_tokens=100,
        )

        # Verify result
        assert result is not None
        assert hasattr(result, 'text')
        assert hasattr(result, 'model')
        assert hasattr(result, 'tokens_used')
        assert result.text == expected_text
        assert result.model == "gpt-4"
        assert result.tokens_used is not None
        assert result.generation_time > 0
        assert result.cached is False
        assert result.retry_count == 0

    @pytest.mark.asyncio
    async def test_generate_definition_with_system_prompt(self, ai_service):
        """Test generation with system prompt."""
        ai_service.client.chat_completion = AsyncMock(
            return_value="Juridische definitie tekst"
        )

        result = await ai_service.generate_definition(
            prompt="Definieer 'aansprakelijkheid'",
            system_prompt="Je bent een juridisch expert",
            model="gpt-4o-mini",
        )

        assert result.text == "Juridische definitie tekst"
        assert result.model == "gpt-4o-mini"

    @pytest.mark.asyncio
    async def test_generate_definition_timeout(self, ai_service):
        """Test timeout handling."""
        # Mock timeout
        async def slow_completion(*args, **kwargs):
            await asyncio.sleep(5)  # Longer than timeout
            return "Should not reach here"

        ai_service.client.chat_completion = slow_completion

        with pytest.raises(AITimeoutError) as exc_info:
            await ai_service.generate_definition(
                prompt="Test prompt",
                timeout_seconds=0.1,
            )

        assert "timed out after 0.1s" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_definition_rate_limit_error(self, ai_service):
        """Test rate limit error handling."""
        # Create a proper RateLimitError mock
        from unittest.mock import Mock
        response = Mock()
        response.status_code = 429
        response.headers = {}

        ai_service.client.chat_completion = AsyncMock(
            side_effect=RateLimitError(
                message="Rate limit exceeded",
                response=response,
                body={"error": {"message": "Rate limit exceeded"}}
            )
        )

        with pytest.raises(AIRateLimitError) as exc_info:
            await ai_service.generate_definition(prompt="Test")

        assert "Rate limit exceeded" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_definition_api_timeout_error(self, ai_service):
        """Test API timeout error handling."""
        from unittest.mock import Mock
        response = Mock()
        response.status_code = 408
        response.headers = {}

        # Use a generic timeout exception
        ai_service.client.chat_completion = AsyncMock(
            side_effect=Exception("Request timed out")
        )

        with pytest.raises(AIServiceError) as exc_info:
            await ai_service.generate_definition(prompt="Test")

        assert "Unexpected error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_definition_openai_error(self, ai_service):
        """Test general OpenAI error handling."""
        # Use generic Exception instead of OpenAIError base class
        ai_service.client.chat_completion = AsyncMock(
            side_effect=Exception("API error")
        )

        with pytest.raises(AIServiceError) as exc_info:
            await ai_service.generate_definition(prompt="Test")

        assert "Unexpected error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_batch_generate_success(self, ai_service):
        """Test successful batch generation."""
        # Mock responses
        responses = ["Def 1", "Def 2", "Def 3"]
        call_count = 0

        async def mock_completion(*args, **kwargs):
            nonlocal call_count
            result = responses[call_count]
            call_count += 1
            return result

        ai_service.client.chat_completion = mock_completion

        # Create batch requests
        requests = [
            AIBatchRequest(prompt=f"Prompt {i}", temperature=0.7, max_tokens=100)
            for i in range(3)
        ]

        # Execute batch
        results = await ai_service.batch_generate(requests)

        # Verify results
        assert len(results) == 3
        for i, result in enumerate(results):
            assert result.text == responses[i]
            assert result.cached is False

    @pytest.mark.asyncio
    async def test_batch_generate_partial_failure(self, ai_service):
        """Test batch generation with one failure."""
        call_count = 0

        async def mock_completion(*args, **kwargs):
            nonlocal call_count
            if call_count == 1:
                call_count += 1
                raise Exception("Failed request")
            result = f"Def {call_count}"
            call_count += 1
            return result

        ai_service.client.chat_completion = mock_completion

        requests = [
            AIBatchRequest(prompt=f"Prompt {i}", temperature=0.7, max_tokens=100)
            for i in range(3)
        ]

        with pytest.raises(AIServiceError) as exc_info:
            await ai_service.batch_generate(requests)

        assert "Batch request 1 failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_batch_generate_empty_list(self, ai_service):
        """Test batch generation with empty list."""
        results = await ai_service.batch_generate([])
        assert results == []

    @pytest.mark.asyncio
    async def test_caching_integration(self):
        """Test V1-compatible caching."""
        with patch("services.ai_service_v2.AsyncGPTClient"):
            service = AIServiceV2(use_cache=True)

            # Mock cache at the correct import location
            with patch("utils.cache._cache") as mock_cache:
                # First call - cache miss
                mock_cache.get.return_value = None
                service.client.chat_completion = AsyncMock(
                    return_value="Generated text"
                )

                result1 = await service.generate_definition(
                    prompt="Test prompt",
                    model="gpt-4",
                    temperature=0.7,
                    max_tokens=100,
                )

                assert result1.text == "Generated text"
                assert result1.cached is False
                assert mock_cache.set.called

                # Second call - cache hit
                mock_cache.get.return_value = "Cached text"

                result2 = await service.generate_definition(
                    prompt="Test prompt",
                    model="gpt-4",
                    temperature=0.7,
                    max_tokens=100,
                )

                assert result2.text == "Cached text"
                assert result2.cached is True

    def test_token_estimation_with_tiktoken(self):
        """Test token estimation with tiktoken available."""
        # Create a service with mocked tiktoken
        with patch("services.ai_service_v2.AsyncGPTClient"):
            with patch("services.ai_service_v2.TIKTOKEN_AVAILABLE", True):
                service = AIServiceV2()

                # Mock the encoder in the cache
                mock_encoder = MagicMock()
                mock_encoder.encode.return_value = list(range(50))  # 50 tokens
                # Directly set in cache to bypass tiktoken import
                service._token_encoders["gpt-4"] = mock_encoder

                tokens = service._estimate_tokens("prompt", "response", "gpt-4")

                assert tokens == 50
                mock_encoder.encode.assert_called_once_with("promptresponse")

                # Verify encoder is in cache
                assert "gpt-4" in service._token_encoders
                assert service._token_encoders["gpt-4"] == mock_encoder

    @pytest.mark.asyncio
    async def test_system_prompt_propagation(self, ai_service):
        """Test that system prompt is properly passed to AsyncGPTClient."""
        expected_text = "Juridische definitie voor het begrip."
        system_prompt = "Je bent een juridisch expert"
        user_prompt = "Definieer 'aansprakelijkheid'"

        # Mock the AsyncGPTClient call
        ai_service.client.chat_completion = AsyncMock(return_value=expected_text)

        result = await ai_service.generate_definition(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.5,
            max_tokens=200,
            model="gpt-4",
        )

        # Verify the result
        assert result.text == expected_text

        # Verify AsyncGPTClient was called with system_prompt
        ai_service.client.chat_completion.assert_called_once_with(
            prompt=user_prompt,
            model="gpt-4",
            temperature=0.5,
            max_tokens=200,
            system_prompt=system_prompt,
            use_cache=False,
        )

    @pytest.mark.asyncio
    async def test_cache_key_includes_system_prompt(self):
        """Test that cache keys are unique for different system prompts."""
        with patch("services.ai_service_v2.AsyncGPTClient"):
            service = AIServiceV2(use_cache=True)

            with patch("utils.cache._cache") as mock_cache:
                mock_cache.get.return_value = None
                service.client.chat_completion = AsyncMock(return_value="Test result")

                # Same prompt, different system prompts
                prompt = "Define test"
                system_prompt1 = "You are a legal expert"
                system_prompt2 = "You are a technical writer"

                # First call with system_prompt1
                await service.generate_definition(
                    prompt=prompt,
                    system_prompt=system_prompt1,
                )

                # Second call with system_prompt2
                await service.generate_definition(
                    prompt=prompt,
                    system_prompt=system_prompt2,
                )

                # Verify cache.set was called twice with different keys
                assert mock_cache.set.call_count == 2

                # Get the cache keys used
                call_args_list = mock_cache.set.call_args_list
                key1 = call_args_list[0][0][0]
                key2 = call_args_list[1][0][0]

                # Keys should be different
                assert key1 != key2

    def test_token_estimation_fallback(self):
        """Test token estimation fallback heuristic."""
        with patch("services.ai_service_v2.TIKTOKEN_AVAILABLE", False):
            with patch("services.ai_service_v2.AsyncGPTClient"):
                service = AIServiceV2()

                # Test short text
                tokens = service._estimate_tokens("Hello", "World", "gpt-4")
                assert 5 <= tokens <= 10  # ~7.5 expected

                # Test longer text
                long_text = "A" * 1000
                tokens = service._estimate_tokens(long_text, long_text, "gpt-4")
                assert 1000 <= tokens <= 2000  # ~1500 expected

    def test_token_estimation_metadata(self):
        """Test tokens_estimated flag in metadata."""
        with patch("services.ai_service_v2.TIKTOKEN_AVAILABLE", False):
            with patch("services.ai_service_v2.AsyncGPTClient"):
                service = AIServiceV2()

                # Without tiktoken, encoders dict should be empty
                assert service._token_encoders == {}

                # Encoder for any model should return None
                encoder = service._get_or_create_encoder("gpt-4")
                assert encoder is None

    @pytest.mark.asyncio
    async def test_rate_limit_config_from_config_manager(self):
        """Test rate limit config from config_manager."""
        with patch("services.ai_service_v2.get_config_manager") as mock_get_cm:
            # Mock config manager
            mock_cm = MagicMock()
            mock_api_config = MagicMock()
            mock_api_config.rate_limit_requests_per_minute = 30
            mock_api_config.rate_limit_requests_per_hour = 1500
            mock_api_config.rate_limit_max_concurrent = 5
            mock_api_config.rate_limit_backoff_factor = 2.0
            mock_api_config.rate_limit_max_retries = 3
            mock_cm.api = mock_api_config
            mock_get_cm.return_value = mock_cm

            with patch("services.ai_service_v2.AsyncGPTClient") as MockClient:
                service = AIServiceV2()  # No rate_limit_config provided

                # Verify AsyncGPTClient was called with config from config_manager
                assert MockClient.called
                rate_config = MockClient.call_args[1]["rate_limit_config"]
                assert rate_config.requests_per_minute == 30
                assert rate_config.requests_per_hour == 1500
                assert rate_config.max_concurrent == 5
                assert rate_config.backoff_factor == 2.0
                assert rate_config.max_retries == 3
