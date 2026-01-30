import pytest

from services.definition_generator_config import UnifiedGeneratorConfig
from services.definition_generator_context import ContextSource, EnrichedContext
from services.prompts.modules.base_module import (
    BasePromptModule,
    ModuleContext,
    ModuleOutput,
)
from services.prompts.modules.prompt_orchestrator import PromptOrchestrator


class _OkModule(BasePromptModule):
    def __init__(self, module_id: str, deps: list[str] | None = None, text: str = "OK"):
        super().__init__(module_id=module_id, module_name=f"{module_id}")
        self._deps = deps or []
        self.text = text

    def initialize(self, config: dict):
        self._initialized = True

    def validate_input(self, context: ModuleContext):
        return True, None

    def execute(self, context: ModuleContext):
        return ModuleOutput(content=f"[{self.module_id}:{self.text}]", metadata={})

    def get_dependencies(self):
        return self._deps


class _SkipModule(BasePromptModule):
    def __init__(self, module_id: str):
        super().__init__(module_id=module_id, module_name=f"{module_id}")

    def initialize(self, config: dict):
        self._initialized = True

    def validate_input(self, context: ModuleContext):
        return False, "not needed"

    def execute(self, context: ModuleContext):
        return ModuleOutput(content="SHOULD_NOT_APPEAR", metadata={})

    def get_dependencies(self):
        return []


def _ctx():
    enriched = EnrichedContext(
        base_context={},
        sources=[ContextSource(source_type="web_lookup", confidence=0.9, content="")],
        expanded_terms={},
        confidence_scores={},
        metadata={},
    )
    return enriched, UnifiedGeneratorConfig()


def test_orchestrator_resolves_dependencies_and_builds_prompt():
    orch = PromptOrchestrator()
    # B depends on A, C independent
    mod_a = _OkModule("A")
    mod_b = _OkModule("B", deps=["A"], text="BTXT")
    mod_c = _OkModule("C")

    orch.register_module(mod_a)
    orch.register_module(mod_b)
    orch.register_module(mod_c)
    orch.initialize_modules({})

    # Ensure execution order resolves into batches
    batches = orch.resolve_execution_order()
    # first batch contains A and C (no incoming deps), second contains B
    assert any("A" in b for b in batches[0])
    assert any("C" in b for b in batches[0])

    enriched, cfg = _ctx()
    # Custom order for combining
    orch.set_module_order(["A", "B", "C"])
    prompt = orch.build_prompt("begrip", enriched, cfg)
    # Modules executed and ordered
    assert prompt.find("[A:") < prompt.find("[B:") < prompt.find("[C:")
    md = orch.get_execution_metadata()
    assert md.get("total_modules") == 3
    assert md.get("prompt_length", 0) > 0


def test_orchestrator_skips_invalid_module_and_keeps_content():
    orch = PromptOrchestrator()
    ok = _OkModule("ok")
    skip = _SkipModule("skip")
    orch.register_module(ok)
    orch.register_module(skip)
    orch.initialize_modules({})
    orch.set_module_order(["skip", "ok"])  # even if skip first, it won't contribute

    enriched, cfg = _ctx()
    prompt = orch.build_prompt("b", enriched, cfg)
    assert "SHOULD_NOT_APPEAR" not in prompt
    assert "[ok:" in prompt


# DEF-123: Context-aware module loading tests
class TestDEF123ContextAwareModuleLoading:
    """Tests for DEF-123: Context-aware module loading optimization."""

    def test_context_awareness_skipped_when_no_context(self):
        """DEF-123: context_awareness module should be skipped when no context present."""
        orch = PromptOrchestrator()
        # Register a known module that should be filtered
        context_mod = _OkModule("context_awareness")
        core_mod = _OkModule("expertise")  # Core module, always active
        orch.register_module(context_mod)
        orch.register_module(core_mod)
        orch.initialize_modules({})

        # Empty context
        enriched = EnrichedContext(
            base_context={},  # No context
            sources=[],
            expanded_terms={},
            confidence_scores={},
            metadata={},
        )
        cfg = UnifiedGeneratorConfig()

        active = orch._get_active_modules(enriched, cfg)
        assert "expertise" in active, "Core modules should always be active"
        assert (
            "context_awareness" not in active
        ), "context_awareness should be skipped without context"

    def test_context_awareness_active_when_context_present(self):
        """DEF-123: context_awareness module should be active when context is present."""
        orch = PromptOrchestrator()
        context_mod = _OkModule("context_awareness")
        orch.register_module(context_mod)
        orch.initialize_modules({})

        # With organisatorische context
        enriched = EnrichedContext(
            base_context={"organisatorisch": ["Gemeente Amsterdam"]},
            sources=[],
            expanded_terms={},
            confidence_scores={},
            metadata={},
        )
        cfg = UnifiedGeneratorConfig()

        active = orch._get_active_modules(enriched, cfg)
        assert (
            "context_awareness" in active
        ), "context_awareness should be active with context"

    def test_metrics_skipped_when_not_debug_mode(self):
        """DEF-123: metrics module should be skipped when not in debug mode."""
        orch = PromptOrchestrator()
        metrics_mod = _OkModule("metrics")
        orch.register_module(metrics_mod)
        orch.initialize_modules({})

        enriched, cfg = _ctx()
        # Ensure debug mode is off
        cfg.debug_mode = False
        cfg.include_metrics = False

        active = orch._get_active_modules(enriched, cfg)
        assert "metrics" not in active, "metrics should be skipped without debug mode"

    def test_metrics_active_in_debug_mode(self):
        """DEF-123: metrics module should be active in debug mode."""
        orch = PromptOrchestrator()
        metrics_mod = _OkModule("metrics")
        orch.register_module(metrics_mod)
        orch.initialize_modules({})

        enriched, cfg = _ctx()
        cfg.debug_mode = True

        active = orch._get_active_modules(enriched, cfg)
        assert "metrics" in active, "metrics should be active in debug mode"

    def test_execution_metadata_includes_active_skipped_info(self):
        """DEF-123: Execution metadata should include active/skipped module info."""
        orch = PromptOrchestrator()
        # Register known modules
        orch.register_module(_OkModule("expertise"))
        orch.register_module(_OkModule("metrics"))
        orch.register_module(_OkModule("context_awareness"))
        orch.initialize_modules({})
        orch.set_module_order(["expertise", "metrics", "context_awareness"])

        # No context, no debug mode → metrics and context_awareness should be skipped
        enriched = EnrichedContext(
            base_context={},
            sources=[],
            expanded_terms={},
            confidence_scores={},
            metadata={},
        )
        cfg = UnifiedGeneratorConfig()
        cfg.debug_mode = False

        orch.build_prompt("test", enriched, cfg)
        metadata = orch.get_execution_metadata()

        assert "active_modules" in metadata, "Should include active module count"
        assert "skipped_modules" in metadata, "Should include skipped modules list"
        assert metadata["active_modules"] == 1, "Only expertise should be active"
        assert (
            "metrics" in metadata["skipped_modules"]
        ), "metrics should be in skipped list"
        assert (
            "context_awareness" in metadata["skipped_modules"]
        ), "context_awareness should be in skipped list"
