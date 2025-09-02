"""
Test script voor de nieuwe modulaire prompt architectuur.

Dit script test de PromptOrchestrator met de geïmplementeerde modules.
"""

import logging
from dataclasses import dataclass
from typing import Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import de nieuwe modules
from src.services.prompts.modules import (
    PromptOrchestrator,
    ExpertiseModule,
    ContextAwarenessModule,
    SemanticCategorisationModule,
    QualityRulesModule,
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


def test_orchestrator():
    """Test de orchestrator met enkele modules."""

    print("=== Test Modular Prompt Orchestrator ===\n")

    # 1. Maak orchestrator
    orchestrator = PromptOrchestrator(max_workers=2)
    print("✅ Orchestrator aangemaakt")

    # 2. Registreer modules
    modules = [
        ExpertiseModule(),
        ContextAwarenessModule(),
        SemanticCategorisationModule(),
        QualityRulesModule()
    ]

    for module in modules:
        orchestrator.register_module(module)
        print(f"✅ Module '{module.module_id}' geregistreerd")

    # 3. Initialize modules
    module_config = {
        "expertise": {},
        "context_awareness": {},
        "semantic_categorisation": {"detailed_guidance": True},
        "quality_rules": {"include_arai_rules": True, "include_examples": True}
    }
    orchestrator.initialize_modules(module_config)
    print("\n✅ Alle modules geïnitialiseerd")

    # 4. Test met verschillende scenario's
    test_cases = [
        {
            "name": "Proces begrip met context",
            "begrip": "sanctionering",
            "context": MockEnrichedContext(
                base_context={
                    "organisatorisch": ["DJI", "OM"],
                    "domein": ["Strafrechtketen"]
                },
                metadata={
                    "ontologische_categorie": "proces"
                }
            )
        },
        {
            "name": "Resultaat begrip zonder context",
            "begrip": "sanctie",
            "context": MockEnrichedContext(
                base_context={},
                metadata={
                    "ontologische_categorie": "resultaat"
                }
            )
        },
        {
            "name": "Type begrip met NP context",
            "begrip": "maatregel",
            "context": MockEnrichedContext(
                base_context={
                    "organisatorisch": ["NP"],
                    "domein": ["Nederlands Politie"]
                },
                metadata={
                    "ontologische_categorie": "type"
                }
            )
        }
    ]

    for test_case in test_cases:
        print(f"\n\n=== Test Case: {test_case['name']} ===")
        print(f"Begrip: {test_case['begrip']}")

        try:
            # Build prompt
            prompt = orchestrator.build_prompt(
                begrip=test_case['begrip'],
                context=test_case['context'],
                config=MockUnifiedConfig()
            )

            print(f"\n📝 Gegenereerde prompt ({len(prompt)} karakters):\n")
            print("-" * 80)
            print(prompt)
            print("-" * 80)

            # Toon metadata
            metadata = orchestrator.get_execution_metadata()
            print(f"\n📊 Execution metadata:")
            print(f"- Execution time: {metadata['execution_time_ms']}ms")
            print(f"- Modules executed: {metadata['total_modules']}")
            print(f"- Execution batches: {metadata['execution_batches']}")

            # Module-specifieke metadata
            print(f"\n📋 Module outputs:")
            for module_id, module_meta in metadata['module_metadata'].items():
                print(f"- {module_id}: {module_meta}")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

    # 5. Test dependency resolution
    print("\n\n=== Dependency Resolution Test ===")
    try:
        batches = orchestrator.resolve_execution_order()
        print(f"Execution batches: {batches}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # 6. Show registered modules info
    print("\n\n=== Registered Modules Info ===")
    for module_info in orchestrator.get_registered_modules():
        print(f"\n{module_info['module_name']} ({module_info['module_id']}):")
        print(f"  Dependencies: {module_info['dependencies']}")
        print(f"  Info: {module_info['info']}")


if __name__ == "__main__":
    test_orchestrator()
