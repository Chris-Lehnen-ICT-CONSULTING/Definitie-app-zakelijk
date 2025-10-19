"""
Monitoring-focused integration test for DefinitionOrchestratorV2.

Asserts that monitoring.complete_generation is awaited with expected fields
and that token_count (from AI result) is propagated as an int.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.integration
@pytest.mark.asyncio
async def test_orchestrator_monitoring_token_count_and_components():
    from services.interfaces import (
        AIGenerationResult,
        CleaningResult,
        GenerationRequest,
    )
    from services.orchestrators.definition_orchestrator_v2 import (
        DefinitionOrchestratorV2,
    )

    prompt_service = AsyncMock()
    ai_service = AsyncMock()
    validation_service = AsyncMock()
    cleaning_service = AsyncMock()
    repository = MagicMock()
    monitoring = AsyncMock()
    feedback_engine = AsyncMock()
    web_lookup = AsyncMock()

    web_lookup.lookup.return_value = []
    web_lookup._last_debug = None

    prompt_service.build_generation_prompt.return_value = MagicMock(
        text="PROMPT",
        token_count=99,
        components_used=["ontologie_proces", "context_pack"],
        feedback_integrated=False,
        optimization_applied=False,
        metadata={},
    )

    ai_service.generate_definition.return_value = AIGenerationResult(
        text="Definitie.", model="gpt-4", tokens_used=77, generation_time=0.01
    )

    cleaning_service.clean_text.return_value = CleaningResult(
        original_text="Definitie.", cleaned_text="Definitie.", was_cleaned=False
    )

    validation_service.validate_definition.return_value = {
        "version": "1.0.0",
        "overall_score": 0.9,
        "is_acceptable": True,
        "violations": [],
        "passed_rules": ["ALL-GOOD"],
        "detailed_scores": {
            "taal": 0.9,
            "juridisch": 0.9,
            "structuur": 0.9,
            "samenhang": 0.9,
        },
        "system": {"correlation_id": "00000000-0000-0000-0000-000000000000"},
    }

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
        web_lookup_service=web_lookup,
    )

    with patch(
        "voorbeelden.unified_voorbeelden.genereer_alle_voorbeelden_async",
        new=AsyncMock(
            return_value={
                "voorbeeldzinnen": [],
                "praktijkvoorbeelden": [],
                "tegenvoorbeelden": [],
                "synoniemen": [],
                "antoniemen": [],
                "toelichting": "",
            }
        ),
    ):
        req = GenerationRequest(
            id="it-MON-1",
            begrip="verificatie",
            ontologische_categorie="proces",
            context="DJI",
            actor="tester",
            legal_basis="testing",
        )
        resp = await orch.create_definition(req)

    assert resp.success is True
    # Verify monitoring was called with expected fields
    monitoring.complete_generation.assert_awaited()
    _args, kwargs = monitoring.complete_generation.call_args
    assert kwargs.get("success") is True
    # Token count should be propagated and coerced to int
    assert isinstance(kwargs.get("token_count"), int)
    assert kwargs.get("token_count") == 77
    # Components used should come from prompt_result.components_used
    assert kwargs.get("components_used") == ["ontologie_proces", "context_pack"]
