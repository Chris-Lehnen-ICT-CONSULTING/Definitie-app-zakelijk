#!/usr/bin/env python3
"""Test orchestrator directly to bypass adapter."""

import asyncio
import logging
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Enable ALL debug logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

from src.services.container import get_container
from src.services.interfaces import GenerationRequest


async def test_orchestrator():
    """Test orchestrator directly."""
    print("\n=== TESTING ORCHESTRATOR DIRECTLY ===\n")

    print("1. Getting container...")
    container = get_container()

    print("2. Getting orchestrator from container...")
    orchestrator = container.orchestrator()
    print(f"   Orchestrator type: {type(orchestrator).__name__}")

    print("3. Creating GenerationRequest...")
    request = GenerationRequest(
        id=str(uuid.uuid4()),
        begrip="overeenkomst",
        organisatorische_context=["Rechtbank"],
        juridische_context=["Burgerlijk recht"],
        wettelijke_basis=["BW"],
        context="Rechtbank",  # Legacy string field
        organisatie="",
        extra_instructies="",
        ontologische_categorie=None,
        actor="test_script",
        legal_basis="legitimate_interest",
    )
    print(f"   Request ID: {request.id}")

    print("4. Calling orchestrator.create_definition()...")
    try:
        response = await asyncio.wait_for(
            orchestrator.create_definition(request), timeout=20.0
        )
        print("5. Response received!")
        print(f"   Success: {response.success}")
        if response.success and response.definition:
            print(f"   Definition: {response.definition.content[:100]}...")
        return response
    except TimeoutError:
        print("ERROR: Orchestrator call timed out after 20 seconds")
        return None
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = asyncio.run(test_orchestrator())
    if result:
        print(f"\nTest completed: Success={result.success}")
