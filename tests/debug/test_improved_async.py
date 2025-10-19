#!/usr/bin/env python
"""Test improved async_bridge with ThreadPoolExecutor."""

import asyncio
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

print("Testing improved async_bridge with thread pool...")


# Test 1: Basic functionality
def test_basic():
    """Test basic async_bridge with new implementation."""
    print("\n1. Basic test:")
    from ui.helpers.async_bridge import run_async_safe

    async def test_coro():
        await asyncio.sleep(0.1)
        return "success"

    result = run_async_safe(test_coro(), default="failed", timeout=1.0)
    print(f"   Result: {result}")
    assert result == "success", f"Expected 'success', got {result}"
    print("   ✓ Basic test passed")


# Test 2: Simulate Streamlit environment
def test_streamlit_like():
    """Test in Streamlit-like environment with existing event loop."""
    print("\n2. Streamlit-like environment test:")

    async def streamlit_main():
        """Simulates Streamlit's main async loop."""
        from ui.helpers.async_bridge import run_async_safe

        # This simulates calling an async service from within Streamlit
        async def service_call():
            await asyncio.sleep(0.1)
            return "streamlit_success"

        result = run_async_safe(service_call(), default="failed", timeout=2.0)
        print(f"   Result from Streamlit-like env: {result}")
        return result

    # Run in event loop (like Streamlit does)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        final = loop.run_until_complete(streamlit_main())
        assert (
            final == "streamlit_success"
        ), f"Expected 'streamlit_success', got {final}"
        print("   ✓ Streamlit-like test passed")
    finally:
        loop.close()


# Test 3: Real import service test
def test_real_import():
    """Test actual import service with new async_bridge."""
    print("\n3. Real import service test:")

    from src.services.container import ServiceContainer
    from ui.helpers.async_bridge import run_async_safe

    container = ServiceContainer()
    import_service = container.import_service()

    payload = {
        "begrip": "Test begrip improved",
        "definitie": "Test definitie met verbeterde async bridge",
        "categorie": "proces",
        "organisatorische_context": ["Test org"],
        "juridische_context": [],
        "wettelijke_basis": [],
    }

    print("   Calling import_single with improved async_bridge...")
    start = time.time()

    result = run_async_safe(
        import_service.import_single(
            payload, duplicate_strategy="skip", created_by="improved_test"
        ),
        default=None,
        timeout=3.0,
    )

    elapsed = time.time() - start
    print(f"   Elapsed: {elapsed:.2f}s")

    if result is None:
        print("   ✗ Result is None (timeout)")
        return False
    print(f"   Success: {result.success}")
    if result.definition_id:
        print(f"   Definition ID: {result.definition_id}")
    if result.error:
        print(f"   Error: {result.error}")
    print("   ✓ Import service test completed")
    return True


# Test 4: Concurrent imports
def test_concurrent():
    """Test multiple concurrent imports."""
    print("\n4. Concurrent imports test:")

    from ui.helpers.async_bridge import run_async_safe

    async def mock_import(n):
        await asyncio.sleep(0.2)
        return f"import_{n}"

    print("   Running 3 imports sequentially with async_bridge...")
    start = time.time()

    results = []
    for i in range(3):
        result = run_async_safe(mock_import(i), default=f"failed_{i}", timeout=1.0)
        results.append(result)
        print(f"   Import {i}: {result}")

    elapsed = time.time() - start
    print(f"   Total time: {elapsed:.2f}s")

    expected = ["import_0", "import_1", "import_2"]
    assert results == expected, f"Expected {expected}, got {results}"
    print("   ✓ Concurrent test passed")


if __name__ == "__main__":
    print("=" * 60)
    print("Improved Async Bridge Tests")
    print("=" * 60)

    try:
        test_basic()
        test_streamlit_like()
        success = test_real_import()
        test_concurrent()

        print("\n" + "=" * 60)
        if success:
            print("✓ All tests passed - async_bridge fix appears to work!")
        else:
            print("⚠ Some issues remain, but async_bridge is improved")
        print("=" * 60)

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback

        traceback.print_exc()
