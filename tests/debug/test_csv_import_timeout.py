#!/usr/bin/env python
"""Debug script voor CSV import timeout probleem.

Dit script test de async/sync bridge met dezelfde aanpak als de CSV import.
"""

import asyncio
import logging
import time
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Test 1: Basic async_bridge functionality
def test_async_bridge():
    """Test basic run_async_safe functionality."""
    from ui.helpers.async_bridge import run_async_safe

    async def simple_async():
        await asyncio.sleep(0.1)
        return "success"

    print("Test 1: Basic async_bridge")
    result = run_async_safe(simple_async(), default="failed")
    print(f"Result: {result}")
    assert result == "success", f"Expected 'success', got {result}"
    print("✓ Basic async_bridge works\n")

# Test 2: Test with Streamlit-like event loop
def test_with_existing_loop():
    """Test async_bridge when event loop already exists (like in Streamlit)."""
    print("Test 2: With existing event loop (Streamlit simulation)")

    async def main_loop():
        from ui.helpers.async_bridge import run_async_safe

        async def nested_async():
            await asyncio.sleep(0.1)
            return "nested_success"

        # Dit simuleert wat er in Streamlit gebeurt
        result = run_async_safe(nested_async(), default="failed")
        print(f"Result from nested: {result}")
        return result

    # Streamlit draait al een event loop
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(main_loop())
        print(f"Final result: {result}")
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        loop.close()
    print()

# Test 3: Test import_single isolation
def test_import_service():
    """Test the actual import service call."""
    print("Test 3: Import service call")

    try:
        from src.services.container import ServiceContainer
        from ui.helpers.async_bridge import run_async_safe

        # Initialize service container
        container = ServiceContainer()
        import_service = container.definition_import

        # Test payload (minimal)
        payload = {
            "begrip": "Test begrip",
            "definitie": "Test definitie voor debugging",
            "categorie": "proces",
            "organisatorische_context": ["Test context"],
            "juridische_context": [],
            "wettelijke_basis": []
        }

        print("Calling import_single...")
        start_time = time.time()

        result = run_async_safe(
            import_service.import_single(
                payload,
                duplicate_strategy="skip",
                created_by="debug_test"
            ),
            default=None
        )

        elapsed = time.time() - start_time
        print(f"Elapsed time: {elapsed:.2f}s")

        if result is None:
            print("ERROR: Result is None (timeout)")
        else:
            print(f"Success: {result.success}")
            print(f"Definition ID: {result.definition_id}")
            if result.error:
                print(f"Error: {result.error}")
    except Exception as e:
        print(f"ERROR in test: {e}")
        import traceback
        traceback.print_exc()
    print()

# Test 4: Check for event loop conflicts
def test_event_loop_state():
    """Check current event loop state."""
    print("Test 4: Event loop state check")

    try:
        loop = asyncio.get_event_loop()
        print(f"Event loop exists: {loop is not None}")
        print(f"Event loop running: {loop.is_running()}")
        print(f"Event loop closed: {loop.is_closed()}")
    except RuntimeError as e:
        print(f"No event loop: {e}")

    try:
        running_loop = asyncio.get_running_loop()
        print(f"Running loop exists: {running_loop is not None}")
    except RuntimeError:
        print("No running loop")
    print()

# Test 5: Direct coroutine execution
def test_direct_coroutine():
    """Test running the coroutine directly without async_bridge."""
    print("Test 5: Direct coroutine execution")

    try:
        from src.services.container import ServiceContainer

        container = ServiceContainer()
        import_service = container.definition_import

        payload = {
            "begrip": "Direct test",
            "definitie": "Direct test definitie",
            "categorie": "proces",
            "organisatorische_context": ["Test"],
            "juridische_context": [],
            "wettelijke_basis": []
        }

        async def run_import():
            return await import_service.import_single(
                payload,
                duplicate_strategy="skip",
                created_by="direct_test"
            )

        # Run directly with asyncio.run
        print("Running with asyncio.run()...")
        start_time = time.time()
        result = asyncio.run(run_import())
        elapsed = time.time() - start_time

        print(f"Elapsed time: {elapsed:.2f}s")
        print(f"Success: {result.success}")
        print(f"Definition ID: {result.definition_id}")
        if result.error:
            print(f"Error: {result.error}")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    print()

if __name__ == "__main__":
    print("=" * 60)
    print("CSV Import Timeout Debug Tests")
    print("=" * 60)
    print()

    test_async_bridge()
    test_event_loop_state()
    test_with_existing_loop()
    test_direct_coroutine()
    test_import_service()

    print("=" * 60)
    print("Debug tests complete")
    print("=" * 60)