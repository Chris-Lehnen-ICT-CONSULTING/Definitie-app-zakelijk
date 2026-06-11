#!/usr/bin/env python
"""Smoke test voor definitie generatie na US-043 wijzigingen."""

import asyncio
import logging
import os
import sys

import pytest

pytestmark = [pytest.mark.smoke]

# Skip-guard: deze smoke-test doet een ECHTE AI-generatie (kost API-calls).
# Draait alleen via `make test-smoke` (smoke-marker) én alleen met een API-key.
_HAS_API_KEY = bool(os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sys.path.insert(0, "src")


async def _run_generation_smoke() -> bool:
    """Test basis definitie generatie functionaliteit. Returnt True bij succes."""

    from services.service_factory import get_definition_service

    # Get V2 service (always V2 na US-043)
    service = get_definition_service()

    # Test context (list-based per US-043)
    context_dict = {
        "organisatorisch": ["Openbaar Ministerie"],
        "juridisch": ["Strafrecht"],
        "wettelijk": ["Wetboek van Strafrecht"],
    }

    logger.info("Starting smoke test for definition generation...")

    try:
        # Generate definition (use generate_definition method)
        result = await service.generate_definition(
            begrip="verdachte", context_dict=context_dict
        )

        # Check result
        if result and result.get("success"):
            logger.info("✅ Generation successful!")
            logger.info(
                f"  Definitie: {result.get('definitie_gecorrigeerd', '')[:100]}..."
            )

            # Check validation
            if result.get("validation_details"):
                score = result["validation_details"].get("overall_score", 0)
                logger.info(f"  Validation score: {score}")

            # Check voorbeelden
            voorbeelden = result.get("voorbeelden", {})
            if voorbeelden:
                logger.info(f"  Voorbeelden types: {list(voorbeelden.keys())}")

            return True
        logger.error(f"❌ Generation failed: {result}")
        return False

    except Exception as e:
        logger.error(f"❌ Smoke test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


@pytest.mark.asyncio
@pytest.mark.skipif(
    not _HAS_API_KEY, reason="geen AI API-key beschikbaar (OPENAI/ANTHROPIC)"
)
async def test_smoke_generation():
    """Pytest-collecteerbare smoke-test (vereist API-key, draait via make test-smoke)."""
    assert await _run_generation_smoke(), "Definitie-generatie smoke-test faalde"


if __name__ == "__main__":
    success = asyncio.run(_run_generation_smoke())

    if success:
        print("\n" + "=" * 60)
        print("✅ SMOKE TEST PASSED - Core functionality works!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("❌ SMOKE TEST FAILED - Core functionality broken!")
        print("=" * 60)
        sys.exit(1)
