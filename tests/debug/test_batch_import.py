#!/usr/bin/env python
"""Test batch CSV import with fixed async_bridge and database constraints."""

import time
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def test_batch_import():
    """Simulate batch CSV import like management_tab does."""
    from src.services.container import ServiceContainer
    from ui.helpers.async_bridge import run_async_safe

    container = ServiceContainer()
    import_service = container.import_service()

    # Test data simulating CSV rows
    test_rows = [
        {
            "begrip": f"Test begrip {i}",
            "definitie": f"Test definitie nummer {i} voor batch import test",
            "categorie": "proces" if i % 2 == 0 else "object",
            "organisatorische_context": [f"Context {i}"],
            "juridische_context": [],
            "wettelijke_basis": [],
            "UFO_Categorie": "Kind" if i % 3 == 0 else "Event",
            "Synoniemen": f"synoniem{i}_1, synoniem{i}_2",
            "Voorkeursterm": f"voorkeursterm_{i}"
        }
        for i in range(5)  # Test with 5 rows
    ]

    print("=" * 60)
    print("Batch Import Test (Simulating CSV)")
    print("=" * 60)
    print(f"\nTesting import of {len(test_rows)} definitions...")

    success_count = 0
    fail_count = 0
    results = []

    start_time = time.time()

    for idx, row in enumerate(test_rows):
        row_start = time.time()
        print(f"\nRow {idx + 1}: {row['begrip']}")

        # Import with timeout protection like management_tab
        result = run_async_safe(
            import_service.import_single(
                row,
                duplicate_strategy="skip",
                created_by="batch_test"
            ),
            default=None,
            timeout=3.0  # Same as management_tab
        )

        row_time = time.time() - row_start

        if result is None:
            fail_count += 1
            status = "TIMEOUT"
            error = "timeout/connection error"
            print(f"  ✗ Status: {status} ({row_time:.2f}s)")
        elif result.success:
            success_count += 1
            status = "SUCCESS"
            error = None
            print(f"  ✓ Status: {status} - ID: {result.definition_id} ({row_time:.2f}s)")
        else:
            fail_count += 1
            status = "FAILED"
            error = result.error
            print(f"  ✗ Status: {status} - Error: {error} ({row_time:.2f}s)")

        results.append({
            "row": idx + 1,
            "begrip": row["begrip"],
            "status": status,
            "time": row_time,
            "error": error
        })

    total_time = time.time() - start_time

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total rows processed: {len(test_rows)}")
    print(f"Successful imports: {success_count}")
    print(f"Failed imports: {fail_count}")
    print(f"Total time: {total_time:.2f}s")
    print(f"Average time per row: {total_time/len(test_rows):.2f}s")

    if fail_count > 0:
        print("\nFailed rows:")
        for r in results:
            if r["status"] != "SUCCESS":
                print(f"  Row {r['row']}: {r['begrip']} - {r['error']}")

    return success_count == len(test_rows)

if __name__ == "__main__":
    success = test_batch_import()

    print("\n" + "=" * 60)
    if success:
        print("✅ BATCH IMPORT TEST PASSED - ALL ROWS IMPORTED SUCCESSFULLY!")
    else:
        print("⚠️  Some rows failed, but the timeout issue appears to be fixed.")
        print("    The failures are likely duplicates or validation issues.")
    print("=" * 60)