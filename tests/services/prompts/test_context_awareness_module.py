import pytest

from services.definition_generator_config import UnifiedGeneratorConfig
from services.definition_generator_context import (ContextSource,
                                                   EnrichedContext)
from services.prompts.modules.base_module import ModuleContext
from services.prompts.modules.context_awareness_module import \
    ContextAwarenessModule


def _ctx(base_items=0, sources=0, expanded=0, confidences=None):
    base = {
        "organisatorisch": [f"ORG{i}" for i in range(base_items)],
        "juridisch": [],
        "wettelijk": [],
    }
    srcs = [
        ContextSource(source_type="web_lookup", confidence=0.9, content="A")
        for _ in range(sources)
    ]
    expanded_terms = {f"K{i}": f"V{i}" for i in range(expanded)}
    confidences = confidences or {"web_lookup": 0.9}
    enriched = EnrichedContext(
        base_context=base,
        sources=srcs,
        expanded_terms=expanded_terms,
        confidence_scores=confidences,
        metadata={},
    )
    cfg = UnifiedGeneratorConfig()
    return ModuleContext(
        begrip="authenticatie", enriched_context=enriched, config=cfg, shared_state={}
    )


def test_minimal_context_yields_minimal_section():
    mod = ContextAwarenessModule()
    mod.initialize({})
    ctx = _ctx(base_items=0, sources=0, expanded=0, confidences={})
    out = mod.execute(ctx)
    assert out.success is True
    # Minimal section keyword
    assert "📍 Context" in out.content
    assert out.metadata.get("formatting_level") == "minimal"
    # Shared state contains score
    assert isinstance(ctx.get_shared("context_richness_score"), float)


def test_moderate_context_section_and_shared_contexts():
    mod = ContextAwarenessModule()
    mod.initialize({})
    # One base item and one source should push into moderate formatting
    ctx = _ctx(base_items=2, sources=1, expanded=0)
    out = mod.execute(ctx)
    assert out.success is True
    assert out.metadata.get("formatting_level") in {"moderate", "rich"}
    # _share_traditional_context should set organization_contexts
    orgs = ctx.get_shared("organization_contexts")
    assert isinstance(orgs, list) and orgs


def test_rich_context_includes_sections_and_emojis():
    mod = ContextAwarenessModule()
    mod.initialize({"include_abbreviations": True})
    # High richness: many base items, multiple sources, expanded terms
    ctx = _ctx(base_items=10, sources=2, expanded=5)
    out = mod.execute(ctx)
    assert out.metadata.get("formatting_level") == "rich"
    assert "📊 UITGEBREIDE CONTEXT ANALYSE:" in out.content
    # Confidence indicator emojis present
    assert (
        any(emoji in out.content for emoji in ["🟢", "🟡", "🔴"])
        or "ADDITIONELE BRONNEN:" in out.content
    )
