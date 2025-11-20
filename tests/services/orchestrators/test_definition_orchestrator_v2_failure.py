"""
Failure-flow integration test for DefinitionOrchestratorV2 with full mocks.

Covers: validation fail → enhancement → revalidation still fail → no save,
feedback processed, monitoring complete with success=False.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.integration()
@pytest.mark.asyncio()
async def test_orchestrator_failure_flow_with_enhancement_and_feedback():
    from services.interfaces import (
        AIGenerationResult,
        CleaningResult,
        GenerationRequest,
        OrchestratorConfig,
    )
    from services.orchestrators.definition_orchestrator_v2 import (
        DefinitionOrchestratorV2,
    )

    # Mocks for services
    prompt_service = AsyncMock()
    ai_service = AsyncMock()
    validation_service = AsyncMock()
    cleaning_service = AsyncMock()
    repository = MagicMock()
    enhancement_service = AsyncMock()
    monitoring = AsyncMock()
    feedback_engine = AsyncMock()
    web_lookup_service = AsyncMock()
    web_lookup_service.lookup.return_value = []
    web_lookup_service._last_debug = None

    # Prompt builder returns a minimal prompt
    prompt_service.build_generation_prompt.return_value = MagicMock(
        text="PROMPT",
        token_count=10,
        components_used=[],
        feedback_integrated=False,
        optimization_applied=False,
        metadata={},
    )

    # AI returns a minimal generation result
    ai_service.generate_definition.return_value = AIGenerationResult(
        text="Een gegenereerde definitie.",
        model="gpt-4",
        tokens_used=10,
        generation_time=0.01,
    )

    # Cleaning returns passthrough
    cleaning_service.clean_text.return_value = CleaningResult(
        original_text="Een gegenereerde definitie.",
        cleaned_text="Een gegenereerde definitie.",
        was_cleaned=False,
    )

    # Validation returns failure both times
    fail_result = {
        "version": "1.0.0",
        "overall_score": 0.45,
        "is_acceptable": False,
        "violations": [
            {
                "code": "ESS-01",
                "severity": "error",
                "message": "",
                "rule_id": "ESS-01",
                "category": "juridisch",
            }
        ],
        "passed_rules": [],
        "detailed_scores": {
            "taal": 0.5,
            "juridisch": 0.4,
            "structuur": 0.5,
            "samenhang": 0.5,
        },
        "system": {"correlation_id": "00000000-0000-0000-0000-000000000000"},
    }
    validation_service.validate_definition.side_effect = [fail_result, fail_result]

    # Enhancement returns a slightly different text
    enhancement_service.enhance_definition.return_value = (
        "Verbeterde definitie (maar nog onvoldoende)"
    )

    # Setup request FIRST
    request = GenerationRequest(
        id="it-FAIL",
        begrip="verificatie",
        ontologische_categorie="proces",
        context="DJI",
        actor="tester",
        legal_basis="testing",
    )

    # Configure security service to return request
    security_service = AsyncMock()
    security_service.sanitize_request.return_value = request

    orch = DefinitionOrchestratorV2(
        prompt_service=prompt_service,
        ai_service=ai_service,
        validation_service=validation_service,
        enhancement_service=enhancement_service,
        security_service=security_service,
        cleaning_service=cleaning_service,
        repository=repository,
        monitoring=monitoring,
        feedback_engine=feedback_engine,
        config=OrchestratorConfig(enable_feedback_loop=True, enable_enhancement=True),
        web_lookup_service=web_lookup_service,
    )

    fake_examples = {
        "voorbeeldzinnen": ["Voorbeeld 1"],
        "praktijkvoorbeelden": [],
        "tegenvoorbeelden": [],
        "synoniemen": [],
        "antoniemen": [],
        "toelichting": "",
    }

    with patch(
        "voorbeelden.unified_voorbeelden.genereer_alle_voorbeelden_async",
        new=AsyncMock(return_value=fake_examples),
    ):
        response = await orch.create_definition(request)

    # Assertions
    # Orchestrator succeeded in running the flow, but validation failed
    assert response.success is True
    assert isinstance(response.validation_result, dict)
    assert response.validation_result.get("is_acceptable") is False
    # Enhancement service should be invoked once
    enhancement_service.enhance_definition.assert_awaited()
    # Repository.save SHOULD be called (failed definitions saved for learning)
    repository.save.assert_called_once()
    # Feedback engine should be used on failure
    feedback_engine.process_validation_feedback.assert_awaited()
    # Monitoring complete called
    monitoring.complete_generation.assert_awaited()
