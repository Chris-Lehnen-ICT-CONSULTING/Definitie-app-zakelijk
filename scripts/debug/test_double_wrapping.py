#!/usr/bin/env python3
"""
Minimal reproduction script for DEF-99 double adapter wrapping bug.

This script demonstrates the root cause of AttributeError: 'coroutine'
object has no attribute 'cleaned_text' in validation flow.

Expected: Single adapter wrapping works correctly
Actual: Double adapter wrapping causes asyncio.to_thread() to fail
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from services.adapters.cleaning_service_adapter import CleaningServiceAdapterV1toV2
from services.interfaces import CleaningResult, Definition


class FakeSyncCleaningService:
    """Mock sync cleaning service that returns CleaningResult."""

    def clean_text(self, text: str, term: str) -> CleaningResult:
        """Sync method that returns CleaningResult."""
        return CleaningResult(
            original_text=text,
            cleaned_text=text.strip(),
            was_cleaned=text != text.strip(),
            applied_rules=["strip"],
        )


async def test_single_wrap():
    """Test single adapter wrapping - SHOULD WORK."""
    print("\n=== Test 1: Single Adapter Wrapping ===")

    # Create sync service
    sync_service = FakeSyncCleaningService()

    # Wrap once
    adapter = CleaningServiceAdapterV1toV2(sync_service)

    # Call async method
    result = await adapter.clean_text("  test  ", "begrip")

    # Verify
    assert isinstance(
        result, CleaningResult
    ), f"Expected CleaningResult, got {type(result)}"
    assert hasattr(
        result, "cleaned_text"
    ), f"Result missing cleaned_text attribute: {result}"
    print(f"✅ Single wrap works! Result: {result.cleaned_text}")
    return True


async def test_double_wrap():
    """Test double adapter wrapping - SHOULD FAIL with coroutine error."""
    print("\n=== Test 2: Double Adapter Wrapping (reproduces DEF-99) ===")

    # Create sync service
    sync_service = FakeSyncCleaningService()

    # Wrap ONCE (like container.py line 245)
    adapter1 = CleaningServiceAdapterV1toV2(sync_service)

    # Wrap AGAIN (like definition_orchestrator_v2.py line 221)
    adapter2 = CleaningServiceAdapterV1toV2(adapter1)

    # Call async method
    try:
        result = await adapter2.clean_text("  test  ", "begrip")

        # Try to access cleaned_text attribute
        print(f"Result type: {type(result)}")
        print(f"Result value: {result}")

        if hasattr(result, "cleaned_text"):
            print(f"✅ Double wrap works (unexpected!): {result.cleaned_text}")
            return False
        print("❌ Result is missing cleaned_text attribute!")
        print(f"   Available attributes: {dir(result)}")
        return True

    except AttributeError as e:
        print(f"❌ AttributeError caught (expected): {e}")
        return True
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")
        return True


async def test_asyncio_to_thread_with_async_function():
    """Test asyncio.to_thread() with async function - SHOULD FAIL."""
    print("\n=== Test 3: asyncio.to_thread() with async function ===")

    async def async_function():
        """Async function that returns a result."""
        return "async result"

    try:
        # This is what happens in double wrapping:
        # asyncio.to_thread(async_function) expects sync function, not async
        result = await asyncio.to_thread(async_function)
        print(f"Result: {result}")
        print(f"Result type: {type(result)}")

        # Result will be a coroutine object, not the actual result
        if asyncio.iscoroutine(result):
            print("❌ Result is a coroutine! This is the bug.")
            print("   asyncio.to_thread() cannot handle async functions")
            return True
        print("✅ Result is not a coroutine (unexpected)")
        return False

    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        return True


async def main():
    """Run all tests."""
    print("=" * 60)
    print("DEF-99 Double Adapter Wrapping Reproduction Test")
    print("=" * 60)

    results = []

    # Test 1: Single wrap (should work)
    try:
        results.append(("Single wrap", await test_single_wrap()))
    except Exception as e:
        print(f"❌ Test 1 failed with exception: {e}")
        results.append(("Single wrap", False))

    # Test 2: Double wrap (should fail with coroutine error)
    try:
        results.append(("Double wrap", await test_double_wrap()))
    except Exception as e:
        print(f"❌ Test 2 failed with exception: {e}")
        results.append(("Double wrap", False))

    # Test 3: asyncio.to_thread with async function
    try:
        results.append(
            ("asyncio.to_thread", await test_asyncio_to_thread_with_async_function())
        )
    except Exception as e:
        print(f"❌ Test 3 failed with exception: {e}")
        results.append(("asyncio.to_thread", False))

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")

    print("\n" + "=" * 60)
    print("ROOT CAUSE ANALYSIS")
    print("=" * 60)
    print(
        """
1. container.py line 245 wraps CleaningService ONCE:
   cleaning_service = CleaningServiceAdapterV1toV2(self.cleaning_service())

2. definition_orchestrator_v2.py line 221 wraps it AGAIN:
   cleaning_adapter = CleaningServiceAdapterV1toV2(self.cleaning_service)

3. Double wrapping chain:
   Adapter2 → Adapter1 → CleaningService

4. When Adapter2.clean_text() is called:
   - Adapter2 calls: asyncio.to_thread(Adapter1.clean_text, ...)
   - But Adapter1.clean_text is ASYNC function!
   - asyncio.to_thread() expects SYNC functions only
   - Result: Returns coroutine object instead of CleaningResult

5. Validation code tries to access result.cleaned_text
   → AttributeError: 'coroutine' object has no attribute 'cleaned_text'
"""
    )

    print("\nRECOMMENDED FIX:")
    print("Remove double wrapping at definition_orchestrator_v2.py line 221")
    print("Change:")
    print("  cleaning_adapter = CleaningServiceAdapterV1toV2(self.cleaning_service)")
    print("To:")
    print("  cleaning_adapter = self.cleaning_service  # Already wrapped by container")


if __name__ == "__main__":
    asyncio.run(main())
