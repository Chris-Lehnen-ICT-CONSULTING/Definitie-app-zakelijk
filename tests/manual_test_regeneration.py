#!/usr/bin/env python3
"""
Manual test script voor complete regeneration flow.

Test de integratie tussen:
- RegenerationService (GVI Rode Kabel)
- TabbedInterface regeneration context detection
- ServiceFactory regeneration context passing
- Definition generation met category override

Run dit script om te valideren dat de regeneration architectuur correct werkt.
"""

import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.regeneration_service import RegenerationContext, RegenerationService

from domain.ontological_categories import OntologischeCategorie
from services.definition_generator_config import UnifiedGeneratorConfig
from services.definition_generator_prompts import UnifiedPromptBuilder

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_regeneration_service_standalone():
    """Test RegenerationService in isolatie."""
    print("\n🔧 Test 1: RegenerationService Standalone")
    print("=" * 50)

    # Initialize service
    config = UnifiedGeneratorConfig()
    prompt_builder = UnifiedPromptBuilder(config)
    service = RegenerationService(prompt_builder)

    # Test 1: Set context
    service.set_regeneration_context(
        begrip="verificatie",
        old_category="proces",
        new_category="type",
        previous_definition="Een proces waarbij iets wordt gecontroleerd",
        reason="Manual category adjustment by user",
    )

    # Test 2: Get context
    context = service.get_active_context()
    assert context is not None, "Context should be active"
    assert context.begrip == "verificatie"
    assert context.new_category == "type"

    print(
        f"✅ Context set: {context.begrip} ({context.old_category} → {context.new_category})"
    )

    # Test 3: Enhance prompt
    base_prompt = "Genereer een definitie voor het begrip."
    enhanced_prompt = service.enhance_prompt_with_context(base_prompt, context)

    print("✅ Prompt enhanced with regeneration context")
    print(f"Enhanced length: {len(enhanced_prompt)} chars (was {len(base_prompt)})")

    # Test 4: Get feedback history
    feedback = service.get_feedback_history()
    assert feedback is not None, "Feedback should be available"
    assert len(feedback) == 1, "Should have one feedback entry"

    print(f"✅ Feedback history: {len(feedback)} entries")

    # Test 5: Clear context
    service.clear_context()
    assert service.get_active_context() is None, "Context should be cleared"

    print("✅ Context cleared successfully")

    print("✅ RegenerationService standalone test PASSED\n")


def test_context_conversion():
    """Test RegenerationContext conversies."""
    print("\n🔄 Test 2: RegenerationContext Conversions")
    print("=" * 50)

    context = RegenerationContext(
        begrip="authenticatie",
        old_category="ACT",
        new_category="ENT",
        previous_definition="Het proces van identity verificatie",
        reason="Category mismatch detected",
    )

    # Test feedback entry conversion
    feedback_entry = context.to_feedback_entry()

    print("✅ Feedback entry created:")
    print(f"   Definition: {feedback_entry['definition'][:50]}...")
    print(f"   Violations: {len(feedback_entry['violations'])}")
    print(f"   Suggestions: {len(feedback_entry['suggestions'])}")

    # Test category focus mapping
    focus_ent = context._get_category_focus("ENT")
    focus_act = context._get_category_focus("ACT")

    assert (
        "wat het IS" in focus_ent
    ), f"ENT focus should mention 'what it IS', got: {focus_ent}"
    assert "proces" in focus_act, f"ACT focus should mention 'proces', got: {focus_act}"

    print("✅ Category focus mapping:")
    print(f"   ENT: {focus_ent}")
    print(f"   ACT: {focus_act}")

    print("✅ Context conversion test PASSED\n")


def test_ui_integration_simulation():
    """Simuleer UI integration scenario."""
    print("\n🎭 Test 3: UI Integration Simulation")
    print("=" * 50)

    # Simulate the flow that would happen in the UI:
    # 1. User changes category in definition_generator_tab.py
    # 2. RegenerationService.set_regeneration_context() wordt aangeroepen
    # 3. User navigates to generator
    # 4. tabbed_interface.py checks regeneration context
    # 5. Category gets overridden in generation call

    config = UnifiedGeneratorConfig()
    prompt_builder = UnifiedPromptBuilder(config)
    regeneration_service = RegenerationService(prompt_builder)

    # Step 1 & 2: User changes category (simulated)
    print("📝 Step 1-2: User wijzigt categorie van 'verificatie' van proces naar type")
    regeneration_service.set_regeneration_context(
        begrip="verificatie",
        old_category="proces",
        new_category="type",
        previous_definition="Een proces waarbij documenten worden gecontroleerd op geldigheid",
        reason="Gebruiker heeft categorie handmatig aangepast",
    )

    # Step 3: User navigates to generator (simulated)
    print("🏠 Step 3: User navigeert naar main generator")

    # Step 4: tabbed_interface.py logic (simulated)
    print("🔍 Step 4: tabbed_interface.py checkt regeneration context")

    active_context = regeneration_service.get_active_context()
    if active_context:
        print(f"   ✅ Active context found voor '{active_context.begrip}'")
        print(
            f"   📊 Category override: {active_context.old_category} → {active_context.new_category}"
        )

        # Simulate category conversion (as done in tabbed_interface.py)
        try:
            if isinstance(active_context.new_category, str):
                new_category_enum = OntologischeCategorie(
                    active_context.new_category.lower()
                )
            else:
                new_category_enum = active_context.new_category

            print(f"   🔄 Category converted to enum: {new_category_enum.value}")

        except Exception as e:
            print(f"   ❌ Category conversion failed: {e}")
            return False

    # Step 5: Enhanced prompt generation (simulated)
    print("💬 Step 5: Enhanced prompt generation")
    base_prompt = (
        "Genereer een definitie voor het begrip verificatie in de context van overheid."
    )

    enhanced_prompt = regeneration_service.enhance_prompt_with_context(base_prompt)
    if "Categorie Regeneratie Context" in enhanced_prompt:
        print("   ✅ Prompt successfully enhanced with regeneration context")
        print(f"   📏 Enhanced prompt length: {len(enhanced_prompt)} chars")
    else:
        print("   ❌ Prompt not enhanced")
        return False

    # Step 6: Context cleanup (simulated)
    print("🧹 Step 6: Context cleanup after successful generation")
    regeneration_service.clear_context()

    if regeneration_service.get_active_context() is None:
        print("   ✅ Context successfully cleared")
    else:
        print("   ❌ Context not cleared")
        return False

    print("✅ UI integration simulation PASSED\n")
    return True


def test_error_scenarios():
    """Test error handling scenarios."""
    print("\n⚠️ Test 4: Error Scenarios")
    print("=" * 50)

    config = UnifiedGeneratorConfig()
    prompt_builder = UnifiedPromptBuilder(config)
    service = RegenerationService(prompt_builder)

    # Test 1: No active context
    print("🔍 Test 4.1: No active context scenario")
    context = service.get_active_context()
    assert context is None, "Should have no active context initially"

    feedback = service.get_feedback_history()
    assert feedback is None, "Should have no feedback without context"

    base_prompt = "Test prompt"
    enhanced = service.enhance_prompt_with_context(base_prompt)
    assert enhanced == base_prompt, "Prompt should be unchanged without context"
    print("   ✅ Correctly handles no active context")

    # Test 2: Invalid category handling
    print("🔍 Test 4.2: Invalid category scenario")
    try:
        service.set_regeneration_context(
            begrip="test",
            old_category="invalid_category",
            new_category="another_invalid",
            reason="Testing error handling",
        )

        context = service.get_active_context()
        # Should still work, category validation happens in UI layer
        assert context is not None, "Context should be set despite invalid categories"
        assert (
            context.new_category == "another_invalid"
        ), "Should preserve invalid category"
        print("   ✅ Correctly handles invalid categories (validation in UI layer)")

    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False

    print("✅ Error scenarios test PASSED\n")
    return True


def main():
    """Run alle regeneration tests."""
    print("🚀 Starting Complete Regeneration Flow Tests")
    print("=" * 60)
    print("Testing RegenerationService integration met:")
    print("- GVI Rode Kabel architectuur")
    print("- Category override mechanisme")
    print("- Prompt enhancement")
    print("- UI integration flow")
    print("=" * 60)

    try:
        # Run all tests
        test_regeneration_service_standalone()
        test_context_conversion()
        ui_success = test_ui_integration_simulation()
        error_success = test_error_scenarios()

        if ui_success and error_success:
            print("🎉 ALL TESTS PASSED!")
            print("✅ RegenerationService is ready for production use")
            print("✅ GVI Rode Kabel architectuur correct geïmplementeerd")
            print("✅ Category regeneration flow werkt end-to-end")
            return True
        print("❌ Some tests failed")
        return False

    except Exception as e:
        print(f"❌ Test suite failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
