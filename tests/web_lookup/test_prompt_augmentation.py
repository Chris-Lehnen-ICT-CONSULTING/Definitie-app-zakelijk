import pytest


def _mk_context_with_sources(sources):
    return {
        "context_dict": {},
        "web_lookup": {
            "sources": sources,
            "top_k": 2,
        },
    }


class _Req:
    def __init__(self, begrip):
        self.begrip = begrip
        self.ontologische_categorie = None
        self.id = "00000000-0000-0000-0000-000000000000"
        self.context = None
        self.domein = None
        self.actor = "test"
        self.legal_basis = None


@pytest.mark.asyncio
async def test_prompt_augmentation_injects_top_k(monkeypatch):
    from services.prompts.prompt_service_v2 import PromptServiceV2

    # Force augmentation enabled via config monkeypatch
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
                    "position": "prepend",
                }
            }
        }

    monkeypatch.setattr(
        "services.prompts.prompt_service_v2.load_web_lookup_config", _fake_loader
    )

    # Stub underlying prompt generator to return fixed prompt
    class _StubBuilder:
        def build_prompt(self, begrip, context):
            return "PROMPT_BODY"

    svc = PromptServiceV2()
    svc.prompt_generator = _StubBuilder()

    sources = [
        {"provider": "wikipedia", "source_label": "Wikipedia NL", "snippet": "A" * 80, "score": 0.5, "used_in_prompt": True},
        {"provider": "overheid", "source_label": "Overheid.nl", "snippet": "B" * 80, "score": 0.9, "used_in_prompt": True},
        {"provider": "wiktionary", "source_label": "Wiktionary NL", "snippet": "C" * 80, "score": 0.4, "used_in_prompt": False},
    ]
    enriched = _mk_context_with_sources(sources)

    result = await svc.build_generation_prompt(_Req("term"), context=enriched)
    text = result.text

    # Should prepend header and two items (max_snippets=2)
    assert text.startswith("### Contextinformatie uit bronnen:")
    assert text.count("- Wikipedia NL:") == 1
    assert text.count("- Overheid.nl:") == 1
    assert "PROMPT_BODY" in text


@pytest.mark.asyncio
async def test_prompt_augmentation_respects_budget(monkeypatch):
    from services.prompts.prompt_service_v2 import PromptServiceV2

    def _fake_loader():
        return {
            "web_lookup": {
                "prompt_augmentation": {
                    "enabled": True,
                    "max_snippets": 3,
                    "max_tokens_per_snippet": 5,   # tiny per-snippet
                    "total_token_budget": 6,       # allow only one snippet
                    "prioritize_juridical": False,
                    "section_header": "### Contextinformatie uit bronnen:",
                    "position": "after_context",
                }
            }
        }

    monkeypatch.setattr(
        "services.prompts.prompt_service_v2.load_web_lookup_config", _fake_loader
    )

    class _StubBuilder:
        def build_prompt(self, begrip, context):
            return "PROMPT_BODY"

    svc = PromptServiceV2()
    svc.prompt_generator = _StubBuilder()

    sources = [
        {"provider": "overheid", "source_label": "Overheid.nl", "snippet": "B" * 200, "score": 0.9, "used_in_prompt": True},
        {"provider": "wikipedia", "source_label": "Wikipedia NL", "snippet": "A" * 200, "score": 0.5, "used_in_prompt": True},
    ]
    enriched = _mk_context_with_sources(sources)

    result = await svc.build_generation_prompt(_Req("term"), context=enriched)
    text = result.text

    # Appended after body
    assert text.startswith("PROMPT_BODY")
    # only one snippet due to total budget
    assert text.count("- ") == 1
