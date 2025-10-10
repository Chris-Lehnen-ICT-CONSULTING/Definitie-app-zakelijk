"""
Tests voor AIServiceInterface en gerelateerde dataclasses.

Deze tests valideren de interface definities en dataclass gedrag
voor de nieuwe AI service architectuur.
"""

import asyncio
from dataclasses import asdict
from typing import Any

import pytest

from src.services.interfaces import (AIBatchRequest, AIGenerationResult,
                                     AIRateLimitError, AIServiceError,
                                     AIServiceInterface, AITimeoutError)


class TestAIGenerationResult:
    """Test suite voor AIGenerationResult dataclass."""

    def test_creation_with_all_fields(self):
        """Test aanmaken met alle velden expliciet."""
        result = AIGenerationResult(
            text="Test definitie",
            model="gpt-4",
            tokens_used=150,
            generation_time=1.5,
            cached=True,
            retry_count=2,
            metadata={"custom": "value"},
        )

        assert result.text == "Test definitie"
        assert result.model == "gpt-4"
        assert result.tokens_used == 150
        assert result.generation_time == 1.5
        assert result.cached is True
        assert result.retry_count == 2
        assert result.metadata["custom"] == "value"

    def test_creation_with_defaults(self):
        """Test default waarden voor optionele velden."""
        result = AIGenerationResult(
            text="Test", model="gpt-4", tokens_used=100, generation_time=1.0
        )

        assert result.cached is False
        assert result.retry_count == 0
        assert isinstance(result.metadata, dict)
        assert len(result.metadata) == 0

    def test_tokens_estimated_flag_when_tokens_none(self):
        """Test automatische tokens_estimated flag bij None tokens."""
        result = AIGenerationResult(
            text="Test", model="gpt-4", tokens_used=None, generation_time=1.0
        )

        assert result.tokens_used is None
        assert result.metadata["tokens_estimated"] is True

    def test_no_tokens_estimated_flag_when_tokens_provided(self):
        """Test geen tokens_estimated flag bij echte tokens."""
        result = AIGenerationResult(
            text="Test", model="gpt-4", tokens_used=100, generation_time=1.0
        )

        assert "tokens_estimated" not in result.metadata

    def test_preserve_existing_metadata_with_tokens_estimated(self):
        """Test behoud van bestaande metadata bij tokens_estimated."""
        result = AIGenerationResult(
            text="Test",
            model="gpt-4",
            tokens_used=None,
            generation_time=1.0,
            metadata={"existing": "data"},
        )

        assert result.metadata["existing"] == "data"
        assert result.metadata["tokens_estimated"] is True

    def test_serialization(self):
        """Test dataclass serialization naar dict."""
        result = AIGenerationResult(
            text="Test", model="gpt-4", tokens_used=100, generation_time=1.0
        )

        data = asdict(result)
        assert isinstance(data, dict)
        assert data["text"] == "Test"
        assert data["model"] == "gpt-4"


class TestAIBatchRequest:
    """Test suite voor AIBatchRequest dataclass."""

    def test_creation_with_all_fields(self):
        """Test aanmaken met alle velden."""
        request = AIBatchRequest(
            prompt="Generate definition",
            temperature=0.8,
            max_tokens=600,
            model="gpt-4-turbo",
            system_prompt="You are a legal expert",
            timeout_seconds=60,
            metadata={"priority": "high"},
        )

        assert request.prompt == "Generate definition"
        assert request.temperature == 0.8
        assert request.max_tokens == 600
        assert request.model == "gpt-4-turbo"
        assert request.system_prompt == "You are a legal expert"
        assert request.timeout_seconds == 60
        assert request.metadata["priority"] == "high"

    def test_creation_with_defaults(self):
        """Test default waarden."""
        request = AIBatchRequest(prompt="Test prompt")

        assert request.temperature == 0.7
        assert request.max_tokens == 500
        assert request.model is None
        assert request.system_prompt is None
        assert request.timeout_seconds == 30
        assert isinstance(request.metadata, dict)
        assert len(request.metadata) == 0


class TestAIServiceInterface:
    """Test suite voor AIServiceInterface abstract base class."""

    def test_cannot_instantiate_directly(self):
        """Test dat interface niet direct geïnstantieerd kan worden."""
        with pytest.raises(TypeError):
            AIServiceInterface()

    def test_concrete_implementation_required_methods(self):
        """Test dat concrete implementatie alle methoden moet hebben."""

        class IncompleteService(AIServiceInterface):
            """Incomplete implementatie voor test."""

        with pytest.raises(TypeError) as exc_info:
            IncompleteService()

        error_msg = str(exc_info.value)
        assert "generate_definition" in error_msg or "abstract" in error_msg

    def test_valid_concrete_implementation(self):
        """Test geldige concrete implementatie."""

        class ConcreteAIService(AIServiceInterface):
            """Volledige implementatie voor test."""

            async def generate_definition(
                self,
                prompt: str,
                temperature: float = 0.7,
                max_tokens: int = 500,
                model: str | None = None,
                system_prompt: str | None = None,
                timeout_seconds: int = 30,
            ) -> AIGenerationResult:
                return AIGenerationResult(
                    text="Test result",
                    model=model or "gpt-4",
                    tokens_used=100,
                    generation_time=1.0,
                )

            async def batch_generate(
                self, requests: list[AIBatchRequest]
            ) -> list[AIGenerationResult]:
                results = []
                for req in requests:
                    result = await self.generate_definition(
                        req.prompt,
                        req.temperature,
                        req.max_tokens,
                        req.model,
                        req.system_prompt,
                        req.timeout_seconds,
                    )
                    results.append(result)
                return results

        # Should not raise
        service = ConcreteAIService()
        assert isinstance(service, AIServiceInterface)

    @pytest.mark.asyncio()
    async def test_interface_async_methods(self):
        """Test dat interface methoden correct async zijn."""

        class TestService(AIServiceInterface):
            async def generate_definition(
                self, prompt: str, **kwargs
            ) -> AIGenerationResult:
                await asyncio.sleep(0.01)  # Simuleer async operatie
                return AIGenerationResult(
                    text="Async result",
                    model="gpt-4",
                    tokens_used=50,
                    generation_time=0.01,
                )

            async def batch_generate(
                self, requests: list[AIBatchRequest]
            ) -> list[AIGenerationResult]:
                return [await self.generate_definition(req.prompt) for req in requests]

        service = TestService()
        result = await service.generate_definition("Test prompt")
        assert result.text == "Async result"

        batch_results = await service.batch_generate(
            [AIBatchRequest(prompt="Prompt 1"), AIBatchRequest(prompt="Prompt 2")]
        )
        assert len(batch_results) == 2


class TestAIServiceExceptions:
    """Test suite voor AI service exception hierarchy."""

    def test_base_exception(self):
        """Test AIServiceError als base exception."""
        error = AIServiceError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_rate_limit_exception(self):
        """Test AIRateLimitError inheritance."""
        error = AIRateLimitError("Rate limit exceeded")
        assert isinstance(error, AIServiceError)
        assert isinstance(error, Exception)
        assert str(error) == "Rate limit exceeded"

    def test_timeout_exception(self):
        """Test AITimeoutError inheritance."""
        error = AITimeoutError("Request timed out")
        assert isinstance(error, AIServiceError)
        assert isinstance(error, Exception)
        assert str(error) == "Request timed out"

    def test_exception_catching(self):
        """Test exception catching patterns."""

        def raise_rate_limit():
            raise AIRateLimitError("Too many requests")

        # Specific catch
        with pytest.raises(AIRateLimitError):
            raise_rate_limit()

        # Generic AI service catch
        try:
            raise_rate_limit()
        except AIServiceError as e:
            assert isinstance(e, AIRateLimitError)

        # Base exception catch
        try:
            raise_rate_limit()
        except Exception as e:
            assert isinstance(e, AIServiceError)


class TestInterfaceIntegration:
    """Integration tests voor interface componenten."""

    @pytest.mark.asyncio()
    async def test_full_flow_simulation(self):
        """Test complete flow met mock implementatie."""

        class MockAIService(AIServiceInterface):
            """Mock service voor integration test."""

            async def generate_definition(
                self, prompt: str, **kwargs
            ) -> AIGenerationResult:
                # Simuleer verschillende scenarios
                if "error" in prompt.lower():
                    raise AIServiceError("Simulated error")
                if "rate" in prompt.lower():
                    raise AIRateLimitError("Rate limit hit")
                if "timeout" in prompt.lower():
                    raise AITimeoutError("Request timeout")

                return AIGenerationResult(
                    text=f"Definition for: {prompt}",
                    model=kwargs.get("model", "gpt-4"),
                    tokens_used=len(prompt) * 2,  # Simuleer token gebruik
                    generation_time=0.5,
                    cached="cache" in prompt.lower(),
                    retry_count=1 if "retry" in prompt.lower() else 0,
                    metadata={"mock": True},
                )

            async def batch_generate(
                self, requests: list[AIBatchRequest]
            ) -> list[AIGenerationResult]:
                results = []
                for req in requests:
                    try:
                        result = await self.generate_definition(
                            req.prompt,
                            model=req.model,
                            temperature=req.temperature,
                            max_tokens=req.max_tokens,
                        )
                        results.append(result)
                    except AIServiceError as e:
                        # In batch, errors worden result met error metadata
                        results.append(
                            AIGenerationResult(
                                text="",
                                model=req.model or "gpt-4",
                                tokens_used=0,
                                generation_time=0,
                                metadata={
                                    "error": str(e),
                                    "error_type": type(e).__name__,
                                },
                            )
                        )
                return results

        service = MockAIService()

        # Test normale flow
        result = await service.generate_definition("Test legal term")
        assert "Definition for: Test legal term" in result.text
        assert result.tokens_used > 0

        # Test batch met mixed results
        batch_requests = [
            AIBatchRequest(prompt="Normal request"),
            AIBatchRequest(prompt="Rate limited request"),
            AIBatchRequest(prompt="Cached request"),
        ]

        batch_results = await service.batch_generate(batch_requests)
        assert len(batch_results) == 3
        assert batch_results[0].text != ""
        assert batch_results[1].metadata.get("error_type") == "AIRateLimitError"
        assert batch_results[2].cached is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
