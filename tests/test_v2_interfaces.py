"""
Tests voor V2 interfaces en dataclasses.

Deze tests valideren alle nieuwe V2 service interfaces
voor compatibiliteit met de V2 orchestrator.
"""

import asyncio
from typing import Any
from unittest.mock import MagicMock

import pytest

from src.services.interfaces import (CleaningResult, CleaningServiceInterface,
                                     Definition,
                                     DefinitionOrchestratorInterface,
                                     DefinitionResponse,
                                     EnhancementServiceInterface,
                                     FeedbackEngineInterface,
                                     GenerationRequest,
                                     MonitoringServiceInterface, PromptResult,
                                     PromptServiceInterface,
                                     SecurityServiceInterface,
                                     ValidationResult,
                                     ValidationServiceInterface)


class TestPromptServiceInterface:
    """Test suite voor PromptServiceInterface."""

    def test_interface_definition(self):
        """Test dat interface correct gedefinieerd is."""
        assert hasattr(PromptServiceInterface, "build_generation_prompt")
        assert hasattr(PromptServiceInterface, "optimize_prompt")

    @pytest.mark.asyncio()
    async def test_concrete_implementation(self):
        """Test concrete implementatie van PromptServiceInterface."""

        class ConcretePromptService(PromptServiceInterface):
            async def build_generation_prompt(
                self,
                request: GenerationRequest,
                feedback_history: list[dict[str, Any]] | None = None,
                context: dict[str, Any] | None = None,
            ) -> PromptResult:
                return PromptResult(
                    text=f"Prompt for {request.begrip}",
                    token_count=100,
                    components_used=["base", "context"],
                    feedback_integrated=feedback_history is not None,
                    optimization_applied=True,
                    metadata={},
                )

            async def optimize_prompt(self, prompt: str, max_tokens: int) -> str:
                return prompt[:max_tokens]

        service = ConcretePromptService()
        request = GenerationRequest(id="test", begrip="test_begrip")
        result = await service.build_generation_prompt(request)
        assert isinstance(result, PromptResult)
        assert "test_begrip" in result.text


class TestValidationServiceInterface:
    """Test suite voor ValidationServiceInterface."""

    def test_interface_definition(self):
        """Test dat interface correct gedefinieerd is."""
        assert hasattr(ValidationServiceInterface, "validate_definition")
        assert hasattr(ValidationServiceInterface, "batch_validate")

    @pytest.mark.asyncio()
    async def test_async_validation(self):
        """Test async validatie methode."""

        class ConcreteValidationService(ValidationServiceInterface):
            async def validate_definition(
                self,
                begrip: str,
                text: str,
                ontologische_categorie: str | None = None,
                context: dict[str, Any] | None = None,
            ) -> ValidationResult:
                await asyncio.sleep(0.01)  # Simuleer async operatie
                return ValidationResult(is_valid=True, definition_text=text)

            async def batch_validate(
                self, definitions: list[tuple[str, str]]
            ) -> list[ValidationResult]:
                results = []
                for begrip, text in definitions:
                    result = await self.validate_definition(begrip, text)
                    results.append(result)
                return results

        service = ConcreteValidationService()
        result = await service.validate_definition("test", "definitie")
        assert result.is_valid is True


class TestCleaningServiceInterface:
    """Test suite voor async CleaningServiceInterface."""

    @pytest.mark.asyncio()
    async def test_async_cleaning(self):
        """Test dat cleaning service nu async is."""

        class ConcreteCleaningService(CleaningServiceInterface):
            async def clean_definition(self, definition: Definition) -> CleaningResult:
                await asyncio.sleep(0.01)
                return CleaningResult(
                    original_text=definition.definitie,
                    cleaned_text=definition.definitie.strip(),
                    was_cleaned=True,
                )

            async def clean_text(self, text: str, term: str) -> CleaningResult:
                await asyncio.sleep(0.01)
                return CleaningResult(
                    original_text=text, cleaned_text=text.strip(), was_cleaned=True
                )

            def validate_cleaning_rules(self) -> bool:
                return True

        service = ConcreteCleaningService()
        definition = Definition(begrip="test", definitie="  test definitie  ")
        result = await service.clean_definition(definition)
        assert result.was_cleaned is True
        assert result.cleaned_text == "test definitie"


class TestEnhancementServiceInterface:
    """Test suite voor EnhancementServiceInterface."""

    @pytest.mark.asyncio()
    async def test_enhancement_interface(self):
        """Test enhancement service interface."""

        class ConcreteEnhancementService(EnhancementServiceInterface):
            async def enhance_definition(
                self,
                definition: Definition,
                enhancement_options: dict[str, Any] | None = None,
            ) -> Definition:
                definition.voorbeelden = ["Voorbeeld 1", "Voorbeeld 2"]
                return definition

            async def generate_examples(
                self, begrip: str, definitie: str, aantal: int = 3
            ) -> list[str]:
                return [f"Voorbeeld {i+1} voor {begrip}" for i in range(aantal)]

        service = ConcreteEnhancementService()
        definition = Definition(begrip="test", definitie="test def")
        enhanced = await service.enhance_definition(definition)
        assert len(enhanced.voorbeelden) == 2


class TestSecurityServiceInterface:
    """Test suite voor SecurityServiceInterface."""

    @pytest.mark.asyncio()
    async def test_security_interface(self):
        """Test security service interface."""

        class ConcreteSecurityService(SecurityServiceInterface):
            async def redact_pii(
                self, text: str, redaction_level: str = "medium"
            ) -> str:
                # Simpele mock redactie
                return text.replace("John Doe", "[REDACTED]")

            async def validate_compliance(
                self, definition: Definition, compliance_rules: list[str] | None = None
            ) -> dict[str, bool]:
                return {"GDPR": True, "AVG": True}

            async def encrypt_sensitive_data(
                self, data: dict[str, Any], encryption_keys: list[str]
            ) -> dict[str, Any]:
                encrypted_data = data.copy()
                for key in encryption_keys:
                    if key in encrypted_data:
                        encrypted_data[key] = f"ENCRYPTED_{encrypted_data[key]}"
                return encrypted_data

        service = ConcreteSecurityService()
        redacted = await service.redact_pii("Hello John Doe")
        assert redacted == "Hello [REDACTED]"


class TestMonitoringServiceInterface:
    """Test suite voor MonitoringServiceInterface."""

    @pytest.mark.asyncio()
    async def test_monitoring_interface(self):
        """Test monitoring service interface."""

        class ConcreteMonitoringService(MonitoringServiceInterface):
            def __init__(self):
                self.metrics = []

            async def track_generation_metrics(
                self, request_id: str, metrics: dict[str, Any]
            ) -> None:
                self.metrics.append({"id": request_id, "metrics": metrics})

            async def log_performance(
                self,
                operation: str,
                duration: float,
                success: bool,
                metadata: dict[str, Any] | None = None,
            ) -> None:
                self.metrics.append(
                    {"operation": operation, "duration": duration, "success": success}
                )

            def get_metrics_summary(
                self, time_range: tuple | None = None
            ) -> dict[str, Any]:
                return {"total_operations": len(self.metrics)}

        service = ConcreteMonitoringService()
        await service.track_generation_metrics("test-123", {"tokens": 100})
        summary = service.get_metrics_summary()
        assert summary["total_operations"] == 1


class TestFeedbackEngineInterface:
    """Test suite voor FeedbackEngineInterface."""

    @pytest.mark.asyncio()
    async def test_feedback_interface(self):
        """Test feedback engine interface."""

        class ConcreteFeedbackEngine(FeedbackEngineInterface):
            def __init__(self):
                self.feedback_store = []

            async def process_feedback(
                self,
                definition_id: str,
                feedback_type: str,
                feedback_content: str,
                metadata: dict[str, Any] | None = None,
            ) -> dict[str, Any]:
                feedback = {
                    "id": definition_id,
                    "type": feedback_type,
                    "content": feedback_content,
                }
                self.feedback_store.append(feedback)
                return {"status": "processed", "feedback_id": len(self.feedback_store)}

            async def get_feedback_history(
                self, definition_id: str | None = None, limit: int = 10
            ) -> list[dict[str, Any]]:
                if definition_id:
                    return [f for f in self.feedback_store if f["id"] == definition_id][
                        :limit
                    ]
                return self.feedback_store[:limit]

            async def integrate_feedback(
                self, prompt: str, feedback_items: list[dict[str, Any]]
            ) -> str:
                feedback_text = " ".join([f["content"] for f in feedback_items])
                return f"{prompt}\n\nFeedback: {feedback_text}"

        engine = ConcreteFeedbackEngine()
        result = await engine.process_feedback("def-123", "quality", "Good definition")
        assert result["status"] == "processed"


class TestOrchestratorInterface:
    """Test suite voor updated DefinitionOrchestratorInterface."""

    @pytest.mark.asyncio()
    async def test_orchestrator_with_context(self):
        """Test orchestrator met optionele context parameter."""

        class ConcreteOrchestrator(DefinitionOrchestratorInterface):
            async def create_definition(
                self, request: GenerationRequest, context: dict[str, Any] | None = None
            ) -> DefinitionResponse:
                # Mock implementatie
                return DefinitionResponse(
                    success=True,
                    definition=Definition(
                        begrip=request.begrip,
                        definitie=f"Definitie voor {request.begrip}",
                    ),
                )

            async def update_definition(
                self, definition_id: int, updates: dict[str, Any]
            ) -> DefinitionResponse:
                return DefinitionResponse(success=True)

            async def validate_and_save(
                self, definition: Definition
            ) -> DefinitionResponse:
                return DefinitionResponse(success=True, definition=definition)

        orchestrator = ConcreteOrchestrator()
        request = GenerationRequest(id="test", begrip="test_begrip")

        # Test met en zonder context
        response1 = await orchestrator.create_definition(request)
        assert response1.success is True

        response2 = await orchestrator.create_definition(
            request, context={"extra": "info"}
        )
        assert response2.success is True


class TestInterfaceCompatibility:
    """Test dat alle interfaces compatible zijn met elkaar."""

    @pytest.mark.asyncio()
    async def test_v2_orchestrator_can_use_all_services(self):
        """Test dat V2 orchestrator alle services kan gebruiken."""

        # Mock alle services
        prompt_service = MagicMock(spec=PromptServiceInterface)
        validation_service = MagicMock(spec=ValidationServiceInterface)
        cleaning_service = MagicMock(spec=CleaningServiceInterface)
        enhancement_service = MagicMock(spec=EnhancementServiceInterface)
        security_service = MagicMock(spec=SecurityServiceInterface)
        monitoring_service = MagicMock(spec=MonitoringServiceInterface)
        feedback_engine = MagicMock(spec=FeedbackEngineInterface)

        # Configureer mock returns
        prompt_service.build_generation_prompt.return_value = PromptResult(
            text="test prompt",
            token_count=100,
            components_used=[],
            feedback_integrated=False,
            optimization_applied=False,
            metadata={},
        )

        validation_service.validate_definition.return_value = ValidationResult(
            is_valid=True
        )

        cleaning_service.clean_text.return_value = CleaningResult(
            original_text="test", cleaned_text="test", was_cleaned=False
        )

        # Verify dat alle services de juiste interface implementeren
        assert hasattr(prompt_service, "build_generation_prompt")
        assert hasattr(validation_service, "validate_definition")
        assert hasattr(cleaning_service, "clean_definition")
        assert hasattr(enhancement_service, "enhance_definition")
        assert hasattr(security_service, "redact_pii")
        assert hasattr(monitoring_service, "track_generation_metrics")
        assert hasattr(feedback_engine, "process_feedback")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
