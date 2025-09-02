"""
Complete test voor alle 8 modules in de modulaire prompt architectuur.

Dit script test de complete PromptOrchestrator met alle modules.
"""

import logging
from dataclasses import dataclass
from typing import Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import alle modules
from src.services.prompts.modules import (
    PromptOrchestrator,
    ExpertiseModule,
    ContextAwarenessModule,
    SemanticCategorisationModule,
    QualityRulesModule,
    ErrorPreventionModule,
    DefinitionTaskModule,
    OutputSpecificationModule,
    ModuleContext
)

# Mock de dependencies voor testing
@dataclass
class MockEnrichedContext:
    """Mock voor EnrichedContext."""
    base_context: dict[str, Any]
    metadata: dict[str, Any]


@dataclass
class MockUnifiedConfig:
    """Mock voor UnifiedGeneratorConfig."""
    pass


def test_complete_orchestrator():
    """Test de orchestrator met alle 8 modules."""

    print("=== Complete Modular Prompt Orchestrator Test ===\n")

    # 1. Maak orchestrator
    orchestrator = PromptOrchestrator(max_workers=4)
    print("✅ Orchestrator aangemaakt")

    # 2. Registreer ALLE modules
    modules = [
        ExpertiseModule(),
        OutputSpecificationModule(),
        ContextAwarenessModule(),
        SemanticCategorisationModule(),
        QualityRulesModule(),
        ErrorPreventionModule(),
        DefinitionTaskModule()
    ]

    for module in modules:
        orchestrator.register_module(module)
        print(f"✅ Module '{module.module_id}' geregistreerd")

    # 3. Initialize modules
    module_config = {
        "expertise": {},
        "output_specification": {
            "default_min_chars": 150,
            "default_max_chars": 350
        },
        "context_awareness": {},
        "semantic_categorisation": {
            "detailed_guidance": True
        },
        "quality_rules": {
            "include_arai_rules": True,
            "include_examples": True
        },
        "error_prevention": {
            "include_validation_matrix": True,
            "extended_forbidden_list": True
        },
        "definition_task": {
            "include_quality_control": True,
            "include_metadata": True
        }
    }
    orchestrator.initialize_modules(module_config)
    print(f"\n✅ Alle {len(modules)} modules geïnitialiseerd")

    # 4. Test scenario
    test_case = {
        "name": "Complete test - sanctionering met DJI context",
        "begrip": "sanctionering",
        "context": MockEnrichedContext(
            base_context={
                "organisatorisch": ["DJI", "OM"],
                "domein": ["Strafrechtketen"]
            },
            metadata={
                "ontologische_categorie": "proces",
                "min_karakters": 200,
                "max_karakters": 400
            }
        )
    }

    print(f"\n=== Test Case: {test_case['name']} ===")
    print(f"Begrip: {test_case['begrip']}")
    print(f"Context: {test_case['context'].base_context}")
    print(f"Metadata: {test_case['context'].metadata}")

    try:
        # Build prompt
        prompt = orchestrator.build_prompt(
            begrip=test_case['begrip'],
            context=test_case['context'],
            config=MockUnifiedConfig()
        )

        # Toon resultaat
        print(f"\n📝 Gegenereerde complete prompt:")
        print("=" * 80)
        print(prompt)
        print("=" * 80)

        # Toon statistieken
        metadata = orchestrator.get_execution_metadata()
        print(f"\n📊 Prompt Statistieken:")
        print(f"- Totale lengte: {len(prompt):,} karakters")
        print(f"- Execution time: {metadata['execution_time_ms']}ms")
        print(f"- Modules executed: {metadata['total_modules']}")
        print(f"- Execution batches: {metadata['execution_batches']}")

        # Module breakdown
        print(f"\n📋 Module Output Breakdown:")
        for module_id, module_meta in metadata['module_metadata'].items():
            print(f"- {module_id}: {module_meta}")

        # Dependency check
        print("\n🔗 Module Dependencies:")
        batches = orchestrator.resolve_execution_order()
        for i, batch in enumerate(batches):
            print(f"  Batch {i+1}: {batch}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    # 5. Vergelijk met verwachte grootte
    print("\n📏 Grootte Vergelijking:")
    print(f"- Legacy systeem: 15-17k karakters")
    print(f"- ModularPromptBuilder: 15-20k karakters")
    print(f"- Volledig modulair systeem: {len(prompt):,} karakters")

    if len(prompt) > 20000:
        print("⚠️  Prompt is groter dan verwacht!")
    else:
        print("✅ Prompt grootte binnen verwachting")


if __name__ == "__main__":
    test_complete_orchestrator()
