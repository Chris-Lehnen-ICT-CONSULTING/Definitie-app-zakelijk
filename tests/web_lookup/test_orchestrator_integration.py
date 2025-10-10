import asyncio
from dataclasses import dataclass
from typing import Any

import pytest


# Minimal stubs for required services
@dataclass
class _StubPromptResult:
    text: str
    token_count: int = 10
    components_used: list[str] = None
    feedback_integrated: bool = False
    optimization_applied: bool = False
    metadata: dict[str, Any] = None


class _StubPromptService:
    async def build_generation_prompt(
        self, request, feedback_history=None, context=None
    ):
        return _StubPromptResult(text=f"PROMPT for {request.begrip}")


class _StubAIService:
    async def generate_definition(self, prompt: str, **kwargs):
        class _Gen:
            model = "stub"
            tokens_used = 0

        return _Gen()


class _StubValidationService:
    async def validate_definition(self, definition, context=None):
        from services.validation.interfaces import CONTRACT_VERSION

        return {
            "version": CONTRACT_VERSION,
            "overall_score": 0.9,
            "is_acceptable": True,
            "violations": [],
            "passed_rules": [],
            "detailed_scores": {},
            "system": {"correlation_id": "00000000-0000-0000-0000-000000000000"},
        }


class _StubCleaningService:
    class _Res:
        def __init__(self, cleaned_text: str):
            self.cleaned_text = cleaned_text

    async def clean_text(self, text: str, begrip: str):
        return self._Res(text.strip())


class _StubRepository:
    def save(self, definition):
        return 1


class _StubWebLookupService:
    async def lookup(self, request):
        # Return two sources with different scores
        from services.interfaces import LookupResult, WebSource

        r1 = LookupResult(
            term=request.term,
            source=WebSource(name="Wikipedia", url="https://w.org/a", confidence=0.7),
            definition="Alpha",
            success=True,
            metadata={},
        )
        r2 = LookupResult(
            term=request.term,
            source=WebSource(
                name="Overheid.nl",
                url="https://overheid.nl/b",
                confidence=1.0,
                is_juridical=True,
            ),
            definition="Beta",
            success=True,
            metadata={},
        )
        return [r2, r1]  # Already ranked


@pytest.mark.asyncio()
async def test_orchestrator_includes_provenance_sources_in_metadata():
    from services.interfaces import GenerationRequest, OrchestratorConfig
    from services.orchestrators.definition_orchestrator_v2 import \
        DefinitionOrchestratorV2

    orch = DefinitionOrchestratorV2(
        prompt_service=_StubPromptService(),
        ai_service=_StubAIService(),
        validation_service=_StubValidationService(),
        cleaning_service=_StubCleaningService(),
        repository=_StubRepository(),
        config=OrchestratorConfig(web_lookup_top_k=1),
        web_lookup_service=_StubWebLookupService(),
    )

    req = GenerationRequest(
        id="00000000-0000-0000-0000-000000000000", begrip="test-term"
    )
    resp = await orch.create_definition(req, context={})

    assert resp.success and resp.definition is not None
    sources = resp.definition.metadata.get("sources", [])
    assert isinstance(sources, list) and len(sources) >= 2
    # First item should be marked used_in_prompt due to top_k=1
    assert sources[0].get("used_in_prompt") is True
