#!/usr/bin/env python
"""Test script om voorbeelden generatie met debug logging te testen."""

import asyncio
import logging
import os
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Zet debug flag
os.environ["DEBUG_EXAMPLES"] = "true"

# Add src to path
sys.path.insert(0, "src")


async def test_voorbeelden_generation():
    """Test voorbeelden generatie met debug logging."""

    from services.container import get_container
    from services.interfaces import GenerationRequest

    # Initialize container
    container = get_container()

    # Get the orchestrator directly
    from services.service_factory import ServiceFactory

    service_factory = ServiceFactory(container)

    # Create a test request
    context_dict = {
        "organisatorisch": ["Openbaar Ministerie"],
        "juridisch": ["Strafrecht"],
        "wettelijk": ["Wetboek van Strafrecht"],
    }

    logger.info("Starting voorbeelden generation test for 'verdachte'...")

    # Generate definition with voorbeelden
    result = await service_factory.generate_with_integrated_service(
        begrip="verdachte", context_dict=context_dict
    )

    # Check results
    if result and result.get("success"):
        logger.info("✅ Generation successful")

        # Check voorbeelden
        voorbeelden = result.get("voorbeelden", {})
        if voorbeelden:
            logger.info(f"✅ Voorbeelden found: {list(voorbeelden.keys())}")
            for key, values in voorbeelden.items():
                count = len(values) if isinstance(values, list) else 1
                logger.info(f"  - {key}: {count} items")
        else:
            logger.error("❌ No voorbeelden in result!")

        # Check metadata for generation_id
        metadata = result.get("metadata", {})
        gen_id = metadata.get("generation_id", "NO_ID")
        logger.info(f"Generation ID: {gen_id}")
    else:
        logger.error(f"❌ Generation failed: {result}")

    return result


if __name__ == "__main__":
    # Run the test
    result = asyncio.run(test_voorbeelden_generation())

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    if result and result.get("voorbeelden"):
        print("✅ Voorbeelden generatie werkt!")
        print(f"Gevonden types: {list(result['voorbeelden'].keys())}")
    else:
        print("❌ Voorbeelden generatie faalt - check logs hierboven")
        print("\nKijk naar de [EXAMPLES-X] log entries:")
        print("- [EXAMPLES-A]: Generated in orchestrator")
        print("- [EXAMPLES-B]: Passed through adapter")
        print("- [EXAMPLES-C]: Pre-store in UI")
        print("- [EXAMPLES-C2]: Post-store in UI")
        print("- [EXAMPLES-D]: UI render")
