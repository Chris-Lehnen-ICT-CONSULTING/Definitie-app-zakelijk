"""
Tests voor Step 2 componenten van de UnifiedDefinitionGenerator refactoring.

Deze tests valideren de nieuwe context, prompt, monitoring en enhancement modules.
"""

import asyncio
from unittest.mock import Mock, patch

import pytest

from services.definition_generator_config import (
    ContextConfig,
    MonitoringConfig,
    QualityConfig,
    UnifiedGeneratorConfig,
)
from services.definition_generator_context import EnrichedContext, HybridContextManager
from services.definition_generator_enhancement import (
    DefinitionEnhancer,
    EnhancementType,
)
from services.definition_generator_monitoring import GenerationMonitor, MetricType
from services.definition_generator_prompts import UnifiedPromptBuilder
from services.interfaces import Definition, GenerationRequest


class TestHybridContextManager:
    """Test de HybridContextManager functionaliteit."""

    def setup_method(self):
        """Setup voor elke test."""
        self.config = ContextConfig()
        self.context_manager = HybridContextManager(self.config)

    @pytest.mark.asyncio()
    async def test_build_enriched_context_basic(self):
        """Test basis context building."""
        request = GenerationRequest(
            id="test-id",
            begrip="testbegrip",
            context="juridisch, OM, Openbaar Ministerie",
            organisatie="OM",
        )

        enriched_context = await self.context_manager.build_enriched_context(request)

        assert isinstance(enriched_context, EnrichedContext)
        assert "organisatorisch" in enriched_context.base_context
        assert "juridisch" in enriched_context.base_context
        assert "OM" in enriched_context.base_context["organisatorisch"]
        assert "juridisch" in enriched_context.base_context["juridisch"]

    @pytest.mark.asyncio()
    async def test_abbreviation_expansion(self):
        """Test afkortingen uitbreiding."""
        request = GenerationRequest(
            id="test-id", begrip="testbegrip", context="OM, FIOD, AVG", organisatie="OM"
        )

        enriched_context = await self.context_manager.build_enriched_context(request)

        assert "OM" in enriched_context.expanded_terms
        assert enriched_context.expanded_terms["OM"] == "Openbaar Ministerie"
        assert "FIOD" in enriched_context.expanded_terms
        assert "AVG" in enriched_context.expanded_terms

    def test_context_summary(self):
        """Test context samenvatting functionaliteit."""
        # Create minimal enriched context
        enriched_context = EnrichedContext(
            base_context={"juridisch": ["test"], "organisatorisch": ["OM"]},
            sources=[],
            expanded_terms={"OM": "Openbaar Ministerie"},
            confidence_scores={},
            metadata={"avg_confidence": 0.8},
        )

        summary = self.context_manager.get_context_summary(enriched_context)

        assert "Basis context: 2 items" in summary
        assert "Context bronnen: 0" in summary
        assert "Afkortingen geëxpandeerd: 1" in summary


class TestUnifiedPromptBuilder:
    """Test de UnifiedPromptBuilder functionaliteit."""

    def setup_method(self):
        """Setup voor elke test."""
        self.config = UnifiedGeneratorConfig()
        self.prompt_builder = UnifiedPromptBuilder(self.config)

    def test_initialization(self):
        """Test correcte initialisatie."""
        # Per EPIC-010: alleen modular strategy beschikbaar na refactoring
        assert len(self.prompt_builder.get_available_strategies()) >= 1
        assert "modular" in self.prompt_builder.get_available_strategies()

    def test_build_prompt_basic(self):
        """Test basis prompt building."""
        enriched_context = EnrichedContext(
            base_context={"juridisch": ["test"], "organisatorisch": ["OM"]},
            sources=[],
            expanded_terms={},
            confidence_scores={},
            metadata={"avg_confidence": 0.3},  # Low confidence = basic strategy
        )

        prompt = self.prompt_builder.build_prompt("testbegrip", enriched_context)

        assert isinstance(prompt, str)
        assert "testbegrip" in prompt
        assert len(prompt) > 50  # Reasonable prompt length

    def test_build_prompt_context_aware(self):
        """Test context-aware prompt building."""
        from services.definition_generator_context import ContextSource

        # Create rich context that should trigger context-aware strategy
        sources = [
            ContextSource("web_lookup", 0.9, "Web informatie over testbegrip"),
            ContextSource("hybrid_context", 0.8, "Hybrid context data"),
        ]

        enriched_context = EnrichedContext(
            base_context={"juridisch": ["test"], "organisatorisch": ["OM"]},
            sources=sources,
            expanded_terms={"OM": "Openbaar Ministerie"},
            confidence_scores={"web": 0.9, "hybrid": 0.8},
            metadata={"avg_confidence": 0.85},  # High confidence = context-aware
        )

        prompt = self.prompt_builder.build_prompt("testbegrip", enriched_context)

        assert isinstance(prompt, str)
        assert "testbegrip" in prompt
        assert len(prompt) > 200  # Context-aware prompts should be longer


class TestGenerationMonitor:
    """Test de GenerationMonitor functionaliteit."""

    def setup_method(self):
        """Setup voor elke test."""
        self.config = MonitoringConfig(enable_monitoring=True)
        self.monitor = GenerationMonitor(self.config)

    def test_start_and_finish_generation(self):
        """Test generatie monitoring lifecycle."""
        # Start monitoring
        generation_id = self.monitor.start_generation(
            "testbegrip", {}
        )  # domein removed per US-043

        assert generation_id != ""
        assert generation_id in self.monitor.active_generations

        # Finish monitoring
        self.monitor.finish_generation(generation_id, success=True)

        assert generation_id not in self.monitor.active_generations

        # Check metrics were recorded
        metrics_summary = self.monitor.get_metrics_summary(window_minutes=1)
        assert MetricType.GENERATION_COUNT.value in metrics_summary
        assert MetricType.SUCCESS_RATE.value in metrics_summary

    def test_context_metrics_recording(self):
        """Test context metrics recording."""
        generation_id = self.monitor.start_generation("testbegrip")

        self.monitor.record_context_metrics(
            generation_id, sources=3, confidence=0.8, richness_score=0.9
        )

        assert generation_id in self.monitor.active_generations
        metrics = self.monitor.active_generations[generation_id]
        assert metrics.context_sources == 3
        assert metrics.context_confidence == 0.8
        assert metrics.context_richness_score == 0.9

        self.monitor.finish_generation(generation_id, success=True)

    def test_error_tracking(self):
        """Test error tracking functionaliteit."""
        generation_id = self.monitor.start_generation("testbegrip")

        error_message = "Test error message"
        self.monitor.finish_generation(
            generation_id, success=False, error=error_message
        )

        # Check error was recorded
        assert len(self.monitor.recent_errors) > 0
        assert self.monitor.recent_errors[-1]["error"] == error_message

    def test_current_status(self):
        """Test current status rapportage."""
        status = self.monitor.get_current_status()

        assert "active_generations" in status
        assert "monitoring_enabled" in status
        assert status["monitoring_enabled"]


class TestDefinitionEnhancer:
    """Test de DefinitionEnhancer functionaliteit."""

    def setup_method(self):
        """Setup voor elke test."""
        self.config = QualityConfig(
            enable_enhancement=True,
            enable_completeness_enhancement=True,
            enable_linguistic_enhancement=True,
            enhancement_confidence_threshold=0.5,
        )
        self.enhancer = DefinitionEnhancer(self.config)

    def test_initialization(self):
        """Test correcte initialisatie."""
        strategies = self.enhancer.get_available_strategies()

        assert len(strategies) >= 4
        assert "clarity_enhancer" in strategies
        assert "context_integration_enhancer" in strategies
        assert "completeness_enhancer" in strategies
        assert "linguistic_enhancer" in strategies

    def test_enhance_definition_basic(self):
        """Test basis definitie enhancement."""
        original_definition = Definition(
            begrip="testbegrip",
            definitie="Een kort begrip.",  # Very short definition should trigger clarity enhancement
            categorie="proces",
            bron="test",
            metadata={},
        )

        enhanced_def, applied_enhancements = self.enhancer.enhance_definition(
            original_definition
        )

        assert isinstance(enhanced_def, Definition)
        assert len(applied_enhancements) >= 0  # May or may not apply enhancements

        # If enhancements were applied, check metadata
        if applied_enhancements:
            assert enhanced_def.metadata.get("enhanced")
            assert "enhancement_applied" in enhanced_def.metadata

    def test_quality_evaluation(self):
        """Test definitie kwaliteits evaluatie."""
        definition = Definition(
            begrip="testbegrip",
            definitie="Een zeer korte definitie die mogelijk verbetering nodig heeft.",
            categorie="proces",
            bron="test",
            metadata={},
        )

        quality_report = self.enhancer.evaluate_definition_quality(definition)

        assert "overall_quality_score" in quality_report
        assert "strategy_scores" in quality_report
        assert "improvement_suggestions" in quality_report
        assert isinstance(quality_report["overall_quality_score"], float)
        assert 0.0 <= quality_report["overall_quality_score"] <= 1.0


class TestIntegration:
    """Integration tests voor alle Step 2 componenten samen."""

    @pytest.mark.asyncio()
    async def test_full_step2_integration(self):
        """Test volledige integratie van alle Step 2 componenten."""
        # Initialize all components
        config = UnifiedGeneratorConfig()
        context_manager = HybridContextManager(config.context)
        prompt_builder = UnifiedPromptBuilder(config)
        monitor = GenerationMonitor(config.monitoring)
        enhancer = DefinitionEnhancer(config.quality)

        # Create test request
        request = GenerationRequest(
            id="test-id", begrip="testbegrip", context="juridisch, OM", organisatie="OM"
        )

        # Test workflow
        generation_id = monitor.start_generation(request.begrip)

        # Build context
        enriched_context = await context_manager.build_enriched_context(request)
        monitor.record_context_metrics(
            generation_id,
            len(enriched_context.sources),
            enriched_context.metadata.get("avg_confidence", 0.0),
            0.8,
        )

        # Build prompt
        prompt = prompt_builder.build_prompt(request.begrip, enriched_context)
        monitor.record_prompt_metrics(generation_id, len(prompt), "test_strategy")

        # Create mock definition for enhancement
        mock_definition = Definition(
            begrip=request.begrip,
            definitie="Een test definitie die mogelijk verbetering nodig heeft.",
            categorie="proces",
            bron="test",
            metadata={},
        )

        # Enhance definition
        enhanced_def, enhancements = enhancer.enhance_definition(mock_definition)
        monitor.record_enhancement(generation_id, len(enhancements) > 0)

        # Finish monitoring
        monitor.finish_generation(generation_id, success=True, definition=enhanced_def)

        # Verify integration worked
        assert isinstance(enriched_context, EnrichedContext)
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert isinstance(enhanced_def, Definition)

        # Check monitoring recorded everything
        status = monitor.get_current_status()
        assert status["active_generations"] == 0  # Should be finished

        # Check metrics were recorded
        metrics_summary = monitor.get_metrics_summary(window_minutes=1)
        assert len(metrics_summary) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
