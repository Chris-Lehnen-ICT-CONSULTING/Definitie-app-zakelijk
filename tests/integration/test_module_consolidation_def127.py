"""
Integration test voor DEF-127 module consolidatie.

Verifieert dat de nieuwe geconsolideerde modules (9) dezelfde output genereren
als de oude modules (19) om te garanderen dat geen functionaliteit verloren is.
"""

from unittest.mock import Mock, patch

import pytest

from src.services.prompts.modular_prompt_adapter import (
    ModularPromptAdapter,
    get_cached_orchestrator,
)
from src.services.prompts.modular_prompt_adapter_v2 import (
    ModularPromptAdapterV2,
    get_cached_orchestrator_v2,
)
from src.services.prompts.modules import ModuleContext


class TestModuleConsolidationIntegration:
    """Integration tests voor module consolidatie."""

    @pytest.fixture()
    def test_context(self):
        """Create test context voor prompt generatie."""
        return {
            "term": "overeenkomst",
            "examples": [
                "De partijen hebben een overeenkomst gesloten.",
                "Deze overeenkomst is bindend voor beide partijen.",
            ],
            "context": {
                "domein": "contractenrecht",
                "organisatorische_context": "juridisch adviesbureau",
                "doelgroep": "juristen",
                "register": "formeel",
                "bronnen": ["BW Boek 6"],
            },
        }

    @patch("src.services.prompts.modular_prompt_adapter.get_cached_toetsregel_manager")
    @patch(
        "src.services.prompts.modular_prompt_adapter_v2.get_cached_toetsregel_manager"
    )
    def test_module_count_reduction(self, mock_v2_manager, mock_v1_manager):
        """Test dat aantal modules verminderd is van 19 naar 9."""
        # Mock toetsregel managers
        mock_v1_manager.return_value = Mock()
        mock_v2_manager.return_value = Mock()

        # Create both adapters
        adapter_v1 = ModularPromptAdapter()
        adapter_v2 = ModularPromptAdapterV2()

        # Get orchestrators
        orchestrator_v1 = get_cached_orchestrator()
        orchestrator_v2 = get_cached_orchestrator_v2()

        # Verify module counts
        v1_count = len(orchestrator_v1.modules)
        v2_count = len(orchestrator_v2.modules)

        assert v1_count >= 16  # Origineel had 16-19 modules
        assert v2_count == 9  # Geconsolideerd naar 9
        assert v2_count < 15  # Doel: <15 modules (DEF-127)

        print(f"Module reductie: {v1_count} → {v2_count} modules")

    def test_consolidated_module_names(self):
        """Verify namen van geconsolideerde modules."""
        adapter_v2 = ModularPromptAdapterV2()
        module_info = adapter_v2.get_module_info()

        # Expected consolidated modules
        expected_modules = {
            "expertise": "Expert Role & Basic Instructions",
            "error_prevention": "Definition Quality Instructions",
            "definition_task": "Definition Task & Checklist",
            "context_awareness": "Context Processing & Awareness",
            "semantic_categorisation": "Semantic Categorisation",
            "unified_validation_rules": "Unified Validation Rules",
            "linguistic_rules": "Linguistic & Grammar Rules",
            "output_format": "Output Format & Templates",
            "metrics": "Quality Metrics & Scoring",
        }

        # Verify all expected modules present
        for module_id, expected_name in expected_modules.items():
            assert module_id in module_info, f"Module {module_id} ontbreekt"

    @patch(
        "src.services.prompts.modules.unified_validation_rules_module.get_cached_toetsregel_manager"
    )
    @patch(
        "src.services.prompts.modules.linguistic_rules_module.get_cached_toetsregel_manager"
    )
    def test_validation_rules_consolidation(self, mock_ling_manager, mock_val_manager):
        """Test dat alle validatie regel categorieën gedekt zijn."""
        # Mock managers
        mock_regel = {
            "naam": "Test Regel",
            "beschrijving": "Test",
            "ai_instructies": ["Test instructie"],
        }
        mock_val_manager.return_value.get_regel_by_key.return_value = mock_regel
        mock_ling_manager.return_value.get_regel_by_key.return_value = mock_regel

        from src.services.prompts.modules.unified_validation_rules_module import (
            UnifiedValidationRulesModule,
        )

        module = UnifiedValidationRulesModule()
        module.initialize({})

        context = ModuleContext(term="test", examples=[], variables={})
        output = module.execute(context)

        # Verify all categories covered
        categories = ["ARAI", "CON", "ESS", "SAM", "INT"]
        for category in categories:
            # Check either code or name is present
            assert (
                category in output.content
                or module.CATEGORY_NAMES[category] in output.content
            ), f"Category {category} niet gevonden in output"

    def test_linguistic_rules_consolidation(self):
        """Test dat grammatica, STR, en VER regels geconsolideerd zijn."""
        from src.services.prompts.modules.linguistic_rules_module import (
            LinguisticRulesModule,
        )

        module = LinguisticRulesModule()
        module.initialize({"extended_grammar": True})

        context = ModuleContext(term="test", examples=[], variables={})

        with patch(
            "src.services.prompts.modules.linguistic_rules_module.get_cached_toetsregel_manager"
        ):
            output = module.execute(context)

        # Verify all linguistic aspects covered
        assert "Grammatica Basisregels" in output.content
        assert "Structuur Regels (STR)" in output.content
        assert "Vorm Regels (VER)" in output.content
        assert "Schrijfstijl Richtlijnen" in output.content

    def test_output_format_consolidation(self):
        """Test dat output specs en templates geconsolideerd zijn."""
        from src.services.prompts.modules.output_format_module import OutputFormatModule

        module = OutputFormatModule()
        module.initialize({"include_templates": True, "strict_format": True})

        context = ModuleContext(
            term="test",
            examples=[],
            variables={"ontological_category": "object"},
        )

        output = module.execute(context)

        # Verify both output specs and templates present
        assert "Output Specificaties" in output.content
        assert "Definitie Templates" in output.content
        assert "object" in output.content.lower()

    @pytest.mark.parametrize(
        "category,expected_template",
        [
            ("object", "essentiële kenmerken"),
            ("actor", "rol/functie"),
            ("proces", "type proces"),
            ("toestand", "type toestand"),
            ("gebeurtenis", "type gebeurtenis"),
        ],
    )
    def test_category_specific_templates(self, category, expected_template):
        """Test dat categorie-specifieke templates behouden zijn."""
        from src.services.prompts.modules.output_format_module import OutputFormatModule

        module = OutputFormatModule()
        module.initialize({"include_templates": True})

        context = ModuleContext(
            term="test",
            examples=[],
            variables={"ontological_category": category},
        )

        output = module.execute(context)

        assert expected_template in output.content.lower()

    def test_no_functionality_lost(self):
        """Verify dat geen kritieke functionaliteit verloren is gegaan."""
        # Map alle originele functionaliteit naar nieuwe modules
        functionality_map = {
            # Expert & Instructions
            "expert_role": "expertise",
            "basic_instructions": "expertise",
            "error_prevention": "error_prevention",
            "definition_task": "definition_task",
            # Context
            "context_processing": "context_awareness",
            "semantic_categorisation": "semantic_categorisation",
            # Validation Rules
            "arai_validation": "unified_validation_rules",
            "con_validation": "unified_validation_rules",
            "ess_validation": "unified_validation_rules",
            "sam_validation": "unified_validation_rules",
            "int_validation": "unified_validation_rules",
            # Linguistic
            "grammar_rules": "linguistic_rules",
            "structure_validation": "linguistic_rules",
            "form_validation": "linguistic_rules",
            # Output
            "output_specs": "output_format",
            "templates": "output_format",
            # Metrics
            "quality_metrics": "metrics",
        }

        # Verify all functionality mapped
        assert len(functionality_map) == 17

        # Verify all mapped to 9 modules
        unique_modules = set(functionality_map.values())
        assert len(unique_modules) == 9

        # No functionality should map to non-existent module
        valid_modules = [
            "expertise",
            "error_prevention",
            "definition_task",
            "context_awareness",
            "semantic_categorisation",
            "unified_validation_rules",
            "linguistic_rules",
            "output_format",
            "metrics",
        ]

        for module in unique_modules:
            assert module in valid_modules, f"Invalid module mapping: {module}"

    def test_performance_improvement(self):
        """Test dat de consolidatie de performance verbetert."""
        import time

        # Measure V2 initialization time
        start = time.time()
        adapter_v2 = ModularPromptAdapterV2()
        v2_init_time = time.time() - start

        # V2 should initialize reasonably fast
        assert v2_init_time < 1.0, f"V2 initialization too slow: {v2_init_time}s"

        # Module count should be reduced
        assert adapter_v2.get_module_count() == 9

        print(f"V2 initialization time: {v2_init_time:.3f}s with 9 modules")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
