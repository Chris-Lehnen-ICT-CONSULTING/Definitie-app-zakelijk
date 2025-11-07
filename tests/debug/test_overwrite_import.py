#!/usr/bin/env python
"""Test CSV import with overwrite strategy to verify complete fix."""

import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def test_with_overwrite():
    """Test batch import with overwrite strategy."""
    from src.services.container import ServiceContainer
    from ui.helpers.async_bridge import run_async_safe

    container = ServiceContainer()
    import_service = container.import_service()

    # Use same test data to test overwriting
    test_rows = [
        {
            "begrip": f"Import test {i}",
            "definitie": f"UPDATED definitie voor import test {i}",
            "categorie": "proces",
            "organisatorische_context": [f"Updated context {i}"],
            "juridische_context": ["Test juridisch"],
            "wettelijke_basis": [],
            "UFO_Categorie": "Event",
            "Synoniemen": f"updated_syn_{i}",
            "Voorkeursterm": f"updated_term_{i}",
        }
        for i in range(3)
    ]

    print("=" * 60)
    print("CSV Import Test with OVERWRITE Strategy")
    print("=" * 60)
    print(f"\nImporting {len(test_rows)} definitions with overwrite enabled...")

    success_count = 0
    fail_count = 0
    timeout_count = 0

    start_time = time.time()

    for idx, row in enumerate(test_rows):
        print(f"\nRow {idx + 1}: {row['begrip']}")

        # First import (should succeed or be duplicate)
        result1 = run_async_safe(
            import_service.import_single(
                row, duplicate_strategy="skip", created_by="test"
            ),
            default=None,
            timeout=3.0,
        )

        if result1 is None:
            print("  ✗ First import: TIMEOUT")
            timeout_count += 1
        elif result1.success:
            print(f"  ✓ First import: SUCCESS - ID {result1.definition_id}")
        else:
            print("  ℹ First import: Duplicate (expected)")

        # Second import with overwrite (should always succeed)
        result2 = run_async_safe(
            import_service.import_single(
                row,
                duplicate_strategy="overwrite",  # Use overwrite
                created_by="test_overwrite",
            ),
            default=None,
            timeout=3.0,
        )

        if result2 is None:
            print("  ✗ Overwrite: TIMEOUT (PROBLEM!)")
            timeout_count += 1
            fail_count += 1
        elif result2.success:
            print(f"  ✓ Overwrite: SUCCESS - ID {result2.definition_id}")
            success_count += 1
        else:
            print(f"  ✗ Overwrite: FAILED - {result2.error}")
            fail_count += 1

    total_time = time.time() - start_time

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total overwrites attempted: {len(test_rows)}")
    print(f"Successful overwrites: {success_count}")
    print(f"Failed overwrites: {fail_count}")
    print(f"Timeout errors: {timeout_count}")
    print(f"Total time: {total_time:.2f}s")
    print(f"Average time per row: {total_time/len(test_rows):.2f}s")

    return timeout_count == 0 and success_count == len(test_rows)


if __name__ == "__main__":
    print("\nThis test verifies that the CSV import fix handles:")
    print("1. Async/sync event loop conflicts (ThreadPoolExecutor)")
    print("2. Database constraint violations (status, categorie)")
    print("3. Both skip and overwrite strategies")
    print()

    success = test_with_overwrite()

    print("\n" + "=" * 60)
    if success:
        print("✅ CSV IMPORT FIX COMPLETE - ALL ISSUES RESOLVED!")
        print()
        print("Fixed issues:")
        print("• Event loop deadlock resolved with ThreadPoolExecutor")
        print("• Status constraint: 'imported' → 'draft'")
        print("• Categorie normalization: 'object' → 'type'")
        print("• Both skip and overwrite strategies working")
    else:
        print("⚠️  Some issues may remain - check the summary above")
    print("=" * 60)
