#!/usr/bin/env python3
"""Debug script to trace where async generation hangs."""

import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.services.service_factory import ServiceFactory

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


async def test_with_debug():
    """Test with detailed debug output."""
    print("=== ASYNC DEBUG TEST ===")
    print("1. Creating ServiceFactory...")

    factory = ServiceFactory()
    print("2. ServiceFactory created successfully")

    begrip = "overeenkomst"
    context_dict = {
        "organisatorisch": ["Rechtbank"],
        "juridisch": ["Burgerlijk recht"],
        "wettelijk": ["BW"],
    }

    print(f"3. Calling generate_definition for: {begrip}")
    print(f"   Context: {context_dict}")

    try:
        # Add timeout to narrow down where it hangs
        print("4. Starting async call...")
        result = await asyncio.wait_for(
            factory.generate_definition(begrip, context_dict), timeout=10.0
        )
        print("5. Async call completed")
        print(f"Result: {result}")

    except TimeoutError:
        print("ERROR: Async call timed out after 10 seconds")
        print("The generate_definition method is hanging")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("Starting async debug test...")
    asyncio.run(test_with_debug())
