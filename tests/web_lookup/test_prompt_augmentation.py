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
        # US-043: Add required fields for HybridContextManager
        self.organisatie = None
        self.organisatorische_context = None
        self.juridische_context = None
        self.wettelijke_basis = None
        self.document_context = None
        self.extra_instructies = None
        self.options = {}


@pytest.mark.asyncio
async def test_prompt_augmentation_injects_top_k(monkeypatch):
    """DEF-315: Web sources produce <bron type="web"> XML tags in <bronnen> block."""
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
        {
            "provider": "wikipedia",
            "source_label": "Wikipedia NL",
            "snippet": "A" * 80,
            "score": 0.5,
            "used_in_prompt": True,
        },
        {
            "provider": "overheid",
            "source_label": "Overheid.nl",
            "snippet": "B" * 80,
            "score": 0.9,
            "used_in_prompt": True,
        },
        {
            "provider": "wiktionary",
            "source_label": "Wiktionary NL",
            "snippet": "C" * 80,
            "score": 0.4,
            "used_in_prompt": False,
        },
    ]
    enriched = _mk_context_with_sources(sources)

    result = await svc.build_generation_prompt(_Req("term"), context=enriched)
    text = result.text

    # DEF-315: Output should be XML <bronnen> block appended after prompt body
    assert text.startswith("PROMPT_BODY")
    assert "<bronnen>" in text
    assert "</bronnen>" in text
    # Two brons selected (max_snippets=2), with juridical prioritization
    assert 'type="web"' in text
    assert text.count("<bron ") == 2
    # Overheid should come first due to prioritize_juridical
    overheid_pos = text.find('provider="overheid"')
    wikipedia_pos = text.find('provider="wikipedia"')
    assert overheid_pos < wikipedia_pos


@pytest.mark.asyncio
async def test_prompt_augmentation_respects_budget(monkeypatch):
    """DEF-315: Token budget limits number of <bron> tags produced."""
    from services.prompts.prompt_service_v2 import PromptServiceV2

    def _fake_loader():
        return {
            "web_lookup": {
                "prompt_augmentation": {
                    "enabled": True,
                    "max_snippets": 3,
                    "max_tokens_per_snippet": 5,  # tiny per-snippet
                    "total_token_budget": 6,  # allow only one snippet
                    "prioritize_juridical": False,
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
        {
            "provider": "overheid",
            "source_label": "Overheid.nl",
            "snippet": "B" * 200,
            "score": 0.9,
            "used_in_prompt": True,
        },
        {
            "provider": "wikipedia",
            "source_label": "Wikipedia NL",
            "snippet": "A" * 200,
            "score": 0.5,
            "used_in_prompt": True,
        },
    ]
    enriched = _mk_context_with_sources(sources)

    result = await svc.build_generation_prompt(_Req("term"), context=enriched)
    text = result.text

    # Appended after body
    assert text.startswith("PROMPT_BODY")
    # Only one bron due to total budget constraint
    assert text.count("<bron ") == 1
    assert "<bronnen>" in text


@pytest.mark.asyncio
async def test_prompt_augmentation_web_with_legal_metadata(monkeypatch):
    """DEF-315: Legal metadata from web sources is included in <bron> attributes."""
    from services.prompts.prompt_service_v2 import PromptServiceV2

    def _fake_loader():
        return {
            "web_lookup": {
                "prompt_augmentation": {
                    "enabled": True,
                    "max_snippets": 5,
                    "max_tokens_per_snippet": 100,
                    "total_token_budget": 500,
                    "prioritize_juridical": False,
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
        {
            "provider": "rechtspraak",
            "snippet": "Uitspraak tekst",
            "score": 0.85,
            "url": "https://uitspraken.rechtspraak.nl/123",
            "used_in_prompt": True,
            "legal": {
                "ecli": "ECLI:NL:HR:2024:123",
                "law": "Awb",
                "article": "1:3",
                "citation_text": "Art. 1:3 Awb",
            },
        },
    ]
    enriched = _mk_context_with_sources(sources)

    result = await svc.build_generation_prompt(_Req("term"), context=enriched)
    text = result.text

    assert 'ecli="ECLI:NL:HR:2024:123"' in text
    assert 'wet="Awb"' in text
    assert 'artikel="1:3"' in text
