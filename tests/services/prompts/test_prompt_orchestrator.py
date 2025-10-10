import pytest

from services.definition_generator_config import UnifiedGeneratorConfig
from services.definition_generator_context import (ContextSource,
                                                   EnrichedContext)
from services.prompts.modules.base_module import (BasePromptModule,
                                                  ModuleContext, ModuleOutput)
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
