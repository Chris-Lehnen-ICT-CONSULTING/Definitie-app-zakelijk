#!/usr/bin/env python3
"""
Manual test voor prompt debug sectie.

Dit script test of de GPT prompts correct worden opgeslagen en
weergegeven in de UI debug sectie.
"""

import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.container import get_container
from services.interfaces import GenerationRequest
from services.service_factory import ServiceAdapter

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def test_prompt_storage():
    """Test of prompts correct worden opgeslagen."""
    print("\n=== Test Prompt Debug Functionaliteit ===\n")

    # 1. Maak service adapter
    print("1. Initialiseer services...")
    container = get_container()
    adapter = ServiceAdapter(container)

    # 2. Genereer een definitie
    print("\n2. Genereer definitie voor 'algoritme'...")
    request = GenerationRequest(
        id="test-id",
        begrip="algoritme",
        context="Een reeks instructies voor het oplossen van een probleem",
        organisatie="Test Organisatie")

    # Call via adapter (die sync interface biedt)
    result = adapter.generate_definition(
        begrip=request.begrip,
        context_dict={
            "organisatorisch": [request.context or ""],
            "domein": [request.domein or ""],
        },
        organisatie=request.organisatie)

    # 3. Check resultaat structuur
    print("\n3. Analyseer resultaat structuur...")
    print(f"   - Result type: {type(result).__name__}")
    print(f"   - Success: {result.success}")

    if hasattr(result, "metadata"):
        print("   - Heeft metadata: Ja")
        if result.metadata:
            print(f"   - Metadata keys: {list(result.metadata.keys())}")
            if "prompt_template" in result.metadata:
                print("   ✅ prompt_template in metadata")
                print(
                    f"   - Prompt lengte: {len(result.metadata['prompt_template'])} chars"
                )
            else:
                print("   ❌ prompt_template NIET in metadata")
    else:
        print("   - Heeft metadata: Nee")

    # Check direct prompt_template
    if hasattr(result, "prompt_template"):
        print("   ✅ Direct prompt_template attribuut aanwezig")
        print(f"   - Prompt lengte: {len(result.prompt_template)} chars")
    else:
        print("   ❌ Geen direct prompt_template attribuut")

    # 4. Simuleer wat de UI doet
    print("\n4. Simuleer UI toegang tot prompt...")

    # Dit is wat definition_generator_tab.py doet
    agent_result = result  # In UI komt dit uit generation_result["agent_result"]

    prompt_found = False
    prompt_location = None

    # Check metadata eerst (zoals de UI fix doet)
    if hasattr(agent_result, "metadata") and agent_result.metadata:
        if (
            isinstance(agent_result.metadata, dict)
            and "prompt_template" in agent_result.metadata
        ):
            prompt_found = True
            prompt_location = "metadata.prompt_template"
            prompt_preview = agent_result.metadata["prompt_template"][:200] + "..."

    # Check direct attribuut
    if not prompt_found and hasattr(agent_result, "prompt_template"):
        prompt_found = True
        prompt_location = "direct prompt_template"
        prompt_preview = agent_result.prompt_template[:200] + "..."

    if prompt_found:
        print(f"   ✅ Prompt gevonden via: {prompt_location}")
        print(f"   Preview: {prompt_preview}")
    else:
        print("   ❌ Geen prompt gevonden in agent_result")

    # 5. Test saved_record simulatie
    print("\n5. Test saved_record scenario...")

    # In werkelijkheid komt dit uit de database
    class MockSavedRecord:
        def __init__(self, metadata):
            self.metadata = metadata

    if result.metadata and "prompt_template" in result.metadata:
        saved_record = MockSavedRecord(result.metadata)
        print("   ✅ Saved record zou prompt_template bevatten")
    else:
        print("   ❌ Saved record zou GEEN prompt_template bevatten")

    # 6. Conclusie
    print("\n=== Test Conclusie ===")
    if prompt_found:
        print("✅ Prompt debug functionaliteit werkt correct!")
        print(f"   Prompt is toegankelijk via: {prompt_location}")
    else:
        print("❌ Prompt debug functionaliteit werkt NIET!")
        print("   De prompt wordt niet correct doorgegeven naar de UI")

    return prompt_found


def main():
    """Run de test."""
    try:
        success = test_prompt_storage()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test gefaald met error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
