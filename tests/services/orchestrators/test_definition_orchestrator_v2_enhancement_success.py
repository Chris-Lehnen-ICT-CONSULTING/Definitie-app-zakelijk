"""
Enhancement success flow for DefinitionOrchestratorV2.

First validation fails -> enhancement applied -> second validation succeeds -> save occurs,
no feedback processing on success.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.integration
@pytest.mark.asyncio
async def test_enhancement_applied_leads_to_successful_validation_and_save():
    from services.interfaces import (
        AIGenerationResult,
        CleaningResult,
        GenerationRequest,
        OrchestratorConfig,
    )
    from services.orchestrators.definition_orchestrator_v2 import (
        DefinitionOrchestratorV2,
    )

    prompt_service = AsyncMock()
    ai_service = AsyncMock()
    validation_service = AsyncMock()
    cleaning_service = AsyncMock()
    repository = MagicMock()
    enhancement_service = AsyncMock()
    monitoring = AsyncMock()
    feedback_engine = AsyncMock()
    web_lookup = AsyncMock()

    web_lookup.lookup.return_value = []
    web_lookup._last_debug = None

    prompt_service.build_generation_prompt.return_value = MagicMock(
        text="PROMPT",
        token_count=50,
        components_used=["ontologie_proces"],
        feedback_integrated=False,
        optimization_applied=False,
        metadata={},
    )

    ai_service.generate_definition.return_value = AIGenerationResult(
        text="Slechte definitie.", model="gpt-4", tokens_used=10, generation_time=0.01
    )

    cleaning_service.clean_text.return_value = CleaningResult(
        original_text="Slechte definitie.",
        cleaned_text="Slechte definitie.",
        was_cleaned=False,
    )

    # First validation fails, second succeeds
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
    ok_result = {
        "version": "1.0.0",
        "overall_score": 0.82,
        "is_acceptable": True,
        "violations": [],
        "passed_rules": ["ALL-GOOD"],
        "detailed_scores": {
            "taal": 0.8,
            "juridisch": 0.82,
            "structuur": 0.78,
            "samenhang": 0.8,
        },
        "system": {"correlation_id": "00000000-0000-0000-0000-000000000000"},
    }

    validation_service.validate_definition.side_effect = [fail_result, ok_result]
    enhancement_service.enhance_definition.return_value = "Verbeterde definitie."

    cfg = OrchestratorConfig(enable_feedback_loop=True, enable_enhancement=True)

    orch = DefinitionOrchestratorV2(
        prompt_service=prompt_service,
        ai_service=ai_service,
        validation_service=validation_service,
        enhancement_service=enhancement_service,
        security_service=AsyncMock(),
        cleaning_service=cleaning_service,
        repository=repository,
        monitoring=monitoring,
        feedback_engine=feedback_engine,
        config=cfg,
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
            id="it-ENH-S",
            begrip="verificatie",
            ontologische_categorie="proces",
            context="DJI",
            actor="tester",
            legal_basis="testing",
        )
        resp = await orch.create_definition(req)

    assert resp.success is True
    # Save should be called on success
    repository.save.assert_called()
    # No feedback processing on success
    feedback_engine.process_validation_feedback.assert_not_awaited()
