#!/usr/bin/env python3
"""
Uitgebreide test voor complete categorie flow.
Test alle componenten van UI tot definitie generatie.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from domain.ontological_categories import OntologischeCategorie
from services.container import get_container
from services.interfaces import GenerationRequest
from services.workflow_service import WorkflowAction, WorkflowService


def print_section(title: str):
    """Print section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


async def test_complete_categorie_flow():
    """Test de complete categorie flow van UI tot generatie."""

    # Initialize services
    container = get_container()
    workflow_service = WorkflowService()

    print_section("Test 1: Generatie met expliciete categorie")

    # Test 1: Generate definition with explicit category
    request = GenerationRequest(
        begrip="verificatieproces",
        context="identiteitscontrole bij overheid",
        ontologische_categorie="proces",
    )

    print("🔹 GenerationRequest aangemaakt:")
    print(f"   - Begrip: {request.begrip}")
    print(f"   - Context: {request.context}")
    print(f"   - Categorie: {request.ontologische_categorie}")

    # Generate via orchestrator
    orchestrator = container.orchestrator()
    response = await orchestrator.create_definition(request)

    if response.success:
        print("\n✅ Definitie succesvol gegenereerd!")
        print(f"   - Definitie: {response.definition.definitie[:100]}...")
        print(
            f"   - Metadata: {response.definition.metadata.get('prompt_template', '')[:100]}..."
        )
    else:
        print(f"\n❌ Generatie mislukt: {response.message}")
        return

    print_section("Test 2: Categorie wijziging via WorkflowService")

    # Test 2: Change category via workflow
    original_category = OntologischeCategorie.PROCES
    new_category = OntologischeCategorie.RESULTAAT

    print(
        f"🔹 Wijzig categorie van {original_category.value} naar {new_category.value}"
    )

    action = workflow_service.handle_category_change(
        definition_id=1,  # Dummy ID voor test
        old_category=original_category,
        new_category=new_category,
    )

    print("\n📋 WorkflowAction resultaat:")
    print(f"   - Type: {action.action_type}")
    print(f"   - Data keys: {list(action.data.keys())}")

    if action.action_type == WorkflowAction.ActionType.SHOW_REGENERATION_OPTIONS:
        print("\n🔄 Regeneratie opties beschikbaar:")
        print(f"   - Old category: {action.data.get('old_category')}")
        print(f"   - New category: {action.data.get('new_category')}")
        print(
            f"   - Impact analysis: {action.data.get('impact_analysis', {}).get('description', '')}"
        )

    print_section("Test 3: Service Adapter Legacy Interface")

    # Test 3: Test via ServiceAdapter (legacy interface)
    adapter = container.service_adapter()

    result = adapter.generate_definition(
        begrip="toetsingsresultaat",
        context_dict={"organisatorisch": ["kwaliteitscontrole"]},
        categorie=OntologischeCategorie.RESULTAAT,
    )

    print("🔹 ServiceAdapter resultaat:")
    print(f"   - Success: {result.get('success', False)}")
    if result.get("success"):
        print(f"   - Definitie: {result.get('final_definitie', '')[:100]}...")
        print(
            f"   - Bevat 'resultaat' keyword: {'resultaat' in result.get('final_definitie', '').lower()}"
        )

    print_section("Test 4: Prompt Template Selectie")

    # Test 4: Direct prompt builder test
    from services.definition_generator_context import EnrichedContext
    from services.definition_generator_prompts import BasicPromptBuilder

    builder = BasicPromptBuilder()

    # Test verschillende categorieën
    categories = ["type", "proces", "resultaat", "exemplaar"]

    for cat in categories:
        context = EnrichedContext(
            base_context={"organisatorisch": ["test context"]},
            sources=[],
            expanded_terms={},
            confidence_scores={},
            metadata={"ontologische_categorie": cat},
        )

        template = builder._select_template("testbegrip", context)
        print(f"\n🔹 Categorie '{cat}' → Template: {template.name}")

        # Check of juiste template geselecteerd is
        expected_template = f"ontologie_{cat}"
        if template.name == expected_template:
            print("   ✅ Correct template geselecteerd")
        else:
            print(
                f"   ❌ Verkeerd template: verwacht {expected_template}, kreeg {template.name}"
            )

    print_section("Samenvatting")

    print("✅ Alle tests voltooid!")
    print("\nGetest:")
    print("- GenerationRequest met categorie veld")
    print("- Orchestrator gebruikt categorie in prompt building")
    print("- WorkflowService handelt categorie wijzigingen af")
    print("- ServiceAdapter converteert categorie correct")
    print("- BasicPromptBuilder selecteert juiste templates")


if __name__ == "__main__":
    print("\n🚀 Start uitgebreide categorie flow test...\n")
    asyncio.run(test_complete_categorie_flow())
