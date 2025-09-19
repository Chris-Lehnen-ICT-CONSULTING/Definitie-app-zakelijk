"""
Feedback-loop integration test for DefinitionOrchestratorV2 with mocks.

Scenario:
- Feedback engine returns history
- Prompt integrates feedback (assert passed through)
- Validation succeeds (with optional warning-level violation)
- No feedback processing on success
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.integration
@pytest.mark.asyncio
async def test_orchestrator_feedback_loop_integration_success():
    from services.orchestrators.definition_orchestrator_v2 import DefinitionOrchestratorV2
    from services.interfaces import (
        AIGenerationResult,
        CleaningResult,
        GenerationRequest,
        OrchestratorConfig,
    )

    # Arrange services
    prompt_service = AsyncMock()
    ai_service = AsyncMock()
    validation_service = AsyncMock()
    cleaning_service = AsyncMock()
    repository = MagicMock()
    monitoring = AsyncMock()
    feedback_engine = AsyncMock()
    web_lookup_service = AsyncMock()

    web_lookup_service.lookup.return_value = []
    web_lookup_service._last_debug = None

    # Prompt result
    prompt_service.build_generation_prompt.return_value = MagicMock(
        text="PROMPT",
        token_count=42,
        components_used=["ontologie_proces", "feedback_integration"],
        feedback_integrated=True,
        optimization_applied=False,
        metadata={"feedback_entries": 1},
    )

    # AI result
    ai_service.generate_definition.return_value = AIGenerationResult(
        text="Definitie met voldoende kwaliteit.", model="gpt-4", tokens_used=123, generation_time=0.02
    )

    # Cleaning
    cleaning_service.clean_text.return_value = CleaningResult(
        original_text="Definitie met voldoende kwaliteit.",
        cleaned_text="Definitie met voldoende kwaliteit.",
        was_cleaned=False,
    )

    # Validation accept with a warning-level violation
    ok_result = {
        "version": "1.0.0",
        "overall_score": 0.82,
        "is_acceptable": True,
        "violations": [
            {
                "code": "STR-01",
                "severity": "warning",
                "message": "Kleine structuur opmerking",
                "rule_id": "STR-01",
                "category": "structuur",
            }
        ],
        "passed_rules": ["ESS-OK"],
        "detailed_scores": {"taal": 0.8, "juridisch": 0.82, "structuur": 0.78, "samenhang": 0.8},
        "system": {"correlation_id": "00000000-0000-0000-0000-000000000000"},
    }
    validation_service.validate_definition.return_value = ok_result

    # Feedback history
    feedback_history = [
        {
            "attempt_number": 1,
            "violations": ["CON-01"],
            "suggestions": ["Vermijd circulariteit"],
            "focus_areas": ["Structuur verbeteren"],
        }
    ]
    feedback_engine.get_feedback_for_request.return_value = feedback_history

    # Orchestrator configured with feedback loop enabled, enhancement off
    cfg = OrchestratorConfig(enable_feedback_loop=True, enable_enhancement=False)

    orch = DefinitionOrchestratorV2(
        prompt_service=prompt_service,
        ai_service=ai_service,
        validation_service=validation_service,
        enhancement_service=None,
        security_service=AsyncMock(),
        cleaning_service=cleaning_service,
        repository=repository,
        monitoring=monitoring,
        feedback_engine=feedback_engine,
        config=cfg,
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
        request = GenerationRequest(
            id="it-FEEDBACK",
            begrip="verificatie",
            ontologische_categorie="proces",
            context="DJI",
            actor="tester",
            legal_basis="testing",
        )

        # Act
        resp = await orch.create_definition(request)

    # Assert
    assert resp.success is True
    assert resp.definition is not None
    assert resp.validation_result is not None

    # Prompt should have received feedback history
    assert prompt_service.build_generation_prompt.await_count == 1
    _, kwargs = prompt_service.build_generation_prompt.call_args
    assert kwargs.get("feedback_history") == feedback_history

    # Metadata indicates feedback integrated
    assert resp.metadata.get("feedback_integrated") is True

    # No feedback processing on success
    feedback_engine.process_validation_feedback.assert_not_awaited()

