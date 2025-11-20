"""
Happy-path integration test for DefinitionOrchestratorV2 with full mocks.

This test focuses on verifying the orchestrator flow when all dependencies
behave correctly. It patches external integrations (web lookup, voorbeelden)
to avoid network/API usage.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.integration()
@pytest.mark.asyncio()
async def test_orchestrator_happy_path_minimal():
    from services.interfaces import (
        AIGenerationResult,
        CleaningResult,
        Definition,
        GenerationRequest,
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
        cleaned_text="Een tegenereerde definitie.",
        was_cleaned=False,
    )

    # Validation returns schema-like dict (accept)
    validation_service.validate_definition.return_value = {
        "version": "1.0.0",
        "overall_score": 0.85,
        "is_acceptable": True,
        "violations": [],
        "passed_rules": ["ESS-OK"],
        "detailed_scores": {
            "taal": 0.8,
            "juridisch": 0.85,
            "structuur": 0.8,
            "samenhang": 0.8,
        },
        "system": {"correlation_id": "00000000-0000-0000-0000-000000000000"},
    }

    # Repository save succeeds
    repository.save.return_value = 123

    # Setup request first
    request = GenerationRequest(
        id="it-001",
        begrip="verificatie",
        ontologische_categorie="proces",
        context="DJI",
        actor="tester",
        legal_basis="testing",
    )

    # Configure security service to return sanitized request
    security_service = AsyncMock()
    security_service.sanitize_request.return_value = request

    orch = DefinitionOrchestratorV2(
        prompt_service=prompt_service,
        ai_service=ai_service,
        validation_service=validation_service,
        enhancement_service=None,
        security_service=security_service,
        cleaning_service=cleaning_service,
        repository=repository,
        monitoring=AsyncMock(),
        feedback_engine=AsyncMock(),
        web_lookup_service=web_lookup_service,
    )

    # Patch voorbeelden to avoid API usage
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

    assert response.success is True
    assert response.definition is not None
    assert response.validation_result is not None
    assert response.metadata.get("orchestrator_version") == "v2.0"
