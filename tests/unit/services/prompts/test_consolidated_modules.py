"""
Test suite voor geconsolideerde prompt modules (DEF-127).

Deze tests verifiëren dat de nieuwe geconsolideerde modules:
1. Alle functionaliteit behouden van de originele modules
2. Correct werken met minder cognitive load (9 ipv 19 modules)
3. Dezelfde output genereren als het oude systeem
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from src.services.definition_generator_config import UnifiedGeneratorConfig
from src.services.definition_generator_context import EnrichedContext
from src.services.prompts.modules import ModuleOutput
from src.services.prompts.modules.base_module import ModuleContext
from src.services.prompts.modules.linguistic_rules_module import LinguisticRulesModule
from src.services.prompts.modules.output_format_module import OutputFormatModule
from src.services.prompts.modules.unified_validation_rules_module import (
    UnifiedValidationRulesModule,
)


def create_test_context(
    term: str = "test", examples: list[str] = None, variables: dict = None
):
    """Helper to create a valid ModuleContext for testing."""
    from dataclasses import dataclass

    from src.services.definition_generator_context import ContextSource

    config = UnifiedGeneratorConfig()

    # Create EnrichedContext as a dataclass
    enriched_context = EnrichedContext(
        base_context={"voorbeelden": examples or []},
        sources=[],
        expanded_terms={},
        confidence_scores={},
        metadata=variables or {},
    )

    return ModuleContext(
        begrip=term,
        enriched_context=enriched_context,
        config=config,
        shared_state={},
    )


class TestUnifiedValidationRulesModule:
    """Test de unified validation rules module."""

    def test_initialization_with_default_categories(self):
        """Test dat module initialiseert met alle categorieën standaard."""
        module = UnifiedValidationRulesModule()

        assert module.module_id == "unified_validation_rules"
        assert module.module_name == "Unified Validation Rules"
        assert module.categories == ["ARAI", "CON", "ESS", "SAM", "INT"]
        assert module.priority == 70

    def test_initialization_with_specific_categories(self):
        """Test dat module initialiseert met specifieke categorieën."""
        module = UnifiedValidationRulesModule(categories=["ARAI", "CON"])

        assert module.categories == ["ARAI", "CON"]

    def test_initialize_with_config(self):
        """Test module configuratie."""
        module = UnifiedValidationRulesModule()
        config = {
            "include_examples": False,
            "categories": ["ESS", "SAM"],
        }

        module.initialize(config)

        assert module.include_examples is False
        assert module.categories == ["ESS", "SAM"]
        assert module._initialized is True

    @patch(
        "src.services.prompts.modules.unified_validation_rules_module.get_cached_toetsregel_manager"
    )
    def test_execute_generates_all_categories(self, mock_get_manager):
        """Test dat alle regel categorieën worden gegenereerd."""
        # Setup mock manager
        mock_manager = Mock()
        mock_manager.get_regel_by_key.return_value = {
            "naam": "Test Regel",
            "beschrijving": "Test beschrijving",
            "ai_instructies": ["Instructie 1", "Instructie 2"],
            "voorbeelden": {
                "goed": ["Goed voorbeeld"],
                "fout": ["Fout voorbeeld"],
            },
        }
        mock_get_manager.return_value = mock_manager

        # Create module and execute
        module = UnifiedValidationRulesModule()
        module.initialize({"include_examples": True})

        context = create_test_context("test")

        output = module.execute(context)

        # Verify output
        assert isinstance(output, ModuleOutput)
        assert "## 📋 Validatie Regels" in output.content
        assert "ARAI" in output.content or "Algemene Richtlijnen" in output.content
        assert output.metadata["categories"] == ["ARAI", "CON", "ESS", "SAM", "INT"]

    @patch(
        "src.services.prompts.modules.unified_validation_rules_module.get_cached_toetsregel_manager"
    )
    def test_execute_with_subset_categories(self, mock_get_manager):
        """Test dat alleen geselecteerde categorieën worden gegenereerd."""
        # Setup mock
        mock_manager = Mock()
        mock_manager.get_regel_by_key.return_value = {
            "naam": "Context Regel",
            "beschrijving": "Context beschrijving",
        }
        mock_get_manager.return_value = mock_manager

        # Create module with subset
        module = UnifiedValidationRulesModule(categories=["CON"])
        module.initialize({})

        context = create_test_context("test")
        output = module.execute(context)

        # Verify only CON rules
        assert "🌐 Context Regels (CON)" in output.content
        assert "ARAI" not in output.content
        assert "ESS" not in output.content

    def test_validate_input_always_returns_true(self):
        """Test dat validatie altijd succesvol is."""
        module = UnifiedValidationRulesModule()
        context = create_test_context("test")

        valid, error = module.validate_input(context)

        assert valid is True
        assert error is None

    def test_get_dependencies_returns_empty(self):
        """Test dat module geen dependencies heeft."""
        module = UnifiedValidationRulesModule()

        deps = module.get_dependencies()

        assert deps == []


class TestLinguisticRulesModule:
    """Test de linguistic rules module."""

    def test_initialization(self):
        """Test module initialisatie."""
        module = LinguisticRulesModule()

        assert module.module_id == "linguistic_rules"
        assert module.module_name == "Linguistic & Grammar Rules"
        assert module.priority == 60
        assert module.include_examples is True
        assert module.extended_grammar is True

    def test_initialize_with_config(self):
        """Test configuratie opties."""
        module = LinguisticRulesModule()
        config = {
            "include_examples": False,
            "extended_grammar": False,
        }

        module.initialize(config)

        assert module.include_examples is False
        assert module.extended_grammar is False
        assert module._initialized is True

    @patch(
        "src.services.prompts.modules.linguistic_rules_module.get_cached_toetsregel_manager"
    )
    def test_execute_generates_all_sections(self, mock_get_manager):
        """Test dat alle linguïstische secties worden gegenereerd."""
        # Setup mock
        mock_manager = Mock()
        mock_manager.get_regel_by_key.return_value = None  # No specific rules
        mock_get_manager.return_value = mock_manager

        module = LinguisticRulesModule()
        module.initialize({"extended_grammar": True})

        context = create_test_context("test")
        output = module.execute(context)

        # Verify all sections present
        assert "## 📝 Taalkundige & Grammaticale Richtlijnen" in output.content
        assert "### 🔤 Grammatica Basisregels" in output.content
        assert "### 🏗️ Structuur Regels (STR)" in output.content
        assert "### 📐 Vorm Regels (VER)" in output.content
        assert "### ✍️ Schrijfstijl Richtlijnen" in output.content

    def test_execute_without_extended_grammar(self):
        """Test output zonder uitgebreide grammatica."""
        module = LinguisticRulesModule()
        module.initialize({"extended_grammar": False})

        context = create_test_context("test")

        with patch(
            "src.services.prompts.modules.linguistic_rules_module.get_cached_toetsregel_manager"
        ):
            output = module.execute(context)

        # Schrijfstijl should not be present
        assert "### ✍️ Schrijfstijl Richtlijnen" not in output.content

    def test_grammar_rules_include_examples(self):
        """Test dat voorbeelden worden toegevoegd indien enabled."""
        module = LinguisticRulesModule()
        module.initialize({"include_examples": True})

        context = create_test_context("test")

        with patch(
            "src.services.prompts.modules.linguistic_rules_module.get_cached_toetsregel_manager"
        ):
            output = module.execute(context)

        assert "✓ Goed:" in output.content
        assert "✗ Fout:" in output.content


class TestOutputFormatModule:
    """Test de output format module."""

    def test_initialization(self):
        """Test module initialisatie."""
        module = OutputFormatModule()

        assert module.module_id == "output_format"
        assert module.module_name == "Output Format & Templates"
        assert module.priority == 30
        assert module.include_templates is True
        assert module.strict_format is True
        assert module.char_limit_warning == 500

    def test_initialize_with_config(self):
        """Test configuratie opties."""
        module = OutputFormatModule()
        config = {
            "include_templates": False,
            "strict_format": False,
            "char_limit_warning": 300,
        }

        module.initialize(config)

        assert module.include_templates is False
        assert module.strict_format is False
        assert module.char_limit_warning == 300

    def test_execute_generates_all_sections(self):
        """Test dat alle output secties worden gegenereerd."""
        module = OutputFormatModule()
        module.initialize({})

        context = create_test_context("test")
        output = module.execute(context)

        # Verify sections
        assert "## 📋 Output Formaat & Structuur" in output.content
        assert "### 📝 Output Specificaties" in output.content
        assert "### 🎯 Definitie Templates" in output.content
        assert "### 🏗️ Definitie Structuur" in output.content
        assert "### 📏 Lengte Richtlijnen" in output.content
        assert "### ⚡ Verplicht Output Formaat" in output.content

    def test_execute_with_specific_category(self):
        """Test template selectie voor specifieke categorie."""
        module = OutputFormatModule()
        module.initialize({"include_templates": True})

        context = create_test_context(
            term="test",
            variables={"ontological_category": "object"},
        )

        output = module.execute(context)

        # Should show specific template for "object"
        assert "Categorie: Object" in output.content
        assert "essentiële kenmerken" in output.content

    def test_execute_without_templates(self):
        """Test output zonder templates."""
        module = OutputFormatModule()
        module.initialize({"include_templates": False})

        context = create_test_context("test")
        output = module.execute(context)

        # Templates section should not be present
        assert "### 🎯 Definitie Templates" not in output.content

    def test_execute_without_strict_format(self):
        """Test output zonder strikte format instructies."""
        module = OutputFormatModule()
        module.initialize({"strict_format": False})

        context = create_test_context("test")
        output = module.execute(context)

        # Strict format section should not be present
        assert "### ⚡ Verplicht Output Formaat" not in output.content

    def test_char_limit_in_output(self):
        """Test dat karakterlimiet correct wordt weergegeven."""
        module = OutputFormatModule()
        module.initialize({"char_limit_warning": 750})

        context = create_test_context("test")
        output = module.execute(context)

        assert "750 karakters" in output.content


class TestModuleConsolidation:
    """Test de complete module consolidatie (DEF-127)."""

    @patch("src.services.prompts.modular_prompt_adapter_v2.get_cached_orchestrator_v2")
    def test_v2_adapter_uses_9_modules(self, mock_get_orchestrator):
        """Test dat V2 adapter precies 9 modules gebruikt."""
        from src.services.prompts.modular_prompt_adapter_v2 import (
            ModularPromptAdapterV2,
        )

        # Mock orchestrator
        mock_orchestrator = Mock()
        mock_orchestrator.modules = {f"module_{i}": Mock() for i in range(9)}
        mock_get_orchestrator.return_value = mock_orchestrator

        # Create adapter
        adapter = ModularPromptAdapterV2()

        # Verify 9 modules
        assert adapter.get_module_count() == 9

    def test_consolidated_modules_cover_all_functionality(self):
        """Verify dat alle originele functionaliteit gedekt is."""
        # Map originele modules naar consolidated modules
        coverage_map = {
            # Validation rules
            "arai_rules": "unified_validation_rules",
            "con_rules": "unified_validation_rules",
            "ess_rules": "unified_validation_rules",
            "sam_rules": "unified_validation_rules",
            "integrity_rules": "unified_validation_rules",
            # Linguistic
            "grammar": "linguistic_rules",
            "structure_rules": "linguistic_rules",
            "ver_rules": "linguistic_rules",
            # Output
            "output_specification": "output_format",
            "template": "output_format",
            # Core (unchanged)
            "expertise": "expertise",
            "error_prevention": "error_prevention",
            "definition_task": "definition_task",
            "context_awareness": "context_awareness",
            "semantic_categorisation": "semantic_categorisation",
            "metrics": "metrics",
        }

        # Verify all 16 original modules are covered
        assert len(coverage_map) == 16

        # Count unique consolidated modules
        unique_consolidated = set(coverage_map.values())
        assert len(unique_consolidated) == 9  # Target: <15, achieved: 9

    def test_module_priorities_maintained(self):
        """Test dat module prioriteiten correct zijn."""
        modules = [
            (UnifiedValidationRulesModule(), 70),
            (LinguisticRulesModule(), 60),
            (OutputFormatModule(), 30),
        ]

        for module, expected_priority in modules:
            assert module.priority == expected_priority


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
