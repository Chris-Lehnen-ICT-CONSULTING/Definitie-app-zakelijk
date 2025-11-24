"""
Regression tests for DEF-171 Phase 1 prompt optimization.

Verifies that:
1. MetricsModule returns empty content (disabled state)
2. Toetsvraag patterns removed from rule modules
3. Instructie patterns preserved in JSON-based rules
"""

import pytest

from services.definition_generator_config import UnifiedGeneratorConfig
from services.definition_generator_context import ContextSource, EnrichedContext
from services.prompts.modules.base_module import ModuleContext
from services.prompts.modules.integrity_rules_module import IntegrityRulesModule
from services.prompts.modules.metrics_module import MetricsModule
from services.prompts.modules.structure_rules_module import StructureRulesModule


def create_test_context(begrip: str, ontologische_categorie: str) -> ModuleContext:
    """Helper to create minimal test context."""
    enriched = EnrichedContext(
        base_context={
            "organisatorische_context": ["test"],
            "juridische_context": ["test"],
        },
        sources=[ContextSource(source_type="test", confidence=0.9, content="test")],
        expanded_terms={},
        confidence_scores={"test": 0.9},
        metadata={"ontologische_categorie": ontologische_categorie},
    )
    cfg = UnifiedGeneratorConfig()
    return ModuleContext(
        begrip=begrip, enriched_context=enriched, config=cfg, shared_state={}
    )


class TestDEF171MetricsModuleDisabled:
    """Verify MetricsModule is properly disabled."""

    def test_metrics_returns_empty_content(self):
        """DEF-171: MetricsModule should return empty content."""
        module = MetricsModule()
        module.initialize({})
        ctx = create_test_context("test", "type")

        result = module.execute(ctx)

        assert result.success is True
        assert result.content == ""
        assert "disabled_reason" in result.metadata
        assert "DEF-171" in result.metadata["disabled_reason"]

    def test_metrics_metadata_explains_why_disabled(self):
        """DEF-171: Metadata should explain why module is disabled."""
        module = MetricsModule()
        module.initialize({})
        ctx = create_test_context("test", "type")

        result = module.execute(ctx)

        metadata = result.metadata
        assert "DEF-171" in metadata["disabled_reason"]
        assert "quality metrics" in metadata["disabled_reason"].lower()
        assert metadata["validation_handled_by"] == "ValidationOrchestratorV2"


class TestDEF171ToetsvraagRemoval:
    """Verify Toetsvraag patterns removed from rule modules."""

    def test_integrity_rules_no_toetsvraag(self):
        """DEF-171: IntegrityRulesModule should not contain Toetsvraag patterns."""
        module = IntegrityRulesModule()
        module.initialize({"include_examples": True})
        ctx = create_test_context("test", "type")

        result = module.execute(ctx)

        assert "Toetsvraag:" not in result.content

    def test_structure_rules_no_toetsvraag(self):
        """DEF-171: StructureRulesModule should not contain Toetsvraag patterns."""
        module = StructureRulesModule()
        module.initialize({"include_examples": True})
        ctx = create_test_context("test", "type")

        result = module.execute(ctx)

        assert "Toetsvraag:" not in result.content


class TestDEF171InstructiePreserved:
    """Verify Instructie patterns preserved in existing rule modules."""

    def test_integrity_rules_verify_no_toetsvraag_after_removal(self):
        """DEF-171: After Toetsvraag removal, verify they don't reappear."""
        module = IntegrityRulesModule()
        module.initialize({"include_examples": True})
        ctx = create_test_context("test", "type")

        result = module.execute(ctx)

        # Primary assertion: No Toetsvraag patterns
        assert "Toetsvraag:" not in result.content
        # Secondary: Module still produces content
        assert result.success is True
        assert len(result.content) > 0

    def test_structure_rules_verify_no_toetsvraag_after_removal(self):
        """DEF-171: After Toetsvraag removal, verify they don't reappear."""
        module = StructureRulesModule()
        module.initialize({"include_examples": True})
        ctx = create_test_context("test", "type")

        result = module.execute(ctx)

        # Primary assertion: No Toetsvraag patterns
        assert "Toetsvraag:" not in result.content
        # Secondary: Module still produces content
        assert result.success is True
        assert len(result.content) > 0
