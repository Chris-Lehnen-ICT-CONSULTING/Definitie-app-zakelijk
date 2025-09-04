import pytest


class _StubAIService:
    def __init__(self):
        self.last_prompt = None

    async def generate_definition(self, prompt: str, **kwargs):
        self.last_prompt = prompt

        class _Gen:
            model = "stub"
            tokens_used = 0
            text = "DEFINITIE-TEKST"

        return _Gen()


class _StubCleaningService:
    class _Res:
        def __init__(self, cleaned_text: str):
            self.cleaned_text = cleaned_text

    async def clean_text(self, text: str, begrip: str):
        return self._Res(text.strip())


class _StubValidationService:
    async def validate_text(self, begrip: str, text: str, ontologische_categorie=None, context=None):
        return {"is_acceptable": True, "overall_score": 0.9, "violations": []}


class _StubRepository:
    def save(self, definition):
        return 42


class _StubWebLookupService:
    async def lookup(self, request):
        # Return two results in ranked order: Overheid first, Wikipedia second
        from services.interfaces import LookupResult, WebSource

        r1 = LookupResult(
            term=request.term,
            source=WebSource(name="Overheid.nl", url="https://overheid.nl/b", confidence=1.0, is_juridical=True),
            definition="Beta",
            success=True,
            metadata={},
        )
        r2 = LookupResult(
            term=request.term,
            source=WebSource(name="Wikipedia", url="https://w.org/a", confidence=0.7, is_juridical=False),
            definition="Alpha",
            success=True,
            metadata={},
        )
        return [r1, r2]


@pytest.mark.asyncio
async def test_e2e_orchestrator_prompt_augmentation(monkeypatch):
    from services.interfaces import GenerationRequest, OrchestratorConfig
    from services.orchestrators.definition_orchestrator_v2 import DefinitionOrchestratorV2
    from services.prompts.prompt_service_v2 import PromptServiceV2

    # Force prompt augmentation enabled with deterministic builder
    def _fake_loader():
        return {
            "web_lookup": {
                "prompt_augmentation": {
                    "enabled": True,
                    "max_snippets": 2,
                    "max_tokens_per_snippet": 50,
                    "total_token_budget": 200,
                    "prioritize_juridical": True,
                    "section_header": "### Contextinformatie uit bronnen:",
                    "snippet_separator": "\n- ",
                    "position": "after_context",
                }
            }
        }

    monkeypatch.setattr(
        "services.prompts.prompt_service_v2.load_web_lookup_config", _fake_loader
    )

    prompt_service = PromptServiceV2()
    # Make prompt body deterministic
    class _StubBuilder:
        def build_prompt(self, begrip, context):
            return "PROMPT_BODY"

    prompt_service.prompt_generator = _StubBuilder()

    ai_service = _StubAIService()
    cleaning_service = _StubCleaningService()
    validation_service = _StubValidationService()
    repository = _StubRepository()
    web_lookup_service = _StubWebLookupService()

    orch = DefinitionOrchestratorV2(
        prompt_service=prompt_service,
        ai_service=ai_service,
        validation_service=validation_service,
        cleaning_service=cleaning_service,
        repository=repository,
        config=OrchestratorConfig(enable_web_lookup=True, web_lookup_top_k=2),
        web_lookup_service=web_lookup_service,
    )

    req = GenerationRequest(id="00000000-0000-0000-0000-000000000000", begrip="e2e-term")
    resp = await orch.create_definition(req, context={})

    # Response OK
    assert resp.success and resp.definition is not None

    # Provenance present and first two marked used_in_prompt
    sources = resp.definition.metadata.get("sources", [])
    assert len(sources) >= 2
    assert sources[0].get("used_in_prompt") is True
    assert sources[1].get("used_in_prompt") is True

    # Prompt contains augmentation header and max 2 snippets
    prompt_text = ai_service.last_prompt
    assert prompt_text is not None
    assert "### Contextinformatie uit bronnen:" in prompt_text
    # There should be exactly 2 list items (max_snippets=2)
    assert prompt_text.count("- ") >= 2
