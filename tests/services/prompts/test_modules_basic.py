import pytest

from services.definition_generator_config import UnifiedGeneratorConfig
from services.definition_generator_context import (ContextSource,
                                                   EnrichedContext)
from services.prompts.modules.base_module import ModuleContext
from services.prompts.modules.definition_task_module import \
    DefinitionTaskModule
from services.prompts.modules.output_specification_module import \
    OutputSpecificationModule
from services.prompts.modules.semantic_categorisation_module import \
    SemanticCategorisationModule
from services.prompts.modules.structure_rules_module import \
    StructureRulesModule


def _make_context(
    begrip: str = "authenticatie",
    meta: dict | None = None,
    base_ctx: dict | None = None,
):
    enriched = EnrichedContext(
        base_context=base_ctx
        or {
            "organisatorische_context": ["OM"],
            "juridische_context": ["Strafrecht"],
            "wettelijke_basis": ["WvSr"],
        },
        sources=[
            ContextSource(source_type="web_lookup", confidence=0.9, content="wiki")
        ],
        expanded_terms={},
        confidence_scores={"web_lookup": 0.9},
        metadata=meta or {},
    )
    cfg = UnifiedGeneratorConfig()
    return ModuleContext(
        begrip=begrip, enriched_context=enriched, config=cfg, shared_state={}
    )


def test_definition_task_module_validate_and_execute():
    mod = DefinitionTaskModule()
    mod.initialize({})

    # validate requires begrip
    invalid_ctx = _make_context(begrip="")
    ok, err = mod.validate_input(invalid_ctx)
    assert ok is False and "Begrip is vereist" in (err or "")

    # execute builds expected sections and metadata
    ctx = _make_context(begrip="authenticatie")
    ctx.set_shared("word_type", "zelfstandig naamwoord")
    ctx.set_shared("organization_contexts", ["OM"])

    out = mod.execute(ctx)
    assert out.success is True
    content = out.content
    assert "FINALE INSTRUCTIES" in content
    assert "CHECKLIST" in content
    assert "Ontologische marker" in content
    assert "Promptmetadata" in content
    assert "authenticatie" in content
    assert out.metadata.get("begrip") == "authenticatie"


def test_structure_rules_module_execute_contains_rules():
    mod = StructureRulesModule()
    mod.initialize({"include_examples": True})
    out = mod.execute(_make_context())
    assert out.success is True
    assert "STR-01" in out.content and "STR-09" in out.content
    assert out.metadata.get("rules_count") == 9


def test_output_specification_module_limit_warning_and_shared():
    mod = OutputSpecificationModule()
    mod.initialize({})
    ctx = _make_context(meta={"min_karakters": 120, "max_karakters": 300})
    out = mod.execute(ctx)
    assert out.success is True
    assert out.metadata.get("has_limit_warning") is True
    # shared state contains character_limit_warning
    clw = ctx.get_shared("character_limit_warning")
    assert isinstance(clw, dict) and clw["min"] == 120 and clw["max"] == 300
    assert "KARAKTER LIMIET WAARSCHUWING" in out.content


def test_semantic_categorisation_sets_shared_and_guidance():
    mod = SemanticCategorisationModule()
    mod.initialize({"detailed_guidance": True})
    ctx = _make_context(meta={"ontologische_categorie": "proces"})
    out = mod.execute(ctx)
    assert out.success is True
    # shared state set
    assert ctx.get_shared("ontological_category") == "proces"
    # guidance hints appear
    assert "PROCES CATEGORIE" in out.content
    assert out.metadata.get("ontological_category") == "proces"
