import pytest

from services.definition_generator_config import UnifiedGeneratorConfig
from services.definition_generator_context import ContextSource, EnrichedContext
from services.prompts.modules.base_module import ModuleContext
from services.prompts.modules.expertise_module import ExpertiseModule
from services.prompts.modules.grammar_module import GrammarModule


def _ctx(begrip: str = "validatie"):
    enriched = EnrichedContext(
        base_context={},
        sources=[
            ContextSource(source_type="web_lookup", confidence=0.8, content="ctx")
        ],
        expanded_terms={},
        confidence_scores={},
        metadata={},
    )
    return ModuleContext(
        begrip=begrip,
        enriched_context=enriched,
        config=UnifiedGeneratorConfig(),
        shared_state={},
    )


def test_expertise_module_wordtype_detection_and_shared_state():
    mod = ExpertiseModule()
    mod.initialize({})

    # Deverbaal
    ctx = _ctx("validatie")
    out = mod.execute(ctx)
    assert out.success is True
    assert out.metadata.get("word_type") == "deverbaal"
    assert ctx.get_shared("word_type") == "deverbaal"
    assert out.metadata.get("sections_generated", 0) >= 3

    # Werkwoord
    ctx2 = _ctx("valideren")
    out2 = mod.execute(ctx2)
    assert out2.metadata.get("word_type") == "werkwoord"

    # Overig
    ctx3 = _ctx("motorvoertuig")
    out3 = mod.execute(ctx3)
    assert out3.metadata.get("word_type") == "overig"


def test_grammar_module_uses_shared_word_type_and_strict_mode_changes_output():
    # Prepare context with shared word type from ExpertiseModule
    exp = ExpertiseModule()
    exp.initialize({})
    ctx = _ctx("validatie")
    _ = exp.execute(ctx)  # sets shared word_type

    gram = GrammarModule()
    gram.initialize({"include_examples": True, "strict_mode": False})
    out1 = gram.execute(ctx)
    assert out1.success is True
    assert out1.metadata.get("word_type") == "deverbaal"
    assert out1.metadata.get("rules_count", 0) >= 1
    assert "GRAMMATICA REGELS" in out1.content

    # Strict mode alters content/metadata
    gram_strict = GrammarModule()
    gram_strict.initialize({"strict_mode": True})
    out2 = gram_strict.execute(ctx)
    assert out2.success is True
    assert out2.metadata.get("strict_mode") is True
    # Content should differ when strict mode enabled
    assert out2.content != out1.content
