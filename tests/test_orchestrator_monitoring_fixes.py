"""Tests for orchestrator monitoring fixes and interface compliance."""

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest

from src.services.interfaces import GenerationRequest, OrchestratorConfig
from src.services.orchestrators.definition_orchestrator_v2 import (
    DefinitionOrchestratorV2,
)


class MonitoringStub:
    """Test stub for monitoring service."""

    def __init__(self):
        self.calls = {"start": [], "complete": [], "error": []}

    async def start_generation(self, generation_id: str) -> None:
        self.calls["start"].append(generation_id)

    async def complete_generation(
        self,
        generation_id: str,
        success: bool,
        duration: float,
        token_count: int | None = None,
        **kwargs,
    ) -> None:
        self.calls["complete"].append(
            {
                "generation_id": generation_id,
                "success": success,
                "duration": duration,
                "token_count": token_count,
                "kwargs": kwargs,
            }
        )

    async def track_error(
        self, generation_id: str, error: Exception, error_type: str | None = None
    ) -> None:
        # Verify error is Exception, not string
        self.calls["error"].append(
            {
                "generation_id": generation_id,
                "error": error,
                "error_is_exception": isinstance(error, Exception),
                "error_type": error_type,
            }
        )


class AIServiceStub:
    """Test stub for AI service."""

    def __init__(self, text="Test definitie.", tokens=42, should_fail=False):
        self.text = text
        self.tokens = tokens
        self.should_fail = should_fail
        self.calls = []

    async def generate_definition(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
        model: str | None = None,
        system_prompt: str | None = None,
        timeout_seconds: int = 30,
    ):
        self.calls.append(
            {
                "prompt": prompt,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "model": model,
                "system_prompt": system_prompt,
                "timeout_seconds": timeout_seconds,
            }
        )

        if self.should_fail:
            raise TimeoutError("AI service timeout")

        # Return AIGenerationResult-like object
        return type(
            "AIGenerationResult",
            (),
            {
                "text": self.text,
                "model": model or "gpt-4",
                "tokens_used": self.tokens,
                "generation_time": 0.5,
                "cached": False,
                "retry_count": 0,
                "metadata": {},
            },
        )()


class CleaningStub:
    """Test stub for cleaning service."""

    async def clean_text(self, text: str, term: str):
        cleaned = text.strip()
        if cleaned and not cleaned.endswith("."):
            cleaned += "."
        return type(
            "CleaningResult",
            (),
            {
                "original_text": text,
                "cleaned_text": cleaned,
                "was_cleaned": cleaned != text,
            },
        )()

    async def clean_definition(self, definition):
        return await self.clean_text(definition.definitie, definition.begrip)


class ValidationStub:
    """Test stub for validation service."""

    async def validate_definition(
        self,
        begrip: str,
        text: str,
        ontologische_categorie: str | None = None,
        context: dict | None = None,
    ):
        # Simple validation: at least 10 chars
        is_valid = len(text or "") >= 10
        return type(
            "ValidationResult",
            (),
            {
                "is_valid": is_valid,
                "violations": (
                    []
                    if is_valid
                    else [
                        type(
                            "ValidationViolation",
                            (),
                            {
                                "rule_id": "MIN_LENGTH",
                                "severity": "HIGH",
                                "description": "Definitie te kort",
                            },
                        )()
                    ]
                ),
                "errors": [],
                "warnings": [],
                "suggestions": [],
            },
        )()


@pytest.mark.asyncio()
async def test_monitoring_success_flow():
    """Test monitoring calls in success flow."""
    # Setup
    mon = MonitoringStub()
    ai = AIServiceStub(text="Een test is een methode om iets te verifiëren.", tokens=25)

    orch = DefinitionOrchestratorV2(
        ai_service=ai,
        cleaning_service=CleaningStub(),
        validation_service=ValidationStub(),
        monitoring=mon,
        config=OrchestratorConfig(),
    )

    req = GenerationRequest(id="test-123", begrip="test", context="testing")

    # Execute
    result = await orch.create_definition(req)

    # Verify
    assert result.success is True
    assert len(mon.calls["start"]) == 1
    assert mon.calls["start"][0] == "test-123"

    assert len(mon.calls["complete"]) == 1
    complete_call = mon.calls["complete"][0]
    assert complete_call["generation_id"] == "test-123"
    assert complete_call["success"] is True
    assert complete_call["duration"] > 0
    assert complete_call["token_count"] == 25  # Should be int
    assert isinstance(complete_call["token_count"], int)

    assert len(mon.calls["error"]) == 0


@pytest.mark.asyncio()
async def test_monitoring_error_tracking():
    """Test that errors are tracked with Exception object, not string."""
    # Setup
    mon = MonitoringStub()
    ai = AIServiceStub(should_fail=True)

    orch = DefinitionOrchestratorV2(
        ai_service=ai,
        cleaning_service=CleaningStub(),
        validation_service=ValidationStub(),
        monitoring=mon,
        config=OrchestratorConfig(),
    )

    req = GenerationRequest(id="test-456", begrip="test")

    # Execute
    result = await orch.create_definition(req)

    # Verify
    assert result.success is False
    assert "AI service timeout" in str(result.error)
    assert result.metadata["error_type"] == "TimeoutError"

    assert len(mon.calls["start"]) == 1
    assert mon.calls["start"][0] == "test-456"

    assert len(mon.calls["complete"]) == 0  # Should not complete on error

    assert len(mon.calls["error"]) == 1
    error_call = mon.calls["error"][0]
    assert error_call["generation_id"] == "test-456"
    assert error_call["error_is_exception"] is True
    assert isinstance(error_call["error"], Exception)
    assert error_call["error_type"] == "TimeoutError"


@pytest.mark.asyncio()
async def test_monitoring_disabled():
    """Test orchestrator works without monitoring service."""
    # Setup without monitoring
    ai = AIServiceStub()

    orch = DefinitionOrchestratorV2(
        ai_service=ai,
        cleaning_service=CleaningStub(),
        validation_service=ValidationStub(),
        monitoring=None,  # No monitoring
        config=OrchestratorConfig(),
    )

    req = GenerationRequest(id="test-789", begrip="test")

    # Execute - should not crash
    result = await orch.create_definition(req)

    # Verify
    assert result.success is True
    assert result.definition is not None


@pytest.mark.asyncio()
async def test_token_count_none_handling():
    """Test handling of None token count."""
    # Setup with None tokens
    mon = MonitoringStub()

    class AIServiceNoneTokens:
        async def generate_definition(self, **kwargs):
            return type(
                "AIGenerationResult",
                (),
                {
                    "text": "Test definitie.",
                    "model": "gpt-4",
                    "tokens_used": None,  # None tokens
                    "generation_time": 0.5,
                    "cached": False,
                    "retry_count": 0,
                    "metadata": {"tokens_estimated": True},
                },
            )()

    orch = DefinitionOrchestratorV2(
        ai_service=AIServiceNoneTokens(),
        cleaning_service=CleaningStub(),
        validation_service=ValidationStub(),
        monitoring=mon,
        config=OrchestratorConfig(),
    )

    req = GenerationRequest(id="test-none", begrip="test")

    # Execute
    result = await orch.create_definition(req)

    # Verify
    assert result.success is True
    assert len(mon.calls["complete"]) == 1
    assert mon.calls["complete"][0]["token_count"] is None


@pytest.mark.asyncio()
async def test_token_count_float_conversion():
    """Test that float token counts are converted to int."""
    # Setup with float tokens
    mon = MonitoringStub()

    class AIServiceFloatTokens:
        async def generate_definition(self, **kwargs):
            return type(
                "AIGenerationResult",
                (),
                {
                    "text": "Test definitie.",
                    "model": "gpt-4",
                    "tokens_used": 42.7,  # Float tokens
                    "generation_time": 0.5,
                    "cached": False,
                    "retry_count": 0,
                    "metadata": {},
                },
            )()

    orch = DefinitionOrchestratorV2(
        ai_service=AIServiceFloatTokens(),
        cleaning_service=CleaningStub(),
        validation_service=ValidationStub(),
        monitoring=mon,
        config=OrchestratorConfig(),
    )

    req = GenerationRequest(id="test-float", begrip="test")

    # Execute
    result = await orch.create_definition(req)

    # Verify
    assert result.success is True
    assert len(mon.calls["complete"]) == 1
    assert mon.calls["complete"][0]["token_count"] == 42  # Should be int
    assert isinstance(mon.calls["complete"][0]["token_count"], int)


if __name__ == "__main__":
    asyncio.run(pytest.main([__file__, "-v"]))
